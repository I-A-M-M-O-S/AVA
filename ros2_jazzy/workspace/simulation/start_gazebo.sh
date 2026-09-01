#!/usr/bin/env bash
set -euo pipefail

ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:=/workspace/simulation/bridge.yaml &
bridge_pid=$!
trap 'kill -INT "${bridge_pid}" 2>/dev/null || true' EXIT INT TERM

gz sim -r -v 3 /workspace/simulation/worlds/jetson_test_track.sdf "$@"
