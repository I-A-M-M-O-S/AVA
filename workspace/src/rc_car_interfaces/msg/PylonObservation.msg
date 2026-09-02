# One camera-derived traffic-cone observation. The containing array header is
# the measurement timestamp and coordinate frame. Spatial values use a REP-103
# vehicle frame (normally base_link): bearing is zero forward and positive to
# the left. The bounding box remains in source-image pixel coordinates.
#
# Publishers must reject non-finite values, confidence outside [0, 1], negative
# standard deviations, invalid boxes and unknown enum values. When range_valid
# is false, range_m and range_stddev_m must be zero and range_source must be
# RANGE_NONE. Consumers must not infer range from the bounding box themselves.

uint8 CLASS_UNKNOWN=0
uint8 CLASS_TRAFFIC_CONE=1

uint8 COLOR_UNKNOWN=0
uint8 COLOR_BLUE=1
uint8 COLOR_YELLOW=2
uint8 COLOR_ORANGE=3
uint8 COLOR_RED=4

uint8 RANGE_NONE=0
uint8 RANGE_MONOCULAR_SIZE=1
uint8 RANGE_STEREO=2
uint8 RANGE_DEPTH_SENSOR=3

# Zero means that the detector has not assigned a temporal track.
uint32 track_id
uint8 object_class
uint8 color
vision_msgs/BoundingBox2D bbox
float32 confidence
float32 bearing_rad
float32 bearing_stddev_rad
bool range_valid
float32 range_m
float32 range_stddev_m
uint8 range_source
