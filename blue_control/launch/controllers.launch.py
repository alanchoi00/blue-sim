from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, TextSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    args = [
        DeclareLaunchArgument(
            "prefix",
            default_value="",
            description=(
                "The prefix of the model. This is useful for multi-robot setups."
                " Expected format '<prefix>/'."
            ),
        ),
        DeclareLaunchArgument(
            "use_sim",
            default_value="false",
            description="Launch the Gazebo + ArduSub simulator.",
        ),
    ]

    message_transformer = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("message_transforms"),
                "launch",
                "message_transforms.launch.py",
            ])
        ),
        launch_arguments={
            "parameters_file": PathJoinSubstitution([
                FindPackageShare("blue_control"),
                "config",
                "controller_transforms.yaml",
            ]),
            "ns": TextSubstitution(text="control_integration"),
        }.items(),
    )

    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="both",
        parameters=[
            PathJoinSubstitution([
                FindPackageShare("blue_control"),
                "config",
                "bluerov2_controllers.yaml",
            ]),
        ],
        remappings=[
            ("/controller_manager/robot_description", "/robot_description"),
        ],
    )

    velocity_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "integral_sliding_mode_controller",
            "--controller-manager",
            ["", "controller_manager"],
        ],
    )

    thruster_spawners = [
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=[
                f"thruster{i + 1}_controller",
                "--controller-manager",
                ["", "controller_manager"],
            ],
        )
        for i in range(6)
    ]

    delay_thruster_spawners = []
    for i, thruster_spawner in enumerate(thruster_spawners):
        if not len(delay_thruster_spawners):
            delay_thruster_spawners.append(thruster_spawner)
        else:
            delay_thruster_spawners.append(
                RegisterEventHandler(
                    event_handler=OnProcessExit(
                        target_action=thruster_spawners[i - 1],
                        on_exit=[thruster_spawner],
                    )
                )
            )

    tam_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "thruster_allocation_matrix_controller",
            "--controller-manager",
            ["", "controller_manager"],
        ],
    )

    delay_tam_after_thrusters = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=thruster_spawners[-1],
            on_exit=[tam_controller_spawner],
        )
    )

    delay_velocity_after_tam = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=tam_controller_spawner,
            on_exit=[velocity_controller_spawner],
        )
    )

    return LaunchDescription([
        *args,
        message_transformer,
        controller_manager,
        *delay_thruster_spawners,
        delay_tam_after_thrusters,
        delay_velocity_after_tam,
    ])
