cmake_minimum_required(VERSION 3.8)
project(avaj_car_control)

find_package(ament_cmake REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(rc_car_interfaces REQUIRED)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(
    test_drive_commander
    test/test_drive_commander.py
    TIMEOUT 60
  )
endif()

install(PROGRAMS
  scripts/drive_commander
  scripts/drive_command_to_twist
  scripts/mode_manager
  scripts/safety_watchdog
  scripts/test_controller
  scripts/wasd_teleop
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
  PATTERN "__pycache__" EXCLUDE
)

ament_package()
