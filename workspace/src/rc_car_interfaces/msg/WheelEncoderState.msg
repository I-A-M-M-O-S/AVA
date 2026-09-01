# Fully validated absolute quadrature counts for all four wheels.
# header.stamp is the Jetson ROS receipt time. sample_counter and each tick
# count are ESP-originated values. sample_counter wraps modulo 2^32; tick counts
# wrap from INT32_MAX to INT32_MIN and vice versa. Unit: one encoder count.
# Positive is forward vehicle motion on every wheel after ESP-side polarity
# normalization; negative is reverse. Unknown channels/extra fields are rejected.

std_msgs/Header header
uint8 protocol_version
uint32 sample_counter
int32 front_left_ticks
int32 front_right_ticks
int32 rear_left_ticks
int32 rear_right_ticks
