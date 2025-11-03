# BAD Phase 1: Module Structure Design

**Document Type:** Supplementary Implementation Guidance
**Related:** [BAD_Phase1_Implementation_Plan.md](./BAD_Phase1_Implementation_Plan.md)
**Status:** Design Finalized
**Date:** 2025-01-28

---

## Purpose

This document specifies the **modular file structure** for the BasicAppDataTypes implementation. It complements the implementation plan by defining exactly where code should be placed and how imports should be organized.

**Primary implementation guide:** [BAD_Phase1_Implementation_Plan.md](./BAD_Phase1_Implementation_Plan.md)

---

## Module Structure Decision: Option A (Modular)

After analyzing the codebase and import patterns, we chose a **modular approach** over a single-file implementation.

**Rationale:**
- ✅ Clean separation of concerns (types, metadata, converters)
- ✅ Easier to navigate and maintain (~300 lines per file vs 1500+ in one file)
- ✅ Testable components (can test voltage/time conversions independently)
- ✅ Scalable (easy to add new type categories in future phases)
- ✅ Follows Python best practices (one module per logical component)

---

## File Structure

### Directory Layout

```
models/custom_inst/
├── __init__.py                    # PUBLIC API (updated with new exports)
├── app_register.py                # OLD: RegisterType, AppRegister (legacy, keep for now)
├── custom_inst_app.py             # CustomInstApp (will use new types in Phase 2+)
│
├── datatypes/                     # NEW: BasicAppDataTypes module
│   ├── __init__.py               # Public API for datatypes
│   ├── types.py                  # BasicAppDataTypes enum (25 types)
│   ├── metadata.py               # TypeMetadata + TYPE_REGISTRY (25 entries)
│   ├── voltage.py                # Voltage-specific utilities (if needed)
│   ├── time.py                   # PulseDuration_* classes (4 classes)
│   └── converters.py             # TypeConverter class (all conversions)
│
└── tests/
    └── test_basic_app_datatypes.py  # Comprehensive test suite
```

---

## File Responsibilities

### `models/custom_inst/datatypes/__init__.py`

**Purpose:** Public API for BasicAppDataTypes module
**Size:** ~60 lines
**Exports:** All public classes and enums

```python
"""
BasicAppDataTypes - Type-safe data serialization for Moku FPGA applications.

Provides fixed-width types with platform-aware serialization:
- Voltage types (INPUT/OUTPUT, range-specific)
- Time/duration types (user-friendly units → clock cycles)
- Boolean type

Design Documentation:
- Voltage specs: docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md
- Time specs: docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md
- Implementation: docs/BasicAppDataTypes/BAD_Phase1_Implementation_Plan.md

Example:
    >>> from models.custom_inst.datatypes import PulseDuration_ns, BasicAppDataTypes
    >>>
    >>> # User-friendly API
    >>> firing_duration = PulseDuration_ns(500, width=16)
    >>>
    >>> # Get type enum
    >>> type_enum = firing_duration.to_basic_type()
    >>> # Returns: BasicAppDataTypes.PULSE_DURATION_NS_U16
    >>>
    >>> # Convert to platform-specific cycles
    >>> cycles = firing_duration.to_cycles(
    ...     clock_period_ns=8.0,  # Moku:Go @ 125 MHz
    ...     rounding='ROUND_UP'
    ... )
    >>> # Returns: 63 cycles (500ns / 8ns = 62.5 → 63)
"""

# Core types and metadata
from .types import BasicAppDataTypes
from .metadata import TypeMetadata, TYPE_REGISTRY

# User-friendly duration classes
from .time import (
    PulseDuration_ns,
    PulseDuration_us,
    PulseDuration_ms,
    PulseDuration_sec,
)

# Conversion utilities
from .converters import TypeConverter

__all__ = [
    # Enums and metadata
    'BasicAppDataTypes',
    'TypeMetadata',
    'TYPE_REGISTRY',

    # Duration classes
    'PulseDuration_ns',
    'PulseDuration_us',
    'PulseDuration_ms',
    'PulseDuration_sec',

    # Converters
    'TypeConverter',
]

__version__ = '1.0.0'
```

---

### `models/custom_inst/datatypes/types.py`

**Purpose:** BasicAppDataTypes enum definitions ONLY
**Size:** ~100 lines
**Dependencies:** None (just Python stdlib)
**Reference:** [VOLTAGE_TYPE_SYSTEM.md](./VOLTAGE_TYPE_SYSTEM.md), [TIME_TYPE_SYSTEM.md](./TIME_TYPE_SYSTEM.md)

**Implementation Task:** Task 2 from [BAD_Phase1_Implementation_Plan.md](./BAD_Phase1_Implementation_Plan.md#task-2-implement-basicappdatatypes-enum)

```python
"""
BasicAppDataTypes enum definitions.

This module contains ONLY the type enum definitions.
For metadata and conversions, see metadata.py and converters.py.

Design References:
- Voltage types: docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md
- Time types: docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md
"""

from enum import Enum


class BasicAppDataTypes(str, Enum):
    """
    Fixed-width data types for BasicAppDataTypes system.

    Design principles:
    - Fixed, immutable bit widths
    - Platform-agnostic definitions
    - Self-documenting type names
    - No endianness (MSB-aligned packing)

    Total types: 25 (12 voltage + 12 time + 1 boolean)
    """

    # ========================================================================
    # VOLTAGE TYPES (12 total)
    # See: docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md
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
    # TIME TYPES (12 total)
    # See: docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md
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
    # BOOLEAN TYPE (1 total)
    # ========================================================================

    BOOLEAN = "boolean"  # 1-bit, True/False
```

---

### `models/custom_inst/datatypes/metadata.py`

**Purpose:** TypeMetadata dataclass and TYPE_REGISTRY
**Size:** ~400 lines
**Dependencies:** `types.py`
**Reference:** [BAD_Phase1_Implementation_Plan.md](./BAD_Phase1_Implementation_Plan.md#task-3-implement-typemetadata-dataclass)

**Implementation Tasks:**
- Task 3: Implement TypeMetadata dataclass
- Task 4: Implement TYPE_REGISTRY

```python
"""
Type metadata and registry for BasicAppDataTypes.

This module defines the metadata structure for all types and provides
the central TYPE_REGISTRY dictionary.

Design References:
- Voltage specs: docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md
- Time specs: docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md
"""

from dataclasses import dataclass
from typing import Optional, Union, Literal
from .types import BasicAppDataTypes


@dataclass(frozen=True)  # Immutable for safety
class TypeMetadata:
    """
    Metadata specification for a BasicAppDataType.

    The frozen=True ensures bit_width is immutable, which is critical
    for Phase 2 register packing (bit widths must be known a priori).

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


# ============================================================================
# TYPE_REGISTRY - Central metadata for all 25 types
# ============================================================================

TYPE_REGISTRY: dict[BasicAppDataTypes, TypeMetadata] = {
    # ========================================================================
    # VOLTAGE OUTPUT TYPES (±5V, all platforms)
    # See: VOLTAGE_TYPE_SYSTEM.md
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
    # ... (continue for all 25 types)

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

---

### `models/custom_inst/datatypes/time.py`

**Purpose:** User-friendly PulseDuration_* classes
**Size:** ~400 lines
**Dependencies:** `types.py`, `math`
**Reference:** [TIME_TYPE_SYSTEM.md](./TIME_TYPE_SYSTEM.md)

**Implementation Task:** Task 5 from [BAD_Phase1_Implementation_Plan.md](./BAD_Phase1_Implementation_Plan.md#task-5-implement-user-friendly-duration-classes)

```python
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
        63  # 500ns / 8ns = 62.5 → 63 (rounded up)
    """

    def __init__(self, nanoseconds: int, width: Literal[8, 16, 32] = 16):
        # ... implementation from plan
        pass

    def to_basic_type(self) -> BasicAppDataTypes:
        # ... implementation from plan
        pass

    def to_nanoseconds(self) -> int:
        # ... implementation from plan
        pass

    def to_cycles(self, clock_period_ns: float,
                   rounding: Literal['ROUND_UP', 'ROUND_DOWN', 'EXACT']) -> int:
        # ... implementation from plan
        pass


class PulseDuration_us:
    """Microsecond-based time duration."""
    # Similar structure to PulseDuration_ns
    pass


class PulseDuration_ms:
    """Millisecond-based time duration."""
    # Similar structure to PulseDuration_ns
    pass


class PulseDuration_sec:
    """Second-based time duration."""
    # Similar structure to PulseDuration_ns
    pass
```

---

### `models/custom_inst/datatypes/voltage.py`

**Purpose:** Voltage-specific utilities (if needed)
**Size:** ~50 lines (minimal, most logic in converters.py)
**Dependencies:** None
**Reference:** [VOLTAGE_TYPE_SYSTEM.md](./VOLTAGE_TYPE_SYSTEM.md)

**Note:** This file may be mostly empty initially. It's reserved for voltage-specific helpers that don't fit in converters.py (e.g., voltage range validation, platform compatibility checks).

```python
"""
Voltage-specific utilities for BasicAppDataTypes.

This module is reserved for voltage-specific helper functions
that don't belong in the general TypeConverter class.

Design Reference: docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md
"""

# Currently minimal - most voltage logic is in converters.py
# Reserved for future voltage-specific utilities
```

---

### `models/custom_inst/datatypes/converters.py`

**Purpose:** TypeConverter class (all conversion logic)
**Size:** ~400 lines
**Dependencies:** `math`, `types.py`
**Reference:** [BAD_Phase1_Implementation_Plan.md](./BAD_Phase1_Implementation_Plan.md#task-6-implement-typeconverter-class)

**Implementation Task:** Task 6 from implementation plan

```python
"""
Conversion utilities for BasicAppDataTypes.

Handles bidirectional conversion between user-friendly units
(millivolts, nanoseconds) and raw binary values for serialization.

Design References:
- Voltage conversions: docs/BasicAppDataTypes/VOLTAGE_TYPE_SYSTEM.md
- Time conversions: docs/BasicAppDataTypes/TIME_TYPE_SYSTEM.md
"""

import math
from typing import Literal


class TypeConverter:
    """
    Conversion utilities for BasicAppDataTypes.

    Provides static methods for converting between user-friendly units
    and raw binary values suitable for FPGA register serialization.

    All voltage conversions work in millivolts (mV).
    All time conversions work in platform-specific clock cycles.
    """

    # ========================================================================
    # VOLTAGE CONVERSIONS (12 types × 2 directions = 24 methods)
    # ========================================================================

    @staticmethod
    def voltage_output_05v_s8_to_raw(millivolts: int) -> int:
        """
        Convert millivolts to 8-bit signed raw value (±5V range).

        Formula: raw = (mV / 5000.0) * 127
        Range: -5000 to +5000 mV → -128 to +127
        """
        # ... implementation from plan
        pass

    @staticmethod
    def raw_to_voltage_output_05v_s8(raw: int) -> int:
        """Convert 8-bit signed raw to millivolts (±5V range)."""
        # ... implementation from plan
        pass

    # ... (continue for all 12 voltage types)

    # ========================================================================
    # TIME CONVERSIONS (platform-aware)
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
        """
        # ... implementation from plan
        pass

    @staticmethod
    def cycles_to_time(
        cycles: int,
        unit: Literal['ns', 'us', 'ms', 's'],
        clock_period_ns: float
    ) -> int:
        """Convert clock cycles to time value (platform-aware)."""
        # ... implementation from plan
        pass
```

---

## Updated Parent Module

### `models/custom_inst/__init__.py` (UPDATED)

Add new exports to the existing public API:

```python
"""
CustomInstApp - Hardware Abstraction Layer for FPGA Applications

... (existing docstring) ...
"""

# Existing imports
from .app_register import AppRegister, RegisterType
from .custom_inst_app import CustomInstApp

# NEW: BasicAppDataTypes system
from .datatypes import (
    BasicAppDataTypes,
    TypeMetadata,
    TYPE_REGISTRY,
    PulseDuration_ns,
    PulseDuration_us,
    PulseDuration_ms,
    PulseDuration_sec,
    TypeConverter,
)

__all__ = [
    # Existing (legacy)
    'CustomInstApp',
    'AppRegister',
    'RegisterType',  # OLD - will be deprecated eventually

    # NEW: BasicAppDataTypes
    'BasicAppDataTypes',
    'TypeMetadata',
    'TYPE_REGISTRY',
    'PulseDuration_ns',
    'PulseDuration_us',
    'PulseDuration_ms',
    'PulseDuration_sec',
    'TypeConverter',
]

__version__ = '1.0.0'
```

---

## Import Patterns for Different Use Cases

### TUI Application Developer (e.g., DS1140-PD)

```python
from models.custom_inst.datatypes import PulseDuration_ns, PulseDuration_ms

# User-friendly API
probe_config = {
    'firing_duration': PulseDuration_ns(500, width=16),
    'cooling_duration': PulseDuration_ms(100, width=16),
}
```

### YAML Parser / Code Generator

```python
from models.custom_inst.datatypes import (
    BasicAppDataTypes,
    TYPE_REGISTRY,
    TypeConverter,
)

# Get type metadata
type_enum = BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
metadata = TYPE_REGISTRY[type_enum]
print(f"Bit width: {metadata.bit_width}")  # 16
print(f"VHDL type: {metadata.vhdl_type}")  # signed(15 downto 0)

# Convert voltage
raw_value = TypeConverter.voltage_output_05v_s16_to_raw(2400)  # 2.4V
```

### Test Code

```python
from models.custom_inst.datatypes import (
    BasicAppDataTypes,
    TYPE_REGISTRY,
    PulseDuration_ns,
    TypeConverter,
)

def test_voltage_conversion():
    raw = TypeConverter.voltage_output_05v_s16_to_raw(2400)
    recovered = TypeConverter.raw_to_voltage_output_05v_s16(raw)
    assert abs(recovered - 2400) <= 10  # Allow rounding error

def test_time_conversion():
    duration = PulseDuration_ns(500, width=16)
    cycles = duration.to_cycles(clock_period_ns=8.0, rounding='ROUND_UP')
    assert cycles == 63  # 500ns / 8ns = 62.5 → 63
```

### Convenience Import (Everything)

```python
# Import everything at once
from models.custom_inst.datatypes import *

# Now have access to:
# - BasicAppDataTypes
# - TypeMetadata
# - TYPE_REGISTRY
# - PulseDuration_ns, PulseDuration_us, PulseDuration_ms, PulseDuration_sec
# - TypeConverter
```

---

## Implementation Order

Follow this sequence when implementing:

1. **Create directory structure**
   ```bash
   mkdir -p models/custom_inst/datatypes
   touch models/custom_inst/datatypes/__init__.py
   touch models/custom_inst/datatypes/types.py
   touch models/custom_inst/datatypes/metadata.py
   touch models/custom_inst/datatypes/voltage.py
   touch models/custom_inst/datatypes/time.py
   touch models/custom_inst/datatypes/converters.py
   ```

2. **Implement files in order:**
   - `types.py` (no dependencies)
   - `metadata.py` (depends on types.py)
   - `time.py` (depends on types.py)
   - `voltage.py` (optional, minimal)
   - `converters.py` (depends on types.py)
   - `datatypes/__init__.py` (imports from all above)

3. **Update parent module:**
   - `models/custom_inst/__init__.py` (add new exports)

4. **Write tests:**
   - `tests/test_basic_app_datatypes.py` (comprehensive suite)

---

## File Size Estimates

| File | Estimated Lines | Purpose |
|------|----------------|---------|
| `types.py` | ~100 | Enum definitions only |
| `metadata.py` | ~400 | TypeMetadata + TYPE_REGISTRY (25 entries) |
| `time.py` | ~400 | 4 PulseDuration classes |
| `voltage.py` | ~50 | Minimal (reserved for future) |
| `converters.py` | ~400 | TypeConverter (24+ methods) |
| `datatypes/__init__.py` | ~60 | Public API exports |
| **Total** | **~1,410 lines** | vs ~1,500 in single file |

**Benefits of modular approach:**
- Easier to navigate (~300 lines per file vs 1500)
- Can edit one concern without touching others
- Tests can import specific modules
- Git diffs are cleaner

---

## Testing Strategy

Tests should import from specific modules when testing individual components:

```python
# Test types module independently
from models.custom_inst.datatypes.types import BasicAppDataTypes

# Test metadata module independently
from models.custom_inst.datatypes.metadata import TypeMetadata, TYPE_REGISTRY

# Test time module independently
from models.custom_inst.datatypes.time import PulseDuration_ns

# Test converters module independently
from models.custom_inst.datatypes.converters import TypeConverter

# Or test full public API
from models.custom_inst.datatypes import *
```

---

## Migration Path

### Phase 1 (Current)
- ✅ New `datatypes/` module created alongside old `app_register.py`
- ✅ Both old and new types coexist
- ✅ No breaking changes

### Phase 2 (Register Mapping)
- `CustomInstApp` starts using new `BasicAppDataTypes`
- Old `RegisterType` still available but deprecated

### Phase 3+ (Future)
- Old `RegisterType` eventually removed
- All code uses `BasicAppDataTypes`

---

## References

**Primary implementation guide:**
- [BAD_Phase1_Implementation_Plan.md](./BAD_Phase1_Implementation_Plan.md) - Tasks, testing, completion criteria

**Design specifications:**
- [VOLTAGE_TYPE_SYSTEM.md](./VOLTAGE_TYPE_SYSTEM.md) - Voltage type taxonomy
- [TIME_TYPE_SYSTEM.md](./TIME_TYPE_SYSTEM.md) - Time type taxonomy

**Platform specifications:**
- `moku-models/docs/MOKU_PLATFORM_SPECIFICATIONS.md` - Hardware constraints

---

## Quick Start Checklist

When implementing, follow this checklist:

- [ ] Create `models/custom_inst/datatypes/` directory
- [ ] Implement `types.py` (enum definitions)
- [ ] Implement `metadata.py` (TypeMetadata + TYPE_REGISTRY)
- [ ] Implement `time.py` (PulseDuration_* classes)
- [ ] Implement `voltage.py` (minimal/reserved)
- [ ] Implement `converters.py` (TypeConverter class)
- [ ] Implement `datatypes/__init__.py` (public API)
- [ ] Update `models/custom_inst/__init__.py` (add exports)
- [ ] Write `tests/test_basic_app_datatypes.py`
- [ ] Verify all imports work
- [ ] Run tests
- [ ] Commit to git

---

**Last Updated:** 2025-01-28
**Status:** Ready for implementation
**Related Documents:** [BAD_Phase1_Implementation_Plan.md](./BAD_Phase1_Implementation_Plan.md)
