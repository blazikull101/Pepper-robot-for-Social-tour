#!/usr/bin/env python3

import time
import qi


PEPPER_IP = "192.168.0.150"
PEPPER_PORT = 9559


def main():
    session = qi.Session()
    session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")

    motion = session.service("ALMotion")
    tracker = session.service("ALTracker")

    motion.wakeUp()

    tracker.stopTracker()
    tracker.unregisterAllTargets()

    tracker.registerTarget("Face", 0.1)
    tracker.setMode("Head")
    tracker.track("Face")

    print("Pepper native face tracking started. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping tracker...")
        tracker.stopTracker()
        tracker.unregisterAllTargets()
        motion.moveToward(0.0, 0.0, 0.0)


if __name__ == "__main__":
    main()