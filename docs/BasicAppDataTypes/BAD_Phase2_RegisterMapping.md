# BAD Phase 2: Automatic Register Mapping Implementation

**Phase:** 2 of 6
**Goal:** Implement automatic register mapping algorithm for efficient bit packing
**Prerequisites:** Phase 1 complete ✓
**Phase 1 Commit:** `14dfec1` (feat(BAD/P1): Complete Phase 1)
**Output:** `models/custom_inst/register_mapper.py` and mapping algorithm
**Test Directory:** `python_tests/` (separate from CocotB VHDL tests)

## Git Workflow

**Branch:** `feature/BAD/P2`

**Starting this phase:**
```bash
git checkout feature/BAD-main
git checkout -b feature/BAD/P2
```

**During development:**
```bash
# Commit frequently as you implement
git add <files>
git commit -m "feat(BAD/P2): <description>"
```

**Completing this phase:**
```bash
# Final commit with phase completion
git add .
git commit -m "feat(BAD/P2): Complete Phase 2 - Register mapping algorithm"

# Write BAD_Phase2_COMPLETE.md with summary

# Merge back to feature branch
git checkout feature/BAD-main
git merge --no-ff feature/BAD/P2 -m "Merge Phase 2: Automatic register mapping"
```

**Full workflow:** See [BAD_MASTER_Orchestrator.md](./BAD_MASTER_Orchestrator.md#git-workflow)

## Context Loading

**Phase 1 Results:**
- ✅ BasicAppDataTypes enum: 23 types (12 voltage + 10 time + 1 boolean)
- ✅ TypeMetadata with immutable bit widths
- ✅ TYPE_REGISTRY: Complete metadata for all types
- ✅ PulseDuration classes: User-friendly time API
- ✅ TypeConverter: Voltage/time conversions
- ✅ Module location: `models/custom_inst/datatypes/`
- ✅ Tests: `python_tests/test_basic_app_datatypes.py` (18 tests passing)

**Key imports for Phase 2:**
```python
from models.custom_inst.datatypes import (
    BasicAppDataTypes,
    TypeMetadata,
    TYPE_REGISTRY,
)
```

**Register constraints to review:**
```bash
# Current register allocation
cat shared/custom_inst/custom_inst_common_pkg.vhd | grep -A 5 "APP_REG"

# How registers are currently assigned (manual)
cat DS1140_PD_app.yaml | grep -A 2 "cr_number"

# Current bit extraction logic
cat shared/custom_inst/templates/custom_inst_shim_template.vhd | grep -A 5 "app_reg_"
```

## Phase 2 Objectives

### Primary Goals
1. Design algorithm for automatic CR number assignment
2. Implement efficient bit packing within 384-bit limit (12 registers)
3. Generate deterministic, reproducible mappings
4. Provide clear mapping reports and diagnostics

### Specific Deliverables

#### 2.1 Register Mapper Core
Create `models/custom_inst/register_mapper.py`:

```python
@dataclass
class MappedRegister:
    """Result of mapping a BasicAppDataType to physical registers"""
    name: str
    type: BasicAppDataTypes
    cr_number: int  # 6-17
    bit_slice: Tuple[int, int]  # (msb, lsb) e.g., (31, 16)

    def to_vhdl_extraction(self) -> str:
        """Generate VHDL bit extraction code"""
        if self.bit_slice[0] == self.bit_slice[1]:
            return f"app_reg_{self.cr_number}({self.bit_slice[0]})"
        return f"app_reg_{self.cr_number}({self.bit_slice[0]} downto {self.bit_slice[1]})"

class RegisterMapper:
    """Maps BasicAppDataTypes to Control Registers with optimal packing"""

    MAX_APP_REGISTERS = 12  # CR6-CR17
    BITS_PER_REGISTER = 32
    TOTAL_BITS = MAX_APP_REGISTERS * BITS_PER_REGISTER  # 384 bits

    def map_registers(self,
                      datatypes: List[Tuple[str, BasicAppDataTypes]],
                      strategy: str = "first_fit") -> List[MappedRegister]:
        """
        Map datatypes to control registers

        Args:
            datatypes: List of (name, type) tuples
            strategy: Packing strategy ('first_fit', 'best_fit', 'optimal')

        Returns:
            List of mapped registers with CR assignments

        Raises:
            RegisterOverflowError: If types don't fit in 384 bits
        """
```

#### 2.2 Packing Strategies

Implement multiple strategies for comparison:

```python
class PackingStrategy(ABC):
    @abstractmethod
    def pack(self, datatypes: List[Tuple[str, BasicAppDataTypes]]) -> List[MappedRegister]:
        pass

class FirstFitStrategy(PackingStrategy):
    """
    Simple strategy: Pack types sequentially into registers
    - Start with CR6
    - Pack each type MSB-aligned
    - Move to next CR when current is full
    """

class BestFitStrategy(PackingStrategy):
    """
    Optimal packing: Minimize wasted bits
    - Sort by bit width (largest first)
    - Pack similar-sized types together
    - Combine small types in single register
    """

class SingleTypePerRegister(PackingStrategy):
    """
    Compatibility mode: One type per CR (like current system)
    - Each type gets its own CR
    - MSB-aligned within register
    - Simple but wasteful
    """
```

#### 2.3 Mapping Report Generator

Provide clear visibility into packing:

```python
@dataclass
class MappingReport:
    """Detailed report of register mapping results"""
    total_bits_used: int
    total_bits_available: int
    efficiency_percent: float
    register_map: Dict[int, List[MappedRegister]]  # CR -> types

    def to_markdown(self) -> str:
        """Generate human-readable mapping report"""

    def to_vhdl_comment(self) -> str:
        """Generate VHDL comment block documenting mapping"""

    def visualize(self) -> str:
        """ASCII art visualization of bit packing"""
```

Example visualization:
```
CR6  [31:16] intensity (voltage_mv)    [15:0] threshold (voltage_mv)
CR7  [31:24] clock_div (unsigned_8)    [23:16] UNUSED    [15:0] timeout (time_ms)
CR8  [31] arm_probe (boolean)          [30:0] UNUSED
...
CR17 UNUSED

Efficiency: 72/384 bits (18.75%)
```

#### 2.4 Constraints and Validation

```python
class MappingConstraints:
    """Define and validate mapping constraints"""

    def __init__(self):
        self.reserved_registers = [18, 19, 20, 21]  # Reserved for internal
        self.max_app_registers = 12
        self.alignment = "msb"  # MSB-aligned packing

    def validate(self, mapping: List[MappedRegister]) -> List[str]:
        """Return list of constraint violations"""
        violations = []

        # Check CR numbers are in valid range
        for reg in mapping:
            if reg.cr_number < 6 or reg.cr_number > 17:
                violations.append(f"{reg.name}: CR{reg.cr_number} out of range")

        # Check no overlapping bit slices
        # Check total bit usage
        # etc...

        return violations
```

## Design Decisions Needed

### 2.1 Packing Strategy Selection

**Option A: First Fit (Simple)**
```
CR6:  [31:16] voltage_1    [15:0] voltage_2
CR7:  [31:16] time_ms      [15:0] UNUSED
CR8:  [31] bool_1          [30] bool_2    [29:0] UNUSED
```
- Pro: Simple, predictable
- Con: Potentially wasteful

**Option B: Best Fit (Optimal)**
```
CR6:  [31:16] voltage_1    [15:0] voltage_2
CR7:  [31:16] time_ms      [15:8] uint8     [7:0] uint8_2
CR8:  [31:28] bool_1..4    [27:0] UNUSED
```
- Pro: Maximum efficiency
- Con: More complex

**Option C: Type Clustering**
```
CR6-7:  All voltage types
CR8-9:  All time types
CR10:   All booleans
```
- Pro: Logical grouping
- Con: May waste space

### 2.2 Multi-Register Types

How should we handle types larger than 32 bits?

```python
# Option 1: Span registers
TIME_NS = "time_ns"  # 32-bit, fits in one CR

TIME_US_48 = "time_us_48"  # 48-bit, needs two CRs
# CR6[31:16] = upper 16 bits
# CR7[31:0] = lower 32 bits

# Option 2: Reject at mapping time
if type_metadata.bit_width > 32:
    raise ValueError(f"Type {type} too large for single register")
```

### 2.3 Alignment Rules

```python
# Current: Always MSB-aligned
CR6[31:16] = 16-bit value
CR6[15:0] = UNUSED

# Alternative: Pack from LSB
CR6[15:0] = 16-bit value
CR6[31:16] = UNUSED

# Or: Natural alignment
CR6[31:16] = 16-bit value_1
CR6[15:0] = 16-bit value_2
```

## Test Cases

Create `python_tests/test_register_mapper.py` (separate from CocotB tests in `tests/`):

```python
def test_simple_mapping():
    """Test basic register assignment"""
    mapper = RegisterMapper()
    datatypes = [
        ("intensity", BasicAppDataTypes.VOLTAGE_MV),
        ("threshold", BasicAppDataTypes.VOLTAGE_MV),
        ("timeout", BasicAppDataTypes.TIME_MS),
        ("enable", BasicAppDataTypes.BOOLEAN),
    ]

    mapping = mapper.map_registers(datatypes)

    # Should fit in 2-3 registers
    assert max(m.cr_number for m in mapping) <= 8

    # Check no overlaps
    for reg in mapping:
        assert reg.cr_number >= 6
        assert reg.cr_number <= 17

def test_overflow_detection():
    """Test handling of too many types"""
    mapper = RegisterMapper()

    # Try to map 25 16-bit values (400 bits > 384 limit)
    datatypes = [(f"val_{i}", BasicAppDataTypes.VOLTAGE_MV)
                 for i in range(25)]

    with pytest.raises(RegisterOverflowError):
        mapper.map_registers(datatypes)

def test_packing_efficiency():
    """Test different packing strategies"""
    datatypes = [
        ("v1", BasicAppDataTypes.VOLTAGE_MV),  # 16 bits
        ("v2", BasicAppDataTypes.VOLTAGE_MV),  # 16 bits
        ("t1", BasicAppDataTypes.TIME_MS),     # 16 bits
        ("u1", BasicAppDataTypes.UNSIGNED_8),  # 8 bits
        ("u2", BasicAppDataTypes.UNSIGNED_8),  # 8 bits
        ("b1", BasicAppDataTypes.BOOLEAN),     # 1 bit
        ("b2", BasicAppDataTypes.BOOLEAN),     # 1 bit
    ]

    mapper = RegisterMapper()

    # Test different strategies
    first_fit = mapper.map_registers(datatypes, strategy="first_fit")
    best_fit = mapper.map_registers(datatypes, strategy="best_fit")

    # Best fit should use fewer registers
    assert max(m.cr_number for m in best_fit) <= max(m.cr_number for m in first_fit)

def test_deterministic_mapping():
    """Ensure mapping is reproducible"""
    mapper = RegisterMapper()
    datatypes = [
        ("a", BasicAppDataTypes.VOLTAGE_MV),
        ("b", BasicAppDataTypes.TIME_MS),
        ("c", BasicAppDataTypes.BOOLEAN),
    ]

    mapping1 = mapper.map_registers(datatypes)
    mapping2 = mapper.map_registers(datatypes)

    # Same input should produce same output
    assert mapping1 == mapping2
```

## Example: DS1140_PD Mapping

Show how the mapper would handle DS1140_PD:

```python
# DS1140_PD datatypes
ds1140_types = [
    ("arm_probe", BasicAppDataTypes.BOOLEAN),      # 1 bit
    ("force_fire", BasicAppDataTypes.BOOLEAN),     # 1 bit
    ("reset_fsm", BasicAppDataTypes.BOOLEAN),      # 1 bit
    ("clock_divider", BasicAppDataTypes.UNSIGNED_8),   # 8 bits
    ("arm_timeout", BasicAppDataTypes.TIME_MS),    # 16 bits
    ("firing_duration", BasicAppDataTypes.UNSIGNED_8), # 8 bits
    ("cooling_duration", BasicAppDataTypes.UNSIGNED_8), # 8 bits
    ("trigger_threshold", BasicAppDataTypes.VOLTAGE_MV), # 16 bits
    ("intensity", BasicAppDataTypes.VOLTAGE_MV),   # 16 bits
]

# Current: Uses 9 registers (one per type)
# With packing: Should fit in 3-4 registers

mapper = RegisterMapper()
mapping = mapper.map_registers(ds1140_types, strategy="best_fit")
report = MappingReport.from_mapping(mapping)

print(report.visualize())
# Expected output:
# CR6  [31] arm_probe [30] force_fire [29] reset_fsm [28:21] clock_div [20:13] fire_dur [12:5] cool_dur [4:0] UNUSED
# CR7  [31:16] arm_timeout [15:0] trigger_threshold
# CR8  [31:16] intensity [15:0] UNUSED
#
# Total: 75 bits used of 384 available (19.5% efficiency)
# Registers saved: 6 (compared to current implementation)
```

## Migration Path

### From Manual to Automatic

**Current Process:**
1. Developer manually assigns CR numbers in YAML
2. Developer manually calculates bit positions
3. No validation of overlaps or overflow

**New Process:**
1. Developer lists datatypes in YAML (no CR numbers)
2. Mapper automatically assigns optimal packing
3. Report shows exact mapping for verification
4. Validation prevents errors

### Backwards Compatibility

```python
class HybridMapper(RegisterMapper):
    """Support both manual and automatic assignment"""

    def map_registers(self, app_config):
        registers = []

        for reg in app_config.registers:
            if hasattr(reg, 'cr_number'):
                # Manual assignment (legacy)
                registers.append(self._map_manual(reg))
            else:
                # Automatic assignment (new)
                registers.append(self._map_auto(reg))

        return registers
```

## Success Criteria

Phase 2 is complete when:

- [ ] `register_mapper.py` implemented with core algorithm
- [ ] Multiple packing strategies available and tested
- [ ] Mapping report generator with visualizations
- [ ] Constraint validation working
- [ ] DS1140_PD example demonstrates 50% reduction
- [ ] Unit tests passing for all strategies
- [ ] Phase summary written to `BAD_Phase2_COMPLETE.md`

## Output Artifacts

### Required Files
1. `models/custom_inst/register_mapper.py` - Mapping algorithm
2. `python_tests/test_register_mapper.py` - Test suite (Python unit tests)
3. `docs/BasicAppDataTypes/BAD_Phase2_COMPLETE.md` - Summary

**Note:** Use `python_tests/` directory for Python unit tests, NOT `tests/` (which contains CocotB VHDL tests)

### Summary Format
The completion summary should include:
- Chosen packing strategy and rationale
- DS1140_PD mapping results (before/after comparison)
- Performance metrics (bits saved, efficiency)
- Any edge cases discovered
- Integration notes for Phase 3

## Handoff to Phase 3

Phase 3 will need:
- The mapping algorithm API
- Understanding of packing constraints
- Report generation utilities
- Example mappings for testing

Update `BAD_Phase3_RegPackage.md` header with:
```markdown
**Prerequisites:** Phase 1-2 complete
**Phase 2 Summary:** ./BAD_Phase2_COMPLETE.md
**Phase 2 Commit:** {git_hash}
```

## Interactive Decisions

As you implement, we'll decide:

1. **Primary packing strategy**: First-fit vs best-fit vs type-clustering?
2. **Multi-bit type handling**: Allow spanning registers?
3. **Boolean packing density**: How many booleans per register?
4. **Mapping stability**: Should mappings be order-dependent?
5. **Report format**: What visualizations are most helpful?

## Getting Started

1. Implement `RegisterMapper` base class
2. Create `FirstFitStrategy` as baseline
3. Test with DS1140_PD types
4. Get feedback on packing efficiency
5. Implement more sophisticated strategies
6. Create comprehensive report generator

Remember: The goal is **automatic, efficient, and deterministic** register assignment that eliminates manual CR number management.

---

**Questions?** The mapper is the heart of BasicAppDataTypes - it transforms the type system into concrete register assignments. Make it robust!