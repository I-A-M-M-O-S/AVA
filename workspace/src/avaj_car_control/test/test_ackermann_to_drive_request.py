"""Tests for the SI-to-normalized autonomous command adapter."""

import importlib.machinery
import importlib.util
import math
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).parents[1] / 'scripts' / 'ackermann_to_drive_request'
)
LOADER = importlib.machinery.SourceFileLoader(
    'ackermann_adapter_under_test', str(SCRIPT)
)
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
adapter = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(adapter)


@pytest.fixture
def converter():
    return adapter.AckermannRequestConverter(1.5, 0.75, 0.5)


def test_converts_si_values_and_ros_steering_sign(converter):
    assert converter.convert(0.75, 0.25) == (50, -50)
    assert converter.convert(-0.375, -0.25) == (-50, 50)


def test_saturates_at_configured_vehicle_limits(converter):
    assert converter.convert(3.0, 1.0) == (100, -100)
    assert converter.convert(-2.0, -1.0) == (-100, 100)


@pytest.mark.parametrize('invalid', [math.nan, math.inf, -math.inf])
def test_invalid_input_fails_neutral(converter, invalid):
    assert converter.convert(invalid, 0.0) == (0, 0)
    assert converter.convert(0.2, invalid) == (0, 0)


def test_invalid_calibration_is_rejected():
    with pytest.raises(ValueError):
        adapter.AckermannRequestConverter(0.0, 1.0, 0.5)
