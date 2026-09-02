# CURRENT STATE — AVAJ RC-Car

**Canonical status date:** 2 September 2026, Europe/Berlin  
**Repository:** `/home/avaj/ros2_jazzy`  
**Branch observed:** `orin`  
**HEAD observed:** `7df2f36`  
**Scope:** repository and live-device inspection, build/tests, and an isolated
Gazebo/SLAM/control smoke test. No powered actuator test was performed.

This is the first file to read for the current implementation state. The
binding target architecture remains in [`AGENTS (1).md`](AGENTS%20(1).md). The
dependency-ordered work plan is
[`DEVELOPMENT_PLAN.md — AVAJ RC-Car.md`](DEVELOPMENT_PLAN.md%20%E2%80%94%20AVAJ%20RC-Car.md).
Historical operational details are in [`HANDOFF.md`](HANDOFF.md).

## 1. Executive status

The repository contains a useful ROS 2, sensor, simulation, SLAM and command
transport foundation. It does **not** yet contain a safe, real, autonomous
vehicle implementation.

Approximate maturity uses this scale: 0% absent, 25% foundation present, 50%
simulation end-to-end, 75% repeatable low-speed real tests, 100% acceptance
criteria passed.

| Capability | Approximate maturity | Current assessment |
|---|---:|---|
| Shared ROS/sensor/simulation foundation | 45% | Useful baseline; real state estimation and hardware safety are incomplete |
| One autonomous lap on a closed track | 25–30% | SLAM works in simulation; track model, saved-map localization and path follower are absent |
| Pylon gate and slalom | 10–15% | Camera interface exists; calibration and the perception-to-control chain are absent |
| Safe powered real vehicle platform | <20% | No matching ESP firmware, verified encoder path, physical E-stop or powered validation |

**Safety conclusion:** do not connect or energize propulsion or steering for
autonomous testing with the present repository state.

## 2. Repository and working-tree state

The working tree contains important modified, deleted and untracked work. It
must be treated as part of the current implementation even though it is not in
HEAD. Before editing, always run:

```bash
git status --short
git diff --stat
```

Known changes include the Ackermann-to-DriveRequest adapter and tests, the C++
`control_center` source relocation, launch updates, ROS graph documentation and
locally modified vendor repositories. Do not reset or clean the worktree
without explicit review.

There are two workspace-like trees. The active source tree used by the root
Compose setup is:

```text
/home/avaj/ros2_jazzy/workspace/src
```

Do not confuse it with the older nested `ros2_jazzy/workspace` copy.

## 3. Live hardware and services observed

`docker compose ps --all` and `lsusb` showed:

| Component | Live state | Meaning |
|---|---|---|
| BNO085 IMU service | Running | `/imu/data_raw`, `/imu/data` and `/imu/mag` path available |
| Sensor-processing service | Running | LiDAR and IMU preprocessors present |
| UC-852 camera | Container exited; USB device absent | Real camera not validated in this audit |
| STL27L LiDAR | Container exited; USB device absent | Real LiDAR not validated in this audit |
| ESP/USB serial | No `/dev/ttyUSB*` or `/dev/ttyACM*` observed | No ESP or actuator validation |
| Gazebo/SLAM/drive stack | Started only for the audit smoke test | Not a persistent live service |

The BNO085 remains physically attached on `/dev/i2c-7`. Its final mounting
orientation must be physically confirmed before real EKF fusion.

Short-lived `jazzy` containers can belong to terminal commands. Do not remove
interactive containers blindly; identify their process and owner first.

## 4. Implemented inventory

Own ROS packages under the active `workspace/src`:

```text
rc_car_interfaces
rc_car_usb_bridge
avaj_sensor_processing
avaj_car_control
control_center
avaj_slam
```

Vendor packages with local changes:

```text
bno08x_driver
ldlidar_stl_ros2
```

### 4.1 Sensor pipeline

Implemented canonical driver boundary:

```text
hardware or Gazebo -> /scan_raw     -> lidar_preprocessor -> /scan
hardware or Gazebo -> /imu/data_raw -> imu_preprocessor   -> /imu/data
hardware or Gazebo -> /camera/image_raw
```

The LiDAR preprocessor validates scan geometry and replaces invalid/out-of-range
samples with infinity. The IMU preprocessor rejects non-finite values. The full
topic contract is in [`docs/ros_graph.md`](docs/ros_graph.md).

Still missing or unverified:

- real LiDAR after the canonical topic migration;
- camera intrinsic calibration and rectification;
- final `camera_link -> camera_optical_frame` TF;
- verified IMU mounting, covariance and timestamps;
- common typed sensor diagnostics.

### 4.2 SLAM and state estimation

Implemented:

- `slam_toolbox` lifecycle launch for mutually exclusive real/simulation
  profiles;
- simulation TF bridges for Gazebo frame names;
- simulation EKF publishing canonical `odom -> base_link`;
- map-saving helper;
- experimental stock-Nav2 startup against online SLAM.

Not implemented:

- real encoder odometry or real IMU/encoder EKF;
- saved-map loading and localization;
- AMCL/map-server launch;
- `DISABLED/MAPPING/LOCALIZATION` lifecycle manager;
- measured localization and map-quality acceptance tests.

No saved track map was present under `workspace/maps` during the audit.

### 4.3 Command and USB pipeline

Implemented path:

```text
AckermannDriveStamped [m/s, rad]
        -> ackermann_to_drive_request
        -> DriveRequest [-100..100]
        -> drive_commander
        -> DriveCommand + sequence + enable
        -> USB bridge and/or Gazebo adapter
```

`drive_commander` invalidates cached commands on mode and enable transitions,
requires a fresh post-transition request and rejects invalid input. It remains
the only intended publisher of `/drive_commands`.

The USB bridge implements command CRC, validation, reconnect handling and an
incremental validated decoder for the synthetic V1 feedback contract. Typed
feedback messages exist for:

```text
/vehicle/status
/vehicle/actuator_status
/vehicle/encoders
```

Critical boundary: no matching ESP firmware exists. ACK meaning, owner state,
actuator truth, fault generation, encoder polarity/scaling and final timeouts
are not hardware-verified. See
[`docs/esp_feedback_protocol.md`](docs/esp_feedback_protocol.md).

### 4.4 Current autonomous controller

The C++ `control_center` is a simulation-oriented baseline. It consumes LiDAR
and filtered odometry, checks freshness and drive enable, applies a front
distance stop, steers toward greater LiDAR clearance, and publishes SI
Ackermann commands.

It is **not** a racing controller. It does not follow `/map` or the subscribed
racing-line topic. It has no track model, trajectory, lap completion or racing
supervisor.

The mode system still uses transitional strings such as `AUTONOMOUS`, `MANUAL`,
`TEST` and `DISABLED`. Typed requested/active `RACING` and `PYLON` modes are not
implemented.

### 4.5 Safety watchdog

The Jetson watchdog currently checks mainly topic arrival/freshness. It does
not yet validate:

- ESP connection, feedback freshness or ACK progression;
- ESP control owner, lock, arming and faults;
- encoder movement and plausibility;
- EKF health, covariance or pose jumps;
- localization confidence;
- mode-specific supervisor and trajectory health.

It must not be considered sufficient authorization for powered autonomy.

## 5. Goal 1 — one autonomous lap

Present foundation:

- simulated closed arena and Ackermann car;
- simulated LiDAR, IMU, camera and odometry;
- scan processing, simulation EKF and online SLAM;
- SI Ackermann command interface;
- basic reactive LiDAR motion.

Missing critical chain:

```text
validated encoder odometry + IMU
        -> real EKF
        -> reproducible mapping
        -> saved-map localization
        -> track-boundary extraction
        -> closed centerline
        -> conservative speed profile
        -> Pure Pursuit/Stanley follower
        -> racing supervisor and lap detection
        -> simulation and physical test gates
```

The first lap should use the centerline and a conservative constant or
curvature-based speed. Racing-line optimization is later work.

## 6. Goal 2 — pylon gates and slalom

Present foundation:

- real and simulated camera topics;
- Jetson Orin GPU;
- common Ackermann command adapter;
- architectural separation of PYLON from RACING.

Missing complete chain:

```text
camera calibration + rectification
        -> pylon dataset and labels
        -> detector
        -> bearing/range in base_link
        -> temporal tracking
        -> gate/slalom interpretation
        -> behavior planner
        -> local trajectory
        -> common path follower
        -> supervisor and fail-safe stop
```

The current Gazebo world has walls and a center island but no pylons, gates or
slalom scenarios. No pylon message, detector, dataset, planner or controller
package was found.

SLAM may provide global context; camera detections should drive local,
pylon-relative planning. Pylon perception must remain separate from racing.

## 7. Verification results

### 7.1 Build and tests

The following own packages were built and tested in the ROS Jazzy container:

```text
rc_car_interfaces
rc_car_usb_bridge
avaj_sensor_processing
avaj_car_control
control_center
avaj_slam
```

Results:

- all six packages built successfully;
- combined result: 64 tests, 63 passed, 1 failed;
- the failure was a USB bridge graph test observing a publisher from the
  shared DDS domain;
- rerun with isolated `ROS_DOMAIN_ID=231`: `rc_car_usb_bridge` passed 36/36;
- `avaj_car_control`: 18 drive-commander and 6 Ackermann-adapter tests passed;
- sensor-processing lint tests passed.

Interpretation: bridge logic passed in isolation, but CI/test invocation does
not yet guarantee ROS domain isolation.

### 7.2 Gazebo/SLAM/control smoke test

An isolated ROS domain started Gazebo headless, the ROS-Gazebo bridge, sensor
processing, simulation EKF, `slam_toolbox`, USB dry-run drive stack and
`control_center`.

Observed:

- `/odom` and `/odometry/filtered` published motion;
- the vehicle moved under LiDAR-gap control;
- `slam_toolbox` was the sole `/map` publisher;
- a map was generated at 0.05 m resolution, 516 × 317 cells;
- the controller produced low-speed SI Ackermann commands.

Not demonstrated: a closed lap, map/path following, saved-map localization,
pylon perception or any real actuator behavior.

New defects observed:

1. `slam_toolbox` repeatedly dropped scans because its message-filter queue was
   full. Mapping produced a map, but TF/timing/queue behavior needs diagnosis.
2. Several Python nodes threw invalid-context exceptions during Ctrl-C
   shutdown, including USB bridge shutdown stop and Ackermann adapter.
3. The first dry-run USB command could be rejected for a missing timestamp.

## 8. External tools/projects recommended for reuse

Preserve AVAJ topic and safety boundaries. External controllers must never
publish `/drive_commands` directly.

Adopt directly:

- ROS `camera_calibration` and `image_proc`;
- Nav2 `map_server`, `amcl` and lifecycle manager;
- existing `robot_localization` for the real EKF;
- ROS `diagnostic_updater` and `diagnostic_aggregator`;
- `rosbag2`, PlotJuggler and CVAT;
- `ros-tooling/action-ros-ci` with isolated ROS domain IDs.

Reuse behind AVAJ wrappers or as algorithm references:

- F1TENTH ROS 2 Pure Pursuit/localization examples;
- Nav2 Regulated Pure Pursuit and Collision Monitor with an explicit
  Twist/Ackermann adapter;
- TUMFTM `global_racetrajectory_optimization` after a valid centerline exists;
- NVIDIA Isaac ROS YOLOv8/RT-DETR after testing a JetPack-6-compatible release
  in a separate container;
- OpenCV projection/`solvePnP` for pylon bearing and range;
- ROS 2 Control Ackermann kinematics for odometry reference or a later ESP
  hardware interface.

Do not import a foreign full F1TENTH/VESC safety and actuator stack. Do not use
micro-ROS as a replacement for the ESP's independent owner state, watchdog and
actuator limits. Do not prioritize Autoware, MPC or minimum-time optimization
before the conservative baseline works.

## 9. Critical work order

### P0 — preserve and stabilize

1. Preserve/review the dirty working tree.
2. Add CI with unique ROS domain IDs.
3. Fix shutdown exceptions and initial timestamp rejection.
4. Diagnose repeated SLAM scan-filter queue drops.

### P1 — safe physical platform

1. Implement matching ESP firmware.
2. Implement and test `SAFE/MANUAL/JETSON` ownership.
3. Implement independent manual and Jetson timeouts.
4. Centralize actuator limits and safe handover.
5. Add a physical propulsion-disable/E-stop.
6. Bench-test disconnected actuators, then lifted vehicle only.

### P2 — real vehicle state

1. Bring up four encoder feedback channels.
2. Calibrate counts, polarity, radius and drivetrain ratio.
3. Implement four-wheel diagnostics and Ackermann odometry.
4. Confirm real sensor frames and IMU orientation.
5. Configure and validate the real EKF.
6. Connect typed ESP/ACK/encoder/EKF health to the watchdog.

### P3 — first autonomous lap

1. Validate and save a real SLAM map.
2. Implement exclusive saved-map localization.
3. Extract a closed centerline and track widths.
4. Implement a conservative Pure Pursuit follower.
5. Add racing supervisor, lap completion and failure handling.
6. Pass simulation, lifted-vehicle and very-low-speed ground gates.

### P3 in parallel — first pylon gate

1. Calibrate and rectify the camera.
2. Add Gazebo cone, gate and slalom scenarios.
3. Record and label a representative dataset.
4. Deploy a detector behind a typed `PylonDetections` interface.
5. Implement gate interpretation, local trajectory and stop-on-loss.
6. Reuse the common path follower and command adapter.
7. Implement slalom after reliable gate traversal.

## 10. Physical test gates

No later gate may bypass an earlier one.

| Gate | Required before entry |
|---|---|
| Electronics only | ESP firmware/protocol tests; actuators disconnected |
| Lifted vehicle | ESP timeout, owner arbitration, limits and handover proven |
| Very-low-speed ground | manual takeover, physical disable, encoders and Jetson timeout proven |
| Autonomous low speed | validated EKF, active watchdog, simulation controller test and rosbag |
| Racing speed | repeatable laps plus measured braking, steering, latency, localization and tracking error |

## 11. Next credible demonstrations

**Conservative autonomous lap:** one complete closed lap in simulation and then
at very low real speed using a saved map, valid localization and reference path,
with no safety bypass, no collision, bounded tracking error and a complete
rosbag.

**Pylon gate:** calibrated-camera detection of two pylons, semantic gate
interpretation, local trajectory and low-speed traversal while every layer
publishes inspectable output. Lost or ambiguous detections must cause a
controlled stop. Slalom is the subsequent target.

## 12. Update rule

When the implementation changes materially, update this file with:

- date and commit, including whether uncommitted work was included;
- component status change;
- exact build/test commands and results;
- environment: synthetic, simulation, bench, lifted, low-speed real or racing;
- remaining safety limitations and newly discovered failures.

Do not mark a component complete based only on source presence. Record runtime
and hardware validation separately.

