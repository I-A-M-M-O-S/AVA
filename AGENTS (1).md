# AGENTS.md — AVAJ RC-Car

## 1. Purpose of this file

This file defines the architectural and implementation rules for AI coding agents working on the AVAJ autonomous 1:10 RC-car project.

The goal is not to build a minimal demo. The software is intended to become a robust, modular and measurable autonomous vehicle stack that can later be transferred from simulation to the real vehicle.

When modifying the repository, treat this document as an architectural contract.

If existing code conflicts with this document:

1. Inspect and understand the existing implementation first.
2. Do not silently rewrite large parts of the system.
3. Preserve working interfaces where practical.
4. Propose or implement migrations in small, testable steps.
5. Safety-relevant behavior always has priority over convenience or compatibility.

---

# 2. Project goal

The vehicle has three user-visible operating modes:

- `MANUAL`
- `RACING`
- `PYLON`

Additionally, the system must support a safe disabled state:

- `DISABLED` / `SAFE`

The two autonomous modes are intentionally separate programs.

## RACING

The vehicle first records a track using LiDAR/SLAM, builds a track model, calculates an optimized racing line and velocity profile, and then attempts to drive the known track as fast as safely possible.

The racing stack is map-based, predictive and optimized for lap time.

Typical processing chain:

```text
LiDAR + IMU + wheel encoders
        ↓
state estimation / TF
        ↓
SLAM / stored map
        ↓
track model
        ↓
racing-line optimization
        ↓
speed profile
        ↓
time/space trajectory
        ↓
race controller
        ↓
DriveRequest
```

## PYLON

The vehicle reacts online to pylons detected by the front camera.

Examples:

- drive through a gate formed by two pylons;
- slalom around a row of pylons;
- react to individual pylons or predefined visual arrangements.

The pylon stack is primarily camera-based and reactive/local.

Typical processing chain:

```text
camera
  ↓
calibration / image processing / ML
  ↓
pylon detection
  ↓
scene interpretation
  ↓
behavior planning
  ↓
local trajectory
  ↓
pylon controller
  ↓
DriveRequest
```

## MANUAL

Manual driving does **not** go through the Jetson control loop.

The ESP32 is the only communication-capable low-level vehicle device and directly receives and processes manual driving commands.

Do not implement this path:

```text
manual controller → ESP32 → Jetson → ESP32 → actuators
```

The correct design is:

```text
manual controller → ESP32 → actuator arbitration → motor/servo
                                ↑
                         Jetson DriveCommand
```

When manual control is active, the ESP32 must block Jetson actuator commands independently of the Jetson software state.

---

# 3. Core architectural rules

These rules are mandatory unless explicitly changed by the project owners.

## 3.1 The ESP32 has final actuator authority

`drive_commander` is the final authority for **Jetson-generated** commands only.

It is **not** the final authority over the physical actuators.

Final actuator ownership is decided on the ESP32.

ESP32 control-owner states:

```text
SAFE
JETSON
MANUAL
```

Rules:

- `MANUAL` has priority over `JETSON`.
- While `MANUAL` is active, Jetson motion commands must be rejected by the ESP32.
- Loss of the active control source must lead to `SAFE`.
- Never automatically fall back from a failed source to another source.
- A manual-controller timeout must not automatically return control to the Jetson.
- A Jetson timeout must not automatically enable manual control.

## 3.2 No automatic source takeover

Example:

```text
MANUAL active
manual controller disappears
        ↓
SAFE
```

Not:

```text
MANUAL active
manual controller disappears
        ↓
JETSON automatically takes over
```

A new source must be explicitly and safely armed.

## 3.3 Internal autonomous control uses physical units

Do not design racing or pylon control algorithms around normalized actuator values such as:

```text
speed = 73
steering = -42
```

Controllers should use SI/vehicle-level quantities where possible, for example:

```text
speed             [m/s]
steering_angle    [rad]
acceleration      [m/s²]
steering_rate     [rad/s]
```

Only a late adapter layer converts physical commands to the normalized low-level `DriveRequest` / `DriveCommand` representation expected by the ESP32.

This separation is required for:

- MPC;
- vehicle-dynamics limits;
- calibration;
- simulation/real-hardware portability;
- proper logging and evaluation.

## 3.4 RACING and PYLON are separate autonomous programs

They may share infrastructure, utilities, controllers or message types, but must not be implemented as one large monolithic planner with mode-specific `if` branches everywhere.

Preferred structure:

```text
                 autonomy_manager
                    /          \
                   /            \
          racing_supervisor   pylon_supervisor
                 |                  |
          racing stack          pylon stack
                 \                  /
                  \                /
                   common control
```

## 3.5 Shared infrastructure should remain reusable

Candidates for shared components include:

- ROS 2 messages;
- TF;
- EKF/state estimation;
- encoder odometry;
- USB communication;
- diagnostics;
- logging;
- safety watchdogs;
- trajectory/controller interfaces;
- vehicle model and calibration parameters;
- actuator-command adapters.

Do not duplicate these inside both autonomous stacks unless there is a technical reason.

---

# 4. Target architecture

## 4.1 Physical sensors

Planned/known sensors:

- STL27L / STL27 360° LiDAR
- BNO085 IMU
- Arducam UC-852 front camera
- four wheel encoders
- NVIDIA Jetson as high-level computer
- ESP32 as low-level communications/control device

The real sensor layer should expose ROS topics through dedicated drivers/bridges.

Do not make control algorithms depend directly on hardware APIs when a ROS interface can be used instead.

---

# 5. Sensor preprocessing

## LiDAR

Preferred pipeline:

```text
LiDAR driver
   ↓
/scan_raw
   ↓
laser_filters / lidar preprocessing
   ↓
/scan
```

Responsibilities may include:

- range filtering;
- invalid-point removal;
- optional angular masking;
- timestamp validation;
- frame assignment;
- diagnostics.

The filtered scan may be consumed by:

- SLAM;
- localization;
- track-model construction;
- obstacle/safety logic;
- optional Nav2 tools.

## IMU

Preferred pipeline:

```text
BNO085
  ↓
/imu/data_raw
  ↓
Madgwick or equivalent preprocessing
  ↓
/imu/data
  ↓
EKF
```

Do not fuse data blindly. Validate timestamps, units, frame conventions and covariance.

## Camera

Preferred pipeline:

```text
camera driver
   ↓
/camera/image_raw
   ↓
camera calibration / rectification
   ↓
vision/perception
```

The camera has at least two possible purposes:

1. pylon detection and semantic scene interpretation;
2. optional visual odometry/localization support.

Do not couple pylon detection to the racing stack.

## Wheel encoders

The physical encoders connect to the ESP32.

Preferred path:

```text
wheel encoders
    ↓
ESP32
    ↓
bidirectional USB protocol
    ↓
/wheel/encoders
    ↓
encoder_odometry
    ↓
/wheel/odometry
    ↓
EKF
```

Four encoders should remain individually available whenever possible so that later software can detect:

- wheel slip;
- locked wheels;
- left/right inconsistencies;
- driven/non-driven wheel differences.

Avoid reducing all four wheel signals to one speed value too early.

---

# 6. State estimation and TF

The target structure is:

```text
wheel odometry ──┐
                 ├── robot_localization EKF ──> odom -> base_link
IMU ─────────────┤
                 │
optional VIO ────┘
```

`robot_state_publisher` is responsible for static/kinematic sensor-frame relationships such as:

```text
base_link -> lidar_link
base_link -> camera_link
base_link -> imu_link
```

The TF architecture should maintain the standard conceptual split:

```text
map -> odom -> base_link -> sensor frames
```

Local state estimation owns:

```text
odom -> base_link
```

Global localization/mapping owns:

```text
map -> odom
```

Do not allow multiple active publishers for the same transform.

---

# 7. Mapping and localization modes

SLAM and AMCL/global localization must not publish `map -> odom` at the same time.

Use an explicit localization-mode manager or lifecycle orchestration.

Required states:

```text
DISABLED
MAPPING
LOCALIZATION
```

## MAPPING

```text
slam_toolbox: ACTIVE
AMCL:         INACTIVE
map_server:   optional/inactive as appropriate
```

## LOCALIZATION

```text
slam_toolbox: INACTIVE
map_server:   ACTIVE
AMCL:         ACTIVE
```

## DISABLED

Both global localization providers are inactive.

This exclusivity should be enforced architecturally, not merely documented in comments.

---

# 8. Racing program

The racing stack is its own program supervised by a `racing_supervisor` or equivalent node.

Recommended internal states:

```text
IDLE
MAPPING
TRACK_BUILD
OPTIMIZATION
READY
RACING
FAULT
```

Exact names may change, but state transitions must be explicit and observable.

## 8.1 Mapping phase

The first purpose of the racing program is to record a usable representation of the track.

Typical flow:

```text
filtered LiDAR + state estimate
        ↓
slam_toolbox
        ↓
map
```

Mapping must not immediately be conflated with race-line calculation.

## 8.2 Track Model Builder

A generic occupancy map is not yet a racing track model.

Create a separate track-model representation.

Inputs may include:

- occupancy map;
- filtered LiDAR;
- vehicle pose/state;
- TF;
- optional camera-derived semantic features.

The track model should eventually represent at least:

- left boundary;
- right boundary;
- centerline;
- track width;
- curvature;
- driving direction;
- whether the course is open or closed;
- reference frame, normally `map`;
- timestamp/version;
- confidence/uncertain sections where useful.

Keep this model independent from a specific racing-line optimizer.

## 8.3 Racing-line optimizer

The racing-line optimizer consumes the track model and produces an optimized geometric line.

Potential optimization targets include:

- lap time;
- curvature;
- minimum curvature change;
- stability margins;
- boundary distance;
- physically feasible cornering.

This component may be offline or relatively slow.

It does not need to run at controller frequency.

## 8.4 Speed-profile planner

The speed profile is separate from the geometric racing line.

It should eventually account for:

- curvature;
- maximum lateral acceleration;
- acceleration capability;
- braking capability;
- speed limits;
- tire/track constraints;
- vehicle-specific limits.

The profile should be recomputable when vehicle limits change without rebuilding the entire map.

## 8.5 Trajectory generator

The trajectory generator converts racing line + speed profile into the reference consumed by the controller.

A useful trajectory representation may include:

```text
x
y
yaw
curvature
velocity
acceleration
time or arc length
```

Do not reduce this prematurely to a list of XY waypoints.

## 8.6 Race controller

Possible controllers:

- Pure Pursuit for early integration;
- Stanley as another baseline if useful;
- MPC for advanced racing control.

The controller should run in physical units and emit a vehicle-level command, preferably Ackermann-like.

Typical output:

```text
speed [m/s]
steering_angle [rad]
acceleration [m/s²] optional
steering_angle_velocity [rad/s] optional
```

Controller loop rate should be chosen based on real timing measurements. A target on the order of 50–100 Hz may be reasonable later, but do not hardcode this assumption without measurement.

---

# 9. Pylon program

The pylon stack is independent from the racing stack and supervised by a `pylon_supervisor` or equivalent node.

The main chain is:

```text
camera
  ↓
vision / ML
  ↓
pylon detection
  ↓
scene interpretation
  ↓
behavior planner
  ↓
local trajectory generator
  ↓
pylon controller
```

Recommended behaviors include:

```text
GATE
SLALOM
SINGLE_PYLON
STOP
UNKNOWN
```

Do not make the controller infer behavior directly from raw image detections.

Keep these layers separate:

1. **Detection** — where are the pylons?
2. **Scene interpretation** — what arrangement do they form?
3. **Behavior planning** — what should the vehicle do?
4. **Trajectory generation** — what path should be followed locally?
5. **Control** — what steering/speed is required now?

This separation is important for testing each stage independently.

The pylon stack may reuse the EKF vehicle state and shared controller infrastructure.

It does not require SLAM to be in its critical path unless a later feature explicitly needs it.

---

# 10. Optional Nav2 use

Nav2 may be used as a tool for generic/slow navigation, development or testing, but it is **not** one of the primary user-visible driving programs unless explicitly added later.

Do not force the racing problem into Nav2.

If Nav2 is used:

- use an Ackermann-compatible motion/controller configuration;
- do not simply scale `Twist.angular.z` into steering percentage;
- perform proper kinematic conversion;
- account for near-zero velocity, reverse, steering limits and steering-rate limits;
- keep Nav2 isolated from the dedicated race and pylon stacks.

---

# 11. Autonomy mode management

The user selects the desired operating mode through the web interface.

The selection reaches the ESP32 first and is then communicated to the Jetson.

Top-level requested modes:

```text
DISABLED
MANUAL
RACING
PYLON
```

Use typed protocol fields/enums rather than free-form strings in production code.

The conceptual flow is:

```text
Web UI
  ↓
ESP32
  ↓
USB protocol
  ↓
Jetson autonomy_manager
```

## Requested mode vs active mode

Always distinguish between:

```text
requested_mode
active_mode
```

Example:

```text
requested_mode = RACING
active_mode    = DISABLED
reason         = LIDAR_UNAVAILABLE
```

or:

```text
requested_mode = RACING
active_mode    = RACING
racing_state   = MAPPING
```

Do not report a mode as active merely because the user requested it.

The web UI should eventually be able to show subsystem readiness and current autonomous sub-state.

---

# 12. Manual control and Jetson lock

When `MANUAL` is active:

- the ESP32 owns the actuators;
- the ESP32 sets `jetson_locked = true`;
- Jetson-generated actuator commands are rejected on the ESP32;
- the Jetson must also stop/disable command generation as a second layer;
- manual control must continue to work even if the high-level ROS stack is unavailable, as far as the low-level hardware design permits.

The lock is a state, not a one-shot message.

The ESP should periodically report status including at least conceptually:

```text
control_owner
jetson_locked
manual_alive
last_jetson_sequence
last_jetson_command_result
fault_code
motor_enabled
```

Exact message schema may differ, but avoid JSON/string status messages for permanent interfaces.

---

# 13. Safe handover rules

Manual takeover should be able to preempt Jetson control quickly.

Returning control from MANUAL to JETSON must be deliberate and safe.

Do not reactivate an old cached Jetson command.

A safe transition should conceptually require:

1. manual source becomes neutral/released;
2. ESP enters a neutral/safe transition state;
3. Jetson reports healthy autonomous state;
4. a fresh Jetson command with a valid timestamp/sequence is received;
5. ownership is explicitly switched to `JETSON`;
6. only then may actuation resume.

Old or stale commands must never become active after a mode change.

---

# 14. Jetson command pipeline

Both autonomous programs should converge on a common late-stage command pipeline.

Preferred structure:

```text
Racing controller ──┐
                    ├── autonomy safety/limits
Pylon controller ───┘
          ↓
physical/SI command adapter
          ↓
drive_commander
          ↓
/drive_commands
          ↓
USB bridge
          ↓
ESP32
```

`drive_commander` must remain the only Jetson node that publishes the final `/drive_commands` interface.

Do not allow arbitrary planning/control nodes to publish directly to the ESP command topic.

---

# 15. DriveRequest and DriveCommand

There are two conceptually different command layers.

## High-level / physical command

Controllers should preferably output an Ackermann/vehicle command in SI units.

Use an existing suitable ROS message such as `ackermann_msgs/AckermannDriveStamped` where practical, or define a strongly typed equivalent if required.

## Low-level DriveRequest / DriveCommand

The current low-level command concept uses normalized values:

```text
header.stamp
sequence
speed       -100 .. +100
steering    -100 .. +100
enabled
```

Semantics:

- `speed = -100`: maximum configured reverse request
- `speed = 0`: stop/neutral
- `speed = +100`: maximum configured forward request
- `steering = -100`: maximum configured left steering
- `steering = 0`: straight
- `steering = +100`: maximum configured right steering
- `enabled`: software drive enable

Keep actuator calibration out of racing/pylon controllers.

The conversion to normalized command values belongs in a dedicated adapter/command layer.

The final conversion to electrical PWM belongs on the ESP32.

---

# 16. drive_commander behavior

The existing implementation may currently know modes similar to:

```text
AUTONOMOUS
MANUAL
TEST
DISABLED
```

The target design should migrate toward a cleaner separation where manual ownership is handled by the ESP and autonomous Jetson sources are explicit.

Target Jetson-level modes should support at least:

```text
RACING
PYLON
TEST
DISABLED
```

If a temporary compatibility `AUTONOMOUS` mode exists, do not delete it blindly. Migrate call sites and tests first.

`drive_commander` responsibilities:

- accept only approved Jetson command sources;
- select the active Jetson source according to mode;
- reject inactive-source commands;
- validate freshness;
- validate ranges;
- honor software safety enable;
- generate monotonic command sequence numbers;
- publish the final `/drive_commands` message;
- publish diagnostics/status for what source is selected and why commands are rejected.

On every mode/source change:

- invalidate cached commands;
- force a neutral command / safe transition as required;
- require a fresh command from the new source.

---

# 17. Safety architecture

Safety is layered.

## 17.1 Jetson safety watchdog

The Jetson `safety_watchdog` decides whether autonomous drive is allowed.

It should eventually monitor:

- LiDAR freshness/health when required by active mode;
- camera/perception health when required by PYLON;
- IMU freshness;
- encoder freshness and plausibility;
- EKF state/diagnostics;
- USB/ESP connection;
- ACK progression;
- hardware fault status;
- active autonomous supervisor health;
- controller heartbeat;
- current mode;
- selected command source.

A fresh topic is not enough to prove that state estimation is healthy.

Check where feasible:

- timestamps;
- NaN/Inf;
- covariance;
- implausible jumps;
- impossible wheel-speed combinations;
- encoder stationary while strong motion is commanded;
- encoder motion while vehicle should be disabled;
- stale sequence numbers;
- repeated/replayed packets.

The watchdog should primarily produce a binary autonomous enable plus detailed status/reason codes.

## 17.2 Continuous command safety envelope

Separate binary enable from continuous limiting.

A common autonomous safety/limiter may enforce:

- velocity bounds;
- acceleration/deceleration bounds;
- steering-angle bounds;
- steering-rate bounds;
- lateral-acceleration limits;
- mode-specific limits;
- collision-related emergency constraints where available.

## 17.3 ESP32 final limiter

The ESP32 must independently enforce final low-level limits for **both** MANUAL and JETSON control.

Examples:

- motor-command limits;
- steering limits;
- servo calibration/end stops;
- command timeout;
- steering slew limits if required;
- reverse limitations;
- valid command format/CRC/sequence.

## 17.4 ESP32 watchdog

If the active source stops producing valid commands, the ESP32 must enter a safe state.

Examples:

```text
JETSON timeout -> SAFE
MANUAL timeout -> SAFE
invalid protocol/CRC -> reject command
```

Safe state should at minimum command motor neutral/off and defined steering behavior.

## 17.5 Physical emergency stop

Where hardware permits, provide a physical means to prevent propulsion independent of Jetson software.

Do not claim a software watchdog is equivalent to a physical emergency stop.

---

# 18. USB communication

The USB bridge is bidirectional.

Jetson → ESP32 may include:

- DriveCommand;
- mode acknowledgement/control fields where appropriate;
- arming/state-control messages;
- configuration where explicitly supported.

ESP32 → Jetson may include:

- encoder ticks;
- ACK + accepted sequence;
- control owner;
- requested/active low-level mode state;
- `jetson_locked`;
- hardware/actuator status;
- fault flags;
- communication diagnostics.

Use a framed protocol with explicit versioning and integrity checking such as CRC.

Do not rely on newline-delimited free-form text for the final real-time protocol.

When changing the wire protocol:

- version it;
- update both sides together;
- provide protocol tests;
- avoid ambiguous field sizes/endian assumptions;
- document timeout behavior.

---

# 19. ROS 2 message policy

Prefer typed messages over `std_msgs/String` or JSON for permanent interfaces.

Likely custom messages include concepts such as:

```text
DriveCommand.msg
DriveRequest.msg
OperatingMode.msg
VehicleStatus.msg
EncoderTicks.msg
ActuatorStatus.msg
SafetyStatus.msg
TrackModel.msg
PylonDetections.msg
BehaviorState.msg
```

Do not create custom messages when an existing standard message expresses the semantics correctly.

Examples to evaluate first:

- `sensor_msgs/LaserScan`
- `sensor_msgs/Image`
- `sensor_msgs/Imu`
- `nav_msgs/Odometry`
- `nav_msgs/OccupancyGrid`
- `geometry_msgs/*`
- `ackermann_msgs/AckermannDriveStamped`
- `diagnostic_msgs/*`

Custom messages should contain timestamps where freshness matters.

Avoid magic integer constants scattered through nodes. Put enums/constants into message definitions or shared interfaces.

---

# 20. Node and package boundaries

Do not create one giant `control_center` node that owns perception, planning, safety and actuation.

Prefer small nodes/packages with clear contracts.

A possible package split is:

```text
avaj_interfaces
avaj_vehicle_description
avaj_sensor_processing
avaj_state_estimation
avaj_localization
avaj_racing
avaj_pylon
avaj_control
avaj_safety
avaj_usb_bridge
avaj_bringup
avaj_simulation
avaj_web_bridge        # only if web/backend is hosted on Jetson side
```

These names are suggestions, not mandatory. Inspect the repository before creating new packages and reuse existing naming conventions where possible.

Avoid unnecessary package fragmentation for tiny utilities, but do not merge unrelated subsystems merely to reduce package count.

---

# 21. Web interface role

The web interface is a supervisory/control interface, not part of the high-frequency control loop.

It should eventually allow at least:

- request `MANUAL`, `RACING`, `PYLON`, `DISABLED`;
- show `requested_mode`;
- show `active_mode`;
- show racing/pylon sub-state;
- show Jetson/ESP connection health;
- show sensor readiness;
- show safety state and reason for inhibition;
- show current control owner (`SAFE`, `MANUAL`, `JETSON`);
- show whether `jetson_locked` is active.

Do not make vehicle safety depend on the web browser remaining connected.

---

# 22. Operating-state model

Keep these concepts separate.

## User operating mode

```text
DISABLED
MANUAL
RACING
PYLON
```

## ESP control owner

```text
SAFE
MANUAL
JETSON
```

## Racing sub-state

Example:

```text
IDLE
MAPPING
TRACK_BUILD
OPTIMIZATION
READY
RACING
FAULT
```

## Pylon sub-state

Example:

```text
IDLE
SEARCHING
TRACKING
GATE
SLALOM
STOP
FAULT
```

## Localization mode

```text
DISABLED
MAPPING
LOCALIZATION
```

Do not collapse these into one giant enum.

---

# 23. Lifecycle and launch design

Use ROS 2 lifecycle management where it adds real value, particularly for mutually exclusive or safety-relevant components.

Strong candidates:

- SLAM / AMCL / map server orchestration;
- racing supervisor;
- pylon supervisor;
- controller activation;
- sensor-dependent processing chains.

Launch profiles should make system states reproducible.

Potential profiles:

```text
simulation
hardware_base
manual
racing_mapping
racing_drive
pylon
sensor_test
usb_test
```

Exact names may differ.

A launch file must not silently activate incompatible global localization publishers.

---

# 24. Simulation and real-hardware portability

The same high-level nodes should work against simulation and real sensors whenever practical.

Prefer replacing drivers/bridges rather than rewriting algorithms.

For example:

```text
simulation LiDAR -> /scan_raw
real LiDAR       -> /scan_raw
```

Both should feed the same preprocessing/SLAM stack.

Likewise, control nodes should emit the same vehicle-level command interface whether the backend is:

- a simulator;
- the real USB bridge/ESP32.

Do not leak simulator-specific APIs into racing or pylon algorithms.

---

# 25. Parameterization

Vehicle geometry and limits must be parameters/configuration, not hardcoded throughout the codebase.

Examples:

```text
wheelbase
track width
wheel radius
encoder ticks per revolution
gear ratio
maximum steering angle
maximum steering rate
maximum forward speed
maximum reverse speed
maximum acceleration
maximum braking deceleration
lateral acceleration limit
servo center/min/max
motor calibration
communication timeout
```

Maintain one clear source of truth where possible.

Simulation and real hardware may use different calibration files while keeping identical node code.

---

# 26. Timing and timestamps

This is a real-time-ish robotics system. Timing semantics matter.

Every sensor/control message that requires freshness should have a meaningful timestamp.

Do not use receipt time as measurement time when the actual sensor timestamp is available.

Do not assume all sensors are synchronized automatically.

Design for later measurement of:

- sensor latency;
- processing latency;
- planning latency;
- controller latency;
- USB round-trip time;
- command-to-actuator latency.

Do not introduce blocking operations into high-frequency callbacks without strong justification.

---

# 27. Diagnostics and observability

Every major subsystem should expose enough status to answer:

- Is it alive?
- Is its input fresh?
- Is its output valid?
- What mode/state is it in?
- Why is it refusing to operate?

Prefer structured diagnostics/status messages.

Important state transitions should be logged once with useful context, but avoid flooding logs in high-frequency loops.

For safety failures, provide machine-readable reason codes where practical.

---

# 28. rosbag and data recording

Design interfaces so that useful runs can be reconstructed offline.

Important topics should be recordable with `rosbag2`, including at least where available:

- LiDAR;
- camera/perception outputs;
- IMU;
- encoder data;
- odometry/EKF state;
- TF;
- map/track model;
- trajectory;
- controller output;
- final DriveCommand;
- ESP feedback/status;
- safety state;
- active operating mode.

Do not hide important control state exclusively inside node-local variables.

---

# 29. Testing requirements

Every implementation change should be testable without requiring a full-speed real vehicle whenever possible.

## Unit tests

Use for:

- message conversion;
- command scaling;
- Ackermann kinematics;
- mode transitions;
- ownership arbitration;
- timeout handling;
- CRC/framing;
- track-model algorithms;
- pylon behavior selection.

## Integration tests

Use for chains such as:

```text
controller -> drive_commander -> USB bridge
```

and:

```text
ESP status -> USB bridge -> safety watchdog
```

## Simulation tests

Use for:

- mapping;
- localization;
- racing-line following;
- pylon behaviors;
- sensor dropout;
- stale commands;
- invalid state estimates;
- mode transitions.

## Hardware-in-the-loop tests

Before high-speed driving, test:

- ESP timeout;
- Jetson disconnect;
- manual-controller disconnect;
- stale sequence;
- invalid CRC;
- mode changes;
- neutral command behavior;
- physical actuator limits.

Do not use a full-speed vehicle as the first integration test.

---

# 30. Safety-critical implementation rules

Coding agents must follow these rules.

1. Never bypass a watchdog to make a test pass without clearly marking the bypass as test-only.
2. Never remove command freshness checks just because simulation timestamps are inconvenient.
3. Never make stale commands valid after a mode transition.
4. Never allow both manual and Jetson sources to own actuators simultaneously.
5. Never allow both SLAM and AMCL to publish `map -> odom` simultaneously.
6. Never silently clamp obviously invalid NaN/Inf control values into something that moves the car; reject them and fail safe.
7. Never make communication loss result in nonzero propulsion.
8. Never make an automatic source switch after source failure.
9. Never assume a ROS heartbeat means the underlying sensor data is physically plausible.
10. Do not weaken ESP-side safety because the Jetson has already checked the same property.

---

# 31. Coding conventions for agents

Before editing:

1. Inspect repository layout.
2. Find existing package naming and style.
3. Search for existing message definitions before creating duplicates.
4. Search for current topic/service/action names before inventing new names.
5. Identify tests relevant to the changed subsystem.
6. Read launch/config files that instantiate the affected nodes.

While editing:

- prefer small coherent commits/changes;
- avoid unrelated refactors;
- preserve backwards compatibility when cheap and safe;
- use typed parameters;
- document units in code and message comments;
- use explicit enums/state machines for modes;
- validate all external inputs;
- keep hardware-specific scaling near the hardware boundary;
- keep algorithms hardware-independent where practical.

After editing:

1. Build the affected workspace/packages.
2. Run relevant unit tests.
3. Run lint/static checks already used by the repository.
4. Validate launch/config parsing.
5. Report what changed, what was tested and what remains unverified.

Do not claim real-vehicle validation unless it was actually performed.

---

# 32. Language guidance

Use the repository's existing language per subsystem.

General preference:

- C++ for timing-sensitive/high-frequency ROS 2 nodes where justified;
- Python for orchestration, experimentation, tooling and ML/perception where appropriate;
- do not rewrite a working node only to change language.

Performance decisions should be evidence-based.

---

# 33. Suggested implementation order

Unless the repository state suggests otherwise, prefer this sequence.

## Phase 1 — Core interfaces and communication

- define/clean up `DriveCommand` and status interfaces;
- implement robust bidirectional USB protocol;
- implement sequence/CRC/timeout handling;
- publish encoder/status data;
- keep `drive_commander` as sole Jetson final-command publisher.

## Phase 2 — ESP ownership and manual mode

- implement `SAFE / MANUAL / JETSON` ownership state machine;
- implement `jetson_locked` feedback;
- implement manual timeout;
- reject Jetson commands in MANUAL;
- ensure source loss leads to SAFE;
- test handovers extensively.

## Phase 3 — State estimation

- encoder odometry;
- IMU preprocessing;
- EKF;
- TF tree;
- diagnostics.

## Phase 4 — Racing mapping pipeline

- LiDAR filtering;
- SLAM mapping;
- map saving/loading;
- localization-mode exclusivity;
- basic track-model extraction.

## Phase 5 — Basic racing controller

- centerline or simple reference path;
- initial speed profile;
- Pure Pursuit baseline;
- simulation tests;
- low-speed real tests.

## Phase 6 — Pylon baseline

- camera calibration;
- pylon detection;
- gate detection;
- simple local target/trajectory;
- controller integration;
- later slalom behavior.

## Phase 7 — Advanced racing

- improved track model;
- optimized racing line;
- braking/acceleration profile;
- MPC;
- vehicle-dynamics estimation;
- systematic lap-time optimization.

Do not block early integration waiting for the final optimal algorithm.

---

# 34. Definition of done for a node

A node is not considered complete merely because it compiles.

For a production-target node, aim to have:

- documented purpose;
- documented inputs/outputs;
- documented units and frames;
- parameter validation;
- sensible behavior for missing/stale input;
- diagnostics/status;
- tests for important logic;
- launch/config integration;
- no unexplained magic constants;
- known failure behavior.

---

# 35. Current architectural priority

When uncertain, optimize for this order:

1. **Safety and deterministic ownership**
2. **Correct interfaces and state estimation**
3. **Observability and testability**
4. **Robust baseline autonomous behavior**
5. **Performance/lap-time optimization**
6. **ML/RL/advanced optimization**

Do not introduce ML merely because the project includes AI. Use it where it provides measurable value.

Likely useful areas include:

- pylon/visual perception;
- learned vehicle models;
- parameter estimation;
- racing-line or speed-profile optimization;
- later policy/optimization research.

The basic safety and actuator pipeline should remain deterministic and understandable.

---

# 36. Architecture summary

```text
                           WEB UI
                             │
                             ↓
                            ESP32
                    requested operating mode
                             │
                             ↓
                      autonomy_manager
                    ┌────────┴────────┐
                    │                 │
                 RACING            PYLON
                    │                 │
        LiDAR/SLAM/track model    Camera/vision
                    │                 │
            racing line         scene/behavior
                    │                 │
          speed/trajectory      local trajectory
                    │                 │
            race controller     pylon controller
                    └────────┬────────┘
                             ↓
                  autonomous safety layer
                             ↓
                       drive_commander
                             ↓
                         USB bridge
                             ↓
                             │
Manual controller ─────────> ESP32
                             │
                  control ownership state
                    SAFE/MANUAL/JETSON
                             │
                     final actuator limits
                             │
                         watchdog
                             │
                       motor + servo
```

The essential architectural distinction is:

- **RACING:** map-based, predictive, optimized for lap time.
- **PYLON:** camera-based, reactive/local, behavior-driven.
- **MANUAL:** direct ESP32 control, independent of the Jetson control loop.

All autonomous Jetson control converges before the USB interface.

All physical actuator commands, regardless of source, are finally arbitrated and limited by the ESP32.

---

# 37. Agent interaction rule

When asked to implement a feature, do not immediately invent the entire missing architecture.

First:

1. inspect the existing repository;
2. identify which part of this target architecture already exists;
3. identify the smallest safe next step;
4. state any required interface migration;
5. implement and test that step.

If a requested change would violate an invariant in this file, explicitly call out the conflict before proceeding.

---

# 38. Implementation status snapshot

Snapshot date: **31 August 2026**, Europe/Berlin.

This section records the repository and runtime state observed on that date. It
is an implementation inventory, not a replacement for the target architecture
above. A component is only marked `PRESENT` when corresponding source/config is
in the repository. Runtime or hardware validation is stated separately.

Status meanings:

- `PRESENT`: implemented at least as a usable baseline;
- `PARTIAL`: some infrastructure exists, but target behavior or validation is
  missing;
- `ABSENT`: no implementation was found in the repository;
- `TEST ONLY`: deliberately limited development path; not safe for powered
  actuators.

## 38.1 Repository baseline and live state

- Git branch: `orin`; inspected HEAD: `c091798`.
- The working tree contains substantial uncommitted and untracked work. This
  includes the current control pipeline, interface package and USB bridge. Do
  not use the HEAD commit alone as the baseline and do not discard the working
  tree.
- Own ROS packages found: `rc_car_interfaces`, `rc_car_usb_bridge`,
  `avaj_car_control`, `control_center` and `avaj_slam`.
- Vendor ROS packages found: `bno08x_driver` and `ldlidar_stl_ros2`, both with
  local changes recorded in `HANDOFF.md`.
- The repository contains no ESP32 firmware implementation. The KiCad data
  contains an ESP32-C3 device, but that is not actuator-arbitration firmware.
- At snapshot time only the IMU service was running. The ROS graph contained
  `/bno08x_ros`, `/imu/data` and `/imu/mag`.
- Camera and LiDAR containers were stopped and neither device appeared in
  `lsusb`. Therefore their current real-data paths were not runtime-validated
  during this snapshot.
- No Gazebo, SLAM, drive stack, web UI or autonomous program was running during
  this snapshot.

## 38.2 Implemented system inventory

| Area | Status | Current implementation | Remaining target gap |
|---|---|---|---|
| ROS container/tooling | PRESENT | ROS 2 Jazzy, Gazebo Harmonic, Nav2, `slam_toolbox`, `robot_localization`, sensor and diagnostic tools are installed in the image. | Reproducible end-to-end launch profiles and automated validation are incomplete. |
| Real camera | PARTIAL | UC-852 Docker service publishes image and camera-info topics when connected; hotplug rules exist. | Camera calibration/rectification, final optical TF and health diagnostics are missing. |
| Real LiDAR | PARTIAL | STL27L driver and hotplug service publish `/scan` when connected. | No `/scan_raw -> filtering -> /scan` preprocessing chain; frame naming must be reconciled with the URDF; current hardware run was not verified. |
| Real IMU | PRESENT | BNO085 service currently publishes `/imu/data` and `/imu/mag` at the ROS interface; local Tesla-unit correction exists. | Mounting orientation must be confirmed; timestamp/covariance/plausibility diagnostics and real EKF integration are missing. |
| Wheel encoders | ABSENT | No encoder message, ESP transport, odometry node or plausibility monitoring was found. | Implement four-channel feedback, typed message, odometry, diagnostics and EKF input. |
| Vehicle description/TF | PARTIAL | `avaj_slam` has a basic URDF for `base_link`, `base_footprint`, LiDAR, IMU and camera; simulation adds a LiDAR frame bridge. | Real driver frame names and optical frames do not yet form a demonstrated complete tree; dimensions and mount positions remain provisional. |
| State estimation | PARTIAL | Simulation EKF consumes Gazebo `/odom` and publishes `odom -> base_link`. | It does not fuse IMU; real encoder odometry/EKF is absent; no complete state-health diagnostic exists. |
| Mapping | PARTIAL | Lifecycle-launched `slam_toolbox`, mapping parameters and `save_map.sh` exist for simulation and real topics. | No current full mapping validation, scan filtering, map quality criteria or robust orchestration. `simulation:=true` and `real:=true` are not made mutually exclusive. |
| Localization | ABSENT | Nav2/AMCL software is installed only. | No map-server/AMCL launch, no `MAPPING/LOCALIZATION/DISABLED` manager and no enforced `map -> odom` exclusivity. |
| Low-level ROS interfaces | PARTIAL | Typed `DriveRequest` and `DriveCommand` messages exist with normalized values, timestamp, sequence and enable. | Operating mode, vehicle/actuator status, encoders, safety, track and pylon messages are absent. No SI-unit vehicle-command interface exists. |
| Jetson command arbitration | PARTIAL | `drive_commander` is the only intended `/drive_commands` publisher, selects AUTONOMOUS/MANUAL/TEST, clamps ranges, checks optional source freshness and generates sequences. | Target modes RACING/PYLON are absent. Cached requests are not invalidated on mode changes, so a fresh-command-after-handover invariant is not enforced. Status is JSON in `String`. |
| Mode management | PARTIAL | `mode_manager` publishes a latched string mode and accepts `/system/mode/set`. | It has no requested-vs-active distinction, readiness gating or ESP-originated typed mode input; `AUTONOMOUS` has not been migrated to RACING/PYLON. |
| Jetson safety watchdog | PARTIAL | Topic-arrival timeouts for LiDAR, camera, IMU, autonomous request and optional USB status produce `/system/drive_enable`. | Requirements are not properly mode-specific; header timestamps, values, covariance, EKF health, encoders, ACK progression, ESP faults and supervisor/controller health are not checked. Output has no typed reason/status message. |
| USB transmit bridge | PARTIAL | Serial discovery, CRC-16/CCITT command encoding, input timestamp/sequence/range validation, reconnect logic and a ROS-command timeout stop exist. | Protocol has no explicit version; response data is only forwarded as raw text; ACK/status/encoder decoding and typed publication are absent. A Jetson timeout cannot replace an independent ESP timeout. |
| ESP feedback and ownership | ABSENT | No firmware or typed `/vehicle/status` path exists. | Implement `SAFE/MANUAL/JETSON`, `jetson_locked`, source timeouts, explicit arming/handover, actuator limits, ACK/fault/status/encoder feedback and final hardware watchdog. |
| Manual mode | TEST ONLY | Qt WASD can flow through Jetson `DriveRequest -> drive_commander -> USB`; focus loss neutralizes the request. | This is explicitly not the target manual architecture. Final manual control must go directly to ESP arbitration and remain independent of Jetson. Current USB launch bypasses safety and must not be used with powered actuators. |
| Gazebo simulation | PRESENT | AWD Ackermann model, test world, camera/LiDAR/IMU, odometry, `/clock` and ROS-Gazebo bridges exist; final normalized command is converted to `Twist`. | Physical parameters are provisional; no shared Ackermann/SI command backend, automated scenario tests or current snapshot run was performed. |
| Autonomous baseline | TEST ONLY | `control_center` reads sensor topics and publishes a simple five-ray LiDAR avoidance request with normalized full speed. | It is not a racing or pylon program, has no distance-based collision stop and mixes monitoring/control responsibilities. It must not be transferred to the real car unchanged. |
| Racing program | ABSENT | Mapping infrastructure can become an input later. | Racing supervisor, track model, racing line, speed profile, trajectory, SI controller and evaluation are all missing. |
| Pylon program | ABSENT | Camera topics exist. | Calibration, detection, scene interpretation, behaviors, local trajectory, supervisor and controller are all missing. |
| Web supervision | ABSENT | No web UI/backend implementation was found in the active ROS workspace. | Mode request via ESP plus readiness, owner, lock, fault and sub-state display are missing. |
| Diagnostics/recording | PARTIAL | Several nodes log state changes and publish temporary JSON/string status; rosbag tools are installed. | No common typed diagnostics, reason-code policy, recording profile or reconstruction test exists. |

## 38.3 Safety deviations requiring immediate attention

The following are known deviations from mandatory sections above:

1. The repository has no ESP32 final actuator authority, owner state machine or
   independent hardware command timeout.
2. The only implemented manual path passes through Jetson. It is a bench-output
   test and must not be treated as operational MANUAL mode.
3. `manual_usb_test.launch.py` deliberately sets watchdog bypass, disables the
   source timeout, disables USB message validation/watchdog behavior and expects
   no ESP response. **Motor controller and steering servo must remain
   disconnected/unpowered in this profile.**
4. `drive_commander` does not clear cached requests on source/mode changes and
   does not require a post-transition request. This conflicts with the stale
   command and safe-handover rules.
5. USB RX is not yet a validated feedback protocol. There is no verified ACK,
   accepted sequence, control owner, lock, hardware fault or encoder feedback.
6. The safety watchdog proves topic arrival only, not physical plausibility or
   state-estimator health, and it has no encoder input.
7. The current autonomous test requests `speed=100` whenever its simple steering
   rule runs. It has no obstacle-distance stop and is simulation-only.
8. There is no documented or tested physical emergency-stop implementation.

No powered-actuator test is authorized by the present repository state.

## 38.4 Verification performed for this snapshot

- `docker compose ... ps --all`: IMU up; camera and LiDAR stopped.
- `lsusb`: camera and LiDAR not connected at inspection time.
- ROS graph check: BNO085 node plus `/imu/data` and `/imu/mag` observed.
- Colcon build succeeded for all five own packages:
  `rc_car_interfaces`, `rc_car_usb_bridge`, `control_center`,
  `avaj_car_control`, `avaj_slam`.
- Direct source test run for `rc_car_usb_bridge`: **3 passed**. This covers the
  CRC reference vector, command encoding and pseudo-terminal serial writing.
- `colcon test` currently does not discover those Python tests and reports
  `NO TESTS RAN` for `rc_car_usb_bridge`; package-level test integration remains
  to be fixed.
- No real camera/LiDAR, mapping, Gazebo, end-to-end USB/ESP, actuator or driving
  validation was performed for this snapshot.

## 38.5 Progress against the suggested implementation phases

| Phase | Assessment on 31 August 2026 | Exit work still required |
|---|---|---|
| 1 — Core interfaces and communication | PARTIAL | Add typed status/encoder interfaces, versioned bidirectional protocol, validated decoder, ACK/sequence/status handling and integration tests. |
| 2 — ESP ownership and manual mode | ABSENT | Implement and hardware-test ESP ownership, direct manual input, lock, safe timeouts, handover and actuator limits. |
| 3 — State estimation | EARLY PARTIAL | Implement encoder odometry, fuse real IMU/odometry, finish TF, validate timestamps/covariance and publish diagnostics. |
| 4 — Racing mapping pipeline | EARLY PARTIAL | Validate SLAM end to end, add preprocessing, localization exclusivity and track-model extraction. |
| 5 — Basic racing controller | ABSENT | Define SI trajectory/control interface, baseline controller, speed limits and simulation tests. |
| 6 — Pylon baseline | ABSENT | Calibrate camera, implement layered perception/behavior/trajectory/control and simulation/data tests. |
| 7 — Advanced racing | ABSENT | Defer until safe baseline racing and measurements exist. |

## 38.6 Recommended next safe work order

1. Preserve the current dirty working tree as a reviewable baseline (commit or
   otherwise snapshot it deliberately); do not mix it with broad refactors.
2. Define typed operating-mode, vehicle-status, actuator-status, safety-status
   and four-encoder interfaces plus a versioned bidirectional wire protocol.
3. Implement ESP firmware with `SAFE/MANUAL/JETSON`, independent timeout,
   final limits, ACK/status/encoder reporting and explicit handover.
4. Fix `drive_commander` transition semantics and add unit/integration tests for
   stale commands, timeout, invalid values and every mode/source transition.
5. Extend the USB bridge to validate/decode ESP feedback and make the watchdog
   depend on connection, ACK progression, owner/lock and faults.
6. Implement encoder odometry, finish real TF and EKF, then validate at zero or
   mechanically lifted wheels before any ground-driving test.
7. Complete and validate mapping/localization orchestration before building a
   track model and basic low-speed racing controller.
8. Start the pylon stack independently after camera calibration; do not extend
   `control_center` into a combined racing/pylon monolith.

## 38.7 Updating this comparison

For later reviews, keep this snapshot intact and append a dated delta containing:

- changed component and old/new status;
- interface or topic changes;
- tests run and exact environment (simulation, bench, HIL or real vehicle);
- remaining safety limitations;
- commit identifier plus whether uncommitted changes were included.

Do not upgrade a status based only on source presence. Record successful build,
test and hardware level separately.

---

# 39. Implementation delta — canonical ROS graph

Date: **31 August 2026**, Europe/Berlin.

Repository baseline: branch `orin`, HEAD `c091798`, including substantial
uncommitted and untracked work. This delta is not represented by HEAD alone.

## 39.1 Changes

- Added the own ROS package `avaj_sensor_processing`.
- Established the canonical sensor pipelines:

  ```text
  /scan_raw     -> /sensors/lidar_preprocessor -> /scan
  /imu/data_raw -> /sensors/imu_preprocessor   -> /imu/data
  ```

- The LiDAR preprocessor rejects invalid scan geometry and replaces non-finite
  or out-of-range samples with positive infinity.
- The IMU preprocessor rejects samples containing NaN or infinity. The BNO085
  rotation vector is passed through because the device already performs its
  own orientation fusion; an additional Madgwick stage is not active yet.
- Changed the Gazebo ROS bridge to publish the same canonical raw interfaces as
  real hardware. `/sim/...` names now remain internal Gazebo topic names only.
- Changed the real STL27L and BNO085 paths to publish `/scan_raw` and
  `/imu/data_raw`. Camera, IMU and LiDAR driver node names use the `/sensors`
  namespace.
- Changed `control_center`, `safety_watchdog` and SLAM to consume only the
  canonical processed topics. `control_center` now defaults to
  `/odometry/filtered` rather than raw `/odom`.
- Added a persistent `sensor_processing` Compose service and made the real IMU
  and LiDAR services depend on it.
- Gazebo startup now launches the same processing nodes with simulation time.
- Added a launch-time error when `avaj_slam` is requested with both
  `simulation:=true` and `real:=true`.
- Documented the permanent topic/node contract, types, publishers,
  subscribers, units, frames, expected rates and failure behavior in
  `docs/ros_graph.md`.

## 39.2 Status changes relative to section 38

| Area | Previous | Current baseline | Still missing |
|---|---|---|---|
| Sensor preprocessing | ABSENT | PRESENT, software and synthetic integration tested | Real LiDAR validation and richer diagnostics |
| Real IMU ROS path | PRESENT | PRESENT, live raw/processed chain verified | Mounting, covariance and EKF validation |
| Real LiDAR ROS path | PARTIAL | PARTIAL, source and launch migrated to raw/processed chain | Hardware was not connected or tested |
| Simulation portability | PARTIAL | PRESENT baseline for canonical sensor topics | Full Gazebo end-to-end rerun and automated scenario tests |
| SLAM profile exclusivity | ABSENT | PRESENT for simultaneous real/simulation selection | Full localization-mode manager remains absent |

## 39.3 Verification

- `colcon build --symlink-install` succeeded for:
  `avaj_sensor_processing`, `avaj_slam`, `control_center`,
  `avaj_car_control`, `bno08x_driver` and `ldlidar_stl_ros2`.
- `avaj_sensor_processing` lint tests: **2 passed**.
- Isolated DDS-domain integration test: the nodes appeared as
  `/sensors/lidar_preprocessor` and `/sensors/imu_preprocessor`.
- Synthetic ranges `[0.05, 2.0, 11.0]` with sensor limits `0.1..10.0 m`
  produced `[inf, 2.0, inf]` on `/scan`.
- Conflicting `simulation:=true real:=true` SLAM launch failed as intended.
- Live BNO085 verification showed exactly one publisher on `/imu/data_raw`,
  exactly one publisher on `/imu/data`, and these nodes:
  `/sensors/imu_driver`, `/sensors/imu_preprocessor` and
  `/sensors/lidar_preprocessor`.
- Docker Compose configuration validation succeeded.

## 39.4 Runtime and limitations

- At the end of verification, `ros2-jazzy-bno085` and
  `ros2-jazzy-sensor-processing` were running. The real LiDAR and camera were
  not running.
- Real hardware and Gazebo must not publish the canonical raw sensor topics at
  the same time. Stop `imu`, `lidar`, `camera` and `sensor_processing` as
  applicable before starting Gazebo.
- No real LiDAR, full Gazebo world, SLAM mapping, powered actuator or driving
  test was performed for this delta.
- The safety deviations in section 38.3 remain in force. In particular, this
  work does not make the manual USB test safe for powered actuators.
- `rc_car_usb_bridge` source tests exist but are still not registered correctly
  with package-level `colcon test`.

## 39.5 Next bounded safety task

Fix and test `drive_commander` source-transition semantics:

1. invalidate all cached requests on every mode/source change;
2. publish disabled neutral output during the transition;
3. require a request received after the transition before enabling motion;
4. reject NaN/Inf and invalid ranges rather than turning them into movement;
5. cover all source, timeout, safety-enable and mode transitions with automated
   tests.

# 40. Implementation delta — safe drive-command transitions

Date: **31 August 2026**, Europe/Berlin.

Repository baseline: branch `orin`, HEAD `c091798`, including the existing
substantial uncommitted and untracked work. No existing worktree changes were
discarded.

## 40.1 Changes and safety invariants

- `drive_commander` now clears every cached request on each actual mode/source
  change and immediately publishes a disabled neutral command.
- A selected source cannot actuate until a valid request from that source has
  arrived after the transition. Requests from inactive sources are rejected
  and never cached, so returning to a previous source cannot revive old input.
- Every `/system/drive_enable` edge invalidates cached requests. Re-enabling
  safety therefore also requires a new request. A source timeout permanently
  drops the timed-out request rather than allowing it to become valid again.
- `DISABLED` neutralizes immediately. Invalid mode input forces `DISABLED`,
  invalidates all requests and records `invalid_mode`.
- Values outside `-100..100`, NaN, infinity, fractional or otherwise invalid
  values are rejected. Clamping was removed from the final command path.
- The JSON status retains the active decision reason and the most recent
  rejection source/reason. Published command sequences continue to increment
  for every periodic or immediate neutral output.
- The topic and message interfaces are unchanged. `drive_commander` remains
  the only publisher of `rc_car_interfaces/msg/DriveCommand` on
  `/drive_commands`.

Changed files are limited to the `drive_commander` executable, its new test,
the package test registration/dependency, and the required delta documentation:

- `workspace/src/avaj_car_control/scripts/drive_commander`
- `workspace/src/avaj_car_control/test/test_drive_commander.py`
- `workspace/src/avaj_car_control/CMakeLists.txt`
- `workspace/src/avaj_car_control/package.xml`
- `HANDOFF.md` and `AGENTS (1).md`

This resolves safety deviation 38.3 item 4 for the currently implemented
`AUTONOMOUS`, `MANUAL` and `TEST` compatibility sources. It does not implement
the later RACING/PYLON mode migration.

## 40.2 Verification

All commands ran in the ROS 2 Jazzy development container without hardware or
actuator access.

- `colcon build --symlink-install --packages-select rc_car_interfaces avaj_car_control`
  succeeded for both packages.
- `colcon test --packages-select avaj_car_control --event-handlers console_direct+`
  ran 18 new tests: **18 passed**. The tests cover startup in `DISABLED`, every
  existing source without and with a post-transition request, return to a
  previous source, transition after non-neutral input, source timeout, both
  safety-enable edges, `DISABLED`, invalid mode, all representable int8 values
  outside `-100..100`, NaN/Inf at the validator boundary, inactive requests,
  strictly increasing observed sequences and the sole publisher invariant.
- `colcon test-result --verbose` reported no errors, failures or skips. Its
  shared result directory contained 21 successful tests in total; 18 belong to
  this package run.
- `python3 -m flake8` on the changed executable and test passed.
- An isolated ROS runtime test under `ROS_DOMAIN_ID=187` passed: five commands
  were received with strictly increasing unique sequences and exactly one
  `/drive_commands` publisher, node `/drive_commander`.
- A full safe dry-run of `drive_stack.launch.py` under `ROS_DOMAIN_ID=188`
  reported `Publisher count: 1`, with `/drive_commander` as publisher and only
  `drive_command_to_twist` plus `usb_bridge` as subscribers. A sampled command
  was neutral and disabled. The persistent launch was interrupted after the
  observations completed.

## 40.3 Remaining limitations

- `DriveRequest.speed` and `.steering` are `int8`. NaN/Inf and values outside
  `-128..127` cannot be serialized on this ROS interface; direct validator
  tests cover non-finite inputs, while ROS-representable invalid ranges
  `-128..-101` and `101..127` are tested directly.
- `DriveCommand.sequence` is `uint32`; strict monotonicity necessarily ends at
  the type-defined wrap after `2^32` publications.
- The other deviations in section 38.3 remain. There is still no verified ESP
  final authority, independent ESP watchdog, ACK/status path, encoder safety
  input or physical emergency stop. No powered-actuator, hardware or driving
  test was performed, and the manual USB profile remains unsafe for powered
  actuators.

## 40.4 Next bounded safety task

Implement the hardware-independent half of the typed ESP feedback path before
making any watchdog or drive-enable decision depend on it:

1. Define the smallest coherent typed feedback interfaces in
   `rc_car_interfaces` for protocol/version state, accepted command sequence,
   ESP control owner (`SAFE/MANUAL/JETSON`), Jetson lock/arming state, faults,
   applied actuator state and four wheel encoders. Document units, enum values,
   bit meanings, timestamp origin and wrap behavior explicitly.
2. Specify a versioned, checksummed ESP-to-Jetson line protocol in a dedicated
   protocol document. Keep the existing outbound `CMD,...*CRC` path compatible
   until matching firmware exists; do not silently reinterpret legacy frames.
3. Add a pure incremental parser/validator to `rc_car_usb_bridge`. It must
   reject malformed ASCII, unknown versions/types, bad CRC, wrong field counts,
   invalid enums/ranges, truncated/oversized frames and non-monotonic ACKs.
4. Publish only validated feedback on stable typed ROS topics. Raw RX may remain
   diagnostic, but must not be treated as trusted vehicle state.
5. Register the existing bridge tests correctly with `colcon test` and add
   unit plus pseudo-terminal integration tests for fragmented, concatenated,
   invalid and valid feedback streams.
6. Do not yet gate `safety_watchdog` or `/system/drive_enable` on synthetic or
   unverified feedback. That integration is the following safety package after
   matching ESP firmware or a contract-faithful emulator is available.

This task must not access physical USB devices, start actuators, weaken any
watchdog, add another `/drive_commands` publisher or claim hardware validation.

# 41. Implementation delta — typed ESP feedback foundation

Delta date: **1 September 2026**, Europe/Berlin. Repository basis remains branch
`orin` at HEAD `c091798` plus the pre-existing extensive uncommitted/untracked
working tree. No existing change was discarded.

## 41.1 Protocol, interfaces and parser

- Added `VehicleStatus`, `ActuatorStatus` and `WheelEncoderState` to
  `rc_car_interfaces`. They cover V1, accepted uint32 command sequence,
  `SAFE/MANUAL/JETSON`, Jetson lock, arming/enable, documented V1 fault bits,
  actually applied normalized actuators and four signed int32 encoder counts.
- `header.stamp` is explicitly Jetson ROS receipt time; ESP sequence/sample
  counters remain separate. Sequence, sample and encoder wrap, units, ranges,
  enum/bit values and unknown-value rejection are documented in the messages
  and `docs/esp_feedback_protocol.md`.
- V1 feedback frames are `V1,STA`, `V1,ACT` and `V1,ENC`, printable ASCII,
  comma-delimited, LF/CRLF terminated, CRC-16/CCITT-FALSE protected and limited
  to 128 bytes before LF. The legacy outbound `CMD,...*CRC\n` representation
  was not changed or reinterpreted.
- `feedback_protocol.py` is ROS-independent and incrementally handles arbitrary
  read boundaries. It atomically rejects bad CRC/format/count/range/enum/bits,
  non-ASCII, unknown version/type, overlength, truncation and invalid ACK
  progression. Its retained partial buffer is bounded. Parser and ACK state are
  reset on reconnect; uint32 wrap is accepted while duplicate, regression and
  jumps over 1,000,000 are rejected without advancing ACK state.
- `usb_bridge` publishes validated STA/ACT/ENC data only on `/vehicle/status`,
  `/vehicle/actuator_status` and `/vehicle/encoders`. `/drive_usb/rx` remains an
  explicitly untrusted diagnostic string. `/drive_usb/status` distinguishes
  transport state, valid feedback and stable reject reasons.
- `safety_watchdog` and `/system/drive_enable` were not changed or coupled to
  these synthetic inputs. The bridge remains a subscriber, never a publisher,
  of `/drive_commands`.

Affected implementation and test files:

- `workspace/src/rc_car_interfaces/CMakeLists.txt`
- `workspace/src/rc_car_interfaces/msg/{VehicleStatus,ActuatorStatus,WheelEncoderState}.msg`
- `workspace/src/rc_car_usb_bridge/{package.xml,setup.py}`
- `workspace/src/rc_car_usb_bridge/rc_car_usb_bridge/{feedback_protocol.py,usb_bridge.py}`
- `workspace/src/rc_car_usb_bridge/test/{test_protocol.py,test_feedback_protocol.py,test_feedback_ros.py}`
- `docs/{esp_feedback_protocol.md,ros_graph.md}`, `HANDOFF.md` and this file

## 41.2 Verification

All checks ran in the ROS Jazzy container with synthetic data/PTys only:

- `colcon build --symlink-install --packages-select rc_car_interfaces rc_car_usb_bridge`:
  both packages built successfully.
- `colcon test --packages-select rc_car_interfaces rc_car_usb_bridge --event-handlers console_direct+`:
  36 bridge tests passed; interface package completed without test failures.
- `colcon test-result --verbose`: shared result store contained **57 tests, 0
  errors, 0 failures, 0 skipped**.
- `python3 -m flake8` over every changed bridge Python/test file: no findings.
- `ROS_DOMAIN_ID=220 python3 -m pytest -q -rA src/rc_car_usb_bridge/test/test_feedback_ros.py`:
  **1 passed**. A PTY stream was fragmented and concatenated; STA, ACT and ENC
  each reached its typed topic once, while a bad-CRC ACT did not publish.
- Under `ROS_DOMAIN_ID=221`, safe
  `ros2 launch avaj_car_control drive_stack.launch.py initial_mode:=DISABLED usb_dry_run:=true`
  plus `ros2 topic info ... --verbose --no-daemon` showed one `/usb_bridge`
  publisher for each new typed topic. `/drive_commands` had exactly one
  publisher, `/drive_commander`, and two subscribers:
  `drive_command_to_twist` and `/usb_bridge`.
- The existing automated graph invariant test was rerun in isolation with
  `ROS_DOMAIN_ID=219`: one test passed, observing five strictly increasing
  commands and exactly one `/drive_commands` publisher, `/drive_commander`.

Tests cover the CRC reference, exact legacy command bytes, every V1 type,
CRC/version/type/count/empty/integer/overflow/range/enum/bit/status failures,
non-ASCII, fragmentation, concatenation, recovery, buffer limit, truncation,
reconnect reset, ACK increase/duplicate/regression/plausibility/uint32 wrap and
positive, negative and boundary encoder counts. No `/dev/ttyUSB*` or
`/dev/ttyACM*` path was opened.

## 41.3 Remaining safety boundary

No ESP firmware or contract-faithful independent emulator exists in this
repository, so protocol behavior, encoder polarity/scaling, ACK meaning,
actuator truth, ESP owner/lock enforcement and fault generation are not
hardware-verified. There is still no verified ESP final authority, independent
ESP command watchdog or physical emergency stop. Consequently the new feedback
must not yet gate autonomous enable. The next package may connect it to
`safety_watchdog` only after matching firmware/emulator verification and must
then validate connection freshness, ACK progress, owner, lock, faults and
encoder plausibility rather than treating topic arrival as health.

# 42. Implementation delta — Gazebo SLAM TF repair and experimental Nav2 start

Delta date: **1 September 2026**, Europe/Berlin. Repository basis remains
branch `orin` at HEAD `c091798` plus the existing uncommitted/untracked work.

## 42.1 Confirmed failure and repair

Gazebo Harmonic publishes `/odom` with `header.frame_id=avaj_car/odom` and
`child_frame_id=avaj_car/base_link`. The simulation EKF is intentionally
configured to publish the canonical `odom -> base_link` transform. Without
connections between these frame names, `robot_localization` did not publish
`/odometry/filtered`; `slam_toolbox` then filled its message-filter queue while
waiting to transform scans from `avaj_car/lidar_link/stl27_sim`.

`avaj_slam/launch/slam.launch.py` now starts two simulation-only identity
transforms:

```text
odom      -> avaj_car/odom
base_link -> avaj_car/base_link
```

The existing simulation-only LiDAR transform remains:

```text
base_link -> avaj_car/lidar_link/stl27_sim
```

`colcon build --symlink-install --packages-select avaj_slam` succeeded and the
launch arguments parsed successfully. A live Gazebo/SLAM verification with
temporary equivalent TF publishers produced a valid `/odometry/filtered`
message with canonical `odom` and `base_link` frames, a continuously updating
`odom -> base_link` transform, and one `/map` publisher named
`/slam_toolbox`. The temporary publishers/container were stopped afterward.
An already-running SLAM launch must be restarted once to instantiate the new
launch nodes.

## 42.2 Fixed BNO085 constraint

The physical BNO085 remains connected on `/dev/i2c-7` and cannot currently be
removed. Do not make removal of that sensor a prerequisite for Gazebo work.
During the repair its ROS service was not stopped or modified and remained
`Up`. The persistent `sensor_processing` service also remained active.

Gazebo currently starts another sensor-processing launch, so duplicate node
names can appear when the persistent hardware profile is still running. Do not
mistake that warning for the repaired odometry failure. Profile-isolated
hardware/simulation sensor ownership remains future work, especially before
the IMU is fused into simulated state estimation. The current simulation EKF
uses `/odom`, not `/imu/data`.

## 42.3 Reproducible mapping start

```bash
gazebo-harmonic
ros2-jazzy ros2 launch avaj_slam slam.launch.py \
  simulation:=true use_sim_time:=true rviz:=true
```

Confirm the repaired path with:

```bash
ros2-jazzy ros2 topic echo /odometry/filtered \
  --once --no-daemon --spin-time 8
ros2-jazzy ros2 run tf2_ros tf2_echo odom base_link
```

Restarting `slam_toolbox` creates a fresh in-memory map. Saved map files under
`workspace/maps/` are independent and must be deleted explicitly by exact
filename when no longer wanted. Save a new map with:

```bash
ros2-jazzy ros2 run avaj_slam save_map.sh /workspace/maps/teststrecke
```

## 42.4 Experimental online-SLAM Nav2 start

With Gazebo and the AVAJ SLAM launch already running and `/map` available,
start the navigation servers and Nav2 RViz separately:

```bash
ros2-jazzy ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true
ros2-jazzy ros2 launch nav2_bringup rviz_launch.py use_sim_time:=true
```

Use RViz fixed frame `map` and the `Nav2 Goal` tool. Do **not** start
`bringup_launch.py slam:=true`: that would create a second SLAM publisher for
`map -> odom`. Do **not** run WASD/manual drive nodes at the same time: this
experimental Nav2 path publishes directly to `/cmd_vel` and bypasses the
project drive-command arbitration.

Nav2 is installed, but only its stock parameter file is used here. No AVAJ
footprint, Ackermann-specific controller tuning, velocity/acceleration tuning,
costmap validation or completed goal-driving test is recorded yet. A saved-map
`map_server`/AMCL profile is not implemented, and SLAM and AMCL exclusivity is
not yet managed by a localization-mode launch. Treat this only as a low-speed
Gazebo development path, not as a completed navigation stack.
