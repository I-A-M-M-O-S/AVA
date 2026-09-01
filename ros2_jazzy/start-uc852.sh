#!/usr/bin/env bash
set -e

# Europe uses 50 Hz mains frequency; this reduces flicker under artificial light.
v4l2-ctl --device=/dev/video0 --set-ctrl=power_line_frequency=1

exec ros2 run usb_cam usb_cam_node_exe --ros-args \
  --params-file /config/uc852.yaml \
  -r image_raw:=/camera/image_raw \
  -r camera_info:=/camera/camera_info
