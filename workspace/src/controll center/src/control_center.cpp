#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <limits>
#include <memory>
#include <sstream>
#include <string>

#include "ackermann_msgs/msg/ackermann_drive_stamped.hpp"
#include "nav_msgs/msg/occupancy_grid.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "nav_msgs/msg/path.hpp"
#include "rc_car_interfaces/msg/actuator_status.hpp"
#include "rc_car_interfaces/msg/vehicle_status.hpp"
#include "rc_car_interfaces/msg/wheel_encoder_state.hpp"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/camera_info.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "sensor_msgs/msg/magnetic_field.hpp"
#include "std_msgs/msg/bool.hpp"
#include "std_msgs/msg/string.hpp"

using namespace std::chrono_literals;

class ControlCenter final : public rclcpp::Node
{
public:
  ControlCenter() : Node("control_center")
  {
    declare_parameters();
    create_sensor_inputs();
    create_vehicle_inputs();
    create_system_inputs();

    command_pub_ = create_publisher<ackermann_msgs::msg::AckermannDriveStamped>(
      "/control/autonomous_ackermann_cmd", 10);
    status_pub_ = create_publisher<std_msgs::msg::String>("/control_center/status", 10);

    const double rate = std::max(1.0, get_parameter("control_rate").as_double());
    control_timer_ = create_wall_timer(
      std::chrono::duration<double>(1.0 / rate), [this]() {control_tick();});
    status_timer_ = create_wall_timer(200ms, [this]() {publish_status();});
    RCLCPP_INFO(get_logger(), "SI control center ready with LIDAR_GAP baseline logic");
  }

private:
  using Clock = std::chrono::steady_clock;
  struct Input
  {
    bool received{false};
    Clock::time_point stamp{};
    void mark() {received = true; stamp = Clock::now();}
  };

  void declare_parameters()
  {
    declare_parameter("image_topic", "/camera/image_raw");
    declare_parameter("camera_info_topic", "/camera/camera_info");
    declare_parameter("scan_topic", "/scan");
    declare_parameter("imu_topic", "/imu/data");
    declare_parameter("mag_topic", "/imu/mag");
    declare_parameter("odom_topic", "/odometry/filtered");
    declare_parameter("map_topic", "/map");
    declare_parameter("racing_line_topic", "/planning/racing_line");
    declare_parameter("logic_enabled", true);
    declare_parameter("require_odometry", true);
    declare_parameter("input_timeout", 0.5);
    declare_parameter("control_rate", 20.0);
    declare_parameter("cruise_speed", 0.35);
    declare_parameter("stop_distance", 0.35);
    declare_parameter("slow_distance", 0.90);
    declare_parameter("maximum_steering_angle", 0.45);
    declare_parameter("steering_gain", 0.9);
  }

  void create_sensor_inputs()
  {
    const auto sensor_qos = rclcpp::SensorDataQoS();
    image_sub_ = create_subscription<sensor_msgs::msg::Image>(
      get_parameter("image_topic").as_string(), sensor_qos,
      [this](sensor_msgs::msg::Image::ConstSharedPtr msg) {
        image_.mark(); image_width_ = msg->width; image_height_ = msg->height;
      });
    camera_info_sub_ = create_subscription<sensor_msgs::msg::CameraInfo>(
      get_parameter("camera_info_topic").as_string(), sensor_qos,
      [this](sensor_msgs::msg::CameraInfo::ConstSharedPtr) {camera_info_.mark();});
    scan_sub_ = create_subscription<sensor_msgs::msg::LaserScan>(
      get_parameter("scan_topic").as_string(), sensor_qos,
      [this](sensor_msgs::msg::LaserScan::ConstSharedPtr msg) {
        scan_.mark();
        front_distance_ = sector_minimum(*msg, -15.0, 15.0);
        left_clearance_ = sector_average(*msg, 10.0, 70.0);
        right_clearance_ = sector_average(*msg, -70.0, -10.0);
      });
    imu_sub_ = create_subscription<sensor_msgs::msg::Imu>(
      get_parameter("imu_topic").as_string(), sensor_qos,
      [this](sensor_msgs::msg::Imu::ConstSharedPtr msg) {
        imu_.mark(); yaw_rate_ = msg->angular_velocity.z;
      });
    mag_sub_ = create_subscription<sensor_msgs::msg::MagneticField>(
      get_parameter("mag_topic").as_string(), sensor_qos,
      [this](sensor_msgs::msg::MagneticField::ConstSharedPtr) {mag_.mark();});
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
      get_parameter("odom_topic").as_string(), 10,
      [this](nav_msgs::msg::Odometry::ConstSharedPtr msg) {
        odom_.mark(); speed_ = msg->twist.twist.linear.x;
      });
    map_sub_ = create_subscription<nav_msgs::msg::OccupancyGrid>(
      get_parameter("map_topic").as_string(), rclcpp::QoS(1).reliable().transient_local(),
      [this](nav_msgs::msg::OccupancyGrid::ConstSharedPtr msg) {
        map_.mark(); map_width_ = msg->info.width; map_height_ = msg->info.height;
      });
    racing_line_sub_ = create_subscription<nav_msgs::msg::Path>(
      get_parameter("racing_line_topic").as_string(), 10,
      [this](nav_msgs::msg::Path::ConstSharedPtr msg) {
        racing_line_.mark(); racing_line_points_ = msg->poses.size();
      });
  }

  void create_vehicle_inputs()
  {
    vehicle_sub_ = create_subscription<rc_car_interfaces::msg::VehicleStatus>(
      "/vehicle/status", 10,
      [this](rc_car_interfaces::msg::VehicleStatus::ConstSharedPtr msg) {
        vehicle_.mark(); faults_ = msg->fault_flags; armed_ = msg->armed;
      });
    actuator_sub_ = create_subscription<rc_car_interfaces::msg::ActuatorStatus>(
      "/vehicle/actuator_status", 10,
      [this](rc_car_interfaces::msg::ActuatorStatus::ConstSharedPtr msg) {
        actuator_.mark(); applied_speed_ = msg->speed; applied_steering_ = msg->steering;
      });
    encoder_sub_ = create_subscription<rc_car_interfaces::msg::WheelEncoderState>(
      "/vehicle/encoders", 10,
      [this](rc_car_interfaces::msg::WheelEncoderState::ConstSharedPtr msg) {
        encoders_.mark(); encoder_sample_ = msg->sample_counter;
      });
  }

  void create_system_inputs()
  {
    const auto latched = rclcpp::QoS(1).reliable().transient_local();
    mode_sub_ = create_subscription<std_msgs::msg::String>(
      "/system/mode", latched,
      [this](std_msgs::msg::String::ConstSharedPtr msg) {
        mode_.mark(); selected_mode_ = msg->data;
      });
    enable_sub_ = create_subscription<std_msgs::msg::Bool>(
      "/system/drive_enable", latched,
      [this](std_msgs::msg::Bool::ConstSharedPtr msg) {
        drive_enable_.mark(); drive_enabled_ = msg->data;
      });
    commander_sub_ = create_subscription<std_msgs::msg::String>(
      "/drive_commander/status", 10,
      [this](std_msgs::msg::String::ConstSharedPtr) {commander_.mark();});
    usb_sub_ = create_subscription<std_msgs::msg::String>(
      "/drive_usb/status", latched,
      [this](std_msgs::msg::String::ConstSharedPtr) {usb_.mark();});
  }

  bool fresh(const Input & input) const
  {
    return input.received && age(input) <= get_parameter("input_timeout").as_double();
  }

  static double age(const Input & input)
  {
    if (!input.received) {return -1.0;}
    return std::chrono::duration<double>(Clock::now() - input.stamp).count();
  }

  static bool usable(const sensor_msgs::msg::LaserScan & scan, float value)
  {
    return std::isfinite(value) && value >= scan.range_min && value <= scan.range_max;
  }

  static double sector_minimum(
    const sensor_msgs::msg::LaserScan & scan, double start_deg, double end_deg)
  {
    double result = std::numeric_limits<double>::infinity();
    for (std::size_t i = 0; i < scan.ranges.size(); ++i) {
      const double angle = (scan.angle_min + i * scan.angle_increment) * 180.0 / M_PI;
      if (angle >= start_deg && angle <= end_deg && usable(scan, scan.ranges[i])) {
        result = std::min(result, static_cast<double>(scan.ranges[i]));
      }
    }
    return result;
  }

  static double sector_average(
    const sensor_msgs::msg::LaserScan & scan, double start_deg, double end_deg)
  {
    double total = 0.0;
    std::size_t count = 0;
    const double clear = std::min(10.0, static_cast<double>(scan.range_max));
    for (std::size_t i = 0; i < scan.ranges.size(); ++i) {
      const double angle = (scan.angle_min + i * scan.angle_increment) * 180.0 / M_PI;
      if (angle >= start_deg && angle <= end_deg) {
        total += usable(scan, scan.ranges[i]) ? scan.ranges[i] : clear;
        ++count;
      }
    }
    return count ? total / count : 0.0;
  }

  void control_tick()
  {
    // Never compete with MANUAL or TEST. Entering AUTONOMOUS begins with
    // neutral heartbeats until the independent watchdog enables driving.
    if (!mode_.received || selected_mode_ != "AUTONOMOUS") {
      reason_ = "mode_not_autonomous";
      return;
    }
    if (!get_parameter("logic_enabled").as_bool()) {
      publish_command(0.0, 0.0, "logic_disabled"); return;
    }
    if (!fresh(scan_)) {
      publish_command(0.0, 0.0, "scan_stale"); return;
    }
    if (get_parameter("require_odometry").as_bool() && !fresh(odom_)) {
      publish_command(0.0, 0.0, "odometry_stale"); return;
    }
    if (!drive_enable_.received || !drive_enabled_) {
      publish_command(0.0, 0.0, "waiting_for_drive_enable"); return;
    }
    if (vehicle_.received && faults_ != 0U) {
      publish_command(0.0, 0.0, "vehicle_fault"); return;
    }

    const double stop = get_parameter("stop_distance").as_double();
    const double slow = std::max(stop + 0.01, get_parameter("slow_distance").as_double());
    if (std::isfinite(front_distance_) && front_distance_ <= stop) {
      publish_command(0.0, 0.0, "obstacle_stop"); return;
    }

    const double max_steer = get_parameter("maximum_steering_angle").as_double();
    const double scale = std::max(0.5, left_clearance_ + right_clearance_);
    const double steering = std::clamp(
      get_parameter("steering_gain").as_double() *
      (left_clearance_ - right_clearance_) / scale, -max_steer, max_steer);
    double speed = get_parameter("cruise_speed").as_double();
    if (std::isfinite(front_distance_) && front_distance_ < slow) {
      speed *= std::clamp((front_distance_ - stop) / (slow - stop), 0.0, 1.0);
    }
    if (max_steer > 0.0) {
      speed *= std::clamp(1.0 - 0.6 * std::abs(steering) / max_steer, 0.25, 1.0);
    }
    publish_command(speed, steering, "lidar_gap");
  }

  void publish_command(double speed, double steering, const std::string & reason)
  {
    ackermann_msgs::msg::AckermannDriveStamped command;
    command.header.stamp = now();
    command.header.frame_id = "base_link";
    command.drive.speed = speed;
    command.drive.steering_angle = steering;
    command_pub_->publish(command);
    requested_speed_ = speed; requested_steering_ = steering; reason_ = reason;
  }

  void publish_status()
  {
    std::ostringstream out;
    out << "{\"logic\":{\"type\":\"LIDAR_GAP\",\"reason\":\"" << reason_
        << "\",\"speed_mps\":" << requested_speed_
        << ",\"steering_rad\":" << requested_steering_ << "},"
        << "\"system\":{\"mode\":\"" << selected_mode_
        << "\",\"drive_enable\":" << (drive_enabled_ ? "true" : "false") << "},"
        << "\"topics\":{\"scan_fresh\":" << (fresh(scan_) ? "true" : "false")
        << ",\"odom_fresh\":" << (fresh(odom_) ? "true" : "false")
        << ",\"imu_fresh\":" << (fresh(imu_) ? "true" : "false")
        << ",\"camera\":" << (image_.received ? "true" : "false")
        << ",\"camera_info\":" << (camera_info_.received ? "true" : "false")
        << ",\"mag\":" << (mag_.received ? "true" : "false")
        << ",\"map\":" << (map_.received ? "true" : "false")
        << ",\"racing_line_points\":" << racing_line_points_
        << ",\"vehicle\":" << (vehicle_.received ? "true" : "false")
        << ",\"actuator\":" << (actuator_.received ? "true" : "false")
        << ",\"encoders\":" << (encoders_.received ? "true" : "false") << "},"
        << "\"state\":{\"front_m\":";
    if (std::isfinite(front_distance_)) {out << front_distance_;} else {out << "null";}
    out << ",\"left_m\":" << left_clearance_ << ",\"right_m\":" << right_clearance_
        << ",\"speed_mps\":" << speed_ << ",\"yaw_rate_radps\":" << yaw_rate_
        << ",\"fault_flags\":" << faults_ << ",\"armed\":"
        << (armed_ ? "true" : "false") << ",\"applied_speed\":"
        << static_cast<int>(applied_speed_) << ",\"applied_steering\":"
        << static_cast<int>(applied_steering_) << ",\"encoder_sample\":"
        << encoder_sample_ << ",\"map_width\":" << map_width_
        << ",\"map_height\":" << map_height_ << "}}";
    std_msgs::msg::String status; status.data = out.str(); status_pub_->publish(status);
  }

  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_sub_;
  rclcpp::Subscription<sensor_msgs::msg::CameraInfo>::SharedPtr camera_info_sub_;
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_sub_;
  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
  rclcpp::Subscription<sensor_msgs::msg::MagneticField>::SharedPtr mag_sub_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
  rclcpp::Subscription<nav_msgs::msg::OccupancyGrid>::SharedPtr map_sub_;
  rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr racing_line_sub_;
  rclcpp::Subscription<rc_car_interfaces::msg::VehicleStatus>::SharedPtr vehicle_sub_;
  rclcpp::Subscription<rc_car_interfaces::msg::ActuatorStatus>::SharedPtr actuator_sub_;
  rclcpp::Subscription<rc_car_interfaces::msg::WheelEncoderState>::SharedPtr encoder_sub_;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr mode_sub_, commander_sub_, usb_sub_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr enable_sub_;
  rclcpp::Publisher<ackermann_msgs::msg::AckermannDriveStamped>::SharedPtr command_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr status_pub_;
  rclcpp::TimerBase::SharedPtr control_timer_, status_timer_;

  Input image_, camera_info_, scan_, imu_, mag_, odom_, map_, racing_line_;
  Input vehicle_, actuator_, encoders_, mode_, drive_enable_, commander_, usb_;
  std::string selected_mode_{"UNKNOWN"}, reason_{"startup"};
  bool drive_enabled_{false}, armed_{false};
  uint32_t image_width_{0}, image_height_{0}, map_width_{0}, map_height_{0};
  uint32_t faults_{0}, encoder_sample_{0};
  std::size_t racing_line_points_{0};
  int8_t applied_speed_{0}, applied_steering_{0};
  double speed_{0.0}, yaw_rate_{0.0};
  double front_distance_{std::numeric_limits<double>::infinity()};
  double left_clearance_{0.0}, right_clearance_{0.0};
  double requested_speed_{0.0}, requested_steering_{0.0};
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ControlCenter>());
  rclcpp::shutdown();
  return 0;
}
