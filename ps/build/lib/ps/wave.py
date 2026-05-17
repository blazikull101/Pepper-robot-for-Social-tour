#!/usr/bin/env python3

import time
import qi
import rclpy

from .wav import PepperWaveReal


PEPPER_IP = "192.168.0.150"
PEPPER_PORT = 9559

FOLLOW_DISTANCE = 0.8
STOP_DISTANCE = 0.4

MAX_FORWARD_SPEED = 3.58
MAX_TURN_SPEED = 1.5

FORWARD_GAIN = 0.35
TURN_GAIN = 0.7


class PersonDetectWave:
    def __init__(self):
        self.session = qi.Session()
        self.session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")

        self.motion = self.session.service("ALMotion")
        self.memory = self.session.service("ALMemory")
        self.tts = self.session.service("ALTextToSpeech")
        self.people = self.session.service("ALPeoplePerception")
        self.tracker = self.session.service("ALTracker")

        self.wave_gesture = PepperWaveReal()

        self.greeted_people = set()
        self.current_target_id = None
        self.last_seen_time = 0.0

        self.motion.wakeUp()
        self.people.subscribe("person_detect_wave")

        self.tracker.stopTracker()
        self.tracker.unregisterAllTargets()

        print("Person follower started.")
        print("Pepper will follow one person, say hello and wave once.")

    def clamp(self, value, low, high):
        return max(low, min(high, value))

    def get_people_list(self):
        try:
            people_list = self.memory.getData("PeoplePerception/PeopleList")
            if people_list in [None, [], 0, -1]:
                return []
            return list(people_list)
        except Exception as e:
            print("Could not read PeopleList:", e)
            return []

    def get_person_position(self, person_id):
        try:
            key = f"PeoplePerception/Person/{person_id}/PositionInRobotFrame"
            pos = self.memory.getData(key)

            if pos in [None, [], 0, -1]:
                return None

            return pos

        except Exception as e:
            print(f"Could not read position for person {person_id}:", e)
            return None

    def start_head_tracking(self, person_id):
        try:
            self.tracker.stopTracker()
            self.tracker.unregisterAllTargets()

            self.tracker.registerTarget("People", [person_id])
            self.tracker.setMode("Head")
            self.tracker.track("People")

            print(f"Head tracking person ID: {person_id}")

        except Exception as e:
            print(f"Could not head-track person {person_id}:", e)

    def wave_to_person_once(self, person_id):
        if person_id in self.greeted_people:
            return

        print(f"Saying hello and waving to person ID: {person_id}")

        try:
            self.motion.moveToward(0.0, 0.0, 0.0)
            self.tts.say("Hello!")
            self.wave_gesture.wave_motion()
            self.greeted_people.add(person_id)

        except Exception as e:
            print("Wave animation failed:", e)

    def follow_person(self, person_id):
        pos = self.get_person_position(person_id)

        if pos is None or len(pos) < 2:
            print("No position. Stopping.")
            self.motion.moveToward(0.0, 0.0, 0.0)
            return

        x = float(pos[0])
        y = float(pos[1])

        print(f"Target position x={x:.2f}, y={y:.2f}")

        distance_error = x - FOLLOW_DISTANCE

        if x < STOP_DISTANCE:
            forward_speed = 0.0
        else:
            forward_speed = self.clamp(
                distance_error * FORWARD_GAIN,
                0.0,
                MAX_FORWARD_SPEED
            )

        turn_speed = self.clamp(
            y * TURN_GAIN,
            -MAX_TURN_SPEED,
            MAX_TURN_SPEED
        )

        self.motion.moveToward(
            float(forward_speed),
            0.0,
            float(turn_speed)
        )

        print(f"Move forward={forward_speed:.2f}, turn={turn_speed:.2f}")

    def run(self):
        try:
            while True:
                people_list = self.get_people_list()
                print("PeopleList:", people_list)
                print("Current target:", self.current_target_id)

                if len(people_list) == 0:
                    print("No people. Stop.")
                    self.motion.moveToward(0.0, 0.0, 0.0)
                    time.sleep(0.5)
                    continue

                if self.current_target_id is None or self.current_target_id not in people_list:
                    self.current_target_id = people_list[0]
                    print(f"New target selected: {self.current_target_id}")
                    self.start_head_tracking(self.current_target_id)
                    self.wave_to_person_once(self.current_target_id)

                self.follow_person(self.current_target_id)

                time.sleep(0.2)

        except KeyboardInterrupt:
            print("Stopping...")

        self.stop()

    def stop(self):
        try:
            self.motion.moveToward(0.0, 0.0, 0.0)
            self.tracker.stopTracker()
            self.tracker.unregisterAllTargets()
            self.people.unsubscribe("person_detect_wave")
        except Exception as e:
            print("Stop failed:", e)


def main(args=None):
    rclpy.init(args=args)

    app = PersonDetectWave()

    try:
        app.run()
    except KeyboardInterrupt:
        pass

    app.stop()
    rclpy.shutdown()


if __name__ == "__main__":
    main()