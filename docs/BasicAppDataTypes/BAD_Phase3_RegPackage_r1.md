# BAD Phase 3: Register Interface Package (Revision 1)

**Phase:** 3 of 6
**Goal:** Create type-safe register interface package for CustomInstrument applications
**Prerequisites:** Phase 1-2 complete
**Phase 1 Summary:** [BAD_Phase1_COMPLETE.md](./BAD_Phase1_COMPLETE.md)
**Phase 2 Summary:** [BAD_Phase2_COMPLETE.md](./BAD_Phase2_COMPLETE.md)
**Output:** `models/custom_inst/reg_package.py` with clean integration to `moku-models`

---

## Architecture Context

### What We Have (Phase 1-2)
```
libs/basic-app-datatypes/
  ✅ BasicAppDataTypes (23 types: voltage, time, boolean)
  ✅ RegisterMapper (pure algorithm: types → CR6-CR17 with bit packing)
  ✅ 46/46 tests passing

models/custom_inst/
  ✅ BADRegisterMapper (Pydantic wrapper for RegisterMapper)
  ✅ BADRegisterConfig (minimal: name, datatype, description, default)

moku-models/ (git submodule)
  ✅ MokuConfig (deployment abstraction)
  ✅ SlotConfig.control_registers: dict[int, int]  # CR number → raw value
  ✅ Platform models (Go/Lab/Pro/Delta)
```

### What Phase 3 Adds
```
models/custom_inst/reg_package.py (NEW)
  - DataTypeSpec: Rich register type with UI metadata
  - BasicAppsRegPackage: Complete register interface
  - Integration: BAD → MokuConfig via to_control_registers()

examples/ (NEW)
  - DS1140_PD_interface.yaml: Example register interface
  - DS1140_PD_deployment.py: Integration with MokuConfig
```

### What Gets Deleted (Clean Break)
```
models/custom_inst/
  ❌ app_register.py (RegisterType enum, AppRegister)
  ❌ custom_inst_app.py (CustomInstApp - replaced by BasicAppsRegPackage)
```

---

## Git Workflow

**Branch:** `feature/BAD/P3`

**Starting this phase:**
```bash
git checkout feature/BAD-main
git checkout -b feature/BAD/P3
```

**During development (commit frequently):**
```bash
# Each deliverable gets a commit
git add <files>
git commit -m "feat(BAD/P3): <description>"
```

**Completing this phase:**
```bash
# Final commit
git add .
git commit -m "feat(BAD/P3): Complete Phase 3 - Register interface package"

# Write completion summary
# docs/BasicAppDataTypes/BAD_Phase3_COMPLETE.md

# Merge to feature branch
git checkout feature/BAD-main
git merge --no-ff feature/BAD/P3 -m "Merge Phase 3: Register interface package"
```

---

## Phase 3 Objectives

### Primary Goals
1. Create `DataTypeSpec` - rich register type with UI metadata
2. Create `BasicAppsRegPackage` - complete register interface specification
3. Integrate with existing `BADRegisterMapper` (Phase 2)
4. Export to `MokuConfig.control_registers` format
5. Delete legacy code (clean break)

### Non-Goals (Defer to Phase 4)
- ❌ VHDL code generation
- ❌ Jinja2 template updates
- ❌ tools/generate_custom_inst.py changes
- ❌ Actual DS1140_PD hardware rebuild

---

## Deliverable 1: DataTypeSpec

**File:** `models/custom_inst/reg_package.py`

```python
"""
Register interface package for BasicAppDataTypes.

Provides type-safe register interface specification with:
- DataTypeSpec: Rich type definition with UI metadata
- BasicAppsRegPackage: Complete register interface container
- Integration with Phase 2 mapper (BADRegisterMapper)
- Export to MokuConfig.control_registers format

Design:
- Platform-agnostic (no bitstream paths, no MCC routing)
- Focused on register interface only
- Integrates with moku-models via to_control_registers()
"""

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


class DataTypeSpec(BaseModel):
    """
    Rich specification for a single register data element.

    Extends BADRegisterConfig with UI metadata for TUI/GUI generation.

    Attributes:
        name: User-defined variable name (e.g., "intensity", "arm_probe")
        datatype: BasicAppDataTypes enum value
        description: Human-readable description
        default_value: Optional default value (must match type constraints)

        # UI metadata (Phase 3 addition)
        min_value: Minimum allowed value (for sliders, validation)
        max_value: Maximum allowed value (for sliders, validation)
        display_name: Human-friendly name for UI (e.g., "Intensity (mV)")
        units: Physical units (e.g., "mV", "ms", "ns")

    Example:
        >>> dt = DataTypeSpec(
        ...     name="intensity",
        ...     datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
        ...     description="Output intensity voltage",
        ...     default_value=2400,  # mV
        ...     min_value=0,
        ...     max_value=5000,
        ...     display_name="Intensity",
        ...     units="mV"
        ... )
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Variable name (becomes VHDL signal)"
    )
    datatype: BasicAppDataTypes = Field(
        ...,
        description="BasicAppDataTypes enum value"
    )
    description: str = Field(
        default="",
        max_length=200,
        description="Human-readable description"
    )
    default_value: Optional[Union[int, bool]] = Field(
        default=None,
        description="Default value (must match type constraints)"
    )

    # UI metadata (all optional)
    min_value: Optional[Union[int, float]] = Field(
        default=None,
        description="Minimum allowed value (for UI sliders/validation)"
    )
    max_value: Optional[Union[int, float]] = Field(
        default=None,
        description="Maximum allowed value (for UI sliders/validation)"
    )
    display_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Human-friendly display name for UI"
    )
    units: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Physical units (e.g., 'mV', 'ms', 'ns')"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is VHDL-safe."""
        # Must start with letter
        if not v[0].isalpha():
            raise ValueError(f"Name must start with letter: '{v}'")

        # Only alphanumeric + underscore
        if not all(c.isalnum() or c == '_' for c in v):
            raise ValueError(f"Name must contain only alphanumeric and underscore: '{v}'")

        # VHDL reserved words (basic check)
        reserved = {
            'signal', 'entity', 'architecture', 'process', 'begin', 'end',
            'if', 'then', 'else', 'loop', 'for', 'while', 'case', 'when'
        }
        if v.lower() in reserved:
            raise ValueError(f"Name cannot be VHDL reserved word: '{v}'")

        return v

    @model_validator(mode='after')
    def validate_default_value(self) -> 'DataTypeSpec':
        """Validate default_value matches datatype constraints."""
        if self.default_value is None:
            return self

        metadata = TYPE_REGISTRY[self.datatype]

        # Boolean special case
        if self.datatype == BasicAppDataTypes.BOOLEAN:
            if not isinstance(self.default_value, bool):
                raise ValueError(
                    f"Boolean type requires bool default_value, got {type(self.default_value)}"
                )
            return self

        # Numeric types
        if not isinstance(self.default_value, int):
            raise ValueError(
                f"Numeric type requires int default_value, got {type(self.default_value)}"
            )

        # Range check (use TYPE_REGISTRY)
        if metadata.min_value is not None and self.default_value < metadata.min_value:
            raise ValueError(
                f"default_value {self.default_value} below min {metadata.min_value} "
                f"for type {self.datatype.value}"
            )

        if metadata.max_value is not None and self.default_value > metadata.max_value:
            raise ValueError(
                f"default_value {self.default_value} above max {metadata.max_value} "
                f"for type {self.datatype.value}"
            )

        return self

    @model_validator(mode='after')
    def validate_min_max_range(self) -> 'DataTypeSpec':
        """Validate min_value <= max_value if both specified."""
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(
                    f"min_value ({self.min_value}) cannot be greater than "
                    f"max_value ({self.max_value})"
                )
        return self

    def get_bit_width(self) -> int:
        """Get bit width from type registry."""
        return TYPE_REGISTRY[self.datatype].bit_width

    def to_bad_register_config(self) -> BADRegisterConfig:
        """Convert to Phase 2 BADRegisterConfig (for mapper integration)."""
        return BADRegisterConfig(
            name=self.name,
            datatype=self.datatype,
            description=self.description,
            default_value=self.default_value
        )
```

---

## Deliverable 2: BasicAppsRegPackage

**Continuation of `models/custom_inst/reg_package.py`:**

```python
class BasicAppsRegPackage(BaseModel):
    """
    Complete register interface specification for CustomInstrument applications.

    This is the single source of truth for application register interfaces.
    Platform-agnostic - does not include bitstream paths, MCC routing, or
    platform-specific configuration (those are handled by moku-models).

    Attributes:
        app_name: Application name (e.g., "DS1140_PD")
        description: Human-readable description
        datatypes: List of DataTypeSpec objects
        mapping_strategy: Packing strategy for register allocation

    Integration:
        - Uses BADRegisterMapper (Phase 2) for actual mapping
        - Exports to MokuConfig.control_registers via to_control_registers()

    Example:
        >>> package = BasicAppsRegPackage(
        ...     app_name="DS1140_PD",
        ...     description="EMFI probe driver",
        ...     datatypes=[
        ...         DataTypeSpec(name="arm_probe", datatype=BasicAppDataTypes.BOOLEAN),
        ...         DataTypeSpec(name="intensity", datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
        ...     ],
        ...     mapping_strategy="best_fit"
        ... )
        >>>
        >>> # Generate mapping
        >>> mappings = package.generate_mapping()
        >>>
        >>> # Export to MokuConfig format
        >>> control_regs = package.to_control_registers()
        >>> # Returns: {6: 0x00000000, 7: 0x09600000, ...}
    """
    # Package identity
    app_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Application name"
    )
    description: str = Field(
        default="",
        max_length=500,
        description="Human-readable description"
    )

    # Register interface
    datatypes: List[DataTypeSpec] = Field(
        ...,
        min_length=1,
        description="List of register data type specifications"
    )
    mapping_strategy: Literal["first_fit", "best_fit", "type_clustering"] = Field(
        default="best_fit",
        description="Register packing strategy"
    )

    # Internal cache (not serialized)
    _mapping_cache: Optional[List[RegisterMapping]] = None

    @field_validator('datatypes')
    @classmethod
    def validate_unique_names(cls, v: List[DataTypeSpec]) -> List[DataTypeSpec]:
        """Validate all datatype names are unique."""
        names = [dt.name for dt in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate datatype names found: {set(duplicates)}")
        return v

    @model_validator(mode='after')
    def validate_total_bits(self) -> 'BasicAppsRegPackage':
        """Validate total bits fit in 384-bit limit (12 registers × 32 bits)."""
        total_bits = sum(dt.get_bit_width() for dt in self.datatypes)
        if total_bits > 384:
            raise ValueError(
                f"Total bits ({total_bits}) exceeds 384-bit limit "
                f"(12 registers × 32 bits)"
            )
        return self

    def generate_mapping(self) -> List[RegisterMapping]:
        """
        Generate register mapping using Phase 2 mapper.

        Returns:
            List of RegisterMapping objects with CR assignments

        Caches result to avoid recomputation.
        """
        if self._mapping_cache is None:
            # Convert to BADRegisterMapper format
            mapper = BADRegisterMapper(
                registers=[dt.to_bad_register_config() for dt in self.datatypes],
                strategy=self.mapping_strategy
            )
            self._mapping_cache = mapper.to_register_mappings()

        return self._mapping_cache

    def to_control_registers(self) -> dict[int, int]:
        """
        Export to MokuConfig.control_registers format.

        Returns:
            Dictionary mapping CR number → raw 32-bit value
            Compatible with SlotConfig.control_registers in moku-models

        Example:
            >>> package.to_control_registers()
            {6: 0x00000960, 7: 0x3DCF0000, 8: 0x26660000}
        """
        from basic_app_datatypes import TypeConverter

        mappings = self.generate_mapping()

        # Build CR → raw value mapping
        result = {}

        for mapping in mappings:
            # Get DataTypeSpec for this mapping
            dt_spec = next(dt for dt in self.datatypes if dt.name == mapping.name)

            if dt_spec.default_value is not None:
                # Convert typed value to raw bits
                if dt_spec.datatype == BasicAppDataTypes.BOOLEAN:
                    raw_value = 1 if dt_spec.default_value else 0
                else:
                    # Use TypeConverter for voltage/time types
                    raw_value = TypeConverter.to_raw(
                        dt_spec.datatype,
                        dt_spec.default_value
                    )

                # Initialize CR if not present
                if mapping.cr_number not in result:
                    result[mapping.cr_number] = 0

                # Shift raw value to correct bit position and OR into register
                msb, lsb = mapping.bit_slice
                bit_width = msb - lsb + 1

                # Mask raw value to bit width
                mask = (1 << bit_width) - 1
                raw_value &= mask

                # Shift and pack
                result[mapping.cr_number] |= (raw_value << lsb)

        return result

    def to_yaml(self, path: Path) -> None:
        """
        Save register interface to YAML file.

        Args:
            path: Output YAML file path

        Format:
            app_name: DS1140_PD
            description: "..."
            mapping_strategy: best_fit
            datatypes:
              - name: intensity
                datatype: voltage_output_05v_s16
                description: "..."
                default_value: 2400
                min_value: 0
                max_value: 5000
                display_name: "Intensity"
                units: "mV"
        """
        data = {
            'app_name': self.app_name,
            'description': self.description,
            'mapping_strategy': self.mapping_strategy,
            'datatypes': [
                {
                    'name': dt.name,
                    'datatype': dt.datatype.value,  # Serialize enum as string
                    'description': dt.description,
                    'default_value': dt.default_value,
                    'min_value': dt.min_value,
                    'max_value': dt.max_value,
                    'display_name': dt.display_name,
                    'units': dt.units,
                }
                for dt in self.datatypes
            ]
        }

        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, path: Path) -> 'BasicAppsRegPackage':
        """
        Load register interface from YAML file.

        Args:
            path: Input YAML file path

        Returns:
            BasicAppsRegPackage instance
        """
        with open(path) as f:
            data = yaml.safe_load(f)

        # Parse datatypes
        datatypes = []
        for dt_dict in data.get('datatypes', []):
            datatypes.append(DataTypeSpec(
                name=dt_dict['name'],
                datatype=BasicAppDataTypes(dt_dict['datatype']),  # Parse enum from string
                description=dt_dict.get('description', ''),
                default_value=dt_dict.get('default_value'),
                min_value=dt_dict.get('min_value'),
                max_value=dt_dict.get('max_value'),
                display_name=dt_dict.get('display_name'),
                units=dt_dict.get('units'),
            ))

        return cls(
            app_name=data['app_name'],
            description=data.get('description', ''),
            datatypes=datatypes,
            mapping_strategy=data.get('mapping_strategy', 'best_fit')
        )
```

---

## Deliverable 3: Example Register Interface YAML

**File:** `examples/DS1140_PD_interface.yaml`

```yaml
# DS1140_PD Register Interface Specification
# Platform-agnostic register definitions for EMFI probe driver
#
# This file defines the type-safe register interface using BasicAppDataTypes.
# Automatic register mapping reduces usage from 9 registers → 3 registers (66.7% savings).
#
# See: docs/BasicAppDataTypes/BAD_Phase3_RegPackage_r1.md

app_name: DS1140_PD
description: "EMFI probe driver register interface with automatic mapping"

mapping_strategy: best_fit  # Optimal packing (alternatives: first_fit, type_clustering)

datatypes:
  # Control signals (1-bit booleans)
  - name: arm_probe
    datatype: boolean
    description: "Arm the probe driver (one-shot operation)"
    default_value: false
    display_name: "Arm Probe"

  - name: force_fire
    datatype: boolean
    description: "Manual trigger for testing (bypasses threshold detection)"
    default_value: false
    display_name: "Force Fire"

  - name: reset_fsm
    datatype: boolean
    description: "Reset state machine to READY state"
    default_value: false
    display_name: "Reset FSM"

  # Timing configuration
  - name: clock_divider
    datatype: unsigned_8
    description: "FSM timing control divider (0=÷1, 1=÷2, ..., 15=÷16)"
    default_value: 0
    min_value: 0
    max_value: 15
    display_name: "Clock Divider"

  - name: arm_timeout
    datatype: pulse_duration_ms_u16
    description: "Maximum time in armed state before timeout"
    default_value: 1000  # 1 second
    min_value: 0
    max_value: 5000
    display_name: "Arm Timeout"
    units: "ms"

  - name: firing_duration
    datatype: pulse_duration_ns_u8
    description: "Number of cycles to remain in FIRING state"
    default_value: 16
    min_value: 1
    max_value: 32
    display_name: "Firing Duration"
    units: "cycles"

  - name: cooling_duration
    datatype: pulse_duration_ns_u8
    description: "Number of cycles to remain in COOLING state"
    default_value: 16
    min_value: 8
    max_value: 255
    display_name: "Cooling Duration"
    units: "cycles"

  # Voltage configuration
  - name: trigger_threshold
    datatype: voltage_input_25v_s16
    description: "Voltage threshold for trigger detection"
    default_value: 2400  # 2.4V in mV
    min_value: -25000
    max_value: 25000
    display_name: "Trigger Threshold"
    units: "mV"

  - name: intensity
    datatype: voltage_output_05v_s16
    description: "Output intensity voltage (hardware clamped to 3.0V)"
    default_value: 2000  # 2.0V safe default
    min_value: 0
    max_value: 5000
    display_name: "Intensity"
    units: "mV"

# Expected mapping result (best_fit strategy):
# CR6  [31:16] arm_timeout (16-bit)       | [15:0] intensity (16-bit)
# CR7  [31:16] trigger_threshold (16-bit) | [15:8] clock_divider (8-bit) | [7:0] cooling_duration (8-bit)
# CR8  [31:24] firing_duration (8-bit)    | [23] arm_probe (1-bit) | [22] force_fire (1-bit) | [21] reset_fsm (1-bit)
#
# Total: 3 registers (vs 9 manual registers = 66.7% savings)
# Efficiency: 75/384 bits used (19.53%)
```

---

## Deliverable 4: Integration Example

**File:** `examples/DS1140_PD_deployment.py`

```python
#!/usr/bin/env python3
"""
DS1140_PD Deployment Example

Demonstrates integration between BasicAppsRegPackage and MokuConfig.

Shows how to:
1. Load register interface from YAML
2. Generate register mapping
3. Export to MokuConfig.control_registers
4. Deploy to Moku hardware

Usage:
    python examples/DS1140_PD_deployment.py --device 192.168.1.100 --bitstream path/to/bitstream.tar
"""

from pathlib import Path
from moku_models import MokuConfig, SlotConfig, MokuConnection, MOKU_GO_PLATFORM

# Import Phase 3 register package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.custom_inst.reg_package import BasicAppsRegPackage


def main():
    # Step 1: Load register interface
    print("Loading register interface...")
    interface_path = Path(__file__).parent / "DS1140_PD_interface.yaml"
    reg_interface = BasicAppsRegPackage.from_yaml(interface_path)

    print(f"  App: {reg_interface.app_name}")
    print(f"  Datatypes: {len(reg_interface.datatypes)}")
    print(f"  Strategy: {reg_interface.mapping_strategy}")

    # Step 2: Generate register mapping
    print("\nGenerating register mapping...")
    mappings = reg_interface.generate_mapping()

    print(f"  Mapped to {len(set(m.cr_number for m in mappings))} registers")
    for mapping in mappings:
        msb, lsb = mapping.bit_slice
        print(f"    CR{mapping.cr_number}[{msb}:{lsb}] = {mapping.name}")

    # Step 3: Export to control registers
    print("\nExporting control registers...")
    control_regs = reg_interface.to_control_registers()

    print(f"  Generated {len(control_regs)} control register defaults:")
    for cr_num, value in sorted(control_regs.items()):
        print(f"    CR{cr_num} = 0x{value:08X}")

    # Step 4: Create MokuConfig
    print("\nCreating MokuConfig...")
    config = MokuConfig(
        platform=MOKU_GO_PLATFORM,
        slots={
            1: SlotConfig(
                instrument='CloudCompile',
                bitstream='modules/DS1140-PD/latest/25ff_bitstreams.tar',
                control_registers=control_regs  # ← BAD-generated values!
            ),
            2: SlotConfig(
                instrument='Oscilloscope',
                settings={'sample_rate': 125e6}
            )
        },
        routing=[
            MokuConnection(source='Input1', destination='Slot1InA'),
            MokuConnection(source='Slot1OutA', destination='Output1'),
            MokuConnection(source='Slot1OutA', destination='Slot2InA')
        ]
    )

    print("  ✓ MokuConfig created successfully")
    print(f"  Platform: {config.platform.name}")
    print(f"  Slots: {list(config.slots.keys())}")
    print(f"  Routing: {len(config.routing)} connections")

    # Step 5: Deploy (optional - requires hardware)
    print("\nTo deploy to hardware:")
    print("  uv run python tools/moku_go.py deploy \\")
    print("    --device <ip_address> \\")
    print("    --bitstream modules/DS1140-PD/latest/25ff_bitstreams.tar \\")
    print("    --slot 1")

    print("\n✓ Integration example complete!")


if __name__ == '__main__':
    main()
```

---

## Deliverable 5: Unit Tests

**File:** `python_tests/test_reg_package.py`

```python
"""
Unit tests for BasicAppsRegPackage (Phase 3).

Tests:
- DataTypeSpec validation
- BasicAppsRegPackage validation
- YAML serialization/deserialization
- Control register export
- Integration with MokuConfig
"""

import pytest
from pathlib import Path
from basic_app_datatypes import BasicAppDataTypes
from models.custom_inst.reg_package import DataTypeSpec, BasicAppsRegPackage


class TestDataTypeSpec:
    """Tests for DataTypeSpec validation."""

    def test_valid_datatype_spec(self):
        """Test creating a valid DataTypeSpec."""
        dt = DataTypeSpec(
            name="intensity",
            datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
            description="Output voltage",
            default_value=2400,
            min_value=0,
            max_value=5000,
            display_name="Intensity",
            units="mV"
        )

        assert dt.name == "intensity"
        assert dt.datatype == BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
        assert dt.default_value == 2400
        assert dt.units == "mV"

    def test_name_validation_must_start_with_letter(self):
        """Test name must start with letter."""
        with pytest.raises(ValueError, match="must start with letter"):
            DataTypeSpec(
                name="123_invalid",
                datatype=BasicAppDataTypes.BOOLEAN
            )

    def test_name_validation_reserved_word(self):
        """Test name cannot be VHDL reserved word."""
        with pytest.raises(ValueError, match="reserved word"):
            DataTypeSpec(
                name="signal",
                datatype=BasicAppDataTypes.BOOLEAN
            )

    def test_default_value_type_mismatch(self):
        """Test default_value must match type (bool vs int)."""
        with pytest.raises(ValueError, match="bool default_value"):
            DataTypeSpec(
                name="enable",
                datatype=BasicAppDataTypes.BOOLEAN,
                default_value=1  # Should be bool, not int
            )

    def test_default_value_out_of_range(self):
        """Test default_value must be within type range."""
        with pytest.raises(ValueError, match="above max"):
            DataTypeSpec(
                name="voltage",
                datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
                default_value=100000  # Exceeds max for voltage type
            )

    def test_min_max_validation(self):
        """Test min_value must be <= max_value."""
        with pytest.raises(ValueError, match="cannot be greater than"):
            DataTypeSpec(
                name="counter",
                datatype=BasicAppDataTypes.UNSIGNED_8,
                min_value=100,
                max_value=50  # Invalid: min > max
            )

    def test_to_bad_register_config(self):
        """Test conversion to BADRegisterConfig."""
        dt = DataTypeSpec(
            name="intensity",
            datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
            description="Output voltage",
            default_value=2400
        )

        config = dt.to_bad_register_config()

        assert config.name == "intensity"
        assert config.datatype == BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
        assert config.default_value == 2400


class TestBasicAppsRegPackage:
    """Tests for BasicAppsRegPackage."""

    def test_valid_package(self):
        """Test creating a valid package."""
        package = BasicAppsRegPackage(
            app_name="TestApp",
            description="Test application",
            datatypes=[
                DataTypeSpec(
                    name="enable",
                    datatype=BasicAppDataTypes.BOOLEAN,
                    default_value=False
                ),
                DataTypeSpec(
                    name="voltage",
                    datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
                    default_value=2400
                )
            ]
        )

        assert package.app_name == "TestApp"
        assert len(package.datatypes) == 2
        assert package.mapping_strategy == "best_fit"

    def test_duplicate_names_rejected(self):
        """Test duplicate datatype names are rejected."""
        with pytest.raises(ValueError, match="Duplicate datatype names"):
            BasicAppsRegPackage(
                app_name="TestApp",
                datatypes=[
                    DataTypeSpec(name="voltage", datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
                    DataTypeSpec(name="voltage", datatype=BasicAppDataTypes.VOLTAGE_INPUT_20V_S16),
                ]
            )

    def test_total_bits_overflow(self):
        """Test validation of 384-bit limit."""
        # Create 13 x 32-bit types (416 bits > 384 limit)
        datatypes = [
            DataTypeSpec(
                name=f"type_{i}",
                datatype=BasicAppDataTypes.UNSIGNED_16
            )
            for i in range(25)  # 25 * 16 = 400 bits
        ]

        with pytest.raises(ValueError, match="exceeds 384-bit limit"):
            BasicAppsRegPackage(
                app_name="OverflowTest",
                datatypes=datatypes
            )

    def test_generate_mapping(self):
        """Test register mapping generation."""
        package = BasicAppsRegPackage(
            app_name="TestApp",
            datatypes=[
                DataTypeSpec(name="enable", datatype=BasicAppDataTypes.BOOLEAN),
                DataTypeSpec(name="counter", datatype=BasicAppDataTypes.UNSIGNED_8),
                DataTypeSpec(name="voltage", datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
            ]
        )

        mappings = package.generate_mapping()

        assert len(mappings) == 3
        assert all(6 <= m.cr_number <= 17 for m in mappings)

    def test_to_control_registers(self):
        """Test export to MokuConfig format."""
        package = BasicAppsRegPackage(
            app_name="TestApp",
            datatypes=[
                DataTypeSpec(
                    name="enable",
                    datatype=BasicAppDataTypes.BOOLEAN,
                    default_value=True
                ),
                DataTypeSpec(
                    name="counter",
                    datatype=BasicAppDataTypes.UNSIGNED_8,
                    default_value=42
                ),
            ]
        )

        control_regs = package.to_control_registers()

        # Should have at least one CR
        assert len(control_regs) > 0

        # All CR numbers should be in valid range
        assert all(6 <= cr <= 17 for cr in control_regs.keys())

        # All values should be 32-bit integers
        assert all(0 <= val <= 0xFFFFFFFF for val in control_regs.values())

    def test_yaml_roundtrip(self, tmp_path):
        """Test YAML serialization and deserialization."""
        original = BasicAppsRegPackage(
            app_name="TestApp",
            description="Test application",
            datatypes=[
                DataTypeSpec(
                    name="intensity",
                    datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
                    description="Output voltage",
                    default_value=2400,
                    display_name="Intensity",
                    units="mV"
                )
            ],
            mapping_strategy="best_fit"
        )

        # Save to YAML
        yaml_path = tmp_path / "test.yaml"
        original.to_yaml(yaml_path)

        # Load from YAML
        loaded = BasicAppsRegPackage.from_yaml(yaml_path)

        # Compare
        assert loaded.app_name == original.app_name
        assert loaded.description == original.description
        assert len(loaded.datatypes) == len(original.datatypes)
        assert loaded.datatypes[0].name == original.datatypes[0].name
        assert loaded.datatypes[0].datatype == original.datatypes[0].datatype
        assert loaded.mapping_strategy == original.mapping_strategy


class TestMokuConfigIntegration:
    """Test integration with moku-models."""

    def test_control_registers_compatible_with_moku_config(self):
        """Test control_registers export is MokuConfig-compatible."""
        from moku_models import MokuConfig, SlotConfig, MOKU_GO_PLATFORM

        # Create package
        package = BasicAppsRegPackage(
            app_name="TestApp",
            datatypes=[
                DataTypeSpec(
                    name="enable",
                    datatype=BasicAppDataTypes.BOOLEAN,
                    default_value=True
                )
            ]
        )

        # Export control registers
        control_regs = package.to_control_registers()

        # Create MokuConfig with exported values
        config = MokuConfig(
            platform=MOKU_GO_PLATFORM,
            slots={
                1: SlotConfig(
                    instrument='CloudCompile',
                    bitstream='test.tar',
                    control_registers=control_regs  # ← Should work!
                )
            }
        )

        # Validate
        assert config.slots[1].control_registers is not None
        assert len(config.slots[1].control_registers) == len(control_regs)
```

---

## Success Criteria

Phase 3 is complete when:

- [x] `models/custom_inst/reg_package.py` implemented
  - [x] DataTypeSpec with UI metadata
  - [x] BasicAppsRegPackage with mapping integration
  - [x] to_control_registers() export method
  - [x] YAML serialization (to_yaml/from_yaml)

- [x] Legacy code deleted (clean break)
  - [x] models/custom_inst/app_register.py removed
  - [x] models/custom_inst/custom_inst_app.py removed

- [x] Examples created
  - [x] examples/DS1140_PD_interface.yaml
  - [x] examples/DS1140_PD_deployment.py

- [x] Tests passing
  - [x] DataTypeSpec validation tests
  - [x] BasicAppsRegPackage tests
  - [x] YAML roundtrip tests
  - [x] MokuConfig integration tests

- [x] Documentation
  - [x] Phase summary written (BAD_Phase3_COMPLETE.md)

---

## Handoff to Phase 4

Phase 4 will need:
- ✅ BasicAppsRegPackage API (complete)
- ✅ YAML loading utilities (complete)
- ✅ Example register interfaces (DS1140_PD)
- ✅ Integration with moku-models (to_control_registers)

Phase 4 tasks:
- Update `tools/generate_custom_inst.py` to use BasicAppsRegPackage
- Update VHDL Jinja2 templates (shim, main)
- Generate VHDL from BasicAppsRegPackage
- End-to-end VHDL generation working

---

## Notes

**Key Design Decisions:**

1. **DataTypeSpec extends BADRegisterConfig semantically**
   - Adds UI metadata (min/max, display_name, units)
   - Converts to BADRegisterConfig for mapper integration

2. **BasicAppsRegPackage is platform-agnostic**
   - No bitstream paths (that's MokuConfig)
   - No MCC routing (that's MokuConnection)
   - Only register interface specification

3. **Clean integration with Phase 2**
   - Uses BADRegisterMapper internally
   - Reuses all Phase 2 mapping logic
   - No duplication

4. **Export to moku-models**
   - to_control_registers() bridges to SlotConfig
   - Compatible with existing deployment tools
   - No changes needed to tools/moku_go.py

5. **Clean break from legacy**
   - app_register.py deleted
   - custom_inst_app.py deleted
   - No backward compatibility needed

---

**Last Updated:** 2025-01-02
**Phase Status:** Ready to implement
**Next Action:** Begin implementation with commit-per-deliverable workflow
