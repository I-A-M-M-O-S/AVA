#!/bin/bash

########
# Main #
########

echo '#'
echo 'Setting up Video4Linux2 (V4L2) and GStreamer libs'
echo '#'

sudo apt update
sudo apt-get install v4l-utils
sudo apt install -y gstreamer1.0-tools
sudo apt install -y gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav

echo 'Libs successfully installed'
