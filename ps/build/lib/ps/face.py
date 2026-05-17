#!/usr/bin/env python3

import cv2
import qi
import time
import numpy as np
import rclpy

from rclpy.node import Node
from sensor_msgs.msg import CompressedImage, Range

HEAD_PITCH_RESET_LIMIT = 0.15
HEAD_RESET_AFTER_LOST = 1.0

PEPPER_IP = "192.168.0.150"
PEPPER_PORT = 9559

IMAGE_TOPIC = "/pepper/front_camera/image_raw/compressed"
FRONT_SONAR_TOPIC = "/naoqi_driver/sonar/front"
BACK_SONAR_TOPIC = "/naoqi_driver/sonar/back"

SAFE_FRONT_DISTANCE = 0.65
STOP_RECT_AREA = 65000

MAX_FORWARD_SPEED = 0.4
MAX_TURN_SPEED = 0.25

LAST_TARGET_TIMEOUT = 2.0

HEAD_YAW_GAIN = 0.22
HEAD_PITCH_GAIN = 0.16

BASE_IMAGE_TURN_GAIN = 0.8
BASE_HEAD_TURN_GAIN = 0.45

HEAD_YAW_LIMIT_FOR_BASE = 0.35


class FacePersonFollower(Node):
    def __init__(self):
        super().__init__("face_person_follower")

        self.front_sonar = 999.0
        self.back_sonar = 999.0

        self.last_seen_time = 0.0
        self.last_error_x = 0.0
        self.last_error_y = 0.0
        self.last_rect_area = 0
        self.last_label = "NONE"

        self.get_logger().info("Connecting to Pepper...")
        self.session = qi.Session()
        self.session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")

        self.motion = self.session.service("ALMotion")
        self.motion.wakeUp()

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        self.image_sub = self.create_subscription(
            CompressedImage,
            IMAGE_TOPIC,
            self.image_callback,
            10
        )

        self.front_sonar_sub = self.create_subscription(
            Range,
            FRONT_SONAR_TOPIC,
            self.front_sonar_callback,
            10
        )

        self.back_sonar_sub = self.create_subscription(
            Range,
            BACK_SONAR_TOPIC,
            self.back_sonar_callback,
            10
        )

        self.get_logger().info("Follower started")

    def front_sonar_callback(self, msg):
        self.front_sonar = msg.range

    def back_sonar_callback(self, msg):
        self.back_sonar = msg.range

    def clamp(self, value, low, high):
        return max(low, min(high, value))

    def stop_robot(self):
        try:
            self.motion.moveToward(0.0, 0.0, 0.0)
        except Exception as e:
            self.get_logger().error(f"Stop failed: {e}")

    def get_head_yaw(self):
        try:
            angles = self.motion.getAngles(["HeadYaw"], True)
            return angles[0]
        except Exception:
            return 0.0

    def move_head_and_base(self, error_x, error_y, rect_area, target_active):
        head_yaw = self.get_head_yaw()

        yaw_change = -error_x * HEAD_YAW_GAIN
        pitch_change = error_y * HEAD_PITCH_GAIN

        turn_from_image = -error_x * BASE_IMAGE_TURN_GAIN

        if abs(head_yaw) > HEAD_YAW_LIMIT_FOR_BASE:
            turn_from_head = head_yaw * BASE_HEAD_TURN_GAIN
        else:
            turn_from_head = 0.0

        turn_speed = turn_from_image + turn_from_head
        turn_speed = self.clamp(turn_speed, -MAX_TURN_SPEED, MAX_TURN_SPEED)

        too_close_by_sonar = self.front_sonar < SAFE_FRONT_DISTANCE
        too_close_by_area = rect_area > STOP_RECT_AREA

        if too_close_by_sonar or too_close_by_area:
            forward_speed = 0.0
            status = "STOP CLOSE"
        elif target_active:
            forward_speed = MAX_FORWARD_SPEED
            status = "FOLLOW"
        else:
            forward_speed = 0.0
            status = "LAST SEEN TURN"

        try:
            self.motion.changeAngles(
                ["HeadYaw", "HeadPitch"],
                [float(yaw_change), float(pitch_change)],
                0.12
            )

            self.motion.moveToward(
                float(forward_speed),
                0.0,
                float(turn_speed)
            )

        except Exception as e:
            self.get_logger().error(f"Movement failed: {e}")
            status = "ERROR"

        return status, head_yaw, turn_speed
    def reset_head_if_needed(self):
        try:
            head_yaw, head_pitch = self.motion.getAngles(["HeadYaw", "HeadPitch"], True)

            if abs(head_pitch) > HEAD_PITCH_RESET_LIMIT:
                self.get_logger().info("Target lost and head pitch too high/low. Resetting head.")
                self.motion.setAngles(
                    ["HeadYaw", "HeadPitch"],
                    [0.0, 0.0],
                    0.15
                )
                return True

        except Exception as e:
            self.get_logger().error(f"Head reset failed: {e}")

        return False

    def image_callback(self, msg):
        now = time.time()

        np_arr = np.frombuffer(msg.data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return

        img_h, img_w, _ = frame.shape

        target_found = False
        target_x = None
        target_y = None
        rect_area = 0
        label = "NONE"

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(20, 20)
        )

        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda box: box[2] * box[3])

            target_x = x + w / 2
            target_y = y + h / 2
            rect_area = w * h
            target_found = True
            label = "FACE"

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        else:
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

            people, _ = self.hog.detectMultiScale(
                small_frame,
                winStride=(8, 8),
                padding=(16, 16),
                scale=1.05
            )

            if len(people) > 0:
                x, y, w, h = max(people, key=lambda box: box[2] * box[3])

                x = int(x * 2)
                y = int(y * 2)
                w = int(w * 2)
                h = int(h * 2)

                target_x = x + w / 2
                target_y = y + h / 3
                rect_area = w * h
                target_found = True
                label = "PERSON"

                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        cv2.circle(frame, (img_w // 2, img_h // 2), 5, (0, 0, 255), -1)

        if target_found:
            cv2.circle(frame, (int(target_x), int(target_y)), 5, (255, 255, 0), -1)

            error_x = (target_x - img_w / 2) / img_w
            error_y = (target_y - img_h / 2) / img_h

            self.last_seen_time = now
            self.last_error_x = error_x
            self.last_error_y = error_y
            self.last_rect_area = rect_area
            self.last_label = label

            status, head_yaw, turn_speed = self.move_head_and_base(
                error_x,
                error_y,
                rect_area,
                True
            )

        else:
            time_since_seen = now - self.last_seen_time

            if time_since_seen < LAST_TARGET_TIMEOUT:
                status, head_yaw, turn_speed = self.move_head_and_base(
                    self.last_error_x,
                    self.last_error_y,
                    self.last_rect_area,
                    False
                )

                cv2.putText(frame, "USING LAST TARGET", (20, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

            else:
                self.stop_robot()

                if time_since_seen > HEAD_RESET_AFTER_LOST:
                    self.reset_head_if_needed()

                status = "NO TARGET STOP / HEAD RESET CHECK"
                head_yaw = self.get_head_yaw()
                turn_speed = 0.0

        cv2.putText(frame, f"Mode: {status}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.putText(frame, f"Last: {self.last_label}", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.putText(frame, f"Rect area: {self.last_rect_area}", (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.putText(frame, f"Front sonar: {self.front_sonar:.2f} m", (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.putText(frame, f"HeadYaw: {head_yaw:.2f} Turn: {turn_speed:.2f}", (20, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow("Pepper Follow Tracking", frame)
        cv2.waitKey(1)

    def shutdown_robot(self):
        self.stop_robot()


def main(args=None):
    rclpy.init(args=args)
    node = FacePersonFollower()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.shutdown_robot()
    cv2.destroyAllWindows()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()