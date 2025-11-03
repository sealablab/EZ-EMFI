# BAD Phase 1: Core Type System Implementation

**Phase:** 1 of 6
**Goal:** Define and implement BasicAppDataTypes with fixed-width serialization
**Prerequisites:** None (first phase)
**Output:** `models/custom_inst/basic_app_datatypes.py` and specification

## Git Workflow

**Branch:** `feature/BAD/P1`

**Starting this phase:**
```bash
git checkout feature/BAD-main
git checkout -b feature/BAD/P1
```

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
git commit -m "feat(BAD/P1): Complete Phase 1 - Core type system"

# Write BAD_Phase1_COMPLETE.md with summary

# Merge back to feature branch
git checkout feature/BAD-main
git merge --no-ff feature/BAD/P1 -m "Merge Phase 1: Core type system implementation"
```

**Full workflow:** See [BAD_MASTER_Orchestrator.md](./BAD_MASTER_Orchestrator.md#git-workflow)

## Context Loading

Please review these files to understand the current system:

### Current Type System
```bash
# Current type system
cat models/custom_inst/app_register.py

# How types are used in apps
cat DS1140_PD_app.yaml

# Example of manual voltage handling
cat VHDL/packages/ds1120_pd_pkg.vhd | grep -A 5 "constant.*signed"

# Current code generator's type handling
cat tools/generate_custom_inst.py | grep -A 10 "get_vhdl_bit_range"
```

### Moku Platform Specifications
BasicAppDataTypes must align with Moku hardware constraints. Review platform specs:

```bash
# Comprehensive platform specifications (Go, Lab, Pro, Delta)
cat moku-models/docs/MOKU_PLATFORM_SPECIFICATIONS.md

# Platform model implementations
cat moku-models/moku_models/platforms/moku_go.py
cat moku-models/moku_models/platforms/moku_lab.py
cat moku-models/moku_models/platforms/moku_pro.py
cat moku-models/moku_models/platforms/moku_delta.py

# Central deployment abstraction
cat moku-models/moku_models/moku_config.py
```

**Key Platform Constraints:**

| Platform | ADC Bits | DAC Bits | Input Range | Output Range | Clock |
|----------|----------|----------|-------------|--------------|-------|
| Moku:Go | 12-bit | 12-bit | ±25V (50 Vpp) | ±5V (10 Vpp) | 125 MHz |
| Moku:Lab | 12-bit | 16-bit | ±5V (10 Vpp) | ±1V (2 Vpp into 50Ω) | 500 MHz |
| Moku:Pro | 10-bit* | 16-bit | ±20V (40 Vpp) | ±5V (up to 100 MHz) | 1.25 GHz |
| Moku:Delta | 14-bit* | 14-bit | ±20V (40 Vpp) | ±5V (up to 100 MHz) | 5 GHz |

\* Blended ADC architectures (Pro: 10-bit + 18-bit, Delta: 14-bit + 20-bit)

**Implications for VOLTAGE_MV type:**
- Must support **±10V range minimum** (covers all platforms with margin)
- 16-bit signed gives ~305µV/bit resolution (sufficient for EMFI probes)
- Moku:Go has widest input range (±25V) but lowest resolution (12-bit)
- Type system should be **platform-agnostic** (works on all 4 platforms)

## Phase 1 Objectives

### Primary Goals
1. Define `BasicAppDataTypes` enum with fundamental types
2. Implement serialization/deserialization for Python↔VHDL
3. Create type specifications with fixed bit widths
4. Provide conversion utilities for units (volts, time, etc.)

### Specific Deliverables

#### 1.1 Type Definitions
Create `models/custom_inst/basic_app_datatypes.py` with:

```python
class BasicAppDataTypes(str, Enum):
    # Fundamental types (no endianness, fixed width)
    VOLTAGE_MV = "voltage_mv"      # 16-bit signed, ±10V range
    TIME_NS = "time_ns"            # 32-bit unsigned, 0-4.29 sec
    TIME_US = "time_us"            # 24-bit unsigned, 0-16.7 sec
    TIME_MS = "time_ms"            # 16-bit unsigned, 0-65.5 sec
    BOOLEAN = "boolean"            # 1-bit

    # Legacy support (preserve compatibility)
    UNSIGNED_8 = "unsigned_8"      # 8-bit unsigned
    UNSIGNED_16 = "unsigned_16"    # 16-bit unsigned
    SIGNED_16 = "signed_16"        # 16-bit signed
```

#### 1.2 Type Specifications
For each type, define:
- Bit width (immutable)
- Value range (min/max)
- Default value
- VHDL type mapping
- Python type mapping
- Serialization format (MSB-aligned)

#### 1.3 Conversion Utilities
Implement bidirectional converters:

```python
class TypeConverter:
    @staticmethod
    def voltage_mv_to_raw(mv: int) -> int:
        """Convert millivolts to 16-bit signed raw value"""
        # 10V full scale = 10000mV
        # Maps to -32768 to 32767
        return int((mv / 10000.0) * 32767)

    @staticmethod
    def raw_to_voltage_mv(raw: int) -> int:
        """Convert 16-bit signed raw to millivolts"""
        return int((raw / 32767.0) * 10000)

    @staticmethod
    def time_ms_to_clk_cycles(ms: int, clk_freq_hz: int) -> int:
        """Convert milliseconds to clock cycles"""
        return (ms * clk_freq_hz) // 1000
```

#### 1.4 Type Registry
Create registry for type metadata:

```python
@dataclass
class TypeMetadata:
    type_name: BasicAppDataTypes
    bit_width: int
    vhdl_type: str  # "signed(15 downto 0)", "std_logic", etc.
    python_type: type  # int, bool, etc.
    min_value: Optional[Union[int, float]]
    max_value: Optional[Union[int, float]]
    default_value: Union[int, float, bool]

TYPE_REGISTRY = {
    BasicAppDataTypes.VOLTAGE_MV: TypeMetadata(
        type_name=BasicAppDataTypes.VOLTAGE_MV,
        bit_width=16,
        vhdl_type="signed(15 downto 0)",
        python_type=int,
        min_value=-10000,  # -10V in mV
        max_value=10000,   # +10V in mV
        default_value=0
    ),
    # ... other types
}
```

## Design Constraints

### Must Have
- Each type has **fixed, immutable bit width**
- **No endianness** - just bit positions
- **MSB-aligned** extraction (consistent with current system)
- Types are **self-documenting** (clear units in name)

### Must Support
- Backwards compatibility with existing `RegisterType`
- Clean migration path from old to new types
- Type validation in Python before serialization
- Clear error messages for out-of-range values

## Interactive Decisions Needed

As you implement, we'll need to decide:

1. **Voltage Resolution:**
   - **Recommended: ±10V range in 16 bits = ~305µV/bit**
   - Rationale: Covers all Moku platforms (Go: ±25V, Lab: ±5V, Pro/Delta: ±20V)
   - EMFI probe context: DS1140-PD datasheet shows ±10V operating range
   - Alternative ±5V would limit compatibility with Moku:Go/Pro/Delta
   - **Decision: Use ±10V (10000 mV) as full-scale range**

2. **Time Type Granularity:**
   - **Platform clock frequencies vary: 125 MHz (Go) to 5 GHz (Delta)**
   - TIME_NS: Needed for high-precision timing on Moku:Pro/Delta
   - TIME_US: Useful for mid-range pulse widths (common in EMFI)
   - TIME_MS: Convenient for longer delays
   - **Decision: Provide all three types, let application choose appropriate granularity**
   - Clock conversion handled at VHDL generation time (platform-specific)

3. **Boolean Packing:**
   - Current system uses MSB-aligned 32-bit registers
   - Phase 2 RegisterMapper will handle optimal bit packing
   - **Decision: Boolean = 1 bit, let Phase 2 pack multiple booleans per register**
   - Example: 8 booleans could fit in upper 8 bits of one 32-bit register

4. **Default Values:**
   - **Type-based defaults** for safety (0V, 0ns, False)
   - Application can override in YAML (`default_mv: 2400`)
   - **Decision: TypeMetadata specifies type defaults, YAML can override**

5. **Signed vs Unsigned:**
   - **Voltage: Always signed** (EMFI probes can have negative/positive pulses)
   - **Time: Always unsigned** (negative time durations are meaningless)
   - **Decision: VOLTAGE_MV = signed(15 downto 0), TIME_* = unsigned**

6. **Platform Compatibility:**
   - Type system must work across Moku:Go, Lab, Pro, Delta
   - VHDL templates will use platform specs from `moku-models`
   - **Decision: Types are platform-agnostic, code generator adapts to platform**

## Test Cases to Implement

Create `tests/test_basic_app_datatypes.py`:

```python
def test_voltage_conversion():
    # Test nominal values
    assert TypeConverter.voltage_mv_to_raw(2400) == 0x1EB8  # 2.4V
    assert TypeConverter.raw_to_voltage_mv(0x1EB8) == 2400

    # Test limits
    assert TypeConverter.voltage_mv_to_raw(10000) == 32767
    assert TypeConverter.voltage_mv_to_raw(-10000) == -32768

    # Test round-trip
    for mv in [0, 1000, -1000, 2400, 5000, -5000]:
        raw = TypeConverter.voltage_mv_to_raw(mv)
        recovered = TypeConverter.raw_to_voltage_mv(raw)
        assert abs(recovered - mv) < 1  # Allow rounding error

def test_type_metadata():
    # Verify all types have metadata
    for type_enum in BasicAppDataTypes:
        assert type_enum in TYPE_REGISTRY
        metadata = TYPE_REGISTRY[type_enum]
        assert metadata.bit_width > 0
        assert metadata.vhdl_type
        assert metadata.python_type

def test_bit_width_immutable():
    # Ensure bit widths are truly fixed
    metadata = TYPE_REGISTRY[BasicAppDataTypes.VOLTAGE_MV]
    assert metadata.bit_width == 16
    # Should not be able to change
    with pytest.raises(AttributeError):
        metadata.bit_width = 32

def test_platform_compatibility():
    """Verify voltage range works across all Moku platforms."""
    from moku_models import MOKU_GO_PLATFORM, MOKU_LAB_PLATFORM, MOKU_PRO_PLATFORM

    # Test voltage is within all platform capabilities
    test_voltages_mv = [0, 2400, 5000, -5000, 10000, -10000]

    for mv in test_voltages_mv:
        raw = TypeConverter.voltage_mv_to_raw(mv)

        # Verify voltage is within platform input ranges
        assert abs(mv / 1000.0) <= 25  # Moku:Go max input (±25V)
        assert abs(mv / 1000.0) <= 20  # Moku:Pro/Delta max (±20V)
        # Note: ±10V easily fits Moku:Lab ±5V range

    # Verify clock conversions for different platforms
    time_ms = 100  # 100ms

    # Moku:Go (125 MHz)
    cycles_go = TypeConverter.time_ms_to_clk_cycles(time_ms, 125_000_000)
    assert cycles_go == 12_500_000

    # Moku:Delta (5 GHz)
    cycles_delta = TypeConverter.time_ms_to_clk_cycles(time_ms, 5_000_000_000)
    assert cycles_delta == 500_000_000
```

## Migration Example

Show how DS1140_PD would change:

**Current (DS1140_PD_app.yaml):**
```yaml
registers:
  - name: "Intensity"
    description: "Output intensity/Firing Voltage"
    reg_type: counter_16bit  # Actually signed voltage
    cr_number: 14
    # Manual: 0x1EB8 = 2.4V
```

**With BasicAppDataTypes:**
```yaml
registers:
  - name: "Intensity"
    description: "Output intensity/Firing Voltage"
    type: voltage_mv
    default_mv: 2400  # Clear units!
    # cr_number: auto-assigned in Phase 2
```

## Success Criteria

Phase 1 is complete when:

- [ ] `basic_app_datatypes.py` created with all type definitions
- [ ] Type specifications documented (bit width, range, etc.)
- [ ] Conversion utilities implemented and tested
- [ ] Type registry with metadata for all types
- [ ] Unit tests passing for conversions
- [ ] Migration example demonstrated
- [ ] Phase summary written to `BAD_Phase1_COMPLETE.md`

## Output Artifacts

### Required Files
1. `models/custom_inst/basic_app_datatypes.py` - Core implementation
2. `tests/test_basic_app_datatypes.py` - Test suite
3. `docs/BasicAppDataTypes/BAD_Phase1_COMPLETE.md` - Summary

### Summary Format
The completion summary should include:
- List of implemented types with bit widths
- Key design decisions made
- Conversion formula documentation
- Any unresolved questions for Phase 2
- Git commit hash

## Handoff to Phase 2

Phase 2 will need:
- The type registry with bit widths
- Understanding of serialization format
- Any packing constraints discovered
- Test utilities for validation

Update `BAD_Phase2_RegisterMapping.md` header with:
```markdown
**Prerequisites:** Phase 1 complete
**Phase 1 Summary:** ./BAD_Phase1_COMPLETE.md
**Phase 1 Commit:** {git_hash}
```

## Getting Started

1. **Review platform specifications** from `moku-models/` to understand hardware constraints
2. Create the basic_app_datatypes.py file
3. Start with VOLTAGE_MV as the canonical example (most constrained by hardware)
4. Get feedback on design decisions as you go
5. Implement other types following the pattern
6. Write comprehensive tests (including platform compatibility tests)
7. Document in completion summary

**Dependencies:**
- `moku-models` package (git submodule at `moku-models/`)
- Platform constants: `MOKU_GO_PLATFORM`, `MOKU_LAB_PLATFORM`, `MOKU_PRO_PLATFORM`, `MOKU_DELTA_PLATFORM`
- Import in tests: `from moku_models import MOKU_GO_PLATFORM`

Remember: Each type must have a **fixed bit width** that's known a priori. This is the fundamental requirement that enables automatic register packing in Phase 2. Types must also be **platform-agnostic** (work on all 4 Moku platforms).

---

**Questions?** Start implementing and ask for clarification on any design decisions as they come up. The goal is an interactive, iterative process.