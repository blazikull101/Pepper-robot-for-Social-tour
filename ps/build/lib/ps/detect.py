#!/usr/bin/env python3

import time
import qi

PEPPER_IP = "192.168.0.150"
PEPPER_PORT = 9559

TARGET_TAG = "box"   # change this to your trained object tag


def main():
    print("Connecting to Pepper...")

    session = qi.Session()
    session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")

    vision = session.service("ALVisionRecognition")
    memory = session.service("ALMemory")
    tts = session.service("ALTextToSpeech")
    motion = session.service("ALMotion")

    motion.wakeUp()

    vision.setMaxOutObjs(5)

    subscriber_name = "object_detector"

    print("Subscribing to ALVisionRecognition...")
    vision.subscribe(subscriber_name)

    print("Looking for object with tag:", TARGET_TAG)

    last_spoken = 0.0

    try:
        while True:
            data = memory.getData("PictureDetected")

            if data and len(data) >= 2:
                detected_objects = data[1]

                for obj in detected_objects:
                    labels = obj[0]
                    matched_keypoints = obj[1]
                    ratio = obj[2]
                    boundary_points = obj[3]

                    print("Detected labels:", labels)
                    print("Matched keypoints:", matched_keypoints)
                    print("Ratio:", ratio)
                    print("Boundary:", boundary_points)

                    if TARGET_TAG in labels:
                        print("OBJECT DETECTED:", TARGET_TAG)

                        now = time.time()
                        if now - last_spoken > 5.0:
                            tts.say("I can see the object")
                            last_spoken = now

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("Stopping detector...")

    finally:
        vision.unsubscribe(subscriber_name)
        print("Unsubscribed.")


if __name__ == "__main__":
    main()