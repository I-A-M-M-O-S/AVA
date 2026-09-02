"""Publish one validated static reference path with transient-local QoS."""

from __future__ import annotations

import math

from avaj_racing.reference_path import (
    PathValidationError,
    ValidationConfig,
    load_csv,
    validate_path,
)

from geometry_msgs.msg import PoseStamped

from nav_msgs.msg import Path

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy


class ReferencePathImporter(Node):
    """Load one CSV file once and publish identical canonical and alias paths."""

    def __init__(self):
        """Configure latched publishers and attempt the one-time import."""
        super().__init__('reference_path_importer')
        self.declare_parameter('csv_path', '')
        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('required_direction', 'counterclockwise')
        self.declare_parameter('min_point_spacing_m', 0.05)
        self.declare_parameter('max_segment_length_m', 3.0)
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._reference_publisher = self.create_publisher(
            Path, '/planning/reference_path', qos
        )
        self._racing_line_publisher = self.create_publisher(
            Path, '/planning/racing_line', qos
        )
        self._load_and_publish()

    def _load_and_publish(self):
        csv_path = str(self.get_parameter('csv_path').value)
        config = ValidationConfig(
            frame_id=str(self.get_parameter('frame_id').value),
            required_direction=str(self.get_parameter('required_direction').value),
            min_point_spacing_m=float(
                self.get_parameter('min_point_spacing_m').value
            ),
            max_segment_length_m=float(
                self.get_parameter('max_segment_length_m').value
            ),
        )
        if not csv_path:
            self.get_logger().error('csv_path is required; no path was published')
            return
        try:
            validated = validate_path(load_csv(csv_path), config)
        except PathValidationError as exc:
            self.get_logger().error(f'Reference path rejected: {exc}')
            return
        path = Path()
        path.header.stamp = self.get_clock().now().to_msg()
        path.header.frame_id = validated.frame_id
        for point in validated.points:
            pose = PoseStamped()
            pose.header = path.header
            pose.pose.position.x = point.x_m
            pose.pose.position.y = point.y_m
            pose.pose.orientation.z = math.sin(point.heading_rad / 2.0)
            pose.pose.orientation.w = math.cos(point.heading_rad / 2.0)
            path.poses.append(pose)
        self._reference_publisher.publish(path)
        self._racing_line_publisher.publish(path)
        self.get_logger().info(
            f'Published {len(path.poses)}-point {validated.direction} path '
            f'({validated.total_length_m:.2f} m) on reference_path and racing_line'
        )


def main():
    """Run the static-path publisher until it is interrupted."""
    rclpy.init()
    node = ReferencePathImporter()
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
