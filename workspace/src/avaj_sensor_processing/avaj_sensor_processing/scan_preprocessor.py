#!/usr/bin/env python3

"""Validate and filter raw laser scans into the canonical scan topic."""

import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


class ScanPreprocessor(Node):
    """Apply configured range limits while preserving LaserScan geometry."""

    def __init__(self):
        super().__init__('lidar_preprocessor')
        self.declare_parameter('input_topic', '/scan_raw')
        self.declare_parameter('output_topic', '/scan')
        self.declare_parameter('minimum_range', 0.0)
        self.declare_parameter('maximum_range', 0.0)

        input_topic = str(self.get_parameter('input_topic').value)
        output_topic = str(self.get_parameter('output_topic').value)
        self._publisher = self.create_publisher(
            LaserScan, output_topic, qos_profile_sensor_data
        )
        self.create_subscription(
            LaserScan, input_topic, self._on_scan, qos_profile_sensor_data
        )
        self.get_logger().info(
            f'LiDAR preprocessing: {input_topic} -> {output_topic}'
        )

    def _on_scan(self, message):
        if (
            not math.isfinite(message.angle_min)
            or not math.isfinite(message.angle_max)
            or not math.isfinite(message.angle_increment)
            or message.angle_increment == 0.0
            or message.range_min < 0.0
            or message.range_max <= message.range_min
        ):
            self.get_logger().error(
                'Dropping LaserScan with invalid geometry or range limits',
                throttle_duration_sec=2.0,
            )
            return

        configured_min = float(self.get_parameter('minimum_range').value)
        configured_max = float(self.get_parameter('maximum_range').value)
        effective_min = max(message.range_min, configured_min)
        effective_max = (
            min(message.range_max, configured_max)
            if configured_max > 0.0
            else message.range_max
        )
        if effective_max <= effective_min:
            self.get_logger().error(
                'Dropping LaserScan because configured limits are empty',
                throttle_duration_sec=2.0,
            )
            return

        output = LaserScan()
        output.header = message.header
        output.angle_min = message.angle_min
        output.angle_max = message.angle_max
        output.angle_increment = message.angle_increment
        output.time_increment = message.time_increment
        output.scan_time = message.scan_time
        output.range_min = effective_min
        output.range_max = effective_max
        output.ranges = [
            value if math.isfinite(value) and effective_min <= value <= effective_max
            else math.inf
            for value in message.ranges
        ]
        output.intensities = message.intensities
        self._publisher.publish(output)


def main():
    rclpy.init()
    node = ScanPreprocessor()
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
