// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from avaj_car_control:msg/DriveCommand.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "avaj_car_control/msg/drive_command.hpp"


#ifndef AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__BUILDER_HPP_
#define AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "avaj_car_control/msg/detail/drive_command__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace avaj_car_control
{

namespace msg
{

namespace builder
{

class Init_DriveCommand_acceleration
{
public:
  explicit Init_DriveCommand_acceleration(::avaj_car_control::msg::DriveCommand & msg)
  : msg_(msg)
  {}
  ::avaj_car_control::msg::DriveCommand acceleration(::avaj_car_control::msg::DriveCommand::_acceleration_type arg)
  {
    msg_.acceleration = std::move(arg);
    return std::move(msg_);
  }

private:
  ::avaj_car_control::msg::DriveCommand msg_;
};

class Init_DriveCommand_steering
{
public:
  Init_DriveCommand_steering()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DriveCommand_acceleration steering(::avaj_car_control::msg::DriveCommand::_steering_type arg)
  {
    msg_.steering = std::move(arg);
    return Init_DriveCommand_acceleration(msg_);
  }

private:
  ::avaj_car_control::msg::DriveCommand msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::avaj_car_control::msg::DriveCommand>()
{
  return avaj_car_control::msg::builder::Init_DriveCommand_steering();
}

}  // namespace avaj_car_control

#endif  // AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__BUILDER_HPP_
