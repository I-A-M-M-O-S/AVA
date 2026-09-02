from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('logic_enabled', default_value='true'),
        Node(
            package='control_center',
            executable='control_center_node',
            name='control_center',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'logic_enabled': LaunchConfiguration('logic_enabled'),
            }],
        ),
    ])
