FROM ros:jazzy-ros-base-noble

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ros-jazzy-desktop \
        ros-jazzy-demo-nodes-cpp \
        ros-jazzy-demo-nodes-py \
        python3-colcon-common-extensions \
        git \
        nano \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ros-jazzy-usb-cam \
        v4l-utils \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ros-jazzy-rviz-imu-plugin \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ros-jazzy-ros-gz \
        ros-jazzy-ackermann-msgs \
        ros-jazzy-slam-toolbox \
        ros-jazzy-navigation2 \
        ros-jazzy-nav2-bringup \
        ros-jazzy-robot-localization \
        ros-jazzy-robot-state-publisher \
        ros-jazzy-joint-state-publisher-gui \
        ros-jazzy-xacro \
        ros-jazzy-tf2-tools \
        ros-jazzy-tf-transformations \
        ros-jazzy-laser-filters \
        ros-jazzy-pointcloud-to-laserscan \
        ros-jazzy-imu-filter-madgwick \
        ros-jazzy-imu-tools \
        ros-jazzy-rqt-plot \
        ros-jazzy-rqt-tf-tree \
        ros-jazzy-rqt-topic \
        ros-jazzy-rosbag2 \
        ros-jazzy-rosbag2-storage-mcap \
        mesa-utils \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /workspace/src \
    && chown -R ubuntu:ubuntu /workspace

USER ubuntu
WORKDIR /workspace

CMD ["bash"]
