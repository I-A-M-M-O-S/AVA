"""Deterministic synthetic tests for the three global graph invariants."""

import time

from ackermann_msgs.msg import AckermannDriveStamped

from graph_invariants import GraphInvariantMonitor

from rc_car_interfaces.msg import DriveCommand

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node

from tf2_msgs.msg import TFMessage


def _node(name, context):
    return Node(
        name,
        context=context,
        parameter_overrides=[
            rclpy.parameter.Parameter(
                'use_sim_time', rclpy.Parameter.Type.BOOL, True
            ),
        ],
    )


def _spin(executor, seconds=0.35):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        executor.spin_once(timeout_sec=0.02)


def _tf_message():
    message = TFMessage()
    transform = message.transforms.add() if hasattr(
        message.transforms, 'add'
    ) else None
    if transform is None:
        from geometry_msgs.msg import TransformStamped
        transform = TransformStamped()
        message.transforms.append(transform)
    transform.header.frame_id = 'map'
    transform.child_frame_id = 'odom'
    return message


def _run_graph(extra_drive=False, extra_ackermann=False, tf_count=1):
    context = rclpy.context.Context()
    rclpy.init(context=context)
    monitor = GraphInvariantMonitor(context=context)
    commander = _node('drive_commander', context)
    commander.create_publisher(DriveCommand, '/drive_commands', 10)
    nodes = [monitor, commander]
    if extra_drive:
        rogue = _node('rogue_drive_publisher', context)
        rogue.create_publisher(DriveCommand, '/drive_commands', 10)
        nodes.append(rogue)
    for index in range(1 + int(extra_ackermann)):
        controller = _node(f'autonomous_controller_{index}', context)
        controller.create_publisher(
            AckermannDriveStamped,
            '/control/autonomous_ackermann_cmd',
            10,
        )
        nodes.append(controller)
    tf_publishers = []
    for index in range(tf_count):
        broadcaster_name = ('slam_toolbox', 'amcl')[index]
        broadcaster = _node(broadcaster_name, context)
        publisher = broadcaster.create_publisher(TFMessage, '/tf', 100)
        nodes.append(broadcaster)
        tf_publishers.append(publisher)
    executor = SingleThreadedExecutor(context=context)
    for node in nodes:
        executor.add_node(node)
    try:
        _spin(executor)
        for publisher in tf_publishers:
            publisher.publish(_tf_message())
        _spin(executor)
        return monitor.report()
    finally:
        for node in reversed(nodes):
            executor.remove_node(node)
            node.destroy_node()
        executor.shutdown()
        rclpy.shutdown(context=context)


def test_valid_graph_passes_all_invariants():
    """Accept the intended single-owner graph."""
    report = _run_graph()
    assert report.ok, report.violations
    assert report.drive_publishers == ('/drive_commander',)
    assert report.ackermann_publishers == ('/autonomous_controller_0',)
    assert report.map_odom_publisher_count == 1


def test_intentional_second_drive_publisher_fails():
    """Reject an intentionally injected second final-command publisher."""
    report = _run_graph(extra_drive=True)
    assert not report.ok
    assert any('/drive_commands' in item for item in report.violations)


def test_second_ackermann_publisher_fails():
    """Reject simultaneous autonomous-controller publishers."""
    report = _run_graph(extra_ackermann=True)
    assert not report.ok
    assert any(
        '/control/autonomous_ackermann_cmd' in item
        for item in report.violations
    )


def test_second_map_to_odom_authority_fails():
    """Reject simultaneous mapping and localization TF authorities."""
    report = _run_graph(tf_count=2)
    assert not report.ok
    assert any('map -> odom' in item for item in report.violations)
