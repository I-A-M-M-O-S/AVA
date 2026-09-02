cmake_minimum_required(VERSION 3.8)
project(rc_car_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(vision_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/DriveRequest.msg"
  "msg/DriveCommand.msg"
  "msg/VehicleStatus.msg"
  "msg/ActuatorStatus.msg"
  "msg/WheelEncoderState.msg"
  "msg/PylonObservation.msg"
  "msg/PylonObservationArray.msg"
  DEPENDENCIES std_msgs vision_msgs
)

ament_export_dependencies(rosidl_default_runtime)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_pylon_interfaces
    test/test_pylon_interfaces.py
    TIMEOUT 30
  )
endif()

ament_package()
