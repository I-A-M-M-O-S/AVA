"""Start the canonical LiDAR and IMU preprocessing pipeline."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Build the shared sensor-processing launch description."""
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('scan_raw_topic', default_value='/scan_raw'),
        DeclareLaunchArgument('scan_topic', default_value='/scan'),
        DeclareLaunchArgument('imu_raw_topic', default_value='/imu/data_raw'),
        DeclareLaunchArgument('imu_topic', default_value='/imu/data'),
        Node(
            package='avaj_sensor_processing',
            executable='scan_preprocessor',
            namespace='sensors',
            name='lidar_preprocessor',
            output='screen',
            parameters=[{
                'input_topic': LaunchConfiguration('scan_raw_topic'),
                'output_topic': LaunchConfiguration('scan_topic'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }],
        ),
        Node(
            package='avaj_sensor_processing',
            executable='imu_preprocessor',
            namespace='sensors',
            name='imu_preprocessor',
            output='screen',
            parameters=[{
                'input_topic': LaunchConfiguration('imu_raw_topic'),
                'output_topic': LaunchConfiguration('imu_topic'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }],
        ),
    ])
