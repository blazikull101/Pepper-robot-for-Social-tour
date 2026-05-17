#!/usr/bin/env python3
#

import sys
import time
from pathlib import Path

import qi
import rclpy
from rclpy.node import Node

import numpy as np
from PIL import Image


PEPPER_IP = "192.168.0.150"
PEPPER_PORT = 9559

MAP_SAVE_PATH = "/home/wayfarer/p_ws/src/ps/maps/pepper_map.png"


class PepperExplore(Node):
    def __init__(self):
        super().__init__("pepper_explore")

        self.get_logger().info("Connecting to Pepper...")
        self.session = qi.Session()

        try:
            self.session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")
        except RuntimeError as e:
            self.get_logger().error(f"Could not connect to Pepper at {PEPPER_IP}:{PEPPER_PORT}")
            self.get_logger().error(str(e))
            rclpy.shutdown()
            return

        self.get_logger().info("Connected to Pepper.")

        self.navigation = self.session.service("ALNavigation")
        self.motion = self.session.service("ALMotion")
        self.tts = self.session.service("ALTextToSpeech")

        self.run_exploration()

    def run_exploration(self):
        self.get_logger().info("Waking Pepper up...")
        self.motion.wakeUp()

        self.tts.say("exploring.")

        radius = 10.0
        self.get_logger().info(f"Starting exploration with radius {radius} meters...")

        error_code = self.navigation.explore(radius)

        if error_code != 0:
            self.get_logger().error("Exploration failed.")
            self.tts.say("Exploration failed.")
            return

        self.get_logger().info("Exploration finished.")

        path = self.navigation.saveExploration()
        self.get_logger().info(f'Exploration saved on Pepper at: "{path}"')

        self.get_logger().info("Starting localization...")
        self.navigation.startLocalization()

        self.get_logger().info("Returning to initial position...")
        self.navigation.navigateToInMap([0.0, 0.0, 0.0])

        self.get_logger().info("Stopping localization...")
        self.navigation.stopLocalization()

        self.get_logger().info("Getting metrical map...")
        result_map = self.navigation.getMetricalMap()

        map_width = result_map[1]
        map_height = result_map[2]
        map_data = result_map[4]

        img = np.array(map_data).reshape(map_width, map_height)
        img = (100 - img) * 2.55
        img = np.array(img, np.uint8)

        save_path = Path(MAP_SAVE_PATH)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        image = Image.frombuffer(
            "L",
            (map_width, map_height),
            img,
            "raw",
            "L",
            0,
            1
        )

        image.save(str(save_path))

        self.get_logger().info(f"Map image saved at: {save_path}")
        self.tts.say("Exploration finished.")


def main(args=None):
    rclpy.init(args=args)

    node = PepperExplore()

    try:
        rclpy.spin_once(node, timeout_sec=1.0)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()