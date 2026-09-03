"""ROS-independent command limiting helpers."""

from __future__ import annotations

import math


def clamp(value: float, limit: float) -> float:
    """Clamp a finite value symmetrically, rejecting invalid input as zero."""
    if not math.isfinite(value) or not math.isfinite(limit) or limit <= 0.0:
        return 0.0
    return max(-limit, min(limit, value))


def limit_command(
    linear_x: float,
    angular_z: float,
    max_linear: float,
    max_angular: float,
    allow_reverse: bool = False,
) -> tuple[float, float]:
    """Return a bounded differential-drive command."""
    linear = clamp(linear_x, max_linear)
    if not allow_reverse:
        linear = max(0.0, linear)
    return linear, clamp(angular_z, max_angular)
