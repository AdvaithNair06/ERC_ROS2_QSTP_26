#!/usr/bin/env python3
import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions

from waypoint_follower.action import Mission


class MissionClient(Node):
    def __init__(self):
        super().__init__('mission_client')
        self.declare_parameter('mission_file', 'mission_square.yaml')
        self.client = ActionClient(self, Mission, 'follow_mission')

    def feedback_callback(self, msg):
        fb = msg.feedback
        print(f'{fb.status} ({fb.distance_to_target:.2f} m to target)')

    def send_mission(self, mission_file):
        self.client.wait_for_server()
        goal = Mission.Goal()
        goal.mission_file = mission_file

        send_future = self.client.send_goal_async(
            goal, feedback_callback=self.feedback_callback
        )
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()
        result_future = goal_handle.get_result_async()

        try:
            rclpy.spin_until_future_complete(self, result_future)
        except KeyboardInterrupt:
            print('Cancelling mission')
            cancel_future = goal_handle.cancel_goal_async()
            rclpy.spin_until_future_complete(self, cancel_future)
            rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result().result
        print(
            f'success={result.success} total_distance={result.total_distance:.2f} '
            f'waypoints_completed={result.waypoints_completed}'
        )


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = MissionClient()
    mission_file = sys.argv[1] if len(sys.argv) > 1 else None
    if mission_file is None or mission_file.startswith('--'):
        mission_file = node.get_parameter('mission_file').value
    node.send_mission(mission_file)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
