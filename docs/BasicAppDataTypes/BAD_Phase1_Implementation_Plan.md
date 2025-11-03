# BAD Phase 1: Implementation Plan

**Phase:** 1 of 6
**Goal:** Implement BasicAppDataTypes with fixed-width serialization
**Prerequisites:** None (first phase)
**Branch:** `feature/BAD/P1`
**Status:** Design Complete → Ready for Implementation

---

## Implementation Overview

Phase 1 implements the core type system with three categories:
1. **Voltage Types** - Platform-specific, INPUT/OUTPUT distinction
2. **Time Types** - User-friendly durations with platform-aware serialization
3. **Boolean Type** - Single 1-bit boolean

**Authoritative Design References:**
- [VOLTAGE_TYPE_SYSTEM.md](./VOLTAGE_TYPE_SYSTEM.md) - Complete voltage type taxonomy
- [TIME_TYPE_SYSTEM.md](./TIME_TYPE_SYSTEM.md) - Complete time/duration type taxonomy

**Legacy types are NOT implemented** - new type system supersedes old `RegisterType` enum.

---

## Git Workflow

### Branch Management

**Current branch:** `feature/BAD/P1` (created from `feature/BAD-main`)

**During development:**
```bash
# Commit frequently as you implement
git add <files>
git commit -m "feat(BAD/P1): <description>"
```

**Completing this phase:**
```bash
# Final commit with phase completion
git add .
git commit -m "feat(BAD/P1): Complete Phase 1 - Core type system implementation"

# Write completion summary
# (see "Phase Completion" section below)

# Merge back to feature branch
git checkout feature/BAD-main
git merge --no-ff feature/BAD/P1 -m "Merge Phase 1: Core type system implementation"
```

**Full workflow reference:** [BAD_MASTER_Orchestrator.md](./BAD_MASTER_Orchestrator.md#git-workflow)

---

## Implementation Tasks

### Task 1: Create `basic_app_datatypes.py` Structure

**File:** `models/custom_inst/basic_app_datatypes.py`

**Imports:**
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Union, Literal
import math
```

**Module structure:**
```python
# 1. BasicAppDataTypes enum (all type names)
# 2. TypeMetadata dataclass (type specifications)
# 3. TYPE_REGISTRY dict (metadata for each type)
# 4. User-friendly duration classes (PulseDuration_*)
# 5. TypeConverter class (conversion utilities)
```

---

### Task 2: Implement `BasicAppDataTypes` Enum

Define all type names from the design specs:

```python
class BasicAppDataTypes(str, Enum):
    """
    Fixed-width data types for BasicAppDataTypes system.

    Design principles:
    - Fixed, immutable bit widths
    - Platform-agnostic definitions
    - Self-documenting type names
    - No endianness (MSB-aligned packing)

    References:
    - Voltage types: docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md
    - Time types: docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md
    """

    # ========================================================================
    # VOLTAGE TYPES (see VOLTAGE_TYPE_SYSTEM.md)
    # ========================================================================

    # Output voltage types (DAC) - All platforms support ±5V
    VOLTAGE_OUTPUT_05V_S8 = "voltage_output_05v_s8"      # 8-bit signed, ±5V
    VOLTAGE_OUTPUT_05V_S16 = "voltage_output_05v_s16"    # 16-bit signed, ±5V
    VOLTAGE_OUTPUT_05V_U7 = "voltage_output_05v_u7"      # 7-bit unsigned, 0 to +5V
    VOLTAGE_OUTPUT_05V_U15 = "voltage_output_05v_u15"    # 15-bit unsigned, 0 to +5V

    # Input voltage types (ADC) - Delta: ±20V
    VOLTAGE_INPUT_20V_S8 = "voltage_input_20v_s8"        # 8-bit signed, ±20V
    VOLTAGE_INPUT_20V_S16 = "voltage_input_20v_s16"      # 16-bit signed, ±20V
    VOLTAGE_INPUT_20V_U7 = "voltage_input_20v_u7"        # 7-bit unsigned, 0 to +20V
    VOLTAGE_INPUT_20V_U15 = "voltage_input_20v_u15"      # 15-bit unsigned, 0 to +20V

    # Input voltage types (ADC) - Go/Lab/Pro: ±25V
    VOLTAGE_INPUT_25V_S8 = "voltage_input_25v_s8"        # 8-bit signed, ±25V
    VOLTAGE_INPUT_25V_S16 = "voltage_input_25v_s16"      # 16-bit signed, ±25V
    VOLTAGE_INPUT_25V_U7 = "voltage_input_25v_u7"        # 7-bit unsigned, 0 to +25V
    VOLTAGE_INPUT_25V_U15 = "voltage_input_25v_u15"      # 15-bit unsigned, 0 to +25V

    # ========================================================================
    # TIME TYPES (see TIME_TYPE_SYSTEM.md)
    # ========================================================================

    # Nanosecond-based durations
    PULSE_DURATION_NS_U8 = "pulse_duration_ns_u8"        # 8-bit, 0-255 ns
    PULSE_DURATION_NS_U16 = "pulse_duration_ns_u16"      # 16-bit, 0-65,535 ns
    PULSE_DURATION_NS_U32 = "pulse_duration_ns_u32"      # 32-bit, 0-4.29 sec

    # Microsecond-based durations
    PULSE_DURATION_US_U8 = "pulse_duration_us_u8"        # 8-bit, 0-255 µs
    PULSE_DURATION_US_U16 = "pulse_duration_us_u16"      # 16-bit, 0-65,535 µs
    PULSE_DURATION_US_U24 = "pulse_duration_us_u24"      # 24-bit, 0-16.7 sec

    # Millisecond-based durations
    PULSE_DURATION_MS_U8 = "pulse_duration_ms_u8"        # 8-bit, 0-255 ms
    PULSE_DURATION_MS_U16 = "pulse_duration_ms_u16"      # 16-bit, 0-65,535 ms

    # Second-based durations
    PULSE_DURATION_S_U8 = "pulse_duration_s_u8"          # 8-bit, 0-255 seconds
    PULSE_DURATION_S_U16 = "pulse_duration_s_u16"        # 16-bit, 0-65,535 seconds

    # ========================================================================
    # BOOLEAN TYPE
    # ========================================================================

    BOOLEAN = "boolean"  # 1-bit, True/False
```

---

### Task 3: Implement `TypeMetadata` Dataclass

```python
@dataclass(frozen=True)  # Immutable for safety
class TypeMetadata:
    """
    Metadata specification for a BasicAppDataType.

    Attributes:
        type_name: BasicAppDataTypes enum value
        bit_width: Fixed bit width (immutable)
        vhdl_type: VHDL type string (e.g., "signed(15 downto 0)")
        python_type: Python type (int, bool)
        min_value: Minimum allowed value (None for boolean)
        max_value: Maximum allowed value (None for boolean)
        default_value: Default value for this type
        direction: 'input', 'output', or None (for time/boolean)
        signedness: 'signed', 'unsigned', or None (for boolean)
        unit: Unit string ('mV', 'ns', 'us', 'ms', 's', None)
    """
    type_name: BasicAppDataTypes
    bit_width: int
    vhdl_type: str
    python_type: type
    min_value: Optional[int]
    max_value: Optional[int]
    default_value: Union[int, bool]
    direction: Optional[Literal['input', 'output']] = None
    signedness: Optional[Literal['signed', 'unsigned']] = None
    unit: Optional[str] = None
```

**Key requirement:** `frozen=True` makes bit_width immutable (critical for Phase 2 register packing).

---

### Task 4: Implement `TYPE_REGISTRY`

Create registry with metadata for all types:

```python
TYPE_REGISTRY: dict[BasicAppDataTypes, TypeMetadata] = {
    # ========================================================================
    # VOLTAGE OUTPUT TYPES (±5V, all platforms)
    # ========================================================================
    BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S8: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S8,
        bit_width=8,
        vhdl_type="signed(7 downto 0)",
        python_type=int,
        min_value=-5000,  # -5V in mV
        max_value=5000,   # +5V in mV
        default_value=0,
        direction='output',
        signedness='signed',
        unit='mV'
    ),
    BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
        bit_width=16,
        vhdl_type="signed(15 downto 0)",
        python_type=int,
        min_value=-5000,
        max_value=5000,
        default_value=0,
        direction='output',
        signedness='signed',
        unit='mV'
    ),
    # ... (continue for all voltage types)

    # ========================================================================
    # TIME TYPES
    # ========================================================================
    BasicAppDataTypes.PULSE_DURATION_NS_U8: TypeMetadata(
        type_name=BasicAppDataTypes.PULSE_DURATION_NS_U8,
        bit_width=8,
        vhdl_type="unsigned(7 downto 0)",
        python_type=int,
        min_value=0,
        max_value=255,  # nanoseconds
        default_value=0,
        direction=None,
        signedness='unsigned',
        unit='ns'
    ),
    # ... (continue for all time types)

    # ========================================================================
    # BOOLEAN TYPE
    # ========================================================================
    BasicAppDataTypes.BOOLEAN: TypeMetadata(
        type_name=BasicAppDataTypes.BOOLEAN,
        bit_width=1,
        vhdl_type="std_logic",
        python_type=bool,
        min_value=None,
        max_value=None,
        default_value=False,
        direction=None,
        signedness=None,
        unit=None
    ),
}
```

**Implementation note:** Complete all 25 entries (12 voltage + 12 time + 1 boolean).

---

### Task 5: Implement User-Friendly Duration Classes

```python
class PulseDuration_ns:
    """
    Nanosecond-based time duration.

    Example:
        >>> firing_duration = PulseDuration_ns(500, width=16)
        >>> firing_duration.value
        500
        >>> firing_duration.to_basic_type()
        BasicAppDataTypes.PULSE_DURATION_NS_U16
    """

    def __init__(self, nanoseconds: int, width: Literal[8, 16, 32] = 16):
        """
        Create a nanosecond duration.

        Args:
            nanoseconds: Duration in nanoseconds
            width: Bit width for serialization (8, 16, or 32)

        Raises:
            ValueError: If nanoseconds exceeds max for chosen width
            ValueError: If nanoseconds is negative
        """
        if nanoseconds < 0:
            raise ValueError("Duration cannot be negative")

        max_value = (2 ** width) - 1
        if nanoseconds > max_value:
            raise ValueError(
                f"{nanoseconds}ns exceeds max for U{width} ({max_value}ns)"
            )

        self.value = nanoseconds
        self.unit = 'ns'
        self.width = width

    def to_basic_type(self) -> BasicAppDataTypes:
        """Convert to explicit BasicAppDataTypes enum."""
        if self.width == 8:
            return BasicAppDataTypes.PULSE_DURATION_NS_U8
        elif self.width == 16:
            return BasicAppDataTypes.PULSE_DURATION_NS_U16
        elif self.width == 32:
            return BasicAppDataTypes.PULSE_DURATION_NS_U32
        else:
            raise ValueError(f"Unsupported width: {self.width}")

    def to_nanoseconds(self) -> int:
        """Get value in nanoseconds."""
        return self.value

    def to_cycles(self, clock_period_ns: float,
                   rounding: Literal['ROUND_UP', 'ROUND_DOWN', 'EXACT']) -> int:
        """
        Convert to clock cycles for target platform.

        Args:
            clock_period_ns: Platform clock period (from platform.clock_period_ns)
            rounding: Rounding strategy (global configuration)

        Returns:
            Number of clock cycles

        Raises:
            ValueError: If rounding='EXACT' and not evenly divisible
        """
        exact_cycles = self.value / clock_period_ns

        if rounding == 'EXACT':
            if exact_cycles != int(exact_cycles):
                raise ValueError(
                    f"{self.value}ns not evenly divisible by "
                    f"clock period {clock_period_ns}ns. "
                    "Use ROUND_UP or ROUND_DOWN."
                )
            return int(exact_cycles)
        elif rounding == 'ROUND_UP':
            return math.ceil(exact_cycles)
        elif rounding == 'ROUND_DOWN':
            return math.floor(exact_cycles)
        else:
            raise ValueError(f"Invalid rounding mode: {rounding}")

# Implement similar classes for:
# - PulseDuration_us (microseconds)
# - PulseDuration_ms (milliseconds)
# - PulseDuration_sec (seconds)
```

---

### Task 6: Implement `TypeConverter` Class

```python
class TypeConverter:
    """
    Conversion utilities for BasicAppDataTypes.

    Handles bidirectional conversion between user-friendly units
    (millivolts, nanoseconds) and raw binary values for serialization.
    """

    # ========================================================================
    # VOLTAGE CONVERSIONS
    # ========================================================================

    @staticmethod
    def voltage_output_05v_s8_to_raw(millivolts: int) -> int:
        """
        Convert millivolts to 8-bit signed raw value (±5V range).

        Args:
            millivolts: Voltage in millivolts (-5000 to +5000)

        Returns:
            8-bit signed raw value (-128 to +127)

        Raises:
            ValueError: If millivolts out of range
        """
        if not (-5000 <= millivolts <= 5000):
            raise ValueError(f"Voltage {millivolts}mV out of ±5V range")

        # Scale: (mV / 5000.0) * 127
        raw = int((millivolts / 5000.0) * 127)
        return max(-128, min(127, raw))  # Clamp to 8-bit signed range

    @staticmethod
    def raw_to_voltage_output_05v_s8(raw: int) -> int:
        """
        Convert 8-bit signed raw to millivolts (±5V range).

        Args:
            raw: 8-bit signed raw value (-128 to +127)

        Returns:
            Voltage in millivolts
        """
        if not (-128 <= raw <= 127):
            raise ValueError(f"Raw value {raw} out of 8-bit signed range")

        # Scale: (raw / 127.0) * 5000
        return int((raw / 127.0) * 5000)

    # Implement similar converters for all voltage types:
    # - voltage_output_05v_s16_to_raw / raw_to_voltage_output_05v_s16
    # - voltage_output_05v_u7_to_raw / raw_to_voltage_output_05v_u7
    # - voltage_output_05v_u15_to_raw / raw_to_voltage_output_05v_u15
    # - voltage_input_20v_* (4 converters)
    # - voltage_input_25v_* (4 converters)

    # ========================================================================
    # TIME CONVERSIONS
    # ========================================================================

    @staticmethod
    def time_to_cycles(
        value: int,
        unit: Literal['ns', 'us', 'ms', 's'],
        clock_period_ns: float,
        rounding: Literal['ROUND_UP', 'ROUND_DOWN', 'EXACT']
    ) -> int:
        """
        Convert time value to clock cycles (platform-aware).

        Args:
            value: Time value in specified unit
            unit: Time unit ('ns', 'us', 'ms', 's')
            clock_period_ns: Platform clock period in nanoseconds
            rounding: Rounding strategy

        Returns:
            Number of clock cycles

        Raises:
            ValueError: If rounding='EXACT' and not evenly divisible
        """
        # Convert to nanoseconds
        if unit == 'ns':
            duration_ns = value
        elif unit == 'us':
            duration_ns = value * 1000
        elif unit == 'ms':
            duration_ns = value * 1_000_000
        elif unit == 's':
            duration_ns = value * 1_000_000_000
        else:
            raise ValueError(f"Invalid unit: {unit}")

        # Convert to cycles
        exact_cycles = duration_ns / clock_period_ns

        if rounding == 'EXACT':
            if exact_cycles != int(exact_cycles):
                raise ValueError(
                    f"{value}{unit} not evenly divisible by "
                    f"clock period {clock_period_ns}ns"
                )
            return int(exact_cycles)
        elif rounding == 'ROUND_UP':
            return math.ceil(exact_cycles)
        elif rounding == 'ROUND_DOWN':
            return math.floor(exact_cycles)
        else:
            raise ValueError(f"Invalid rounding mode: {rounding}")

    @staticmethod
    def cycles_to_time(
        cycles: int,
        unit: Literal['ns', 'us', 'ms', 's'],
        clock_period_ns: float
    ) -> int:
        """
        Convert clock cycles to time value (platform-aware).

        Args:
            cycles: Number of clock cycles
            unit: Desired time unit
            clock_period_ns: Platform clock period in nanoseconds

        Returns:
            Time value in specified unit
        """
        duration_ns = cycles * clock_period_ns

        if unit == 'ns':
            return int(duration_ns)
        elif unit == 'us':
            return int(duration_ns / 1000)
        elif unit == 'ms':
            return int(duration_ns / 1_000_000)
        elif unit == 's':
            return int(duration_ns / 1_000_000_000)
        else:
            raise ValueError(f"Invalid unit: {unit}")
```

---

## Testing Requirements

### Test File: `tests/test_basic_app_datatypes.py`

**Test coverage:**

#### 1. Type Registry Tests
```python
def test_type_registry_completeness():
    """Verify all BasicAppDataTypes have metadata."""
    for type_enum in BasicAppDataTypes:
        assert type_enum in TYPE_REGISTRY
        metadata = TYPE_REGISTRY[type_enum]
        assert metadata.bit_width > 0
        assert metadata.vhdl_type
        assert metadata.python_type

def test_bit_width_immutable():
    """Ensure bit widths are truly fixed."""
    metadata = TYPE_REGISTRY[BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16]
    assert metadata.bit_width == 16

    # Should not be able to change (frozen dataclass)
    with pytest.raises(AttributeError):
        metadata.bit_width = 32
```

#### 2. Voltage Conversion Tests
```python
def test_voltage_output_05v_s16_conversion():
    """Test ±5V 16-bit signed voltage conversions."""
    # Test nominal values
    raw = TypeConverter.voltage_output_05v_s16_to_raw(2400)  # 2.4V
    assert -32768 <= raw <= 32767
    recovered = TypeConverter.raw_to_voltage_output_05v_s16(raw)
    assert abs(recovered - 2400) <= 10  # Allow ~10mV rounding error

    # Test limits
    assert TypeConverter.voltage_output_05v_s16_to_raw(5000) == 32767
    assert TypeConverter.voltage_output_05v_s16_to_raw(-5000) == -32768

    # Test out-of-range
    with pytest.raises(ValueError):
        TypeConverter.voltage_output_05v_s16_to_raw(6000)  # Exceeds ±5V

def test_voltage_input_25v_s16_conversion():
    """Test ±25V 16-bit signed voltage conversions."""
    # Test nominal value
    raw = TypeConverter.voltage_input_25v_s16_to_raw(10000)  # 10V
    recovered = TypeConverter.raw_to_voltage_input_25v_s16(raw)
    assert abs(recovered - 10000) <= 50  # Allow ~50mV rounding error

    # Test limits
    assert TypeConverter.voltage_input_25v_s16_to_raw(25000) == 32767
    assert TypeConverter.voltage_input_25v_s16_to_raw(-25000) == -32768

# Add tests for all 12 voltage type converters
```

#### 3. Time Conversion Tests
```python
def test_pulse_duration_ns_construction():
    """Test PulseDuration_ns validation."""
    # Valid construction
    duration = PulseDuration_ns(500, width=16)
    assert duration.value == 500
    assert duration.unit == 'ns'
    assert duration.width == 16

    # Invalid: exceeds U8 max
    with pytest.raises(ValueError):
        PulseDuration_ns(500, width=8)  # 500 > 255

    # Invalid: negative duration
    with pytest.raises(ValueError):
        PulseDuration_ns(-100, width=16)

def test_pulse_duration_to_cycles_exact():
    """Test exact cycle conversion (no rounding)."""
    duration = PulseDuration_ns(800, width=16)

    # Moku:Go @ 125 MHz (8ns period)
    cycles = duration.to_cycles(clock_period_ns=8.0, rounding='EXACT')
    assert cycles == 100  # 800ns / 8ns = 100 cycles (exact)

    # Should fail if not evenly divisible
    duration_odd = PulseDuration_ns(500, width=16)
    with pytest.raises(ValueError):
        duration_odd.to_cycles(clock_period_ns=8.0, rounding='EXACT')

def test_pulse_duration_to_cycles_rounding():
    """Test rounding strategies."""
    duration = PulseDuration_ns(500, width=16)

    # ROUND_UP: 500ns / 8ns = 62.5 → 63 cycles
    cycles_up = duration.to_cycles(clock_period_ns=8.0, rounding='ROUND_UP')
    assert cycles_up == 63

    # ROUND_DOWN: 500ns / 8ns = 62.5 → 62 cycles
    cycles_down = duration.to_cycles(clock_period_ns=8.0, rounding='ROUND_DOWN')
    assert cycles_down == 62

# Add tests for all 4 duration classes (ns, us, ms, sec)
```

#### 4. Platform Compatibility Tests
```python
def test_voltage_platform_compatibility():
    """Verify voltage types work across all Moku platforms."""
    from moku_models import (
        MOKU_GO_PLATFORM,
        MOKU_LAB_PLATFORM,
        MOKU_PRO_PLATFORM,
        MOKU_DELTA_PLATFORM
    )

    # ±5V output type should work on all platforms
    test_mv = 2400
    raw = TypeConverter.voltage_output_05v_s16_to_raw(test_mv)

    for platform in [MOKU_GO_PLATFORM, MOKU_LAB_PLATFORM,
                      MOKU_PRO_PLATFORM, MOKU_DELTA_PLATFORM]:
        # All platforms support ±5V outputs
        assert platform.get_analog_output_by_id('OUT1').voltage_range_vpp == 10.0

def test_time_platform_compatibility():
    """Verify time types convert correctly for all platforms."""
    from moku_models import MOKU_GO_PLATFORM, MOKU_DELTA_PLATFORM

    duration_ms = PulseDuration_ms(100, width=16)  # 100ms

    # Moku:Go @ 125 MHz (8ns period)
    cycles_go = duration_ms.to_cycles(
        clock_period_ns=MOKU_GO_PLATFORM.clock_period_ns,
        rounding='EXACT'
    )
    assert cycles_go == 12_500_000  # 100ms @ 125MHz

    # Moku:Delta @ 5 GHz (0.2ns period)
    cycles_delta = duration_ms.to_cycles(
        clock_period_ns=MOKU_DELTA_PLATFORM.clock_period_ns,
        rounding='EXACT'
    )
    assert cycles_delta == 500_000_000  # 100ms @ 5GHz
```

#### 5. Boolean Type Tests
```python
def test_boolean_type():
    """Test boolean type metadata."""
    metadata = TYPE_REGISTRY[BasicAppDataTypes.BOOLEAN]
    assert metadata.bit_width == 1
    assert metadata.vhdl_type == "std_logic"
    assert metadata.python_type == bool
    assert metadata.default_value == False
```

**Test execution:**
```bash
# Run all tests
uv run pytest tests/test_basic_app_datatypes.py -v

# Run with coverage
uv run pytest tests/test_basic_app_datatypes.py --cov=models.custom_inst.basic_app_datatypes
```

---

## Implementation Checklist

Phase 1 is complete when:

- [x] Design specifications written
  - [x] `VOLTAGE_TYPE_SYSTEM.md` committed
  - [x] `TIME_TYPE_SYSTEM.md` committed
- [ ] `basic_app_datatypes.py` implemented
  - [ ] `BasicAppDataTypes` enum (25 types)
  - [ ] `TypeMetadata` dataclass (frozen)
  - [ ] `TYPE_REGISTRY` (25 entries)
  - [ ] `PulseDuration_*` classes (4 classes: ns, us, ms, sec)
  - [ ] `TypeConverter` class (voltage + time converters)
- [ ] Unit tests passing
  - [ ] Type registry completeness tests
  - [ ] Voltage conversion tests (all 12 types)
  - [ ] Time conversion tests (all 12 types)
  - [ ] Platform compatibility tests
  - [ ] Boolean type tests
  - [ ] Immutability tests
- [ ] Documentation complete
  - [ ] Docstrings for all classes/methods
  - [ ] Type hints for all functions
  - [ ] Usage examples in docstrings
- [ ] Phase completion summary written
  - [ ] `BAD_Phase1_COMPLETE.md`

---

## Phase Completion

### Step 1: Write Completion Summary

Create `docs/BasicAppDataTypes/BAD_Phase1_COMPLETE.md` with:

```markdown
# BAD Phase 1 Completion Summary

**Phase:** 1 of 6 - Core Type System Implementation
**Status:** Complete ✓
**Completion Date:** YYYY-MM-DD
**Git Commit:** {git_hash}

## Deliverables

### 1. Type Definitions Implemented

**Voltage Types (12 total):**
- Output types (4): VOLTAGE_OUTPUT_05V_{S8,S16,U7,U15}
- Input types ±20V (4): VOLTAGE_INPUT_20V_{S8,S16,U7,U15}
- Input types ±25V (4): VOLTAGE_INPUT_25V_{S8,S16,U7,U15}

**Time Types (12 total):**
- Nanoseconds (3): PULSE_DURATION_NS_{U8,U16,U32}
- Microseconds (3): PULSE_DURATION_US_{U8,U16,U24}
- Milliseconds (2): PULSE_DURATION_MS_{U8,U16}
- Seconds (2): PULSE_DURATION_S_{U8,U16}

**Boolean Type (1):**
- BOOLEAN (1-bit)

**Total: 25 types**

### 2. Key Design Decisions

1. **Voltage types have INPUT/OUTPUT distinction** - prevents misuse
2. **Voltage types are range-specific** - prevents range mismatches
3. **Unsigned voltage types save 1 bit** - enables better packing in Phase 2
4. **Time types use user-friendly units** - ns/us/ms/sec instead of raw cycles
5. **Time types serialize to platform-specific cycles** - automatic conversion
6. **Explicit bit width selection** - forces conscious decision
7. **Global rounding strategy** - ROUND_UP, ROUND_DOWN, or EXACT
8. **No legacy type support** - new system supersedes old RegisterType

### 3. Conversion Formulas

**Voltage (±5V, 16-bit signed):**
```
raw = (millivolts / 5000.0) * 32767
millivolts = (raw / 32767.0) * 5000
```

**Time (platform-aware):**
```
cycles = duration_ns / clock_period_ns  (with rounding strategy)
duration_ns = cycles * clock_period_ns
```

### 4. Test Results

```
tests/test_basic_app_datatypes.py::test_type_registry_completeness PASSED
tests/test_basic_app_datatypes.py::test_bit_width_immutable PASSED
tests/test_basic_app_datatypes.py::test_voltage_output_05v_s16_conversion PASSED
tests/test_basic_app_datatypes.py::test_voltage_input_25v_s16_conversion PASSED
tests/test_basic_app_datatypes.py::test_pulse_duration_ns_construction PASSED
tests/test_basic_app_datatypes.py::test_pulse_duration_to_cycles_exact PASSED
tests/test_basic_app_datatypes.py::test_pulse_duration_to_cycles_rounding PASSED
tests/test_basic_app_datatypes.py::test_voltage_platform_compatibility PASSED
tests/test_basic_app_datatypes.py::test_time_platform_compatibility PASSED
tests/test_basic_app_datatypes.py::test_boolean_type PASSED

========== 10 passed in 0.42s ==========
Coverage: 98%
```

### 5. Files Created

- `models/custom_inst/basic_app_datatypes.py` (core implementation)
- `tests/test_basic_app_datatypes.py` (comprehensive tests)
- `docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md` (voltage spec)
- `docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md` (time spec)
- `docs/BasicAppDataTypes/BAD_Phase1_Implementation_Plan.md` (this plan)
- `docs/BasicAppDataTypes/BAD_Phase1_COMPLETE.md` (this summary)

### 6. Migration Example

**Before (old RegisterType):**
```yaml
- name: "Intensity"
  reg_type: counter_16bit  # Ambiguous: voltage? count? units?
  cr_number: 8
  default_value: 0x2666    # What does this hex value mean?
```

**After (BasicAppDataTypes):**
```yaml
- name: "Intensity"
  type: voltage_output_05v_s16  # Clear: output voltage, ±5V, signed 16-bit
  default_mv: 2400              # Clear: 2400 millivolts = 2.4V
```

## Unresolved Questions for Phase 2

None - Phase 1 design is complete and self-contained.

## Handoff to Phase 2: Register Mapping

**What Phase 2 needs from Phase 1:**
1. `TYPE_REGISTRY` with fixed bit widths for all types
2. Understanding that types are MSB-aligned when packed
3. Knowledge that unsigned types save 1 bit (U7/U15 vs S8/S16)
4. Awareness of platform-specific clock periods for time conversion

**Phase 2 Objectives:**
- Automatic register assignment (no more manual `cr_number`)
- Optimal bit packing (multiple values per 32-bit register)
- Collision detection (overlapping bit ranges)
- VHDL signal extraction code generation

**Next Phase Branch:**
```bash
git checkout feature/BAD-main
git checkout -b feature/BAD/P2
```
```

### Step 2: Update Phase 2 Header

Update `docs/BasicAppDataTypes/BAD_Phase2_RegisterMapping.md` header with:
```markdown
**Prerequisites:** Phase 1 complete ✓
**Phase 1 Summary:** [BAD_Phase1_COMPLETE.md](./BAD_Phase1_COMPLETE.md)
**Phase 1 Commit:** {git_hash_from_merge}
```

### Step 3: Final Git Workflow

```bash
# Verify all tests pass
uv run pytest tests/test_basic_app_datatypes.py -v

# Final commit
git add .
git commit -m "feat(BAD/P1): Complete Phase 1 - Core type system implementation

Implemented:
- BasicAppDataTypes enum (25 types: 12 voltage, 12 time, 1 boolean)
- TypeMetadata dataclass (frozen, immutable bit widths)
- TYPE_REGISTRY (complete metadata for all types)
- PulseDuration_* classes (user-friendly duration API)
- TypeConverter (voltage/time conversions)
- Comprehensive test suite (10 tests, 98% coverage)

Design docs:
- VOLTAGE_TYPE_SYSTEM.md (authoritative voltage spec)
- TIME_TYPE_SYSTEM.md (authoritative time spec)
- BAD_Phase1_Implementation_Plan.md (implementation guide)
- BAD_Phase1_COMPLETE.md (completion summary)

Ready for Phase 2: Register mapping and automatic bit packing.
"

# Merge back to feature branch
git checkout feature/BAD-main
git merge --no-ff feature/BAD/P1 -m "Merge Phase 1: Core type system implementation"

# Verify merge
git log --oneline --graph --decorate -10
```

---

## Design References

**Authoritative type specifications:**
- [VOLTAGE_TYPE_SYSTEM.md](./VOLTAGE_TYPE_SYSTEM.md)
- [TIME_TYPE_SYSTEM.md](./TIME_TYPE_SYSTEM.md)

**Platform specifications:**
- `moku-models/docs/MOKU_PLATFORM_SPECIFICATIONS.md`
- `moku-models/moku_models/platforms/*.py`

**Master orchestrator:**
- [BAD_MASTER_Orchestrator.md](./BAD_MASTER_Orchestrator.md)

---

## Getting Started

```bash
# Ensure you're on the correct branch
git branch --show-current  # Should show: feature/BAD/P1

# Create the implementation file
touch models/custom_inst/basic_app_datatypes.py

# Create the test file
touch tests/test_basic_app_datatypes.py

# Start implementing (follow tasks 1-6 above)
```

**Implementation order:**
1. Enum (Task 2)
2. TypeMetadata dataclass (Task 3)
3. TYPE_REGISTRY (Task 4)
4. Duration classes (Task 5)
5. TypeConverter (Task 6)
6. Tests (comprehensive coverage)

**Commit frequently** as you complete each task!

---

**Ready to implement?** Start with Task 1 and work through sequentially. Reference the type system docs for exact specifications. Good luck! 🎯
