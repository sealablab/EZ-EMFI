# Phase 5 START Prompt: Comprehensive Testing Suite

**Purpose:** Load this prompt in a fresh Claude session to begin Phase 5 implementation
**Phase:** 5 of 6 (Testing and Validation)
**Branch:** `feature/BAD/P5`
**Prerequisites:** Phase 1-4 complete and merged
**Full Spec:** [BAD_Phase5_Testing_r2.md](./BAD_Phase5_Testing_r2.md)

---

## Quick Start

```bash
# Ensure you're on the Phase 5 branch
git checkout feature/BAD/P5

# Or create it if starting fresh
git checkout feature/BAD-main
git checkout -b feature/BAD/P5

# Verify prerequisites
cat docs/BasicAppDataTypes/BAD_Phase4_COMPLETE.md
```

---

## Your Mission

Implement comprehensive testing for BasicAppDataTypes (BAD) system.

**What's already done:**
- ✅ Phase 1-4: Type system, register mapper, package model, code generator
- ✅ Core library tests: 44 tests passing in `libs/basic-app-datatypes/tests/`
- ✅ Frozen VHDL utilities: `shared/custom_inst/vhdl/` (v1.0.0)
- ✅ DS1140_PD test case: Generated VHDL from Phase 4

**What Phase 5 needs:**
- ❌ Code generation tests (`python_tests/test_code_generation.py`)
- ❌ Integration tests (`python_tests/test_bad_integration.py`)
- ❌ CocotB tests for generated VHDL (`tests/test_bad_generated_vhdl_progressive.py`)
- ❌ Performance benchmarks (`python_tests/test_bad_benchmarks.py`)
- 🟡 Expand existing integration tests
- ✅ Test runner script (`run_bad_tests.sh`)
- ✅ Coverage reporting

---

## Essential Context Files

**Read these FIRST:**

1. **Phase 5 Full Spec** (this is your bible)
   ```bash
   cat docs/BasicAppDataTypes/BAD_Phase5_Testing_r2.md
   ```

2. **Phase 4 Completion Summary** (what you're testing)
   ```bash
   cat docs/BasicAppDataTypes/BAD_Phase4_COMPLETE.md
   ```

3. **CocotB Testing Patterns** (critical for VHDL tests)
   ```bash
   cat docs/VHDL_COCOTB_LESSONS_LEARNED.md
   cat tests/test_base.py
   cat tests/test_handshake_shim_progressive.py  # Example pattern
   ```

4. **Project Structure** (understand test organization)
   ```bash
   cat python_tests/README.md
   cat tests/run.py | head -100
   ```

5. **Existing Test Examples**
   ```bash
   # Core library tests (reference for patterns)
   cat libs/basic-app-datatypes/tests/test_basic_app_datatypes.py | head -100
   cat libs/basic-app-datatypes/tests/test_mapper.py | head -100

   # Python integration tests (expand these)
   cat python_tests/test_bad_register_mapper.py | head -100
   cat python_tests/test_reg_package.py | head -100
   ```

---

## Test Structure Overview (CRITICAL)

**Three test directories:**

```
tests/              → CocotB VHDL simulation tests (GHDL)
python_tests/       → Python unit/integration tests (pytest)
libs/.../tests/     → Core BAD library tests (standalone)
```

**Why separate?**
- CocotB test discovery conflicts with pytest-only tests
- Different execution contexts (hardware sim vs pure Python)
- Clean separation of concerns

**Key patterns:**
- CocotB uses `TestBase` with progressive levels (P1/P2/P3)
- Python tests use standard pytest
- All use Pydantic models extensively

---

## Implementation Checklist

### Step 1: Code Generation Tests (Python)

**File:** `python_tests/test_code_generation.py` (NEW)

**What to test:**
- [ ] Generator imports and basic execution
- [ ] YAML parsing and validation
- [ ] Template rendering (shim + main)
- [ ] Platform constant injection (CLK_FREQ_HZ for Go/Lab/Pro/Delta)
- [ ] Type conversion function selection (voltage/time/boolean)
- [ ] Register mapping accuracy
- [ ] Default value initialization

**Reference:**
- Phase 4 generator: `tools/generate_custom_inst_v2.py`
- Templates: `shared/custom_inst/templates/custom_inst_*_template_v2.vhd`
- Example YAML: `examples/DS1140_PD_interface.yaml`

**See:** BAD_Phase5_Testing_r2.md Section 5.1.A for full test skeleton

### Step 2: Integration Tests (Python)

**File:** `python_tests/test_bad_integration.py` (NEW)

**What to test:**
- [ ] Full pipeline: YAML → Package → Mapping → VHDL
- [ ] DS1140_PD migration validation (8 datatypes → 3 registers)
- [ ] MokuConfig export (`to_control_registers()`)
- [ ] Multi-platform generation (Go/Lab/Pro/Delta)
- [ ] Efficiency metrics (bit utilization > 60%)

**Key assertion:** DS1140_PD should use ≤3 registers (vs 7 manual registers = 57% savings)

**See:** BAD_Phase5_Testing_r2.md Section 5.1.B for full test skeleton

### Step 3: CocotB VHDL Tests

**File:** `tests/test_bad_generated_vhdl_progressive.py` (NEW)

**What to test (P1 - Essential):**
- [ ] Voltage type extraction (signed 16-bit)
- [ ] Boolean type extraction (single bit)
- [ ] Handshaking protocol (ready_for_updates)
- [ ] Default values on reset

**What to test (P2 - Comprehensive):**
- [ ] Multi-type register packing
- [ ] Time type extraction
- [ ] All 8 DS1140_PD signals

**DUT:** `generated/DS1140_PD/DS1140_PD_custom_inst_shim.vhd`

**Pattern:** Inherit from `TestBase`, implement `run_p1_basic()` and `run_p2_intermediate()`

**Critical:** Follow patterns from `test_handshake_shim_progressive.py`

**See:** BAD_Phase5_Testing_r2.md Section 5.2 for full test skeleton

### Step 4: Expand Existing Tests

**Files to expand:**

A. `python_tests/test_bad_register_mapper.py`
   - [ ] Edge cases (overflow, single register)
   - [ ] Strategy comparison (first_fit vs best_fit)
   - [ ] Mapping report formats (ASCII, markdown, JSON)

B. `python_tests/test_reg_package.py`
   - [ ] YAML v2.0 parsing edge cases
   - [ ] Validation rules (duplicate names, invalid datatypes)
   - [ ] MokuConfig export
   - [ ] UI metadata validation

### Step 5: Performance Benchmarks

**File:** `python_tests/test_bad_benchmarks.py` (NEW)

**What to benchmark:**
- [ ] Mapping algorithm performance (10, 100 datatypes)
- [ ] Type conversion throughput (voltage, time)
- [ ] VHDL generation speed

**Framework:** `pytest-benchmark`

**See:** BAD_Phase5_Testing_r2.md Section 5.3 for full test skeleton

### Step 6: Test Runner Script

**File:** `run_bad_tests.sh` (NEW)

**What it does:**
1. Run core library tests (`libs/basic-app-datatypes/tests/`)
2. Run Python integration tests (`python_tests/`)
3. Run CocotB VHDL tests (`tests/`)
4. Run performance benchmarks
5. Report summary

**See:** BAD_Phase5_Testing_r2.md Section 5.4 for full script

### Step 7: Test Configuration

**Update:** `tests/test_configs.py`

Add BAD test configuration:
```python
"bad_generated_vhdl": {
    "module": "test_bad_generated_vhdl_progressive",
    "toplevel": "DS1140_PD_custom_inst_shim",
    "sources": [
        "generated/DS1140_PD/DS1140_PD_custom_inst_shim.vhd",
        "shared/custom_inst/vhdl/basic_app_types_pkg.vhd",
        "shared/custom_inst/vhdl/basic_app_voltage_pkg.vhd",
        "shared/custom_inst/vhdl/basic_app_time_pkg.vhd",
    ],
    "category": "bad",
},
```

---

## Platform-Specific Testing (CRITICAL)

BasicAppDataTypes MUST work on all 4 Moku platforms:

| Platform | Clock | Test Focus |
|----------|-------|------------|
| Moku:Go | 125 MHz | Default, DS1140_PD reference |
| Moku:Lab | 500 MHz | Time conversion at 4× clock |
| Moku:Pro | 1.25 GHz | Time conversion at 10× clock |
| Moku:Delta | 5 GHz | Time conversion at 40× clock |

**Key tests:**
- CLK_FREQ_HZ generic matches platform
- Time conversion functions reference correct clock
- Same YAML generates correct VHDL for each platform

**See:** BAD_Phase5_Testing_r2.md Section "Platform-Specific Testing Requirements"

---

## Running Tests During Development

```bash
# Core library tests (should already pass)
cd libs/basic-app-datatypes
uv run pytest tests/ -v
cd ../..

# Python integration tests (as you add them)
PYTHONPATH=libs/basic-app-datatypes:. uv run pytest python_tests/test_code_generation.py -v

# CocotB tests (after creating them)
python tests/run.py bad_generated_vhdl

# All tests together
./run_bad_tests.sh

# With coverage
PYTHONPATH=libs/basic-app-datatypes:. uv run pytest python_tests/ \
  --cov=models.custom_inst \
  --cov=tools.generate_custom_inst_v2 \
  --cov-report=html
```

---

## Key Design Patterns

### 1. Pydantic Models Everywhere

All configuration uses Pydantic for validation:
```python
from models.custom_inst.reg_package import BasicAppsRegPackage, DataTypeSpec
from models.custom_inst.bad_register_mapper import BADRegisterMapper
from basic_app_datatypes import BasicAppDataTypes

# Create package
package = BasicAppsRegPackage(
    app_name="TestApp",
    platform="moku_go",
    datatypes=[
        DataTypeSpec(
            name="intensity",
            datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
            default_value=2400
        )
    ]
)

# Generate mapping
mapper = BADRegisterMapper.from_package(package)
mapping = mapper.generate_mapping()

# Export to MokuConfig
control_regs = package.to_control_registers()
```

### 2. Progressive CocotB Tests

```python
from test_base import TestBase, VerbosityLevel

class MyTests(TestBase):
    def __init__(self, dut):
        super().__init__(dut, "MyModule")

    async def run_p1_basic(self):
        """P1 essential tests"""
        await self.setup()
        await self.test("Basic operation", self.test_basic)

    async def test_basic(self):
        """Individual test implementation"""
        self.log("Testing...", VerbosityLevel.NORMAL)
        assert self.dut.signal.value == expected
```

### 3. Test Data Accuracy

**CRITICAL:** Match VHDL integer arithmetic exactly:
```python
# ❌ WRONG - Python rounds, VHDL truncates
expected = int((50 / 100.0) * 0xFFFF + 0.5)  # = 32768

# ✅ CORRECT - Matches VHDL truncation
expected = int((50 / 100.0) * 0xFFFF)  # = 32767
```

---

## Success Criteria

Phase 5 is complete when:

- [ ] All new test files created (4 files)
- [ ] Existing tests expanded (2 files)
- [ ] Test runner script working (`run_bad_tests.sh`)
- [ ] All tests passing:
  - [ ] Core library: 44 tests ✅
  - [ ] Code generation: 10+ tests
  - [ ] Integration: 10+ tests
  - [ ] CocotB VHDL: P1 + P2 tests
  - [ ] Benchmarks: 5+ benchmarks
- [ ] DS1140_PD migration validated (3 regs vs 7 manual)
- [ ] Multi-platform tests passing (Go/Lab/Pro/Delta)
- [ ] Coverage > 90% for new code
- [ ] Phase completion summary written (`BAD_Phase5_COMPLETE.md`)

---

## Completion: Phase Summary

When all tests pass, create `docs/BasicAppDataTypes/BAD_Phase5_COMPLETE.md`:

**Template:**
```markdown
# Phase 5 Completion Summary: Comprehensive Testing Suite

**Branch:** `feature/BAD/P5`
**Status:** ✅ Complete
**Date:** YYYY-MM-DD

## Test Results

### Core Library Tests
- Location: `libs/basic-app-datatypes/tests/`
- Tests: 44
- Status: ✅ All passing

### Python Integration Tests
- Location: `python_tests/`
- Tests: XX
- Files: test_code_generation.py, test_bad_integration.py, test_bad_benchmarks.py
- Coverage: XX%
- Status: ✅ All passing

### CocotB VHDL Tests
- Location: `tests/`
- Tests: test_bad_generated_vhdl_progressive.py
- Levels: P1 (essential), P2 (comprehensive)
- Status: ✅ All passing

### DS1140_PD Validation
- Datatypes: 8
- Registers used: 3 (vs 7 manual = 57% savings)
- Bit efficiency: XX%
- Status: ✅ Validated

### Multi-Platform Validation
- Platforms tested: Moku:Go, Moku:Lab, Moku:Pro, Moku:Delta
- Clock frequencies: 125 MHz, 500 MHz, 1.25 GHz, 5 GHz
- Status: ✅ All platforms validated

## Performance Benchmarks
[Results from pytest-benchmark]

## Key Findings
[Any issues discovered during testing]

## Handoff to Phase 6
Ready for documentation phase. All tests passing, coverage XX%.
```

---

## Git Workflow

```bash
# Commit frequently as you implement
git add python_tests/test_code_generation.py
git commit -m "feat(BAD/P5): Add code generation tests"

git add tests/test_bad_generated_vhdl_progressive.py
git commit -m "feat(BAD/P5): Add CocotB tests for generated VHDL"

# When phase complete
git add .
git commit -m "feat(BAD/P5): Complete Phase 5 - Comprehensive testing suite"

# Create completion summary
vim docs/BasicAppDataTypes/BAD_Phase5_COMPLETE.md
git add docs/BasicAppDataTypes/BAD_Phase5_COMPLETE.md
git commit -m "docs(BAD/P5): Add Phase 5 completion summary"

# Merge to feature branch
git checkout feature/BAD-main
git merge --no-ff feature/BAD/P5 -m "Merge Phase 5: Testing and validation"

# Update orchestrator
vim docs/BasicAppDataTypes/BAD_MASTER_Orchestrator.md
# Update Phase 5 status to 🟢 Complete
git add docs/BasicAppDataTypes/BAD_MASTER_Orchestrator.md
git commit -m "docs(BAD): Update orchestrator - Phase 5 complete"
```

---

## Common Pitfalls

**1. Test Discovery Conflicts**
- Don't mix CocotB and pytest in same directory
- Use `python_tests/` for pure Python tests

**2. Import Paths**
- Use `PYTHONPATH=libs/basic-app-datatypes:.` for Python tests
- CocotB tests auto-add `tests/` to path

**3. VHDL Simulation**
- Always follow TestBase pattern for CocotB
- Clear all control signals between tests (signal persistence)
- Match VHDL arithmetic exactly (truncation not rounding)

**4. Platform Testing**
- Test all 4 platforms, not just Moku:Go
- Time conversions depend on clock frequency
- CLK_FREQ_HZ must match platform specs

**5. Generator Testing**
- Test YAML → VHDL pipeline end-to-end
- Verify generated VHDL matches RegisterMapper output
- Test platform constant injection

---

## Questions?

1. **"Where do I start?"**
   → Start with `python_tests/test_code_generation.py` (easiest)

2. **"How do I run a single test?"**
   → `PYTHONPATH=libs/basic-app-datatypes:. uv run pytest python_tests/test_code_generation.py::test_name -v`

3. **"CocotB test failing?"**
   → Check `docs/VHDL_COCOTB_LESSONS_LEARNED.md` for common issues

4. **"Need platform specs?"**
   → See `moku-models/docs/MOKU_PLATFORM_SPECIFICATIONS.md`

5. **"What's the TestBase pattern?"**
   → See `tests/test_base.py` and `tests/test_handshake_shim_progressive.py`

---

## Ready to Start?

1. Read `docs/BasicAppDataTypes/BAD_Phase5_Testing_r2.md` (full spec)
2. Read Phase 4 completion summary (what you're testing)
3. Read CocotB lessons learned (critical patterns)
4. Start with `python_tests/test_code_generation.py`
5. Commit frequently, test often
6. Ask questions if stuck!

**Good luck! Phase 5 validates all the great work from Phases 1-4. Let's ensure BasicAppDataTypes is rock solid! 🧪**

---

**Last Updated:** 2025-11-03
**For Details:** [BAD_Phase5_Testing_r2.md](./BAD_Phase5_Testing_r2.md)
**Master Tracker:** [BAD_MASTER_Orchestrator.md](./BAD_MASTER_Orchestrator.md)
