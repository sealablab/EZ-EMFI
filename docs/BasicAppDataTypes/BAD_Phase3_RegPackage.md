# BAD Phase 3: BasicAppsRegPackage Implementation

**Phase:** 3 of 6
**Goal:** Bundle BasicAppDataTypes with mapping metadata into a cohesive package
**Prerequisites:** Phase 1-2 complete
**Phase 1 Summary:** ./BAD_Phase1_COMPLETE.md
**Phase 2 Summary:** ./BAD_Phase2_COMPLETE.md
**Output:** `models/custom_inst/reg_package.py` and YAML schema evolution

## Git Workflow

**Branch:** `feature/BAD/P3`

**Starting this phase:**
```bash
git checkout feature/BAD-main
git checkout -b feature/BAD/P3
```

**During development:**
```bash
# Commit frequently as you implement
git add <files>
git commit -m "feat(BAD/P3): <description>"
```

**Completing this phase:**
```bash
# Final commit with phase completion
git add .
git commit -m "feat(BAD/P3): Complete Phase 3 - Package model and YAML v2.0"

# Write BAD_Phase3_COMPLETE.md with summary

# Merge back to feature branch
git checkout feature/BAD-main
git merge --no-ff feature/BAD/P3 -m "Merge Phase 3: Package bundling and YAML schema"
```

**Full workflow:** See [BAD_MASTER_Orchestrator.md](./BAD_MASTER_Orchestrator.md#git-workflow)

## Context Loading

Please review these files and previous phase outputs:

```bash
# Phase 1-2 results
cat docs/BasicAppDataTypes/BAD_Phase1_COMPLETE.md
cat docs/BasicAppDataTypes/BAD_Phase2_COMPLETE.md

# Current app model structure
cat models/custom_inst/custom_inst_app.py

# Current YAML schema
cat DS1140_PD_app.yaml

# How apps are currently loaded
cat tools/generate_custom_inst.py | grep -A 20 "load_yaml"
```

## Phase 3 Objectives

### Primary Goals
1. Define `BasicAppsRegPackage` as the container for types + mapping
2. Evolve YAML schema to support new package format
3. Create serialization/deserialization for the package
4. Maintain backwards compatibility with existing apps

### Specific Deliverables

#### 3.1 Package Definition
Create `models/custom_inst/reg_package.py`:

```python
@dataclass
class BasicAppsRegPackage:
    """
    Complete package for a custom instrument's register interface
    Combines BasicAppDataTypes with their mapped register assignments
    """
    # Package metadata
    package_version: str = "2.0"  # BasicAppDataTypes version
    app_name: str
    description: str

    # Type definitions
    datatypes: List['DataTypeSpec']

    # Mapping configuration
    mapping_strategy: str = "auto"  # "auto" or "manual"
    mapping_result: Optional[List[MappedRegister]] = None

    # Constraints
    reserved_registers: List[int] = field(default_factory=lambda: [18, 19, 20, 21])
    max_app_registers: int = 12

    def validate(self) -> List[str]:
        """Validate package consistency"""
        errors = []

        # Check total bit usage
        total_bits = sum(dt.get_bit_width() for dt in self.datatypes)
        if total_bits > self.max_app_registers * 32:
            errors.append(f"Total bits ({total_bits}) exceeds limit (384)")

        # Check for duplicate names
        names = [dt.name for dt in self.datatypes]
        if len(names) != len(set(names)):
            errors.append("Duplicate datatype names found")

        return errors

    def generate_mapping(self, mapper: RegisterMapper) -> None:
        """Generate register mapping for this package"""
        type_tuples = [(dt.name, dt.type) for dt in self.datatypes]
        self.mapping_result = mapper.map_registers(type_tuples, self.mapping_strategy)

    def to_yaml(self) -> str:
        """Serialize package to YAML format"""
        # Implementation below

    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'BasicAppsRegPackage':
        """Deserialize package from YAML"""
        # Implementation below
```

#### 3.2 DataType Specification

```python
@dataclass
class DataTypeSpec:
    """Specification for a single data element in the package"""
    name: str  # Python/VHDL identifier
    type: BasicAppDataTypes
    description: str

    # Type-specific configuration
    default_value: Optional[Union[int, float, bool]] = None

    # Optional constraints
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None

    # UI hints (for TUI/GUI generation)
    display_name: Optional[str] = None
    units: Optional[str] = None  # "mV", "ms", etc.

    # Manual mapping override (if not using auto)
    manual_cr: Optional[int] = None
    manual_bits: Optional[Tuple[int, int]] = None

    def get_bit_width(self) -> int:
        """Get bit width from type registry"""
        return TYPE_REGISTRY[self.type].bit_width

    def validate_value(self, value: Union[int, float, bool]) -> bool:
        """Check if value is valid for this type"""
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True

    def to_vhdl_default(self) -> str:
        """Generate VHDL default value initialization"""
        if self.type == BasicAppDataTypes.VOLTAGE_MV:
            raw = TypeConverter.voltage_mv_to_raw(self.default_value or 0)
            return f"to_signed({raw}, 16)"
        elif self.type == BasicAppDataTypes.BOOLEAN:
            return "'1'" if self.default_value else "'0'"
        # ... other types
```

#### 3.3 YAML Schema Evolution

**New YAML Format (v2.0):**
```yaml
# DS1140_PD_app_v2.yaml
package_version: "2.0"
app_name: "DS1140_PD"
description: "DS1140 EMFI Probe Driver with BasicAppDataTypes"

# Mapping configuration
mapping:
  strategy: "auto"  # Let mapper decide optimal packing
  # strategy: "manual"  # Use manual_cr fields
  reserved: [18, 19, 20, 21]  # Reserved CRs

# Data type definitions
datatypes:
  - name: "intensity"
    type: "voltage_mv"
    description: "Output firing voltage"
    default_value: 2400  # 2.4V in millivolts
    min_value: -10000
    max_value: 10000
    display_name: "Intensity"
    units: "mV"

  - name: "trigger_threshold"
    type: "voltage_mv"
    description: "Trigger detection threshold"
    default_value: 2000
    display_name: "Trigger Threshold"
    units: "mV"

  - name: "arm_timeout"
    type: "time_ms"
    description: "Maximum time in armed state"
    default_value: 1000  # 1 second
    max_value: 5000
    display_name: "Arm Timeout"
    units: "ms"

  - name: "arm_probe"
    type: "boolean"
    description: "Arm the EMFI probe"
    default_value: false
    display_name: "Arm Probe"

  - name: "clock_divider"
    type: "unsigned_8"
    description: "FSM clock divider"
    default_value: 10
    min_value: 1
    max_value: 255
```

**Backwards Compatible Format (v1.0):**
```yaml
# Support old format for gradual migration
app_name: "DS1120_PD"
registers:  # Old key name
  - name: "Intensity"
    reg_type: counter_16bit  # Old type system
    cr_number: 20  # Manual assignment
    default_value: 0x1EB8
```

#### 3.4 Package Factory

```python
class RegPackageFactory:
    """Factory for creating packages from various sources"""

    @staticmethod
    def from_yaml_file(filepath: Path) -> BasicAppsRegPackage:
        """Load package from YAML file with version detection"""
        with open(filepath) as f:
            data = yaml.safe_load(f)

        # Detect version
        if 'package_version' in data and data['package_version'] == "2.0":
            return RegPackageFactory._from_v2_yaml(data)
        elif 'registers' in data:
            return RegPackageFactory._from_v1_yaml(data)
        else:
            raise ValueError("Unknown YAML format")

    @staticmethod
    def _from_v2_yaml(data: dict) -> BasicAppsRegPackage:
        """Parse v2.0 YAML format"""
        datatypes = []
        for dt_dict in data['datatypes']:
            datatypes.append(DataTypeSpec(
                name=dt_dict['name'],
                type=BasicAppDataTypes(dt_dict['type']),
                description=dt_dict['description'],
                default_value=dt_dict.get('default_value'),
                min_value=dt_dict.get('min_value'),
                max_value=dt_dict.get('max_value'),
                display_name=dt_dict.get('display_name'),
                units=dt_dict.get('units'),
                manual_cr=dt_dict.get('manual_cr'),
                manual_bits=dt_dict.get('manual_bits'),
            ))

        return BasicAppsRegPackage(
            package_version=data['package_version'],
            app_name=data['app_name'],
            description=data.get('description', ''),
            datatypes=datatypes,
            mapping_strategy=data.get('mapping', {}).get('strategy', 'auto'),
            reserved_registers=data.get('mapping', {}).get('reserved', [18, 19, 20, 21]),
        )

    @staticmethod
    def _from_v1_yaml(data: dict) -> BasicAppsRegPackage:
        """Convert v1.0 format to package (backwards compatibility)"""
        # Map old RegisterType to BasicAppDataTypes
        type_mapping = {
            'counter_8bit': BasicAppDataTypes.UNSIGNED_8,
            'counter_16bit': BasicAppDataTypes.UNSIGNED_16,
            'button': BasicAppDataTypes.BOOLEAN,
            # Add more mappings as needed
        }

        datatypes = []
        for reg in data['registers']:
            datatypes.append(DataTypeSpec(
                name=reg['name'].lower().replace(' ', '_'),
                type=type_mapping[reg['reg_type']],
                description=reg.get('description', ''),
                default_value=reg.get('default_value'),
                manual_cr=reg['cr_number'],  # Preserve manual assignment
            ))

        return BasicAppsRegPackage(
            package_version="1.0-compat",
            app_name=data['app_name'],
            datatypes=datatypes,
            mapping_strategy="manual",  # Old format uses manual mapping
        )
```

#### 3.5 Package Validation and Reporting

```python
class PackageValidator:
    """Comprehensive validation for reg packages"""

    def validate_complete(self, package: BasicAppsRegPackage) -> ValidationReport:
        """Full validation with detailed report"""
        report = ValidationReport()

        # Structure validation
        report.add_check("Package structure", package.validate())

        # Type validation
        for dt in package.datatypes:
            if dt.type not in TYPE_REGISTRY:
                report.add_error(f"{dt.name}: Unknown type {dt.type}")

            # Value range validation
            if dt.default_value is not None:
                if not dt.validate_value(dt.default_value):
                    report.add_error(f"{dt.name}: Default value out of range")

        # Mapping validation
        if package.mapping_result:
            mapper = RegisterMapper()
            constraints = MappingConstraints()
            violations = constraints.validate(package.mapping_result)
            report.add_check("Mapping constraints", violations)

        # Naming validation
        for dt in package.datatypes:
            if not self._is_valid_identifier(dt.name):
                report.add_error(f"{dt.name}: Invalid identifier for Python/VHDL")

        return report

    @staticmethod
    def _is_valid_identifier(name: str) -> bool:
        """Check if name is valid Python and VHDL identifier"""
        import re
        return bool(re.match(r'^[a-z][a-z0-9_]*$', name))
```

## Design Decisions Needed

### 3.1 Version Migration Strategy

**Option A: Clean Break**
- Only support v2.0 format
- Provide migration tool for old YAMLs
- Simpler implementation

**Option B: Dual Support (Recommended)**
- Support both v1.0 and v2.0
- Auto-detect version
- Gradual migration path

**Option C: In-Place Evolution**
- Extend existing format with new fields
- More complex parsing
- Risk of confusion

### 3.2 Default Value Handling

```python
# Where should defaults live?

# Option 1: In YAML only
default_value: 2400  # mV

# Option 2: Type-based defaults if not specified
if dt.default_value is None:
    dt.default_value = TYPE_REGISTRY[dt.type].default_value

# Option 3: Cascading defaults
# YAML > Type default > Zero
```

### 3.3 Package Immutability

```python
# Should packages be immutable after creation?

# Option 1: Immutable (frozen dataclass)
@dataclass(frozen=True)
class BasicAppsRegPackage:
    # Cannot modify after creation
    pass

# Option 2: Mutable with validation
@dataclass
class BasicAppsRegPackage:
    def add_datatype(self, dt: DataTypeSpec):
        self.datatypes.append(dt)
        self.validate()  # Re-validate
```

### 3.4 UI Metadata

Should we include UI generation hints in the package?

```yaml
datatypes:
  - name: "intensity"
    type: "voltage_mv"
    # UI metadata
    ui:
      control: "slider"
      min: -5000
      max: 5000
      step: 100
      group: "Output Settings"
```

## Test Cases

Create `tests/test_reg_package.py`:

```python
def test_package_creation():
    """Test creating a package programmatically"""
    package = BasicAppsRegPackage(
        app_name="TestApp",
        description="Test application",
        datatypes=[
            DataTypeSpec(
                name="voltage_out",
                type=BasicAppDataTypes.VOLTAGE_MV,
                description="Output voltage",
                default_value=1000,
            ),
            DataTypeSpec(
                name="enable",
                type=BasicAppDataTypes.BOOLEAN,
                description="Enable output",
                default_value=False,
            ),
        ],
    )

    # Validate
    errors = package.validate()
    assert len(errors) == 0

    # Generate mapping
    mapper = RegisterMapper()
    package.generate_mapping(mapper)
    assert package.mapping_result is not None
    assert len(package.mapping_result) == 2

def test_yaml_roundtrip():
    """Test YAML serialization/deserialization"""
    yaml_content = """
    package_version: "2.0"
    app_name: "TestApp"
    datatypes:
      - name: "test_voltage"
        type: "voltage_mv"
        description: "Test voltage"
        default_value: 2400
    """

    package = BasicAppsRegPackage.from_yaml(yaml_content)
    assert package.app_name == "TestApp"
    assert len(package.datatypes) == 1
    assert package.datatypes[0].default_value == 2400

    # Round trip
    yaml_out = package.to_yaml()
    package2 = BasicAppsRegPackage.from_yaml(yaml_out)
    assert package == package2

def test_backwards_compatibility():
    """Test loading v1.0 format YAML"""
    old_yaml = """
    app_name: "LegacyApp"
    registers:
      - name: "Counter Value"
        reg_type: counter_16bit
        cr_number: 6
        default_value: 100
    """

    package = RegPackageFactory.from_yaml(old_yaml)
    assert package.package_version == "1.0-compat"
    assert package.mapping_strategy == "manual"
    assert package.datatypes[0].manual_cr == 6

def test_validation():
    """Test package validation"""
    package = BasicAppsRegPackage(
        app_name="TestApp",
        datatypes=[
            DataTypeSpec(
                name="invalid-name",  # Invalid identifier
                type=BasicAppDataTypes.VOLTAGE_MV,
                description="Test",
            ),
            DataTypeSpec(
                name="valid_name",
                type=BasicAppDataTypes.VOLTAGE_MV,
                default_value=20000,  # Out of range
                max_value=10000,
            ),
        ],
    )

    validator = PackageValidator()
    report = validator.validate_complete(package)
    assert not report.is_valid()
    assert "invalid-name" in report.errors[0]
    assert "out of range" in report.errors[1]

def test_ds1140_migration():
    """Test migrating DS1140_PD to v2.0 format"""
    # Load existing DS1140_PD
    old_package = RegPackageFactory.from_yaml_file("DS1140_PD_app.yaml")

    # Convert to v2.0
    new_datatypes = []
    for dt in old_package.datatypes:
        # Enhance with new type system
        if "intensity" in dt.name.lower():
            dt.type = BasicAppDataTypes.VOLTAGE_MV
            dt.units = "mV"
            dt.default_value = 2400
        elif "timeout" in dt.name.lower():
            dt.type = BasicAppDataTypes.TIME_MS
            dt.units = "ms"
        new_datatypes.append(dt)

    new_package = BasicAppsRegPackage(
        package_version="2.0",
        app_name=old_package.app_name,
        datatypes=new_datatypes,
        mapping_strategy="auto",  # Switch to auto-mapping
    )

    # Generate new mapping
    mapper = RegisterMapper()
    new_package.generate_mapping(mapper)

    # Verify improvement
    old_registers_used = 9  # Current DS1140_PD
    new_registers_used = len(set(m.cr_number for m in new_package.mapping_result))
    assert new_registers_used <= old_registers_used // 2  # 50% reduction
```

## Migration Guide

### Converting Existing Apps

1. **Analyze current register usage:**
```bash
grep -E "reg_type|cr_number" DS1140_PD_app.yaml
```

2. **Identify type upgrades:**
   - `counter_16bit` + voltage comment → `voltage_mv`
   - `counter_16bit` + time comment → `time_ms`
   - `button` → `boolean`

3. **Create v2.0 YAML:**
```python
# Migration script
def migrate_to_v2(old_yaml_path):
    old_pkg = RegPackageFactory.from_yaml_file(old_yaml_path)

    # Enhance types based on context
    for dt in old_pkg.datatypes:
        dt = enhance_type(dt)

    # Switch to auto-mapping
    old_pkg.mapping_strategy = "auto"
    old_pkg.package_version = "2.0"

    # Save new version
    new_path = old_yaml_path.replace('.yaml', '_v2.yaml')
    with open(new_path, 'w') as f:
        f.write(old_pkg.to_yaml())
```

## Success Criteria

Phase 3 is complete when:

- [ ] `reg_package.py` implemented with full package model
- [ ] YAML schema v2.0 defined and documented
- [ ] Backwards compatibility with v1.0 maintained
- [ ] Package validation comprehensive
- [ ] Factory pattern for flexible loading
- [ ] DS1140_PD successfully migrated to v2.0
- [ ] Unit tests passing for all scenarios
- [ ] Phase summary written to `BAD_Phase3_COMPLETE.md`

## Output Artifacts

### Required Files
1. `models/custom_inst/reg_package.py` - Package implementation
2. `DS1140_PD_app_v2.yaml` - Example migration
3. `tests/test_reg_package.py` - Test suite
4. `docs/BasicAppDataTypes/BAD_Phase3_COMPLETE.md` - Summary

### Summary Format
The completion summary should include:
- Final package structure design
- YAML schema v2.0 specification
- Migration guide key points
- Validation rules implemented
- Integration notes for Phase 4

## Handoff to Phase 4

Phase 4 will need:
- Complete package model API
- YAML loading/saving utilities
- Validation framework
- Example migrated packages

Update `BAD_Phase4_CodeGeneration.md` header with:
```markdown
**Prerequisites:** Phase 1-3 complete
**Phase 3 Summary:** ./BAD_Phase3_COMPLETE.md
**Phase 3 Commit:** {git_hash}
```

## Interactive Decisions

As you implement, we'll decide:

1. **Metadata scope**: How much UI/display metadata to include?
2. **Validation strictness**: Warnings vs errors for edge cases?
3. **Migration automation**: How much can be automated vs manual?
4. **Package versioning**: How to handle future schema changes?
5. **Type inference**: Should we infer types from names/descriptions?

## Getting Started

1. Create the package model with core fields
2. Implement YAML serialization/deserialization
3. Add factory for version detection
4. Test with DS1140_PD migration
5. Add comprehensive validation
6. Document schema changes

Remember: The package is the **unified interface** between Python configuration and VHDL implementation. Make it expressive yet strict!

---

**Questions?** The package ties everything together - it's where types meet mapping meet configuration. Let's make it elegant!