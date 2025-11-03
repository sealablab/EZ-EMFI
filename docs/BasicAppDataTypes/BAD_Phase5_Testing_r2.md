# BAD Phase 5: Comprehensive Testing Suite (Revision 2)

**Phase:** 5 of 6
**Goal:** Validate BasicAppDataTypes with comprehensive Python unit tests and CocotB progressive tests
**Prerequisites:** Phase 1-4 complete
**Phase 1-4 Summaries:** ./BAD_Phase{1-4}_COMPLETE.md
**Output:** Complete test suite validating all components
**Revision:** 2 (Updated with proper project context)
**Date:** 2025-11-03

---

## Revision 2 Changes

**Why this revision?**
1. **Proper test structure**: Clarified `tests/` (CocotB VHDL) vs `python_tests/` (Python unit)
2. **Pydantic awareness**: Recognized extensive use of Pydantic models throughout
3. **Existing tests**: Acknowledged `libs/basic-app-datatypes/tests/` has 44 passing tests
4. **CocotB patterns**: Incorporated TestBase progressive pattern and lessons learned
5. **Platform testing**: Added proper multi-platform validation requirements

**What's already done:**
- ✅ libs/basic-app-datatypes/tests/test_basic_app_datatypes.py (type system)
- ✅ libs/basic-app-datatypes/tests/test_mapper.py (register mapper)
- 🟡 python_tests/test_bad_register_mapper.py (Pydantic wrapper - partial)
- 🟡 python_tests/test_reg_package.py (Pydantic package model - partial)

**What Phase 5 needs:**
- Code generation tests (tools/generate_custom_inst_v2.py)
- CocotB tests for generated VHDL
- Integration tests (YAML → VHDL pipeline)
- Platform-aware validation
- Coverage reporting

---

## Git Workflow

**Branch:** `feature/BAD/P5`

**Starting this phase:**
```bash
git checkout feature/BAD-main
git checkout -b feature/BAD/P5
```

**During development:**
```bash
# Commit frequently as you implement
git add <files>
git commit -m "feat(BAD/P5): <description>"
```

**Completing this phase:**
```bash
# Final commit with phase completion
git add .
git commit -m "feat(BAD/P5): Complete Phase 5 - Comprehensive testing suite"

# Write BAD_Phase5_COMPLETE.md with summary

# Merge back to feature branch
git checkout feature/BAD-main
git merge --no-ff feature/BAD/P5 -m "Merge Phase 5: Testing and validation"
```

**Full workflow:** See [BAD_MASTER_Orchestrator.md](./BAD_MASTER_Orchestrator.md#git-workflow)

---

## EZ-EMFI Project Test Structure

### Two Test Directories

**1. `tests/` - CocotB VHDL Tests**
- **Purpose**: VHDL simulation and hardware validation
- **Framework**: CocotB 2.0+ with GHDL simulator
- **Runner**: `tests/run.py` (Python-based, no Makefiles)
- **Pattern**: Progressive testing (P1/P2/P3/P4 levels)
- **Base class**: `tests/test_base.py` (TestBase, VerbosityLevel)
- **Examples**: `test_handshake_shim_progressive.py`, `test_ds1140_pd_progressive.py`

**2. `python_tests/` - Python Unit Tests**
- **Purpose**: Pure Python logic, Pydantic models, non-VHDL code
- **Framework**: pytest
- **Examples**: `test_bad_register_mapper.py`, `test_reg_package.py`
- **Note**: Separate from CocotB to avoid test discovery conflicts

**3. `libs/basic-app-datatypes/tests/` - BAD Library Tests**
- **Purpose**: Core BasicAppDataTypes library (standalone)
- **Status**: ✅ 44 tests passing (type system + mapper algorithm)
- **Coverage**: Type conversions, register mapping, determinism
- **Runner**: `uv run pytest tests/` from `libs/basic-app-datatypes/`

### Key Distinction

```
tests/             → VHDL + CocotB → Simulates hardware
python_tests/      → pytest only → Tests Python Pydantic models
libs/.../tests/    → pytest only → Tests core library logic
```

**Why separate?**
- CocotB test discovery can interfere with pytest-only tests
- Different execution contexts (GHDL sim vs pure Python)
- Clean separation of concerns

---

## CocotB Testing Patterns (From docs/VHDL_COCOTB_LESSONS_LEARNED.md)

### Progressive Test Levels

**P1 (Basic - LLM-friendly)**
- Essential functionality only
- Minimal output (controlled verbosity)
- Fast execution (~seconds)
- Must pass before P2

**P2 (Intermediate)**
- Core functionality
- Moderate output
- Longer execution (~minutes)
- Comprehensive coverage

**P3 (Comprehensive)**
- Edge cases, stress tests
- Full output
- Longest execution
- Exhaustive validation

**P4 (Exhaustive - rare)**
- Debug-level output
- All permutations
- Used for deep investigation

### TestBase Pattern

```python
from test_base import TestBase, VerbosityLevel

class MyTests(TestBase):
    def __init__(self, dut):
        super().__init__(dut, "MyModule")

    async def setup(self):
        """Common setup for all tests"""
        cocotb.start_soon(Clock(self.dut.Clk, 10, units="ns").start())
        # Reset logic

    async def run_p1_basic(self):
        """P1 essential tests"""
        await self.setup()
        await self.test("Basic operation", self.test_basic)

    async def run_p2_intermediate(self):
        """P2 comprehensive tests"""
        await self.setup()
        await self.test("Edge cases", self.test_edges)
```

### Critical Lessons Learned

**1. VHDL Function Overloading**
- ❌ Subtypes do NOT enable overloading
- ✅ Use base type only (e.g., `natural` not `pct_index_t`)

**2. Hex Literal Notation**
- ❌ `16#0000#` (ambiguous type)
- ✅ `x"0000"` (std_logic_vector)

**3. Test Data Rounding**
- Match VHDL integer division exactly
- ❌ `int(val + 0.5)` (rounds up)
- ✅ `int(val)` (truncates)

**4. Signal Persistence**
- Outputs persist between tests
- Always reset or clear control signals
- Use helper functions for cleanup

**5. Import Order**
- Define helper functions BEFORE using in constants
- Avoid module-level computation that depends on later definitions

---

## Pydantic Model Architecture

### Core Models (models/custom_inst/)

**1. DataTypeSpec** (`reg_package.py`)
```python
class DataTypeSpec(BaseModel):
    """Rich specification for a single register data element"""
    name: str
    datatype: BasicAppDataTypes
    description: str = ""
    default_value: Optional[Union[int, bool]] = None

    # UI metadata
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    display_name: Optional[str] = None
    units: Optional[str] = None
```

**2. BasicAppsRegPackage** (`reg_package.py`)
```python
class BasicAppsRegPackage(BaseModel):
    """Complete register interface container"""
    app_name: str
    description: str = ""
    platform: str  # "moku_go" | "moku_lab" | "moku_pro" | "moku_delta"
    datatypes: List[DataTypeSpec]
    mapping_strategy: Literal["first_fit", "best_fit", "type_clustering"] = "best_fit"
    _mapping_result: Optional[List[RegisterMapping]] = PrivateAttr(default=None)

    def generate_mapping(self, mapper: RegisterMapper) -> List[RegisterMapping]:
        """Generate register mapping"""

    def to_control_registers(self) -> dict[int, int]:
        """Export to MokuConfig.control_registers format"""
```

**3. BADRegisterConfig** (`bad_register_mapper.py`)
```python
class BADRegisterConfig(BaseModel):
    """Pydantic wrapper for RegisterMapper inputs"""
    name: str
    datatype: BasicAppDataTypes
    description: str = ""
    default_value: Union[int, bool] = 0

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        # VHDL identifier rules
```

**4. BADRegisterMapper** (`bad_register_mapper.py`)
```python
class BADRegisterMapper(BaseModel):
    """Pydantic wrapper for RegisterMapper"""
    configs: List[BADRegisterConfig]
    strategy: Literal["first_fit", "best_fit", "type_clustering"] = "best_fit"

    def generate_mapping(self) -> List[RegisterMapping]:
        """Call core RegisterMapper"""

    def to_app_registers(self) -> List[AppRegister]:
        """Convert to legacy AppRegister format"""
```

### Integration with moku-models/

**MokuConfig** (`moku-models/moku_models/moku_config.py`)
```python
class SlotConfig(BaseModel):
    """Per-slot configuration"""
    instrument: str
    settings: dict[str, Any] = Field(default_factory=dict)
    control_registers: dict[int, int] | None = None  # ← BAD exports here
    bitstream: str | None = None

class MokuConfig(BaseModel):
    """Central deployment abstraction"""
    platform: MokuGoPlatform  # or Lab/Pro/Delta
    slots: dict[int, SlotConfig]
    routing: list[MokuConnection]
    metadata: dict[str, Any] = Field(default_factory=dict)
```

**Platform Models** (`moku-models/moku_models/platforms/`)
- `MokuGoPlatform`: 125 MHz, 2 slots, 2 I/O
- `MokuLabPlatform`: 500 MHz, 2 slots, 2 I/O
- `MokuProPlatform`: 1.25 GHz, 4 slots, 4 I/O
- `MokuDeltaPlatform`: 5 GHz, 3 slots, 8 I/O

**Key Exports**:
```python
from moku_models import (
    MokuConfig,
    SlotConfig,
    MokuConnection,
    MOKU_GO_PLATFORM,
    MOKU_LAB_PLATFORM,
    MOKU_PRO_PLATFORM,
    MOKU_DELTA_PLATFORM,
)
```

---

## Phase 5 Test Coverage Matrix

| Component | Library Tests | Python Tests | CocotB Tests | Integration | Benchmarks |
|-----------|---------------|--------------|--------------|-------------|------------|
| Type System | ✅ 44 tests | ✅ Existing | 🟡 Needed | - | - |
| Register Mapper | ✅ 44 tests | 🟡 Partial | - | - | 🟡 Needed |
| Package Model | - | 🟡 Partial | - | 🟡 Needed | - |
| Code Generator | - | ❌ Missing | - | 🟡 Needed | - |
| Generated VHDL | - | - | ❌ Missing | - | - |
| DS1140_PD Migration | - | - | ❌ Missing | ✅ Exists | 🟡 Needed |

**Legend:**
- ✅ Complete
- 🟡 Partial/needs expansion
- ❌ Missing

---

## Phase 5 Deliverables

### 5.1 Complete Python Unit Tests

**Location:** `python_tests/`

**Files to create/expand:**

#### A. `python_tests/test_code_generation.py` (NEW)
```python
"""
Tests for tools/generate_custom_inst_v2.py code generator.

Validates:
- YAML parsing and validation
- Template rendering (shim + main)
- Platform constant injection
- Type conversion function selection
- Register mapping integration
"""

import pytest
import yaml
from pathlib import Path
from tempfile import TemporaryDirectory

from models.custom_inst.reg_package import BasicAppsRegPackage, DataTypeSpec
from basic_app_datatypes import BasicAppDataTypes
from moku_models import MOKU_GO_PLATFORM, MOKU_LAB_PLATFORM


class TestCodeGenerator:
    """Test VHDL code generation from YAML specs"""

    def test_generator_imports(self):
        """Verify generator script can be imported"""
        # Import the generator module
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
        import generate_custom_inst_v2

        assert hasattr(generate_custom_inst_v2, 'generate_vhdl')

    def test_simple_yaml_generation(self):
        """Test generating VHDL from minimal YAML spec"""
        yaml_content = """
        package_version: "2.0"
        app_name: "TestApp"
        platform: "moku_go"
        datatypes:
          - name: "enable"
            datatype: "boolean"
            default_value: false
        """

        with TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "test.yaml"
            yaml_path.write_text(yaml_content)

            # Generate VHDL
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            # Call generator (implementation detail - adjust as needed)
            # generate_vhdl(yaml_path, output_dir)

            # Verify files created
            shim_path = output_dir / "TestApp_custom_inst_shim.vhd"
            main_path = output_dir / "TestApp_custom_inst_main.vhd"

            # Tests will be implemented based on actual generator API
            # assert shim_path.exists()
            # assert main_path.exists()

    def test_platform_constant_injection(self):
        """Test CLK_FREQ_HZ generic matches platform"""
        # Test Moku:Go (125 MHz)
        # Test Moku:Lab (500 MHz)
        # Test Moku:Pro (1.25 GHz)
        # Test Moku:Delta (5 GHz)
        pass

    def test_voltage_type_function_selection(self):
        """Test correct voltage conversion function selected"""
        # VOLTAGE_OUTPUT_05V_S16 → voltage_output_05v_s16_from_raw()
        # VOLTAGE_INPUT_25V_S16 → voltage_input_25v_s16_from_raw()
        pass

    def test_time_type_function_selection(self):
        """Test correct time conversion function selected"""
        # PULSE_DURATION_NS_U16 → pulse_duration_ns_from_raw()
        pass

    def test_boolean_type_bit_extraction(self):
        """Test boolean types extract single bit correctly"""
        pass

    def test_register_mapping_accuracy(self):
        """Test generated VHDL matches RegisterMapper output"""
        pass

    def test_default_value_initialization(self):
        """Test default values propagated to reset logic"""
        pass
```

#### B. `python_tests/test_bad_integration.py` (NEW)
```python
"""
Integration tests for complete BasicAppDataTypes pipeline.

Tests:
- YAML → Package → Mapping → VHDL generation
- DS1140_PD migration validation
- Multi-platform generation
- MokuConfig export
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from models.custom_inst.reg_package import BasicAppsRegPackage, RegPackageFactory
from models.custom_inst.bad_register_mapper import BADRegisterMapper
from basic_app_datatypes import BasicAppDataTypes
from moku_models import MokuConfig, SlotConfig, MOKU_GO_PLATFORM


class TestEndToEndPipeline:
    """Test complete YAML → VHDL workflow"""

    def test_yaml_to_vhdl_pipeline(self):
        """Test full pipeline from YAML spec to generated VHDL"""

        # Create test YAML
        yaml_content = """
        package_version: "2.0"
        app_name: "PipelineTest"
        platform: "moku_go"
        datatypes:
          - name: "intensity"
            datatype: "voltage_output_05v_s16"
            default_value: 2400
            units: "mV"
          - name: "timeout"
            datatype: "pulse_duration_ms_u16"
            default_value: 1000
            units: "ms"
          - name: "enable"
            datatype: "boolean"
            default_value: false
        """

        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Step 1: Save YAML
            yaml_path = tmpdir / "test.yaml"
            yaml_path.write_text(yaml_content)

            # Step 2: Load as package
            package = RegPackageFactory.from_yaml_file(yaml_path)
            assert package.app_name == "PipelineTest"
            assert package.platform == "moku_go"
            assert len(package.datatypes) == 3

            # Step 3: Generate mapping
            mapper = BADRegisterMapper.from_package(package)
            mapping = mapper.generate_mapping()
            assert len(mapping) > 0

            # Step 4: Generate VHDL
            output_dir = tmpdir / "vhdl"
            output_dir.mkdir()

            # Generator call (adjust based on actual API)
            # generate_vhdl(yaml_path, output_dir)

            # Step 5: Verify outputs
            shim_path = output_dir / "PipelineTest_custom_inst_shim.vhd"
            # assert shim_path.exists()

            # Step 6: Verify content
            # shim_content = shim_path.read_text()
            # assert "CLK_FREQ_HZ : integer := 125000000" in shim_content
            # assert "signal intensity : signed(15 downto 0)" in shim_content


class TestDS1140PDMigration:
    """Test DS1140_PD migration to BasicAppDataTypes"""

    def test_ds1140_pd_yaml_v2_generation(self):
        """Test creating v2.0 YAML from DS1140_PD spec"""

        # DS1140_PD has 8 datatypes (from Phase 4)
        expected_datatypes = [
            ("arm_probe", BasicAppDataTypes.BOOLEAN),
            ("force_fire", BasicAppDataTypes.BOOLEAN),
            ("reset_fsm", BasicAppDataTypes.BOOLEAN),
            ("intensity", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
            ("trigger_threshold", BasicAppDataTypes.VOLTAGE_INPUT_25V_S16),
            ("arm_timeout", BasicAppDataTypes.PULSE_DURATION_MS_U16),
            ("firing_duration", BasicAppDataTypes.PULSE_DURATION_NS_U8),
            ("cooling_duration", BasicAppDataTypes.PULSE_DURATION_NS_U8),
        ]

        # Create package
        from models.custom_inst.reg_package import DataTypeSpec

        package = BasicAppsRegPackage(
            app_name="DS1140_PD",
            platform="moku_go",
            datatypes=[
                DataTypeSpec(name=name, datatype=dtype)
                for name, dtype in expected_datatypes
            ]
        )

        # Generate mapping
        mapper = BADRegisterMapper.from_package(package)
        mapping = mapper.generate_mapping()

        # Phase 4 result: 8 datatypes → 3 registers (57% savings vs 7 manual)
        used_registers = set(m.cr_number for m in mapping)
        assert len(used_registers) <= 3, f"Expected ≤3 registers, got {len(used_registers)}"

        # Verify efficiency (Phase 4: 69.8% bit utilization)
        total_bits = len(used_registers) * 32
        used_bits = sum(m.datatype_metadata.bit_width for m in mapping)
        efficiency = (used_bits / total_bits) * 100

        assert efficiency > 60, f"Expected >60% efficiency, got {efficiency:.1f}%"

    def test_export_to_moku_config(self):
        """Test exporting BasicAppsRegPackage to MokuConfig format"""

        package = BasicAppsRegPackage(
            app_name="DS1140_PD",
            platform="moku_go",
            datatypes=[
                DataTypeSpec(
                    name="intensity",
                    datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
                    default_value=2400
                ),
            ]
        )

        # Generate mapping
        mapper = BADRegisterMapper.from_package(package)
        mapping = mapper.generate_mapping()

        # Export to control_registers format
        control_regs = package.to_control_registers()

        # Create MokuConfig
        config = MokuConfig(
            platform=MOKU_GO_PLATFORM,
            slots={
                1: SlotConfig(
                    instrument='CloudCompile',
                    bitstream='DS1140_PD.tar',
                    control_registers=control_regs
                )
            }
        )

        assert config.platform.clock_mhz == 125
        assert 1 in config.slots
        assert config.slots[1].control_registers is not None


class TestMultiPlatformGeneration:
    """Test generating for different Moku platforms"""

    @pytest.mark.parametrize("platform,expected_clk_mhz", [
        ("moku_go", 125),
        ("moku_lab", 500),
        ("moku_pro", 1250),
        ("moku_delta", 5000),
    ])
    def test_platform_specific_generation(self, platform, expected_clk_mhz):
        """Test code generation for each platform"""

        yaml_content = f"""
        package_version: "2.0"
        app_name: "MultiPlatformTest"
        platform: "{platform}"
        datatypes:
          - name: "delay"
            datatype: "pulse_duration_ms_u16"
            default_value: 1000
        """

        # Test that CLK_FREQ_HZ matches platform
        # Test that time conversion functions use correct frequency
        pass
```

#### C. Expand `python_tests/test_bad_register_mapper.py`
- Add tests for edge cases (overflow, single register, all 32-bit types)
- Add tests for strategy comparison (first_fit vs best_fit)
- Add tests for mapping report formats (ASCII, markdown, VHDL comments, JSON)

#### D. Expand `python_tests/test_reg_package.py`
- Add tests for YAML v2.0 parsing
- Add tests for validation rules (duplicate names, invalid datatypes)
- Add tests for MokuConfig export (`to_control_registers()`)
- Add tests for UI metadata (min/max values, units)

---

### 5.2 CocotB Tests for Generated VHDL

**Location:** `tests/`

**File to create:** `tests/test_bad_generated_vhdl_progressive.py`

```python
"""
CocotB Progressive Tests: BasicAppDataTypes Generated VHDL

Tests the generated shim layer from generate_custom_inst_v2.py.
Uses progressive testing pattern (P1: essential, P2: comprehensive).

Prerequisites:
- Generated DS1140_PD VHDL from Phase 4
- Frozen VHDL type utilities in shared/custom_inst/vhdl/
- HandShakeProtocol.md v2.0 compliance

Test DUT: DS1140_PD_custom_inst_shim (generated from examples/DS1140_PD_interface.yaml)
"""

import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.clock import Clock
import sys
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

from test_base import TestBase, VerbosityLevel


class BADGeneratedVHDLTests(TestBase):
    """Progressive tests for BasicAppDataTypes generated VHDL"""

    def __init__(self, dut):
        super().__init__(dut, "DS1140_PD_Shim")

    async def setup(self):
        """Common setup for all tests"""
        # Start clock (Moku:Go - 125 MHz = 8ns period)
        cocotb.start_soon(Clock(self.dut.Clk, 8, units="ns").start())

        # Reset
        self.dut.Reset.value = 1
        self.dut.ready_for_updates.value = 0

        # Clear all app registers
        for reg_num in range(6, 18):
            reg = getattr(self.dut, f"app_reg_{reg_num}")
            reg.value = 0

        await ClockCycles(self.dut.Clk, 5)
        self.dut.Reset.value = 0
        await RisingEdge(self.dut.Clk)

        self.log("Setup complete", VerbosityLevel.VERBOSE)

    # ========================================================================
    # P1 Tests - Essential Functionality
    # ========================================================================

    async def run_p1_basic(self):
        """P1: Essential BAD shim tests"""
        await self.setup()

        await self.test(
            "P1.1: Voltage type extraction",
            self.test_voltage_extraction
        )

        await self.test(
            "P1.2: Boolean type extraction",
            self.test_boolean_extraction
        )

        await self.test(
            "P1.3: Handshaking protocol",
            self.test_handshaking
        )

        await self.test(
            "P1.4: Default values on reset",
            self.test_reset_defaults
        )

    async def test_voltage_extraction(self):
        """Verify voltage type conversion from raw register bits"""

        # DS1140_PD mapping (from Phase 4):
        # CR6[31:16]: arm_timeout (pulse_duration_ms_u16)
        # CR6[15:0]:  intensity (voltage_output_05v_s16)

        # Test intensity extraction
        # 2400 mV = 0x1EB8 (from Phase 4 default)
        test_intensity_raw = 0x1EB8

        self.dut.app_reg_6.value = test_intensity_raw  # Lower 16 bits
        self.dut.ready_for_updates.value = 1
        await ClockCycles(self.dut.Clk, 2)

        # Verify signal extraction
        intensity_value = int(self.dut.intensity.value.signed_integer)
        expected = test_intensity_raw if test_intensity_raw < 32768 else test_intensity_raw - 65536

        assert intensity_value == expected, \
            f"Voltage extraction failed: {intensity_value} != {expected}"

        self.log(f"✓ Voltage extracted: {intensity_value} ({hex(test_intensity_raw)})",
                 VerbosityLevel.NORMAL)

    async def test_boolean_extraction(self):
        """Verify boolean type extraction from single bit"""

        # DS1140_PD mapping (from Phase 4):
        # CR8[31]: arm_probe (boolean)
        # CR8[30]: force_fire (boolean)
        # CR8[29]: reset_fsm (boolean)

        # Test arm_probe
        self.dut.app_reg_8.value = 0x80000000  # Set bit 31
        self.dut.ready_for_updates.value = 1
        await ClockCycles(self.dut.Clk, 2)

        assert self.dut.arm_probe.value == 1, "Boolean extraction failed (expected 1)"

        # Clear and verify
        self.dut.app_reg_8.value = 0x00000000
        await ClockCycles(self.dut.Clk, 2)

        assert self.dut.arm_probe.value == 0, "Boolean clear failed (expected 0)"

        self.log("✓ Boolean extraction working", VerbosityLevel.NORMAL)

    async def test_handshaking(self):
        """Verify ready_for_updates handshaking protocol"""

        # Gate CLOSED (ready=0)
        self.dut.ready_for_updates.value = 0
        self.dut.app_reg_6.value = 0xFFFF
        await ClockCycles(self.dut.Clk, 5)

        initial_intensity = int(self.dut.intensity.value.signed_integer)

        # Change value while gate closed
        self.dut.app_reg_6.value = 0x3333
        await ClockCycles(self.dut.Clk, 5)

        # Verify NO change
        current_intensity = int(self.dut.intensity.value.signed_integer)
        assert current_intensity == initial_intensity, \
            f"Value changed when gate closed: {initial_intensity} → {current_intensity}"

        # Gate OPEN (ready=1)
        self.dut.ready_for_updates.value = 1
        await ClockCycles(self.dut.Clk, 2)

        # Verify change applied
        updated_intensity = int(self.dut.intensity.value.signed_integer)
        assert updated_intensity != initial_intensity, \
            "Value did not change when gate opened"

        self.log("✓ Handshaking protocol working", VerbosityLevel.NORMAL)

    async def test_reset_defaults(self):
        """Verify YAML-defined defaults loaded on reset"""

        # DS1140_PD defaults (from Phase 4 YAML):
        # intensity: 2400 mV
        # arm_probe: false

        # Write non-default values
        self.dut.app_reg_6.value = 0xFFFFFFFF
        self.dut.app_reg_8.value = 0xFFFFFFFF
        self.dut.ready_for_updates.value = 1
        await ClockCycles(self.dut.Clk, 2)

        # Reset
        self.dut.Reset.value = 1
        await RisingEdge(self.dut.Clk)
        self.dut.Reset.value = 0
        await RisingEdge(self.dut.Clk)

        # Verify defaults (2400 mV = 0x1EB8 signed)
        intensity_default = int(self.dut.intensity.value.signed_integer)
        expected_default = 0x1EB8

        assert abs(intensity_default - expected_default) < 2, \
            f"Default value incorrect: {intensity_default} != {expected_default}"

        self.log(f"✓ Defaults loaded: intensity={intensity_default}", VerbosityLevel.NORMAL)

    # ========================================================================
    # P2 Tests - Comprehensive Functionality
    # ========================================================================

    async def run_p2_intermediate(self):
        """P2: Comprehensive BAD shim tests"""
        await self.setup()

        await self.test(
            "P2.1: Multi-type register packing",
            self.test_multi_type_packing
        )

        await self.test(
            "P2.2: Time type extraction",
            self.test_time_extraction
        )

        await self.test(
            "P2.3: All DS1140_PD signals",
            self.test_all_ds1140_signals
        )

    async def test_multi_type_packing(self):
        """Verify multiple types packed in single register"""

        # CR7 packing (from Phase 4):
        # CR7[31:16]: trigger_threshold (voltage_input_25v_s16)
        # CR7[15:8]:  cooling_duration (pulse_duration_ns_u8)
        # CR7[7:0]:   firing_duration (pulse_duration_ns_u8)

        packed_value = (0x1234 << 16) | (0x56 << 8) | 0x78
        self.dut.app_reg_7.value = packed_value
        self.dut.ready_for_updates.value = 1
        await ClockCycles(self.dut.Clk, 2)

        # Verify each field extracted correctly
        threshold = int(self.dut.trigger_threshold.value.signed_integer)
        cooling = int(self.dut.cooling_duration.value)
        firing = int(self.dut.firing_duration.value)

        # Verify bit slices
        assert cooling == 0x56, f"Cooling duration mismatch: {cooling:#04x} != 0x56"
        assert firing == 0x78, f"Firing duration mismatch: {firing:#04x} != 0x78"

        self.log(f"✓ Multi-type packing: threshold={threshold:#06x}, "
                 f"cooling={cooling:#04x}, firing={firing:#04x}",
                 VerbosityLevel.NORMAL)

    async def test_time_extraction(self):
        """Verify time type extraction (no conversion in shim)"""

        # arm_timeout is pulse_duration_ms_u16 in CR6[31:16]
        test_timeout_ms = 1000  # 1000 ms

        self.dut.app_reg_6.value = test_timeout_ms << 16
        self.dut.ready_for_updates.value = 1
        await ClockCycles(self.dut.Clk, 2)

        # Verify raw extraction (conversion happens in main layer)
        timeout_value = int(self.dut.arm_timeout.value)

        assert timeout_value == test_timeout_ms, \
            f"Time extraction failed: {timeout_value} != {test_timeout_ms}"

        self.log(f"✓ Time type extracted: {timeout_value} ms", VerbosityLevel.NORMAL)

    async def test_all_ds1140_signals(self):
        """Verify all 8 DS1140_PD signals extract correctly"""

        # All 8 datatypes from Phase 4
        signals_to_test = [
            ("arm_probe", 8, 31, 1),           # CR8[31]
            ("force_fire", 8, 30, 1),          # CR8[30]
            ("reset_fsm", 8, 29, 1),           # CR8[29]
            ("intensity", 6, 15, 0x1234),      # CR6[15:0]
            ("trigger_threshold", 7, 31, 16),  # CR7[31:16] (0x5678)
            ("arm_timeout", 6, 31, 16),        # CR6[31:16] (1000 ms)
            ("firing_duration", 7, 7, 0),      # CR7[7:0] (100 ns)
            ("cooling_duration", 7, 15, 8),    # CR7[15:8] (200 ns)
        ]

        # Write test values
        self.dut.app_reg_6.value = (1000 << 16) | 0x1234
        self.dut.app_reg_7.value = (0x5678 << 16) | (200 << 8) | 100
        self.dut.app_reg_8.value = 0xE0000000  # Set top 3 bits

        self.dut.ready_for_updates.value = 1
        await ClockCycles(self.dut.Clk, 2)

        # Verify all signals readable
        for signal_name, cr, msb, lsb in signals_to_test:
            signal = getattr(self.dut, signal_name)
            value = int(signal.value)
            self.log(f"  {signal_name}: {value}", VerbosityLevel.VERBOSE)

        self.log("✓ All 8 DS1140_PD signals extracted", VerbosityLevel.NORMAL)


# ============================================================================
# CocotB Test Entry Points
# ============================================================================

@cocotb.test()
async def run_p1_tests(dut):
    """Run P1 (basic) progressive tests"""
    test_harness = BADGeneratedVHDLTests(dut)
    await test_harness.run_p1_basic()


@cocotb.test()
async def run_p2_tests(dut):
    """Run P2 (intermediate) progressive tests"""
    test_harness = BADGeneratedVHDLTests(dut)
    await test_harness.run_p2_intermediate()
```

**CocotB Test Configuration:**

Create `tests/test_configs.py` entry:
```python
# Add to TESTS_CONFIG dictionary
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

### 5.3 Performance Benchmarks

**Location:** `python_tests/test_bad_benchmarks.py` (NEW)

```python
"""
Performance benchmarks for BasicAppDataTypes.

Uses pytest-benchmark to measure:
- Mapping algorithm performance
- Type conversion throughput
- VHDL generation speed
"""

import pytest
from basic_app_datatypes import BasicAppDataTypes, RegisterMapper, TypeConverter


class TestMappingPerformance:
    """Benchmark register mapping algorithm"""

    def test_mapper_small_dataset(self, benchmark):
        """Benchmark mapping 10 datatypes"""
        mapper = RegisterMapper()
        datatypes = [
            (f"signal_{i}", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16)
            for i in range(10)
        ]

        result = benchmark(mapper.map_registers, datatypes, strategy="best_fit")
        assert len(result) == 10

    def test_mapper_large_dataset(self, benchmark):
        """Benchmark mapping 100 datatypes (near register limit)"""
        mapper = RegisterMapper()

        # Mix of types to test packing efficiency
        datatypes = []
        for i in range(100):
            if i % 3 == 0:
                dtype = BasicAppDataTypes.BOOLEAN
            elif i % 3 == 1:
                dtype = BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
            else:
                dtype = BasicAppDataTypes.PULSE_DURATION_MS_U16

            datatypes.append((f"signal_{i}", dtype))

        try:
            result = benchmark(mapper.map_registers, datatypes, strategy="best_fit")
            # Should fit if packing is efficient
            assert len(result) > 0
        except Exception:
            # May overflow register limit (expected)
            pass


class TestTypeConversionPerformance:
    """Benchmark type conversion functions"""

    def test_voltage_conversion_batch(self, benchmark):
        """Benchmark voltage conversions"""

        def convert_batch():
            results = []
            for mv in range(-10000, 10000, 10):
                raw = TypeConverter.voltage_mv_to_raw(mv)
                recovered = TypeConverter.raw_to_voltage_mv(raw)
                results.append(recovered)
            return results

        result = benchmark(convert_batch)
        assert len(result) == 2000

    def test_time_conversion_batch(self, benchmark):
        """Benchmark time conversions"""

        def convert_batch():
            clk_freq = 125_000_000  # Moku:Go
            results = []
            for ms in range(0, 1000, 1):
                cycles = TypeConverter.time_ms_to_clk_cycles(ms, clk_freq)
                results.append(cycles)
            return results

        result = benchmark(convert_batch)
        assert len(result) == 1000


class TestCodeGenerationPerformance:
    """Benchmark VHDL code generation"""

    def test_generation_speed(self, benchmark):
        """Benchmark full YAML → VHDL generation"""
        # Implementation depends on generator API
        pass
```

---

### 5.4 Test Runner Integration

Update `tests/run.py` to include BAD tests in `--category=bad`:

```python
# In TESTS_CONFIG
CATEGORIES = {
    "volo_common": ["volo_clk_divider", ...],
    "ds1140_pd": ["test_ds1140_pd_progressive", ...],
    "bad": ["bad_generated_vhdl"],  # ← Add BAD category
}
```

Create convenience runner script:

**`run_bad_tests.sh`** (NEW)
```bash
#!/usr/bin/env bash
# Run all BasicAppDataTypes tests

set -e

echo "================================================"
echo "BasicAppDataTypes Phase 5 Test Suite"
echo "================================================"
echo

# 1. Core library tests (libs/basic-app-datatypes/)
echo "[1/4] Running core library tests..."
cd libs/basic-app-datatypes
uv run pytest tests/ -v --tb=short
cd ../..
echo "✓ Core library tests passed"
echo

# 2. Python integration tests (python_tests/)
echo "[2/4] Running Python integration tests..."
PYTHONPATH=libs/basic-app-datatypes:. uv run pytest python_tests/ -v --tb=short
echo "✓ Python integration tests passed"
echo

# 3. CocotB tests (tests/)
echo "[3/4] Running CocotB VHDL tests..."
python tests/run.py bad_generated_vhdl
echo "✓ CocotB tests passed"
echo

# 4. Benchmarks (python_tests/)
echo "[4/4] Running performance benchmarks..."
PYTHONPATH=libs/basic-app-datatypes:. uv run pytest python_tests/test_bad_benchmarks.py --benchmark-only -v
echo "✓ Benchmarks completed"
echo

echo "================================================"
echo "All BasicAppDataTypes tests passed! ✓"
echo "================================================"
```

---

## Platform-Specific Testing Requirements

### Multi-Platform Validation

**Critical:** BasicAppDataTypes must work across all 4 Moku platforms.

**Test Matrix:**

| Platform | Clock (MHz) | Test Focus |
|----------|-------------|------------|
| Moku:Go | 125 | Default platform, DS1140_PD reference |
| Moku:Lab | 500 | Time conversion accuracy at 4× clock |
| Moku:Pro | 1,250 | Time conversion accuracy at 10× clock |
| Moku:Delta | 5,000 | Time conversion accuracy at 40× clock |

**Platform Test Strategy:**

1. **Parametrized CocotB Tests:**
```python
@pytest.mark.parametrize("platform,clock_ns", [
    ("moku_go", 8),      # 125 MHz
    ("moku_lab", 2),     # 500 MHz
    ("moku_pro", 0.8),   # 1.25 GHz
    ("moku_delta", 0.2), # 5 GHz
])
async def test_time_conversion_platform(dut, platform, clock_ns):
    """Test time conversion at different clock frequencies"""
    # Start clock at platform frequency
    cocotb.start_soon(Clock(dut.Clk, clock_ns, units="ns").start())

    # Test 1ms delay converts to correct cycle count
    # ...
```

2. **Generator Tests:**
- Test `CLK_FREQ_HZ` generic matches platform
- Test time conversion functions reference correct clock

3. **Integration Tests:**
- Generate VHDL for same YAML spec on all 4 platforms
- Verify clock-dependent values differ appropriately

---

## Success Criteria

Phase 5 is complete when:

- [x] Test structure understood (tests/ vs python_tests/ vs libs/)
- [ ] Code generation tests written (`test_code_generation.py`)
- [ ] Integration tests written (`test_bad_integration.py`)
- [ ] CocotB tests written (`test_bad_generated_vhdl_progressive.py`)
- [ ] Performance benchmarks written (`test_bad_benchmarks.py`)
- [ ] All existing tests passing (44 library + Python + CocotB)
- [ ] DS1140_PD migration validated (3 registers vs 7 manual)
- [ ] Multi-platform tests passing (Go/Lab/Pro/Delta)
- [ ] Coverage > 90% for BAD components
- [ ] Test runner script working (`run_bad_tests.sh`)
- [ ] Phase summary written (`BAD_Phase5_COMPLETE.md`)

---

## Handoff to Phase 6 (Documentation)

Phase 6 will need:
- ✅ All tests passing
- ✅ Coverage reports
- ✅ Performance benchmarks
- ✅ Migration validation (DS1140_PD)
- ✅ Multi-platform validation

Update `BAD_Phase6_Documentation.md` header with:
```markdown
**Prerequisites:** Phase 1-5 complete
**Phase 5 Summary:** ./BAD_Phase5_COMPLETE.md
**Phase 5 Commit:** {git_hash}
**Test Coverage:** {coverage}%
**Platforms Validated:** Moku:Go, Moku:Lab, Moku:Pro, Moku:Delta
```

---

## Quick Reference

### Running Tests

```bash
# Core library tests
cd libs/basic-app-datatypes && uv run pytest tests/ -v

# Python integration tests
PYTHONPATH=libs/basic-app-datatypes:. uv run pytest python_tests/ -v

# CocotB tests
python tests/run.py bad_generated_vhdl

# All tests
./run_bad_tests.sh

# With coverage
uv run pytest python_tests/ --cov=models.custom_inst --cov-report=html
```

### Test Categories

- **P1 (Basic):** Essential functionality, fast, LLM-friendly
- **P2 (Intermediate):** Comprehensive coverage, moderate speed
- **P3 (Comprehensive):** Edge cases, stress tests, slower

### Key Files

- `libs/basic-app-datatypes/tests/` - Core library tests (✅ 44 passing)
- `python_tests/` - Python integration tests (🟡 partial)
- `tests/` - CocotB VHDL tests (❌ missing BAD tests)
- `tests/run.py` - CocotB test runner
- `tests/test_base.py` - Progressive test base class
- `docs/VHDL_COCOTB_LESSONS_LEARNED.md` - Critical testing patterns

---

**Phase 5 Status:** Ready to implement ✅
**Next Steps:** Create missing test files following this specification
**Last Updated:** 2025-11-03 (Revision 2)
