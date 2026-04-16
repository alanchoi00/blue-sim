from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import LaunchConfigurationEquals
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import (
    Command,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

# https://github.com/ArduPilot/ardupilot/blob/master/ArduSub/mode.h
VALID_MODES = frozenset(
    {
        "MANUAL",
        "STABILIZE",
        "ACRO",
        "ALT_HOLD",
        "AUTO",
        "GUIDED",
        "VELHOLD",
        "POSHOLD",
        "CIRCLE",
        "SURFACE",
    }
)


def generate_launch_description():
    use_sim = LaunchConfiguration("use_sim")
    use_rviz = LaunchConfiguration("use_rviz")
    flight_mode = LaunchConfiguration("flight_mode")
    gazebo_world_file = LaunchConfiguration("gazebo_world_file")

    declare_model = DeclareLaunchArgument(
        "model",
        choices=["bluerov2", "bluerov2_heavy", "bluerov2_reach"],
        description="BlueROV2 model variant (bluerov2 or bluerov2_heavy)",
    )
    declare_use_sim = DeclareLaunchArgument(
        "use_sim",
        default_value="true",
        description="Launch Gazebo + ArduSub SITL",
    )
    declare_use_rviz = DeclareLaunchArgument(
        "use_rviz",
        default_value="false",
        description="Open RViz",
    )
    declare_use_joy = DeclareLaunchArgument(
        "use_joy",
        default_value="false",
        description="Use ArduSub joystick teleoperation (joy_interface)",
    )
    declare_use_key = DeclareLaunchArgument(
        "use_key",
        default_value="false",
        description="Use keyboard for teleoperation",
    )
    declare_flight_mode = DeclareLaunchArgument(
        "flight_mode",
        default_value="ALT_HOLD",
        choices=list(VALID_MODES),
        description=(
            "ArduSub flight mode to set on startup. "
            "Valid: MANUAL, STABILIZE, ACRO, ALT_HOLD, AUTO, GUIDED, "
            "VELHOLD, POSHOLD, CIRCLE, SURFACE. "
            "For more details on flight modes, see: "
            "https://ardupilot.org/sub/docs/modes.html"
        ),
    )
    declare_use_ardusub = DeclareLaunchArgument(
        "use_ardusub",
        default_value="false",
        description="Launch ArduSub bridge and initialization nodes",
    )
    declare_gazebo_world_file = DeclareLaunchArgument(
        "gazebo_world_file",
        default_value=PathJoinSubstitution(
            [
                FindPackageShare("blue_description"),
                "gazebo/worlds/underwater.world",
            ]
        ),
        description="Path to Gazebo world file",
    )

    robot_description_heavy = Command(
        [
            "xacro ",
            PathJoinSubstitution(
                [
                    FindPackageShare("blue_control"),
                    "description/urdf/bluerov2_heavy.config.xacro",
                ]
            ),
            " use_sim:=",
            use_sim,
        ]
    )

    robot_description_standard = Command(
        [
            "xacro ",
            PathJoinSubstitution(
                [
                    FindPackageShare("blue_control"),
                    "description/urdf/bluerov2.config.xacro",
                ]
            ),
            " use_sim:=",
            use_sim,
        ]
    )

    bringup_heavy = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("blue_bringup"),
                    "launch/bluerov2_heavy/bluerov2_heavy.launch.yaml",
                ]
            )
        ),
        launch_arguments={
            "use_sim": use_sim,
            "use_rviz": use_rviz,
            "robot_description": robot_description_heavy,
            "gazebo_world_file": gazebo_world_file,
        }.items(),
        condition=LaunchConfigurationEquals("model", "bluerov2_heavy"),
    )

    bringup_standard = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("blue_bringup"),
                    "launch/bluerov2/bluerov2.launch.yaml",
                ]
            )
        ),
        launch_arguments={
            "use_sim": use_sim,
            "use_rviz": use_rviz,
            "robot_description": robot_description_standard,
            "gazebo_world_file": gazebo_world_file,
        }.items(),
        condition=LaunchConfigurationEquals("model", "bluerov2"),
    )

    teleop_keyboard = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("blue_teleop"),
                    "launch/keyboard.launch.py",
                ]
            )
        ),
        condition=LaunchConfigurationEquals("use_key", "true"),
    )
    teleop_joystick = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("blue_teleop"),
                    "launch/joystick.launch.yaml",
                ]
            )
        ),
        condition=LaunchConfigurationEquals("use_joy", "true"),
    )

    ardusub_init = Node(
        package="blue_sim",
        executable="ardusub_init",
        name="ardusub_init",
        output="screen",
        parameters=[{"flight_mode": flight_mode}],
        condition=LaunchConfigurationEquals("use_ardusub", "true"),
    )

    ardusub_bridge = Node(
        package="blue_sim",
        executable="ardusub_bridge",
        name="ardusub_bridge",
        output="screen",
        condition=LaunchConfigurationEquals("use_ardusub", "true"),
    )

    return LaunchDescription(
        [
            declare_model,
            declare_use_sim,
            declare_use_rviz,
            declare_use_key,
            declare_use_joy,
            declare_flight_mode,
            declare_gazebo_world_file,
            declare_use_ardusub,
            bringup_heavy,
            bringup_standard,
            teleop_keyboard,
            teleop_joystick,
            ardusub_init,
            ardusub_bridge,
        ]
    )
