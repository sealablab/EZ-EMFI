# BAD Phase 1: Core Type System Implementation

**Phase:** 1 of 6
**Goal:** Define and implement BasicAppDataTypes with fixed-width serialization
**Prerequisites:** None (first phase)
**Output:** `models/custom_inst/basic_app_datatypes.py` and specification

## Git Workflow

**Branch:** `feature/BAD/P1`

**Starting this phase:**
```bash
git checkout feature/BAD
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
git checkout feature/BAD
git merge --no-ff feature/BAD/P1 -m "Merge Phase 1: Core type system implementation"
```

**Full workflow:** See [BAD_MASTER_Orchestrator.md](./BAD_MASTER_Orchestrator.md#git-workflow)

## Context Loading

Please review these files to understand the current system:

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
   - Current: ±10V range in 16 bits = ~305µV/bit
   - Alternative: ±5V range in 16 bits = ~153µV/bit
   - Which is more appropriate for EMFI probes?

2. **Time Type Granularity:**
   - Should we have TIME_NS, TIME_US, TIME_MS or just one?
   - How do we handle clock frequency variations?

3. **Boolean Packing:**
   - Pack multiple booleans per register bit?
   - Or always use full bit with MSB alignment?

4. **Default Values:**
   - Type-based defaults (0V, 0ms, False)?
   - Or application-specified defaults?

5. **Signed vs Unsigned:**
   - Should voltage always be signed?
   - Should time always be unsigned?

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

1. Create the basic_app_datatypes.py file
2. Start with VOLTAGE_MV as the canonical example
3. Get feedback on design decisions as you go
4. Implement other types following the pattern
5. Write comprehensive tests
6. Document in completion summary

Remember: Each type must have a **fixed bit width** that's known a priori. This is the fundamental requirement that enables automatic register packing in Phase 2.

---

**Questions?** Start implementing and ask for clarification on any design decisions as they come up. The goal is an interactive, iterative process.