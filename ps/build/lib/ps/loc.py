#!/usr/bin/env python3

import qi
import rclpy
from rclpy.node import Node

from nav_msgs.msg import OccupancyGrid, MapMetaData
from geometry_msgs.msg import Pose, PointStamped, PoseWithCovarianceStamped


PEPPER_IP = "192.168.0.150"
PEPPER_PORT = 9559


class PepperMapRviz(Node):
    def __init__(self):
        super().__init__("pepper_map_rviz")

        self.declare_parameter("explo", "")
        self.exploration_file = self.get_parameter("explo").value

        self.map_pub = self.create_publisher(OccupancyGrid, "/map", 10)
        self.initial_pose_sub = self.create_subscription(PoseWithCovarianceStamped, "/initialpose", self.estimate_callback, 10)

        self.clicked_sub = self.create_subscription(
            PointStamped,
            "/clicked_point",
            self.clicked_point_callback,
            10
        )

        self.get_logger().info("Connecting to Pepper...")
        self.session = qi.Session()

        try:
            self.session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")
        except RuntimeError as e:
            self.get_logger().error(f"Could not connect to Pepper at {PEPPER_IP}:{PEPPER_PORT}")
            self.get_logger().error(str(e))
            return

        self.get_logger().info("Connected to Pepper.")

        self.navigation = self.session.service("ALNavigation")
        self.motion = self.session.service("ALMotion")
        self.tts = self.session.service("ALTextToSpeech")

        self.get_logger().info("Waking Pepper up...")
        self.motion.wakeUp()

        if not self.exploration_file:
            self.get_logger().error("No .explo file given.")
            self.get_logger().error(
                "Run like this: ros2 run ps loc --ros-args -p explo:=/home/nao/.local/share/Explorer/YOUR_FILE.explo"
            )
            return

        self.get_logger().info(f"Loading exploration file: {self.exploration_file}")
        self.navigation.loadExploration(self.exploration_file)

        self.get_logger().info("Relocalizing Pepper in map...")
        self.navigation.relocalizeInMap([-1.1284265518188477, 8.004386901855469])

        self.get_logger().info("Starting localization...")
        self.navigation.startLocalization()

        try:
            position = self.navigation.getRobotPositionInMap()
            self.get_logger().info(f"Pepper current position in map: {position}")
        except Exception as e:
            self.get_logger().warn(f"Could not get Pepper position yet: {e}")

        self.timer = self.create_timer(1.0, self.publish_map)

        self.get_logger().info("Publishing Pepper map to /map")
        self.get_logger().info("Open RViz2, set Fixed Frame to map, then use Publish Point.")

    def estimate_callback(self,msg):
        self.get_logger().info("Relocalizing Pepper in map...")
        self.navigation.relocalizeInMap([msg.pose.position.x, msg.pose.position.y])

        self.get_logger().info("Starting localization...")
        self.navigation.startLocalization()

    def publish_map(self):
        try:
            result_map = self.navigation.getMetricalMap()
        except Exception as e:
            self.get_logger().error(f"Could not get map: {e}")
            return

        resolution = float(result_map[0])
        width = int(result_map[1])
        height = int(result_map[2])
        offset_x = float(result_map[3][0])
        offset_y = float(result_map[3][1])
        raw_data = result_map[4]

        grid = OccupancyGrid()
        grid.header.stamp = self.get_clock().now().to_msg()
        grid.header.frame_id = "map"

        grid.info = MapMetaData()
        grid.info.resolution = resolution
        grid.info.width = width
        grid.info.height = height

        grid.info.origin = Pose()
        grid.info.origin.position.x = offset_x
        grid.info.origin.position.y = offset_y
        grid.info.origin.position.z = 0.0
        grid.info.origin.orientation.w = 1.0

        ros_data = []

        for value in raw_data:
            value = int(value)

            if value < 0:
                ros_data.append(-1)
            else:
                ros_data.append(value)

        grid.data = ros_data
        self.map_pub.publish(grid)

    def clicked_point_callback(self, msg):
        clicked_x = float(msg.point.x)
        clicked_y = float(msg.point.y)

        self.get_logger().info(
            f"RViz clicked point received: x={clicked_x:.2f}, y={clicked_y:.2f}"
        )

        try:
            current_position = self.navigation.getRobotPositionInMap()[0]

            robot_x = float(current_position[0])
            robot_y = float(current_position[1])
            robot_theta = float(current_position[2])

            self.get_logger().info(
                f"Pepper position: x={robot_x:.2f}, y={robot_y:.2f}, theta={robot_theta:.2f}"
            )

            dx = clicked_x - robot_x
            dy = clicked_y - robot_y

            self.get_logger().info(
                f"Target difference: dx={dx:.2f}, dy={dy:.2f}"
            )

            # Convert clicked map direction into a simple angle
            import math
            target_angle = math.atan2(dy, dx)
            angle_error = target_angle - robot_theta

            # Normalize angle to [-pi, pi]
            while angle_error > math.pi:
                angle_error -= 2.0 * math.pi
            while angle_error < -math.pi:
                angle_error += 2.0 * math.pi

            self.get_logger().info(
                f"Angle to target: {target_angle:.2f}, angle error: {angle_error:.2f}"
            )

            # First rotate toward the clicked point
            if abs(angle_error) > 0.2:
                turn_amount = max(min(angle_error, 0.4), -0.4)
                self.get_logger().info(f"Turning by {turn_amount:.2f} rad")
                result = self.navigation.navigateTo(0.0, 0.0, turn_amount)
                self.get_logger().info(f"Turn result: {result}")
                

            # Then move forward a small step
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 0.2:
                step = min(distance, 0.3)
                self.get_logger().info(f"Moving forward by {step:.2f} m")
                result = self.navigation.navigateTo(step, 0.0, 0.0)
                self.get_logger().info(f"Forward result: {result}")
            else:
                self.get_logger().info("Clicked point is already close. Not moving.")

        except Exception as e:
            self.get_logger().error(f"Navigation failed: {e}")

    def destroy_node(self):
        try:
            self.get_logger().info("Stopping localization...")
            self.navigation.stopLocalization()
        except Exception:
            pass

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = PepperMapRviz()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()