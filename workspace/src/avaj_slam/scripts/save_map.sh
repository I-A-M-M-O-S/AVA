#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Verwendung: save_map.sh /workspace/maps/meine_strecke" >&2
  exit 2
fi

ros2 run nav2_map_server map_saver_cli -f "$1" --ros-args -p map_subscribe_transient_local:=true
