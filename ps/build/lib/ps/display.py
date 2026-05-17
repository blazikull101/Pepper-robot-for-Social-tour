import os
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import qi


PEPPER_IP = "192.168.0.150"
PEPPER_PORT = 9559

LAPTOP_IP = "192.168.0.185"
WEB_PORT = 8080

PAGE_FOLDER = "/tmp/pepper_tablet_page"
PAGE_FILE = "walking_robot.html"


SPEECH_TEXT = """
hello""".strip()


HTML_TEXT = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Pepper Tablet</title>
    <style>
        body {{
            background-color: #ffffff;
            margin: 0;
            padding: 35px;
            font-family: Arial, Helvetica, sans-serif;
            color: #1a1a1a;
            line-height: 1.5;
        }}

        .container {{
            max-width: 900px;
            width: 100%;
            margin: auto;
        }}

        h1 {{
            font-size: 34px;
            margin-bottom: 25px;
            border-bottom: 4px solid #2c3e50;
            padding-bottom: 10px;
        }}

        p {{
            font-size: 22px;
            margin-bottom: 20px;
            text-align: left;
        }}
    </style>
</head>

<body>
    <div class="container">
        <h1>Hello</h1>

    </div>
</body>
</html>
"""


class PepperSayAndDisplay(Node):
    def __init__(self):
        super().__init__("pepper_say_and_display")

        self.pub = self.create_publisher(String, "/pepper_say", 10)
        self.sent = False

        self.make_html_page()
        self.start_web_server()
        self.show_on_tablet()

        self.timer = self.create_timer(1.0, self.say_once)

    def make_html_page(self):
        os.makedirs(PAGE_FOLDER, exist_ok=True)

        html_path = os.path.join(PAGE_FOLDER, PAGE_FILE)

        with open(html_path, "w") as f:
            f.write(HTML_TEXT)

        self.get_logger().info(f"Created tablet page: {html_path}")

    def start_web_server(self):
        os.chdir(PAGE_FOLDER)

        handler = SimpleHTTPRequestHandler
        self.server = ThreadingHTTPServer(("0.0.0.0", WEB_PORT), handler)

        thread = threading.Thread(target=self.server.serve_forever)
        thread.daemon = True
        thread.start()

        self.get_logger().info(f"Web server running at http://{LAPTOP_IP}:{WEB_PORT}/{PAGE_FILE}")

    def show_on_tablet(self):
        page_url = f"http://{LAPTOP_IP}:{WEB_PORT}/{PAGE_FILE}"

        try:
            session = qi.Session()
            session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")

            tablet = session.service("ALTabletService")
            tablet.showWebview(page_url)

            self.get_logger().info(f"Showing tablet page: {page_url}")

        except Exception as e:
            self.get_logger().error(f"Could not show tablet page: {e}")

    def say_once(self):
        if self.sent:
            return

        msg = String()
        msg.data = SPEECH_TEXT

        self.pub.publish(msg)
        self.get_logger().info("Sent speech message to Pepper")

        self.sent = True

        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = PepperSayAndDisplay()
    rclpy.spin(node)


if __name__ == "__main__":
    main()