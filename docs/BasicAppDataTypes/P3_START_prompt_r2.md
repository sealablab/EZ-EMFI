# Phase 3 Execution Prompt: Register Interface Package (Revision 2)

**Context:** You are implementing Phase 3 of the BasicAppDataTypes (BAD) system for the EZ-EMFI project. This is a fresh context window with everything needed to complete Phase 3.

**Revision 2 Updates:**
- Corrected TypeConverter integration (no generic `to_raw()` method exists)
- Fixed DS1140_PD example to use only `BasicAppDataTypes` (no legacy types)
- Clarified human-friendly units (millivolts, nanoseconds)
- Added DS1120A EMFI probe hardware context

---

## What You're Building

**Phase 3 Goal:** Create `BasicAppsRegPackage` - a type-safe register interface specification that integrates with the existing moku-models deployment system.

**Key Files:**
- `models/custom_inst/reg_package.py` (NEW - main deliverable)
- `examples/DS1140_PD_interface.yaml` (NEW - example)
- `examples/DS1140_PD_deployment.py` (NEW - integration demo)
- `python_tests/test_reg_package.py` (NEW - tests)

**Files to DELETE:**
- `models/custom_inst/app_register.py` (legacy)
- `models/custom_inst/custom_inst_app.py` (legacy)

---

## Phase 1-2 Context (What Already Exists)

### Phase 1: Type System (COMPLETE ✅)
```python
# libs/basic-app-datatypes/basic_app_datatypes/types.py
class BasicAppDataTypes(Enum):
    # 23 types total:
    # - 12 voltage types (INPUT/OUTPUT, ±5V/±20V/±25V, signed/unsigned)
    # - 10 time types (ns/us/ms/s with various widths)
    # - 1 boolean type
    VOLTAGE_OUTPUT_05V_S16 = "voltage_output_05v_s16"
    VOLTAGE_INPUT_25V_S16 = "voltage_input_25v_s16"
    PULSE_DURATION_NS_U8 = "pulse_duration_ns_u8"
    PULSE_DURATION_MS_U16 = "pulse_duration_ms_u16"
    BOOLEAN = "boolean"
    # ... (see libs/basic-app-datatypes/basic_app_datatypes/types.py for full list)

# libs/basic-app-datatypes/basic_app_datatypes/metadata.py
TYPE_REGISTRY: Dict[BasicAppDataTypes, TypeMetadata]
# Contains bit_width, min_value, max_value for each type

# libs/basic-app-datatypes/basic_app_datatypes/converters.py
class TypeConverter:
    """Voltage-specific conversion methods (no generic to_raw() method!)"""
    @staticmethod
    def voltage_output_05v_s16_to_raw(millivolts: int) -> int: ...
    @staticmethod
    def voltage_input_25v_s16_to_raw(millivolts: int) -> int: ...
    # ... (12 voltage types, each with specific _to_raw method)
```

### Phase 2: Register Mapping (COMPLETE ✅)
```python
# libs/basic-app-datatypes/basic_app_datatypes/mapper.py
class RegisterMapper:
    """Pure algorithm: maps BasicAppDataTypes to CR6-CR17 with bit packing."""
    def map(items: List[Tuple[str, BasicAppDataTypes]], strategy: str) -> List[RegisterMapping]
        # CR6-CR17 = 12 registers × 32 bits = 384 bits total
        # Strategies: first_fit, best_fit, type_clustering

class RegisterMapping:
    """Immutable result of mapping."""
    name: str
    datatype: BasicAppDataTypes
    cr_number: int  # 6-17
    bit_slice: Tuple[int, int]  # (msb, lsb)

# models/custom_inst/bad_register_mapper.py
class BADRegisterConfig(BaseModel):
    """Pydantic model for single register config."""
    name: str
    datatype: BasicAppDataTypes
    description: str = ""
    default_value: Optional[int | bool] = None

class BADRegisterMapper(BaseModel):
    """Pydantic wrapper for RegisterMapper."""
    registers: List[BADRegisterConfig]
    strategy: Literal["first_fit", "best_fit", "type_clustering"] = "best_fit"

    def to_register_mappings(self) -> List[RegisterMapping]:
        # Calls RegisterMapper.map() internally
```

**46/46 tests passing** in Phase 1-2.

---

## moku-models Context (Deployment System)

The project uses a separate `moku-models/` git submodule for deployment:

```python
# moku-models/moku_models/moku_config.py
class SlotConfig(BaseModel):
    """Per-slot instrument configuration."""
    instrument: str  # 'CloudCompile', 'Oscilloscope', etc.
    bitstream: str | None
    control_registers: dict[int, int] | None  # CR number → raw 32-bit value
    settings: dict[str, Any] = {}

class MokuConfig(BaseModel):
    """Central deployment abstraction."""
    platform: MokuGoPlatform  # Go/Lab/Pro/Delta
    slots: dict[int, SlotConfig]
    routing: list[MokuConnection]
    metadata: dict[str, Any] = {}
```

**Key Integration Point:** `BasicAppsRegPackage.to_control_registers()` must return `dict[int, int]` compatible with `SlotConfig.control_registers`.

---

## Hardware Context: Riscure DS1120A EMFI Probe

The DS1140_PD example interfaces with a Riscure DS1120A EMFI probe:

**Key Characteristics:**
- **Fixed 50ns pulse width** (hardware-determined, NOT software configurable)
- **Trigger:** digital_glitch (0-3.3V TTL, rising edge)
- **Power control:** pulse_amplitude (0-3.3V analog, linear 5-100% power)
- **Current monitor:** coil_current (-1.4V to 0V transient)

**Important:** The `firing_duration` and `cooling_duration` parameters control **FSM state timing**, NOT the actual EM pulse width (which is fixed at 50ns by the probe hardware).

Reference: `.serena/memories/riscure_ds1120a.md`

---

## Your Task: Implement Phase 3

### Step 1: Read the Full Specification
```bash
cat docs/BasicAppDataTypes/BAD_Phase3_RegPackage_r2.md
```

This contains:
- Complete `DataTypeSpec` implementation
- Complete `BasicAppsRegPackage` implementation
- TypeConverter dispatcher pattern (`_convert_to_raw()`)
- Example YAML format (corrected)
- Integration example
- Test specifications

### Step 2: Create Phase 3 Branch
```bash
git checkout feature/BAD-main
git checkout -b feature/BAD/P3
```

### Step 3: Implement `models/custom_inst/reg_package.py`

**Key Implementation Details:**

1. **TypeConverter Dispatcher** (CRITICAL):
   ```python
   def _convert_to_raw(self, dt_spec: DataTypeSpec) -> int:
       """No generic to_raw() exists - route by type category."""
       if dt_spec.datatype == BasicAppDataTypes.BOOLEAN:
           return 1 if dt_spec.default_value else 0

       # Voltage: use specific method (e.g., voltage_output_05v_s16_to_raw)
       if dt_spec.datatype.value.startswith('voltage_'):
           method_name = f"{dt_spec.datatype.value}_to_raw"
           converter_method = getattr(TypeConverter, method_name)
           return converter_method(dt_spec.default_value)

       # Time/duration: already raw (user provides nanoseconds/ms)
       if dt_spec.datatype.value.startswith('pulse_duration_'):
           return dt_spec.default_value

       raise ValueError(f"Unknown datatype: {dt_spec.datatype}")
   ```

2. **DataTypeSpec class** (see spec lines 73-165)
   - Extends BADRegisterConfig with UI metadata
   - Validators: VHDL-safe names, default value constraints, min/max range

3. **BasicAppsRegPackage class** (see spec lines 170-395)
   - Methods: `generate_mapping()`, `to_control_registers()`, `to_yaml()`, `from_yaml()`
   - Integration with Phase 2 BADRegisterMapper

**Commit:**
```bash
git add models/custom_inst/reg_package.py
git commit -m "feat(BAD/P3): Implement DataTypeSpec and BasicAppsRegPackage

Add type-safe register interface package:
- DataTypeSpec: Rich register type with UI metadata
- BasicAppsRegPackage: Complete register interface container
- TypeConverter dispatcher for raw value conversion
- Integration with Phase 2 BADRegisterMapper
- Export to MokuConfig.control_registers format

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 4: Create Example Interface YAML

**Create:** `examples/DS1140_PD_interface.yaml`

See spec (Deliverable 3) for complete YAML.

**Key points:**
- Uses only `BasicAppDataTypes` (no `unsigned_8` or legacy types)
- Voltage values in **millivolts** (e.g., `2400` = 2.4V)
- Time values in **nanoseconds/milliseconds** (human-friendly)
- Comments explain DS1120A hardware constraints

**Commit:**
```bash
git add examples/DS1140_PD_interface.yaml
git commit -m "feat(BAD/P3): Add DS1140_PD register interface example

Example register interface specification showing:
- 8 datatypes (booleans, timers, voltages) - all BasicAppDataTypes
- Automatic mapping: 8 types → 3 registers (57% savings)
- Human-friendly units (millivolts, nanoseconds)
- UI metadata for TUI generation
- DS1120A EMFI probe hardware context

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 5: Create Integration Example

**Create:** `examples/DS1140_PD_deployment.py`

See spec (Deliverable 4) for complete script.

Shows:
1. Load `BasicAppsRegPackage` from YAML
2. Generate register mapping
3. Export to `control_registers`
4. Create `MokuConfig` with exported values

**Commit:**
```bash
git add examples/DS1140_PD_deployment.py
git commit -m "feat(BAD/P3): Add MokuConfig integration example

Demonstrates BasicAppsRegPackage → MokuConfig workflow:
- Load register interface from YAML
- Generate register mapping
- Export to control_registers (dict[int, int])
- Integration with moku-models deployment

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 6: Write Unit Tests

**Create:** `python_tests/test_reg_package.py`

See spec (Deliverable 5) for complete test suite.

**Test classes:**
1. `TestDataTypeSpec` - validation tests
2. `TestBasicAppsRegPackage` - package tests
3. `TestMokuConfigIntegration` - integration tests

**Run tests:**
```bash
uv run pytest python_tests/test_reg_package.py -v
```

**Commit:**
```bash
git add python_tests/test_reg_package.py
git commit -m "test(BAD/P3): Add comprehensive tests for reg_package

Tests:
- DataTypeSpec validation (names, types, ranges)
- BasicAppsRegPackage (mapping, export, YAML)
- MokuConfig integration (control_registers)
- TypeConverter dispatcher

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 7: Delete Legacy Files (After Tests Pass)

```bash
git rm models/custom_inst/app_register.py
git rm models/custom_inst/custom_inst_app.py
git commit -m "refactor(BAD/P3): Remove legacy register models

Remove superseded files:
- app_register.py (RegisterType, AppRegister)
- custom_inst_app.py (CustomInstApp)

Replaced by BasicAppsRegPackage (Phase 3).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 8: Write Completion Summary

**Create:** `docs/BasicAppDataTypes/BAD_Phase3_COMPLETE.md`

**Template structure:**
```markdown
# BAD Phase 3 Complete: Register Interface Package

**Phase:** 3 of 6
**Status:** ✅ Complete
**Completion Date:** 2025-11-02
**Branch:** `feature/BAD/P3`
**Merge Commit:** [to be filled after merge]

## Summary
[Brief overview of what was accomplished]

## Deliverables
### 1. Core Package ✅
- DataTypeSpec implementation
- BasicAppsRegPackage implementation
- TypeConverter dispatcher

### 2. Examples ✅
- DS1140_PD_interface.yaml
- DS1140_PD_deployment.py

### 3. Tests ✅
- python_tests/test_reg_package.py
- [X/Y] tests passing

### 4. Legacy Cleanup ✅
- app_register.py deleted
- custom_inst_app.py deleted

## Architecture
[Integration flow diagram]

## Example Usage
[Code snippets]

## Test Results
[Test output]

## Files Changed
[List of added/deleted files]

## Handoff to Phase 4
[What Phase 4 needs]

## Lessons Learned
[Key insights from implementation]
```

**Commit:**
```bash
git add docs/BasicAppDataTypes/BAD_Phase3_COMPLETE.md
git commit -m "docs(BAD/P3): Add Phase 3 completion summary

Phase 3 complete:
- BasicAppsRegPackage implemented
- Integration with moku-models working
- Examples and tests complete
- Legacy code removed

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 9: Merge to feature/BAD-main

```bash
# Switch to feature branch
git checkout feature/BAD-main

# Merge with no-fast-forward (preserves phase history)
git merge --no-ff feature/BAD/P3 -m "Merge Phase 3: Register interface package

Complete Phase 3 implementation:
- DataTypeSpec with UI metadata
- BasicAppsRegPackage with mapping integration
- TypeConverter dispatcher for raw value conversion
- Export to MokuConfig.control_registers format
- Examples: DS1140_PD interface + deployment
- Comprehensive test suite
- Legacy cleanup (app_register.py, custom_inst_app.py removed)

Integration:
- Uses Phase 2 BADRegisterMapper internally
- Compatible with moku-models deployment
- No changes needed to tools/moku_go.py

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Verify merge
git log --oneline --graph -10
```

### Step 10: Update Master Orchestrator

Edit `docs/BasicAppDataTypes/BAD_MASTER_Orchestrator.md`:

Change Phase 3 row to:
```markdown
| 3 | [BAD_Phase3_RegPackage_r2.md](./BAD_Phase3_RegPackage_r2.md) | 🟢 Complete | `feature/BAD/P3` | ✅ | [BAD_Phase3_COMPLETE.md](./BAD_Phase3_COMPLETE.md) | `[commit_hash]` |
```

**Commit:**
```bash
git add docs/BasicAppDataTypes/BAD_MASTER_Orchestrator.md
git commit -m "docs(BAD): Update orchestrator - Phase 3 complete

Phase 3 status:
- Status: 🟢 Complete
- Merged: ✅
- Summary: BAD_Phase3_COMPLETE.md
- Commit: [hash]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Success Criteria Checklist

Before considering Phase 3 complete, verify:

- [ ] `models/custom_inst/reg_package.py` exists and implements:
  - [ ] DataTypeSpec class with all validators
  - [ ] BasicAppsRegPackage class with all methods
  - [ ] `_convert_to_raw()` dispatcher (NO generic TypeConverter.to_raw()!)
  - [ ] `to_control_registers()` returns dict[int, int]
  - [ ] YAML serialization works (to_yaml/from_yaml)

- [ ] Examples created:
  - [ ] examples/DS1140_PD_interface.yaml (uses only BasicAppDataTypes)
  - [ ] examples/DS1140_PD_deployment.py runs without errors

- [ ] Tests passing:
  - [ ] python_tests/test_reg_package.py exists
  - [ ] All tests pass: `uv run pytest python_tests/test_reg_package.py -v`

- [ ] Legacy removed:
  - [ ] models/custom_inst/app_register.py deleted
  - [ ] models/custom_inst/custom_inst_app.py deleted

- [ ] Documentation:
  - [ ] BAD_Phase3_COMPLETE.md written
  - [ ] Orchestrator updated

- [ ] Git workflow:
  - [ ] All commits follow naming convention `feat(BAD/P3): ...`
  - [ ] Merged to feature/BAD-main with --no-ff
  - [ ] feature/BAD/P3 branch preserved

---

## Quick Reference: Key Design Decisions

### 1. TypeConverter Integration
**Problem:** Spec assumed `TypeConverter.to_raw()` exists, but it doesn't.

**Solution:** Implement `_convert_to_raw()` dispatcher:
- Boolean → direct conversion (True=1, False=0)
- Voltage → route to specific method (e.g., `voltage_output_05v_s16_to_raw()`)
- Time/duration → already raw (user provides ns/ms values)

### 2. Human-Friendly Units
**Philosophy:** BAD uses human-friendly units throughout:
- Voltages in **millivolts** (2400 = 2.4V, NOT hex 0x3DCF)
- Times in **nanoseconds/milliseconds** (1000 = 1000ms, NOT cycles)
- Conversion to raw values happens internally

### 3. DS1140_PD Hardware Context
- **DS1120A probe:** Fixed 50ns EM pulse (hardware, not configurable)
- **firing_duration:** FSM state timing, NOT EM pulse width
- **intensity:** 0-3.3V control voltage (hardware-limited)
- **trigger_threshold:** ±25V ADC range (Moku Go/Lab/Pro)

### 4. No Legacy Types
- ❌ NO `unsigned_8` - use `pulse_duration_ns_u8` instead
- ❌ NO `counter_16bit` - use appropriate BasicAppDataTypes
- ✅ ONLY use types from `BasicAppDataTypes` enum

---

## Troubleshooting

### Import Errors
If you see `ImportError: cannot import name 'BasicAppDataTypes'`:
```bash
# Ensure basic-app-datatypes is installed
cd libs/basic-app-datatypes
uv pip install -e .
```

### Test Failures
```bash
# Run with verbose output
uv run pytest python_tests/test_reg_package.py -vv

# Run specific test
uv run pytest python_tests/test_reg_package.py::TestDataTypeSpec::test_valid_datatype_spec -v
```

### Git Branch Issues
```bash
# Check current branch
git branch --show-current

# Should be on feature/BAD/P3 during implementation
# Should be on feature/BAD-main after merge

# View branch structure
git log --oneline --graph feature/BAD-main -10
```

---

## Files You'll Create/Modify

**Create:**
1. `models/custom_inst/reg_package.py`
2. `examples/DS1140_PD_interface.yaml`
3. `examples/DS1140_PD_deployment.py`
4. `python_tests/test_reg_package.py`
5. `docs/BasicAppDataTypes/BAD_Phase3_COMPLETE.md`

**Delete:**
1. `models/custom_inst/app_register.py`
2. `models/custom_inst/custom_inst_app.py`

**Modify:**
1. `docs/BasicAppDataTypes/BAD_MASTER_Orchestrator.md` (update Phase 3 status)

---

## Expected Timeline

- Step 1-2 (Setup): 5 min
- Step 3 (Implement reg_package.py): 30 min
- Step 4-5 (Examples): 15 min
- Step 6 (Tests): 30 min
- Step 7 (Delete legacy): 5 min (after tests pass)
- Step 8-10 (Docs + merge): 15 min

**Total:** ~2 hours of focused work

---

## Ready to Start?

1. Read the full specification: `cat docs/BasicAppDataTypes/BAD_Phase3_RegPackage_r2.md`
2. Create branch: `git checkout -b feature/BAD/P3`
3. Start implementing: Begin with Step 3
4. Commit frequently (after each deliverable)
5. Run tests incrementally
6. Ask questions if anything is unclear

**You have everything you need. Good luck! 🚀**
