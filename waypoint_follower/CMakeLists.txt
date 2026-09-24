cmake_minimum_required(VERSION 3.8)
project(waypoint_follower)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(action_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "action/Mission.action"
  DEPENDENCIES action_msgs
)

install(PROGRAMS scripts/mission_server.py DESTINATION lib/${PROJECT_NAME} RENAME mission_server)
install(PROGRAMS scripts/mission_client.py DESTINATION lib/${PROJECT_NAME} RENAME mission_client)
install(DIRECTORY missions DESTINATION share/${PROJECT_NAME})

ament_package()
