# blue-sim

Self-contained ROS 2 / Gazebo simulation environment for BlueROV2, forked from
[Robotic-Decision-Making-Lab/blue](https://github.com/Robotic-Decision-Making-Lab/blue).

This fork ships pre-built Docker images that include Gazebo Harmonic, ArduPilot SITL,
MAVROS, and `ardupilot_gazebo` - all built from source with no dependency on external
maintained images. It is developed as part of UNSW undergraduate thesis research on
autonomous underwater vehicle docking, and is intended as a simulation harness for
downstream projects (e.g. [bluerov2-docking](https://github.com/alanchoi00/bluerov2-docking)).

## Supported Distributions

| ROS 2 | Ubuntu | Status |
|---|---|---|
| [Jazzy](https://github.com/alanchoi00/blue-sim/pkgs/container/blue-sim) | 24.04 | Supported |
| [Humble](https://github.com/alanchoi00/blue-sim/pkgs/container/blue-sim-humble) | 22.04 | Discontinued |

**Why Humble is no longer supported:** The previous Humble images were derived from
`ghcr.io/robotic-decision-making-lab/blue:humble-*`, an externally-maintained image last updated
in 2024. The bundled `ardusub_driver` became stale and incompatible with current MAVROS and ArduSub
SITL versions. Updating it would require maintaining a full fork of the upstream build pipeline.
The new Jazzy images are fully self-contained, built from `ros:jazzy-ros-base`, and have no
external image dependency.

## Supported ROV Models

| Model | Support | Collision |
|---|---|---|
| `bluerov2_heavy` | Full | Detailed mesh collision + separate buoyancy volume; physical parameters from von Benzon et al. 2022 |
| `bluerov2` | Supported | Simple box |
| `bluerov2_heavy_reach` | Not tested | Simple box |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Compose v2
- A working display (X11 or Wayland) for Gazebo GUI
- **Dev Container path:** [VS Code](https://code.visualstudio.com/) with the
  [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension
- [Optional] **NVIDIA GPU:** additionally requires the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

## Setup

### Option A - VS Code Dev Container (Recommended)

Dev containers provide an integrated editor environment with pre-configured extensions, linters,
and pre-commit hooks.

1. Clone the repo and open it in VS Code.
2. When prompted, select **Reopen in Container** (or run the command `Dev Containers: Reopen in Container`).
   - Select `.devcontainer/nouveau/` for AMD/Intel/Nouveau GPU
   - Select `.devcontainer/nvidia/` for NVIDIA GPU
3. Wait for the container image to build (first time only - pulls `jazzy-desktop` base image and
   installs dependencies).
4. Open a terminal inside the container and build the workspace:
   ```bash
   cd ~/ws_blue && colcon build --symlink-install
   source install/setup.bash
   ```

### Option B - Docker Compose

**Nouveau / AMD / Intel:**
```bash
# Pull pre-built image (or replace 'pull' with 'up --build' to build locally)
docker compose -f .docker/compose/nouveau-desktop.yaml pull
docker compose -f .docker/compose/nouveau-desktop.yaml up -d
docker compose -f .docker/compose/nouveau-desktop.yaml exec blue bash
```

**NVIDIA:**
```bash
docker compose -f .docker/compose/nvidia-desktop.yaml pull
docker compose -f .docker/compose/nvidia-desktop.yaml up -d
docker compose -f .docker/compose/nvidia-desktop.yaml exec blue bash
```

Once inside the container, source the workspace:
```bash
source ~/ws_blue/install/setup.bash
```

## Running the Simulation

### Basic launch

```bash
ros2 launch blue_sim sim.launch.py model:=bluerov2_heavy
```

### Launch arguments

| Argument | Default | Description |
|---|---|---|
| `model` | *(required)* | ROV model: `bluerov2` or `bluerov2_heavy` |
| `use_sim` | `true` | Launch Gazebo and ArduSub SITL |
| `use_rviz` | `false` | Open RViz |
| `use_joy` | `false` | Enable joystick teleoperation |
| `use_key` | `false` | Enable keyboard teleoperation |
| `use_ardusub` | `false` | Launch ArduSub init + bridge nodes (arms vehicle on startup, subscribes to `cmd_vel`) |
| `flight_mode` | `ALT_HOLD` | ArduSub flight mode set on startup - only takes effect when `use_ardusub:=true` |
| `gazebo_world_file` | `blue_description/gazebo/worlds/underwater.world` | Path to Gazebo world SDF/world file |

### Examples

**With ArduSub control** (arm on startup, bridge `cmd_vel` to RC override):
```bash
ros2 launch blue_sim sim.launch.py model:=bluerov2_heavy use_ardusub:=true
```

**With joystick teleoperation:**
```bash
ros2 launch blue_sim sim.launch.py model:=bluerov2_heavy use_joy:=true
```

**With a custom world file:**
```bash
ros2 launch blue_sim sim.launch.py model:=bluerov2_heavy \
  gazebo_world_file:=/path/to/your/world.sdf
```

**Standard ROV, custom world, keyboard teleop:**
```bash
ros2 launch blue_sim sim.launch.py model:=bluerov2 \
  gazebo_world_file:=/path/to/your/world.sdf \
  use_key:=true
```

## Downstream Usage

Downstream workspaces pull the blue-sim Docker image as their base environment:

| GPU | Image |
|---|---|
| Nouveau / AMD / Intel | `ghcr.io/alanchoi00/blue-sim:jazzy-desktop` |
| NVIDIA | `ghcr.io/alanchoi00/blue-sim:jazzy-desktop-nvidia` |

It is recommended to keep downstream packages in a separate workspace (e.g. `~/ws_<app>`)
rather than adding them to the image's `~/ws_blue` workspace. Source `ws_blue` first,
then build and source your own workspace on top:

```bash
source ~/ws_blue/install/setup.bash
cd ~/ws_<app> && colcon build --symlink-install
source ~/ws_<app>/install/setup.bash
```

blue-sim packages are then available as dependencies, and downstream launch files can
reference them via `FindPackageShare("blue_sim")`. blue-sim is consumed via
`IncludeLaunchDescription`. The typical pattern is to write a thin wrapper launch file
that fixes the model, world file, and ArduSub settings for your project, and
exposes only the arguments relevant to your use case.

[bluerov2-docking](https://github.com/alanchoi00/bluerov2-docking) is an example of this -
its `sim` package wraps blue-sim with `bluerov2_heavy`, a custom ocean world, and
`POSHOLD` flight mode pre-configured:

```python
IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        PathJoinSubstitution([FindPackageShare("blue_sim"), "launch/sim.launch.py"])
    ),
    launch_arguments={
        "model": "bluerov2_heavy",
        "use_ardusub": LaunchConfiguration("use_ardusub"),
        "flight_mode": LaunchConfiguration("flight_mode"),
        "gazebo_world_file": [
            PathJoinSubstitution([FindPackageShare("sim"), "worlds"]),
            "/ocean.world",
        ],
    }.items(),
)
```

The `gazebo_world_file` argument is the primary extension point - pass a world file from
your own package to add custom models, lighting, or ocean conditions on top of the base
simulation.

## References

von Benzon, M.; Sorensen, F.F.; Uth, E.; Emery, A.; Jouffroy, J.; Leth, S. An Open-Source
Benchmark Simulator: Control of a BlueROV2 Underwater Robot. *J. Mar. Sci. Eng.* **2022**, *10*, 1898.
https://www.mdpi.com/2077-1312/10/12/1898
