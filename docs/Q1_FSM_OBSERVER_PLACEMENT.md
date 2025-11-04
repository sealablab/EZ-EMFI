# Q1: FSM Observer Placement Decision

**Question:** Should `fsm_observer.vhd` be in volo-platform-vhdl (generic utility) or probe-specific?

**Answer:** `fsm_observer.vhd` should move to **volo-platform-vhdl** as a generic utility.

**Decision Date:** 2025-11-03
**Confidence Level:** ✅ High (user-confirmed + authoritative pattern documentation)

---

## Executive Summary

The FSM Observer Pattern is a **generic, platform-agnostic debugging utility** that should be treated as core Moku platform infrastructure, not probe-specific code.

**Recommendation:**
- ✅ Move `fsm_observer.vhd` → `volo-platform-vhdl/`
- ✅ Move `volo_voltage_pkg.vhd` → `volo-platform-vhdl/packages/` (dependency)
- ✅ Update all probe drivers to import from volo-platform-vhdl submodule

---

## Evidence Supporting Generic Utility Classification

### 1. Authoritative Pattern Documentation

**Source:** `/tmp/moku-instrument-forge/docs/debugging/fsm_observer_pattern.md` (509 lines)

The forge documentation explicitly states:

> **Recommended for:** All custom VHDL instruments with state machines

Key characteristics documented:
- **Platform-agnostic**: Works on Go/Lab/Pro/Delta
- **Non-invasive**: Parallel signal observation (no FSM modification required)
- **Fixed 6-bit interface**: Supports FSMs with up to 64 states
- **Zero runtime overhead**: LUT calculated at elaboration time
- **Single tested entity**: One implementation serves all FSMs

### 2. User Confirmation

**User statement (2025-11-03):**
> "we definitely dont want the fsm-observer pattern to be thought of as 'probe specific'"

This directly confirms the intended architectural role.

### 3. Multi-Module Reuse Evidence

**Current usage in EZ-EMFI:**
1. `DS1120_PD_volo_main.vhd` - DS1120A probe driver FSM (instantiates `U_OBSERVER`)
2. `DS1140_PD_volo_main.vhd` - DS1140A probe driver FSM (instantiates `U_FSM_OBSERVER`)
3. `volo_bram_loader.vhd` - Generic BRAM loading utility (instantiates `U_BRAM_OBSERVER`)

**Analysis:** Used across 2 different probe families AND a generic loader utility. This demonstrates the pattern is NOT probe-specific but a general-purpose debugging tool.

### 4. Implementation Characteristics

**File:** `/home/user/EZ-EMFI/VHDL/fsm_observer.vhd` (178 lines)

Key implementation details:
```vhdl
entity fsm_observer is
    generic (
        NUM_STATES : positive := 8;  -- Configurable for any FSM size
        V_MIN : real := 0.0;
        V_MAX : real := 2.5;
        FAULT_STATE_THRESHOLD : natural := 8;  -- Optional fault mode
        -- State name documentation (optional, for tooling)
        STATE_0_NAME : string := "STATE_0";
        -- ... up to STATE_7_NAME (extensible to STATE_63_NAME)
    );
    port (
        clk          : in  std_logic := '0';
        reset        : in  std_logic := '0';
        state_vector : in  std_logic_vector(5 downto 0);  -- Fixed 6-bit
        voltage_out  : out signed(15 downto 0)            -- Moku ±5V
    );
end entity;
```

**Generic design characteristics:**
- **Configurable:** Generic parameters adapt to any FSM size/voltage range
- **Fixed interface:** 6-bit input works for all FSMs (up to 64 states)
- **Platform-standard output:** Moku 16-bit signed ±5V (all platforms)
- **Optional features:** Fault sign-flip mode via FAULT_STATE_THRESHOLD
- **Documentation-friendly:** State name generics for tooling integration

**No probe-specific logic whatsoever.**

### 5. Dependency Analysis

**Single dependency:** `work.volo_voltage_pkg.all` (line 37)

**File:** `/home/user/EZ-EMFI/VHDL/packages/volo_voltage_pkg.vhd` (328 lines)

```vhdl
--------------------------------------------------------------------------------
-- Package: volo_voltage_pkg
-- Purpose: Platform-independent voltage conversion utilities for ADC/DAC interfaces
-- Author: johnnyc
-- Date: 2025-01-27
--
-- DATADEF PACKAGE: This package provides voltage conversion utilities for
-- 16-bit signed ADC/DAC interfaces. Designed for maximum Verilog compatibility
-- and testbench convenience.
--
-- VOLTAGE SPECIFICATION:
-- - Digital range: -32768 to +32767 (0x8000 to 0x7FFF)
-- - Voltage range: -5.0V to +5.0V (full-scale analog input/output)
-- - Resolution: ~305 µV per digital step (10V / 65536)
--------------------------------------------------------------------------------
```

**Analysis:** `volo_voltage_pkg` is ALSO a platform-independent utility package. It provides:
- Standard Moku ±5V digital/analog conversions
- Testbench convenience functions
- Validation and clamping utilities
- Zero probe-specific logic

**Recommendation:** Both `fsm_observer.vhd` AND `volo_voltage_pkg.vhd` should move to volo-platform-vhdl together.

---

## Architectural Fit for volo-platform-vhdl

### What is volo-platform-vhdl?

**Purpose (from planning doc):** Reusable VHDL utilities for Moku CloudCompile instruments

**Expected contents:**
- Clock dividers (`volo_clk_divider`)
- BRAM loaders (`volo_bram_loader`)
- VoloApp framework (Loader/Shim/Main architecture)
- Platform-agnostic debugging utilities
- Voltage/timing utilities

### Why fsm_observer Belongs Here

| Criterion | fsm_observer | volo_clk_divider (reference) |
|-----------|--------------|------------------------------|
| **Platform-agnostic** | ✅ Yes (Go/Lab/Pro/Delta) | ✅ Yes |
| **Reusable across instruments** | ✅ Yes (3+ modules) | ✅ Yes |
| **No instrument-specific logic** | ✅ None | ✅ None |
| **Fixed, stable interface** | ✅ 6-bit + 16-bit signed | ✅ Clock ports |
| **Documented pattern** | ✅ Forge docs | ✅ Implied standard |
| **Zero probe dependencies** | ✅ Only volo_voltage_pkg | ✅ Only IEEE libs |

**fsm_observer matches the profile of other volo-platform utilities perfectly.**

---

## Migration Plan

### Step 1: Create volo-platform-vhdl Package Structure

```
volo-platform-vhdl/
├── packages/
│   └── volo_voltage_pkg.vhd       # Platform voltage utilities
├── debugging/
│   └── fsm_observer.vhd            # FSM debugging pattern
├── loader/
│   └── volo_bram_loader.vhd        # (future migration candidate)
└── docs/
    └── fsm_observer_pattern.md     # (copy from forge)
```

### Step 2: Update EZ-EMFI Imports

**Before (current):**
```vhdl
-- DS1120_PD_volo_main.vhd
use work.volo_voltage_pkg.all;  -- Local VHDL/packages/

-- fsm_observer instantiation
U_OBSERVER : entity work.fsm_observer  -- Local VHDL/
```

**After (with submodule):**
```vhdl
-- DS1120_PD_volo_main.vhd
use volo_platform.volo_voltage_pkg.all;  -- From submodule

-- fsm_observer instantiation
U_OBSERVER : entity volo_platform.fsm_observer  -- From submodule
```

**Files requiring updates:**
1. `DS1120_PD_volo_main.vhd`
2. `DS1140_PD_volo_main.vhd`
3. `volo_bram_loader.vhd` (if migrating loader too)

### Step 3: Update Build System

**Current (ghdl.sh):**
```bash
# Compile local packages
ghdl -a VHDL/packages/volo_voltage_pkg.vhd
ghdl -a VHDL/fsm_observer.vhd
```

**After (with submodule):**
```bash
# Compile volo-platform-vhdl submodule
ghdl -a volo-platform-vhdl/packages/volo_voltage_pkg.vhd
ghdl -a volo-platform-vhdl/debugging/fsm_observer.vhd
```

### Step 4: Update CocotB Tests

**Test files potentially affected:**
- `tests/fsm_observer_wrapper.vhd` (if exists)
- Any tests directly instantiating fsm_observer

**Action:** Update library references from `work` → `volo_platform`

---

## Risks and Mitigations

### Risk 1: Build Order Dependencies

**Issue:** volo_voltage_pkg must compile before fsm_observer

**Mitigation:**
- Document compilation order in volo-platform-vhdl/README.md
- Add Makefile/build script to volo-platform-vhdl
- CocotB tests should use volo-platform's build script

### Risk 2: Forge vs EZ-EMFI Divergence

**Issue:** Forge has authoritative fsm_observer_pattern.md, EZ-EMFI has implementation

**Mitigation:**
- Copy docs/debugging/fsm_observer_pattern.md to volo-platform-vhdl
- Add "Authoritative Source: moku-instrument-forge" note
- Update CLAUDE.md in volo-platform-vhdl with pattern usage

### Risk 3: Version Synchronization

**Issue:** If fsm_observer evolves, both repos need updates

**Mitigation:**
- Treat volo-platform-vhdl as authoritative (submodule upstream)
- Use git submodule pinning in EZ-EMFI
- Document update workflow in volo-platform-vhdl

---

## Alternative Approaches Considered

### Alternative 1: Keep fsm_observer Probe-Specific

**Rejected because:**
- ❌ User explicitly said "we definitely dont want the fsm-observer pattern to be thought of as 'probe specific'"
- ❌ Contradicts forge documentation ("All custom VHDL instruments")
- ❌ Already used in non-probe code (volo_bram_loader)
- ❌ Would require duplicating code across probe families

### Alternative 2: Create Separate fsm-debugging-vhdl Submodule

**Rejected because:**
- ❌ Overcomplicates submodule hierarchy
- ❌ Only 178 lines of code (too small for separate repo)
- ❌ Dependencies on volo_voltage_pkg couple it to platform utilities anyway
- ❌ Adds maintenance overhead for marginal organizational benefit

### Alternative 3: Vendor into Each Probe

**Rejected because:**
- ❌ Violates DRY principle
- ❌ Creates divergence risk (each probe could modify independently)
- ❌ Loses "single tested entity" benefit from forge docs
- ❌ Contradicts established forge/EZ-EMFI architectural patterns

---

## Validation Criteria

### Success Metrics

✅ **Organizational:**
- fsm_observer in volo-platform-vhdl repository
- volo_voltage_pkg in volo-platform-vhdl/packages/
- Documentation copied from forge (with attribution)

✅ **Technical:**
- All EZ-EMFI probe drivers compile with updated imports
- CocotB tests pass with volo_platform library references
- Build time unchanged (< 2 minutes)
- Zero behavioral changes to FSM observation

✅ **Documentation:**
- volo-platform-vhdl/README.md documents fsm_observer usage
- CLAUDE.md updated with debugging pattern guidance
- EZ-EMFI docs reference volo-platform-vhdl for fsm_observer

---

## Next Steps

### Immediate (this branch)

1. ✅ Document Q1 decision (this file)
2. Commit Q1 recommendation
3. Update START_HERE.md with Q1 resolution

### Iteration 1 (spike branch)

When creating `spike/forge-as-copy` or similar:

1. Create volo-platform-vhdl skeleton
2. Copy fsm_observer.vhd → volo-platform-vhdl/debugging/
3. Copy volo_voltage_pkg.vhd → volo-platform-vhdl/packages/
4. Update DS1120_PD imports and test compilation
5. Run CocotB tests to validate
6. Document integration in spike findings

### Iteration 2 (mono-repo integration)

1. Finalize volo-platform-vhdl structure
2. Migrate all probe drivers to use submodule
3. Update build orchestration (Q2 decision)
4. Update CLAUDE.md with new import patterns

---

## References

### Primary Documentation

- **Authoritative Pattern:** `/tmp/moku-instrument-forge/docs/debugging/fsm_observer_pattern.md`
- **Implementation:** `/home/user/EZ-EMFI/VHDL/fsm_observer.vhd`
- **Dependency:** `/home/user/EZ-EMFI/VHDL/packages/volo_voltage_pkg.vhd`

### Usage Examples

- **DS1120_PD:** Search for `U_OBSERVER` instantiation
- **DS1140_PD:** Search for `U_FSM_OBSERVER` instantiation
- **volo_bram_loader:** Search for `U_BRAM_OBSERVER` instantiation

### Related Decisions

- **Q2:** Migrate both DS1120_PD and DS1140_PD? (pending)
- **Q3:** Test coverage threshold? (pending)
- **Spike 1:** Forge integration strategy (depends on this decision)

---

## Appendix: User Confirmation

**User message (2025-11-03):**

> we definitely dont want the fsm-observer pattern to be thought of as 'probe specific'

This explicit confirmation removes any ambiguity about architectural intent.

---

**Decision Finalized:** 2025-11-03
**Documented By:** Claude (AI assistant)
**Approved By:** User (via explicit confirmation)
**Status:** ✅ Ready for spike branch validation
