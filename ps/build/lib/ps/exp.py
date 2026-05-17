#!/usr/bin/env python3

import sys

import qi
import rclpy
from rclpy.node import Node
import math


PEPPER_IP = "192.168.0.150"
PEPPER_PORT = 9559


class PepperLocalize(Node):
    def __init__(self):
        super().__init__("pepper_localize")

        self.declare_parameter("explo", "")
        self.declare_parameter("target_x", 0.5)
        self.declare_parameter("target_y", 0.5)
        self.declare_parameter("target_theta", 0.0)

        self.exploration_file = self.get_parameter("explo").value
        self.target_x = self.get_parameter("target_x").value
        self.target_y = self.get_parameter("target_y").value
        self.target_theta = self.get_parameter("target_theta").value

        if not self.exploration_file:
            self.get_logger().error("No exploration file given.")
            self.get_logger().error("Run like this:")
            self.get_logger().error(
                "ros2 run ps localize --ros-args -p explo:=/path/to/file.explo"
            )
            return

        self.get_logger().info("Connecting to Pepper...")
        self.session = qi.Session()

        try:
            self.session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")
        except RuntimeError as e:
            self.get_logger().error(f"Could not connect to Pepper at {PEPPER_IP}:{PEPPER_PORT}")
            self.get_logger().error(str(e))
            return

        self.navigation = self.session.service("ALNavigation")
        self.motion = self.session.service("ALMotion")

        self.run_localization()

    def run_localization(self):
        self.get_logger().info("Waking Pepper up...")
        self.motion.wakeUp()

        self.get_logger().info(f"Loading exploration file: {self.exploration_file}")
        self.navigation.loadExploration(self.exploration_file)

        self.get_logger().info("Relocalizing in map...")

        guess = [0.0, 0.0, 0.0]
        self.navigation.relocalizeInMap(guess)

        self.get_logger().info("Starting localization...")
        self.navigation.startLocalization()

        position = self.navigation.getRobotPositionInMap()[0]
        self.get_logger().info(f"Current map position: {position}")

        dx = position[0] - guess[0]
        dy = position[1] - guess[1]
        distance_from_origin = math.sqrt(dx * dx + dy * dy)

        self.get_logger().info(f"Distance from map origin: {distance_from_origin:.2f} m")

        if distance_from_origin > 0.5:
            self.get_logger().warn(
                "Pepper does not seem close to the map origin. Move Pepper near the exploration start point."
            )
            self.navigation.stopLocalization()
            return

        target = [self.target_x, self.target_y, self.target_theta]

        self.get_logger().info(f"Navigating to target in map: {target}")
        self.navigation.navigateToInMap(target)

        position = self.navigation.getRobotPositionInMap()[0]
        self.get_logger().info(f"I reached: {position}")

        self.get_logger().info("Stopping localization...")
        self.navigation.stopLocalization()


def main(args=None):
    rclpy.init(args=args)

    node = PepperLocalize()

    try:
        rclpy.spin_once(node, timeout_sec=1.0)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()