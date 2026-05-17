#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import rclpy.duration


class LaserRetime(Node):
    def __init__(self):
        super().__init__("laser_retime")
        self.pub = self.create_publisher(LaserScan, "/scan", 10)
        self.sub = self.create_subscription(
            LaserScan,
            "/naoqi_driver/laser",
            self.cb,
            10
        )
        self.get_logger().info("Fixing Pepper laser -> /scan")

    def cb(self, msg):
        now = self.get_clock().now()
        msg.header.stamp = (now - rclpy.duration.Duration(seconds=0.2)).to_msg()
        msg.header.frame_id = "base_footprint"

        n = len(msg.ranges)

        if n > 1:
            msg.angle_max = msg.angle_min + msg.angle_increment * (n - 1)

        msg.range_min = 0.1
        msg.range_max = 10.0

        msg.ranges = [
            r if math.isfinite(r) and 0.1 <= r <= 10.0 else float("inf")
            for r in msg.ranges
        ]

        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = LaserRetime()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()