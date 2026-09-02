"""Serialization and constant-contract tests for pylon interfaces."""

from rc_car_interfaces.msg import PylonObservation, PylonObservationArray

from rclpy.serialization import deserialize_message, serialize_message


def test_pylon_enum_values_are_stable():
    """Keep enum values stable for independent producers and consumers."""
    assert PylonObservation.CLASS_UNKNOWN == 0
    assert PylonObservation.CLASS_TRAFFIC_CONE == 1
    assert PylonObservation.COLOR_UNKNOWN == 0
    assert PylonObservation.COLOR_BLUE == 1
    assert PylonObservation.COLOR_YELLOW == 2
    assert PylonObservation.COLOR_ORANGE == 3
    assert PylonObservation.COLOR_RED == 4
    assert PylonObservation.RANGE_NONE == 0
    assert PylonObservation.RANGE_MONOCULAR_SIZE == 1
    assert PylonObservation.RANGE_STEREO == 2
    assert PylonObservation.RANGE_DEPTH_SENSOR == 3


def test_pylon_array_round_trip_preserves_contract_boundaries():
    """Preserve valid low/high boundary examples through serialization."""
    message = PylonObservationArray()
    message.header.stamp.sec = 42
    message.header.stamp.nanosec = 123_000_000
    message.header.frame_id = 'base_link'

    near = PylonObservation()
    near.track_id = 1
    near.object_class = PylonObservation.CLASS_TRAFFIC_CONE
    near.color = PylonObservation.COLOR_BLUE
    near.bbox.center.position.x = 320.0
    near.bbox.center.position.y = 240.0
    near.bbox.size_x = 80.0
    near.bbox.size_y = 160.0
    near.confidence = 0.0
    near.bearing_rad = -1.0
    near.bearing_stddev_rad = 0.01
    near.range_valid = False
    near.range_m = 0.0
    near.range_stddev_m = 0.0
    near.range_source = PylonObservation.RANGE_NONE

    far = PylonObservation()
    far.track_id = 2
    far.object_class = PylonObservation.CLASS_TRAFFIC_CONE
    far.color = PylonObservation.COLOR_YELLOW
    far.bbox.center.position.x = 640.0
    far.bbox.center.position.y = 240.0
    far.bbox.size_x = 20.0
    far.bbox.size_y = 40.0
    far.confidence = 1.0
    far.bearing_rad = 1.0
    far.bearing_stddev_rad = 0.2
    far.range_valid = True
    far.range_m = 12.5
    far.range_stddev_m = 1.25
    far.range_source = PylonObservation.RANGE_MONOCULAR_SIZE

    message.observations = [near, far]
    restored = deserialize_message(
        serialize_message(message), PylonObservationArray)

    assert restored.header.stamp.sec == 42
    assert restored.header.frame_id == 'base_link'
    assert len(restored.observations) == 2
    assert restored.observations[0].confidence == 0.0
    assert restored.observations[0].bearing_rad == -1.0
    assert not restored.observations[0].range_valid
    assert restored.observations[0].range_source == PylonObservation.RANGE_NONE
    assert restored.observations[1].confidence == 1.0
    assert restored.observations[1].bearing_rad == 1.0
    assert restored.observations[1].range_valid
    assert restored.observations[1].range_source == (
        PylonObservation.RANGE_MONOCULAR_SIZE)
    assert restored.observations[1].bbox.size_y == 40.0


def test_empty_detection_result_round_trip_is_explicit():
    """Represent a processed frame with no detections as an empty array."""
    message = PylonObservationArray()
    message.header.frame_id = 'base_link'
    restored = deserialize_message(
        serialize_message(message), PylonObservationArray)
    assert restored.header.frame_id == 'base_link'
    assert restored.observations == []
