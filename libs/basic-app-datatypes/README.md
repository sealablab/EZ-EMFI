# BasicAppDataTypes

Type-safe data serialization for Moku FPGA applications.

## Overview

BasicAppDataTypes provides a type system for automatic register mapping and serialization between Python control applications and VHDL FPGA logic on Moku platforms (Go, Lab, Pro, Delta).

**Key Features:**
- 23 built-in types (12 voltage + 10 time + 1 boolean)
- Platform-aware time conversions (125 MHz to 5 GHz)
- Automatic register packing (50-75% space savings)
- Type-safe voltage ranges (±5V, ±20V, ±25V)
- User-friendly units (nanoseconds, microseconds, volts)

## Installation

From EZ-EMFI repository:
```bash
# As editable dependency (for development)
uv pip install -e libs/basic-app-datatypes
```

## Quick Start

```python
from basic_app_datatypes import (
    BasicAppDataTypes,
    PulseDuration_ns,
    TypeConverter,
)

# Define a 500ns pulse duration
firing_duration = PulseDuration_ns(500, width=16)

# Convert to clock cycles (Moku:Go @ 125 MHz)
cycles = firing_duration.to_cycles(clock_period_ns=8.0, rounding='ROUND_UP')
# Result: 63 cycles

# Get the corresponding BasicAppDataType
duration_type = firing_duration.to_basic_type()
# Result: BasicAppDataTypes.PULSE_DURATION_NS_U16

# Convert voltage to register value
converter = TypeConverter()
voltage = 2.5  # volts
register_value = converter.voltage_output_05v_s16_to_bits(voltage)
```

## Type System

### Voltage Types (12 total)

**Output Types (±5V range):**
- `VOLTAGE_OUTPUT_05V_S8` - Signed 8-bit (128 steps)
- `VOLTAGE_OUTPUT_05V_S16` - Signed 16-bit (32768 steps)
- `VOLTAGE_OUTPUT_05V_U7` - Unsigned 7-bit (0 to +5V, 128 steps)
- `VOLTAGE_OUTPUT_05V_U15` - Unsigned 15-bit (0 to +5V, 32768 steps)

**Input Types (±20V range):**
- `VOLTAGE_INPUT_20V_S8`, `VOLTAGE_INPUT_20V_S16`
- `VOLTAGE_INPUT_20V_U7`, `VOLTAGE_INPUT_20V_U15`

**Input Types (±25V range):**
- `VOLTAGE_INPUT_25V_S8`, `VOLTAGE_INPUT_25V_S16`
- `VOLTAGE_INPUT_25V_U7`, `VOLTAGE_INPUT_25V_U15`

### Time Types (10 total)

**Nanoseconds:**
- `PULSE_DURATION_NS_U8` (0-255 ns)
- `PULSE_DURATION_NS_U16` (0-65,535 ns)
- `PULSE_DURATION_NS_U32` (0-4.3 billion ns)

**Microseconds:**
- `PULSE_DURATION_US_U8` (0-255 µs)
- `PULSE_DURATION_US_U16` (0-65,535 µs)
- `PULSE_DURATION_US_U24` (0-16.7 million µs)

**Milliseconds:**
- `PULSE_DURATION_MS_U8` (0-255 ms)
- `PULSE_DURATION_MS_U16` (0-65,535 ms)

**Seconds:**
- `PULSE_DURATION_S_U8` (0-255 sec)
- `PULSE_DURATION_S_U16` (0-65,535 sec)

### Boolean Type (1 total)

- `BOOLEAN` - 1-bit (0 or 1)

## Platform Support

BasicAppDataTypes supports all 4 Moku platforms with automatic clock period conversion:

| Platform | Clock | Period | Example |
|----------|-------|--------|---------|
| Moku:Go | 125 MHz | 8.0 ns | `PulseDuration_ns(500).to_cycles(8.0)` → 63 cycles |
| Moku:Lab | 500 MHz | 2.0 ns | `PulseDuration_ns(500).to_cycles(2.0)` → 250 cycles |
| Moku:Pro | 1.25 GHz | 0.8 ns | `PulseDuration_ns(500).to_cycles(0.8)` → 625 cycles |
| Moku:Delta | 5 GHz | 0.2 ns | `PulseDuration_ns(500).to_cycles(0.2)` → 2500 cycles |

## Testing

Run the test suite:
```bash
pytest libs/basic-app-datatypes/tests/
```

Expected: 18 passing tests covering:
- Type registry completeness
- Voltage conversions (all 12 types)
- Time conversions (all 10 types)
- Platform compatibility
- Boolean type
- Immutability

## Architecture

```
Python App                FPGA Logic
──────────                ──────────
PulseDuration_ns(500)
    ↓
to_cycles(clock_period)
    ↓
63 cycles
    ↓
TypeConverter
    ↓
Register bits (0x003F)  →  Network  →  std_logic_vector(15 downto 0)
                                              ↓
                                         VHDL Deserializer
                                              ↓
                                         App Logic
```

## Development

**Project Structure:**
```
libs/basic-app-datatypes/
├── README.md                   # This file
├── pyproject.toml              # Package configuration
├── basic_app_datatypes/        # Source code
│   ├── __init__.py             # Public API
│   ├── types.py                # BasicAppDataTypes enum
│   ├── metadata.py             # TYPE_REGISTRY
│   ├── time.py                 # PulseDuration_* classes
│   ├── voltage.py              # Voltage utilities
│   └── converters.py           # TypeConverter
└── tests/                      # Test suite
    └── test_basic_app_datatypes.py
```

**Future Roadmap:**
- Phase 2: Automatic register mapping algorithm
- Phase 3: Package bundling system
- Phase 4: VHDL code generation
- Phase 5: CocotB hardware validation
- Phase 6: Migration guides and documentation

## Contributing

This package is part of the [EZ-EMFI](https://github.com/yourusername/EZ-EMFI) project.

See `docs/BasicAppDataTypes/` in the main repository for:
- Design specifications
- Implementation phases
- Migration guides
- VHDL integration

## License

[Your License Here]

---

**Version:** 0.1.0
**Status:** Alpha (Phase 1 Complete)
**Last Updated:** 2025-11-02
