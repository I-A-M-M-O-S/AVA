"""Strict, ROS-independent ESP feedback decoder tests."""

import pytest

from rc_car_usb_bridge.feedback_protocol import (
    ActuatorFeedback,
    DecodedFrame,
    EncoderFeedback,
    FeedbackDecoder,
    INT32_MAX,
    INT32_MIN,
    RejectedFrame,
    VehicleFeedback,
    crc16_ccitt,
)


def frame(payload, ending=b'\n'):
    """Build one protocol-contract frame for a test payload."""
    encoded = payload.encode('ascii')
    return encoded + f'*{crc16_ccitt(encoded):04X}'.encode() + ending


def decoded(decoder, data):
    """Return the single expected valid payload."""
    events = decoder.feed(data)
    assert len(events) == 1
    assert isinstance(events[0], DecodedFrame)
    return events[0].feedback


def rejected(decoder, data, reason):
    """Assert one rejection with the expected stable reason."""
    events = decoder.feed(data)
    assert len(events) == 1
    assert isinstance(events[0], RejectedFrame)
    assert events[0].reason == reason


def test_valid_status_actuator_and_encoder_frames():
    """Decode all V1 frame types and both allowed line endings."""
    decoder = FeedbackDecoder()
    status = decoded(decoder, frame('V1,STA,42,2,0,1,1,0'))
    assert status == VehicleFeedback(1, 42, 2, False, True, True, 0)
    actuator = decoded(decoder, frame('V1,ACT,42,-100,100,1', b'\r\n'))
    assert actuator == ActuatorFeedback(1, 42, -100, 100, True)
    encoder = decoded(decoder, frame('V1,ENC,7,-1,2,-3,4'))
    assert encoder == EncoderFeedback(1, 7, -1, 2, -3, 4)


@pytest.mark.parametrize(
    ('wire', 'reason'),
    [
        (b'V1,ACT,1,0,0,0*0000\n', 'crc_error'),
        (frame('V2,ACT,1,0,0,0'), 'unknown_version'),
        (frame('V1,WHAT,1'), 'unknown_frame_type'),
        (frame('V1,ACT,1,0,0'), 'field_count'),
        (frame('V1,ACT,1,,0,0'), 'empty_field'),
        (frame('V1,ACT,no,0,0,0'), 'invalid_integer'),
        (frame('V1,ACT,4294967296,0,0,0'), 'range'),
        (frame('V1,ACT,1,101,0,0'), 'range'),
        (frame('V1,ACT,01,0,0,0'), 'invalid_integer'),
        (frame('V1,ACT,1,0,0,2'), 'invalid_boolean'),
        (frame('V1,STA,1,3,0,0,0,0'), 'range'),
        (frame('V1,STA,1,0,0,0,0,2048'), 'unknown_fault_bits'),
        (frame('V1,STA,1,0,0,0,1,0'), 'invalid_status'),
        (frame('V1,STA,1,1,0,1,1,0'), 'invalid_status'),
        (frame('V1,STA,1,2,1,1,1,0'), 'invalid_status'),
        (b'V1,ACT,1,0,0,0*12\n', 'invalid_crc_format'),
        (b'V1,ACT,1,0,0,0\n', 'missing_or_multiple_crc'),
        (b'V1,ACT,1,0,0,0*0000\xff\n', 'non_ascii'),
    ],
)
def test_rejects_invalid_frames(wire, reason):
    """Reject CRC, version, type, count, format, enum and range errors."""
    rejected(FeedbackDecoder(), wire, reason)


def test_fragmented_and_concatenated_streams_recover_after_invalid_frame():
    """Handle arbitrary read boundaries and recover at the next LF."""
    decoder = FeedbackDecoder()
    first = frame('V1,ACT,9,-2,3,0')
    assert decoder.feed(first[:4]) == []
    assert decoder.feed(first[4:-1]) == []
    events = decoder.feed(first[-1:] + b'bad\n' + frame('V1,ENC,2,1,2,3,4'))
    assert isinstance(events[0], DecodedFrame)
    assert isinstance(events[1], RejectedFrame)
    assert isinstance(events[2], DecodedFrame)
    assert isinstance(events[2].feedback, EncoderFeedback)


def test_empty_lines_are_ignored_and_partial_frame_waits_for_lf():
    """Ignore empty lines and never publish an unterminated fragment."""
    decoder = FeedbackDecoder()
    assert decoder.feed(b'\n\r\n') == []
    assert decoder.feed(frame('V1,ACT,1,0,0,0')[:-1]) == []
    assert decoder.buffered_bytes > 0


def test_overlong_frame_is_bounded_and_next_frame_is_decoded():
    """Bound retained memory while discarding through the next LF."""
    decoder = FeedbackDecoder(max_frame_length=32)
    events = decoder.feed(b'X' * 100)
    assert len(events) == 1
    assert events[0].reason == 'overlong_frame'
    assert decoder.buffered_bytes == 0
    assert decoder.feed(b'ignored\n') == []
    feedback = decoded(decoder, frame('V1,ACT,1,0,0,0'))
    assert isinstance(feedback, ActuatorFeedback)


def test_reset_rejects_truncated_frame_and_clears_ack_state():
    """Treat a reconnect as a framing and sequence epoch boundary."""
    decoder = FeedbackDecoder()
    decoded(decoder, frame('V1,STA,10,0,0,0,0,0'))
    decoder.feed(b'V1,ENC,')
    event = decoder.reset()
    assert event is not None and event.reason == 'truncated_frame'
    # A lower ACK is valid as the first observation of the new connection.
    decoded(decoder, frame('V1,STA,1,0,0,0,0,0'))


def test_ack_progress_duplicate_regression_implausible_and_uint32_wrap():
    """Apply serial uint32 ordering, plausibility and valid wrap rules."""
    decoder = FeedbackDecoder()
    decoded(decoder, frame('V1,STA,4294967294,0,0,0,0,0'))
    decoded(decoder, frame('V1,STA,4294967295,0,0,0,0,0'))
    decoded(decoder, frame('V1,STA,0,0,0,0,0,0'))
    rejected(decoder, frame('V1,STA,0,0,0,0,0,0'), 'ack_duplicate')
    rejected(
        decoder, frame('V1,STA,4294967295,0,0,0,0,0'),
        'ack_regression',
    )
    rejected(decoder, frame('V1,STA,1000001,0,0,0,0,0'), 'ack_implausible')
    decoded(decoder, frame('V1,STA,1,0,0,0,0,0'))


@pytest.mark.parametrize('tick', [INT32_MIN, -1, 0, 1, INT32_MAX])
def test_encoder_signed_boundaries(tick):
    """Accept positive, negative and both int32 encoder endpoints."""
    feedback = decoded(
        FeedbackDecoder(), frame(f'V1,ENC,0,{tick},{tick},{tick},{tick}')
    )
    assert feedback.front_left_ticks == tick


@pytest.mark.parametrize('tick', [INT32_MIN - 1, INT32_MAX + 1])
def test_encoder_overflow_is_rejected(tick):
    """Reject encoder values beyond the documented int32 wire range."""
    rejected(
        FeedbackDecoder(), frame(f'V1,ENC,0,{tick},0,0,0'), 'range'
    )
