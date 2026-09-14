import  rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

class Listener(Node):
	def __init__(self):
		super().__init__('listener')
		self.sub = self.create_subscription(Float32,'/random',self.callback,10)
		
	def callback(self,msg):
		self.get_logger().info(f'Got {msg.data*2:.2f}')


def main():
	rclpy.init()
	node = Listener()
	rclpy.spin(node)
	node.destroy_node()
	rclpy.shutdown()
