# BAD Phase 4: Code Generation Updates

**Phase:** 4 of 6
**Goal:** Update Jinja2 templates and code generator for BasicAppDataTypes
**Prerequisites:** Phase 1-3 complete
**Phase 1 Summary:** ./BAD_Phase1_COMPLETE.md
**Phase 2 Summary:** ./BAD_Phase2_COMPLETE.md
**Phase 3 Summary:** ./BAD_Phase3_COMPLETE.md
**Output:** Updated templates and enhanced `generate_custom_inst.py`

## Git Workflow

**Branch:** `feature/BAD/P4`

**Starting this phase:**
```bash
git checkout feature/BAD
git checkout -b feature/BAD/P4
```

**During development:**
```bash
# Commit frequently as you implement
git add <files>
git commit -m "feat(BAD/P4): <description>"
```

**Completing this phase:**
```bash
# Final commit with phase completion
git add .
git commit -m "feat(BAD/P4): Complete Phase 4 - Code generation system"

# Write BAD_Phase4_COMPLETE.md with summary

# Merge back to feature branch
git checkout feature/BAD
git merge --no-ff feature/BAD/P4 -m "Merge Phase 4: Template and code generator updates"
```

**Full workflow:** See [BAD_MASTER_Orchestrator.md](./BAD_MASTER_Orchestrator.md#git-workflow)

## Context Loading

Please review these files and previous phase outputs:

```bash
# Previous phase results
cat docs/BasicAppDataTypes/BAD_Phase3_COMPLETE.md

# Current templates
cat shared/custom_inst/templates/custom_inst_shim_template.vhd
cat shared/custom_inst/templates/custom_inst_main_template.vhd

# Current generator
cat tools/generate_custom_inst.py

# Example of current generated code
cat VHDL/apps/DS1140_PD/DS1140_PD_custom_inst_shim.vhd | head -100
```

## Phase 4 Objectives

### Primary Goals
1. Update shim template for type-aware signal generation
2. Enhance main template with type utilities
3. Modify code generator to use BasicAppsRegPackage
4. Generate comprehensive mapping documentation

### Specific Deliverables

#### 4.1 Enhanced Shim Template

Update `shared/custom_inst/templates/custom_inst_shim_template_v2.vhd`:

```vhdl
-- ================================================================================
-- {{ app.app_name }}_custom_inst_shim.vhd
-- Generated: {{ timestamp }}
-- Package Version: {{ app.package_version }}
-- Mapping Strategy: {{ app.mapping_strategy }}
-- ================================================================================
-- Register Mapping Report:
{% for cr_num, mappings in app.get_register_map().items() %}
-- CR{{ cr_num }}: {% for m in mappings %}{{ m.name }}[{{ m.bit_slice[0] }}:{{ m.bit_slice[1] }}] {% endfor %}
{% endfor %}
-- Total Efficiency: {{ app.get_efficiency() }}% ({{ app.get_bits_used() }}/384 bits)
-- ================================================================================

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity {{ app.app_name }}_custom_inst_shim is
    Port (
        -- System signals
        Clk            : in  std_logic;
        Reset          : in  std_logic;

        -- Raw register interface (from loader)
        {% for i in range(6, 18) %}
        app_reg_{{ i }} : in  std_logic_vector(31 downto 0);
        {% endfor %}

        -- Typed signals to main app
        {% for dt in app.datatypes %}
        {{ dt.name }} : out {{ dt.get_vhdl_type() }};
        {% endfor %}

        -- Handshaking
        ready_for_updates : in  std_logic
    );
end {{ app.app_name }}_custom_inst_shim;

architecture Behavioral of {{ app.app_name }}_custom_inst_shim is
    -- Type conversion functions (generated)
    {% if app.has_voltage_types() %}
    function raw_to_voltage_signed(raw: std_logic_vector(15 downto 0)) return signed is
    begin
        return signed(raw);
    end function;
    {% endif %}

    {% if app.has_time_types() %}
    constant CLK_FREQ_HZ : integer := {{ app.clock_freq_hz | default(125000000) }};

    function time_ms_to_cycles(ms_value: unsigned(15 downto 0)) return unsigned is
    begin
        return resize(ms_value * (CLK_FREQ_HZ/1000), 32);
    end function;
    {% endif %}

begin
    -- ============================================================
    -- Register Update Process (Atomic with Handshaking)
    -- ============================================================
    REGISTER_UPDATE_PROC: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                -- Type-aware default initialization
                {% for dt in app.datatypes %}
                {{ dt.name }} <= {{ dt.to_vhdl_default() }};
                {% endfor %}

            elsif ready_for_updates = '1' then
                -- Atomic update: Extract from mapped registers
                {% for mapping in app.mapping_result %}
                {% if mapping.type == 'voltage_mv' %}
                {{ mapping.name }} <= raw_to_voltage_signed(
                    app_reg_{{ mapping.cr_number }}{{ mapping.get_bit_slice_vhdl() }}
                );
                {% elif mapping.type == 'boolean' %}
                {{ mapping.name }} <= app_reg_{{ mapping.cr_number }}({{ mapping.bit_slice[0] }});
                {% elif mapping.type == 'time_ms' %}
                {{ mapping.name }} <= unsigned(
                    app_reg_{{ mapping.cr_number }}{{ mapping.get_bit_slice_vhdl() }}
                );
                {% else %}
                {{ mapping.name }} <= app_reg_{{ mapping.cr_number }}{{ mapping.get_bit_slice_vhdl() }};
                {% endif %}
                {% endfor %}
            end if;
            -- else: Hold previous values (configuration locked)
        end if;
    end process REGISTER_UPDATE_PROC;

end Behavioral;
```

#### 4.2 Enhanced Main Template

Update `shared/custom_inst/templates/custom_inst_main_template_v2.vhd`:

```vhdl
-- ================================================================================
-- {{ app.app_name }}_custom_inst_main.vhd
-- Application logic for {{ app.description }}
-- ================================================================================

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

-- Import type utilities if needed
{% if app.needs_type_utilities() %}
use work.basic_app_types_pkg.all;  -- Generated type utilities
{% endif %}

entity {{ app.app_name }}_custom_inst_main is
    Port (
        -- System signals
        Clk               : in  std_logic;
        Reset             : in  std_logic;

        -- Typed configuration inputs (from shim)
        {% for dt in app.datatypes %}
        {% if dt.is_input() %}
        {{ dt.name }} : in {{ dt.get_vhdl_type() }};
        {% endif %}
        {% endfor %}

        -- Application outputs
        {% for dt in app.datatypes %}
        {% if dt.is_output() %}
        {{ dt.name }} : out {{ dt.get_vhdl_type() }};
        {% endif %}
        {% endfor %}

        -- Hardware I/O
        Output            : out signed(15 downto 0);
        Input             : in  signed(15 downto 0);

        -- Handshaking
        ready_for_updates : out std_logic
    );
end {{ app.app_name }}_custom_inst_main;

architecture Behavioral of {{ app.app_name }}_custom_inst_main is
    -- FSM states (if applicable)
    {% if app.has_fsm %}
    type state_type is ({{ app.get_fsm_states()|join(', ') }});
    signal current_state : state_type := {{ app.initial_state }};
    {% endif %}

    -- Internal signals
    {% for sig in app.internal_signals %}
    signal {{ sig.name }} : {{ sig.type }};
    {% endfor %}

begin
    -- ============================================================
    -- Main Application Logic
    -- ============================================================
    {% if app.has_fsm %}
    FSM_PROC: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                current_state <= {{ app.initial_state }};
                ready_for_updates <= '1';
            else
                case current_state is
                    {% for state in app.fsm_states %}
                    when {{ state.name }} =>
                        {{ state.get_vhdl_logic() | indent(24) }}
                    {% endfor %}
                end case;
            end if;
        end if;
    end process FSM_PROC;
    {% else %}
    -- Simple combinational logic
    ready_for_updates <= '1';  -- Always ready for updates
    {% endif %}

    -- Output assignments
    {% for output in app.output_assignments %}
    {{ output }};
    {% endfor %}

end Behavioral;
```

#### 4.3 Updated Code Generator

Enhance `tools/generate_custom_inst.py`:

```python
#!/usr/bin/env python3
"""
Generate CustomInstrument VHDL from BasicAppsRegPackage YAML
Supports both v1.0 (legacy) and v2.0 (BasicAppDataTypes) formats
"""

from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import click
import yaml

from models.custom_inst.reg_package import (
    BasicAppsRegPackage,
    RegPackageFactory,
)
from models.custom_inst.register_mapper import RegisterMapper
from models.custom_inst.basic_app_datatypes import BasicAppDataTypes


class CustomInstGenerator:
    """Enhanced generator for BasicAppDataTypes"""

    def __init__(self, template_dir: Path):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.mapper = RegisterMapper()

    def generate(self, yaml_path: Path, output_dir: Path) -> None:
        """Generate VHDL from YAML package definition"""

        # Load package (auto-detects version)
        package = RegPackageFactory.from_yaml_file(yaml_path)
        click.echo(f"Loaded {package.app_name} (v{package.package_version})")

        # Generate mapping if using auto strategy
        if package.mapping_strategy == "auto":
            package.generate_mapping(self.mapper)
            click.echo(f"Generated mapping: {package.get_efficiency():.1f}% efficient")
        else:
            click.echo("Using manual register assignments")

        # Validate before generation
        errors = package.validate()
        if errors:
            click.echo("Validation errors:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            raise click.Abort()

        # Generate files
        self._generate_shim(package, output_dir)
        self._generate_main(package, output_dir)
        self._generate_package(package, output_dir)
        self._generate_documentation(package, output_dir)

        click.echo(f"Generated VHDL in {output_dir}")

    def _generate_shim(self, package: BasicAppsRegPackage, output_dir: Path) -> None:
        """Generate shim layer VHDL"""
        # Select template based on version
        if package.package_version.startswith("2"):
            template = self.env.get_template("custom_inst_shim_template_v2.vhd")
        else:
            template = self.env.get_template("custom_inst_shim_template.vhd")

        # Add helper methods to package for template
        self._add_template_helpers(package)

        # Render template
        content = template.render(
            app=package,
            timestamp=datetime.now().isoformat(),
        )

        # Write file
        output_path = output_dir / f"{package.app_name}_custom_inst_shim.vhd"
        output_path.write_text(content)
        click.echo(f"  Generated: {output_path.name}")

    def _generate_package(self, package: BasicAppsRegPackage, output_dir: Path) -> None:
        """Generate VHDL package with type utilities"""
        if not package.needs_type_utilities():
            return

        template = self.env.get_template("basic_app_types_pkg_template.vhd")
        content = template.render(app=package)

        output_path = output_dir / "basic_app_types_pkg.vhd"
        output_path.write_text(content)
        click.echo(f"  Generated: {output_path.name}")

    def _generate_documentation(self, package: BasicAppsRegPackage, output_dir: Path) -> None:
        """Generate mapping documentation"""
        doc_path = output_dir / f"{package.app_name}_mapping.md"

        doc_content = f"""
# {package.app_name} Register Mapping

Generated: {datetime.now().isoformat()}
Package Version: {package.package_version}
Strategy: {package.mapping_strategy}

## Register Map

| CR | Bits | Signal | Type | Description |
|----|------|--------|------|-------------|
"""
        for mapping in sorted(package.mapping_result, key=lambda m: (m.cr_number, m.bit_slice[0])):
            bit_range = f"[{mapping.bit_slice[0]}:{mapping.bit_slice[1]}]"
            doc_content += f"| {mapping.cr_number} | {bit_range} | {mapping.name} | {mapping.type.value} | {mapping.get_description()} |\n"

        doc_content += f"""

## Efficiency Report

- Total bits used: {package.get_bits_used()}/384
- Efficiency: {package.get_efficiency():.1f}%
- Registers used: {len(package.get_register_map())}/12

## Type Conversions

"""
        for dt in package.datatypes:
            if dt.type == BasicAppDataTypes.VOLTAGE_MV:
                doc_content += f"- {dt.name}: ±10V range, 305µV resolution\n"
            elif dt.type == BasicAppDataTypes.TIME_MS:
                doc_content += f"- {dt.name}: 0-65.5 seconds range\n"

        doc_path.write_text(doc_content)
        click.echo(f"  Generated: {doc_path.name}")

    def _add_template_helpers(self, package: BasicAppsRegPackage) -> None:
        """Add helper methods for template rendering"""

        def get_register_map():
            """Group mappings by CR number"""
            from collections import defaultdict
            reg_map = defaultdict(list)
            for m in package.mapping_result:
                reg_map[m.cr_number].append(m)
            return dict(reg_map)

        def get_efficiency():
            """Calculate packing efficiency"""
            bits_used = sum(dt.get_bit_width() for dt in package.datatypes)
            return (bits_used / 384) * 100

        def get_bits_used():
            """Total bits used"""
            return sum(dt.get_bit_width() for dt in package.datatypes)

        def has_voltage_types():
            """Check if package uses voltage types"""
            return any(dt.type == BasicAppDataTypes.VOLTAGE_MV
                      for dt in package.datatypes)

        def has_time_types():
            """Check if package uses time types"""
            return any(dt.type in [BasicAppDataTypes.TIME_MS,
                                  BasicAppDataTypes.TIME_US,
                                  BasicAppDataTypes.TIME_NS]
                      for dt in package.datatypes)

        # Attach methods to package instance
        package.get_register_map = get_register_map
        package.get_efficiency = get_efficiency
        package.get_bits_used = get_bits_used
        package.has_voltage_types = has_voltage_types
        package.has_time_types = has_time_types


@click.command()
@click.argument('yaml_file', type=click.Path(exists=True, path_type=Path))
@click.option('--output-dir', '-o', type=click.Path(path_type=Path),
              default=Path('VHDL/apps'), help='Output directory for generated VHDL')
@click.option('--validate-only', is_flag=True,
              help='Only validate YAML, do not generate code')
@click.option('--show-mapping', is_flag=True,
              help='Display register mapping report')
def main(yaml_file: Path, output_dir: Path, validate_only: bool, show_mapping: bool):
    """Generate CustomInstrument VHDL from BasicAppsRegPackage YAML"""

    # Load package
    try:
        package = RegPackageFactory.from_yaml_file(yaml_file)
    except Exception as e:
        click.echo(f"Error loading YAML: {e}", err=True)
        raise click.Abort()

    # Validate
    errors = package.validate()
    if errors:
        click.echo("Validation errors:", err=True)
        for error in errors:
            click.echo(f"  - {error}", err=True)
        raise click.Abort()

    click.echo(f"✓ Validated {package.app_name} (v{package.package_version})")

    # Show mapping if requested
    if show_mapping:
        mapper = RegisterMapper()
        package.generate_mapping(mapper)
        click.echo("\nRegister Mapping:")
        click.echo("-" * 60)
        for mapping in package.mapping_result:
            click.echo(f"CR{mapping.cr_number}[{mapping.bit_slice[0]}:{mapping.bit_slice[1]}] "
                      f"← {mapping.name} ({mapping.type.value})")
        click.echo(f"\nEfficiency: {package.get_efficiency():.1f}%")

    # Generate code unless validate-only
    if not validate_only:
        app_output_dir = output_dir / package.app_name
        app_output_dir.mkdir(parents=True, exist_ok=True)

        generator = CustomInstGenerator(Path('shared/custom_inst/templates'))
        generator.generate(yaml_file, app_output_dir)


if __name__ == '__main__':
    main()
```

#### 4.4 Type Utilities Package

Create `shared/custom_inst/templates/basic_app_types_pkg_template.vhd`:

```vhdl
-- ================================================================================
-- basic_app_types_pkg.vhd
-- Type conversion utilities for BasicAppDataTypes
-- Generated: {{ timestamp }}
-- ================================================================================

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

package basic_app_types_pkg is

    -- ============================================================
    -- Type Definitions
    -- ============================================================
    {% if app.has_voltage_types() %}
    subtype voltage_type is signed(15 downto 0);
    constant VOLTAGE_MV_PER_BIT : real := 305.0e-3;  -- mV per LSB
    constant VOLTAGE_MAX_MV : integer := 10000;      -- ±10V range
    {% endif %}

    {% if app.has_time_types() %}
    subtype time_ms_type is unsigned(15 downto 0);
    subtype time_us_type is unsigned(23 downto 0);
    subtype time_ns_type is unsigned(31 downto 0);
    {% endif %}

    -- ============================================================
    -- Conversion Functions
    -- ============================================================
    {% if app.has_voltage_types() %}
    -- Voltage conversions
    function mv_to_raw(mv: integer) return voltage_type;
    function raw_to_mv(raw: voltage_type) return integer;
    function clamp_voltage(v: voltage_type; max_v: voltage_type) return voltage_type;
    {% endif %}

    {% if app.has_time_types() %}
    -- Time conversions
    function ms_to_cycles(ms: time_ms_type; clk_freq_hz: integer) return unsigned;
    function cycles_to_ms(cycles: unsigned; clk_freq_hz: integer) return time_ms_type;
    {% endif %}

    -- ============================================================
    -- Constants
    -- ============================================================
    {% for dt in app.datatypes %}
    {% if dt.type == 'voltage_mv' and dt.default_value %}
    constant {{ dt.name.upper() }}_DEFAULT : voltage_type := to_signed({{ dt.get_raw_default() }}, 16);
    {% endif %}
    {% endfor %}

end package;

package body basic_app_types_pkg is

    {% if app.has_voltage_types() %}
    function mv_to_raw(mv: integer) return voltage_type is
        variable raw: integer;
    begin
        raw := (mv * 32767) / VOLTAGE_MAX_MV;
        return to_signed(raw, 16);
    end function;

    function raw_to_mv(raw: voltage_type) return integer is
    begin
        return to_integer((raw * VOLTAGE_MAX_MV) / 32767);
    end function;

    function clamp_voltage(v: voltage_type; max_v: voltage_type) return voltage_type is
    begin
        if v > max_v then
            return max_v;
        elsif v < -max_v then
            return -max_v;
        else
            return v;
        end if;
    end function;
    {% endif %}

    {% if app.has_time_types() %}
    function ms_to_cycles(ms: time_ms_type; clk_freq_hz: integer) return unsigned is
        variable cycles: unsigned(31 downto 0);
    begin
        cycles := resize(ms * (clk_freq_hz/1000), 32);
        return cycles;
    end function;

    function cycles_to_ms(cycles: unsigned; clk_freq_hz: integer) return time_ms_type is
    begin
        return resize(cycles / (clk_freq_hz/1000), 16);
    end function;
    {% endif %}

end package body;
```

## Design Decisions Needed

### 4.1 Template Versioning

**Option A: Separate Templates**
```
templates/
  custom_inst_shim_template.vhd      # Legacy
  custom_inst_shim_template_v2.vhd   # BasicAppDataTypes
```
- Pro: Clean separation
- Con: Duplicate code

**Option B: Single Template with Conditionals**
```jinja
{% if app.package_version.startswith('2') %}
    {# New type-aware code #}
{% else %}
    {# Legacy code #}
{% endif %}
```
- Pro: Single source of truth
- Con: Complex template

### 4.2 Type Utility Generation

**Option A: Always Generate Package**
- Generate `basic_app_types_pkg.vhd` for every app
- Import even if not needed

**Option B: Conditional Generation**
- Only generate if app uses voltage/time types
- Check with `app.needs_type_utilities()`

**Option C: Global Shared Package**
- One package for all apps
- Risk of version conflicts

### 4.3 Documentation Generation

What documentation should be auto-generated?

```python
# Option 1: Markdown only
generate_markdown_docs(package)

# Option 2: VHDL comments + Markdown
generate_vhdl_header_comments(package)
generate_markdown_docs(package)

# Option 3: Full suite
generate_markdown_docs(package)
generate_python_api_docs(package)
generate_cocotb_test_template(package)
```

### 4.4 Migration Tools

```python
# Should we provide automatic migration?
class MigrationTool:
    def migrate_yaml(self, old_yaml: Path) -> Path:
        """Auto-convert v1.0 to v2.0 YAML"""

    def migrate_vhdl(self, old_vhdl: Path) -> Path:
        """Update existing VHDL to use new shim"""

    def generate_diff_report(self, old: Path, new: Path):
        """Show what changed in migration"""
```

## Test Cases

Create `tests/test_code_generation.py`:

```python
def test_generate_v2_yaml():
    """Test generating VHDL from v2.0 YAML"""
    yaml_content = """
    package_version: "2.0"
    app_name: "TestApp"
    datatypes:
      - name: "output_voltage"
        type: "voltage_mv"
        default_value: 2400
      - name: "enable_output"
        type: "boolean"
        default_value: false
    """

    with tempfile.NamedTemporaryFile(suffix='.yaml') as f:
        f.write(yaml_content.encode())
        f.flush()

        generator = CustomInstGenerator(template_dir)
        output_dir = Path(tempfile.mkdtemp())
        generator.generate(Path(f.name), output_dir)

        # Check generated files
        shim_path = output_dir / "TestApp_custom_inst_shim.vhd"
        assert shim_path.exists()

        # Verify content
        shim_content = shim_path.read_text()
        assert "output_voltage <= raw_to_voltage_signed(" in shim_content
        assert "enable_output <= app_reg_" in shim_content
        assert "Package Version: 2.0" in shim_content

def test_backward_compatibility():
    """Test generating from v1.0 YAML still works"""
    old_yaml = """
    app_name: "LegacyApp"
    registers:
      - name: "Counter"
        reg_type: counter_16bit
        cr_number: 6
    """

    # Should still generate valid VHDL
    generator = CustomInstGenerator(template_dir)
    # ... test generation

def test_mapping_report():
    """Test register mapping documentation"""
    package = create_test_package()
    generator = CustomInstGenerator(template_dir)

    output_dir = Path(tempfile.mkdtemp())
    generator._generate_documentation(package, output_dir)

    doc_path = output_dir / f"{package.app_name}_mapping.md"
    assert doc_path.exists()

    content = doc_path.read_text()
    assert "Register Map" in content
    assert "Efficiency Report" in content
    assert "Type Conversions" in content

def test_type_utilities_generation():
    """Test conditional type utilities package"""
    # Package with voltage types
    voltage_package = create_package_with_voltage()
    generator = CustomInstGenerator(template_dir)
    generator._generate_package(voltage_package, output_dir)
    assert (output_dir / "basic_app_types_pkg.vhd").exists()

    # Package without special types
    simple_package = create_simple_package()
    generator._generate_package(simple_package, output_dir2)
    assert not (output_dir2 / "basic_app_types_pkg.vhd").exists()

def test_cli_validation():
    """Test CLI validate-only mode"""
    result = runner.invoke(main, ['test.yaml', '--validate-only'])
    assert result.exit_code == 0
    assert "Validated" in result.output
    # Should not generate files
    assert not Path("VHDL/apps/TestApp").exists()

def test_cli_show_mapping():
    """Test CLI mapping display"""
    result = runner.invoke(main, ['test.yaml', '--show-mapping'])
    assert "Register Mapping:" in result.output
    assert "CR6[31:16]" in result.output
    assert "Efficiency:" in result.output
```

## Migration Example

### DS1140_PD Migration Process

1. **Create v2.0 YAML:**
```bash
python tools/migrate_to_bad.py DS1140_PD_app.yaml -o DS1140_PD_app_v2.yaml
```

2. **Generate new VHDL:**
```bash
python tools/generate_custom_inst.py DS1140_PD_app_v2.yaml --show-mapping
```

3. **Compare old vs new:**
```
Old Implementation:
  - 9 registers used (CR6-CR14)
  - Manual bit slicing in YAML comments
  - No type safety

New Implementation:
  - 3-4 registers used (auto-packed)
  - Type-aware conversions
  - Automatic documentation
```

4. **Update main application:**
```vhdl
-- Old port
intensity : in std_logic_vector(15 downto 0);

-- New port
intensity : in signed(15 downto 0);  -- voltage_type
```

## Success Criteria

Phase 4 is complete when:

- [ ] Shim template v2 handles all BasicAppDataTypes
- [ ] Main template includes type utilities
- [ ] Generator supports both v1.0 and v2.0 YAMLs
- [ ] Mapping documentation auto-generated
- [ ] Type utilities package generated when needed
- [ ] DS1140_PD successfully generated with new system
- [ ] Unit tests passing for generation
- [ ] Phase summary written to `BAD_Phase4_COMPLETE.md`

## Output Artifacts

### Required Files
1. `shared/custom_inst/templates/*_v2.vhd` - New templates
2. `tools/generate_custom_inst.py` - Enhanced generator
3. `VHDL/apps/DS1140_PD_v2/` - Generated example
4. `tests/test_code_generation.py` - Test suite
5. `docs/BasicAppDataTypes/BAD_Phase4_COMPLETE.md` - Summary

### Summary Format
The completion summary should include:
- Template design decisions
- Generation workflow changes
- DS1140_PD generation results
- Documentation samples
- Integration notes for Phase 5

## Handoff to Phase 5

Phase 5 will need:
- Complete generation pipeline
- Example generated VHDL
- Test templates
- Documentation format

Update `BAD_Phase5_Testing.md` header with:
```markdown
**Prerequisites:** Phase 1-4 complete
**Phase 4 Summary:** ./BAD_Phase4_COMPLETE.md
**Phase 4 Commit:** {git_hash}
```

## Interactive Decisions

As you implement, we'll decide:

1. **Template structure**: Separate files or conditionals?
2. **Documentation depth**: How comprehensive should auto-docs be?
3. **Migration automation**: How much hand-holding for migrations?
4. **Error handling**: How verbose should generation errors be?
5. **Optimization**: Should generator optimize packing further?

## Getting Started

1. Create enhanced shim template with type awareness
2. Add template helper methods to package
3. Update generator to handle both versions
4. Test with simple example first
5. Generate DS1140_PD as proof of concept
6. Add comprehensive documentation generation

Remember: The generator bridges the gap between high-level types and low-level VHDL. Make the generated code **readable and maintainable**!

---

**Questions?** Code generation is where the magic happens - types become signals, packages become VHDL. Let's make it seamless!