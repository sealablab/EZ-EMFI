# Mono-Repo Refactor: Pickup Document

**Date:** 2025-11-03
**Status:** Planning Phase - Ready to Execute
**Goal:** Extract VHDL utilities from EZ-EMFI, create composable `moku-custom-BPD` mono-repo inspired by moku-instrument-forge

---

## 📍 Where We Left Off

You successfully refactored code generation into **moku-instrument-forge** (https://github.com/sealablab/moku-instrument-forge) with:
- ✅ Clean 5-agent architecture (forge, deployment, docgen, hardware-debug, workflow-coordinator)
- ✅ Git submodules for composability (`basic-app-datatypes`, `moku-models`, `riscure-models`)
- ✅ Intentional context management (`.claude/agents/` with detailed `agent.md` files)
- ✅ 69 passing tests validating the entire toolchain

**Remaining value in EZ-EMFI to extract:**
- 🔌 VHDL utilities (`volo_bram_loader`, `volo_clk_divider`, `volo_voltage_threshold_trigger_core`)
- 📦 VHDL packages (`volo_common_pkg`, `volo_lut_pkg`, `volo_voltage_pkg`)
- 🧪 Comprehensive CocotB progressive test suite
- 🎛️ Probe-specific FSMs (`ds1120_pd_fsm.vhd`, `fsm_observer.vhd`)

---

## 🎯 Proposed Architecture

### Phase 1: Create `volo-platform-vhdl` (New Git Submodule)

**Purpose:** Reusable VHDL utilities + CocotB tests for Moku platform

```
volo-platform-vhdl/
├── .claude/
│   ├── agents/
│   │   └── vhdl-test-context/
│   │       └── agent.md         # CocotB testing patterns
│   └── commands/
│       └── test-vhdl.md         # /test-vhdl [module]
├── vhdl/
│   ├── utilities/
│   │   ├── volo_bram_loader.vhd
│   │   ├── volo_clk_divider.vhd
│   │   └── volo_voltage_threshold_trigger_core.vhd
│   ├── packages/
│   │   ├── volo_common_pkg.vhd
│   │   ├── volo_lut_pkg.vhd
│   │   └── volo_voltage_pkg.vhd
│   └── test_stubs/
│       ├── CustomWrapper_test_stub.vhd
│       └── test_shim_handshake.vhd
├── tests/
│   ├── conftest.py              # Shared CocotB fixtures
│   ├── run.py                   # Test runner (from EZ-EMFI)
│   ├── volo_bram_loader_tests/
│   ├── volo_clk_divider_tests/
│   ├── volo_lut_pkg_tests/
│   └── volo_voltage_pkg_tests/
├── docs/
│   ├── COCOTB_LESSONS_LEARNED.md
│   └── VHDL_UTILITIES_REFERENCE.md
├── CLAUDE.md                    # Top-level VHDL context
├── README.md
└── pyproject.toml               # CocotB dependencies
```

**Key Decision Points:**
- Should `fsm_observer.vhd` be here (utility) or probe-specific?
- Should `Debug_Top.vhd` be included?
- Test coverage requirements before "done"?

---

### Phase 2: Create `moku-custom-BPD` (New Mono-Repo)

**Purpose:** Probe driver development with composable agentic contexts

```
moku-custom-BPD/
├── .claude/
│   ├── agents/
│   │   ├── probe-design-context/    # NEW: VHDL FSM design
│   │   │   └── agent.md             # FSM patterns, volo utility integration
│   │   ├── deployment-context/      # REUSE: From forge (hardware deployment)
│   │   │   └── agent.md
│   │   ├── hardware-debug-context/  # REUSE: From forge (oscilloscope/FSM debugging)
│   │   │   └── agent.md
│   │   └── workflow-coordinator/    # ADAPT: From forge (orchestrates design → test → deploy)
│   │       └── agent.md
│   ├── commands/
│   │   ├── probe-design.md          # /design-fsm, /test-vhdl, /sim
│   │   ├── deployment.md            # /deploy, /discover (reuse from forge)
│   │   ├── hardware-debug.md        # /debug-fsm (reuse from forge)
│   │   └── workflow.md              # /workflow new-probe, /workflow validate
│   └── shared/
│       ├── volo_platform_ref.md     # Quick ref for volo utilities
│       ├── cocotb_patterns.md       # CocotB testing patterns
│       └── package_contract.md      # Reuse from forge
├── libs/                            # Git submodules (ALL reused!)
│   ├── volo-platform-vhdl/          # NEW: Your extracted VHDL utilities
│   ├── basic-app-datatypes/         # From forge
│   ├── moku-models/                 # From forge
│   └── riscure-models/              # From forge
├── probes/                          # Probe applications
│   ├── DS1120_PD/
│   │   ├── spec/
│   │   │   └── DS1120_PD.yaml       # Generated via /generate (forge)
│   │   ├── generated/               # VHDL shim/main from forge
│   │   │   ├── DS1120_PD_custom_inst_shim.vhd
│   │   │   └── DS1120_PD_custom_inst_main.vhd
│   │   ├── vhdl/
│   │   │   ├── ds1120_pd_fsm.vhd    # Hand-written FSM logic
│   │   │   └── DS1120_PD_volo_main.vhd  # Current implementation
│   │   ├── tests/
│   │   │   └── test_ds1120_pd_progressive.py
│   │   ├── tools/
│   │   │   └── ds1120_tui.py        # Control TUI (future)
│   │   └── CLAUDE.md                # Probe-specific context
│   └── DS1140_PD/
│       ├── spec/
│       │   └── DS1140_PD.yaml
│       ├── generated/
│       ├── vhdl/
│       │   └── DS1140_PD_volo_main.vhd
│       ├── tests/
│       │   └── test_ds1140_pd_progressive.py
│       ├── tools/
│       │   └── ds1140_tui.py        # TUI for DS1140-PD
│       └── CLAUDE.md
├── CLAUDE.md                        # Top-level: choose your context
├── README.md
└── pyproject.toml
```

---

## 🔑 Key Architectural Principles (Learned from Forge)

### 1. **Agent Context Scoping**
Each agent has a clear domain boundary:
- **probe-design-context**: Read/write `probes/*/vhdl/`, read-only `libs/volo-platform-vhdl/`
- **deployment-context**: Read-only `probes/*/generated/`, talks to Moku hardware
- **hardware-debug-context**: Read-only everything, monitors FSM states via oscilloscope
- **workflow-coordinator**: Orchestrates other agents, no direct code writing

**From forge/.claude/agents/forge-context/agent.md:**
```markdown
### ✅ Read & Write Access
- `forge/generator/` - Code generation engine
- `apps/*/*.yaml` - Application specifications

### ✅ Read-Only Access
- `libs/basic-app-datatypes/` - Type system
```

**Apply this pattern to `probe-design-context`**

---

### 2. **Nested CLAUDE.md Strategy**
```
moku-custom-BPD/CLAUDE.md                → "Use /probe-design for FSM work"
├── libs/volo-platform-vhdl/CLAUDE.md    → "VHDL utilities and CocotB tests"
├── libs/moku-models/CLAUDE.md           → "Platform specifications"
└── probes/DS1140_PD/CLAUDE.md           → "DS1140-PD FSM specifics"
```

Each file loads **only the context needed** for that domain.

---

### 3. **Shared Memory Files**
From forge:
```
.claude/shared/
├── package_contract.md           # What forge generates (manifest.json schema)
├── riscure_probe_integration.md  # How to wire up Riscure probes
└── type_system_quick_ref.md      # Quick type lookup table
```

For BPD:
```
.claude/shared/
├── volo_platform_ref.md          # Quick ref for volo utilities
├── cocotb_patterns.md            # CocotB testing best practices
├── package_contract.md           # Reuse from forge
└── fsm_design_patterns.md        # Common FSM patterns for probes
```

---

## 🎬 Migration Execution Plan

### Step 1: Extract VHDL Utilities → `volo-platform-vhdl`
**Time estimate:** 2-3 hours

**Actions:**
1. Create new repo: `mkdir volo-platform-vhdl && cd volo-platform-vhdl && git init`
2. Copy VHDL files from EZ-EMFI:
   ```bash
   # Utilities
   cp EZ-EMFI/VHDL/volo_bram_loader.vhd vhdl/utilities/
   cp EZ-EMFI/VHDL/volo_clk_divider.vhd vhdl/utilities/
   cp EZ-EMFI/VHDL/volo_voltage_threshold_trigger_core.vhd vhdl/utilities/

   # Packages
   cp -r EZ-EMFI/VHDL/packages/ vhdl/

   # Test stubs
   cp EZ-EMFI/VHDL/CustomWrapper_test_stub.vhd vhdl/test_stubs/
   cp EZ-EMFI/VHDL/test_shim_handshake.vhd vhdl/test_stubs/
   ```
3. Copy tests:
   ```bash
   cp -r EZ-EMFI/tests/volo_bram_loader_tests/ tests/
   cp -r EZ-EMFI/tests/volo_clk_divider_tests/ tests/
   cp -r EZ-EMFI/tests/volo_lut_pkg_tests/ tests/
   cp -r EZ-EMFI/tests/volo_voltage_pkg_tests/ tests/
   cp EZ-EMFI/tests/conftest.py tests/
   cp EZ-EMFI/tests/run.py tests/
   ```
4. Write CLAUDE.md (VHDL utilities context)
5. Create pyproject.toml with CocotB dependencies
6. Verify tests pass: `uv run python tests/run.py --all`
7. Commit and push to GitHub

**Deliverable:** `volo-platform-vhdl` repo ready to be used as git submodule

---

### Step 2: Create `moku-custom-BPD` Skeleton
**Time estimate:** 1-2 hours

**Actions:**
1. Create new repo: `mkdir moku-custom-BPD && cd moku-custom-BPD && git init`
2. Add submodules:
   ```bash
   git submodule add https://github.com/sealablab/basic-app-datatypes.git libs/basic-app-datatypes
   git submodule add https://github.com/sealablab/moku-models.git libs/moku-models
   git submodule add https://github.com/sealablab/riscure-models.git libs/riscure-models
   git submodule add https://github.com/YOUR_ORG/volo-platform-vhdl.git libs/volo-platform-vhdl
   ```
3. Copy agent structure from forge:
   ```bash
   cp -r moku-instrument-forge/.claude/agents/deployment-context/ .claude/agents/
   cp -r moku-instrument-forge/.claude/agents/hardware-debug-context/ .claude/agents/
   cp -r moku-instrument-forge/.claude/agents/workflow-coordinator/ .claude/agents/
   ```
4. Create new `probe-design-context/agent.md` (adapt from forge-context)
5. Write top-level CLAUDE.md
6. Create pyproject.toml with workspace config

**Deliverable:** `moku-custom-BPD` skeleton with agent structure

---

### Step 3: Migrate Probe Applications
**Time estimate:** 3-4 hours

**Actions:**
1. Migrate DS1140_PD:
   ```bash
   mkdir -p probes/DS1140_PD
   cp -r EZ-EMFI/generated/DS1140_PD/ probes/DS1140_PD/generated/
   cp EZ-EMFI/VHDL/DS1140_PD_volo_* probes/DS1140_PD/vhdl/
   cp -r EZ-EMFI/tests/ds1140_pd_tests/ probes/DS1140_PD/tests/
   cp -r EZ-EMFI/tools/ probes/DS1140_PD/tools/
   ```
2. Migrate DS1120_PD (if needed)
3. Update import paths in test files
4. Verify tests pass with new structure
5. Write probe-specific CLAUDE.md files

**Deliverable:** Working probe applications in new structure

---

### Step 4: Write Agent Contexts
**Time estimate:** 2-3 hours

**Actions:**
1. Write `probe-design-context/agent.md`:
   - FSM design patterns
   - How to use volo utilities
   - CocotB testing workflow
   - Integration with forge-generated shims
2. Adapt `workflow-coordinator/agent.md` for probe workflow:
   - `/workflow new-probe SPEC.yaml` → forge generate → FSM design → test → deploy
3. Create `.claude/shared/` documentation files
4. Write `/probe-design` command in `.claude/commands/`

**Deliverable:** Complete agent system ready for use

---

## ❓ Questions to Answer Before Starting

### Scope Questions

**Q1: VHDL Utilities Scope**
- ✅ Include: `volo_bram_loader`, `volo_clk_divider`, `volo_voltage_threshold_trigger_core`
- ✅ Include: `volo_common_pkg`, `volo_lut_pkg`, `volo_voltage_pkg`
- ❓ Include `fsm_observer.vhd`? (Generic utility or probe-specific?)
- ❓ Include `Debug_Top.vhd`? (Generic debug infrastructure or project-specific?)
- ❓ Include handshake test infrastructure? (`test_shim_handshake.vhd`, `handshake_tests/`)

**Q2: Probe Migration**
- ❓ Migrate both DS1120_PD and DS1140_PD, or just DS1140_PD?
- ❓ Keep current `DS1140_PD_volo_main.vhd` or start fresh with forge-generated template?
- ❓ Migrate TUI apps (`tools/`) or rebuild from scratch?

**Q3: Testing Strategy**
- ❓ Test coverage threshold before considering `volo-platform-vhdl` "done"? (80%? 100%?)
- ❓ Keep progressive test pattern (P1/P2/P3) or simplify?
- ❓ Keep `test_base.py` and `test_app_register.py` in new structure?

**Q4: Documentation Migration**
- ✅ Migrate `docs/VHDL_COCOTB_LESSONS_LEARNED.md` to `volo-platform-vhdl/docs/`
- ❓ Migrate `docs/OSCILLOSCOPE_DEBUGGING_TECHNIQUES.md` to BPD or forge?
- ❓ Keep `.serena/memories/` structure or integrate into `.claude/shared/`?

**Q5: Naming Conventions**
- ❓ `volo-platform-vhdl` vs `moku-vhdl-utilities` vs `moku-platform-vhdl`?
- ❓ `moku-custom-BPD` (Basic Probe Driver) or different name?
- ❓ `probes/` vs `apps/` directory naming?

---

## 🏆 Success Criteria

### For `volo-platform-vhdl`:
- [ ] All VHDL utilities compile with GHDL --std=08
- [ ] All CocotB tests pass (`uv run python tests/run.py --all`)
- [ ] CLAUDE.md provides clear context for VHDL utilities
- [ ] Can be used as git submodule in other projects
- [ ] README documents each utility with usage examples

### For `moku-custom-BPD`:
- [ ] All 4 agent contexts (probe-design, deployment, hardware-debug, workflow-coordinator) work independently
- [ ] `/workflow new-probe` command orchestrates full pipeline
- [ ] DS1140_PD tests pass in new structure
- [ ] Can deploy to Moku hardware via `/deploy`
- [ ] Nested CLAUDE.md files load appropriate contexts

---

## 💡 Key Insights from Forge

### What Worked Well:
1. **Agent boundaries** (556-820 lines per agent.md) provide comprehensive context without overload
2. **Shared memory files** (`.claude/shared/`) avoid duplication across agents
3. **Submodules for libraries** enable clean versioning and reuse
4. **Test-first approach** (69 tests before docs) ensured quality

### Apply to BPD:
1. Keep agent.md files comprehensive (500-800 lines)
2. Use `.claude/shared/` for FSM patterns, volo utility docs
3. Version `volo-platform-vhdl` independently
4. Ensure CocotB tests pass before considering migration complete

---

## 📚 Reference Files

### From EZ-EMFI (Current State):
- **VHDL Utilities:** `/Users/johnycsh/EZ-EMFI/VHDL/` (16 files)
- **Tests:** `/Users/johnycsh/EZ-EMFI/tests/` (28 files + subdirs)
- **Documentation:** `/Users/johnycsh/EZ-EMFI/docs/`
- **Current CLAUDE.md:** `/Users/johnycsh/EZ-EMFI/CLAUDE.md`

### From moku-instrument-forge (Reference):
- **Agent Structure:** `/Users/johnycsh/moku-instrument-forge/.claude/agents/` (5 agents)
- **Submodule Pattern:** `/Users/johnycsh/moku-instrument-forge/libs/` (3 submodules)
- **forge-context Agent:** `/Users/johnycsh/moku-instrument-forge/.claude/agents/forge-context/agent.md` (753 lines)
- **README:** `/Users/johnycsh/moku-instrument-forge/README.md` (546 lines)

---

## 🚀 Next Steps When You Return

1. **Answer scope questions above** (5-10 minutes discussion)
2. **Execute Step 1**: Extract `volo-platform-vhdl` (2-3 hours)
3. **Execute Step 2**: Create `moku-custom-BPD` skeleton (1-2 hours)
4. **Execute Step 3**: Migrate probe applications (3-4 hours)
5. **Execute Step 4**: Write agent contexts (2-3 hours)

**Total estimated time:** 8-12 hours

---

## 🎯 Why This Approach Wins

### Composability
- `volo-platform-vhdl` can be used in **any** future Moku VHDL project
- Agent contexts are portable across repos
- Each library (basic-app-datatypes, moku-models, volo-platform-vhdl) versions independently

### Context Scoping
- `/probe-design` → Only loads VHDL FSM context
- `/deployment` → Only loads hardware deployment context
- No more mixing Python tooling with VHDL design context

### Leverage Forge Investment
- Reuse 3 of 5 agents (deployment, hardware-debug, workflow-coordinator)
- Proven `.claude/` structure
- Established patterns for agent.md files (scope boundaries, success criteria)

### Clean Git History
- Each submodule tracks changes independently
- Easy to see when volo utilities change vs probe FSMs
- Clear commit history for future debugging

---

**Status:** Ready to execute upon return. Answer questions above, then start with Step 1.

**Contact:** Created by Claude Code on 2025-11-03 during planning session.
