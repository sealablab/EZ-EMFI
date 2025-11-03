# Handoff to Fresh Context Window

**Date:** 2025-01-02
**From:** Planning session
**To:** Implementation session
**Task:** Execute Phase 3 of BasicAppDataTypes

---

## What Was Accomplished

### ✅ Planning & Design Complete
1. **Enhanced Phase 3 specification created:**
   - File: `docs/BasicAppDataTypes/BAD_Phase3_RegPackage_r1.md`
   - Complete technical specification
   - Integration with moku-models clarified
   - Clean separation of concerns defined

2. **Standalone execution prompt created:**
   - File: `docs/BasicAppDataTypes/P3_START_prompt.md`
   - Self-contained for fresh context window
   - Step-by-step implementation guide
   - All templates and examples included

3. **Architecture decisions finalized:**
   - **D1:** Hybrid file structure (interface + deployment separate)
   - **D2:** DataTypeSpec extends BADRegisterConfig semantically
   - **D3:** Medium UI metadata (display_name, units, min/max)
   - **D4:** Clean break - delete legacy code (no backward compat)
   - **D5:** Package handles interface only, MokuConfig handles deployment

---

## Git State

**Current branch:** `feature/BAD-main`

**Recent commits:**
```
65f9da3 docs(BAD/P3): Add standalone Phase 3 execution prompt
512e444 docs(BAD/P3): Add enhanced Phase 3 prompt with MokuConfig integration
43c66bb docs(BAD): Update orchestrator - Phase 2 complete
```

**Phase branches:**
- ✅ `feature/BAD/P1` (merged)
- ✅ `feature/BAD/P2` (merged)
- ⏳ `feature/BAD/P3` (ready to create)

**Phases complete:**
- ✅ Phase 1: Type System (23 types, 18 tests passing)
- ✅ Phase 2: Register Mapping (46/46 tests passing)
- ⏳ Phase 3: Register Interface Package (ready to implement)

---

## What to Do Next

### For Fresh Context Window:

1. **Load the execution prompt:**
   ```bash
   cat docs/BasicAppDataTypes/P3_START_prompt.md
   ```

2. **That prompt contains everything needed:**
   - Phase 1-2 summary
   - moku-models integration context
   - Complete implementation guide
   - Code templates
   - Examples
   - Tests
   - Success criteria

3. **Expected workflow:**
   ```bash
   # Step 1: Create phase branch
   git checkout feature/BAD-main
   git checkout -b feature/BAD/P3

   # Step 2: Implement (following P3_START_prompt.md)
   # - models/custom_inst/reg_package.py
   # - examples/DS1140_PD_interface.yaml
   # - examples/DS1140_PD_deployment.py
   # - python_tests/test_reg_package.py

   # Step 3: Delete legacy
   git rm models/custom_inst/app_register.py
   git rm models/custom_inst/custom_inst_app.py

   # Step 4: Test
   uv run pytest python_tests/test_reg_package.py -v

   # Step 5: Merge
   git checkout feature/BAD-main
   git merge --no-ff feature/BAD/P3
   ```

---

## Key Context for Fresh Session

### What Phase 3 Builds:
```python
# models/custom_inst/reg_package.py

class DataTypeSpec(BaseModel):
    """Rich register type with UI metadata."""
    name: str
    datatype: BasicAppDataTypes
    description: str = ""
    default_value: int | bool | None = None
    min_value: int | float | None = None
    max_value: int | float | None = None
    display_name: str | None = None
    units: str | None = None

class BasicAppsRegPackage(BaseModel):
    """Register interface specification."""
    app_name: str
    description: str = ""
    datatypes: List[DataTypeSpec]
    mapping_strategy: Literal["first_fit", "best_fit", "type_clustering"] = "best_fit"

    def generate_mapping(self) -> List[RegisterMapping]:
        # Uses Phase 2 BADRegisterMapper

    def to_control_registers(self) -> dict[int, int]:
        # Exports to MokuConfig format
```

### Integration Point:
```python
# Load register interface
package = BasicAppsRegPackage.from_yaml("DS1140_PD_interface.yaml")

# Export to MokuConfig
control_regs = package.to_control_registers()

# Use in deployment
config = MokuConfig(
    platform=MOKU_GO_PLATFORM,
    slots={
        1: SlotConfig(
            instrument='CloudCompile',
            bitstream='bitstream.tar',
            control_registers=control_regs  # ← BAD integration!
        )
    }
)
```

---

## Files That Already Exist (Don't recreate)

**Phase 1-2 (complete):**
- ✅ `libs/basic-app-datatypes/basic_app_datatypes/types.py`
- ✅ `libs/basic-app-datatypes/basic_app_datatypes/metadata.py`
- ✅ `libs/basic-app-datatypes/basic_app_datatypes/mapper.py`
- ✅ `models/custom_inst/bad_register_mapper.py`

**moku-models (submodule):**
- ✅ `moku-models/moku_models/moku_config.py`
- ✅ `moku-models/moku_models/platforms/*.py`

**Documentation:**
- ✅ `docs/BasicAppDataTypes/BAD_Phase3_RegPackage_r1.md` (spec)
- ✅ `docs/BasicAppDataTypes/P3_START_prompt.md` (execution guide)

---

## Success Criteria

Phase 3 is complete when:

1. ✅ `models/custom_inst/reg_package.py` implemented
2. ✅ Examples created (interface.yaml + deployment.py)
3. ✅ Tests passing (test_reg_package.py)
4. ✅ Legacy deleted (app_register.py, custom_inst_app.py)
5. ✅ Completion summary written (BAD_Phase3_COMPLETE.md)
6. ✅ Merged to feature/BAD-main with --no-ff
7. ✅ Orchestrator updated

---

## Quick Commands for Fresh Context

```bash
# Verify current state
git branch --show-current  # Should be: feature/BAD-main
git log --oneline -3       # Should see Phase 3 prompt commits

# Load execution guide
cat docs/BasicAppDataTypes/P3_START_prompt.md

# Start Phase 3
git checkout -b feature/BAD/P3

# After implementation, verify
uv run pytest python_tests/test_reg_package.py -v
git log --oneline --graph feature/BAD/P3

# Merge when done
git checkout feature/BAD-main
git merge --no-ff feature/BAD/P3 -m "Merge Phase 3: Register interface package"
```

---

## What NOT to Do

❌ Don't recreate Phase 1-2 code (already exists and tested)
❌ Don't modify moku-models (it's a submodule)
❌ Don't implement VHDL generation (that's Phase 4)
❌ Don't worry about backward compatibility (clean break)
❌ Don't create migration tools (not needed)

---

## Questions for Fresh Context?

If unclear during implementation:

1. **"What exactly should to_control_registers() return?"**
   → `dict[int, int]` mapping CR number → raw 32-bit value
   → See P3_START_prompt.md line 285-320 for implementation

2. **"How do I integrate with BADRegisterMapper?"**
   → Call `mapper.to_register_mappings()` in `generate_mapping()`
   → See P3_START_prompt.md line 240-260

3. **"What's the YAML format?"**
   → See example in P3_START_prompt.md line 400-510
   → Or check examples/DS1140_PD_interface.yaml after creation

4. **"Where do tests go?"**
   → `python_tests/test_reg_package.py`
   → See test template in P3_START_prompt.md line 620-870

---

## Estimated Time

**Total: ~2 hours**
- Implementation: 30 min (reg_package.py)
- Examples: 15 min (YAML + deployment script)
- Tests: 30 min (test_reg_package.py)
- Cleanup: 5 min (delete legacy)
- Documentation: 15 min (completion summary)
- Merge: 5 min

---

## Ready to Execute?

✅ Specification complete (`BAD_Phase3_RegPackage_r1.md`)
✅ Execution guide ready (`P3_START_prompt.md`)
✅ Git branch ready (`feature/BAD-main` clean)
✅ All dependencies available (Phase 1-2, moku-models)
✅ Success criteria defined

**Next step:** Open fresh context window and load `P3_START_prompt.md`

🚀 **You're ready to build Phase 3!**
