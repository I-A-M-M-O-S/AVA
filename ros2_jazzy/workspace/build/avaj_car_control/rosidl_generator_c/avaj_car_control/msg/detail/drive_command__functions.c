// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from avaj_car_control:msg/DriveCommand.idl
// generated code does not contain a copyright notice
#include "avaj_car_control/msg/detail/drive_command__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
avaj_car_control__msg__DriveCommand__init(avaj_car_control__msg__DriveCommand * msg)
{
  if (!msg) {
    return false;
  }
  // steering
  // acceleration
  return true;
}

void
avaj_car_control__msg__DriveCommand__fini(avaj_car_control__msg__DriveCommand * msg)
{
  if (!msg) {
    return;
  }
  // steering
  // acceleration
}

bool
avaj_car_control__msg__DriveCommand__are_equal(const avaj_car_control__msg__DriveCommand * lhs, const avaj_car_control__msg__DriveCommand * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // steering
  if (lhs->steering != rhs->steering) {
    return false;
  }
  // acceleration
  if (lhs->acceleration != rhs->acceleration) {
    return false;
  }
  return true;
}

bool
avaj_car_control__msg__DriveCommand__copy(
  const avaj_car_control__msg__DriveCommand * input,
  avaj_car_control__msg__DriveCommand * output)
{
  if (!input || !output) {
    return false;
  }
  // steering
  output->steering = input->steering;
  // acceleration
  output->acceleration = input->acceleration;
  return true;
}

avaj_car_control__msg__DriveCommand *
avaj_car_control__msg__DriveCommand__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  avaj_car_control__msg__DriveCommand * msg = (avaj_car_control__msg__DriveCommand *)allocator.allocate(sizeof(avaj_car_control__msg__DriveCommand), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(avaj_car_control__msg__DriveCommand));
  bool success = avaj_car_control__msg__DriveCommand__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
avaj_car_control__msg__DriveCommand__destroy(avaj_car_control__msg__DriveCommand * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    avaj_car_control__msg__DriveCommand__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
avaj_car_control__msg__DriveCommand__Sequence__init(avaj_car_control__msg__DriveCommand__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  avaj_car_control__msg__DriveCommand * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(avaj_car_control__msg__DriveCommand)) {
      return false;
    }
    data = (avaj_car_control__msg__DriveCommand *)allocator.zero_allocate(size, sizeof(avaj_car_control__msg__DriveCommand), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = avaj_car_control__msg__DriveCommand__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        avaj_car_control__msg__DriveCommand__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
avaj_car_control__msg__DriveCommand__Sequence__fini(avaj_car_control__msg__DriveCommand__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      avaj_car_control__msg__DriveCommand__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

avaj_car_control__msg__DriveCommand__Sequence *
avaj_car_control__msg__DriveCommand__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  avaj_car_control__msg__DriveCommand__Sequence * array = (avaj_car_control__msg__DriveCommand__Sequence *)allocator.allocate(sizeof(avaj_car_control__msg__DriveCommand__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = avaj_car_control__msg__DriveCommand__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
avaj_car_control__msg__DriveCommand__Sequence__destroy(avaj_car_control__msg__DriveCommand__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    avaj_car_control__msg__DriveCommand__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
avaj_car_control__msg__DriveCommand__Sequence__are_equal(const avaj_car_control__msg__DriveCommand__Sequence * lhs, const avaj_car_control__msg__DriveCommand__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!avaj_car_control__msg__DriveCommand__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
avaj_car_control__msg__DriveCommand__Sequence__copy(
  const avaj_car_control__msg__DriveCommand__Sequence * input,
  avaj_car_control__msg__DriveCommand__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(avaj_car_control__msg__DriveCommand)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(avaj_car_control__msg__DriveCommand);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    avaj_car_control__msg__DriveCommand * data =
      (avaj_car_control__msg__DriveCommand *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!avaj_car_control__msg__DriveCommand__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          avaj_car_control__msg__DriveCommand__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!avaj_car_control__msg__DriveCommand__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
