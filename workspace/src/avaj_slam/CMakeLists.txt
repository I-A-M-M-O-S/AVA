cmake_minimum_required(VERSION 3.8)
project(avaj_slam)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch config urdf scripts
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS scripts/save_map.sh
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
