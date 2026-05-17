#!/usr/bin/env python3

import qi
import time
from pathlib import Path
from PIL import Image

PEPPER_IP = "192.168.0.150"
PEPPER_PORT = 9559

CAMERA_ID = 0      # 0 = top camera, 1 = bottom camera
RESOLUTION = 2    # 640x480
COLOR_SPACE = 11  # RGB
FPS = 10

SAVE_DIR = Path("/home/wayfarer/p_ws/src/ps/images")


def main():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    name = input("Enter image name without .jpg: ").strip()

    if not name:
        print("No name entered. Cancelled.")
        return

    save_path = SAVE_DIR / f"{name}.jpg"

    print("Connecting to Pepper...")
    session = qi.Session()
    session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")

    video = session.service("ALVideoDevice")

    print("Connected.")
    print("Put the object in front of Pepper.")
    input("Press ENTER to capture image...")

    client_name = video.subscribeCamera(
        "pepper_capture_client",
        CAMERA_ID,
        RESOLUTION,
        COLOR_SPACE,
        FPS
    )

    time.sleep(1.0)

    image = video.getImageRemote(client_name)
    video.unsubscribe(client_name)

    if image is None:
        print("No image received.")
        return

    width = image[0]
    height = image[1]
    image_data = image[6]
    img = Image.frombytes("RGB", (width, height), bytes(image_data))
    img.save(str(save_path))

    print("Image saved as:")
    print(save_path)


if __name__ == "__main__":
    main()