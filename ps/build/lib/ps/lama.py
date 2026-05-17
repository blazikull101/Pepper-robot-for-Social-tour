#!/usr/bin/env python3

import json
import urllib.request
import qi

PEPPER_IP = "192.168.0.150"
PEPPER_PORT = 9559

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:1b"


def ask_bot(text):
    data = {
        "model": MODEL,
        "prompt": (
            "You are Pepper, a friendly robot tour guide. "
            "Keep replies short, simple, and natural. "
            "Do not ask too many follow-up questions. "
            "Do not pretend you can move unless the operator gives a command.\n\n"
            "Human: " + text + "\n"
            "Pepper:"
        ),
        "stream": False
    }

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["response"].strip()


def main():
    print("Connecting to Pepper...")

    session = qi.Session()
    session.connect("tcp://{}:{}".format(PEPPER_IP, PEPPER_PORT))

    tts = session.service("ALTextToSpeech")
    motion = session.service("ALMotion")

    motion.wakeUp()
    tts.setLanguage("English")
    tts.setVolume(0.8)

    print("Connected to Pepper.")
    print("Type text. Pepper will speak the chatbot reply.")
    print("Type quit to stop.")

    while True:
        user_text = input("You: ").strip()

        if user_text.lower() in ["quit", "exit", "stop"]:
            break

        if not user_text:
            continue

        reply = ask_bot(user_text)

        print("Pepper:", reply)
        tts.say(reply)


if __name__ == "__main__":
    main()