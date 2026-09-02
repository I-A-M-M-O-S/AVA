# AP-D01 — Referenzpfadformat und Offline-Importer

```yaml
work_package: AP-D01
status: complete
completion_date: 2026-09-02
repository_basis:
  branch: orin
  head: 7df2f36f1a8d00ff6080dbec1ae1263aa5948f2b
validation_mode:
  - isolated ROS 2 Jazzy container
  - unit tests
  - static CSV example validation
hardware_accessed: false
usb_bridge_started: false
real_vehicle_validation: false
```

## Result and scope

AP-D01 adds only the package `workspace/src/avaj_racing/**` and this handoff.
It does not add a controller, track extraction, launch profile, hardware access,
or a command publisher. Existing worktree changes were preserved.

The new `reference_path_importer` loads one offline CSV, validates it
fail-closed, and publishes the resulting `nav_msgs/msg/Path` once on both:

```text
/planning/reference_path   canonical
/planning/racing_line      migration alias with identical content
```

Both publishers use `reliable + transient_local + keep_last(1)`. The node is
therefore event-driven: after a successful load it retains the one valid path
for late-joining consumers instead of periodically republishing it. It never
publishes a control topic.

## Format and contract

The importer accepts these SI CSV layouts:

| Layout | Columns used |
|---|---|
| Headered AVAJ CSV | `x_m`, `y_m`, optional `s_m`, optional `psi_rad` |
| TUMFTM global race trajectory | headerless `s_m,x_m,y_m,psi_rad,kappa_radpm,vx_mps,ax_mps2` |
| `trajectory_planning_helpers` reference track | headerless `x_m,y_m,width_right_m,width_left_m` |

The latter two formats are adapters only. No upstream code was copied. AP-R01
classifies `trajectory_planning_helpers` at commit
`aa950f6045680366b789dbb855db8d59d54b1db5` as offline `ADAPT`, and TUMFTM
`global_racetrajectory_optimization` at commit
`a9995e2f5407f22eb7fb9dceac2b71a35276bb41` as `REFERENCE ONLY`; the full
licenses, attribution and rationale remain in `THIRD_PARTY.md`.

The AP-M01 v1 path contract is implemented exactly:

| Attribute | Value |
|---|---|
| Type | `nav_msgs/msg/Path` |
| Frame | exactly `map` (REP-103; no leading slash) |
| Units | metres and radians |
| Pose headers | same stamp and frame as path header |
| Orientation | normalized yaw quaternion, tangential to driving direction |
| Closure | implicit last-to-first segment; first point is not duplicated |
| Direction | counterclockwise by default, parameterizable to clockwise |

Validation rejects finite-value violations, fewer than four points, wrong
frame, invalid configuration, coincident/too-close points, overlong segments
(open or undersampled paths), non-monotonic supplied arc length, self-crossing
or touching segments, zero enclosed area, wrong direction, and supplied
headings incompatible with the forward tangent. Defaults are 0.05 m minimum
spacing, 3.0 m maximum segment length and 45 degrees heading tolerance. They
are parameters of the importer and must be set deliberately for a future
track's scale and sampling.

`data/example_reference_path.csv` is a valid four-point TUMFTM-style diamond
with no duplicated closing point. It is an interface example, not a measured
map, track, trajectory or vehicle-validation artifact.

## Files

```text
workspace/src/avaj_racing/
  avaj_racing/reference_path.py           CSV parser and geometry validator
  avaj_racing/reference_path_importer.py  transient-local ROS publisher
  data/example_reference_path.csv
  test/test_reference_path.py
  package.xml, setup.py, setup.cfg, resource/
docs/work_packages/AP-D01.md
```

## Verification

All commands ran without Compose dependencies and with a local-only isolated
DDS domain. No USB, I2C, camera, LiDAR, ESP, actuator, or Gazebo process was
started.

```bash
docker compose run --rm --no-deps \
  -e ROS_DOMAIN_ID=189 -e ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST \
  jazzy bash -lc '
    cd /workspace
    source /opt/ros/jazzy/setup.bash
    colcon build --symlink-install --packages-select avaj_racing
    source install/setup.bash
    colcon test --packages-select avaj_racing --event-handlers console_direct+
    colcon test-result --test-result-base build/avaj_racing --verbose
  '

docker compose run --rm --no-deps jazzy bash -lc \
  'cd /workspace/src/avaj_racing && python3 -m flake8 avaj_racing test'
```

Results: build passed; 10/10 unit and package tests passed; Flake8 had no
findings. Tests cover valid closure/tangent generation and rejection of too few
points, self-intersection, NaN, overlong/open geometry, frame mismatch,
direction mismatch, nonmonotonic arc length, opposite heading, and nonfinite
CSV data. The importer also logged successful creation of the example's
four-point Path in an isolated ROS container. This is local software
validation only; no simulation or physical vehicle behavior was tested.

## Use

After building and sourcing the workspace, a later racing-only bringup may run:

```bash
ros2 run avaj_racing reference_path_importer --ros-args \
  -p csv_path:=/workspace/src/avaj_racing/data/example_reference_path.csv \
  -p frame_id:=map \
  -p required_direction:=counterclockwise
```

It is intentionally not added to any existing launch file. AP-I01 owns the
future racing simulation integration and must ensure that exactly one source
owns the canonical path topics.

## Limitations and follow-up

- This package does not infer a path from a map; AP-G01 owns centerline
  extraction and must validate its output through this boundary.
- No speed, curvature or acceleration contract is exported; AP-V01 must first
  establish the need under the AP-M01 rules.
- No controller consumes the result yet; AP-C01 must reject absent or invalid
  paths fail-safe and remains the only future Ackermann publisher.
- No runtime integration with SLAM, localization, Gazebo, USB or ESP was made.
- `CURRENT_STATE.md` and `docs/ros_graph.md` remain untouched, as reserved for
  AP-I01.
