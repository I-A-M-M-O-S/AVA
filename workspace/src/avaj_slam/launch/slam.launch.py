import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, EmitEvent, OpaqueFunction,
                            RegisterEventHandler)
from launch.events import matches_action
from lifecycle_msgs.msg import Transition
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode, Node
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState


def generate_launch_description():
    share = get_package_share_directory('avaj_slam')
    urdf = os.path.join(share, 'urdf', 'avaj_car.urdf')
    slam_params = os.path.join(share, 'config', 'slam_params.yaml')
    ekf_params = os.path.join(share, 'config', 'ekf_sim.yaml')

    simulation = LaunchConfiguration('simulation')
    use_rviz = LaunchConfiguration('rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')

    robot_description = open(urdf, encoding='utf-8').read()

    def validate_profiles(context):
        simulation_enabled = simulation.perform(context).lower() == 'true'
        real_value = LaunchConfiguration('real').perform(context)
        real_enabled = real_value.lower() == 'true'
        if simulation_enabled and real_enabled:
            raise RuntimeError(
                'simulation and real are mutually exclusive launch profiles'
            )
        return []

    slam_sim = LifecycleNode(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        namespace='',
        parameters=[slam_params, {'use_sim_time': use_sim_time}],
        condition=IfCondition(simulation),
        output='screen')

    slam_real = LifecycleNode(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        namespace='',
        parameters=[slam_params, {'use_sim_time': use_sim_time}],
        condition=IfCondition(LaunchConfiguration('real')),
        output='screen')

    return LaunchDescription([
        DeclareLaunchArgument(
            'simulation', default_value='false',
            description='Simulation topics and simulated odometry'),
        DeclareLaunchArgument(
            'real', default_value='false',
            description='Reales Fahrzeug mit /scan und realer Odometrie'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use the Gazebo /clock topic'),
        DeclareLaunchArgument(
            'rviz', default_value='false',
            description='Start RViz2'),
        OpaqueFunction(function=validate_profiles),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{
                'robot_description': robot_description,
                'use_sim_time': use_sim_time,
            }],
            output='screen'),

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='sim_odom_frame_bridge',
            arguments=[
                '--x', '0.0', '--y', '0.0', '--z', '0.0',
                '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
                '--frame-id', 'odom',
                '--child-frame-id', 'avaj_car/odom',
            ],
            condition=IfCondition(simulation),
            output='screen'),

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='sim_base_frame_bridge',
            arguments=[
                '--x', '0.0', '--y', '0.0', '--z', '0.0',
                '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
                '--frame-id', 'base_link',
                '--child-frame-id', 'avaj_car/base_link',
            ],
            condition=IfCondition(simulation),
            output='screen'),

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='sim_lidar_frame_bridge',
            arguments=[
                '--x', '0.18', '--y', '0.0', '--z', '0.059',
                '--yaw', '-1.57079632679',
                '--frame-id', 'base_link',
                '--child-frame-id', 'avaj_car/lidar_link/stl27_sim',
            ],
            condition=IfCondition(simulation),
            output='screen'),

        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            parameters=[ekf_params, {'use_sim_time': use_sim_time}],
            remappings=[('odometry/filtered', '/odometry/filtered')],
            condition=IfCondition(simulation),
            output='screen'),

        slam_sim,
        slam_real,

        EmitEvent(
            event=ChangeState(
                lifecycle_node_matcher=matches_action(
                    slam_sim),
                transition_id=Transition.TRANSITION_CONFIGURE),
            condition=IfCondition(simulation)),

        RegisterEventHandler(
            OnStateTransition(
                target_lifecycle_node=slam_sim,
                start_state='configuring',
                goal_state='inactive',
                entities=[EmitEvent(event=ChangeState(
                    lifecycle_node_matcher=matches_action(slam_sim),
                    transition_id=Transition.TRANSITION_ACTIVATE))]),
            condition=IfCondition(simulation)),

        EmitEvent(
            event=ChangeState(
                lifecycle_node_matcher=matches_action(
                    slam_real),
                transition_id=Transition.TRANSITION_CONFIGURE),
            condition=IfCondition(LaunchConfiguration('real'))),

        RegisterEventHandler(
            OnStateTransition(
                target_lifecycle_node=slam_real,
                start_state='configuring',
                goal_state='inactive',
                entities=[EmitEvent(event=ChangeState(
                    lifecycle_node_matcher=matches_action(slam_real),
                    transition_id=Transition.TRANSITION_ACTIVATE))]),
            condition=IfCondition(LaunchConfiguration('real'))),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            parameters=[{'use_sim_time': use_sim_time}],
            condition=IfCondition(use_rviz),
            output='screen'),
    ])
