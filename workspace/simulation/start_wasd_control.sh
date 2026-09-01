#!/usr/bin/env bash
set -euo pipefail

exec ros2 launch avaj_car_control manual_usb_test.launch.py "$@"
