"""Safety and ROS graph tests for drive_commander."""

import importlib.machinery
import importlib.util
import math
import time
from pathlib import Path

import pytest

from rc_car_interfaces.msg import DriveCommand

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node


SCRIPT = Path(__file__).parents[1] / 'scripts' / 'drive_commander'
LOADER = importlib.machinery.SourceFileLoader(
    'drive_commander_under_test', str(SCRIPT)
)
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
drive_commander = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(drive_commander)
DriveCommandArbiter = drive_commander.DriveCommandArbiter


def assert_neutral(result, reason=None):
    """Assert a disabled neutral arbitration result."""
    speed, steering, enabled, actual_reason = result
    assert (speed, steering, enabled) == (0, 0, False)
    if reason is not None:
        assert actual_reason == reason


def enable_source(arbiter, source, now=1.0):
    """Select and safety-enable a source, then provide a fresh request."""
    arbiter.set_mode(source)
    arbiter.set_drive_enable(True)
    assert arbiter.accept_request(source, 40, -20, now) == (True, None)


def test_start_is_disabled_and_neutral():
    """Startup cannot produce motion."""
    arbiter = DriveCommandArbiter()
    assert_neutral(arbiter.evaluate(0.0, True, 0.3), 'mode_disabled')


@pytest.mark.parametrize('source', DriveCommandArbiter.VALID_SOURCES)
def test_each_source_transition_requires_a_new_request(source):
    """No selected source is usable before its post-transition request."""
    arbiter = DriveCommandArbiter()
    arbiter.set_mode(source)
    arbiter.set_drive_enable(True)
    assert_neutral(
        arbiter.evaluate(1.0, True, 0.3), 'safety_refresh_required'
    )
    arbiter.accept_request(source, 25, -10, 1.0)
    assert arbiter.evaluate(1.1, True, 0.3) == (25, -10, True, 'enabled')


def test_return_to_previously_used_source_does_not_reactivate_cache():
    """Switching away and back cannot revive an earlier request."""
    arbiter = DriveCommandArbiter()
    enable_source(arbiter, 'AUTONOMOUS')
    assert arbiter.evaluate(1.1, True, 0.3)[2]
    arbiter.set_mode('MANUAL')
    arbiter.accept_request('MANUAL', -30, 5, 1.2)
    arbiter.set_mode('AUTONOMOUS')
    assert_neutral(
        arbiter.evaluate(1.3, True, 0.3), 'source_refresh_required'
    )


def test_switch_after_non_neutral_request_immediately_neutralizes():
    """A source change invalidates a currently moving request."""
    arbiter = DriveCommandArbiter()
    enable_source(arbiter, 'TEST')
    assert arbiter.evaluate(1.1, True, 0.3) == (40, -20, True, 'enabled')
    changed, reason = arbiter.set_mode('MANUAL')
    assert (changed, reason) == (True, 'source_transition')
    assert_neutral(
        arbiter.evaluate(1.1, True, 0.3), 'source_refresh_required'
    )


def test_source_timeout_discards_request_permanently():
    """A timed-out request stays invalid until another request arrives."""
    arbiter = DriveCommandArbiter()
    enable_source(arbiter, 'AUTONOMOUS')
    assert_neutral(arbiter.evaluate(1.31, True, 0.3), 'source_timeout')
    assert_neutral(arbiter.evaluate(1.32, False, 0.3), 'source_timeout')
    arbiter.accept_request('AUTONOMOUS', 7, 8, 1.32)
    assert arbiter.evaluate(1.33, True, 0.3) == (7, 8, True, 'enabled')


def test_safety_edges_neutralize_and_require_fresh_request():
    """Safety off/on edges cannot reactivate the pre-edge request."""
    arbiter = DriveCommandArbiter()
    enable_source(arbiter, 'MANUAL')
    assert arbiter.evaluate(1.1, True, 0.3)[2]
    assert arbiter.set_drive_enable(False) == (True, 'safety_off')
    assert_neutral(arbiter.evaluate(1.1, True, 0.3), 'source_missing')
    assert arbiter.set_drive_enable(True) == (True, 'safety_transition')
    assert_neutral(
        arbiter.evaluate(1.1, True, 0.3), 'safety_refresh_required'
    )
    arbiter.accept_request('MANUAL', 9, 10, 1.1)
    assert arbiter.evaluate(1.2, True, 0.3) == (9, 10, True, 'enabled')


def test_disabled_and_invalid_modes_fail_safe():
    """DISABLED and malformed modes invalidate all motion state."""
    arbiter = DriveCommandArbiter()
    enable_source(arbiter, 'TEST')
    assert arbiter.set_mode('DISABLED') == (True, 'mode_disabled')
    assert_neutral(arbiter.evaluate(1.1, True, 0.3), 'mode_disabled')
    arbiter.set_mode('TEST')
    arbiter.accept_request('TEST', 20, 20, 1.1)
    assert arbiter.set_mode('not-a-mode') == (True, 'invalid_mode')
    assert_neutral(arbiter.evaluate(1.2, True, 0.3), 'invalid_mode')
    assert arbiter.last_rejection == {
        'source': 'mode', 'reason': 'invalid_mode'
    }


@pytest.mark.parametrize('value', [-128, -101, 101, 127])
def test_out_of_range_values_are_rejected_not_clamped(value):
    """Representable int8 values outside the command contract are rejected."""
    arbiter = DriveCommandArbiter()
    enable_source(arbiter, 'TEST')
    assert arbiter.accept_request('TEST', value, 0, 1.1) == (
        False, 'value_out_of_range'
    )
    assert_neutral(
        arbiter.evaluate(1.2, True, 0.3), 'value_out_of_range'
    )


@pytest.mark.parametrize('value', [math.nan, math.inf, -math.inf])
def test_non_finite_values_are_rejected(value):
    """Core validation rejects values ROS int8 cannot itself serialize."""
    arbiter = DriveCommandArbiter()
    enable_source(arbiter, 'TEST')
    assert arbiter.accept_request('TEST', value, 0, 1.1) == (
        False, 'non_finite_value'
    )
    assert_neutral(
        arbiter.evaluate(1.2, True, 0.3), 'non_finite_value'
    )


def test_inactive_source_request_is_never_cached():
    """Requests received before their source is selected remain unusable."""
    arbiter = DriveCommandArbiter()
    assert arbiter.accept_request('MANUAL', 50, 0, 1.0) == (
        False, 'inactive_source'
    )
    arbiter.set_mode('MANUAL')
    arbiter.set_drive_enable(True)
    assert_neutral(arbiter.evaluate(1.1, True, 0.3))


def test_ros_node_has_one_publisher_and_monotonic_sequences():
    """The runtime graph has one final publisher with increasing sequences."""
    context = rclpy.context.Context()
    rclpy.init(context=context)
    commander = drive_commander.DriveCommander(context=context)
    observer = Node('drive_commander_test_observer', context=context)
    received = []
    observer.create_subscription(
        DriveCommand, '/drive_commands',
        lambda message: received.append(message.sequence), 10
    )
    executor = SingleThreadedExecutor(context=context)
    executor.add_node(commander)
    executor.add_node(observer)
    try:
        deadline = time.monotonic() + 3.0
        while len(received) < 5 and time.monotonic() < deadline:
            executor.spin_once(timeout_sec=0.05)
        assert len(received) >= 5
        assert received == sorted(received)
        assert len(set(received)) == len(received)
        publishers = observer.get_publishers_info_by_topic('/drive_commands')
        assert len(publishers) == 1
        assert publishers[0].node_name == 'drive_commander'
    finally:
        executor.remove_node(observer)
        executor.remove_node(commander)
        observer.destroy_node()
        commander.destroy_node()
        executor.shutdown()
        rclpy.shutdown(context=context)
