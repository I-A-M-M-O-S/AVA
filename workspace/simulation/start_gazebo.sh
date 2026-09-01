#!/usr/bin/env bash
set -euo pipefail

ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:=/workspace/simulation/bridge.yaml &
bridge_pid=$!
ros2 launch avaj_sensor_processing sensor_processing.launch.py \
  use_sim_time:=true &
processing_pid=$!
trap 'kill -INT "${bridge_pid}" "${processing_pid}" 2>/dev/null || true' EXIT INT TERM

gz sim -r -v 3 /workspace/simulation/worlds/jetson_test_track.sdf "$@"
