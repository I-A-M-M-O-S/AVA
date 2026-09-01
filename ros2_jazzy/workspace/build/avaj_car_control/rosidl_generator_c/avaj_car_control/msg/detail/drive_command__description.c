// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from avaj_car_control:msg/DriveCommand.idl
// generated code does not contain a copyright notice

#include "avaj_car_control/msg/detail/drive_command__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_avaj_car_control
const rosidl_type_hash_t *
avaj_car_control__msg__DriveCommand__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xf7, 0xa1, 0xb9, 0x3b, 0x1f, 0xa8, 0x6e, 0xc7,
      0x3f, 0xee, 0x23, 0xe0, 0x66, 0xe0, 0x94, 0x81,
      0xc8, 0x79, 0x44, 0xff, 0xee, 0x5f, 0x46, 0xaf,
      0x0b, 0xde, 0xef, 0x1d, 0x26, 0xd3, 0xa7, 0xef,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char avaj_car_control__msg__DriveCommand__TYPE_NAME[] = "avaj_car_control/msg/DriveCommand";

// Define type names, field names, and default values
static char avaj_car_control__msg__DriveCommand__FIELD_NAME__steering[] = "steering";
static char avaj_car_control__msg__DriveCommand__FIELD_NAME__acceleration[] = "acceleration";

static rosidl_runtime_c__type_description__Field avaj_car_control__msg__DriveCommand__FIELDS[] = {
  {
    {avaj_car_control__msg__DriveCommand__FIELD_NAME__steering, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {avaj_car_control__msg__DriveCommand__FIELD_NAME__acceleration, 12, 12},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
avaj_car_control__msg__DriveCommand__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {avaj_car_control__msg__DriveCommand__TYPE_NAME, 33, 33},
      {avaj_car_control__msg__DriveCommand__FIELDS, 2, 2},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "# Normalized driver input. Every value is limited to the inclusive range 0..100.\n"
  "# steering:    0 = fully left, 50 = straight, 100 = fully right\n"
  "# acceleration: 0 = full reverse, 50 = neutral, 100 = full forward\n"
  "uint8 steering\n"
  "uint8 acceleration";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
avaj_car_control__msg__DriveCommand__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {avaj_car_control__msg__DriveCommand__TYPE_NAME, 33, 33},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 246, 246},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
avaj_car_control__msg__DriveCommand__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *avaj_car_control__msg__DriveCommand__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
