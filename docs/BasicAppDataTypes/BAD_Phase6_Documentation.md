# BAD Phase 6: Documentation and Deployment

**Phase:** 6 of 6
**Goal:** Create comprehensive documentation and deployment guides
**Prerequisites:** Phase 1-5 complete
**Phase 1-5 Summaries:** ./BAD_Phase{1-5}_COMPLETE.md
**Test Status:** (from Phase 5)
**Output:** User guides, API docs, migration guides, and deployment instructions

## Git Workflow

**Branch:** `feature/BAD/P6`

**Starting this phase:**
```bash
git checkout feature/BAD
git checkout -b feature/BAD/P6
```

**During development:**
```bash
# Commit frequently as you implement
git add <files>
git commit -m "feat(BAD/P6): <description>"
```

**Completing this phase:**
```bash
# Final commit with phase completion
git add .
git commit -m "feat(BAD/P6): Complete Phase 6 - Documentation and deployment"

# Write BAD_Phase6_COMPLETE.md with summary

# Merge back to feature branch
git checkout feature/BAD
git merge --no-ff feature/BAD/P6 -m "Merge Phase 6: Documentation and deployment guides"

# Update orchestrator status table to show all phases complete
```

**Final merge to main:**
Once all phases are complete, tested, and documented:
```bash
git checkout main
git merge --no-ff feature/BAD -m "feat: Add BasicAppDataTypes system"
```

**Full workflow:** See [BAD_MASTER_Orchestrator.md](./BAD_MASTER_Orchestrator.md#git-workflow)

## Context Loading

Please review these files and all previous phase outputs:

```bash
# All phase summaries
ls docs/BasicAppDataTypes/BAD_Phase*_COMPLETE.md

# Generated artifacts from previous phases
ls models/custom_inst/basic_app_datatypes.py
ls models/custom_inst/register_mapper.py
ls models/custom_inst/reg_package.py

# Example generated VHDL
ls VHDL/apps/DS1140_PD_v2/

# Test results
pytest tests/test_basic_app_datatypes.py --tb=no
```

## Phase 6 Objectives

### Primary Goals
1. Create user-facing documentation
2. Generate API reference documentation
3. Write migration guides for existing apps
4. Document deployment procedures
5. Create troubleshooting guide
6. Update project documentation (README, CLAUDE.md)

### Documentation Structure

```
docs/BasicAppDataTypes/
├── User_Guide.md                 # End-user documentation
├── API_Reference.md              # Developer API docs
├── Migration_Guide.md            # Step-by-step migration
├── Type_Reference.md             # All types with examples
├── Troubleshooting.md           # Common issues and solutions
├── Examples/
│   ├── simple_voltage.yaml      # Minimal example
│   ├── complex_fsm.yaml        # Advanced example
│   └── ds1140_pd_v2.yaml       # Real migration
└── generated/
    ├── api_docs.html            # Auto-generated API docs
    └── coverage_report.html     # Test coverage report
```

### Specific Deliverables

#### 6.1 User Guide

Create `docs/BasicAppDataTypes/User_Guide.md`:

```markdown
# BasicAppDataTypes User Guide

## Overview

BasicAppDataTypes revolutionizes how custom instruments handle register communication in EZ-EMFI. Instead of manually managing bit positions and type conversions, you declare your data types and let the system handle the rest.

## Quick Start

### 1. Create Your Application YAML

```yaml
package_version: "2.0"
app_name: "MyEMFIProbe"
description: "Custom EMFI probe controller"

datatypes:
  - name: "output_voltage"
    type: "voltage_mv"
    description: "Probe output voltage"
    default_value: 2400  # 2.4V in millivolts
    min_value: -5000
    max_value: 5000
    units: "mV"

  - name: "pulse_duration"
    type: "time_ms"
    description: "Pulse length"
    default_value: 10  # 10 milliseconds
    max_value: 1000
    units: "ms"

  - name: "enable_output"
    type: "boolean"
    description: "Enable probe output"
    default_value: false
```

### 2. Generate VHDL

```bash
python tools/generate_custom_inst.py MyEMFIProbe.yaml
```

This generates:
- `MyEMFIProbe_custom_inst_shim.vhd` - Register interface
- `MyEMFIProbe_custom_inst_main.vhd` - Your application logic
- `MyEMFIProbe_mapping.md` - Register documentation

### 3. Implement Your Logic

Edit the generated `main.vhd`:

```vhdl
-- Signals arrive pre-typed from shim
process(Clk)
begin
    if rising_edge(Clk) then
        if enable_output = '1' then
            Output <= output_voltage;  -- Already signed(15 downto 0)
        else
            Output <= (others => '0');
        end if;
    end if;
end process;
```

## Type System

### Available Types

| Type | Bit Width | Range | Resolution | Use Case |
|------|-----------|--------|------------|----------|
| `voltage_mv` | 16 | ±10V | 305µV | Voltages, amplitudes |
| `time_ms` | 16 | 0-65.5s | 1ms | Durations, delays |
| `time_us` | 24 | 0-16.7s | 1µs | Fine timing |
| `time_ns` | 32 | 0-4.29s | 1ns | Precise timing |
| `boolean` | 1 | true/false | - | Flags, enables |
| `unsigned_8` | 8 | 0-255 | 1 | Counters, IDs |
| `unsigned_16` | 16 | 0-65535 | 1 | Large counters |
| `signed_16` | 16 | ±32767 | 1 | Signed values |

### Type Features

**Automatic Conversions:**
- Voltage values in millivolts → 16-bit signed
- Time values in ms/us/ns → clock cycles
- Booleans → single bits

**Range Validation:**
- Min/max constraints enforced
- Clear error messages for violations

**Default Values:**
- Type-appropriate defaults
- YAML-specified defaults
- Reset behavior guaranteed

## Register Mapping

### Automatic Packing

BasicAppDataTypes automatically packs your data into the 12 available registers (CR6-CR17):

```yaml
# Your YAML defines data
datatypes:
  - name: "voltage1"
    type: "voltage_mv"
  - name: "voltage2"
    type: "voltage_mv"
  - name: "flag1"
    type: "boolean"

# System generates optimal packing:
# CR6[31:16] ← voltage1
# CR6[15:0]  ← voltage2
# CR7[31]    ← flag1
# CR7[30:0]  ← unused
```

### Mapping Strategies

**Auto (Recommended):**
```yaml
mapping:
  strategy: "auto"  # System optimizes packing
```

**Manual (Legacy Support):**
```yaml
datatypes:
  - name: "my_signal"
    type: "voltage_mv"
    manual_cr: 6
    manual_bits: [31, 16]
```

## Python Control

### Basic Usage

```python
from moku.instruments import CustomInstrument
import yaml

# Load your app configuration
with open("MyEMFIProbe.yaml") as f:
    config = yaml.safe_load(f)

# Connect to Moku
moku = CustomInstrument('192.168.0.1', mcc_file='MyEMFIProbe.mcc')

# Set values using meaningful units
moku.set_control(6, voltage_to_raw(2400))  # 2.4V
moku.set_control(7, time_ms_to_raw(100))   # 100ms
```

### Advanced Control Class

```python
class MyEMFIProbeController:
    def __init__(self, moku_ip):
        self.moku = CustomInstrument(moku_ip)
        self.load_config()

    def set_voltage(self, mv):
        """Set output voltage in millivolts"""
        raw = self.mv_to_raw(mv)
        cr, bits = self.mapping['output_voltage']
        self.moku.set_control(cr, raw << (31 - bits[0]))

    def arm_probe(self):
        """Arm the EMFI probe"""
        self.set_boolean('enable_output', True)
```

## Common Patterns

### Pattern 1: Simple Output Control

```yaml
datatypes:
  - name: "amplitude"
    type: "voltage_mv"
    default_value: 1000
    min_value: 0
    max_value: 5000
```

### Pattern 2: FSM Configuration

```yaml
datatypes:
  - name: "state_timeout"
    type: "time_ms"
    default_value: 1000
  - name: "trigger_level"
    type: "voltage_mv"
    default_value: 2500
  - name: "start_fsm"
    type: "boolean"
    default_value: false
```

### Pattern 3: Multi-Channel Control

```yaml
datatypes:
  - name: "ch1_voltage"
    type: "voltage_mv"
  - name: "ch2_voltage"
    type: "voltage_mv"
  - name: "ch1_enable"
    type: "boolean"
  - name: "ch2_enable"
    type: "boolean"
```

## Best Practices

1. **Use Descriptive Names:**
   - Good: `trigger_threshold_mv`
   - Bad: `trig_thr`

2. **Set Appropriate Defaults:**
   - Safe values that won't damage hardware
   - Reasonable starting points

3. **Document Units:**
   - Always specify units in descriptions
   - Use the `units` field for clarity

4. **Validate Ranges:**
   - Set min/max for safety
   - Consider hardware limits

5. **Group Related Data:**
   - Keep related signals together
   - Use prefixes for channels

## Troubleshooting

See [Troubleshooting Guide](Troubleshooting.md) for common issues.

## Examples

See the [Examples](Examples/) directory for complete applications.
```

#### 6.2 API Reference

Create `docs/BasicAppDataTypes/API_Reference.md`:

```markdown
# BasicAppDataTypes API Reference

## Python API

### Core Types

#### `BasicAppDataTypes`

```python
class BasicAppDataTypes(str, Enum):
    """Enumeration of available data types"""

    VOLTAGE_MV = "voltage_mv"      # 16-bit signed, ±10V
    TIME_NS = "time_ns"            # 32-bit unsigned, 0-4.29s
    TIME_US = "time_us"            # 24-bit unsigned, 0-16.7s
    TIME_MS = "time_ms"            # 16-bit unsigned, 0-65.5s
    BOOLEAN = "boolean"            # 1-bit
    UNSIGNED_8 = "unsigned_8"      # 8-bit unsigned
    UNSIGNED_16 = "unsigned_16"    # 16-bit unsigned
    SIGNED_16 = "signed_16"        # 16-bit signed
```

#### `TypeConverter`

```python
class TypeConverter:
    """Bidirectional type conversion utilities"""

    @staticmethod
    def voltage_mv_to_raw(mv: int) -> int:
        """
        Convert millivolts to 16-bit signed raw value.

        Args:
            mv: Voltage in millivolts (-10000 to 10000)

        Returns:
            16-bit signed raw value (-32768 to 32767)

        Example:
            >>> TypeConverter.voltage_mv_to_raw(2400)
            7864
        """

    @staticmethod
    def raw_to_voltage_mv(raw: int) -> int:
        """Convert 16-bit signed raw to millivolts"""

    @staticmethod
    def time_ms_to_clk_cycles(ms: int, clk_freq_hz: int) -> int:
        """Convert milliseconds to clock cycles"""
```

### Package Management

#### `BasicAppsRegPackage`

```python
@dataclass
class BasicAppsRegPackage:
    """Container for application register configuration"""

    package_version: str
    app_name: str
    description: str
    datatypes: List[DataTypeSpec]
    mapping_strategy: str = "auto"

    def validate(self) -> List[str]:
        """Validate package consistency"""

    def generate_mapping(self, mapper: RegisterMapper) -> None:
        """Generate register mapping"""

    def to_yaml(self) -> str:
        """Serialize to YAML"""

    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'BasicAppsRegPackage':
        """Load from YAML"""
```

#### `DataTypeSpec`

```python
@dataclass
class DataTypeSpec:
    """Specification for a single data element"""

    name: str                    # Identifier
    type: BasicAppDataTypes      # Data type
    description: str             # Documentation
    default_value: Optional[Union[int, float, bool]]
    min_value: Optional[Union[int, float]]
    max_value: Optional[Union[int, float]]
    units: Optional[str]         # Display units

    def validate_value(self, value) -> bool:
        """Check if value is valid"""

    def to_vhdl_default(self) -> str:
        """Generate VHDL initialization"""
```

### Register Mapping

#### `RegisterMapper`

```python
class RegisterMapper:
    """Maps datatypes to control registers"""

    MAX_APP_REGISTERS = 12  # CR6-CR17
    BITS_PER_REGISTER = 32

    def map_registers(self,
                     datatypes: List[Tuple[str, BasicAppDataTypes]],
                     strategy: str = "first_fit") -> List[MappedRegister]:
        """
        Map datatypes to registers.

        Args:
            datatypes: List of (name, type) tuples
            strategy: "first_fit", "best_fit", or "single"

        Returns:
            List of register mappings

        Raises:
            RegisterOverflowError: If data doesn't fit
        """
```

#### `MappedRegister`

```python
@dataclass
class MappedRegister:
    """Result of mapping a datatype to registers"""

    name: str
    type: BasicAppDataTypes
    cr_number: int              # 6-17
    bit_slice: Tuple[int, int]  # (msb, lsb)

    def to_vhdl_extraction(self) -> str:
        """Generate VHDL bit extraction"""
```

### Code Generation

#### `CustomInstGenerator`

```python
class CustomInstGenerator:
    """Generate VHDL from BasicAppsRegPackage"""

    def generate(self, yaml_path: Path, output_dir: Path) -> None:
        """
        Generate complete VHDL from YAML.

        Args:
            yaml_path: Input YAML configuration
            output_dir: Output directory for VHDL

        Generates:
            - {app}_custom_inst_shim.vhd
            - {app}_custom_inst_main.vhd
            - {app}_mapping.md
            - basic_app_types_pkg.vhd (if needed)
        """
```

## VHDL API

### Generated Shim Interface

```vhdl
entity {app_name}_custom_inst_shim is
    Port (
        -- System
        Clk : in std_logic;
        Reset : in std_logic;

        -- Raw registers (from loader)
        app_reg_6 through app_reg_17 : in std_logic_vector(31 downto 0);

        -- Typed signals (to main)
        {datatype_name} : out {vhdl_type};

        -- Handshaking
        ready_for_updates : in std_logic
    );
end entity;
```

### Type Utilities Package

```vhdl
package basic_app_types_pkg is
    -- Type definitions
    subtype voltage_type is signed(15 downto 0);
    subtype time_ms_type is unsigned(15 downto 0);

    -- Conversion functions
    function mv_to_raw(mv: integer) return voltage_type;
    function raw_to_mv(raw: voltage_type) return integer;
    function ms_to_cycles(ms: time_ms_type; clk_freq_hz: integer) return unsigned;

    -- Constants
    constant VOLTAGE_MV_PER_BIT : real := 305.0e-3;
end package;
```

## CLI Tools

### generate_custom_inst.py

```bash
# Generate VHDL from YAML
python tools/generate_custom_inst.py app.yaml

# Options:
--output-dir DIR     # Output directory (default: VHDL/apps)
--validate-only      # Only validate, don't generate
--show-mapping       # Display register mapping
```

### migrate_to_bad.py

```bash
# Convert v1.0 YAML to v2.0
python tools/migrate_to_bad.py old_app.yaml -o new_app.yaml

# Options:
--interactive        # Ask about type inference
--preserve-manual    # Keep manual CR assignments
```

## Error Codes

| Code | Error | Solution |
|------|-------|----------|
| E001 | Register overflow | Reduce datatypes or use smaller types |
| E002 | Invalid type | Check type name spelling |
| E003 | Value out of range | Check min/max constraints |
| E004 | Duplicate names | Use unique datatype names |
| E005 | Invalid identifier | Use lowercase with underscores |
```

#### 6.3 Migration Guide

Create `docs/BasicAppDataTypes/Migration_Guide.md`:

```markdown
# Migration Guide: Legacy to BasicAppDataTypes

## Overview

This guide helps you migrate existing custom instruments from the legacy register system to BasicAppDataTypes.

## Before You Start

1. **Backup your existing files**
2. **Understand the benefits:**
   - 50-75% reduction in register usage
   - Type-safe conversions
   - Automatic documentation
   - Cleaner VHDL code

## Step-by-Step Migration

### Step 1: Analyze Current Register Usage

```bash
# List current registers
grep -E "cr_number|reg_type" YourApp_app.yaml

# Count registers used
grep "cr_number" YourApp_app.yaml | wc -l
```

### Step 2: Create v2.0 YAML

#### Manual Migration

1. Start with template:
```yaml
package_version: "2.0"
app_name: "YourApp"
description: "Migrated from v1.0"
mapping:
  strategy: "auto"
datatypes:
  # Add datatypes here
```

2. Convert each register:

| Old (v1.0) | New (v2.0) |
|------------|------------|
| `reg_type: counter_16bit` + voltage comment | `type: voltage_mv` |
| `reg_type: counter_16bit` + time comment | `type: time_ms` |
| `reg_type: button` | `type: boolean` |
| `reg_type: counter_8bit` | `type: unsigned_8` |
| `reg_type: percent` | `type: unsigned_8` with max_value: 100 |

#### Automated Migration

```bash
python tools/migrate_to_bad.py YourApp_app.yaml -o YourApp_app_v2.yaml
```

### Step 3: Review and Enhance

Add metadata to improve the configuration:

```yaml
datatypes:
  - name: "intensity"
    type: "voltage_mv"
    description: "Output intensity"
    default_value: 2400  # Add meaningful default
    min_value: 0         # Add safety limits
    max_value: 5000
    units: "mV"          # Add units for clarity
```

### Step 4: Generate New VHDL

```bash
# Generate with mapping report
python tools/generate_custom_inst.py YourApp_app_v2.yaml --show-mapping

# Output:
# CR6[31:16] ← intensity (voltage_mv)
# CR6[15:0]  ← threshold (voltage_mv)
# CR7[31]    ← enable (boolean)
# Efficiency: 33/384 bits (8.6%)
```

### Step 5: Update Main Application

#### Before (v1.0):
```vhdl
-- In shim:
intensity <= app_reg_14(31 downto 16);

-- In main:
intensity : in std_logic_vector(15 downto 0);
-- Manual conversion needed
intensity_signed <= signed(intensity);
```

#### After (v2.0):
```vhdl
-- In shim (auto-generated):
intensity <= raw_to_voltage_signed(app_reg_6(31 downto 16));

-- In main:
intensity : in signed(15 downto 0);  -- Already correct type!
-- Direct use, no conversion
```

### Step 6: Update Python Control

#### Before:
```python
# Manual bit manipulation
intensity_raw = int((2.4 / 5.0) * 32767)
cr14_value = intensity_raw << 16
moku.set_control(14, cr14_value)
```

#### After:
```python
# Type-aware API
controller = YourAppController(moku)
controller.set_intensity(2400)  # millivolts
```

### Step 7: Test the Migration

```bash
# Run unit tests
pytest tests/test_YourApp_migration.py

# Run CocotB tests
make -C tests MODULE=test_YourApp_vhdl

# Deploy and test on hardware
python scripts/deploy_and_test.py YourApp_v2
```

## Real Example: DS1140_PD Migration

### Original (9 registers):
```yaml
registers:
  - name: "Arm Probe"
    reg_type: button
    cr_number: 6
  - name: "Force Fire"
    reg_type: button
    cr_number: 7
  - name: "Reset FSM"
    reg_type: button
    cr_number: 8
  # ... 6 more registers
```

### Migrated (3 registers):
```yaml
datatypes:
  - name: "arm_probe"
    type: "boolean"
  - name: "force_fire"
    type: "boolean"
  - name: "reset_fsm"
    type: "boolean"
  # ... all packed efficiently
```

**Result:** 67% reduction in register usage!

## Common Migration Issues

### Issue 1: Type Inference

**Problem:** Not sure which BasicAppDataType to use
**Solution:** Check comments and usage in VHDL:
- Contains "volt", "mV", "amplitude" → `voltage_mv`
- Contains "time", "delay", "duration" → `time_ms`
- Single bit usage → `boolean`

### Issue 2: Manual CR Dependencies

**Problem:** Code depends on specific CR numbers
**Solution:** Use mapping report to update:
```python
# Old: Hardcoded CR14
moku.set_control(14, value)

# New: Read from mapping
cr_map = load_mapping("YourApp_mapping.md")
moku.set_control(cr_map['intensity'], value)
```

### Issue 3: Bit Manipulation

**Problem:** Complex bit manipulation in Python
**Solution:** Use TypeConverter utilities:
```python
# Old: Manual scaling
raw = int((volts / 10.0) * 65535) & 0xFFFF

# New: Type-aware
raw = TypeConverter.voltage_mv_to_raw(volts * 1000)
```

## Validation Checklist

- [ ] All registers converted to datatypes
- [ ] YAML validates without errors
- [ ] Generated VHDL compiles
- [ ] Mapping uses fewer registers
- [ ] Python control updated
- [ ] Unit tests pass
- [ ] CocotB tests pass
- [ ] Hardware test successful

## Rollback Plan

If issues arise:
1. Keep original files as `.backup`
2. Run parallel testing before switching
3. Use feature flags in Python:
```python
if USE_BAD_TYPES:
    controller = NewController()
else:
    controller = LegacyController()
```
```

#### 6.4 Troubleshooting Guide

Create `docs/BasicAppDataTypes/Troubleshooting.md`:

```markdown
# BasicAppDataTypes Troubleshooting Guide

## Common Issues and Solutions

### YAML Validation Errors

#### Error: "Total bits (400) exceeds limit (384)"

**Cause:** Too many datatypes for available registers
**Solutions:**
1. Reduce number of datatypes
2. Use smaller types where possible
3. Remove unused datatypes

#### Error: "Duplicate datatype names found"

**Cause:** Multiple datatypes with same name
**Solution:** Ensure all names are unique

```yaml
# Bad:
datatypes:
  - name: "voltage"
  - name: "voltage"  # Duplicate!

# Good:
datatypes:
  - name: "voltage_in"
  - name: "voltage_out"
```

### Code Generation Issues

#### Error: "Template not found"

**Cause:** Missing template files
**Solution:** Ensure templates directory exists:
```bash
ls shared/custom_inst/templates/
```

#### Warning: "No type utilities needed"

**Cause:** App doesn't use voltage/time types
**Solution:** This is normal - package not generated

### VHDL Compilation Errors

#### Error: "signed type not found"

**Cause:** Missing IEEE.NUMERIC_STD library
**Solution:** Add to VHDL file:
```vhdl
use IEEE.NUMERIC_STD.ALL;
```

#### Error: "Signal width mismatch"

**Cause:** Type mismatch between shim and main
**Solution:** Regenerate both files together

### Python Control Issues

#### Error: "Register out of range"

**Cause:** Using CR numbers outside 6-17
**Solution:** Check mapping report for actual assignments

#### Error: "Value exceeds type range"

**Cause:** Trying to set value beyond type limits
**Solution:** Check min/max constraints:
```python
# Voltage limited to ±10V
TypeConverter.voltage_mv_to_raw(15000)  # Error!
TypeConverter.voltage_mv_to_raw(10000)  # OK
```

### Hardware Testing Issues

#### Symptom: Values don't update

**Possible Causes:**
1. `ready_for_updates` stuck at 0
2. FSM blocking updates
3. Reset held high

**Debug Steps:**
```python
# Check register values
for i in range(6, 18):
    print(f"CR{i}: {moku.get_control(i):08x}")

# Force update
moku.set_control(0, 0x80000000)  # Set VOLO_READY
```

#### Symptom: Wrong values

**Possible Causes:**
1. Incorrect type conversion
2. Wrong bit extraction
3. Endianness issue

**Debug:**
```python
# Verify conversion
mv = 2400
raw = TypeConverter.voltage_mv_to_raw(mv)
print(f"{mv}mV → 0x{raw:04x}")
```

## Debug Techniques

### 1. Verbose Generation

```bash
# Enable debug output
PYTHONPATH=. python tools/generate_custom_inst.py \
    --verbose \
    --show-mapping \
    app.yaml
```

### 2. Mapping Visualization

```python
# Visualize register packing
from models.custom_inst.register_mapper import RegisterMapper

mapper = RegisterMapper()
result = mapper.map_registers(datatypes)
mapper.visualize(result)
```

### 3. Test Individual Components

```python
# Test type conversion
from models.custom_inst.basic_app_datatypes import TypeConverter

# Test voltage
assert TypeConverter.voltage_mv_to_raw(2400) == 7864

# Test time
assert TypeConverter.time_ms_to_clk_cycles(1, 125_000_000) == 125_000
```

### 4. CocotB Interactive Debug

```python
# In test file
import ipdb

@cocotb.test()
async def debug_test(dut):
    ipdb.set_trace()  # Breakpoint
    # Inspect signals interactively
```

## Performance Issues

### Slow Mapping Generation

**Cause:** Large number of datatypes
**Solution:** Use simpler packing strategy:
```yaml
mapping:
  strategy: "first_fit"  # Faster than "best_fit"
```

### High Register Usage

**Cause:** Inefficient packing
**Solution:** Review datatypes:
- Combine related booleans
- Use smaller types where possible
- Remove unused fields

## Getting Help

### Resources

1. **Documentation:**
   - [User Guide](User_Guide.md)
   - [API Reference](API_Reference.md)
   - [Examples](Examples/)

2. **Source Code:**
   - Type definitions: `models/custom_inst/basic_app_datatypes.py`
   - Mapper: `models/custom_inst/register_mapper.py`
   - Generator: `tools/generate_custom_inst.py`

3. **Tests:**
   - Run tests for examples: `pytest tests/`
   - Check test patterns: `tests/test_*.py`

### Support Channels

- GitHub Issues: Report bugs
- Discord: Real-time help
- Email: support@example.com

## FAQ

**Q: Can I mix v1.0 and v2.0 formats?**
A: No, use one format per application

**Q: What's the maximum number of datatypes?**
A: Depends on types - typically 30-50

**Q: Can I extend with custom types?**
A: Yes, add to BasicAppDataTypes enum

**Q: How do I handle arrays?**
A: Not directly supported - use multiple named elements
```

#### 6.5 Update Project Documentation

Update `CLAUDE.md`:

```markdown
# CLAUDE.md Updates

## BasicAppDataTypes (Added)

**New in 2025:** BasicAppDataTypes provides type-safe register communication between Python and VHDL.

### Quick Reference

- **Types:** voltage_mv, time_ms/us/ns, boolean, unsigned_8/16, signed_16
- **Auto-packing:** Efficient register usage (typically 50-75% reduction)
- **Type safety:** Automatic conversions, range validation
- **Documentation:** Auto-generated mapping reports

### Commands

```bash
# Generate from v2.0 YAML
python tools/generate_custom_inst.py app_v2.yaml

# Migrate v1.0 to v2.0
python tools/migrate_to_bad.py old.yaml -o new.yaml

# Run BAD tests
pytest tests/test_basic_app_datatypes.py
```

### File Locations

- Types: `models/custom_inst/basic_app_datatypes.py`
- Mapper: `models/custom_inst/register_mapper.py`
- Package: `models/custom_inst/reg_package.py`
- Docs: `docs/BasicAppDataTypes/`
```

Update `README.md`:

```markdown
# README.md Updates

## Features (Updated)

- ✨ **NEW: BasicAppDataTypes** - Type-safe register communication
  - Automatic register packing (50-75% space savings)
  - Built-in voltage/time conversions
  - YAML-driven configuration
  - [Documentation](docs/BasicAppDataTypes/User_Guide.md)
```

## Success Criteria

Phase 6 is complete when:

- [ ] User Guide written and reviewed
- [ ] API Reference complete
- [ ] Migration Guide with real examples
- [ ] Troubleshooting Guide comprehensive
- [ ] Example YAMLs created
- [ ] Project docs updated (README, CLAUDE.md)
- [ ] All documentation reviewed for accuracy
- [ ] Phase summary written to `BAD_Phase6_COMPLETE.md`
- [ ] Final commit with all documentation

## Output Artifacts

### Required Files
1. `docs/BasicAppDataTypes/User_Guide.md`
2. `docs/BasicAppDataTypes/API_Reference.md`
3. `docs/BasicAppDataTypes/Migration_Guide.md`
4. `docs/BasicAppDataTypes/Type_Reference.md`
5. `docs/BasicAppDataTypes/Troubleshooting.md`
6. `docs/BasicAppDataTypes/Examples/` - Example YAMLs
7. `docs/BasicAppDataTypes/BAD_Phase6_COMPLETE.md`

### Documentation Standards

- Clear, concise language
- Plenty of examples
- Visual aids where helpful
- Cross-references between docs
- Version information
- Update dates

## Final Checklist

### System Validation

- [ ] Type system complete and tested
- [ ] Register mapper optimal
- [ ] Package model robust
- [ ] Code generation reliable
- [ ] Tests comprehensive (>90% coverage)
- [ ] Documentation complete

### Deployment Readiness

- [ ] DS1140_PD successfully migrated
- [ ] Performance benchmarks acceptable
- [ ] Error handling comprehensive
- [ ] Migration path clear
- [ ] Rollback plan documented
- [ ] Support channels defined

## Project Completion

### Final Summary

Create `docs/BasicAppDataTypes/BAD_COMPLETE.md`:

```markdown
# BasicAppDataTypes Implementation Complete

## Summary

BasicAppDataTypes has been successfully implemented across 6 phases:

1. ✅ **Type System:** 8 types defined with conversions
2. ✅ **Register Mapping:** Automatic packing with 50-75% savings
3. ✅ **Package Model:** YAML v2.0 schema with validation
4. ✅ **Code Generation:** Enhanced templates and generator
5. ✅ **Testing:** 95% coverage with CocotB validation
6. ✅ **Documentation:** Complete user and developer docs

## Key Achievements

- **Register Efficiency:** DS1140_PD reduced from 9 to 3 registers (67% savings)
- **Type Safety:** Zero manual bit manipulation required
- **Developer Experience:** YAML configuration with auto-generation
- **Test Coverage:** 95% with comprehensive validation
- **Documentation:** 6 guides with examples and troubleshooting

## Next Steps

1. Deploy DS1140_PD v2 to hardware
2. Migrate remaining applications
3. Gather user feedback
4. Consider additional types (complex, arrays)
5. Optimize packing algorithm further

## Acknowledgments

This implementation represents a fundamental improvement to the EZ-EMFI custom instrument architecture, enabling safer, more efficient, and more maintainable FPGA applications.

**Implementation Period:** 2025-11-02 to [completion date]
**Total Effort:** 6 phases
**Breaking Changes:** Yes (with migration path)
**Backwards Compatibility:** Maintained via v1.0 support
```

---

**Congratulations!** BasicAppDataTypes is ready for production use!