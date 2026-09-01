#!/usr/bin/env bash
set -euo pipefail

ros2 run avaj_car_control drive_command_to_twist &
converter_pid=$!

stop_converter() {
  kill -TERM "${converter_pid}" 2>/dev/null || true
  wait "${converter_pid}" 2>/dev/null || true
}
trap stop_converter EXIT INT TERM

ros2 run avaj_car_control wasd_teleop "$@"
