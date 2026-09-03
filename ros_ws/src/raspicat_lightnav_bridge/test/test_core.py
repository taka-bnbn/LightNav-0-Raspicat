import math

from raspicat_lightnav_bridge.core import limit_command


def test_limits_forward_and_turn_rate():
    assert limit_command(1.0, -2.0, 0.08, 0.25) == (0.08, -0.25)


def test_reverse_is_blocked_by_default():
    assert limit_command(-0.1, 0.1, 0.08, 0.25) == (0.0, 0.1)


def test_invalid_values_become_zero():
    assert limit_command(math.nan, math.inf, 0.08, 0.25) == (0.0, 0.0)


def test_reverse_can_be_enabled():
    assert limit_command(-0.04, 0.0, 0.08, 0.25, True) == (-0.04, 0.0)
