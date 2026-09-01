#!/usr/bin/env python3

"""Validate raw IMU samples and expose the canonical IMU topic."""

import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu


class ImuPreprocessor(Node):
    """Reject non-finite samples before republishing sensor-fused IMU data."""

    def __init__(self):
        super().__init__('imu_preprocessor')
        self.declare_parameter('input_topic', '/imu/data_raw')
        self.declare_parameter('output_topic', '/imu/data')

        input_topic = str(self.get_parameter('input_topic').value)
        output_topic = str(self.get_parameter('output_topic').value)
        self._publisher = self.create_publisher(
            Imu, output_topic, qos_profile_sensor_data
        )
        self.create_subscription(
            Imu, input_topic, self._on_imu, qos_profile_sensor_data
        )
        self.get_logger().info(
            f'IMU validation: {input_topic} -> {output_topic}'
        )

    def _on_imu(self, message):
        values = (
            message.orientation.x,
            message.orientation.y,
            message.orientation.z,
            message.orientation.w,
            message.angular_velocity.x,
            message.angular_velocity.y,
            message.angular_velocity.z,
            message.linear_acceleration.x,
            message.linear_acceleration.y,
            message.linear_acceleration.z,
        )
        if not all(math.isfinite(value) for value in values):
            self.get_logger().error(
                'Dropping IMU sample containing NaN or Inf',
                throttle_duration_sec=2.0,
            )
            return
        self._publisher.publish(message)


def main():
    rclpy.init()
    node = ImuPreprocessor()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
