// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from avaj_car_control:msg/DriveCommand.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "avaj_car_control/msg/drive_command.hpp"


#ifndef AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__TRAITS_HPP_
#define AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "avaj_car_control/msg/detail/drive_command__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace avaj_car_control
{

namespace msg
{

inline void to_flow_style_yaml(
  const DriveCommand & msg,
  std::ostream & out)
{
  out << "{";
  // member: steering
  {
    out << "steering: ";
    rosidl_generator_traits::value_to_yaml(msg.steering, out);
    out << ", ";
  }

  // member: acceleration
  {
    out << "acceleration: ";
    rosidl_generator_traits::value_to_yaml(msg.acceleration, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DriveCommand & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: steering
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "steering: ";
    rosidl_generator_traits::value_to_yaml(msg.steering, out);
    out << "\n";
  }

  // member: acceleration
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "acceleration: ";
    rosidl_generator_traits::value_to_yaml(msg.acceleration, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DriveCommand & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace avaj_car_control

namespace rosidl_generator_traits
{

[[deprecated("use avaj_car_control::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const avaj_car_control::msg::DriveCommand & msg,
  std::ostream & out, size_t indentation = 0)
{
  avaj_car_control::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use avaj_car_control::msg::to_yaml() instead")]]
inline std::string to_yaml(const avaj_car_control::msg::DriveCommand & msg)
{
  return avaj_car_control::msg::to_yaml(msg);
}

template<>
inline const char * data_type<avaj_car_control::msg::DriveCommand>()
{
  return "avaj_car_control::msg::DriveCommand";
}

template<>
inline const char * name<avaj_car_control::msg::DriveCommand>()
{
  return "avaj_car_control/msg/DriveCommand";
}

template<>
struct has_fixed_size<avaj_car_control::msg::DriveCommand>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<avaj_car_control::msg::DriveCommand>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<avaj_car_control::msg::DriveCommand>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__TRAITS_HPP_
