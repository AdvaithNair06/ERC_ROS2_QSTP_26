import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    model = LaunchConfiguration('model').perform(context)  # burger / waffle / waffle_pi

    pkg_share = get_package_share_directory('turtlebot3_gz_sim')
    tb3_description_share = get_package_share_directory('turtlebot3_description')

    # robot_state_publisher: static/kinematic TF tree, one URDF per model
    robot_description_path = os.path.join(
        tb3_description_share, 'urdf', f'turtlebot3_{model}.urdf'
    )
    with open(robot_description_path, 'r') as f:
        robot_description_content = f.read()

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'robot_description': robot_description_content,
        }],
    )

    # Spawn the robot straight from our gz-sim-native model.sdf for this model
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-file', os.path.join(pkg_share, 'models', f'turtlebot3_{model}', 'model.sdf'),
            '-name', 'turtlebot3',
            '-x', '0.0', '-y', '0.0', '-z', '0.05',
        ],
        output='screen',
    )

    return [robot_state_publisher, spawn_robot]


def generate_launch_description():

    pkg_share = get_package_share_directory('turtlebot3_gz_sim')
    tb3_gazebo_share = get_package_share_directory('turtlebot3_gazebo')  # for meshes only
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    world_file_name = LaunchConfiguration('world', default='empty.sdf')
    world_path = PathJoinSubstitution([pkg_share, 'worlds', world_file_name])

    world_arg = DeclareLaunchArgument(
        'world',
        default_value='empty.sdf',
        description='Name of the Gazebo world file to load (e.g., obstacle.sdf)',
    )

    model_arg = DeclareLaunchArgument(
        'model',
        default_value='burger',
        description='TurtleBot3 model: burger, waffle, waffle_pi',
    )

    # Meshes for the tb3 model (turtlebot3_common) live in the classic
    # turtlebot3_gazebo package; our own model.sdf files live in this package.
    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.path.join(pkg_share, 'models') + ':' +
        os.path.join(tb3_gazebo_share, 'models'),
    )

    # Bring up the Gazebo Fortress server + client via ros_gz_sim
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': [world_path, ' -r']}.items(),
    )

    # Bridge gz <-> ROS 2 topics (cmd_vel, odom, tf, scan, imu, clock,
    # camera - only waffle/waffle_pi actually publish the camera topics)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '--ros-args',
            '-p', f"config_file:={os.path.join(pkg_share, 'config', 'tb3_bridge.yaml')}",
        ],
        output='screen',
    )

    # DiffDrive doesn't animate the wheel joints on its own, so publish
    # zeroed joint states for the two wheel joints (fine for nav/teleop;
    # swap for the ignition-gazebo-joint-state-publisher-system + a bridge
    # entry if you need the wheels to visually spin in RViz).
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'rate': 30,
        }],
    )

    return LaunchDescription([
        world_arg,
        model_arg,
        gz_resource_path,
        gz_sim,
        bridge,
        joint_state_publisher,
        OpaqueFunction(function=launch_setup),
    ])
