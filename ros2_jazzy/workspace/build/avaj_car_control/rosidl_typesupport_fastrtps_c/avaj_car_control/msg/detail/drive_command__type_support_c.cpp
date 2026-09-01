// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from avaj_car_control:msg/DriveCommand.idl
// generated code does not contain a copyright notice
#include "avaj_car_control/msg/detail/drive_command__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <cstddef>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/serialization_helpers.hpp"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "avaj_car_control/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "avaj_car_control/msg/detail/drive_command__struct.h"
#include "avaj_car_control/msg/detail/drive_command__functions.h"
#include "fastcdr/Cdr.h"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

// includes and forward declarations of message dependencies and their conversion functions

#if defined(__cplusplus)
extern "C"
{
#endif


// forward declare type support functions


using _DriveCommand__ros_msg_type = avaj_car_control__msg__DriveCommand;


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
bool cdr_serialize_avaj_car_control__msg__DriveCommand(
  const avaj_car_control__msg__DriveCommand * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: steering
  {
    cdr << ros_message->steering;
  }

  // Field name: acceleration
  {
    cdr << ros_message->acceleration;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
bool cdr_deserialize_avaj_car_control__msg__DriveCommand(
  eprosima::fastcdr::Cdr & cdr,
  avaj_car_control__msg__DriveCommand * ros_message)
{
  // Field name: steering
  {
    cdr >> ros_message->steering;
  }

  // Field name: acceleration
  {
    cdr >> ros_message->acceleration;
  }

  return true;
}  // NOLINT(readability/fn_size)


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
size_t get_serialized_size_avaj_car_control__msg__DriveCommand(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _DriveCommand__ros_msg_type * ros_message = static_cast<const _DriveCommand__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: steering
  {
    size_t item_size = sizeof(ros_message->steering);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: acceleration
  {
    size_t item_size = sizeof(ros_message->acceleration);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
size_t max_serialized_size_avaj_car_control__msg__DriveCommand(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;

  // Field name: steering
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: acceleration
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }


  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = avaj_car_control__msg__DriveCommand;
    is_plain =
      (
      offsetof(DataType, acceleration) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
bool cdr_serialize_key_avaj_car_control__msg__DriveCommand(
  const avaj_car_control__msg__DriveCommand * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: steering
  {
    cdr << ros_message->steering;
  }

  // Field name: acceleration
  {
    cdr << ros_message->acceleration;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
size_t get_serialized_size_key_avaj_car_control__msg__DriveCommand(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _DriveCommand__ros_msg_type * ros_message = static_cast<const _DriveCommand__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;

  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: steering
  {
    size_t item_size = sizeof(ros_message->steering);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: acceleration
  {
    size_t item_size = sizeof(ros_message->acceleration);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_avaj_car_control
size_t max_serialized_size_key_avaj_car_control__msg__DriveCommand(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;
  // Field name: steering
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: acceleration
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = avaj_car_control__msg__DriveCommand;
    is_plain =
      (
      offsetof(DataType, acceleration) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}


static bool _DriveCommand__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const avaj_car_control__msg__DriveCommand * ros_message = static_cast<const avaj_car_control__msg__DriveCommand *>(untyped_ros_message);
  (void)ros_message;
  return cdr_serialize_avaj_car_control__msg__DriveCommand(ros_message, cdr);
}

static bool _DriveCommand__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  avaj_car_control__msg__DriveCommand * ros_message = static_cast<avaj_car_control__msg__DriveCommand *>(untyped_ros_message);
  (void)ros_message;
  return cdr_deserialize_avaj_car_control__msg__DriveCommand(cdr, ros_message);
}

static uint32_t _DriveCommand__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_avaj_car_control__msg__DriveCommand(
      untyped_ros_message, 0));
}

static size_t _DriveCommand__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_avaj_car_control__msg__DriveCommand(
    full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}


static message_type_support_callbacks_t __callbacks_DriveCommand = {
  "avaj_car_control::msg",
  "DriveCommand",
  _DriveCommand__cdr_serialize,
  _DriveCommand__cdr_deserialize,
  _DriveCommand__get_serialized_size,
  _DriveCommand__max_serialized_size,
  nullptr
};

static rosidl_message_type_support_t _DriveCommand__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_DriveCommand,
  get_message_typesupport_handle_function,
  &avaj_car_control__msg__DriveCommand__get_type_hash,
  &avaj_car_control__msg__DriveCommand__get_type_description,
  &avaj_car_control__msg__DriveCommand__get_type_description_sources,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, avaj_car_control, msg, DriveCommand)() {
  return &_DriveCommand__type_support;
}

#if defined(__cplusplus)
}
#endif
