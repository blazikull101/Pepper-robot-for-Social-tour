#!/usr/bin/env python3

import qi
import pprint

PEPPER_IP = "192.168.0.150"
PEPPER_PORT = 9559

FRONT_IMG = "/home/nao/artifacts/d_front_small.jpg"
SIDE_IMG = "/home/nao/artifacts/d_side_small.jpg"
OTHERSIDE_IMG = "/home/nao/artifacts/d_other_small.jpg"

OBJECT_NAME = "pendulum"
OBJECT_TAGS = ["artifact", "box"]


def main():
    print("Connecting to Pepper...")

    session = qi.Session()
    session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")

    vision = session.service("ALVisionRecognition")
    tts = session.service("ALTextToSpeech")

    print("Connected.")
    print("Database directory:", vision.getDefaultDatabaseDirectory())
    print("Database name:", vision.getDefaultDatabaseName())

    print("Clearing old vision database...")
    vision.clearCurrentDatabase()

    vision.setMaxOutObjs(5)

    print("Database size after clear:", vision.getSize())

    print("Training front...")
    ok1 = vision.learnFromFile(
        FRONT_IMG,
        OBJECT_NAME + "_front",
        OBJECT_TAGS,
        True,
        True
    )
    print("Front learned:", ok1)

    print("Training side...")
    ok2 = vision.learnFromFile(
        SIDE_IMG,
        OBJECT_NAME + "_side",
        OBJECT_TAGS,
        True,
        True
    )
    print("Side learned:", ok2)

    print("Training other side...")
    ok3 = vision.learnFromFile(
        OTHERSIDE_IMG,
        OBJECT_NAME + "_other",
        OBJECT_TAGS,
        True,
        True
    )
    print("Other side learned:", ok3)

    print("Database size after training:", vision.getSize())
    print("Max output objects:", vision.getMaxOutObjs())

    print("Testing front image...")
    result_front = vision.detectFromFile(FRONT_IMG)
    pprint.pprint(result_front)

    print("Testing side image...")
    result_side = vision.detectFromFile(SIDE_IMG)
    pprint.pprint(result_side)

    print("Testing other side image...")
    result_otherside = vision.detectFromFile(OTHERSIDE_IMG)
    pprint.pprint(result_otherside)

    if ok1 and ok2 and ok3:
        tts.say("I learned the object")
    else:
        tts.say("I could not learn one of the object images")


if __name__ == "__main__":
    main()