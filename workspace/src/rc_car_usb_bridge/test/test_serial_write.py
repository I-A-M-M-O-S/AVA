"""One-way operating-system serial write test."""

import os
import pty
import select

from rc_car_interfaces.msg import DriveCommand

from rc_car_usb_bridge.usb_bridge import UsbBridge, encode_command

import rclpy


def test_one_way_serial_write():
    """Write one encoded command through a pseudo-terminal."""
    master_fd, slave_fd = pty.openpty()
    slave_name = os.ttyname(slave_fd)
    rclpy.init(args=[
        '--ros-args',
        '-p', f'device:={slave_name}',
        '-p', 'dry_run:=false',
        '-p', 'expect_response:=false',
        '-p', 'message_watchdog_enabled:=false',
        '-p', 'validate_timestamp:=false',
        '-p', 'validate_sequence:=false',
    ])
    node = UsbBridge()
    try:
        command = DriveCommand()
        command.sequence = 42
        command.speed = 30
        command.steering = -20
        command.enabled = True
        node._on_command(command)

        readable, _, _ = select.select([master_fd], [], [], 1.0)
        assert readable
        assert os.read(master_fd, 256).decode('ascii') == encode_command(
            42, 30, -20, True
        )
    finally:
        node.close_serial()
        node.destroy_node()
        rclpy.shutdown()
        os.close(master_fd)
        os.close(slave_fd)
