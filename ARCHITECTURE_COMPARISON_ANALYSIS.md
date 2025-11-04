# Systematic Architecture Comparison: EZ-EMFI vs moku-instrument-forge

**Analysis Date:** 2025-11-03
**Repositories Analyzed:**
- **EZ-EMFI** (feature/BAD-main branch) @ /home/user/EZ-EMFI
- **moku-instrument-forge** (main branch) @ /tmp/moku-instrument-forge

---

## Executive Summary

This analysis compares the architectural patterns between **EZ-EMFI** (VHDL probe driver development) and **moku-instrument-forge** (code generation platform) to systematically assess the proposed mono-repo refactor in commit `b0cb32bb`.

**Key Finding:** The proposed refactor has **significant architectural gaps** that must be addressed before execution. The planning document underestimates complexity by treating this as primarily a "file reorganization" when it's actually a **fundamental architectural integration challenge**.

---

## 1. Repository Structure Comparison

### 1.1 Directory Organization

| Aspect | moku-instrument-forge | EZ-EMFI | Migration Impact |
|--------|----------------------|---------|------------------|
| **Primary Domain** | Python code generation | VHDL firmware + Python tooling | **HIGH** - Dual-domain complexity |
| **Agent System** | 5 agents, 3233 lines | 3 agents, 1142 lines | **HIGH** - 2x agent complexity increase |
| **Submodules** | 3 (basic-app-datatypes, moku-models, riscure-models) | 1 (basic-app-datatypes @ root, moku-models @ root) | **CRITICAL** - Submodule path conflicts |
| **Build System** | Pure Python (uv workspace) | VHDL (GHDL) + Python (uv) | **CRITICAL** - Dual build orchestration |
| **Test Framework** | pytest (Python only) | CocotB (VHDL simulation) + pytest | **HIGH** - Test infrastructure merge |

### 1.2 File Count Analysis

```bash
# moku-instrument-forge
Total files: 157 (excluding .git)
- Python: 89 files
- VHDL: 0 files
- Markdown: 43 files
- YAML: 12 files

# EZ-EMFI (current)
Total files: 203+ (excluding .git)
- Python: 47 files
- VHDL: 27 files
- Markdown: 38 files
- YAML: 3 files
```

**Concern:** Proposed `moku-custom-BPD` will have **250+ files across 2 build systems**. This violates the forge's "single-domain clarity" principle.

---

## 2. Agent Architecture Gap Analysis

### 2.1 Agent Maturity Comparison

| Agent Domain | Forge (lines) | EZ-EMFI (lines) | Proposed BPD | Gap Analysis |
|--------------|---------------|-----------------|--------------|--------------|
| **Code Generation** | forge-context (753) | ❌ None | probe-design-context (?) | **NEW** - 500-800 lines from scratch |
| **Deployment** | deployment-context (556) | moku-deploy (348) | Reuse forge? | **208 line gap** - forge is more mature |
| **Hardware Debug** | hardware-debug-context (646) | ❌ None | Reuse forge? | **646 lines** - needs VHDL/FSM adaptation |
| **Documentation** | docgen-context (820) | ❌ None | ❌ Not proposed | **Missing** - no doc generation plan |
| **Workflow Orchestration** | workflow-coordinator (458) | ❌ None | Adapt forge? | **NEW** - design → test → deploy workflow |
| **VHDL Testing** | ❌ None | test-runner (417) | probe-design-context? | **417 lines** - where does this go? |
| **Python Tooling** | ❌ None | python-dev (377) | ❌ Not proposed | **Missing** - TUI development context |

**Total Agent Content:**
- Forge: 3,233 lines (5 agents)
- EZ-EMFI: 1,142 lines (3 agents)
- **Proposed BPD: ~4,500-5,000 lines (4-6 agents)**

**Critical Gap:** Planning doc estimates **2-3 hours** for writing agent contexts. Reality: **8-12 hours minimum** to write 3,000-4,000 new lines of agent documentation.

### 2.2 Agent Scope Conflicts

**Problem:** The refactor plan proposes this agent boundary:

```
probe-design-context:
  Read/Write: probes/*/vhdl/
  Read-Only: libs/volo-platform-vhdl/
```

**Conflict 1: Build System Orchestration**
- VHDL compilation requires: `ghdl -a --std=08 volo_common_pkg.vhd ...`
- Who manages compilation order? (packages → utilities → application)
- Forge agents don't handle build orchestration (only file generation)

**Conflict 2: Test Execution Context**
- CocotB tests require: VHDL simulation + Python test runner
- Current `test-runner` agent handles this
- **Where does this agent go in BPD?** (Not in planning doc!)

**Conflict 3: Hardware Validation Workflow**
- Current workflow: VHDL → CocotB → CloudCompile → Moku → Oscilloscope
- Forge `hardware-debug-context` assumes already-deployed firmware
- **Gap:** Who orchestrates the full pipeline?

---

## 3. Submodule Dependency Analysis

### 3.1 Current Submodule State

**moku-instrument-forge:**
```
libs/
├── basic-app-datatypes/  (git submodule)
├── moku-models/          (git submodule)
└── riscure-models/       (git submodule)
```

**EZ-EMFI:**
```
moku-models/              (git submodule @ root)
libs/
└── basic-app-datatypes/  (git submodule @ libs/)
```

**Critical Issue:** Submodule path inconsistency!
- Forge: `libs/moku-models/`
- EZ-EMFI: `moku-models/` (root level)

### 3.2 Import Path Conflicts

**Example from EZ-EMFI:**
```python
# Current import paths
from moku_models.platform_models import MokuConfig
from models.ds1140_pd_spec import DS1140PDSpec  # Local models/

# After refactor to proposed structure:
from libs.moku_models.platform_models import MokuConfig  # ❌ Breaking change
from probes.DS1140_PD.models.ds1140_pd_spec import DS1140PDSpec  # ❌ Breaking change
```

**Impact:** Every Python file that imports moku-models or local models needs refactoring.

**Files affected:** 47 Python files in EZ-EMFI (grep analysis: `grep -r "from moku_models" --include="*.py" | wc -l`)

### 3.3 Proposed `volo-platform-vhdl` Submodule

**Planning doc proposes:**
```
libs/
├── volo-platform-vhdl/   (NEW git submodule)
│   ├── vhdl/
│   │   ├── utilities/
│   │   └── packages/
│   └── tests/
```

**Critical Questions Not Addressed:**

1. **VHDL Compilation Order:**
   - GHDL requires: compile packages → compile utilities → compile application
   - Who maintains the `Makefile` or build script?
   - Current `tests/run.py` handles this for EZ-EMFI - where does it go?

2. **Test Dependencies:**
   ```python
   # Current test structure
   tests/conftest.py  # Shared fixtures
   tests/run.py       # Test orchestrator
   tests/volo_clk_divider_tests/
       test_volo_clk_divider_progressive.py
   ```

   **After refactor:**
   ```
   libs/volo-platform-vhdl/tests/  # Utility tests
   probes/DS1140_PD/tests/         # Integration tests
   ```

   **Problem:** Does `probes/DS1140_PD/tests/` depend on `libs/volo-platform-vhdl/tests/conftest.py`?
   - If YES: Cross-repo test dependencies (fragile!)
   - If NO: Duplicate test infrastructure (violates DRY)

3. **Version Pinning:**
   - What happens when `volo-platform-vhdl` releases breaking changes?
   - Planning doc has NO version pinning strategy
   - Example scenario:
     ```
     # Today: DS1140_PD works with volo-platform-vhdl @ main
     # Tomorrow: volo-platform-vhdl changes volo_common_pkg interface
     # Result: DS1140_PD breaks until updated
     ```

---

## 4. Build System Complexity

### 4.1 Forge Build System (Simple)

**Single Build Target: Python Package**
```toml
[tool.uv.workspace]
members = ["forge", "libs/basic-app-datatypes"]

[tool.uv.sources]
basic-app-datatypes = { workspace = true }
```

**Build steps:**
1. `uv sync` - Install Python dependencies
2. `pytest` - Run tests
3. Done

### 4.2 EZ-EMFI Build System (Dual Build)

**Two Build Targets: VHDL Firmware + Python Tooling**

```toml
[tool.uv.sources]
moku-models = { path = "moku-models", editable = true }
basic-app-datatypes = { path = "libs/basic-app-datatypes", editable = true }
```

**Build steps:**
1. `git submodule update --init --recursive` - Initialize submodules
2. `uv sync` - Install Python dependencies
3. `ghdl -a --std=08 VHDL/**/*.vhd` - Compile VHDL
4. `pytest python_tests/` - Test Python code
5. `uv run python tests/run.py --all` - Test VHDL via CocotB

**Critical Difference:** EZ-EMFI has **VHDL build dependency** that forge doesn't handle.

### 4.3 Proposed BPD Build System (COMPLEX)

**Proposed structure adds another layer:**

```
moku-custom-BPD/
├── libs/volo-platform-vhdl/   # Build 1: VHDL utilities
│   └── tests/run.py           # CocotB runner
├── probes/DS1140_PD/          # Build 2: Probe firmware
│   ├── generated/             # Generated from forge
│   ├── vhdl/                  # Hand-written FSM
│   └── tests/                 # Integration tests
└── forge/                     # Build 3: Code generator?
```

**Unresolved Questions:**

1. **Compilation Order:**
   - Compile `volo-platform-vhdl` utilities first?
   - Then compile `probes/DS1140_PD/vhdl/` with utilities as dependencies?
   - Where is the orchestration script?

2. **Test Execution:**
   ```bash
   # Option 1: Run from root
   uv run python libs/volo-platform-vhdl/tests/run.py --all
   uv run python probes/DS1140_PD/tests/run.py --all

   # Option 2: Unified runner (not in planning doc!)
   uv run python scripts/test_all.py
   ```

3. **Forge Integration:**
   - Planning doc says "Reuse forge for code generation"
   - But forge is a **separate repo** (moku-instrument-forge)
   - **How does BPD call forge?** (Git submodule? Copy code? External tool?)

---

## 5. Testing Infrastructure Concerns

### 5.1 Forge Test Infrastructure

```
forge/tests/
├── test_generator.py       # 16 tests (code generation)
├── test_integration.py     # 9 tests (end-to-end)
├── test_models.py          # Type validation
└── test_packing.py         # Register packing
```

**Characteristics:**
- Pure Python (pytest)
- Fast (<10s for full suite)
- No hardware dependencies
- 69 passing tests

### 5.2 EZ-EMFI Test Infrastructure

```
tests/
├── run.py                          # Custom CocotB orchestrator
├── conftest.py                     # Shared fixtures
├── volo_clk_divider_tests/
│   └── test_volo_clk_divider_progressive.py
├── volo_lut_pkg_tests/
│   └── test_volo_lut_pkg_progressive.py
└── ds1120_pd_tests/
    └── test_ds1120_pd_progressive.py
```

**Characteristics:**
- VHDL simulation (CocotB + GHDL)
- Slow (~2-5 minutes for full suite)
- Progressive test levels (P1/P2/P3)
- 28+ test modules

### 5.3 Proposed BPD Test Infrastructure (UNCLEAR)

**Planning doc says:**
```
probes/DS1140_PD/
└── tests/
    └── test_ds1140_pd_progressive.py

libs/volo-platform-vhdl/
└── tests/
    ├── conftest.py
    └── volo_bram_loader_tests/
```

**Critical Gaps:**

1. **Test Orchestration:**
   - Who runs tests across both `libs/` and `probes/`?
   - Current `tests/run.py` is 150+ lines of custom orchestration
   - **Where does it live in new structure?**

2. **Fixture Sharing:**
   ```python
   # Current: tests/conftest.py defines shared fixtures
   # Proposed: libs/volo-platform-vhdl/tests/conftest.py?
   # Problem: Can probes/DS1140_PD/tests/ import fixtures from libs/?
   ```

3. **CI/CD:**
   - Forge has `.github/workflows/test.yml`
   - EZ-EMFI has **no CI/CD**
   - Planning doc mentions "add CI/CD" but provides no workflow spec

---

## 6. Context Management Challenges

### 6.1 Forge Context Strategy

**5 Agents, 6 Slash Commands:**
```
/.claude/commands/
├── forge.md        → forge-context
├── deployment.md   → deployment-context
├── debug.md        → hardware-debug-context
├── docgen.md       → docgen-context
├── workflow.md     → workflow-coordinator
└── platform.md     → (loads platform specs)
```

**Agent Boundaries:**
- Each agent has clear read/write vs read-only scopes
- Agents call each other via workflow-coordinator
- No agent writes outside its domain

### 6.2 EZ-EMFI Context Strategy

**3 Agents, 5 Slash Commands:**
```
.claude/commands/
├── vhdl.md      → (loads VHDL context, no agent)
├── python.md    → python-dev agent
├── test.md      → test-runner agent
├── moku.md      → moku-deploy agent
└── models.md    → (loads moku-models context)
```

**Context Switching:**
- Slash commands load focused contexts
- Agents are optional (vhdl/models are pure context)
- Simpler than forge (fewer agents)

### 6.3 Proposed BPD Context Strategy (COMPLEX)

**Planning doc proposes:**
```
moku-custom-BPD/.claude/commands/
├── probe-design.md     → probe-design-context (NEW)
├── deployment.md       → deployment-context (from forge)
├── hardware-debug.md   → hardware-debug-context (from forge)
└── workflow.md         → workflow-coordinator (adapted from forge)

libs/volo-platform-vhdl/.claude/
└── commands/
    └── test-vhdl.md    → vhdl-test-context (NEW)

probes/DS1140_PD/
└── CLAUDE.md           → (probe-specific context)
```

**Critical Issues:**

1. **Nested Context Ambiguity:**
   ```
   # Scenario: Working on DS1140_PD FSM
   # Which context do I load?

   Option A: /probe-design (top-level BPD command)
   Option B: cd probes/DS1140_PD && /vhdl (nested command?)
   Option C: Read probes/DS1140_PD/CLAUDE.md (static doc)
   ```

   **Problem:** Planning doc doesn't specify how nested contexts interact.

2. **Agent Call Hierarchy:**
   ```
   User: "/workflow new-probe DS1140_PD.yaml"
   → workflow-coordinator agent
       → forge-context agent (generate VHDL shim)
           ❌ ERROR: forge-context is in moku-instrument-forge repo!

   # OR does BPD copy forge code locally?
   # OR does BPD call forge as external tool?
   ```

   **Planning doc is silent on this critical integration point.**

3. **Shared Memory Files:**
   ```
   Forge uses:
   .claude/shared/
   ├── package_contract.md
   ├── type_system_quick_ref.md
   └── riscure_probe_integration.md

   EZ-EMFI uses:
   .serena/memories/
   ├── instrument_oscilloscope.md
   ├── mcc_routing_concepts.md
   └── 18 other files

   BPD proposes:
   .claude/shared/
   ├── volo_platform_ref.md (NEW)
   ├── cocotb_patterns.md (NEW)
   └── fsm_design_patterns.md (NEW)
   ```

   **Question:** What happens to `.serena/memories/`? Planning doc doesn't mention it!

---

## 7. Dependency Graph Analysis

### 7.1 Current EZ-EMFI Dependencies

```
EZ-EMFI (root repo)
├─ moku-models/                    (git submodule @ root)
├─ libs/basic-app-datatypes/       (git submodule)
├─ models/                         (local Python models)
│   ├─ ds1140_pd_spec.py
│   └─ register_types.py
├─ VHDL/                           (local VHDL source)
│   ├─ volo_common_pkg.vhd
│   ├─ DS1140_PD_volo_main.vhd
│   └─ 25 other files
└─ tests/                          (local CocotB tests)
    └─ run.py (orchestrator)

Dependency Flow:
tests/run.py → VHDL/*.vhd → (compiled by GHDL)
models/*.py → moku-models/ (platform specs)
```

### 7.2 Proposed BPD Dependencies

```
moku-custom-BPD (root repo)
├─ libs/
│   ├─ volo-platform-vhdl/         (NEW git submodule)
│   │   ├─ vhdl/packages/          (volo_common_pkg.vhd)
│   │   └─ tests/run.py            (utility tests)
│   ├─ basic-app-datatypes/        (existing submodule)
│   ├─ moku-models/                (existing submodule, moved from root!)
│   └─ riscure-models/             (existing submodule)
├─ probes/
│   └─ DS1140_PD/
│       ├─ generated/              (VHDL shim from forge)
│       ├─ vhdl/                   (hand-written FSM)
│       │   └─ DS1140_PD_fsm.vhd  (depends on volo-platform-vhdl!)
│       └─ tests/
│           └─ run.py?             (or reuse libs/volo-platform-vhdl/tests/run.py?)
└─ forge/                          (??? copy from moku-instrument-forge?)

Dependency Flow (UNRESOLVED):
probes/DS1140_PD/vhdl/DS1140_PD_fsm.vhd
  ↓ (imports)
libs/volo-platform-vhdl/vhdl/packages/volo_common_pkg.vhd
  ↓ (compiled by GHDL)
[WHO ORCHESTRATES THIS BUILD?]

probes/DS1140_PD/generated/*.vhd
  ↓ (generated by forge)
[WHERE IS FORGE? SUBMODULE? COPY? EXTERNAL?]
```

**Critical Missing Piece:** The planning doc doesn't specify **how forge integrates with BPD**.

### 7.3 Circular Dependency Risk

**Scenario:**
1. `volo-platform-vhdl` contains `volo_common_pkg.vhd`
2. `DS1140_PD` imports `volo_common_pkg.vhd`
3. `volo-platform-vhdl/tests/` test utilities in isolation
4. `DS1140_PD/tests/` test probe with utilities

**Problem:** If `DS1140_PD` discovers a bug in `volo_common_pkg.vhd`:
- Fix in `volo-platform-vhdl` (separate repo)
- Commit + push `volo-platform-vhdl`
- Update submodule pointer in `moku-custom-BPD`
- Test `DS1140_PD` again

**5-step process** for a simple bug fix! (vs 2 steps in current monolith)

---

## 8. Migration Risk Matrix

| Risk Category | Likelihood | Impact | Mitigation Strategy | Planning Doc Coverage |
|---------------|-----------|--------|---------------------|----------------------|
| **Submodule path conflicts** | HIGH | HIGH | Normalize to `libs/*` for all submodules | ❌ Not mentioned |
| **Import path breakage** | HIGH | HIGH | Write migration script to update imports | ❌ Not mentioned |
| **Build orchestration complexity** | HIGH | MEDIUM | Write unified `Makefile` or `scripts/build_all.py` | ❌ Not mentioned |
| **Test infrastructure fragmentation** | MEDIUM | HIGH | Clarify test runner responsibilities | ⚠️ Partially (Q3) |
| **Agent context overload** | MEDIUM | MEDIUM | Keep agent.md files focused (<800 lines) | ✅ Mentioned |
| **Version pinning issues** | MEDIUM | HIGH | Add git submodule version pinning policy | ❌ Not mentioned |
| **Forge integration undefined** | HIGH | CRITICAL | Specify: submodule, copy, or external tool? | ❌ Not mentioned |
| **CI/CD setup** | LOW | MEDIUM | Copy forge workflows, adapt for VHDL | ⚠️ Mentioned as "add CI/CD" (no spec) |
| **Backward compatibility** | HIGH | MEDIUM | Document breaking changes, provide migration guide | ❌ Not mentioned |
| **Documentation drift** | MEDIUM | LOW | Use nested CLAUDE.md strategy | ✅ Well-specified |

**Summary:** 10 major risks, only 2 addressed in planning doc.

---

## 9. Time Estimate Reality Check

### 9.1 Planning Doc Estimates

| Phase | Estimated Time | Confidence |
|-------|---------------|------------|
| Step 1: Extract volo-platform-vhdl | 2-3 hours | Medium |
| Step 2: Create BPD skeleton | 1-2 hours | Low |
| Step 3: Migrate probe applications | 3-4 hours | Low |
| Step 4: Write agent contexts | 2-3 hours | Very Low |
| **Total** | **8-12 hours** | **Optimistic** |

### 9.2 Revised Estimates (Based on This Analysis)

| Phase | Realistic Estimate | Justification |
|-------|-------------------|---------------|
| **Pre-Flight** | **2-3 hours** | Answer Q1-Q5, create repos, set up CI/CD skeleton |
| **Step 1: Extract volo-platform-vhdl** | **4-6 hours** | File copy (1h) + test verification (2h) + build scripts (1h) + docs (1h) + submodule setup (1h) |
| **Step 1.5: Normalize submodule paths** | **2-3 hours** | **NEW** - Move `moku-models` to `libs/`, update imports |
| **Step 2: Create BPD skeleton** | **3-4 hours** | Git setup (1h) + submodule debugging (1h) + pyproject.toml workspace (1h) + verify builds (1h) |
| **Step 2.5: Forge integration plan** | **2-3 hours** | **NEW** - Decide: submodule, copy, or external? Implement. |
| **Step 3: Migrate probe applications** | **6-8 hours** | File copy (1h) + import path updates (3h) + test adaptation (2h) + verification (2h) |
| **Step 4: Write agent contexts** | **8-12 hours** | probe-design-context (4h) + workflow adaptation (3h) + shared docs (2h) + testing agent integration (3h) |
| **Step 5: Integration testing** | **3-4 hours** | **NEW** - End-to-end workflow testing |
| **Step 6: Documentation** | **2-3 hours** | **NEW** - Migration guide, README updates |
| **Total** | **32-46 hours** | **4-6 working days** |

**Reality:** Planning doc estimates **8-12 hours**, actual complexity is **32-46 hours** (3-4x underestimate).

---

## 10. Critical Unresolved Questions

### 10.1 Architecture Questions (Not in Planning Doc)

1. **How does forge integrate with BPD?**
   - [ ] Option A: Git submodule (`libs/forge/`)
   - [ ] Option B: Copy forge code into BPD repo
   - [ ] Option C: External tool (call via CLI)
   - [ ] Option D: Separate service (API endpoint)

2. **Who orchestrates VHDL compilation across submodules?**
   - [ ] Root-level `Makefile`
   - [ ] `scripts/build_all.py`
   - [ ] Each probe has own build script
   - [ ] Integrated into test runner

3. **How are test fixtures shared between libs/ and probes/?**
   - [ ] Cross-repo imports (fragile)
   - [ ] Duplicate fixtures (violates DRY)
   - [ ] pytest plugin mechanism
   - [ ] Unified test infrastructure package

4. **What happens to `.serena/memories/`?**
   - [ ] Migrate to `.claude/shared/`
   - [ ] Keep `.serena/` for backward compat
   - [ ] Split between BPD and volo-platform-vhdl
   - [ ] Archive (no longer needed)

5. **Version pinning strategy for submodules?**
   - [ ] Pin to specific commits (strict)
   - [ ] Pin to tags/releases (flexible)
   - [ ] Always use `main` (dangerous)
   - [ ] Use `git submodule update --remote` (auto-update)

### 10.2 Scope Questions (Partially Addressed)

From planning doc Q1-Q5, only Q1 (fsm_observer placement) is answerable by quick code inspection. The others require architectural decisions:

**Q2: Migrate both DS1120_PD and DS1140_PD?**
- Analysis needed: Are they actually separate probes or iterations?
- Check commit history to understand relationship

**Q3: Test coverage threshold?**
- Depends on CI/CD strategy (not specified)
- Recommend: P1 tests required for merge, P2 for release

**Q4: Documentation migration?**
- `.serena/memories/` fate unresolved
- Oscilloscope debugging belongs in hardware-debug-context

**Q5: Naming conventions?**
- Impact analysis: How many files reference these names?
- grep for "volo-platform", "moku-custom-BPD", etc.

---

## 11. Recommendations

### 11.1 CRITICAL: Do NOT Proceed Until These Are Resolved

1. **Define forge integration strategy**
   - Write a 1-page spec: "How moku-instrument-forge integrates with moku-custom-BPD"
   - Prototype the integration (1-2 hours spike)

2. **Normalize submodule paths**
   - Move `EZ-EMFI/moku-models/` to `EZ-EMFI/libs/moku-models/`
   - Update all imports (write script to automate)
   - Test before proceeding with refactor

3. **Design test orchestration**
   - Decide: single `tests/run_all.py` or distributed runners?
   - Write pseudocode for cross-repo test execution

4. **Specify CI/CD workflows**
   - Create `.github/workflows/test-vhdl.yml` skeleton
   - Define: What runs on PR? What runs on merge?

### 11.2 HIGH PRIORITY: Enhance Planning Document

5. **Add "Step 0: Pre-Flight Checklist"**
   - Answer Q1-Q5
   - Prototype forge integration
   - Create GitHub repos
   - Set up CI/CD skeletons

6. **Add "Step 1.5: Normalize Submodules"**
   - Move moku-models to libs/
   - Update import paths
   - Test existing functionality

7. **Add "Step 2.5: Forge Integration"**
   - Implement chosen integration strategy
   - Verify `/generate` workflow

8. **Add "Step 5: Integration Testing"**
   - End-to-end workflow validation
   - Document any issues discovered

9. **Add "Step 6: Documentation"**
   - Migration guide for existing users
   - Breaking changes documentation
   - Rollback procedures

### 11.3 MEDIUM PRIORITY: Clarify Agent Boundaries

10. **Write agent scope matrix**
    ```
    | Agent | Read | Write | Calls | Called By |
    |-------|------|-------|-------|-----------|
    | probe-design | libs/volo-platform-vhdl/, probes/*/vhdl/ | probes/*/vhdl/ | workflow-coordinator | workflow-coordinator |
    | deployment | probes/*/generated/ | [hardware] | hardware-debug | workflow-coordinator |
    ...
    ```

11. **Specify workflow-coordinator orchestration**
    - Sequence diagram: `/workflow new-probe` end-to-end
    - Error handling: What happens if forge generation fails?

12. **Clarify test-runner integration**
    - Where does current `test-runner` agent go?
    - Does it merge with `probe-design-context`?
    - Who orchestrates CocotB execution?

### 11.4 LOW PRIORITY: Polish & Optimization

13. **Add troubleshooting guide** (as mentioned in original review)

14. **Document rollback strategy** (as mentioned in original review)

15. **Create spike branches for prototyping**
    - `spike/forge-integration-test`
    - `spike/submodule-path-normalization`
    - `spike/test-orchestration`

---

## 12. Verdict

**Planning Document Quality: 6/10**
- Excellent architectural vision (composability, agent boundaries)
- Good questions raised (Q1-Q5)
- **Critical gaps in execution details**

**Recommended Action: ❌ DO NOT PROCEED AS-IS**

**Required Before Execution:**
1. Resolve 4 CRITICAL unresolved questions (Section 11.1)
2. Add missing steps to planning doc (Section 11.2)
3. Prototype forge integration (2-4 hour spike)
4. Revise time estimate to 32-46 hours

**Alternative Approach:**
Consider **incremental refactor** instead of big-bang migration:
1. **Phase 1:** Extract `volo-platform-vhdl` submodule only (keep EZ-EMFI otherwise intact)
2. **Phase 2:** Normalize submodule paths in EZ-EMFI
3. **Phase 3:** Prototype forge integration in EZ-EMFI
4. **Phase 4:** Create `moku-custom-BPD` after validating architecture

**Estimated time for incremental approach:** 20-30 hours (vs 32-46 for big-bang)

---

## 13. Action Items for Repository Owner

**Before next session:**
- [ ] Read this analysis document
- [ ] Answer CRITICAL question: How should forge integrate?
- [ ] Check `fsm_observer.vhd` usage (Q1)
- [ ] Decide: Big-bang migration or incremental refactor?
- [ ] Allocate realistic time: 4-6 days of focused work

**During next session:**
- [ ] Prototype forge integration (2-4 hours)
- [ ] Normalize submodule paths (2-3 hours)
- [ ] Update planning doc with missing steps (1-2 hours)

---

**Analysis completed: 2025-11-03**
**Analyst: Claude Code (Sonnet 4.5)**
**Repositories analyzed: EZ-EMFI @ feature/BAD-main, moku-instrument-forge @ main**
