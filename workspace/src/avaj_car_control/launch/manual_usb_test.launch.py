"""Launch the intentionally unguarded manual one-way USB output test."""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    """Build the manual USB test launch description."""
    stack_launch = os.path.join(
        get_package_share_directory('avaj_car_control'),
        'launch',
        'drive_stack.launch.py',
    )
    usb_physical_port = LaunchConfiguration('usb_physical_port')
    return LaunchDescription([
        DeclareLaunchArgument(
            'usb_physical_port', default_value='1-2.2'
        ),
        LogInfo(msg=(
            'WARNING: MANUAL USB TEST MODE. ROS and USB message watchdogs '
            'are intentionally bypassed; do not connect motors.'
        )),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(stack_launch),
            launch_arguments={
                'initial_mode': 'MANUAL',
                # TODO(SAFETY-MANDATORY): Before any motor or steering hardware
                # is connected, enable the ROS source/sensor watchdogs, require
                # ESP feedback, and enable the independent ESP command timeout.
                'watchdog_bypass': 'true',
                'source_timeout_enabled': 'false',
                'usb_dry_run': 'false',
                'usb_device': '',
                # Selected free socket in the same dual USB-A block as the
                # Apple keyboard (keyboard=1-2.1, selected socket=1-2.2).
                # If a serial
                # adapter enumerates elsewhere, determine its topology and
                # override usb_physical_port on the launch command line.
                'usb_physical_port': usb_physical_port,
                'usb_expect_response': 'false',
                'usb_message_watchdog': 'false',
            }.items(),
        ),
        Node(
            package='avaj_car_control',
            executable='wasd_teleop',
            name='manual_controller',
            output='screen',
        ),
    ])
