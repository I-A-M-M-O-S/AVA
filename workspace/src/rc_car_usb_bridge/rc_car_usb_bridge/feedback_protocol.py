"""Pure incremental decoder for the versioned ESP feedback protocol."""

from dataclasses import dataclass
from typing import Optional, Union


PROTOCOL_VERSION = 1
MAX_FRAME_LENGTH = 128
UINT32_MAX = (1 << 32) - 1
INT32_MIN = -(1 << 31)
INT32_MAX = (1 << 31) - 1
KNOWN_FAULT_MASK = (1 << 11) - 1
MAX_ACK_ADVANCE = 1_000_000


@dataclass(frozen=True)
class VehicleFeedback:
    """Validated V1 STA payload."""

    protocol_version: int
    accepted_sequence: int
    control_owner: int
    jetson_locked: bool
    armed: bool
    enabled: bool
    fault_flags: int


@dataclass(frozen=True)
class ActuatorFeedback:
    """Validated V1 ACT payload."""

    protocol_version: int
    applied_sequence: int
    speed: int
    steering: int
    enabled: bool


@dataclass(frozen=True)
class EncoderFeedback:
    """Validated V1 ENC payload."""

    protocol_version: int
    sample_counter: int
    front_left_ticks: int
    front_right_ticks: int
    rear_left_ticks: int
    rear_right_ticks: int


Feedback = Union[VehicleFeedback, ActuatorFeedback, EncoderFeedback]


@dataclass(frozen=True)
class DecodedFrame:
    """One validated feedback object and its diagnostic raw line."""

    feedback: Feedback
    raw_line: bytes


@dataclass(frozen=True)
class RejectedFrame:
    """One atomically rejected line or stream fragment."""

    reason: str
    detail: str = ''
    raw_line: bytes = b''


DecodeEvent = Union[DecodedFrame, RejectedFrame]


def crc16_ccitt(data: bytes) -> int:
    """Return CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def _unsigned(text: str, maximum: int, field: str) -> int:
    if not text or not text.isascii() or not text.isdecimal():
        raise ValueError(f'invalid_integer:{field}')
    if len(text) > 1 and text[0] == '0':
        raise ValueError(f'invalid_integer:{field}')
    value = int(text)
    if value > maximum:
        raise ValueError(f'range:{field}')
    return value


def _signed(text: str, minimum: int, maximum: int, field: str) -> int:
    negative = text.startswith('-')
    digits = text[1:] if negative else text
    if (
        not digits or not digits.isascii() or not digits.isdecimal()
        or text.startswith('+') or (len(digits) > 1 and digits[0] == '0')
        or (negative and digits == '0')
    ):
        raise ValueError(f'invalid_integer:{field}')
    value = int(text)
    if not minimum <= value <= maximum:
        raise ValueError(f'range:{field}')
    return value


def _boolean(text: str, field: str) -> bool:
    if text not in ('0', '1'):
        raise ValueError(f'invalid_boolean:{field}')
    return text == '1'


class FeedbackDecoder:
    """Incrementally frame and strictly validate ESP feedback bytes."""

    def __init__(
        self,
        max_frame_length: int = MAX_FRAME_LENGTH,
        max_ack_advance: int = MAX_ACK_ADVANCE,
    ):
        """Initialize bounded framing and ACK validation state."""
        if max_frame_length < 1 or max_ack_advance < 1:
            raise ValueError('decoder limits must be positive')
        self.max_frame_length = max_frame_length
        self.max_ack_advance = max_ack_advance
        self._buffer = bytearray()
        self._discarding_overlong = False
        self._last_ack: Optional[int] = None

    @property
    def buffered_bytes(self) -> int:
        """Return retained partial-frame bytes (always bounded)."""
        return len(self._buffer)

    def reset(self) -> Optional[RejectedFrame]:
        """Reset stream and ACK state at disconnect/reconnect."""
        rejected = None
        if self._buffer or self._discarding_overlong:
            rejected = RejectedFrame(
                'truncated_frame', 'stream reset before LF',
                bytes(self._buffer),
            )
        self._buffer.clear()
        self._discarding_overlong = False
        self._last_ack = None
        return rejected

    def feed(self, data: bytes) -> list[DecodeEvent]:
        """Consume arbitrary bytes and return complete validation events."""
        if not isinstance(data, bytes):
            raise TypeError('data must be bytes')
        events: list[DecodeEvent] = []
        for byte in data:
            if self._discarding_overlong:
                if byte == 0x0A:
                    self._discarding_overlong = False
                continue
            if byte == 0x0A:
                line = bytes(self._buffer)
                self._buffer.clear()
                if line.endswith(b'\r'):
                    line = line[:-1]
                if line:
                    events.append(self._decode_line(line))
                continue
            self._buffer.append(byte)
            if len(self._buffer) > self.max_frame_length:
                raw = bytes(self._buffer[:self.max_frame_length])
                self._buffer.clear()
                self._discarding_overlong = True
                events.append(RejectedFrame(
                    'overlong_frame',
                    f'line exceeds {self.max_frame_length} bytes', raw,
                ))
        return events

    def _decode_line(self, line: bytes) -> DecodeEvent:
        if any(byte < 0x20 or byte > 0x7E for byte in line):
            return RejectedFrame('non_ascii', 'non-printable ASCII byte', line)
        try:
            text = line.decode('ascii')
            if text.count('*') != 1:
                raise ValueError('missing_or_multiple_crc')
            payload, checksum = text.split('*')
            if len(checksum) != 4 or any(
                char not in '0123456789ABCDEF' for char in checksum
            ):
                raise ValueError('invalid_crc_format')
            expected = crc16_ccitt(payload.encode('ascii'))
            if int(checksum, 16) != expected:
                raise ValueError('crc_error')
            fields = payload.split(',')
            if any(field == '' for field in fields):
                raise ValueError('empty_field')
            if not fields[0].startswith('V'):
                raise ValueError('format:version')
            version = _unsigned(fields[0][1:], 255, 'version')
            if version != PROTOCOL_VERSION:
                raise ValueError('unknown_version')
            if len(fields) < 2:
                raise ValueError('field_count')
            frame_type = fields[1]
            if frame_type == 'STA':
                feedback = self._decode_status(fields, version)
            elif frame_type == 'ACT':
                feedback = self._decode_actuator(fields, version)
            elif frame_type == 'ENC':
                feedback = self._decode_encoder(fields, version)
            else:
                raise ValueError('unknown_frame_type')
            return DecodedFrame(feedback, line)
        except ValueError as error:
            detail = str(error)
            reason = detail.split(':', 1)[0]
            return RejectedFrame(reason, detail, line)

    def _decode_status(self, fields: list[str], version: int) -> Feedback:
        if len(fields) != 8:
            raise ValueError('field_count:STA')
        sequence = _unsigned(fields[2], UINT32_MAX, 'accepted_sequence')
        owner = _unsigned(fields[3], 2, 'control_owner')
        locked = _boolean(fields[4], 'jetson_locked')
        armed = _boolean(fields[5], 'armed')
        enabled = _boolean(fields[6], 'enabled')
        faults = _unsigned(fields[7], UINT32_MAX, 'fault_flags')
        if faults & ~KNOWN_FAULT_MASK:
            raise ValueError('unknown_fault_bits')
        if enabled and (not armed or owner == 0):
            raise ValueError('invalid_status:enabled')
        if owner == 1 and not locked:
            raise ValueError('invalid_status:manual_without_lock')
        if owner == 2 and locked:
            raise ValueError('invalid_status:jetson_locked')
        self._validate_ack(sequence)
        return VehicleFeedback(
            version, sequence, owner, locked, armed, enabled, faults
        )

    def _decode_actuator(self, fields: list[str], version: int) -> Feedback:
        if len(fields) != 6:
            raise ValueError('field_count:ACT')
        return ActuatorFeedback(
            version,
            _unsigned(fields[2], UINT32_MAX, 'applied_sequence'),
            _signed(fields[3], -100, 100, 'speed'),
            _signed(fields[4], -100, 100, 'steering'),
            _boolean(fields[5], 'enabled'),
        )

    def _decode_encoder(self, fields: list[str], version: int) -> Feedback:
        if len(fields) != 7:
            raise ValueError('field_count:ENC')
        return EncoderFeedback(
            version,
            _unsigned(fields[2], UINT32_MAX, 'sample_counter'),
            _signed(fields[3], INT32_MIN, INT32_MAX, 'front_left_ticks'),
            _signed(fields[4], INT32_MIN, INT32_MAX, 'front_right_ticks'),
            _signed(fields[5], INT32_MIN, INT32_MAX, 'rear_left_ticks'),
            _signed(fields[6], INT32_MIN, INT32_MAX, 'rear_right_ticks'),
        )

    def _validate_ack(self, sequence: int) -> None:
        if self._last_ack is None:
            self._last_ack = sequence
            return
        delta = (sequence - self._last_ack) & UINT32_MAX
        if delta == 0:
            raise ValueError('ack_duplicate')
        if delta >= (1 << 31):
            raise ValueError('ack_regression')
        if delta > self.max_ack_advance:
            raise ValueError('ack_implausible')
        self._last_ack = sequence
