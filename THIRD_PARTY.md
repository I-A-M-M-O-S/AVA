# Third-party software decisions

This file records reproducible upstream decisions for AVAJ. An entry marked
`USE`, `ADAPT`, or `REFERENCE ONLY` is not evidence that source was copied into
this repository. The **Repository use** field states what is actually present.

Decision meanings:

- `USE`: use the released package/API without copying its implementation.
- `ADAPT`: use only the named component behind an AVAJ-owned adapter; retain
  the upstream license and attribution for any copied code.
- `REFERENCE ONLY`: use concepts, formats, or benchmark behavior only.
- `REJECT`: do not use for the stated need.

## AP-R01 pinned decisions (2 September 2026)

### Nav2 Regulated Pure Pursuit Controller 1.3.12 — USE

- **Need:** primary path-follower candidate and AP-C01 benchmark.
- **Repository:** <https://github.com/ros-navigation/navigation2>
- **Pin:** tag `1.3.12`, commit
  [`6be3614013ec586051b86c97b919b293281490fe`](https://github.com/ros-navigation/navigation2/commit/6be3614013ec586051b86c97b919b293281490fe)
- **License/attribution:** Apache-2.0 for
  `nav2_regulated_pure_pursuit_controller`; retain the license and notices from
  Navigation2 when redistributing it.
- **Environment:** ROS 2 Jazzy binary
  `1.3.12-1noble.20260614.095312` is installed for `arm64`. It is C++ and has
  no Python runtime dependency. The pinned Jazzy sync commit is dated
  29 April 2026.
- **API boundary:** Nav2 `nav2_core::Controller` plugin; receives a
  `nav_msgs/msg/Path` through `setPlan()`, current pose and velocity through
  `computeVelocityCommands()`, and returns
  `geometry_msgs/msg/TwistStamped`.
- **AVAJ adaptation:** configure the existing Nav2 plugin and costmap; convert
  its body velocity to Ackermann SI units in a small adapter. AP-C01 must check
  the near-zero case, reverse rejection, wheelbase conversion
  `atan(wheelbase * angular_z / linear_x)`, steering/rate limits, stale input,
  frames, and exclusive publication on
  `/control/autonomous_ackermann_cmd`. The plugin must never publish directly
  to `/drive_commands`, `/control/autonomous_cmd`, or `/cmd_vel` in an AVAJ
  profile.
- **Maintenance/ARM64 assessment:** maintained Jazzy release line and native
  ARM64 binary; lowest supply and porting risk of the controller candidates.
- **Repository use:** no source copied and no AVAJ adapter added by AP-R01.

### tum-phoenix/f1tenth_ros Pure Pursuit — ADAPT

- **Need:** F1TENTH Ackermann-native comparison kernel for AP-C01.
- **Repository:** <https://github.com/tum-phoenix/f1tenth_ros>
- **Pin:** commit
  [`c20cf63d04b9841ffdb6b2f963bd737d78074136`](https://github.com/tum-phoenix/f1tenth_ros/commit/c20cf63d04b9841ffdb6b2f963bd737d78074136)
  (`main`, last upstream commit observed 10 June 2024).
- **License/attribution:** repository MIT, while the nested Pure Pursuit
  license attributes copyright to xLab for Safe Autonomous Systems. Preserve
  both relevant MIT notices for any copied portion.
- **Environment:** ROS 2 C++ package, documented for ROS 2 Foxy or newer;
  no Jazzy CI or release binary was found. Eigen/rclcpp/TF2 and standard ROS
  messages are architecture-neutral and buildable in principle on ARM64.
- **API boundary:** reads CSV waypoints, `nav_msgs/msg/Odometry`, and TF;
  publishes `ackermann_msgs/msg/AckermannDriveStamped`. The upstream defaults
  are F1TENTH-specific (`/ego_racecar/odom`, `/drive`, F1TENTH frames).
- **AVAJ adaptation:** if RPP cannot meet AP-C01 acceptance, extract only the
  Pure Pursuit geometry into a tested AVAJ wrapper accepting
  `nav_msgs/msg/Path` and AVAJ TF/pose contracts. Add deterministic stale/empty
  path and transform-failure behavior, SI/limit validation, sim time, and the
  exclusive AVAJ Ackermann output. Do not import launch, map, simulator,
  particle-filter, VESC, safety, or vehicle-command parts.
- **Maintenance/quality assessment:** useful ROS 2/Ackermann reference but
  much less active than Nav2. Source review found no controller tests and
  unsafe integration assumptions (CSV-owned path, wall timer, hard-coded
  visualization frame, and continued computation after TF lookup failure).
- **Repository use:** no source copied by AP-R01.

### f1tenth-dev/pure_pursuit — REJECT

- **Need:** alternative F1TENTH path follower.
- **Repository:** <https://github.com/f1tenth-dev/pure_pursuit>
- **Pin:** commit
  [`213297d59fa225381a66ea0851c819874bbafcc2`](https://github.com/f1tenth-dev/pure_pursuit/commit/213297d59fa225381a66ea0851c819874bbafcc2)
  (`master`, last upstream commit observed 14 April 2020).
- **License/attribution:** Apache-2.0.
- **Environment/API:** ROS 1 Python (`rospy`, ROS 1 launch XML), with several
  cooperating nodes and project-specific topics rather than a ROS 2/Jazzy
  component.
- **Reason:** stale ROS 1 design, high adapter surface, and the pinned source
  fails Python 3.12 compilation in `find_nearest_goal.py` because a name is
  assigned before its `global` declaration. It offers no advantage over the
  installed Nav2 plugin or the ROS 2 tum-phoenix comparison.
- **Repository use:** none.

### slam_toolbox 2.8.5 localization mode — USE

- **Need:** first-choice stored-map localization for AP-L01.
- **Repository:** <https://github.com/SteveMacenski/slam_toolbox>
- **Pin:** tag `2.8.5`, commit
  [`ec8f7635dea317b531c419f798f87d90a336f32e`](https://github.com/SteveMacenski/slam_toolbox/commit/ec8f7635dea317b531c419f798f87d90a336f32e)
- **License/attribution:** LGPL-2.1; preserve the license/source obligations
  when redistributing or modifying the library.
- **Environment:** ROS 2 Jazzy binary
  `2.8.5-1noble.20260614.104642` is installed for ARM64. The pinned Jazzy sync
  is dated 29 April 2026.
- **API boundary:** lifecycle localization node consuming `/scan` and
  `odom -> base_link`, loading a serialized pose graph, and owning the single
  `map -> odom` transform. This differs from loading only a PGM/YAML occupancy
  map.
- **AVAJ adaptation:** AP-L01 should configure and lifecycle-manage the
  installed localization executable, add serialized-posegraph save/load to the
  existing map workflow, surface pose loss, and enforce mutual exclusion with
  mapping and every other `map -> odom` provider.
- **Repository use:** binary already installed and mapping mode already used;
  AP-R01 adds no launch or source.

### Nav2 map_server and AMCL 1.3.12 — REFERENCE ONLY fallback

- **Need:** measurable fallback if slam_toolbox localization cannot satisfy
  AP-L01 with the project's saved artifacts.
- **Repository/pin:** Navigation2 tag `1.3.12`, commit
  [`6be3614013ec586051b86c97b919b293281490fe`](https://github.com/ros-navigation/navigation2/commit/6be3614013ec586051b86c97b919b293281490fe)
- **License/attribution:** `nav2_map_server` is Apache-2.0 and BSD-3-Clause;
  `nav2_amcl` is LGPL-2.1-or-later. Retain all applicable notices.
- **Environment:** both Jazzy `1.3.12` binaries are installed for ARM64.
- **API boundary:** lifecycle `map_server` loads occupancy-grid YAML/image;
  AMCL consumes the map, LaserScan, initial pose, odometry and TF, then owns
  `map -> odom` and publishes its pose estimate.
- **Decision reason:** technically compatible and maintained, but using it now
  would add a second localization path before the already-installed
  slam_toolbox mode is measured. AP-L01 may promote it to `USE` only with a
  recorded comparison and must never activate it concurrently with
  slam_toolbox.
- **Repository use:** binaries installed; no AP-R01 runtime configuration.

### TUMFTM trajectory_planning_helpers 0.80 — ADAPT offline

- **Need:** closed-track spline, curvature, normal-vector, minimum-curvature,
  path-matching, and speed-profile utilities for AP-G01/AP-V01.
- **Repository:** <https://github.com/TUMFTM/trajectory_planning_helpers>
- **Pin:** commit
  [`aa950f6045680366b789dbb855db8d59d54b1db5`](https://github.com/TUMFTM/trajectory_planning_helpers/commit/aa950f6045680366b789dbb855db8d59d54b1db5)
  (PyPI version `0.80`, last upstream commit observed 25 March 2024).
- **License/attribution:** LGPL-3.0; retain license, attribution, relinking and
  source/modification obligations for distributed adapted code.
- **Environment:** Python package classified through Python 3.10, not 3.12.
  Most helpers use NumPy/SciPy and are architecture-neutral; optimization uses
  the compiled `quadprog` dependency. The AVAJ ARM64/Jazzy image has Python
  3.12, NumPy 1.26.4 and SciPy 1.11.4, but no `quadprog`.
- **API boundary:** NumPy arrays, notably closed reference track
  `[x, y, width_right, width_left]`; helpers return splines, normals,
  curvature, optimized lateral offsets, race line, and profiles. No ROS API.
- **AVAJ adaptation:** use a separate offline, pinned environment and a thin
  importer/exporter. Pass only validated SI arrays; export through the AP-M01
  path contract. Start with non-optimizer geometry helpers and do not run this
  package in the controller loop.
- **Probe:** all modules compile with Python 3.12, but importing the top-level
  package fails deterministically with `ModuleNotFoundError: quadprog` because
  `__init__.py` eagerly imports the optimizers. AP-G01/AP-V01 must resolve and
  test that dependency explicitly before promoting selected helpers to direct
  runtime use.
- **Repository use:** no package or source imported by AP-R01.

### TUMFTM global_racetrajectory_optimization — REFERENCE ONLY

- **Need:** race-line formats, minimum-curvature workflow, and future offline
  optimization reference.
- **Repository:** <https://github.com/TUMFTM/global_racetrajectory_optimization>
- **Pin:** commit
  [`a9995e2f5407f22eb7fb9dceac2b71a35276bb41`](https://github.com/TUMFTM/global_racetrajectory_optimization/commit/a9995e2f5407f22eb7fb9dceac2b71a35276bb41)
  (`master`, last upstream commit observed 1 April 2021).
- **License/attribution:** LGPL-3.0.
- **Environment:** developed for Ubuntu 20.04/Python 3.7. Its requirements pin
  NumPy 1.18.1, SciPy 1.3.3, scikit-learn 0.23.1, matplotlib 3.3.1,
  trajectory_planning_helpers 0.76 and, for minimum time, CasADi 3.5.1. Those
  pins are not a viable Python 3.12/ARM64 runtime contract; CasADi,
  scikit-learn and quadprog are absent from the current image.
- **API boundary:** offline files. Input reference track is
  `[x, y, width_right, width_left]`. Its seven-column race trajectory output is
  `s_m,x_m,y_m,psi_rad,kappa_radpm,vx_mps,ax_mps2`.
- **Decision reason:** valuable format/algorithm reference, but stale strict
  dependencies and a large vehicle/minimum-time parameter surface are
  disproportionate before a validated AVAJ centerline exists. Do not import
  or run the full stack. Re-evaluate only after the conservative baseline.
- **Repository use:** none.

### ROS image_pipeline 5.0.13 — USE once installed

- **Need:** camera calibration and image rectification for AP-P02.
- **Repository:** <https://github.com/ros-perception/image_pipeline>
- **Pin:** Jazzy tag `5.0.13`, commit
  [`6c3df3099bc7b1ec92215719215c8eefd0d3aa69`](https://github.com/ros-perception/image_pipeline/commit/6c3df3099bc7b1ec92215719215c8eefd0d3aa69)
- **License/attribution:** package manifests declare BSD; the repository
  license includes BSD and Apache-2.0 portions. Retain the applicable notices.
- **Environment:** maintained Jazzy release dated 10 July 2026; ROS-native C++
  and Python components support ARM64 through ROS packages. `image_proc` and
  `camera_calibration` are not installed in the currently inspected image, so
  AP-P02 must add pinned Jazzy binary dependencies before use.
- **API boundary:** `camera_calibration` consumes camera images and writes
  intrinsics; `image_proc` consumes `sensor_msgs/Image` plus matching
  `CameraInfo` and publishes rectified images through image_transport.
- **AVAJ adaptation:** launch/configuration and canonical topic remaps only.
  Calibration validity must be checked; do not infer 3-D pylon geometry from
  uncalibrated images.
- **Repository use:** none installed or copied by AP-R01.

### vision_opencv/cv_bridge 4.1.0 — USE

- **Need:** typed ROS Image to OpenCV boundary for AP-P02.
- **Repository:** <https://github.com/ros-perception/vision_opencv>
- **Pin:** tag `4.1.0`, commit
  [`f5b738d9694f0cee5904440d03912fc249943f8a`](https://github.com/ros-perception/vision_opencv/commit/f5b738d9694f0cee5904440d03912fc249943f8a)
- **License/attribution:** cv_bridge declares Apache-2.0 and BSD; retain both
  applicable notices.
- **Environment:** Jazzy binary
  `4.1.0-1noble.20260612.114100` is installed for ARM64 and links the installed
  OpenCV/NumPy stack.
- **API boundary:** conversion between `sensor_msgs/msg/Image` and OpenCV
  matrices/NumPy arrays with explicit encodings.
- **AVAJ adaptation:** direct API use; validate encoding and dimensions and
  preserve header timestamp/frame in the perception output.
- **Repository use:** binary installed; no AP-R01 code.

### OpenCV 4.6.0 — USE

- **Need:** deterministic baseline pylon image processing and calibrated
  projection primitives for AP-P02; geometry utilities for offline tools.
- **Repository:** <https://github.com/opencv/opencv>
- **Pin:** tag `4.6.0`, commit
  [`b0dc474160e389b9c9045da5db49d03ae17c6a6b`](https://github.com/opencv/opencv/commit/b0dc474160e389b9c9045da5db49d03ae17c6a6b)
- **License/attribution:** Apache-2.0 for OpenCV 4.6.0; a redistributed binary
  must also retain notices for any bundled third-party components listed by
  OpenCV.
- **Environment:** Ubuntu packages `4.6.0+dfsg-13.1ubuntu1` and Python cv2
  `4.6.0` are installed for ARM64; current Python is 3.12.3.
- **API boundary:** AP-P02 may directly use `cvtColor`, `inRange`, morphology,
  contour/component filtering, bounding boxes and calibrated projection/PnP.
  These are primitives, not a trained pylon detector or semantic gate planner.
- **AVAJ adaptation:** implement only a replaceable HSV/geometry baseline for
  the deterministic Gazebo world, document thresholds and uncertainty, and do
  not claim transfer to the real camera.
- **Repository use:** system dependency already present; no source copied.

### External pylon detector or cone-planning stack — REJECT for baseline

- **Need:** pylon class detection and gate/slalom semantic planning.
- **Sources examined:** the official ROS image pipeline, vision_opencv, and
  OpenCV components pinned above. None provides a maintained, domain-specific
  pylon detector or a gate/slalom planner with the AVAJ typed contracts.
- **Decision reason:** importing a vehicle stack would bring its topics,
  vehicle/safety assumptions and uncertain model/dataset licensing. AP-P02
  should therefore use the allowed OpenCV simulation baseline behind a
  replaceable detector interface. AP-P03 should implement only the small,
  explicit AVAJ gate/slalom interpretation state machine against AP-M01's
  typed observations and output `nav_msgs/msg/Path`; it must not copy a
  downstream command or safety stack.
- **Repository use:** none.
