cmake_minimum_required(VERSION 3.8)
project(control_center)

find_package(ament_cmake REQUIRED)
find_package(ackermann_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(rc_car_interfaces REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(control_center_node src/control_center.cpp)
target_compile_features(control_center_node PUBLIC cxx_std_17)
ament_target_dependencies(control_center_node
  ackermann_msgs
  nav_msgs
  rc_car_interfaces
  rclcpp
  sensor_msgs
  std_msgs
)

install(TARGETS control_center_node DESTINATION lib/${PROJECT_NAME})
install(PROGRAMS scripts/control_center DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})
ament_package()
