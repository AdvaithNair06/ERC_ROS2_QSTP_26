import rclpy
import random
from rclpy.node import Node
from std_msgs.msg import Float32

class Talker(Node):
	def __init__(self):
		super().__init__('talker')
		self.pub = self.create_publisher(Float32,'/random',10)
		self.timer = self.create_timer(1.0,self.tick)
	def tick(self):
		msg = Float32()
		msg.data = random.uniform(67.0,69.0)
		self.pub.publish(msg)
		self.get_logger().info(f'Published {msg.data:.2f}')


def main():
	rclpy.init()
	node = Talker()
	rclpy.spin(node)
	node.destroy_node()
	rclpy.shutdown()


