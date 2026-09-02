"""Launch the autonomous controller through the complete drive stack."""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    """Build the safe autonomous launch description."""
    stack_launch = os.path.join(
        get_package_share_directory('avaj_car_control'),
        'launch',
        'drive_stack.launch.py',
    )
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('usb_dry_run', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(stack_launch),
            launch_arguments={
                'initial_mode': 'AUTONOMOUS',
                'watchdog_bypass': 'false',
                'source_timeout_enabled': 'true',
                'usb_dry_run': LaunchConfiguration('usb_dry_run'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items(),
        ),
        Node(
            package='control_center',
            executable='control_center_node',
            name='control_center',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }],
        ),
    ])
