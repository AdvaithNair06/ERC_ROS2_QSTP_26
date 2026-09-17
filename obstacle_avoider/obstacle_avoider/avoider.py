import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan


class Avoider(Node):
    def __init__(self):
        super().__init__('avoider')
        self.is_active = False
        self.angular_z = 1.0
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(LaserScan, '/scan', self.callback, 10)
        self.srv = self.create_service(SetBool, '/toggle_robot', self.toggle_callback)

    def toggle_callback(self, request, response):
        self.is_active = request.data
        response.success = True
        response.message = 'Robot toggled'
        return response

    def callback(self, msg):
        twist = Twist()

        if not self.is_active:
            self.pub.publish(twist)
            return

        front = msg.ranges[0]

        if front > 1.0:
            self.angular_z = max(0.2, self.angular_z - 0.01)
            twist.linear.x = 0.15
            twist.angular.z = self.angular_z
        else:
            left = msg.ranges[90]
            right = msg.ranges[270]
            twist.linear.x = 0.05
            twist.angular.z = 0.5 if left > right else -0.5

        self.pub.publish(twist)


def main():
    rclpy.init()
    node = Avoider()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
