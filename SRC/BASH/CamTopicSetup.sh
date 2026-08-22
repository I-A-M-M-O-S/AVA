#!/bin/bash

#############
# Variables #
#############

#############
# Functions #
#############

standby(){
  echo 'Video device needs to be identified first.'
  echo '1) Print current video device list'
  echo '2) Target video device is known'
  read answer
  case '$answer' in 
    1)
      v4l2-ctl --list-devices
      standby
      ;;
    2)
      echo ''
      ;;
  esac
  return 0;
}

startnode(){
  echo 'Enter device name'
  read device
  echo 'Enter resolution-height'
  read height
  echo 'Enter resolution-width'
  read width
  echo "Chosen device: /dev/$device"
  echo "Chosen resolution: [$height , $width]"
  ros2  run v4l2_camera v4l2_camera_node \
  --ros-args \
  -p video_device:=/dev/${answer} \
  -p image_size:=[${height},${width}] \
  -p pixel_format:=UYVY
  return 0;
}

########
# Main #
########

echo '#'
echo 'Cam setup script'
echo '#'
echo ''
standby
startnode