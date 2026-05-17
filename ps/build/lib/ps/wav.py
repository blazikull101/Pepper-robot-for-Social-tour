#!/usr/bin/env python3
# This contains various gestures

import os
import time
import qi
import rclpy
from rclpy.node import Node


PEPPER_IP = "192.168.0.150"
PEPPER_PORT = 9559


class PepperWaveReal(Node):
    def __init__(self):
        super().__init__("pepper_wave_real")

        self.state_file = "/home/wayfarer/pepper_ros2_ws/src/pepper_speech_ros2/pepper_speech_ros2/previous_gesture.txt"
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

        self.get_logger().info("Connecting to Pepper...")
        self.session = qi.Session()
        self.session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")

        self.motion = self.session.service("ALMotion")
        self.motion.wakeUp()

        self.get_logger().info("Connected")

    def get_last_gesture_name(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                return f.read().strip()
        return "none"

    def set_current_gesture_name(self, name):
        with open(self.state_file, "w") as f:
            f.write(name)

    def execute_transition(self, waypoints):
        last = self.get_last_gesture_name()
        self.get_logger().info(f"Last gesture: {last}")

        if last == "listening_gesture.launch.py":
            self.get_logger().info("Applying transition...")

            bridge = [0.169, -0.5, 1.184, 0.5, -0.522, 0.5]
            shifted = [wp[:-1] + [wp[-1] + 1.0] for wp in waypoints]

            return [bridge] + shifted

        return waypoints

    def add_waypoints(self, names, angles, times, joint_names, wps):
        for j, joint in enumerate(joint_names):
            names.append(joint)

            a = []
            t = []

            for wp in wps:
                a.append(float(wp[j]))

                time_val = max(0.1, float(wp[-1]))
                t.append(time_val)

            angles.append(a)
            times.append(t)

    def wave_motion(self):

      

        l_arm_joints = [
            "LShoulderPitch",
            "LShoulderRoll",
            "LElbowYaw",
            "LElbowRoll",
            "LWristYaw",
        ]

        l_arm_wps = [
            [1.274, 0.067, -0.485, -0.706, -0.424, 0.5],
            [0.13, 0.3, -1.951, -1.562, 0.877, 1.0],
            [0.1, 0.0, -1.545, -1.7, 0.9, 1.5],
            [0.13, 0.3, -1.951, -1.562, 0.877, 2.0],
            [0.1, 0.0, -1.545, -1.7, 0.9, 2.5],
            [0.13, 0.3, -1.8, -1.562, 0.877, 3.0],
            [1.5,0.2,-1.2,-0.5,0.0,3.5]
        ]

        r_arm_joints = [
            "RShoulderPitch",
            "RShoulderRoll",
            "RElbowYaw",
            "RElbowRoll",
            "RWristYaw",
        ]

        r_arm_wps = [
            [1.3, 0.07, 0.5, 0.7, 0.42, 0.5],
        ]

        r_arm_wps = self.execute_transition(r_arm_wps)

        # Real Pepper hands (NOT finger joints)
        l_hand_joints = ["LHand"]
        r_hand_joints = ["RHand"]

        l_hand_wps = [
            [1.0, 0.7],  # open
        ]

        r_hand_wps = [
            [0.0, 0.5],  # closed
        ]

        names = []
        angles = []
        times = []

        self.add_waypoints(names, angles, times, l_arm_joints, l_arm_wps)
        self.add_waypoints(names, angles, times, r_arm_joints, r_arm_wps)
        self.add_waypoints(names, angles, times, l_hand_joints, l_hand_wps)
        self.add_waypoints(names, angles, times, r_hand_joints, r_hand_wps)

        self.get_logger().info("Executing wave gesture...")

        self.motion.angleInterpolation(names, angles, times, True)

        self.set_current_gesture_name("wave_hello_gesture.launch.py")
        self.get_logger().info("Done")

    def explaining_motions(self):
   

        l_arm_joints = [
            "LShoulderPitch",
            "LShoulderRoll",
            "LElbowYaw",
            "LElbowRoll",
            "LWristYaw",
        ]

        r_arm_joints = [
            "RShoulderPitch",
            "RShoulderRoll",
            "RElbowYaw",
            "RElbowRoll",
            "RWristYaw",
        ]

        l_arm_wps = [
            [1.274, 0.067, -0.485, -0.706, -0.424, 0.5],
            [0.958, 0.151, -0.981, -0.790, -1.824, 1.0],
            [0.958, 0.151, -0.981, -0.790, -1.824, 2.0],
            [1.274, 0.067, -0.485, -0.706, -0.424, 2.5],
        ]

        r_arm_wps = [
            [1.274, 0.067, 0.485, 0.706, 0.424, 0.5],
            [0.958, 0.151, 0.981, 0.790, 1.824, 1.0],
            [0.958, 0.151, 0.981, 0.790, 1.824, 1.5],
            [1.274, 0.067, 0.485, 0.706, 0.424, 2.0],
        ]

        l_hand_joints = ["LHand"]
        r_hand_joints = ["RHand"]

        l_hand_wps = [
            [0.2, 1.0],
            [1.0, 2.0],
            [0.2, 2.5],
        ]

        r_hand_wps = [
            [0.2, 1.0],
            [1.0, 1.7],
            [0.2, 2.5],
        ]

        names = []
        angles = []
        times = []

        self.add_waypoints(names, angles, times, l_arm_joints, l_arm_wps)
        self.add_waypoints(names, angles, times, r_arm_joints, r_arm_wps)
        self.add_waypoints(names, angles, times, l_hand_joints, l_hand_wps)
        self.add_waypoints(names, angles, times, r_hand_joints, r_hand_wps)

        self.get_logger().info("Executing explaining gesture...")
        self.motion.angleInterpolation(names, angles, times, True)

        self.set_current_gesture_name("explaining_gesture.launch.py")
        self.get_logger().info("Done")
    def explaining_motions_2(self):
      
        

        l_arm_joints = [
            "LShoulderPitch",
            "LShoulderRoll",
            "LElbowYaw",
            "LElbowRoll",
            "LWristYaw",
        ]

        r_arm_joints = [
            "RShoulderPitch",
            "RShoulderRoll",
            "RElbowYaw",
            "RElbowRoll",
            "RWristYaw",
        ]

        l_arm_wps = [
            [1.206, 0.193, -1.409, -1.092, -1.2, 0.5],
            [0.846, 0.378, -1.635, -1.562, 0.0, 1.0],
            [1.229, 0.009, -1.049, -0.638, -1.2, 1.5],
        ]

        r_arm_wps = [
            [1.206, 0.193, 1.409, 1.092, 1.2, 0.4],
            [0.846, 0.378, 1.635, 1.562, 0.0, 1.0],
            [1.229, 0.009, 1.049, 0.638, 1.2, 1.4],
        ]

        r_arm_wps = self.execute_transition(r_arm_wps)

        # Real Pepper hands use LHand/RHand, not LFinger/RFinger joints.
        l_hand_joints = ["LHand"]
        r_hand_joints = ["RHand"]

        l_hand_wps = [
            [1.0, 0.5],
            [0.2, 1.0],
            [1.0, 2.5],
        ]

        r_hand_wps = [
            [1.0, 0.4],
            [0.2, 1.0],
            [1.0, 1.4],
        ]

        names = []
        angles = []
        times = []

        self.add_waypoints(names, angles, times, l_arm_joints, l_arm_wps)
        self.add_waypoints(names, angles, times, r_arm_joints, r_arm_wps)
        self.add_waypoints(names, angles, times, l_hand_joints, l_hand_wps)
        self.add_waypoints(names, angles, times, r_hand_joints, r_hand_wps)

        self.get_logger().info("Executing explaining gesture 2...")
        self.motion.angleInterpolation(names, angles, times, True)

        self.set_current_gesture_name("explaining_gesture_2.launch.py")
        self.get_logger().info("Done")
        
    def listening_motion(self):
        head_joints = ["HeadYaw", "HeadPitch"]
        head_wps = [
            [1.0, 0.4, 0.5],
        ]

        l_arm_joints = [
            "LShoulderPitch",
            "LShoulderRoll",
            "LElbowYaw",
            "LElbowRoll",
            "LWristYaw",
        ]

        r_arm_joints = [
            "RShoulderPitch",
            "RShoulderRoll",
            "RElbowYaw",
            "RElbowRoll",
            "RWristYaw",
        ]

        l_arm_wps = [
            [1.3, 0.07, -0.5, -0.7, -0.42, 0.1],
        ]

        r_arm_wps = [
            [0.169, -1.0, 1.184, 1.562, -0.522, 0.4],
            [0.169, 0.059, 1.184, 1.562, -0.522, 0.8],
        ]

        # Real Pepper hands use LHand/RHand, not individual finger joints.
        l_hand_joints = ["LHand"]
        r_hand_joints = ["RHand"]

        l_hand_wps = [
            [0.0, 0.5],
        ]

        r_hand_wps = [
            [1.0, 0.5],
        ]

        names = []
        angles = []
        times = []

        self.add_waypoints(names, angles, times, head_joints, head_wps)
        self.add_waypoints(names, angles, times, l_arm_joints, l_arm_wps)
        self.add_waypoints(names, angles, times, r_arm_joints, r_arm_wps)
        self.add_waypoints(names, angles, times, l_hand_joints, l_hand_wps)
        self.add_waypoints(names, angles, times, r_hand_joints, r_hand_wps)

        self.get_logger().info("Executing listening gesture...")
        self.motion.angleInterpolation(names, angles, times, True)

        self.set_current_gesture_name("listening_gesture.launch.py")
        self.get_logger().info("Done")

    def initial(self):
            head_joints = ["HeadYaw", "HeadPitch"]
            head_wps = [
                [0.0, 0.0, 0.5],
            ]

            l_arm_joints = [
                "LShoulderPitch",
                "LShoulderRoll",
                "LElbowYaw",
                "LElbowRoll",
                "LWristYaw",
            ]

            r_arm_joints = [
                "RShoulderPitch",
                "RShoulderRoll",
                "RElbowYaw",
                "RElbowRoll",
                "RWristYaw",
            ]

            l_arm_wps = [
                [1.274, 0.067, -0.485, -0.706, -0.424, 1.0],
            ]

            r_arm_wps = [
                [1.274, 0.067, 0.485, 0.706, 0.424, 1.0],
            ]

            l_hand_joints = ["LHand"]
            r_hand_joints = ["RHand"]

            l_hand_wps = [
                [0.0, 0.7],
            ]

            r_hand_wps = [
                [0.0, 0.7],
            ]

            names = []
            angles = []
            times = []

            self.add_waypoints(names, angles, times, head_joints, head_wps)
            self.add_waypoints(names, angles, times, l_arm_joints, l_arm_wps)
            self.add_waypoints(names, angles, times, r_arm_joints, r_arm_wps)
            self.add_waypoints(names, angles, times, l_hand_joints, l_hand_wps)
            self.add_waypoints(names, angles, times, r_hand_joints, r_hand_wps)

            self.get_logger().info("Moving to initial pose...")
            self.motion.angleInterpolation(names, angles, times, True)

            self.set_current_gesture_name("initial_gesture.launch.py")
            self.get_logger().info("Initial pose done")        


    def loop(self):
        try:
            self.wave_motion()
            time.sleep(2.0)
            self.explaining_motions()
            time.sleep(2.0)
            self.explaining_motions_2()
            time.sleep(2.0)
            self.listening_motion()
            time.sleep(2.0)
            self.initial()
            time.sleep(2.0) 
        except KeyboardInterrupt:
            self.get_logger().info("Stopped")


def main(args=None):
    rclpy.init(args=args)

    node = PepperWaveReal()

    node.loop()

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()