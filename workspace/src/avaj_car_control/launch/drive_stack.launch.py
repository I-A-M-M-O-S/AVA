"""Launch mode, safety, final command, simulation and USB transport nodes."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Build the common drive stack launch description."""
    initial_mode = LaunchConfiguration('initial_mode')
    watchdog_bypass = LaunchConfiguration('watchdog_bypass')
    source_timeout_enabled = LaunchConfiguration('source_timeout_enabled')
    usb_dry_run = LaunchConfiguration('usb_dry_run')
    usb_device = LaunchConfiguration('usb_device')
    usb_physical_port = LaunchConfiguration('usb_physical_port')
    usb_expect_response = LaunchConfiguration('usb_expect_response')
    usb_message_watchdog = LaunchConfiguration('usb_message_watchdog')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument('initial_mode', default_value='DISABLED'),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('watchdog_bypass', default_value='false'),
        DeclareLaunchArgument(
            'source_timeout_enabled', default_value='true'
        ),
        DeclareLaunchArgument('usb_dry_run', default_value='true'),
        DeclareLaunchArgument('usb_device', default_value=''),
        DeclareLaunchArgument('usb_physical_port', default_value=''),
        DeclareLaunchArgument('usb_expect_response', default_value='false'),
        DeclareLaunchArgument('usb_message_watchdog', default_value='true'),
        Node(
            package='avaj_car_control',
            executable='mode_manager',
            name='mode_manager',
            output='screen',
            parameters=[{
                'initial_mode': initial_mode,
                'use_sim_time': use_sim_time,
            }],
        ),
        Node(
            package='avaj_car_control',
            executable='safety_watchdog',
            name='safety_watchdog',
            output='screen',
            parameters=[{
                'bypass': ParameterValue(watchdog_bypass, value_type=bool),
                'use_sim_time': use_sim_time,
            }],
        ),
        Node(
            package='avaj_car_control',
            executable='ackermann_to_drive_request',
            name='ackermann_to_drive_request',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
        ),
        Node(
            package='avaj_car_control',
            executable='drive_commander',
            name='drive_commander',
            output='screen',
            parameters=[{
                'source_timeout_enabled': ParameterValue(
                    source_timeout_enabled, value_type=bool
                ),
                'use_sim_time': use_sim_time,
            }],
        ),
        Node(
            package='avaj_car_control',
            executable='drive_command_to_twist',
            name='drive_command_to_twist',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
        ),
        Node(
            package='rc_car_usb_bridge',
            executable='usb_bridge',
            name='usb_bridge',
            output='screen',
            parameters=[{
                'dry_run': ParameterValue(usb_dry_run, value_type=bool),
                'device': usb_device,
                'physical_port': usb_physical_port,
                'expect_response': ParameterValue(
                    usb_expect_response, value_type=bool
                ),
                'message_watchdog_enabled': ParameterValue(
                    usb_message_watchdog, value_type=bool
                ),
                'validate_timestamp': ParameterValue(
                    usb_message_watchdog, value_type=bool
                ),
                'validate_sequence': ParameterValue(
                    usb_message_watchdog, value_type=bool
                ),
                'use_sim_time': use_sim_time,
            }],
        ),
    ])
