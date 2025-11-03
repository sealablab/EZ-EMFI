"""
User-friendly duration classes for BasicAppDataTypes.

Provides PulseDuration_* classes that abstract time durations with
platform-aware clock cycle conversion.

Design Reference: docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md
"""

import math
from typing import Literal
from .types import BasicAppDataTypes


class PulseDuration_ns:
    """
    Nanosecond-based time duration.

    Example:
        >>> firing_duration = PulseDuration_ns(500, width=16)
        >>> firing_duration.value
        500
        >>> firing_duration.to_basic_type()
        BasicAppDataTypes.PULSE_DURATION_NS_U16
        >>>
        >>> # Convert to clock cycles (Moku:Go @ 125 MHz, 8ns period)
        >>> cycles = firing_duration.to_cycles(
        ...     clock_period_ns=8.0,
        ...     rounding='ROUND_UP'
        ... )
        >>> cycles
