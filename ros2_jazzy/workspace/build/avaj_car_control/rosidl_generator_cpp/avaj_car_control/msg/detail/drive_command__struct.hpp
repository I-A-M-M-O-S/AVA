// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from avaj_car_control:msg/DriveCommand.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "avaj_car_control/msg/drive_command.hpp"


#ifndef AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__STRUCT_HPP_
#define AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__avaj_car_control__msg__DriveCommand __attribute__((deprecated))
#else
# define DEPRECATED__avaj_car_control__msg__DriveCommand __declspec(deprecated)
#endif

namespace avaj_car_control
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct DriveCommand_
{
  using Type = DriveCommand_<ContainerAllocator>;

  explicit DriveCommand_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->steering = 0;
      this->acceleration = 0;
    }
  }

  explicit DriveCommand_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->steering = 0;
      this->acceleration = 0;
    }
  }

  // field types and members
  using _steering_type =
    uint8_t;
  _steering_type steering;
  using _acceleration_type =
    uint8_t;
  _acceleration_type acceleration;

  // setters for named parameter idiom
  Type & set__steering(
    const uint8_t & _arg)
  {
    this->steering = _arg;
    return *this;
  }
  Type & set__acceleration(
    const uint8_t & _arg)
  {
    this->acceleration = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    avaj_car_control::msg::DriveCommand_<ContainerAllocator> *;
  using ConstRawPtr =
    const avaj_car_control::msg::DriveCommand_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<avaj_car_control::msg::DriveCommand_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<avaj_car_control::msg::DriveCommand_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      avaj_car_control::msg::DriveCommand_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<avaj_car_control::msg::DriveCommand_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      avaj_car_control::msg::DriveCommand_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<avaj_car_control::msg::DriveCommand_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<avaj_car_control::msg::DriveCommand_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<avaj_car_control::msg::DriveCommand_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__avaj_car_control__msg__DriveCommand
    std::shared_ptr<avaj_car_control::msg::DriveCommand_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__avaj_car_control__msg__DriveCommand
    std::shared_ptr<avaj_car_control::msg::DriveCommand_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DriveCommand_ & other) const
  {
    if (this->steering != other.steering) {
      return false;
    }
    if (this->acceleration != other.acceleration) {
      return false;
    }
    return true;
  }
  bool operator!=(const DriveCommand_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DriveCommand_

// alias to use template instance with default allocator
using DriveCommand =
  avaj_car_control::msg::DriveCommand_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace avaj_car_control

#endif  // AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__STRUCT_HPP_
