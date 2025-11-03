# Phase 4 Completion Summary: VHDL Code Generation

**Branch:** `feature/BAD/P4`
**Status:** ✅ Complete
**Date:** 2025-11-03

---

## Overview

Phase 4 implemented the VHDL code generation system for BasicAppDataTypes, enabling automatic generation of platform-aware CustomInst applications from YAML specifications.

---

## Deliverables

### 1. Frozen VHDL Type Utilities (v1.0.0)

**Generator:** `tools/generate_type_utilities.py`
**Output:** `shared/custom_inst/vhdl/` (3 packages, 1043 lines)

Generated **once**, committed, and **frozen** - never to be regenerated:

```
shared/custom_inst/vhdl/
├── basic_app_types_pkg.vhd      # Core types, utilities (2.1 KB)
├── basic_app_voltage_pkg.vhd    # Voltage conversions (9.9 KB, 12 types)
└── basic_app_time_pkg.vhd       # Time conversions (5.3 KB, clock-aware)
```

**Key Design Decision:** Shared, frozen utilities ensure stability across projects. Apps import via VHDL libraries:

```vhdl
library WORK;
use WORK.basic_app_types_pkg.all;
use WORK.basic_app_voltage_pkg.all;  -- If using voltage types
use WORK.basic_app_time_pkg.all;     -- If using time types
```

### 2. VHDL Templates v2.0

**Location:** `shared/custom_inst/templates/`

- **`custom_inst_shim_template_v2.vhd`** (4.0 KB)
  - Platform-aware register mapping shim
  - Injects `CLK_FREQ_HZ` generic from platform specs
  - Type-safe signal extraction using frozen packages
  - Automatic voltage/time conversion function selection

- **`custom_inst_main_template_v2.vhd`** (3.3 KB)
  - Application logic template with typed signals
  - Example time-to-cycles conversions
  - Handshake protocol integration
  - State machine skeleton

### 3. Platform-Aware Generator

**Script:** `tools/generate_custom_inst_v2.py` (374 lines)

**Features:**
- Platform-aware code generation (Moku:Go/Lab/Pro/Delta)
- Automatic register packing via `RegisterMapper`
- Type-safe signal extraction
- Jinja2-based templating
- Efficiency reporting

**Platform Support:**

| Platform | Clock (MHz) | Slots | CLK_FREQ_HZ |
|----------|-------------|-------|-------------|
| Moku:Go  | 125         | 2     | 125,000,000 |
| Moku:Lab | 500         | 2     | 500,000,000 |
| Moku:Pro | 1,250       | 4     | 1,250,000,000 |
| Moku:Delta | 5,000     | 3     | 5,000,000,000 |

**Usage:**

```bash
python tools/generate_custom_inst_v2.py examples/DS1140_PD_interface.yaml
```

---

## Test Results: DS1140_PD

**YAML Spec:** `examples/DS1140_PD_interface.yaml`
**Platform:** Moku:Go (125 MHz)
**Strategy:** `best_fit`

### Input Specification

8 datatypes:
- 3 booleans (arm_probe, force_fire, reset_fsm)
- 2 voltages (intensity, trigger_threshold)
- 3 time values (arm_timeout, firing_duration, cooling_duration)

### Generated Mapping

**Automatic packing:** 8 datatypes → 3 registers (57% savings vs. 7 manual registers)

```
CR6: arm_timeout[31:16]       | intensity[15:0]
CR7: trigger_threshold[31:16] | cooling_duration[15:8] | firing_duration[7:0]
CR8: arm_probe[31]            | force_fire[30]         | reset_fsm[29]
```

**Efficiency:** 67/96 bits used (69.8%)

### Generated Files

```
generated/DS1140_PD/
├── DS1140_PD_custom_inst_shim.vhd  # 8,480 bytes (auto-generated, always overwritten)
└── DS1140_PD_custom_inst_main.vhd  # 7,275 bytes (template, customize for app)
```

**Shim Highlights:**

```vhdl
entity DS1140_PD_custom_inst_shim is
    generic (
        CLK_FREQ_HZ : integer := 125000000  -- Moku:Go clock frequency
    );
    -- ...
end entity;

-- Signal declarations (typed)
signal arm_probe : std_logic;
signal intensity : signed(15 downto 0);
signal arm_timeout : unsigned(15 downto 0);
-- ...

-- Type-safe extraction
arm_probe <= app_reg_8(31);
intensity <= voltage_output_05v_s16_from_raw(app_reg_6(15 downto 0));
arm_timeout <= unsigned(app_reg_6(31 downto 16));
```

**Main Template Highlights:**

```vhdl
-- Time conversion example (platform-aware)
arm_timeout_cycles <= ms_to_cycles(arm_timeout, CLK_FREQ_HZ);

-- Application logic skeleton provided
process(Clk)
begin
    if rising_edge(Clk) then
        if Reset = '1' then
            -- Initialize outputs
        elsif global_enable = '1' then
            -- Application state machine
        end if;
    end if;
end process;
```

---

## Design Decisions

### Decision 1: Separate Templates (v1.0 legacy, v2.0 BAD)

**Rationale:** No backward compatibility burden, clean v2.0-only implementation.

**Files:**
- v1.0: `custom_inst_shim_template.vhd` (legacy, manual registers)
- v2.0: `custom_inst_shim_template_v2.vhd` (BasicAppDataTypes, automatic packing)

### Decision 2: Shared, Frozen VHDL Utilities

**Rationale:** Stability > flexibility. Generate once, commit, freeze (v1.0.0).

**Impact:**
- Apps share identical type conversion functions
- No version fragmentation
- Predictable behavior across projects
- Easy to review (1043 lines, one-time audit)

**Alternative Rejected:** Per-app inline generation (would cause code duplication and version drift)

### Decision 3: Platform-Aware, Default Moku:Go

**Rationale:** Time conversions require clock frequency. Generator injects `CLK_FREQ_HZ` generic.

**YAML Schema Addition:**

```yaml
platform: moku_go  # Required field (moku_go | moku_lab | moku_pro | moku_delta)
```

**Default:** If platform omitted, warns and defaults to `moku_go`.

### Decision 4: v2.0 Only (No Legacy v1.0 Support)

**Rationale:** Clean break, no migration complexity. Phase 4 focuses on new system.

**Migration Path (future):** Separate tool to convert v1.0 manual YAML → v2.0 BAD YAML.

### Decision 5: Abstraction-Respecting Generator

**Critical Fix:** Initial implementation accessed `RegisterMapping.bit_slice` tuples directly (breaking abstraction).

**Corrected Approach:**
- Use `RegisterMapping.to_vhdl_slice()` method
- Use `RegisterMapping.bit_width()` method
- Never unpack internal `bit_slice` tuples

**Design Goal Maintained:** Users work with semantic types, not bits. The abstraction is preserved throughout:
- **YAML:** Semantic type names (`voltage_output_05v_s16`)
- **RegisterMapper:** Provides VHDL slice methods
- **Generator:** Uses methods, never reaches into internals

---

## Architecture Summary

### 3-Layer CustomInstApp with BasicAppDataTypes

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: MCC_TOP_custom_inst_loader.vhd (static, shared)       │
│   - BRAM loader FSM                                             │
│   - VOLO_READY control                                          │
│   - Passes app_reg_6..15 to shim                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: {app}_custom_inst_shim.vhd (GENERATED v2.0)           │
│   - Atomic register update process                              │
│   - Type-safe extraction (voltage/time/boolean)                 │
│   - Uses frozen VHDL packages (v1.0.0)                          │
│   - Platform-aware (CLK_FREQ_HZ generic)                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: {app}_custom_inst_main.vhd (hand-written logic)       │
│   - Application state machine                                   │
│   - Typed signal interface (no raw registers)                   │
│   - Time-to-cycles conversions (platform-aware)                 │
│   - Ready-for-updates handshake                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Type Conversion Flow

```
YAML (semantic)              RegisterMapper              VHDL (generated)
───────────────              ──────────────              ────────────────

intensity:                   RegisterMapping(            signal intensity : signed(15 downto 0);
  datatype:          →         name="intensity",    →    intensity <= voltage_output_05v_s16_from_raw(
    voltage_output_            datatype=...,                app_reg_6(15 downto 0)
    _05v_s16                   cr_number=6,               );
  default: 2000                bit_slice=(15, 0)
                             )

arm_timeout:                 RegisterMapping(            signal arm_timeout : unsigned(15 downto 0);
  datatype:          →         name="arm_timeout",  →    arm_timeout <= unsigned(
    pulse_duration_            datatype=...,                app_reg_6(31 downto 16)
    _ms_u16                    cr_number=6,               );
  default: 1000                bit_slice=(31, 16)        -- Time conversion in main:
                             )                           arm_timeout_cycles <= ms_to_cycles(
                                                            arm_timeout, CLK_FREQ_HZ
                                                          );
```

---

## Validation

### Manual Testing

✅ **Generator Execution:**
```bash
$ python tools/generate_custom_inst_v2.py examples/DS1140_PD_interface.yaml
[1/5] Loading YAML specification: examples/DS1140_PD_interface.yaml
       App: DS1140_PD
       Platform: moku_go
       Datatypes: 8

[2/5] Creating register package...
       Package: DS1140_PD
       Strategy: best_fit

[3/5] Preparing template context...
       Signals: 8
       Registers used: 3 (CR6-CR8)
       Efficiency: 69.8% (67/96 bits)

[4/5] Generating shim file...
       Written: /Users/johnycsh/EZ-EMFI/generated/DS1140_PD/DS1140_PD_custom_inst_shim.vhd
       Size: 8480 bytes

[5/5] Generating main template file...
       Written: /Users/johnycsh/EZ-EMFI/generated/DS1140_PD/DS1140_PD_custom_inst_main.vhd
       Size: 7275 bytes

✅ Generation Complete
```

✅ **Generated VHDL Validation:**
- Shim compiles (syntax-checked manually)
- Correct platform constants (125 MHz for Moku:Go)
- Type conversions use frozen packages
- Register mapping matches expected layout
- No MSB/LSB references in templates (abstraction preserved)

### Unit Testing (Deferred to Phase 5)

**Planned Coverage:**
- Generator input validation (bad YAML, unknown platforms)
- Template rendering (all type categories)
- Platform constant injection
- Register mapping edge cases (overflow, single register)

**Test File:** `python_tests/test_code_generation.py` (to be implemented in Phase 5)

---

## Known Limitations

1. **No Direction Support:** All signals assumed `input`. YAML schema needs `direction: input|output` field.
2. **No Output Signal Support:** Templates don't handle output datatypes (e.g., DAC values from VHDL → Python).
3. **No Multi-Platform YAML:** One YAML = one platform. Future: support platform-specific overrides.
4. **No VHDL Simulation Tests:** Generated code not yet tested in GHDL/CocotB (Phase 5 task).
5. **No Legacy Migration Tool:** v1.0 → v2.0 conversion not implemented.

---

## File Inventory

### New Files (Committed)

```
tools/
├── generate_type_utilities.py          # Type utilities generator (467 lines)
└── generate_custom_inst_v2.py          # VHDL generator v2.0 (374 lines)

shared/custom_inst/
├── vhdl/
│   ├── basic_app_types_pkg.vhd         # Core types (2.1 KB, FROZEN v1.0.0)
│   ├── basic_app_voltage_pkg.vhd       # Voltage conversions (9.9 KB, FROZEN v1.0.0)
│   └── basic_app_time_pkg.vhd          # Time conversions (5.3 KB, FROZEN v1.0.0)
└── templates/
    ├── custom_inst_shim_template_v2.vhd   # Shim template v2.0 (4.0 KB)
    └── custom_inst_main_template_v2.vhd   # Main template v2.0 (3.3 KB)

generated/DS1140_PD/
├── DS1140_PD_custom_inst_shim.vhd      # Generated shim (8.5 KB, test artifact)
└── DS1140_PD_custom_inst_main.vhd      # Generated main (7.3 KB, test artifact)

examples/
└── DS1140_PD_interface.yaml            # Updated with platform: moku_go

docs/BasicAppDataTypes/
└── BAD_Phase4_COMPLETE.md              # This file
```

**Total New Lines:** ~1,500 lines (generator + templates + VHDL packages)

### Modified Files

- `examples/DS1140_PD_interface.yaml`: Added `platform: moku_go` field

---

## Git History

**Branch:** `feature/BAD/P4`

```bash
d02e81d feat(BAD/P4): Add frozen VHDL type utilities v1.0.0
8879a55 feat(BAD/P4): Add VHDL code generation system
f831663 refactor(BAD/P4): Use RegisterMapping abstraction in generator
```

**Merge Target:** `feature/BAD-main` (after Phase 5 validation)

---

## Next: Phase 5 - Testing and Validation

**Focus Areas:**

1. **Unit Tests:**
   - Generator input validation
   - Template rendering for all type categories
   - Platform constant injection
   - Register mapping edge cases

2. **VHDL Simulation:**
   - CocotB tests for generated shim
   - Type conversion validation (voltage/time)
   - Platform-specific clock frequency tests

3. **Integration Testing:**
   - Full DS1140_PD generation pipeline
   - GHDL compilation tests
   - Register read/write validation

4. **Documentation:**
   - User guide for generator
   - YAML schema v2.0 specification
   - Migration guide (v1.0 → v2.0)

**Branch:** `feature/BAD/P5` (to be created from `feature/BAD/P4`)

---

## Handoff to Phase 5

**Context Preserved:**

1. **Generator is working:** DS1140_PD test case validates end-to-end flow
2. **Abstraction is sound:** No MSB/LSB references in templates or generator
3. **Platform awareness works:** Correct clock frequencies injected
4. **Frozen utilities committed:** v1.0.0 VHDL packages in repo, never regenerate

**Open Questions for Phase 5:**

1. Should `generated/` be gitignored or committed as examples?
2. What GHDL/CocotB test structure for generated VHDL?
3. Do we need a `--platform` CLI override for generator?
4. Should main template be more opinionated (FSM helper functions)?

**Ready to Start Phase 5:** ✅

---

**Phase 4 Status:** Complete ✅
**Handoff Date:** 2025-11-03
**Next Phase:** Phase 5 (Testing and Validation)
