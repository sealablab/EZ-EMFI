# Phase 3 Execution Prompt: Register Interface Package

**Context:** You are implementing Phase 3 of the BasicAppDataTypes (BAD) system for the EZ-EMFI project. This is a fresh context window with everything needed to complete Phase 3.

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
    BOOLEAN = "boolean"
    UNSIGNED_8 = "unsigned_8"
    PULSE_DURATION_MS_U16 = "pulse_duration_ms_u16"
    PULSE_DURATION_NS_U8 = "pulse_duration_ns_u8"
    # ... (see libs/basic-app-datatypes/basic_app_datatypes/types.py for full list)

# libs/basic-app-datatypes/basic_app_datatypes/metadata.py
TYPE_REGISTRY: Dict[BasicAppDataTypes, TypeMetadata]
# Contains bit_width, min_value, max_value for each type
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

## Your Task: Implement Phase 3

### Step 1: Read the Specification
```bash
cat docs/BasicAppDataTypes/BAD_Phase3_RegPackage_r1.md
```

This contains:
- Complete `DataTypeSpec` implementation
- Complete `BasicAppsRegPackage` implementation
- Example YAML format
- Integration example
- Test specifications

### Step 2: Create Phase 3 Branch
```bash
git checkout feature/BAD-main
git checkout -b feature/BAD/P3
```

### Step 3: Implement `models/custom_inst/reg_package.py`

**Create the file with:**

1. **Imports:**
```python
from typing import List, Optional, Literal, Union
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, model_validator
import yaml

from basic_app_datatypes import (
    BasicAppDataTypes,
    TYPE_REGISTRY,
    RegisterMapper,
    RegisterMapping,
)
from .bad_register_mapper import BADRegisterMapper, BADRegisterConfig
```

2. **DataTypeSpec class** (see spec lines 73-165)
   - Extends BADRegisterConfig concept with UI metadata
   - Fields: name, datatype, description, default_value, min_value, max_value, display_name, units
   - Validators: VHDL-safe names, default value constraints, min/max range
   - Method: `to_bad_register_config()` for Phase 2 integration

3. **BasicAppsRegPackage class** (see spec lines 170-395)
   - Fields: app_name, description, datatypes, mapping_strategy
   - Methods:
     - `generate_mapping()` - uses BADRegisterMapper
     - `to_control_registers()` - exports to MokuConfig format (KEY METHOD!)
     - `to_yaml()` / `from_yaml()` - serialization

**Commit:**
```bash
git add models/custom_inst/reg_package.py
git commit -m "feat(BAD/P3): Implement DataTypeSpec and BasicAppsRegPackage

Add type-safe register interface package:
- DataTypeSpec: Rich register type with UI metadata
- BasicAppsRegPackage: Complete register interface container
- Integration with Phase 2 BADRegisterMapper
- Export to MokuConfig.control_registers format

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 4: Create Example Interface YAML

**Create:** `examples/DS1140_PD_interface.yaml`

See spec lines 400-510 for complete example.

**Key structure:**
```yaml
app_name: DS1140_PD
description: "EMFI probe driver register interface"
mapping_strategy: best_fit

datatypes:
  - name: arm_probe
    datatype: boolean
    description: "Arm the probe"
    default_value: false
    display_name: "Arm Probe"

  - name: intensity
    datatype: voltage_output_05v_s16
    description: "Output intensity"
    default_value: 2400  # mV
    min_value: 0
    max_value: 5000
    display_name: "Intensity"
    units: "mV"

  # ... 7 more datatypes (see spec)
```

**Commit:**
```bash
git add examples/DS1140_PD_interface.yaml
git commit -m "feat(BAD/P3): Add DS1140_PD register interface example

Example register interface specification showing:
- 9 datatypes (booleans, timers, voltages)
- Automatic mapping: 9 types → 3 registers (66.7% savings)
- UI metadata for TUI generation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 5: Create Integration Example

**Create:** `examples/DS1140_PD_deployment.py`

See spec lines 515-615 for complete script.

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

### Step 6: Delete Legacy Files (Clean Break)

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

### Step 7: Write Unit Tests

**Create:** `python_tests/test_reg_package.py`

See spec lines 620-870 for complete test suite.

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

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 8: Write Completion Summary

**Create:** `docs/BasicAppDataTypes/BAD_Phase3_COMPLETE.md`

**Template:**
```markdown
# BAD Phase 3 Complete: Register Interface Package

**Phase:** 3 of 6
**Status:** ✅ Complete
**Completion Date:** 2025-01-02
**Branch:** `feature/BAD/P3`
**Merge Commit:** [to be filled after merge]

---

## Summary

Phase 3 delivered `BasicAppsRegPackage` - a type-safe register interface specification that integrates with moku-models deployment system.

### Key Achievement: Clean Separation of Concerns
- **BasicAppsRegPackage:** Register interface only (platform-agnostic)
- **MokuConfig:** Deployment configuration (bitstreams, routing, platforms)
- **Integration:** via `to_control_registers()` method

---

## Deliverables

### 1. Core Package ✅
**Location:** `models/custom_inst/reg_package.py`

**Classes:**
- `DataTypeSpec`: Rich register type with UI metadata
  - Extends BADRegisterConfig semantically
  - Adds: min_value, max_value, display_name, units
  - Validates: VHDL-safe names, type constraints, ranges

- `BasicAppsRegPackage`: Complete register interface
  - Fields: app_name, description, datatypes, mapping_strategy
  - Methods: generate_mapping(), to_control_registers(), to_yaml(), from_yaml()
  - Integration: Uses BADRegisterMapper (Phase 2) internally

### 2. Examples ✅
- `examples/DS1140_PD_interface.yaml` - Register interface spec
- `examples/DS1140_PD_deployment.py` - MokuConfig integration

### 3. Tests ✅
- `python_tests/test_reg_package.py` - Comprehensive test suite
- [X/Y] tests passing

### 4. Legacy Cleanup ✅
Deleted:
- `models/custom_inst/app_register.py`
- `models/custom_inst/custom_inst_app.py`

---

## Architecture

### Integration Flow
```
BasicAppsRegPackage (YAML)
    ↓ from_yaml()
    ↓ generate_mapping() → uses BADRegisterMapper → RegisterMapper
    ↓ to_control_registers() → dict[int, int]
    ↓
SlotConfig.control_registers (moku-models)
    ↓
MokuConfig (deployment)
    ↓
tools/moku_go.py (hardware)
```

### Key Design Decisions

1. **Platform-Agnostic**
   - No bitstream paths (that's MokuConfig)
   - No MCC routing (that's MokuConnection)
   - Only register interface specification

2. **Builds on Phase 2**
   - Uses BADRegisterMapper internally
   - No duplication of mapping logic
   - Reuses all Phase 2 tests

3. **Clean Integration**
   - `to_control_registers()` bridges to moku-models
   - Compatible with existing tools/moku_go.py
   - No changes needed to deployment scripts

---

## Example Usage

### 1. Create Register Interface
```python
from models.custom_inst.reg_package import BasicAppsRegPackage, DataTypeSpec
from basic_app_datatypes import BasicAppDataTypes

package = BasicAppsRegPackage(
    app_name="DS1140_PD",
    description="EMFI probe driver",
    datatypes=[
        DataTypeSpec(
            name="intensity",
            datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
            default_value=2400,
            display_name="Intensity",
            units="mV"
        ),
        # ... more datatypes
    ]
)

# Save to YAML
package.to_yaml(Path("DS1140_PD_interface.yaml"))
```

### 2. Deploy to Hardware
```python
from moku_models import MokuConfig, SlotConfig, MOKU_GO_PLATFORM

# Load register interface
package = BasicAppsRegPackage.from_yaml("DS1140_PD_interface.yaml")

# Export control registers
control_regs = package.to_control_registers()
# Returns: {6: 0x09600000, 7: 0x3DCF0000, ...}

# Create deployment config
config = MokuConfig(
    platform=MOKU_GO_PLATFORM,
    slots={
        1: SlotConfig(
            instrument='CloudCompile',
            bitstream='path/to/bitstream.tar',
            control_registers=control_regs  # ← BAD-generated!
        )
    }
)

# Deploy using existing tools
# uv run python tools/moku_go.py deploy --device <ip> --config <config>
```

---

## Test Results

```
python_tests/test_reg_package.py::
  ✅ TestDataTypeSpec: [X] tests
  ✅ TestBasicAppsRegPackage: [Y] tests
  ✅ TestMokuConfigIntegration: [Z] tests

Total: [X+Y+Z] tests passing
```

---

## Files Changed

**Added:**
- `models/custom_inst/reg_package.py` (~400 lines)
- `examples/DS1140_PD_interface.yaml` (~100 lines)
- `examples/DS1140_PD_deployment.py` (~80 lines)
- `python_tests/test_reg_package.py` (~250 lines)

**Deleted:**
- `models/custom_inst/app_register.py`
- `models/custom_inst/custom_inst_app.py`

**Total:** ~830 lines added, ~550 lines deleted

---

## Handoff to Phase 4

**What Phase 4 Needs:**
- ✅ BasicAppsRegPackage API (complete)
- ✅ YAML loading utilities (complete)
- ✅ Example interfaces (DS1140_PD)
- ✅ Integration with moku-models (working)

**Phase 4 Tasks:**
- Update `tools/generate_custom_inst.py`
- Update VHDL Jinja2 templates
- Generate shim/main from BasicAppsRegPackage
- End-to-end VHDL generation

**Next Phase Branch:**
```bash
git checkout feature/BAD-main
git checkout -b feature/BAD/P4
```

---

## Lessons Learned

[To be filled during implementation]

---

**Implementation Complete:** Phase 3 delivers clean register interface abstraction with seamless moku-models integration.
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

# Update orchestrator
# Edit docs/BasicAppDataTypes/BAD_MASTER_Orchestrator.md
# Mark Phase 3 as complete
```

### Step 10: Update Master Orchestrator

Edit `docs/BasicAppDataTypes/BAD_MASTER_Orchestrator.md`:

Change line 20 from:
```markdown
| 3 | [BAD_Phase3_RegPackage.md](./BAD_Phase3_RegPackage.md) | 🔴 Not Started | `feature/BAD/P3` | ❌ | `BAD_Phase3_COMPLETE.md` | - |
```

To:
```markdown
| 3 | [BAD_Phase3_RegPackage_r1.md](./BAD_Phase3_RegPackage_r1.md) | 🟢 Complete | `feature/BAD/P3` | ✅ | [BAD_Phase3_COMPLETE.md](./BAD_Phase3_COMPLETE.md) | `[commit_hash]` |
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
  - [ ] to_control_registers() returns dict[int, int]
  - [ ] YAML serialization works (to_yaml/from_yaml)

- [ ] Examples created:
  - [ ] examples/DS1140_PD_interface.yaml
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

## Quick Reference: Key APIs

### DataTypeSpec
```python
DataTypeSpec(
    name: str,                    # VHDL-safe identifier
    datatype: BasicAppDataTypes,  # Enum value
    description: str = "",
    default_value: int | bool | None = None,
    min_value: int | float | None = None,
    max_value: int | float | None = None,
    display_name: str | None = None,
    units: str | None = None
)
```

### BasicAppsRegPackage
```python
package = BasicAppsRegPackage(
    app_name: str,
    description: str = "",
    datatypes: List[DataTypeSpec],
    mapping_strategy: "first_fit" | "best_fit" | "type_clustering" = "best_fit"
)

# Generate mapping
mappings: List[RegisterMapping] = package.generate_mapping()

# Export to MokuConfig
control_regs: dict[int, int] = package.to_control_registers()

# YAML I/O
package.to_yaml(Path("interface.yaml"))
package = BasicAppsRegPackage.from_yaml(Path("interface.yaml"))
```

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
- Step 6 (Delete legacy): 5 min
- Step 7 (Tests): 30 min
- Step 8-10 (Docs + merge): 15 min

**Total:** ~2 hours of focused work

---

## Ready to Start?

1. Read the full specification: `cat docs/BasicAppDataTypes/BAD_Phase3_RegPackage_r1.md`
2. Create branch: `git checkout -b feature/BAD/P3`
3. Start implementing: Begin with Step 3
4. Commit frequently
5. Run tests often
6. Ask questions if anything is unclear

**You have everything you need. Good luck! 🚀**
