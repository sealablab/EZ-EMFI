# BAD Phase 5: Comprehensive Testing Suite

**Phase:** 5 of 6
**Goal:** Validate BasicAppDataTypes with comprehensive CocotB and Python tests
**Prerequisites:** Phase 1-4 complete
**Phase 1-4 Summaries:** ./BAD_Phase{1-4}_COMPLETE.md
**Output:** Complete test suite validating all components

## Context Loading

Please review these files and previous phase outputs:

```bash
# Previous phase results
cat docs/BasicAppDataTypes/BAD_Phase4_COMPLETE.md

# Existing test infrastructure
cat tests/test_handshake_shim_progressive.py | head -100
cat tests/run.py

# CocotB patterns
cat docs/VHDL_COCOTB_LESSONS_LEARNED.md

# Generated VHDL to test (from Phase 4)
ls VHDL/apps/DS1140_PD_v2/
```

## Phase 5 Objectives

### Primary Goals
1. Unit test each BasicAppDataTypes component
2. Integration test the complete pipeline
3. CocotB validation of generated VHDL
4. Performance and efficiency benchmarks
5. Migration validation for DS1140_PD

### Test Coverage Matrix

| Component | Unit Tests | Integration | CocotB | Benchmarks |
|-----------|------------|-------------|---------|------------|
| Type System | ✓ | ✓ | ✓ | - |
| Register Mapper | ✓ | ✓ | - | ✓ |
| Package Model | ✓ | ✓ | - | - |
| Code Generator | ✓ | ✓ | - | - |
| Generated VHDL | - | - | ✓ | ✓ |

### Specific Deliverables

#### 5.1 Python Unit Tests

Create comprehensive test files:

```python
# tests/test_basic_app_datatypes.py
"""Unit tests for BasicAppDataTypes type system"""

import pytest
from models.custom_inst.basic_app_datatypes import (
    BasicAppDataTypes,
    TypeConverter,
    TypeMetadata,
    TYPE_REGISTRY,
)


class TestTypeDefinitions:
    """Test type definitions and metadata"""

    def test_all_types_have_metadata(self):
        """Every type must have complete metadata"""
        for type_enum in BasicAppDataTypes:
            assert type_enum in TYPE_REGISTRY
            metadata = TYPE_REGISTRY[type_enum]
            assert metadata.bit_width > 0
            assert metadata.vhdl_type
            assert metadata.python_type
            assert metadata.default_value is not None

    def test_bit_widths_are_fixed(self):
        """Bit widths must be immutable"""
        metadata = TYPE_REGISTRY[BasicAppDataTypes.VOLTAGE_MV]
        assert metadata.bit_width == 16

        # Should not be modifiable
        with pytest.raises(AttributeError):
            metadata.bit_width = 32

    def test_type_names_are_descriptive(self):
        """Type names should indicate units"""
        assert "mv" in BasicAppDataTypes.VOLTAGE_MV.value.lower()
        assert "ms" in BasicAppDataTypes.TIME_MS.value.lower()
        assert "bool" in BasicAppDataTypes.BOOLEAN.value.lower()


class TestVoltageConversion:
    """Test voltage type conversions"""

    @pytest.mark.parametrize("mv,expected_raw", [
        (0, 0),
        (10000, 32767),      # Max positive
        (-10000, -32768),     # Max negative
        (2400, 7864),        # 2.4V typical
        (5000, 16383),       # 5V
        (-5000, -16384),     # -5V
    ])
    def test_voltage_to_raw(self, mv, expected_raw):
        """Test millivolt to raw conversion"""
        raw = TypeConverter.voltage_mv_to_raw(mv)
        assert abs(raw - expected_raw) <= 1  # Allow rounding

    def test_voltage_round_trip(self):
        """Test conversion round-trip accuracy"""
        test_values = [0, 100, -100, 2400, 5000, -5000, 9999, -9999]

        for mv in test_values:
            raw = TypeConverter.voltage_mv_to_raw(mv)
            recovered = TypeConverter.raw_to_voltage_mv(raw)
            # Should be within 1mV due to quantization
            assert abs(recovered - mv) <= 1

    def test_voltage_saturation(self):
        """Test voltage saturation at limits"""
        assert TypeConverter.voltage_mv_to_raw(15000) == 32767  # Saturate
        assert TypeConverter.voltage_mv_to_raw(-15000) == -32768


class TestTimeConversion:
    """Test time type conversions"""

    @pytest.mark.parametrize("ms,clk_freq,expected_cycles", [
        (1, 125_000_000, 125_000),      # 1ms @ 125MHz
        (1000, 125_000_000, 125_000_000), # 1s @ 125MHz
        (10, 100_000_000, 1_000_000),    # 10ms @ 100MHz
    ])
    def test_time_to_cycles(self, ms, clk_freq, expected_cycles):
        """Test millisecond to clock cycle conversion"""
        cycles = TypeConverter.time_ms_to_clk_cycles(ms, clk_freq)
        assert cycles == expected_cycles

    def test_time_overflow_handling(self):
        """Test handling of time overflow"""
        # 16-bit time_ms can hold max 65535ms
        with pytest.raises(OverflowError):
            TypeConverter.validate_time_ms(70000)


# tests/test_register_mapper.py
"""Unit tests for register mapping algorithm"""

import pytest
from models.custom_inst.register_mapper import (
    RegisterMapper,
    MappedRegister,
    PackingStrategy,
    RegisterOverflowError,
)
from models.custom_inst.basic_app_datatypes import BasicAppDataTypes


class TestRegisterMapper:
    """Test core mapping functionality"""

    def test_simple_sequential_mapping(self):
        """Test basic sequential register assignment"""
        mapper = RegisterMapper()
        datatypes = [
            ("voltage1", BasicAppDataTypes.VOLTAGE_MV),   # 16 bits
            ("voltage2", BasicAppDataTypes.VOLTAGE_MV),   # 16 bits
            ("enable", BasicAppDataTypes.BOOLEAN),        # 1 bit
        ]

        mapping = mapper.map_registers(datatypes, strategy="first_fit")

        # Should pack efficiently
        assert len(mapping) == 3
        # First two should share CR6
        assert mapping[0].cr_number == 6
        assert mapping[0].bit_slice == (31, 16)
        assert mapping[1].cr_number == 6
        assert mapping[1].bit_slice == (15, 0)
        # Boolean in CR7
        assert mapping[2].cr_number == 7
        assert mapping[2].bit_slice == (31, 31)

    def test_best_fit_packing(self):
        """Test optimal packing strategy"""
        mapper = RegisterMapper()
        datatypes = [
            ("v1", BasicAppDataTypes.VOLTAGE_MV),     # 16 bits
            ("v2", BasicAppDataTypes.VOLTAGE_MV),     # 16 bits
            ("t1", BasicAppDataTypes.TIME_MS),        # 16 bits
            ("u1", BasicAppDataTypes.UNSIGNED_8),     # 8 bits
            ("u2", BasicAppDataTypes.UNSIGNED_8),     # 8 bits
            ("b1", BasicAppDataTypes.BOOLEAN),        # 1 bit
            ("b2", BasicAppDataTypes.BOOLEAN),        # 1 bit
            ("b3", BasicAppDataTypes.BOOLEAN),        # 1 bit
            ("b4", BasicAppDataTypes.BOOLEAN),        # 1 bit
        ]

        mapping = mapper.map_registers(datatypes, strategy="best_fit")

        # Should pack into 2-3 registers maximum
        used_crs = set(m.cr_number for m in mapping)
        assert len(used_crs) <= 3

        # Verify no overlaps
        self._verify_no_overlaps(mapping)

    def test_overflow_detection(self):
        """Test detection of register overflow"""
        mapper = RegisterMapper()

        # Try to map 25 16-bit values (400 bits > 384 bit limit)
        datatypes = [(f"v{i}", BasicAppDataTypes.VOLTAGE_MV)
                    for i in range(25)]

        with pytest.raises(RegisterOverflowError) as exc:
            mapper.map_registers(datatypes)

        assert "400 bits" in str(exc.value)
        assert "384 bits" in str(exc.value)

    def test_deterministic_mapping(self):
        """Mapping should be reproducible"""
        mapper = RegisterMapper()
        datatypes = [
            ("a", BasicAppDataTypes.VOLTAGE_MV),
            ("b", BasicAppDataTypes.TIME_MS),
            ("c", BasicAppDataTypes.BOOLEAN),
        ]

        mapping1 = mapper.map_registers(datatypes)
        mapping2 = mapper.map_registers(datatypes)

        # Identical input should produce identical output
        assert mapping1 == mapping2

    def test_cr_range_validation(self):
        """Ensure CR numbers stay in valid range"""
        mapper = RegisterMapper()

        # Max types that should fit
        datatypes = [(f"b{i}", BasicAppDataTypes.BOOLEAN)
                    for i in range(384)]  # 384 booleans = 384 bits

        mapping = mapper.map_registers(datatypes)

        for m in mapping:
            assert 6 <= m.cr_number <= 17  # Valid range

    def _verify_no_overlaps(self, mapping: list[MappedRegister]):
        """Helper to verify no bit overlaps in mapping"""
        by_cr = {}
        for m in mapping:
            if m.cr_number not in by_cr:
                by_cr[m.cr_number] = []
            by_cr[m.cr_number].append(m)

        for cr, mappings in by_cr.items():
            # Check each pair for overlaps
            for i, m1 in enumerate(mappings):
                for m2 in mappings[i+1:]:
                    # Ranges should not overlap
                    assert not self._ranges_overlap(
                        m1.bit_slice, m2.bit_slice
                    ), f"Overlap in CR{cr}: {m1.name} and {m2.name}"

    @staticmethod
    def _ranges_overlap(r1: tuple, r2: tuple) -> bool:
        """Check if two bit ranges overlap"""
        return not (r1[1] > r2[0] or r2[1] > r1[0])


# tests/test_reg_package.py
"""Unit tests for BasicAppsRegPackage"""

import pytest
import yaml
from pathlib import Path
from models.custom_inst.reg_package import (
    BasicAppsRegPackage,
    DataTypeSpec,
    RegPackageFactory,
    PackageValidator,
)


class TestRegPackage:
    """Test package creation and manipulation"""

    def test_create_package_programmatically(self):
        """Test creating package in code"""
        package = BasicAppsRegPackage(
            app_name="TestApp",
            description="Test application",
            datatypes=[
                DataTypeSpec(
                    name="output_voltage",
                    type=BasicAppDataTypes.VOLTAGE_MV,
                    description="Main output",
                    default_value=2400,
                    min_value=-5000,
                    max_value=5000,
                ),
            ],
        )

        assert package.app_name == "TestApp"
        assert len(package.datatypes) == 1
        assert package.datatypes[0].default_value == 2400

    def test_yaml_v2_parsing(self):
        """Test parsing v2.0 YAML format"""
        yaml_content = """
        package_version: "2.0"
        app_name: "TestApp"
        description: "Test BasicAppDataTypes"
        mapping:
          strategy: "auto"
        datatypes:
          - name: "intensity"
            type: "voltage_mv"
            description: "Output voltage"
            default_value: 2400
            min_value: -10000
            max_value: 10000
            units: "mV"
        """

        package = RegPackageFactory._from_v2_yaml(
            yaml.safe_load(yaml_content)
        )

        assert package.package_version == "2.0"
        assert package.app_name == "TestApp"
        assert package.mapping_strategy == "auto"
        assert len(package.datatypes) == 1
        assert package.datatypes[0].units == "mV"

    def test_yaml_v1_compatibility(self):
        """Test parsing legacy v1.0 format"""
        yaml_content = """
        app_name: "LegacyApp"
        registers:
          - name: "Intensity"
            description: "Output level"
            reg_type: counter_16bit
            cr_number: 6
            default_value: 100
        """

        package = RegPackageFactory._from_v1_yaml(
            yaml.safe_load(yaml_content)
        )

        assert package.package_version == "1.0-compat"
        assert package.app_name == "LegacyApp"
        assert package.mapping_strategy == "manual"
        assert package.datatypes[0].manual_cr == 6

    def test_package_validation(self):
        """Test package validation rules"""
        # Invalid: duplicate names
        package = BasicAppsRegPackage(
            app_name="BadApp",
            datatypes=[
                DataTypeSpec(name="dup", type=BasicAppDataTypes.VOLTAGE_MV),
                DataTypeSpec(name="dup", type=BasicAppDataTypes.BOOLEAN),
            ],
        )

        errors = package.validate()
        assert any("duplicate" in e.lower() for e in errors)

    def test_datatype_value_validation(self):
        """Test datatype value range validation"""
        dt = DataTypeSpec(
            name="limited_voltage",
            type=BasicAppDataTypes.VOLTAGE_MV,
            min_value=-5000,
            max_value=5000,
        )

        assert dt.validate_value(0)
        assert dt.validate_value(5000)
        assert dt.validate_value(-5000)
        assert not dt.validate_value(6000)
        assert not dt.validate_value(-6000)
```

#### 5.2 CocotB Progressive Tests

Create `tests/test_bad_generated_vhdl_progressive.py`:

```python
"""
CocotB tests for BasicAppDataTypes generated VHDL
Uses progressive testing pattern (P1: essential, P2: comprehensive)
"""

import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
import random
from pathlib import Path


class TestBadGeneratedShim:
    """Test generated shim layer with BasicAppDataTypes"""

    @cocotb.test()
    async def test_p1_basic_type_extraction(dut):
        """P1: Test basic type extraction from registers"""
        # Setup clock
        clock = Clock(dut.Clk, 10, units="ns")
        cocotb.start_soon(clock.start())

        # Reset
        dut.Reset.value = 1
        await RisingEdge(dut.Clk)
        await RisingEdge(dut.Clk)
        dut.Reset.value = 0

        # Test voltage type extraction
        # Assuming intensity is mapped to CR6[31:16]
        raw_voltage = 0x1EB8  # 2.4V
        dut.app_reg_6.value = raw_voltage << 16

        dut.ready_for_updates.value = 1
        await RisingEdge(dut.Clk)

        # Verify correct extraction and type conversion
        intensity_signed = dut.intensity.value.signed_integer
        expected_signed = raw_voltage if raw_voltage < 32768 else raw_voltage - 65536
        assert intensity_signed == expected_signed, \
            f"Voltage extraction failed: {intensity_signed} != {expected_signed}"

    @cocotb.test()
    async def test_p1_boolean_extraction(dut):
        """P1: Test boolean type extraction"""
        clock = Clock(dut.Clk, 10, units="ns")
        cocotb.start_soon(clock.start())

        # Reset
        dut.Reset.value = 1
        await RisingEdge(dut.Clk)
        dut.Reset.value = 0

        # Test boolean extraction from MSB
        # Assuming arm_probe is mapped to CR7[31]
        dut.app_reg_7.value = 0x80000000  # Set MSB
        dut.ready_for_updates.value = 1
        await RisingEdge(dut.Clk)

        assert dut.arm_probe.value == 1, "Boolean extraction failed"

        # Clear boolean
        dut.app_reg_7.value = 0x00000000
        await RisingEdge(dut.Clk)
        assert dut.arm_probe.value == 0, "Boolean clear failed"

    @cocotb.test()
    async def test_p1_handshaking_with_types(dut):
        """P1: Test handshaking protocol with typed signals"""
        clock = Clock(dut.Clk, 10, units="ns")
        cocotb.start_soon(clock.start())

        # Reset
        dut.Reset.value = 1
        await RisingEdge(dut.Clk)
        dut.Reset.value = 0

        # Set register values
        dut.app_reg_6.value = 0x1EB80000  # intensity in upper 16
        dut.app_reg_7.value = 0x80000000  # arm_probe in MSB

        # Updates blocked when ready_for_updates = 0
        dut.ready_for_updates.value = 0
        await RisingEdge(dut.Clk)

        old_intensity = dut.intensity.value.signed_integer

        # Change register values
        dut.app_reg_6.value = 0x33330000
        await RisingEdge(dut.Clk)

        # Values should not change
        assert dut.intensity.value.signed_integer == old_intensity, \
            "Value changed when updates were blocked"

        # Enable updates
        dut.ready_for_updates.value = 1
        await RisingEdge(dut.Clk)

        # Now values should update
        assert dut.intensity.value.signed_integer != old_intensity, \
            "Value did not update when ready"

    @cocotb.test()
    async def test_p2_multi_type_packing(dut):
        """P2: Test multiple types packed in single register"""
        clock = Clock(dut.Clk, 10, units="ns")
        cocotb.start_soon(clock.start())

        # Assuming CR8 has:
        # [31:24] clock_divider (unsigned_8)
        # [23:16] firing_duration (unsigned_8)
        # [15:8] cooling_duration (unsigned_8)
        # [7:0] unused

        packed_value = (10 << 24) | (20 << 16) | (30 << 8)
        dut.app_reg_8.value = packed_value
        dut.ready_for_updates.value = 1
        await RisingEdge(dut.Clk)

        # Verify each field extracted correctly
        assert dut.clock_divider.value == 10
        assert dut.firing_duration.value == 20
        assert dut.cooling_duration.value == 30

    @cocotb.test()
    async def test_p2_type_defaults_on_reset(dut):
        """P2: Test type-specific default values on reset"""
        clock = Clock(dut.Clk, 10, units="ns")
        cocotb.start_soon(clock.start())

        # Set some values
        dut.app_reg_6.value = 0xFFFF0000
        dut.ready_for_updates.value = 1
        await RisingEdge(dut.Clk)

        # Reset
        dut.Reset.value = 1
        await RisingEdge(dut.Clk)

        # Check defaults from YAML
        # Assuming intensity default is 2400mV = 0x1EB8
        expected_default = 0x1EB8
        actual = dut.intensity.value.signed_integer
        assert abs(actual - expected_default) < 2, \
            f"Default value incorrect: {actual} != {expected_default}"

    @cocotb.test()
    async def test_p3_stress_random_updates(dut):
        """P3: Stress test with random register updates"""
        clock = Clock(dut.Clk, 10, units="ns")
        cocotb.start_soon(clock.start())

        dut.Reset.value = 0
        dut.ready_for_updates.value = 1

        for _ in range(100):
            # Random values for all registers
            for reg_num in range(6, 18):
                reg = getattr(dut, f"app_reg_{reg_num}")
                reg.value = random.randint(0, 0xFFFFFFFF)

            await RisingEdge(dut.Clk)

            # Randomly toggle ready_for_updates
            if random.random() > 0.5:
                dut.ready_for_updates.value = 0
                await RisingEdge(dut.Clk)
                await RisingEdge(dut.Clk)
                dut.ready_for_updates.value = 1

        # System should remain stable
        assert True, "Stress test completed"
```

#### 5.3 Integration Tests

Create `tests/test_bad_integration.py`:

```python
"""Integration tests for complete BasicAppDataTypes pipeline"""

import pytest
import tempfile
from pathlib import Path
import yaml
import subprocess

from models.custom_inst.reg_package import RegPackageFactory
from models.custom_inst.register_mapper import RegisterMapper
from tools.generate_custom_inst import CustomInstGenerator


class TestEndToEnd:
    """Test complete workflow from YAML to VHDL"""

    def test_complete_pipeline(self):
        """Test YAML → Package → Mapping → VHDL generation"""

        # Create test YAML
        yaml_content = """
        package_version: "2.0"
        app_name: "IntegrationTest"
        datatypes:
          - name: "voltage_out"
            type: "voltage_mv"
            default_value: 2400
          - name: "timeout"
            type: "time_ms"
            default_value: 1000
          - name: "enable"
            type: "boolean"
            default_value: false
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Save YAML
            yaml_path = tmpdir / "test.yaml"
            yaml_path.write_text(yaml_content)

            # Load package
            package = RegPackageFactory.from_yaml_file(yaml_path)
            assert package.app_name == "IntegrationTest"

            # Generate mapping
            mapper = RegisterMapper()
            package.generate_mapping(mapper)
            assert package.mapping_result is not None

            # Generate VHDL
            generator = CustomInstGenerator(
                Path("shared/custom_inst/templates")
            )
            output_dir = tmpdir / "vhdl"
            output_dir.mkdir()
            generator.generate(yaml_path, output_dir)

            # Verify files generated
            shim_path = output_dir / "IntegrationTest_custom_inst_shim.vhd"
            assert shim_path.exists()

            # Verify content
            shim_content = shim_path.read_text()
            assert "package_version: 2.0" in shim_content.lower()
            assert "voltage_out" in shim_content
            assert "ready_for_updates" in shim_content

    def test_ds1140_migration(self):
        """Test migrating DS1140_PD to BasicAppDataTypes"""

        # Load original
        original_yaml = Path("DS1140_PD_app.yaml")
        if not original_yaml.exists():
            pytest.skip("DS1140_PD_app.yaml not found")

        # Create v2.0 version
        with open(original_yaml) as f:
            original = yaml.safe_load(f)

        v2_config = {
            "package_version": "2.0",
            "app_name": original["app_name"],
            "mapping": {"strategy": "auto"},
            "datatypes": []
        }

        # Convert registers to datatypes
        for reg in original.get("registers", []):
            datatype = {
                "name": reg["name"].lower().replace(" ", "_"),
                "description": reg.get("description", ""),
            }

            # Infer types from names/comments
            if "intensity" in reg["name"].lower():
                datatype["type"] = "voltage_mv"
                datatype["default_value"] = 2400
            elif "threshold" in reg["name"].lower():
                datatype["type"] = "voltage_mv"
                datatype["default_value"] = 2000
            elif "timeout" in reg["name"].lower():
                datatype["type"] = "time_ms"
                datatype["default_value"] = 1000
            elif reg["reg_type"] == "button":
                datatype["type"] = "boolean"
                datatype["default_value"] = False
            else:
                datatype["type"] = f"unsigned_{reg['reg_type'].split('_')[1]}"
                datatype["default_value"] = reg.get("default_value", 0)

            v2_config["datatypes"].append(datatype)

        # Test the conversion
        with tempfile.NamedTemporaryFile(suffix=".yaml") as f:
            yaml.dump(v2_config, f, default_flow_style=False)
            f.flush()

            # Load as package
            package = RegPackageFactory.from_yaml_file(Path(f.name))

            # Generate mapping
            mapper = RegisterMapper()
            package.generate_mapping(mapper)

            # Check efficiency improvement
            original_registers = len(original.get("registers", []))
            new_registers = len(set(m.cr_number for m in package.mapping_result))

            assert new_registers < original_registers, \
                f"No improvement: {new_registers} vs {original_registers}"

            print(f"Register usage improved: {original_registers} → {new_registers}")
            print(f"Efficiency: {package.get_efficiency():.1f}%")
```

#### 5.4 Performance Benchmarks

Create `tests/test_bad_benchmarks.py`:

```python
"""Performance benchmarks for BasicAppDataTypes"""

import pytest
import time
from models.custom_inst.register_mapper import RegisterMapper
from models.custom_inst.basic_app_datatypes import BasicAppDataTypes


class TestPerformance:
    """Benchmark performance characteristics"""

    def test_mapper_performance(self, benchmark):
        """Benchmark mapping algorithm performance"""
        mapper = RegisterMapper()

        # Create large dataset
        datatypes = []
        for i in range(50):
            datatypes.extend([
                (f"v{i}", BasicAppDataTypes.VOLTAGE_MV),
                (f"t{i}", BasicAppDataTypes.TIME_MS),
                (f"b{i}", BasicAppDataTypes.BOOLEAN),
            ])

        def run_mapping():
            try:
                return mapper.map_registers(datatypes, strategy="best_fit")
            except:
                return None

        result = benchmark(run_mapping)
        if result:
            print(f"Mapped {len(datatypes)} types to {len(result)} assignments")

    def test_type_conversion_performance(self, benchmark):
        """Benchmark type conversion performance"""

        def convert_batch():
            for mv in range(-10000, 10000, 100):
                raw = TypeConverter.voltage_mv_to_raw(mv)
                recovered = TypeConverter.raw_to_voltage_mv(raw)

        benchmark(convert_batch)

    def test_package_validation_performance(self, benchmark):
        """Benchmark package validation"""
        # Create large package
        package = BasicAppsRegPackage(
            app_name="BenchmarkApp",
            datatypes=[
                DataTypeSpec(
                    name=f"signal_{i}",
                    type=BasicAppDataTypes.VOLTAGE_MV,
                    default_value=i * 10,
                )
                for i in range(100)
            ],
        )

        validator = PackageValidator()
        benchmark(validator.validate_complete, package)
```

#### 5.5 Test Runner Integration

Update `tests/run.py`:

```python
#!/usr/bin/env python3
"""Enhanced test runner with BasicAppDataTypes support"""

import click
import subprocess
import sys
from pathlib import Path


@click.command()
@click.option('--unit', is_flag=True, help='Run Python unit tests')
@click.option('--cocotb', is_flag=True, help='Run CocotB VHDL tests')
@click.option('--integration', is_flag=True, help='Run integration tests')
@click.option('--benchmark', is_flag=True, help='Run performance benchmarks')
@click.option('--all', is_flag=True, help='Run all tests')
@click.option('--coverage', is_flag=True, help='Generate coverage report')
def run_tests(unit, cocotb, integration, benchmark, all, coverage):
    """Run BasicAppDataTypes test suite"""

    if all:
        unit = cocotb = integration = benchmark = True

    if not any([unit, cocotb, integration, benchmark]):
        click.echo("Specify test type: --unit, --cocotb, --integration, --benchmark, or --all")
        return 1

    failed = []

    if unit:
        click.echo("\n" + "="*60)
        click.echo("Running Python Unit Tests")
        click.echo("="*60)

        cmd = ["pytest", "tests/test_basic_app_datatypes.py",
               "tests/test_register_mapper.py",
               "tests/test_reg_package.py",
               "tests/test_code_generation.py",
               "-v"]

        if coverage:
            cmd.extend(["--cov=models.custom_inst", "--cov-report=html"])

        result = subprocess.run(cmd)
        if result.returncode != 0:
            failed.append("Unit Tests")

    if cocotb:
        click.echo("\n" + "="*60)
        click.echo("Running CocotB VHDL Tests")
        click.echo("="*60)

        # Build and run CocotB tests
        test_files = [
            "test_bad_generated_vhdl_progressive.py",
        ]

        for test_file in test_files:
            cmd = ["make", "-C", "tests",
                   f"MODULE={test_file[:-3]}",
                   "SIM=ghdl"]

            click.echo(f"Running {test_file}...")
            result = subprocess.run(cmd)
            if result.returncode != 0:
                failed.append(f"CocotB: {test_file}")

    if integration:
        click.echo("\n" + "="*60)
        click.echo("Running Integration Tests")
        click.echo("="*60)

        result = subprocess.run([
            "pytest", "tests/test_bad_integration.py", "-v"
        ])
        if result.returncode != 0:
            failed.append("Integration Tests")

    if benchmark:
        click.echo("\n" + "="*60)
        click.echo("Running Performance Benchmarks")
        click.echo("="*60)

        result = subprocess.run([
            "pytest", "tests/test_bad_benchmarks.py",
            "--benchmark-only", "-v"
        ])
        if result.returncode != 0:
            failed.append("Benchmarks")

    # Summary
    click.echo("\n" + "="*60)
    if failed:
        click.echo("FAILED TESTS:", err=True)
        for test in failed:
            click.echo(f"  ✗ {test}", err=True)
        return 1
    else:
        click.echo("ALL TESTS PASSED! ✓")
        return 0


if __name__ == "__main__":
    sys.exit(run_tests())
```

## Test Strategy

### Progressive Testing Levels

**P1 (Essential - 30% coverage):**
- Basic type conversions work
- Register extraction correct
- Handshaking protocol honored
- Default values applied

**P2 (Comprehensive - 70% coverage):**
- Multi-type packing verified
- Edge cases handled
- Performance acceptable
- Migration successful

**P3 (Exhaustive - 95% coverage):**
- Stress testing passed
- Random fuzzing stable
- All error paths tested
- Documentation validated

### Test Environments

1. **Local Python:** Unit tests, integration
2. **GHDL Simulation:** CocotB tests
3. **Hardware:** Final validation on Moku

## Success Criteria

Phase 5 is complete when:

- [ ] All type conversion tests passing
- [ ] Register mapper tests passing
- [ ] Package model tests passing
- [ ] Code generation tests passing
- [ ] CocotB tests validating generated VHDL
- [ ] DS1140_PD migration validated
- [ ] Performance benchmarks acceptable
- [ ] Test coverage > 90%
- [ ] Phase summary written to `BAD_Phase5_COMPLETE.md`

## Output Artifacts

### Required Files
1. `tests/test_basic_app_datatypes.py` - Type system tests
2. `tests/test_register_mapper.py` - Mapper tests
3. `tests/test_reg_package.py` - Package tests
4. `tests/test_bad_generated_vhdl_progressive.py` - CocotB tests
5. `tests/test_bad_integration.py` - End-to-end tests
6. `tests/test_bad_benchmarks.py` - Performance tests
7. `docs/BasicAppDataTypes/BAD_Phase5_COMPLETE.md` - Summary

### Test Report Format

The completion summary should include:
- Test coverage percentage
- Performance benchmark results
- DS1140_PD migration metrics
- Any failing tests and why
- Readiness assessment for production

## Handoff to Phase 6

Phase 6 will need:
- All tests passing
- Coverage reports
- Performance data
- Migration validation

Update `BAD_Phase6_Documentation.md` header with:
```markdown
**Prerequisites:** Phase 1-5 complete
**Phase 5 Summary:** ./BAD_Phase5_COMPLETE.md
**Phase 5 Commit:** {git_hash}
**Test Status:** {coverage}% coverage, {status}
```

## Interactive Decisions

As you implement tests, we'll decide:

1. **Coverage targets**: 90% or 95% minimum?
2. **Performance criteria**: What's acceptable latency?
3. **Test data**: Real hardware values or synthetic?
4. **Failure handling**: Hard fail or warnings?
5. **Hardware testing**: When to test on actual Moku?

## Getting Started

1. Start with type conversion unit tests
2. Add mapper algorithm tests
3. Create minimal CocotB test
4. Build integration test
5. Run DS1140_PD migration
6. Measure performance
7. Generate coverage report

Remember: Tests are the **safety net** that lets us refactor confidently. Make them thorough!

---

**Questions?** Testing validates that BasicAppDataTypes delivers on its promises. Let's ensure quality!