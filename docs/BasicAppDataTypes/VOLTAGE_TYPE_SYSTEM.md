# BasicAppDataTypes Voltage Type System

**Status:** Design Finalized
**Date:** 2025-01-28
**Phase:** BAD Phase 1 - Core Type System Implementation

---

## Overview

The BasicAppDataTypes voltage type system provides **fixed-width, range-specific voltage types** for safe serialization between Python and VHDL across all Moku platforms.

**Core Design Principles:**
1. **Type Safety**: Input and output types are distinct and non-interchangeable
2. **Range-Specific**: Each voltage range has dedicated types (prevents misuse)
3. **Platform-Agnostic**: Types work across Go/Lab/Pro/Delta platforms
4. **Bit Efficiency**: Unsigned variants save 1 bit for unipolar signals
5. **Fixed Width**: All types have immutable bit widths known a priori

---

## Voltage Type Taxonomy

### Naming Convention

```
VOLTAGE_{DIRECTION}_{RANGE}_{SIGNEDNESS}{BITS}
```

**Components:**
- `DIRECTION`: `INPUT` (ADC) or `OUTPUT` (DAC)
- `RANGE`: `05V`, `20V`, `25V` (zero-padded for consistency)
- `SIGNEDNESS`: `S` (signed, bipolar ±X) or `U` (unsigned, unipolar 0 to +X)
- `BITS`: `7`, `8`, `15`, `16`

**Examples:**
- `VOLTAGE_OUTPUT_05V_S16` → Output, ±5V, signed 16-bit
- `VOLTAGE_INPUT_25V_U7` → Input, 0 to +25V, unsigned 7-bit

---

## Platform Voltage Capabilities

### Hardware Specifications (from moku-models)

| Platform | ADC Bits | DAC Bits | Input Range | Output Range |
|----------|----------|----------|-------------|--------------|
| Moku:Go  | 12-bit   | 12-bit   | ±25V (50Vpp)| ±5V (10Vpp)  |
| Moku:Lab | 12-bit   | 16-bit   | ±25V (50Vpp)| ±5V (10Vpp)  |
| Moku:Pro | 10-bit*  | 16-bit   | ±25V (50Vpp)| ±5V (10Vpp)  |
| Moku:Delta | 14-bit* | 14-bit  | ±20V (40Vpp)| ±5V (10Vpp)  |

\* Blended ADC architectures (ignored for first-pass implementation)

**Key Observations:**
- **All platforms support ±5V outputs** (10Vpp DAC range)
- **Go/Lab/Pro support ±25V inputs** (50Vpp ADC range)
- **Delta supports ±20V inputs** (40Vpp ADC range)

---

## Type Definitions

### Output Voltage Types (DAC)

**All platforms support ±5V output range**

```python
# Signed (bipolar ±5V)
VOLTAGE_OUTPUT_05V_S8   # 8-bit signed,  ±5V, ~39mV/bit resolution
VOLTAGE_OUTPUT_05V_S16  # 16-bit signed, ±5V, ~153µV/bit resolution

# Unsigned (unipolar 0 to +5V)
VOLTAGE_OUTPUT_05V_U7   # 7-bit unsigned,  0 to +5V, ~39mV/bit resolution
VOLTAGE_OUTPUT_05V_U15  # 15-bit unsigned, 0 to +5V, ~153µV/bit resolution
```

**Use Cases:**
- **Signed (S)**: Bipolar waveforms, AC-coupled signals, EMFI probe driving
- **Unsigned (U)**: Positive-only signals, DC offsets, amplitude envelopes

---

### Input Voltage Types (ADC)

#### Delta Inputs: ±20V (40Vpp)

```python
# Signed (bipolar ±20V)
VOLTAGE_INPUT_20V_S8    # 8-bit signed,  ±20V, ~156mV/bit resolution
VOLTAGE_INPUT_20V_S16   # 16-bit signed, ±20V, ~611µV/bit resolution

# Unsigned (unipolar 0 to +20V)
VOLTAGE_INPUT_20V_U7    # 7-bit unsigned,  0 to +20V, ~156mV/bit resolution
VOLTAGE_INPUT_20V_U15   # 15-bit unsigned, 0 to +20V, ~611µV/bit resolution
```

#### Go/Lab/Pro Inputs: ±25V (50Vpp)

```python
# Signed (bipolar ±25V)
VOLTAGE_INPUT_25V_S8    # 8-bit signed,  ±25V, ~195mV/bit resolution
VOLTAGE_INPUT_25V_S16   # 16-bit signed, ±25V, ~763µV/bit resolution

# Unsigned (unipolar 0 to +25V)
VOLTAGE_INPUT_25V_U7    # 7-bit unsigned,  0 to +25V, ~195mV/bit resolution
VOLTAGE_INPUT_25V_U15   # 15-bit unsigned, 0 to +25V, ~763µV/bit resolution
```

**Use Cases:**
- **Signed (S)**: Bipolar input signals, trigger thresholds, AC measurements
- **Unsigned (U)**: Positive-only signals, current monitoring, safety-critical controls

---

## Design Rationale

### Why Separate INPUT/OUTPUT Types?

**Safety and Semantics:**
- Prevents accidentally using an ADC type on a DAC output (or vice versa)
- Makes YAML configs self-documenting ("this drives the DAC")
- Enables future platform-specific validation

**Example of prevented misuse:**
```python
# GOOD: Correct usage
intensity = VOLTAGE_OUTPUT_05V_S16  # Drives DAC output

# BAD: Type mismatch (would be caught by validator)
intensity = VOLTAGE_INPUT_25V_S16   # ERROR: Input type on output register
```

---

### Why Unsigned (U) Variants?

**Bit Packing Efficiency:**
- Unsigned types pack into 7/15 bits vs signed 8/16 bits
- **Saves 1 bit per register** for Phase 2 register packing optimization
- Example: 8 booleans + 1 unsigned voltage = fits in one 32-bit register

**Application Safety:**
- Prevents negative voltages when physically impossible/unsafe
- Self-documenting intent ("this value is always positive")

**Example:**
```yaml
# EMFI probe current monitor (positive-only)
- name: "Current Monitor"
  type: voltage_input_25v_u15  # Cannot go negative (safety + packing)

# EMFI probe intensity (bipolar control)
- name: "Intensity"
  type: voltage_output_05v_s16  # Can go positive/negative
```

---

### Why Range-Specific Types?

**Prevents Range Mismatches:**
- A ±25V value cannot accidentally be used where only ±5V is supported
- Code generator validates type compatibility with target platform

**Example:**
```python
# Platform validation at YAML parse time
if register.type == VOLTAGE_INPUT_25V_S16:
    if platform == MOKU_DELTA_PLATFORM:
        raise ValueError("Delta only supports ±20V inputs, not ±25V")
```

---

## Resolution Calculations

### Formula

For **signed** types:
```
resolution = (2 × max_voltage) / (2^bits)
```

For **unsigned** types:
```
resolution = max_voltage / (2^bits)
```

### Lookup Table

| Type                      | Range      | Bits | Resolution   |
|---------------------------|------------|------|--------------|
| VOLTAGE_OUTPUT_05V_S8     | ±5V        | 8    | ~39 mV/bit   |
| VOLTAGE_OUTPUT_05V_S16    | ±5V        | 16   | ~153 µV/bit  |
| VOLTAGE_OUTPUT_05V_U7     | 0 to +5V   | 7    | ~39 mV/bit   |
| VOLTAGE_OUTPUT_05V_U15    | 0 to +5V   | 15   | ~153 µV/bit  |
| VOLTAGE_INPUT_20V_S8      | ±20V       | 8    | ~156 mV/bit  |
| VOLTAGE_INPUT_20V_S16     | ±20V       | 16   | ~611 µV/bit  |
| VOLTAGE_INPUT_20V_U7      | 0 to +20V  | 7    | ~156 mV/bit  |
| VOLTAGE_INPUT_20V_U15     | 0 to +20V  | 15   | ~611 µV/bit  |
| VOLTAGE_INPUT_25V_S8      | ±25V       | 8    | ~195 mV/bit  |
| VOLTAGE_INPUT_25V_S16     | ±25V       | 16   | ~763 µV/bit  |
| VOLTAGE_INPUT_25V_U7      | 0 to +25V  | 7    | ~195 mV/bit  |
| VOLTAGE_INPUT_25V_U15     | 0 to +25V  | 15   | ~763 µV/bit  |

---

## VHDL Type Mappings

### Signed Types (S8, S16)

```vhdl
-- S8: 8-bit signed
signal voltage : signed(7 downto 0);

-- S16: 16-bit signed
signal voltage : signed(15 downto 0);
```

### Unsigned Types (U7, U15)

```vhdl
-- U7: 7-bit unsigned
signal voltage : unsigned(6 downto 0);

-- U15: 15-bit unsigned
signal voltage : unsigned(14 downto 0);
```

### MSB-Aligned Packing (32-bit Control Registers)

**Example: S16 type in Control Register**
```vhdl
-- Extract signed 16-bit voltage from upper 16 bits of CR
signal intensity : signed(15 downto 0);
intensity <= signed(control_reg_8(31 downto 16));
```

**Example: U7 type in Control Register**
```vhdl
-- Extract unsigned 7-bit voltage from upper 7 bits of CR
signal current_monitor : unsigned(6 downto 0);
current_monitor <= unsigned(control_reg_9(31 downto 25));
```

---

## Usage Example (DS1140-PD EMFI Probe)

```yaml
# DS1140-PD VoloApp Definition
registers:
  # Input: Trigger threshold from ADC
  - name: "Trigger Threshold"
    description: "Voltage threshold for trigger detection"
    type: voltage_input_25v_s16  # Moku:Go/Lab/Pro ADC input
    default_mv: 2400             # 2.4V

  # Output: Probe intensity to DAC
  - name: "Intensity"
    description: "Output intensity/Firing Voltage"
    type: voltage_output_05v_s16  # DAC output (all platforms)
    default_mv: 2400              # 2.4V

  # Input: Current monitor (positive-only, unsigned for safety)
  - name: "Current Monitor"
    description: "Probe current feedback"
    type: voltage_input_25v_u15   # Unsigned (cannot go negative)
    default_mv: 0
```

**Generated VHDL signals:**
```vhdl
-- From Control Register 7 (upper 16 bits)
signal trigger_threshold : signed(15 downto 0);
trigger_threshold <= signed(control_reg_7(31 downto 16));

-- From Control Register 8 (upper 16 bits)
signal intensity : signed(15 downto 0);
intensity <= signed(control_reg_8(31 downto 16));

-- From Control Register 9 (upper 15 bits)
signal current_monitor : unsigned(14 downto 0);
current_monitor <= unsigned(control_reg_9(31 downto 17));
```

---

## Implementation Requirements

### TypeMetadata Structure

```python
@dataclass(frozen=True)  # Immutable for safety
class TypeMetadata:
    type_name: BasicAppDataTypes
    bit_width: int                    # Fixed width (7, 8, 15, or 16)
    vhdl_type: str                    # "signed(15 downto 0)" or "unsigned(14 downto 0)"
    python_type: type                 # int
    min_value: int                    # Minimum value in millivolts
    max_value: int                    # Maximum value in millivolts
    default_value: int                # Default value (0 mV)
    direction: Literal['input', 'output']  # ADC or DAC
    signedness: Literal['signed', 'unsigned']
```

### TypeConverter Requirements

```python
class TypeConverter:
    @staticmethod
    def voltage_output_05v_s16_to_raw(mv: int) -> int:
        """Convert millivolts to 16-bit signed raw value (±5V range)."""
        # Clamp to ±5000 mV
        # Scale: (mv / 5000.0) * 32767
        ...

    @staticmethod
    def raw_to_voltage_output_05v_s16(raw: int) -> int:
        """Convert 16-bit signed raw to millivolts (±5V range)."""
        # Scale: (raw / 32767.0) * 5000
        ...
```

---

## Design Constraints

### Must Have
- ✅ Fixed, immutable bit widths
- ✅ No endianness (just bit positions)
- ✅ MSB-aligned extraction
- ✅ Self-documenting type names
- ✅ Input/output distinction
- ✅ Range-specific types

### Must Support
- ✅ Platform-agnostic (works on all 4 Moku platforms)
- ✅ Type validation before serialization
- ✅ Clear error messages for out-of-range values
- ✅ Bit-packing optimization (unsigned saves 1 bit)

### Out of Scope (Phase 1)
- ❌ Switchable voltage ranges (deferred)
- ❌ Platform-specific ADC/DAC resolution handling
- ❌ Blended ADC modes (Pro/Delta)
- ❌ Dynamic range selection

---

## References

- **Platform specs**: `moku-models/docs/MOKU_PLATFORM_SPECIFICATIONS.md`
- **Platform models**: `moku-models/moku_models/platforms/*.py`
- **Phase 1 prompt**: `docs/BasicAppDataTypes/BAD_Phase1_TypeSystem.md`
- **Historical VHDL voltage package**: `VHDL/packages/volo_voltage_pkg.vhd` (±5V only)

---

## Version History

- **2025-01-28**: Initial design finalized
  - Established INPUT/OUTPUT distinction
  - Added unsigned variants (U7, U15)
  - Defined range-specific types (05V, 20V, 25V)
  - Zero-padded range naming for consistency

---

**Next Steps**: Proceed to TIME type system design
