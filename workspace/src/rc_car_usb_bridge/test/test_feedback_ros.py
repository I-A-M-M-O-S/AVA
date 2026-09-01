"""Pseudo-terminal integration from serial bytes to typed ROS topics."""

import os
import pty
import time

from rc_car_interfaces.msg import (
    ActuatorStatus,
    VehicleStatus,
    WheelEncoderState,
)

from rc_car_usb_bridge.feedback_protocol import crc16_ccitt
from rc_car_usb_bridge.usb_bridge import UsbBridge

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node


def frame(payload):
    """Build one valid LF-terminated feedback frame."""
    encoded = payload.encode('ascii')
    return encoded + f'*{crc16_ccitt(encoded):04X}\n'.encode('ascii')


def spin_until(executor, predicate, timeout=2.0):
    """Spin the isolated executor until a condition or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and not predicate():
        executor.spin_once(timeout_sec=0.02)
    return predicate()


def test_pty_fragmented_concatenated_and_invalid_feedback():
    """Publish typed ROS data only for valid PTY feedback frames."""
    master_fd, slave_fd = pty.openpty()
    slave_name = os.ttyname(slave_fd)
    rclpy.init(args=[
        '--ros-args',
        '-p', f'device:={slave_name}',
        '-p', 'dry_run:=false',
        '-p', 'expect_response:=true',
        '-p', 'message_watchdog_enabled:=false',
    ])
    bridge = UsbBridge()
    observer = Node('feedback_test_observer')
    received = {'status': [], 'actuator': [], 'encoder': []}
    observer.create_subscription(
        VehicleStatus, '/vehicle/status',
        received['status'].append, 10,
    )
    observer.create_subscription(
        ActuatorStatus, '/vehicle/actuator_status',
        received['actuator'].append, 10,
    )
    observer.create_subscription(
        WheelEncoderState, '/vehicle/encoders',
        received['encoder'].append, 10,
    )
    executor = SingleThreadedExecutor()
    executor.add_node(bridge)
    executor.add_node(observer)
    try:
        status = frame('V1,STA,7,2,0,1,1,0')
        os.write(master_fd, status[:5])
        for _ in range(3):
            executor.spin_once(timeout_sec=0.02)
        assert received['status'] == []
        os.write(master_fd, status[5:])

        invalid = b'V1,ACT,7,1,2,1*0000\n'
        actuator = frame('V1,ACT,7,1,2,1')
        encoder = frame('V1,ENC,3,-10,20,-30,40')
        os.write(master_fd, invalid + actuator + encoder)
        assert spin_until(
            executor,
            lambda: all(len(values) == 1 for values in received.values()),
        )
        assert received['status'][0].last_accepted_sequence == 7
        assert received['actuator'][0].speed == 1
        assert received['encoder'][0].rear_right_ticks == 40
        assert received['status'][0].header.stamp.sec > 0

        # Invalid feedback did not create an additional typed publication.
        for _ in range(5):
            executor.spin_once(timeout_sec=0.02)
        assert {key: len(value) for key, value in received.items()} == {
            'status': 1, 'actuator': 1, 'encoder': 1,
        }

        publishers = bridge.get_publishers_info_by_topic('/drive_commands')
        subscribers = bridge.get_subscriptions_info_by_topic('/drive_commands')
        assert publishers == []
        assert len(subscribers) == 1
        assert subscribers[0].node_name == bridge.get_name()
    finally:
        executor.remove_node(observer)
        executor.remove_node(bridge)
        observer.destroy_node()
        bridge.close_serial()
        bridge.destroy_node()
        executor.shutdown()
        rclpy.shutdown()
        os.close(master_fd)
        os.close(slave_fd)
