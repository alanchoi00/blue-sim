#!/usr/bin/env python3
from typing import Optional

import rclpy
from geometry_msgs.msg import Twist
from mavros_msgs.msg import OverrideRCIn
from rclpy.node import Node
from rclpy.qos import QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy

RC_CENTER = 1500
RC_RANGE = 400
RC_IGNORE = 65535
PUBLISH_RATE = 10.0  # Hz to keeps RC link alive to prevent ArduSub failsafe


class ArduSubBridge(Node):
    """Convert cmd_vel Twist messages to MAVROS RC override for ArduSub."""

    def __init__(self) -> None:
        super().__init__("ardusub_bridge")

        self.declare_parameter("max_linear", 1.0)
        self.declare_parameter("max_angular", 1.0)

        self.max_linear = float(self.get_parameter("max_linear").value)
        self.max_angular = float(self.get_parameter("max_angular").value)

        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self._last_cmd: Optional[Twist] = None
        self.sub = self.create_subscription(Twist, "cmd_vel", self._on_cmd_vel, qos)
        self.pub = self.create_publisher(OverrideRCIn, "/mavros/rc/override", 10)
        self.create_timer(1.0 / PUBLISH_RATE, self._publish)

    def _on_cmd_vel(self, msg: Twist) -> None:
        self._last_cmd = msg

    def _to_pwm(self, value: float, max_value: float) -> int:
        normalized = max(-1.0, min(1.0, value / max_value))
        return int(RC_CENTER + RC_RANGE * normalized)

    def _publish(self) -> None:
        rc = OverrideRCIn()
        rc.channels = [RC_IGNORE] * 18

        # ArduSub channel mapping:
        # 0=pitch, 1=roll, 2=throttle, 3=yaw, 4=forward, 5=lateral
        if self._last_cmd is not None:
            rc.channels[4] = self._to_pwm(self._last_cmd.linear.x, self.max_linear)
            rc.channels[5] = self._to_pwm(-self._last_cmd.linear.y, self.max_linear)
            rc.channels[2] = self._to_pwm(self._last_cmd.linear.z, self.max_linear)
            rc.channels[3] = self._to_pwm(-self._last_cmd.angular.z, self.max_angular)
        else:
            rc.channels[4] = RC_CENTER
            rc.channels[5] = RC_CENTER
            rc.channels[2] = RC_CENTER
            rc.channels[3] = RC_CENTER

        self.pub.publish(rc)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ArduSubBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
