#!/usr/bin/env python3
"""Arm the vehicle and set flight mode on startup via MAVROS."""

import rclpy
from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool, SetMode
from rclpy.node import Node

# https://github.com/ArduPilot/ardupilot/blob/master/ArduSub/mode.h
VALID_MODES = frozenset(
    {
        "MANUAL",
        "STABILIZE",
        "ACRO",
        "ALT_HOLD",
        "AUTO",
        "GUIDED",
        "VELHOLD",
        "POSHOLD",
        "CIRCLE",
        "SURFACE",
    }
)

ARM_RETRY_DELAY = 2.0

# https://mavlink.io/en/messages/common.html#MAV_STATE
MAV_STATE_STANDBY = 3


class ArduSubInit(Node):
    def __init__(self) -> None:
        super().__init__("ardusub_init")

        self.declare_parameter("arm", True)
        self.declare_parameter("flight_mode", "ALT_HOLD")

        self._arm = bool(self.get_parameter("arm").value)
        self._mode = str(self.get_parameter("flight_mode").value)

        if self._mode not in VALID_MODES:
            raise ValueError(
                f"Invalid flight mode: {self._mode!r}. "
                f"Valid modes: {sorted(VALID_MODES)}"
            )

        self._connected = False
        self._system_status = 0
        self._current_mode = ""
        self._arming_client = self.create_client(CommandBool, "/mavros/cmd/arming")
        self._mode_client = self.create_client(SetMode, "/mavros/set_mode")
        self._state_sub = self.create_subscription(
            State, "/mavros/state", self._on_state, 10
        )
        self._timer = self.create_timer(1.0, self._wait_and_init)

    def _on_state(self, msg: State) -> None:
        self._connected = msg.connected
        self._system_status = msg.system_status
        self._current_mode = msg.mode

    def _wait_and_init(self) -> None:
        if not self._arming_client.service_is_ready():
            self.get_logger().info("Waiting for /mavros/cmd/arming ...", once=True)
            return
        if not self._mode_client.service_is_ready():
            self.get_logger().info("Waiting for /mavros/set_mode ...", once=True)
            return
        if not self._connected:
            self.get_logger().info("Waiting for FCU connection ...", once=True)
            return
        if self._system_status < MAV_STATE_STANDBY:
            self.get_logger().info("Waiting for FCU to be ready ...", once=True)
            return

        self._timer.cancel()

        if self._arm:
            self._do_arm()
        else:
            self._set_mode()

    def _do_arm(self) -> None:
        req = CommandBool.Request()
        req.value = True
        self._arming_client.call_async(req).add_done_callback(self._on_arm)

    def _on_arm(self, future) -> None:
        result = future.result()
        if result and result.success:
            self.get_logger().info("Armed successfully")
            self._set_mode()
        else:
            self.get_logger().warning(
                f"Arming failed, retrying in {ARM_RETRY_DELAY}s ..."
            )
            self._retry_timer = self.create_timer(ARM_RETRY_DELAY, self._on_retry_arm)

    def _on_retry_arm(self) -> None:
        self._retry_timer.cancel()
        self._do_arm()

    def _set_mode(self) -> None:
        req = SetMode.Request()
        req.custom_mode = self._mode
        self._mode_client.call_async(req).add_done_callback(self._on_set_mode)

    def _on_set_mode(self, future) -> None:
        result = future.result()
        if result and result.mode_sent:
            self._mode_verify_timer = self.create_timer(1.0, self._verify_mode)
        else:
            self.get_logger().warning(
                f"Failed to request flight mode {self._mode}, retrying ..."
            )
            self._retry_mode_timer = self.create_timer(
                ARM_RETRY_DELAY, self._on_retry_mode
            )

    def _verify_mode(self) -> None:
        self._mode_verify_timer.cancel()
        if self._current_mode == self._mode:
            self.get_logger().info(f"Flight mode set to {self._mode}")
        else:
            self.get_logger().warning(
                f"Flight mode not applied "
                f"(current: {self._current_mode!r}), retrying ..."
            )
            self._set_mode()

    def _on_retry_mode(self) -> None:
        self._retry_mode_timer.cancel()
        self._set_mode()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ArduSubInit()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
