#!/usr/bin/env python3

import time
from pathlib import Path
from .wav import PepperWaveReal
import qi
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


PEPPER_IP = "192.168.0.150"
PEPPER_PORT = 9559

TEXT_FILE = "/home/wayfarer/p_ws/src/ps/text/sp.txt"


class PepperSpeechGesture(Node):
    def __init__(self):
        super().__init__("pepper_speech_gesture")

        self.speech_pub = self.create_publisher(String, "/pepper_say", 10)

        self.get_logger().info("Connecting to Pepper...")
        self.session = qi.Session()
        self.session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")

        self.motion = self.session.service("ALMotion")
        self.motion.wakeUp()

        self.get_logger().info("Connected to Pepper")
        self.wave_gesture = PepperWaveReal()

    def read_text(self):
        path = Path(TEXT_FILE)
        if not path.exists():
            self.get_logger().error(f"Text file not found: {TEXT_FILE}")
            return ""
        return path.read_text().strip()

    def send_speech(self, text):
        msg = String()
        msg.data = text
        self.speech_pub.publish(msg)
        self.get_logger().info("Sent speech")

    def run(self):
        text = self.read_text()

        if text == "":
            self.get_logger().error("No speech text")
            return

        self.send_speech(text)
        time.sleep(0.1)  # Wait for speech to start
        self.wave_gesture.wave_motion()

        while rclpy.ok():
            self.wave_gesture.explaining_motions()
            time.sleep(0.5)
            self.wave_gesture.explaining_motions_2()
            time.sleep(0.5)


def main(args=None):
    rclpy.init(args=args)

    node = PepperSpeechGesture()

    try:
        node.run()
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()