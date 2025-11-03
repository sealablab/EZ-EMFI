# BasicAppDataTypes Time Type System

**Status:** Design Finalized
**Date:** 2025-01-28
**Phase:** BAD Phase 1 - Core Type System Implementation

---

## Overview

The BasicAppDataTypes time type system provides **user-friendly duration types** with **platform-aware clock cycle serialization** for precise timing control across all Moku platforms.

**Core Design Principles:**
1. **User-Friendly API**: Application developers specify durations in intuitive units (ns, µs, ms, seconds)
2. **Platform-Aware Serialization**: Types automatically convert to clock cycles based on target platform
3. **Explicit Bit Widths**: Developers must choose bit width (forces conscious decision)
4. **Configurable Rounding**: Global rounding strategy (`ROUND_UP`, `ROUND_DOWN`, `EXACT`)
5. **Fixed Width**: All types have immutable bit widths known a priori

---

## Two-Layer Architecture

### Layer 1: User-Friendly Python API

Application developers work with intuitive duration classes:

```python
from models.custom_inst.basic_app_datatypes import (
    PulseDuration_ns,   # Nanosecond-based durations
    PulseDuration_us,   # Microsecond-based durations
    PulseDuration_ms,   # Millisecond-based durations
    PulseDuration_sec,  # Second-based durations
)

# Application code (e.g., DS1140-PD TUI)
probe_config = {
    'firing_duration': PulseDuration_ns(500),      # 500ns pulse
    'cooling_duration': PulseDuration_ms(100),     # 100ms cooling
    'arm_timeout': PulseDuration_ms(1000),         # 1 second timeout
}
```

### Layer 2: Platform-Aware Serialization

At VHDL generation time, durations are converted to **clock cycles** based on target platform:

```python
# Serialization for Moku:Go (125 MHz, 8ns clock period)
firing_duration = PulseDuration_ns(500)
cycles = 500ns / 8ns = 62.5 → 63 cycles (ROUND_UP)
vhdl_value = 63  # unsigned(7 downto 0)

# Serialization for Moku:Delta (5 GHz, 0.2ns clock period)
firing_duration = PulseDuration_ns(500)
cycles = 500ns / 0.2ns = 2500 cycles
vhdl_value = 2500  # unsigned(15 downto 0)
```

---

## Platform Clock Specifications

### Clock Rates (from moku-models)

| Platform | Clock Frequency | Clock Period |
|----------|----------------|--------------|
| Moku:Go  | 125 MHz        | 8.0 ns       |
| Moku:Lab | 500 MHz        | 2.0 ns       |
| Moku:Pro | 1.25 GHz       | 0.8 ns       |
| Moku:Delta | 5 GHz        | 0.2 ns       |

**Note**: VHDL designs also have access to clock dividers (÷1 to ÷16), enabling longer durations with fewer bits. This is handled at VHDL generation time, not in the type system.

---

## Time Type Taxonomy

### Naming Convention

```
PULSE_DURATION_{UNIT}_{SIGNEDNESS}{BITS}
```

**Components:**
- `UNIT`: `NS` (nanoseconds), `US` (microseconds), `MS` (milliseconds), `S` (seconds)
- `SIGNEDNESS`: `U` (unsigned only - negative time is meaningless)
- `BITS`: `8`, `16`, `24`, `32`

**Examples:**
- `PULSE_DURATION_NS_U16` → Nanoseconds, unsigned 16-bit, 0-65,535 ns
- `PULSE_DURATION_MS_U8` → Milliseconds, unsigned 8-bit, 0-255 ms

---

## Type Definitions

### Nanosecond-Based Durations

```python
PULSE_DURATION_NS_U8 = "pulse_duration_ns_u8"      # 8-bit, 0-255 ns
PULSE_DURATION_NS_U16 = "pulse_duration_ns_u16"    # 16-bit, 0-65,535 ns (~65 µs)
PULSE_DURATION_NS_U32 = "pulse_duration_ns_u32"    # 32-bit, 0-4,294,967,295 ns (~4.29 sec)
```

**Use Cases:**
- Sub-microsecond pulse widths (EMFI glitch timing)
- High-precision timing on fast platforms (Delta @ 5 GHz)
- Short gate/enable signals

---

### Microsecond-Based Durations

```python
PULSE_DURATION_US_U8 = "pulse_duration_us_u8"      # 8-bit, 0-255 µs
PULSE_DURATION_US_U16 = "pulse_duration_us_u16"    # 16-bit, 0-65,535 µs (~65 ms)
PULSE_DURATION_US_U24 = "pulse_duration_us_u24"    # 24-bit, 0-16,777,215 µs (~16.7 sec)
```

**Use Cases:**
- Typical EMFI pulse widths (10-100 µs range)
- Medium-duration timing (settling times, delays)
- Trigger window timeouts

---

### Millisecond-Based Durations

```python
PULSE_DURATION_MS_U8 = "pulse_duration_ms_u8"      # 8-bit, 0-255 ms
PULSE_DURATION_MS_U16 = "pulse_duration_ms_u16"    # 16-bit, 0-65,535 ms (~65 sec)
```

**Use Cases:**
- Cooling periods (thermal management)
- Long timeouts (arm timeout, trigger wait)
- Human-scale delays

---

### Second-Based Durations

```python
PULSE_DURATION_S_U8 = "pulse_duration_s_u8"        # 8-bit, 0-255 seconds (~4 min)
PULSE_DURATION_S_U16 = "pulse_duration_s_u16"      # 16-bit, 0-65,535 seconds (~18 hours)
```

**Use Cases:**
- Very long timeouts
- Test campaign durations
- Thermal recovery periods

---

## Duration Range Tables

### Maximum Representable Durations by Type

| Type                    | Bits | Max Value (Native) | Max Value (Converted)    |
|-------------------------|------|-------------------|--------------------------|
| PULSE_DURATION_NS_U8    | 8    | 255 ns            | 255 ns                   |
| PULSE_DURATION_NS_U16   | 16   | 65,535 ns         | ~65.5 µs                 |
| PULSE_DURATION_NS_U32   | 32   | 4,294,967,295 ns  | ~4.29 seconds            |
| PULSE_DURATION_US_U8    | 8    | 255 µs            | 255 µs                   |
| PULSE_DURATION_US_U16   | 16   | 65,535 µs         | ~65.5 ms                 |
| PULSE_DURATION_US_U24   | 24   | 16,777,215 µs     | ~16.7 seconds            |
| PULSE_DURATION_MS_U8    | 8    | 255 ms            | 255 ms                   |
| PULSE_DURATION_MS_U16   | 16   | 65,535 ms         | ~65.5 seconds (~1 min)   |
| PULSE_DURATION_S_U8     | 8    | 255 s             | ~4.25 minutes            |
| PULSE_DURATION_S_U16    | 16   | 65,535 s          | ~18.2 hours              |

---

### Clock Cycles by Platform (Example: 1 µs duration)

| Platform | Clock Period | Cycles for 1 µs |
|----------|-------------|-----------------|
| Go       | 8.0 ns      | 125 cycles      |
| Lab      | 2.0 ns      | 500 cycles      |
| Pro      | 0.8 ns      | 1,250 cycles    |
| Delta    | 0.2 ns      | 5,000 cycles    |

**Key Insight**: Same duration requires different cycle counts on different platforms. The type system handles this automatically during serialization.

---

## Rounding Strategy

### The Rounding Problem

Not all durations are evenly divisible by all clock periods:

```python
# Example: 500ns on Moku:Go (8ns clock period)
desired_ns = 500
clock_period_ns = 8.0

exact_cycles = 500 / 8.0 = 62.5 cycles  # Not an integer!

# What should we do?
```

### Rounding Modes (Global Configuration)

#### `ROUND_UP` (Conservative, guarantees minimum duration)

```python
cycles = math.ceil(62.5) = 63 cycles
actual_ns = 63 × 8.0 = 504 ns  # 4ns longer than requested
```

**Use when**: Duration must be **at least** the specified value (e.g., minimum cooling time)

---

#### `ROUND_DOWN` (Conservative, guarantees maximum duration)

```python
cycles = math.floor(62.5) = 62 cycles
actual_ns = 62 × 8.0 = 496 ns  # 4ns shorter than requested
```

**Use when**: Duration must be **at most** the specified value (e.g., maximum pulse width)

---

#### `EXACT` (Strict, requires perfect divisibility)

```python
if exact_cycles != int(exact_cycles):
    raise ValueError(
        "Duration 500ns not evenly divisible by clock period 8ns. "
        "Use ROUND_UP or ROUND_DOWN."
    )
```

**Use when**: Precision is critical and rounding is unacceptable

---

### Rounding Configuration

**Global setting** (applies to all time type conversions):

```python
# In application config or YAML
global_rounding_mode = 'ROUND_UP'  # or 'ROUND_DOWN', 'EXACT'
```

**Not per-register** (simpler, more consistent behavior across application).

---

## Python API Design

### User-Facing Duration Classes

```python
class PulseDuration_ns:
    """Nanosecond-based time duration."""

    def __init__(self, nanoseconds: int, width: Literal[8, 16, 32] = 16):
        """
        Create a nanosecond duration.

        Args:
            nanoseconds: Duration in nanoseconds
            width: Bit width for serialization (8, 16, or 32)

        Raises:
            ValueError: If nanoseconds exceeds max for chosen width
        """
        self.value = nanoseconds
        self.unit = 'ns'
        self.width = width

        # Validate range
        max_value = (2 ** width) - 1
        if nanoseconds > max_value:
            raise ValueError(
                f"{nanoseconds}ns exceeds max for U{width} ({max_value}ns)"
            )
        if nanoseconds < 0:
            raise ValueError("Duration cannot be negative")

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

    def to_cycles(self, platform: MokuPlatform,
                   rounding: Literal['ROUND_UP', 'ROUND_DOWN', 'EXACT']) -> int:
        """Convert to clock cycles for target platform."""
        exact_cycles = self.value / platform.clock_period_ns

        if rounding == 'EXACT':
            if exact_cycles != int(exact_cycles):
                raise ValueError(
                    f"{self.value}ns not evenly divisible by "
                    f"clock period {platform.clock_period_ns}ns"
                )
            return int(exact_cycles)
        elif rounding == 'ROUND_UP':
            return math.ceil(exact_cycles)
        elif rounding == 'ROUND_DOWN':
            return math.floor(exact_cycles)
        else:
            raise ValueError(f"Invalid rounding mode: {rounding}")

# Similar implementations for:
# - PulseDuration_us (microseconds)
# - PulseDuration_ms (milliseconds)
# - PulseDuration_sec (seconds)
```

---

## VHDL Type Mappings

### Unsigned Types (All Time Types)

```vhdl
-- U8: 8-bit unsigned
signal duration : unsigned(7 downto 0);

-- U16: 16-bit unsigned
signal duration : unsigned(15 downto 0);

-- U24: 24-bit unsigned
signal duration : unsigned(23 downto 0);

-- U32: 32-bit unsigned
signal duration : unsigned(31 downto 0);
```

**Note**: Time is always unsigned (negative durations are meaningless).

---

### MSB-Aligned Packing (32-bit Control Registers)

**Example: U8 type in Control Register**
```vhdl
-- Extract unsigned 8-bit duration from upper 8 bits of CR
signal firing_duration : unsigned(7 downto 0);
firing_duration <= unsigned(control_reg_5(31 downto 24));
```

**Example: U16 type in Control Register**
```vhdl
-- Extract unsigned 16-bit duration from upper 16 bits of CR
signal cooling_duration : unsigned(15 downto 0);
cooling_duration <= unsigned(control_reg_6(31 downto 16));
```

**Example: U24 type in Control Register**
```vhdl
-- Extract unsigned 24-bit duration from upper 24 bits of CR
signal arm_timeout : unsigned(23 downto 0);
arm_timeout <= unsigned(control_reg_4(31 downto 8));
```

---

## Usage Examples

### Example 1: DS1140-PD EMFI Probe (YAML)

```yaml
# DS1140-PD VoloApp Definition
registers:
  # Short pulse (nanosecond precision)
  - name: "Firing Duration"
    description: "Number of cycles to remain in FIRING state"
    type: pulse_duration_ns_u8       # 8-bit, 0-255 ns
    default_ns: 128                  # 128ns pulse

  # Medium duration (millisecond precision)
  - name: "Cooling Duration"
    description: "Thermal recovery period"
    type: pulse_duration_ms_u16      # 16-bit, 0-65,535 ms
    default_ms: 100                  # 100ms cooling

  # Long timeout (millisecond precision)
  - name: "Arm Timeout"
    description: "Max time to wait for trigger"
    type: pulse_duration_ms_u16      # 16-bit, 0-65,535 ms
    default_ms: 1000                 # 1 second timeout
```

---

### Example 2: Python Application Code

```python
from models.custom_inst.basic_app_datatypes import (
    PulseDuration_ns,
    PulseDuration_ms,
)

# User-friendly API
probe_config = {
    'firing_duration': PulseDuration_ns(128, width=8),     # 128ns, 8-bit
    'cooling_duration': PulseDuration_ms(100, width=16),   # 100ms, 16-bit
    'arm_timeout': PulseDuration_ms(1000, width=16),       # 1s, 16-bit
}

# Validation happens at construction time
try:
    bad_duration = PulseDuration_ns(500, width=8)  # ERROR: 500 > 255 (max for U8)
except ValueError as e:
    print(f"Invalid duration: {e}")
```

---

### Example 3: VHDL Generation (Moku:Go @ 125 MHz)

```python
from moku_models import MOKU_GO_PLATFORM

platform = MOKU_GO_PLATFORM  # 125 MHz, 8ns clock period
rounding = 'ROUND_UP'

# Convert durations to clock cycles
firing_ns = PulseDuration_ns(128, width=8)
firing_cycles = firing_ns.to_cycles(platform, rounding)
# 128ns / 8ns = 16 cycles (exact)

cooling_ms = PulseDuration_ms(100, width=16)
cooling_cycles = cooling_ms.to_cycles(platform, rounding)
# 100ms = 100,000,000ns / 8ns = 12,500,000 cycles

# Generated VHDL
"""
-- Firing duration (8-bit, 16 cycles)
constant FIRING_DURATION : unsigned(7 downto 0) := to_unsigned(16, 8);

-- Cooling duration (16-bit would overflow! Need 24-bit)
-- ERROR: 12,500,000 cycles exceeds U16 max (65,535)
-- Solution: Use clock divider or larger bit width
"""
```

**Key Insight**: High clock rates (Delta @ 5 GHz) produce large cycle counts. Must choose appropriate bit width or use VHDL clock dividers.

---

## Clock Divider Integration (VHDL Side)

All VHDL designs have access to clock dividers (÷1 to ÷16):

```vhdl
-- Clock divider control (from Control Register)
signal clk_divider : unsigned(3 downto 0);  -- 0-15 (÷1 to ÷16)
signal divided_clk : std_logic;

-- Example: 100ms timeout on Moku:Go (125 MHz)
-- Option A: Full-speed clock (125 MHz)
--   100ms = 12,500,000 cycles (needs 24 bits)
--
-- Option B: Divided clock (125 MHz ÷ 16 = 7.8125 MHz)
--   100ms = 781,250 cycles (needs 20 bits)

-- Divider selection handled by VHDL code generator
-- based on required duration and available bit width
```

**Type system doesn't handle divider selection** - that's VHDL generation logic.

---

## Type Metadata Structure

```python
@dataclass(frozen=True)  # Immutable for safety
class TypeMetadata:
    type_name: BasicAppDataTypes
    bit_width: int                    # Fixed width (8, 16, 24, or 32)
    vhdl_type: str                    # "unsigned(15 downto 0)"
    python_type: type                 # int
    min_value: int                    # Minimum value in base unit (0)
    max_value: int                    # Maximum value in base unit
    default_value: int                # Default value (0)
    unit: str                         # 'ns', 'us', 'ms', 's'
    base_unit: str                    # 'nanoseconds', 'microseconds', etc.

# Example: PULSE_DURATION_NS_U16
TYPE_REGISTRY[BasicAppDataTypes.PULSE_DURATION_NS_U16] = TypeMetadata(
    type_name=BasicAppDataTypes.PULSE_DURATION_NS_U16,
    bit_width=16,
    vhdl_type="unsigned(15 downto 0)",
    python_type=int,
    min_value=0,
    max_value=65535,  # nanoseconds
    default_value=0,
    unit='ns',
    base_unit='nanoseconds'
)
```

---

## Design Rationale

### Why User-Friendly Units (ns, µs, ms)?

**Self-Documenting Code:**
```python
# GOOD: Clear intent
firing_duration = PulseDuration_ns(500)  # 500 nanoseconds

# BAD: What unit is this?
firing_duration = 500  # cycles? nanoseconds? microseconds?
```

**Platform Independence:**
```yaml
# Same YAML config works on all platforms
- name: "Firing Duration"
  type: pulse_duration_ns_u16
  default_ns: 500  # 500ns on ALL platforms (Go/Lab/Pro/Delta)
```

---

### Why Explicit Bit Widths?

**Forces Conscious Decision:**
- Developer must think about value range and register packing
- Prevents accidental oversized types (wasting register space)
- Enables Phase 2 register packing optimization

**Example:**
```python
# GOOD: Developer chose appropriate width
short_pulse = PulseDuration_ns(128, width=8)  # 0-255ns is sufficient

# BAD: Wasteful (could use U8 instead of U16)
short_pulse = PulseDuration_ns(128, width=16)  # Wastes 8 bits
```

---

### Why No Signed Time Types?

**Negative durations are physically meaningless:**
- Time always moves forward
- Pulse widths are always positive
- Delays/timeouts are always positive

**Unsigned saves 1 bit** (same as voltage U7/U15 types).

---

### Why Platform-Aware Serialization?

**Prevents Clock Rate Mismatches:**
```python
# YAML specifies duration in nanoseconds (platform-agnostic)
default_ns: 500

# VHDL generator converts to cycles (platform-specific)
# Moku:Go:   500ns / 8.0ns   = 63 cycles
# Moku:Delta: 500ns / 0.2ns = 2500 cycles
```

**Same config works across all platforms** - no manual cycle calculation needed.

---

## Design Constraints

### Must Have
- ✅ Fixed, immutable bit widths (8, 16, 24, 32)
- ✅ No endianness (just bit positions)
- ✅ MSB-aligned extraction
- ✅ Unsigned only (no negative time)
- ✅ User-friendly units (ns, µs, ms, s)
- ✅ Explicit bit width selection

### Must Support
- ✅ Platform-agnostic YAML configs
- ✅ Platform-aware clock cycle conversion
- ✅ Configurable rounding (ROUND_UP, ROUND_DOWN, EXACT)
- ✅ Range validation (duration fits in chosen bit width)
- ✅ Clear error messages for invalid durations

### Out of Scope (Phase 1)
- ❌ Automatic bit width selection (must be explicit)
- ❌ Clock divider selection (handled by VHDL generator)
- ❌ Per-register rounding modes (global only)
- ❌ Fractional nanosecond precision

---

## References

- **Platform specs**: `moku-models/docs/MOKU_PLATFORM_SPECIFICATIONS.md`
- **Platform models**: `moku-models/moku_models/platforms/*.py`
- **Phase 1 prompt**: `docs/BasicAppDataTypes/BAD_Phase1_TypeSystem.md`
- **Voltage type system**: `docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md`
- **Historical DS1140-PD YAML**: `DS1140_PD_app.yaml`

---

## Version History

- **2025-01-28**: Initial design finalized
  - Established user-friendly duration classes (PulseDuration_ns, etc.)
  - Defined explicit bit width selection (U8, U16, U24, U32)
  - Implemented platform-aware clock cycle conversion
  - Added global rounding strategy (ROUND_UP, ROUND_DOWN, EXACT)
  - Included 24-bit types for extended ranges

---

**Next Steps**: Implement Boolean and legacy types, then proceed to Phase 1 implementation
