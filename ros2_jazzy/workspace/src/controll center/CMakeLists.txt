cmake_minimum_required(VERSION 3.8)
project(control_center)

find_package(ament_cmake REQUIRED)
find_package(avaj_car_control REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)

# The requested source file has no conventional extension. Copy it to a
# temporary C++-named build source so every CMake/compiler version recognizes it.
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/c++ ${CMAKE_CURRENT_BINARY_DIR}/control_center.cpp COPYONLY)
add_executable(control_center_node ${CMAKE_CURRENT_BINARY_DIR}/control_center.cpp)
target_compile_features(control_center_node PUBLIC cxx_std_17)
ament_target_dependencies(control_center_node
  avaj_car_control
  nav_msgs
  rclcpp
  sensor_msgs
  std_msgs
)

install(TARGETS control_center_node DESTINATION lib/${PROJECT_NAME})
install(PROGRAMS scripts/control_center DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})
ament_package()
