// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from avaj_car_control:msg/DriveCommand.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "avaj_car_control/msg/drive_command.h"


#ifndef AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__STRUCT_H_
#define AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

/// Struct defined in msg/DriveCommand in the package avaj_car_control.
/**
  * Normalized driver input. Every value is limited to the inclusive range 0..100.
  * steering:    0 = fully left, 50 = straight, 100 = fully right
  * acceleration: 0 = full reverse, 50 = neutral, 100 = full forward
 */
typedef struct avaj_car_control__msg__DriveCommand
{
  uint8_t steering;
  uint8_t acceleration;
} avaj_car_control__msg__DriveCommand;

// Struct for a sequence of avaj_car_control__msg__DriveCommand.
typedef struct avaj_car_control__msg__DriveCommand__Sequence
{
  avaj_car_control__msg__DriveCommand * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} avaj_car_control__msg__DriveCommand__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // AVAJ_CAR_CONTROL__MSG__DETAIL__DRIVE_COMMAND__STRUCT_H_
