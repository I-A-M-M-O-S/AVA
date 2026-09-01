# Fully validated ESP vehicle state. header.stamp is the Jetson ROS receipt
# time, not an ESP measurement time. header.frame_id is empty.
# protocol_version is the validated wire version; only 1 is currently known.
# last_accepted_sequence is the most recent CMD sequence accepted by the ESP
# and wraps modulo 2^32. Unknown owner/boolean/fault values are rejected before
# publication, so this message never represents an unvalidated wire value.

uint8 OWNER_SAFE=0
uint8 OWNER_MANUAL=1
uint8 OWNER_JETSON=2

# fault_flags is a bit mask. Unknown/reserved bits are rejected in protocol v1.
uint32 FAULT_NONE=0
uint32 FAULT_COMMAND_TIMEOUT=1
uint32 FAULT_COMMAND_CRC=2
uint32 FAULT_COMMAND_FORMAT=4
uint32 FAULT_MANUAL_TIMEOUT=8
uint32 FAULT_MOTOR_DRIVER=16
uint32 FAULT_STEERING=32
uint32 FAULT_ENCODER_FRONT_LEFT=64
uint32 FAULT_ENCODER_FRONT_RIGHT=128
uint32 FAULT_ENCODER_REAR_LEFT=256
uint32 FAULT_ENCODER_REAR_RIGHT=512
uint32 FAULT_PROTOCOL=1024

std_msgs/Header header
uint8 protocol_version
uint32 last_accepted_sequence
uint8 control_owner
bool jetson_locked
bool armed
bool enabled
uint32 fault_flags
