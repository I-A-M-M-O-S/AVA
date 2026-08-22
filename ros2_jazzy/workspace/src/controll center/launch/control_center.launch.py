from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='avaj_car_control',
            executable='drive_command_to_twist',
            name='drive_command_to_twist',
            output='screen',
        ),
        Node(
            package='control_center',
            executable='control_center_node',
            name='control_center',
            output='screen',
        ),
    ])
