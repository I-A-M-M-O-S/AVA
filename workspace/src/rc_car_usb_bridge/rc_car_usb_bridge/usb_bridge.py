#!/usr/bin/env python3

"""Transport commands and publish only validated typed ESP feedback."""

import errno
import glob
import json
import os
import select
import termios
import time
import tty

from rc_car_interfaces.msg import (
    ActuatorStatus,
    DriveCommand,
    VehicleStatus,
    WheelEncoderState,
)

from rc_car_usb_bridge.feedback_protocol import (
    ActuatorFeedback,
    DecodedFrame,
    EncoderFeedback,
    FeedbackDecoder,
    RejectedFrame,
    VehicleFeedback,
    crc16_ccitt,
)

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

from std_msgs.msg import String


STATUS_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


def encode_command(sequence, speed, steering, enabled):
    """Encode one human-readable, checksummed command line."""
    payload = (
        f'CMD,{sequence},{speed},{steering},{1 if enabled else 0}'
    )
    checksum = crc16_ccitt(payload.encode('ascii'))
    return f'{payload}*{checksum:04X}\n'


class UsbBridge(Node):
    """Subscribe to DriveCommand and forward safe commands to an ESP32."""

    def __init__(self):
        """Configure the ROS subscription and optional serial output."""
        super().__init__('rc_car_usb_bridge')
        self.declare_parameter('drive_topic', '/drive_commands')
        self.declare_parameter('device', '')
        self.declare_parameter('physical_port', '')
        self.declare_parameter('device_search_roots', ['/host/dev', '/dev'])
        self.declare_parameter('sysfs_roots', ['/host/sys', '/sys'])
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('dry_run', True)
        self.declare_parameter('expect_response', False)
        # TODO(SAFETY-MANDATORY): Enable response handling, message watchdogs,
        # and ESP acknowledgements before motor hardware is connected. The
        # one-way settings exist only for the requested PuTTY output test.
        self.declare_parameter('message_watchdog_enabled', True)
        self.declare_parameter('validate_timestamp', True)
        self.declare_parameter('validate_sequence', True)
        self.declare_parameter('command_timeout', 0.3)
        self.declare_parameter('max_message_age', 0.5)
        self.declare_parameter('allow_zero_stamp', False)

        self._device = str(self.get_parameter('device').value)
        self._physical_port = str(
            self.get_parameter('physical_port').value
        ).strip()
        self._device_search_roots = list(
            self.get_parameter('device_search_roots').value
        )
        self._sysfs_roots = list(self.get_parameter('sysfs_roots').value)
        self._baud_rate = int(self.get_parameter('baud_rate').value)
        self._dry_run = bool(self.get_parameter('dry_run').value)
        self._expect_response = bool(
            self.get_parameter('expect_response').value
        )
        self._message_watchdog_enabled = bool(
            self.get_parameter('message_watchdog_enabled').value
        )
        self._validate_timestamp = bool(
            self.get_parameter('validate_timestamp').value
        )
        self._validate_sequence = bool(
            self.get_parameter('validate_sequence').value
        )
        self._command_timeout = float(
            self.get_parameter('command_timeout').value
        )
        self._max_message_age = float(
            self.get_parameter('max_message_age').value
        )
        self._allow_zero_stamp = bool(
            self.get_parameter('allow_zero_stamp').value
        )

        self._fd = None
        self._connected_device = ''
        self._decoder = FeedbackDecoder()
        self._last_sequence = None
        self._last_command_time = None
        self._timeout_stop_sent = True
        self._last_status_data = None

        self._tx_publisher = self.create_publisher(
            String, '/drive_usb/tx', 10
        )
        self._rx_publisher = self.create_publisher(
            String, '/drive_usb/rx', 10
        )
        # Diagnostic mirror only: replacement characters and rejected lines
        # are expected here. Safety code must use validated typed topics.
        self._status_publisher = self.create_publisher(
            String, '/drive_usb/status', STATUS_QOS
        )
        self._vehicle_status_publisher = self.create_publisher(
            VehicleStatus, '/vehicle/status', 10
        )
        self._actuator_status_publisher = self.create_publisher(
            ActuatorStatus, '/vehicle/actuator_status', 10
        )
        self._encoder_publisher = self.create_publisher(
            WheelEncoderState, '/vehicle/encoders', 10
        )
        self.create_subscription(
            DriveCommand,
            str(self.get_parameter('drive_topic').value),
            self._on_command,
            10,
        )
        self.create_timer(0.05, self._check_timeout)
        if self._expect_response:
            self.create_timer(0.02, self._read_serial)
        self.create_timer(1.0, self._ensure_serial_open)

        if self._dry_run:
            self._publish_status('ready', detail='dry_run')
            self.get_logger().info(
                'USB bridge ready in dry-run mode; no device will be written'
            )
        else:
            if not self._expect_response:
                self.get_logger().warn(
                    'One-way USB test mode: no response is expected'
                )
            if not self._message_watchdog_enabled:
                self.get_logger().warn(
                    'USB message watchdog is disabled for this test'
                )
            self._ensure_serial_open()

    def _publish_status(self, state, **details):
        message = String()
        message.data = json.dumps(
            {'state': state, **details}, separators=(',', ':')
        )
        if message.data == self._last_status_data:
            return
        self._status_publisher.publish(message)
        self._last_status_data = message.data

    def _ensure_serial_open(self):
        if self._dry_run:
            return
        if self._fd is not None:
            self._publish_status(
                'connected', device=self._connected_device,
                baud=self._baud_rate,
                expect_response=self._expect_response,
            )
            return
        selected_device = self._device or self._discover_device()
        if not selected_device:
            self._publish_status(
                'waiting_for_device', physical_port=self._physical_port
            )
            return
        try:
            access_mode = os.O_RDWR if self._expect_response else os.O_WRONLY
            fd = os.open(
                selected_device,
                access_mode | os.O_NOCTTY | os.O_NONBLOCK,
            )
            tty.setraw(fd, when=termios.TCSANOW)
            attributes = termios.tcgetattr(fd)
            baud_constant = self._baud_constant(self._baud_rate)
            attributes[4] = baud_constant
            attributes[5] = baud_constant
            termios.tcsetattr(fd, termios.TCSANOW, attributes)
            termios.tcflush(fd, termios.TCIOFLUSH)
            self._fd = fd
            self._connected_device = selected_device
            reset_event = self._decoder.reset()
            if reset_event is not None:
                self._handle_decode_event(reset_event)
            self._publish_status(
                'connected', device=selected_device, baud=self._baud_rate,
                expect_response=self._expect_response
            )
            self.get_logger().info(
                f'Connected serial output on {selected_device} at '
                f'{self._baud_rate} baud'
            )
        except OSError as error:
            self._publish_status(
                'disconnected', device=selected_device, error=str(error)
            )

    def _discover_device(self):
        candidates = []
        for root in self._device_search_roots:
            for pattern in ('ttyACM*', 'ttyUSB*'):
                candidates.extend(glob.glob(os.path.join(root, pattern)))

        candidates = sorted(set(candidates))
        if self._physical_port:
            candidates = [
                candidate for candidate in candidates
                if self._candidate_matches_port(candidate)
            ]

        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            self._publish_status(
                'ambiguous_devices',
                physical_port=self._physical_port,
                candidates=candidates,
            )
        return ''

    def _candidate_matches_port(self, candidate):
        tty_name = os.path.basename(os.path.realpath(candidate))
        for root in self._sysfs_roots:
            device_path = os.path.join(
                root, 'class', 'tty', tty_name, 'device'
            )
            if os.path.exists(device_path):
                topology = os.path.realpath(device_path)
                if self._physical_port in topology:
                    return True
        return False

    @staticmethod
    def _baud_constant(baud_rate):
        supported = {
            9600: termios.B9600,
            19200: termios.B19200,
            38400: termios.B38400,
            57600: termios.B57600,
            115200: termios.B115200,
            230400: termios.B230400,
        }
        if baud_rate not in supported:
            raise OSError(
                errno.EINVAL,
                f'unsupported baud rate {baud_rate}',
            )
        return supported[baud_rate]

    def _on_command(self, command):
        speed = int(command.speed)
        steering = int(command.steering)
        sequence = int(command.sequence)

        if not -100 <= speed <= 100 or not -100 <= steering <= 100:
            self._reject(
                'range', sequence, speed=speed, steering=steering
            )
            return

        stamp_ns = (
            int(command.header.stamp.sec) * 1_000_000_000
            + int(command.header.stamp.nanosec)
        )
        if (
            self._validate_timestamp
            and not stamp_ns
            and not self._allow_zero_stamp
        ):
            self._reject('missing_timestamp', sequence)
            return
        if self._validate_timestamp and stamp_ns:
            age = (self.get_clock().now().nanoseconds - stamp_ns) / 1e9
            if age < -0.2 or age > self._max_message_age:
                self._reject('stale', sequence, age_s=round(age, 3))
                return

        now = time.monotonic()
        if self._validate_sequence and self._last_sequence is not None:
            delta = (sequence - self._last_sequence) & 0xFFFFFFFF
            sequence_is_new = 0 < delta < 0x80000000
            publisher_was_quiet = (
                self._last_command_time is None
                or now - self._last_command_time > self._command_timeout
            )
            if not sequence_is_new and not publisher_was_quiet:
                self._reject(
                    'sequence', sequence, previous=self._last_sequence
                )
                return
            if not sequence_is_new:
                self._publish_status(
                    'sequence_reset',
                    sequence=sequence,
                    previous=self._last_sequence,
                )

        self._last_sequence = sequence
        self._last_command_time = now
        self._timeout_stop_sent = False
        self._send_frame(
            encode_command(sequence, speed, steering, command.enabled)
        )

    def _reject(self, reason, sequence, **details):
        self._publish_status(
            'rejected', reason=reason, sequence=sequence, **details
        )
        self.get_logger().warn(
            f'Rejected drive command {sequence}: {reason}'
        )

    def _send_frame(self, frame):
        tx_message = String()
        tx_message.data = frame.rstrip('\n')
        self._tx_publisher.publish(tx_message)

        if self._dry_run:
            return True
        if self._fd is None:
            self._publish_status('dropped', reason='serial disconnected')
            return False
        try:
            data = frame.encode('ascii')
            offset = 0
            while offset < len(data):
                _, writable, _ = select.select([], [self._fd], [], 0.1)
                if not writable:
                    raise OSError(errno.ETIMEDOUT, 'serial write timed out')
                offset += os.write(self._fd, data[offset:])
            return True
        except OSError as error:
            self._serial_failed(error)
            return False

    def _read_serial(self):
        if self._dry_run or not self._expect_response or self._fd is None:
            return
        try:
            while True:
                chunk = os.read(self._fd, 512)
                if not chunk:
                    break
                for event in self._decoder.feed(chunk):
                    self._handle_decode_event(event)
        except BlockingIOError:
            pass
        except OSError as error:
            self._serial_failed(error)

    def _handle_decode_event(self, event):
        raw_message = String()
        raw_message.data = event.raw_line.decode('ascii', errors='replace')
        self._rx_publisher.publish(raw_message)

        if isinstance(event, RejectedFrame):
            self._publish_status(
                'feedback_rejected', reason=event.reason,
                detail=event.detail,
            )
            self.get_logger().warn(
                f'Rejected ESP feedback: {event.reason} ({event.detail})'
            )
            return

        if not isinstance(event, DecodedFrame):
            raise TypeError('unexpected decoder event')
        feedback = event.feedback
        stamp = self.get_clock().now().to_msg()
        if isinstance(feedback, VehicleFeedback):
            message = VehicleStatus()
            message.header.stamp = stamp
            message.protocol_version = feedback.protocol_version
            message.last_accepted_sequence = feedback.accepted_sequence
            message.control_owner = feedback.control_owner
            message.jetson_locked = feedback.jetson_locked
            message.armed = feedback.armed
            message.enabled = feedback.enabled
            message.fault_flags = feedback.fault_flags
            self._vehicle_status_publisher.publish(message)
            frame_type = 'STA'
        elif isinstance(feedback, ActuatorFeedback):
            message = ActuatorStatus()
            message.header.stamp = stamp
            message.protocol_version = feedback.protocol_version
            message.applied_sequence = feedback.applied_sequence
            message.speed = feedback.speed
            message.steering = feedback.steering
            message.enabled = feedback.enabled
            self._actuator_status_publisher.publish(message)
            frame_type = 'ACT'
        elif isinstance(feedback, EncoderFeedback):
            message = WheelEncoderState()
            message.header.stamp = stamp
            message.protocol_version = feedback.protocol_version
            message.sample_counter = feedback.sample_counter
            message.front_left_ticks = feedback.front_left_ticks
            message.front_right_ticks = feedback.front_right_ticks
            message.rear_left_ticks = feedback.rear_left_ticks
            message.rear_right_ticks = feedback.rear_right_ticks
            self._encoder_publisher.publish(message)
            frame_type = 'ENC'
        else:
            raise TypeError('unexpected feedback type')
        self._publish_status('valid_feedback', frame_type=frame_type)

    def _serial_failed(self, error):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        reset_event = self._decoder.reset()
        if reset_event is not None:
            self._handle_decode_event(reset_event)
        self._publish_status(
            'disconnected', device=self._connected_device, error=str(error)
        )
        self.get_logger().error(f'ESP32 serial connection failed: {error}')
        self._connected_device = ''

    def _check_timeout(self):
        if not self._message_watchdog_enabled:
            return
        if self._last_command_time is None or self._timeout_stop_sent:
            return
        if time.monotonic() - self._last_command_time <= self._command_timeout:
            return
        sequence = (
            self._last_sequence if self._last_sequence is not None else 0
        )
        self._send_frame(encode_command(sequence, 0, 0, False))
        self._timeout_stop_sent = True
        self._publish_status(
            'command_timeout', sequence=sequence, action='disabled_stop'
        )
        self.get_logger().warn('Drive command timed out; disabled stop sent')

    def send_shutdown_stop(self):
        """Send a final disabled command when production watchdogs are on."""
        if not self._message_watchdog_enabled:
            return
        sequence = (
            self._last_sequence if self._last_sequence is not None else 0
        )
        self._send_frame(encode_command(sequence, 0, 0, False))

    def close_serial(self):
        """Close the selected serial device."""
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        reset_event = self._decoder.reset()
        if reset_event is not None:
            self._handle_decode_event(reset_event)
        self._connected_device = ''


def main(args=None):
    """Run the USB bridge node."""
    rclpy.init(args=args)
    node = UsbBridge()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.send_shutdown_stop()
        node.close_serial()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
