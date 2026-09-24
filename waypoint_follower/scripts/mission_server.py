#!/usr/bin/env python3
import math
import os
import time

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.action import ActionServer, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from waypoint_follower.action import Mission


class MissionServer(Node):
    def __init__(self):
        super().__init__('mission_server')
        self.group = ReentrantCallbackGroup()
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10, callback_group=self.group
        )
        self.server = ActionServer(
            self,
            Mission,
            'follow_mission',
            self.execute_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.group,
        )

    def cancel_callback(self, goal_handle):
        return CancelResponse.ACCEPT

    def odom_callback(self, msg):
        q = msg.pose.pose.orientation
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        self.yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        )

    def drive_to(self, goal_handle, x, y, index, status, travelled):
        last_x, last_y = self.x, self.y
        while True:
            if goal_handle.is_cancel_requested:
                self.cmd_pub.publish(Twist())
                return False

            travelled[0] += math.hypot(self.x - last_x, self.y - last_y)
            last_x, last_y = self.x, self.y

            dx = x - self.x
            dy = y - self.y
            distance = math.hypot(dx, dy)

            feedback = Mission.Feedback()
            feedback.current_waypoint_index = index
            feedback.status = status
            feedback.distance_to_target = distance
            goal_handle.publish_feedback(feedback)

            if distance < 0.1:
                self.cmd_pub.publish(Twist())
                return True

            error = math.atan2(dy, dx) - self.yaw
            error = math.atan2(math.sin(error), math.cos(error))

            cmd = Twist()
            cmd.angular.z = max(-1.0, min(1.0, 1.5 * error))
            if abs(error) < 0.1:
                cmd.linear.x = min(0.15, 0.5 * distance)
            self.cmd_pub.publish(cmd)
            time.sleep(0.1)

    def execute_callback(self, goal_handle):
        path = os.path.join(
            get_package_share_directory('waypoint_follower'),
            'missions',
            goal_handle.request.mission_file,
        )
        with open(path) as f:
            mission = yaml.safe_load(f)

        waypoints = mission['waypoints']
        travelled = [0.0]
        completed = 0
        result = Mission.Result()

        for i, wp in enumerate(waypoints):
            status = f'en route to waypoint {i + 1}/{len(waypoints)}'
            if not self.drive_to(goal_handle, wp['x'], wp['y'], i, status, travelled):
                goal_handle.canceled()
                result.success = False
                result.total_distance = travelled[0]
                result.waypoints_completed = completed
                return result
            completed += 1

        if mission['return_to_base']:
            base = mission['base']
            index = len(waypoints)
            if not self.drive_to(
                goal_handle, base['x'], base['y'], index, 'returning to base', travelled
            ):
                goal_handle.canceled()
                result.success = False
                result.total_distance = travelled[0]
                result.waypoints_completed = completed
                return result

        goal_handle.succeed()
        result.success = True
        result.total_distance = travelled[0]
        result.waypoints_completed = completed
        return result


def main():
    rclpy.init()
    node = MissionServer()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()


if __name__ == '__main__':
    main()
