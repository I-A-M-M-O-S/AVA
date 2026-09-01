# Fully validated actuator state actually applied by the ESP, distinct from a
# requested DriveCommand. header.stamp is the Jetson ROS receipt time.
# applied_sequence wraps modulo 2^32 and identifies the accepted CMD associated
# with this state. speed and steering are normalized, dimensionless values:
# -100 maximum configured reverse/left, 0 neutral/straight, +100 maximum
# configured forward/right. enabled=false means propulsion is not applied.

std_msgs/Header header
uint8 protocol_version
uint32 applied_sequence
int8 speed
int8 steering
bool enabled
