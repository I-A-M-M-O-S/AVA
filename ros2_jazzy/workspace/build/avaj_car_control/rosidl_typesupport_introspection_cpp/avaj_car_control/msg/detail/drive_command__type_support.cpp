// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from avaj_car_control:msg/DriveCommand.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "avaj_car_control/msg/detail/drive_command__functions.h"
#include "avaj_car_control/msg/detail/drive_command__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace avaj_car_control
{

namespace msg
{

namespace rosidl_typesupport_introspection_cpp
{

void DriveCommand_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) avaj_car_control::msg::DriveCommand(_init);
}

void DriveCommand_fini_function(void * message_memory)
{
  auto typed_message = static_cast<avaj_car_control::msg::DriveCommand *>(message_memory);
  typed_message->~DriveCommand();
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember DriveCommand_message_member_array[2] = {
  {
    "steering",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(avaj_car_control::msg::DriveCommand, steering),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "acceleration",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(avaj_car_control::msg::DriveCommand, acceleration),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers DriveCommand_message_members = {
  "avaj_car_control::msg",  // message namespace
  "DriveCommand",  // message name
  2,  // number of fields
  sizeof(avaj_car_control::msg::DriveCommand),
  false,  // has_any_key_member_
  DriveCommand_message_member_array,  // message members
  DriveCommand_init_function,  // function to initialize message memory (memory has to be allocated)
  DriveCommand_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t DriveCommand_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &DriveCommand_message_members,
  get_message_typesupport_handle_function,
  &avaj_car_control__msg__DriveCommand__get_type_hash,
  &avaj_car_control__msg__DriveCommand__get_type_description,
  &avaj_car_control__msg__DriveCommand__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace avaj_car_control


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<avaj_car_control::msg::DriveCommand>()
{
  return &::avaj_car_control::msg::rosidl_typesupport_introspection_cpp::DriveCommand_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, avaj_car_control, msg, DriveCommand)() {
  return &::avaj_car_control::msg::rosidl_typesupport_introspection_cpp::DriveCommand_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
