// generated from rosidl_typesupport_fastrtps_c/resource/idl__rosidl_typesupport_fastrtps_c.h.em
// with input from avaj_car_control:msg/DriveCommand.idl
// generated code does not contain a copyright notice
#ifndef AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_
#define AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_


#include <stddef.h>
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "avaj_car_control/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "avaj_car_control/msg/detail/drive_command__struct.h"
#include "fastcdr/Cdr.h"

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
bool cdr_serialize_avaj_car_control__msg__DriveCommand(
  const avaj_car_control__msg__DriveCommand * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
bool cdr_deserialize_avaj_car_control__msg__DriveCommand(
  eprosima::fastcdr::Cdr &,
  avaj_car_control__msg__DriveCommand * ros_message);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
size_t get_serialized_size_avaj_car_control__msg__DriveCommand(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
size_t max_serialized_size_avaj_car_control__msg__DriveCommand(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
bool cdr_serialize_key_avaj_car_control__msg__DriveCommand(
  const avaj_car_control__msg__DriveCommand * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
size_t get_serialized_size_key_avaj_car_control__msg__DriveCommand(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
size_t max_serialized_size_key_avaj_car_control__msg__DriveCommand(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, avaj_car_control, msg, DriveCommand)();

#ifdef __cplusplus
}
#endif

#endif  // AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_
