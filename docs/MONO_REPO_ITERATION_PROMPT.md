# Mono-Repo Design Iteration Prompt

**Status:** Ready for pickup on dev laptop
**Created:** 2025-11-03
**Context:** Architecture analysis complete, ready for design iteration

---

## 🎯 Purpose

This document guides the iterative design of the **moku-custom-BPD mono-repo architecture**. Use this when picking up work to refine the mono-repo strategy through spike branches.

**Expected iterations:** 2-3 design cycles before final architecture
**Test approach:** Spike branches to validate architectural decisions

---

## 📋 Quick Context Summary

### Current State

**EZ-EMFI** (existing project):
- Dual-domain: VHDL probe drivers + Python tooling
- 27 VHDL files, 47 Python files
- 3 agents (1,142 lines): test-runner, python-dev, moku-deploy
- 1 submodule at root: `moku-models/`, 1 in `libs/`: `basic-app-datatypes/`
- CocotB test infrastructure with custom runner (`tests/run.py`)

**moku-instrument-forge** (reference architecture):
- Pure Python code generation platform
- 5 agents (3,233 lines): forge-context, deployment-context, docgen-context, hardware-debug-context, workflow-coordinator
- 3 submodules in `libs/`: basic-app-datatypes, moku-models, riscure-models
- Single llms.txt entry point (319 lines), NO nested CLAUDE.md
- Package contract: manifest.json as source of truth

**Planning Document** (commit b0cb32bb):
- Proposes extracting VHDL utilities → `volo-platform-vhdl` submodule
- Proposes creating `moku-custom-BPD` mono-repo with 4 agents
- **Identified gaps:** 7 critical architectural questions unanswered
- **Time underestimate:** 8-12h planned, 32-46h realistic

### Analysis Documents Available

**For full context, load these files:**

1. **`ARCHITECTURE_COMPARISON_ANALYSIS.md`** (7,600 words)
   - Section 2: Agent architecture gaps
   - Section 3: Submodule path conflicts
   - Section 5: Testing infrastructure concerns
   - Section 10: Critical unresolved questions
   - Section 11: Recommendations

2. **`FORGE_ARCHITECTURE_ANALYSIS.md`** (6,800 words)
   - Section 2: Agent system architecture (boundaries, scopes)
   - Section 3: llms.txt documentation strategy
   - Section 4: Git submodule patterns
   - Section 10: Key takeaways for BPD migration
   - Section 12: Adopt/Adapt/Extend recommendations

3. **`monorepo-refactor-pickup-here.md`** (original planning doc)
   - Section "Proposed Architecture" (Phase 1 & 2)
   - Section "Migration Execution Plan" (Steps 1-4)
   - Section "Questions to Answer" (Q1-Q5)

**Quick command to load context:**
```bash
# Read analysis summaries
head -100 ARCHITECTURE_COMPARISON_ANALYSIS.md
head -100 FORGE_ARCHITECTURE_ANALYSIS.md

# Jump to specific sections as needed
# (Use search or line numbers from file)
```

---

## 🔑 Four Critical Architectural Decisions

These decisions determine the mono-repo structure. Each needs validation via spike branch.

### Decision 1: Forge Integration Strategy

**Question:** How does moku-custom-BPD integrate with moku-instrument-forge?

**Options:**

| Option | Approach | Pros | Cons | Validation Method |
|--------|----------|------|------|-------------------|
| **A: Git Submodule** | `libs/forge/` | Version control, upstream updates | Coupling, submodule complexity | Create `spike/forge-as-submodule` |
| **B: Copy Code** | Fork forge into BPD repo | Full control, customize freely | Divergence, manual sync | Create `spike/forge-as-copy` |
| **C: External Tool** | Call forge via CLI/API | Clean separation, no coupling | Requires forge deployment, API stability | Create `spike/forge-as-external` |

**Decision Criteria:**
- Can we generate VHDL shims for probes? (Validation: Run `/generate` on DS1140_PD.yaml)
- Can we modify forge behavior? (Validation: Customize VHDL template)
- Is versioning manageable? (Validation: Update forge version, test impact)

**Recommendation to test first:** Option B (Copy Code)
- Most control during early development
- Can merge upstream changes selectively
- Easier to customize for VHDL-specific needs

### Decision 2: VHDL Build Orchestration

**Question:** How is VHDL compiled across submodules and probe applications?

**Options:**

| Option | Approach | Pros | Cons | Validation Method |
|--------|----------|------|------|-------------------|
| **A: Root Makefile** | `Makefile` at repo root | Standard, familiar, parallelizable | Platform-specific (Make syntax) | Create `spike/makefile-build` |
| **B: Python Build Script** | `scripts/build_all.py` | Cross-platform, flexible | Reinventing Make, slower | Create `spike/python-build` |
| **C: Integrated Test Runner** | Extend `tests/run.py` | Unified test+build, existing pattern | Mixing concerns, less modular | Create `spike/test-runner-build` |

**Decision Criteria:**
- Can we compile `libs/volo-platform-vhdl/` utilities? (Validation: `ghdl -a volo_common_pkg.vhd`)
- Can we compile `probes/DS1140_PD/` with utilities as deps? (Validation: `ghdl -a DS1140_PD_volo_main.vhd`)
- Can we run CocotB tests? (Validation: `pytest probes/DS1140_PD/tests/`)
- Does it work on CI/CD? (Validation: `.github/workflows/test.yml`)

**Recommendation to test first:** Option C (Integrated Test Runner)
- Leverages existing `tests/run.py` (150+ lines already written)
- Unified workflow (developers only run one command)
- Can evolve into separate build tool if needed

### Decision 3: CocotB Test Infrastructure

**Question:** Where does CocotB test infrastructure live and how is it shared?

**Options:**

| Option | Approach | Pros | Cons | Validation Method |
|--------|----------|------|------|-------------------|
| **A: Centralized Runner** | Root `tests/run_all.py` | Single test command, shared fixtures | Tight coupling, harder to test libs independently | Create `spike/centralized-tests` |
| **B: Distributed Runners** | Each submodule/probe has own runner | Modular, test libs independently | Fixture duplication, complex orchestration | Create `spike/distributed-tests` |
| **C: Pytest Plugin** | Custom pytest plugin for CocotB | Standard pytest commands, IDE integration | Development overhead, learning curve | Create `spike/pytest-plugin` |

**Decision Criteria:**
- Can we test `libs/volo-platform-vhdl/` utilities in isolation? (Validation: `pytest libs/volo-platform-vhdl/tests/`)
- Can we test `probes/DS1140_PD/` with utility dependencies? (Validation: `pytest probes/DS1140_PD/tests/`)
- Can we share fixtures across tests? (Validation: `conftest.py` structure)
- Does it work with progressive tests (P1/P2/P3)? (Validation: `TEST_LEVEL=P2_INTERMEDIATE pytest`)

**Recommendation to test first:** Option A (Centralized Runner)
- Matches current EZ-EMFI pattern
- Simpler for developers (one command to run all tests)
- Can refactor to distributed later if needed

### Decision 4: Agent Boundary Definition

**Question:** What are read/write scopes for probe-design-context agent?

**Current Ambiguity:**
```
probe-design-context:
  Read/Write: probes/*/vhdl/  ← Hand-written FSMs
  Read-Only: libs/volo-platform-vhdl/  ← Utilities

Problem: Who orchestrates VHDL compilation? Who runs CocotB tests?
```

**Options:**

| Option | Agent Responsibilities | Pros | Cons | Validation Method |
|--------|----------------------|------|------|-------------------|
| **A: Design-Only** | VHDL editing only, calls test-runner agent | Clear separation, reuses existing agent | Extra coordination overhead | Create `spike/design-only-agent` |
| **B: Design+Test** | VHDL editing + test execution | Self-contained workflow, faster iteration | Scope creep, large agent | Create `spike/design-test-agent` |
| **C: Design+Build+Test** | Full development cycle | Complete autonomy, no context switching | Violates single responsibility | Create `spike/full-cycle-agent` |

**Decision Criteria:**
- Can the agent edit VHDL and verify changes? (Validation: Edit FSM, run tests)
- Is the agent.md file manageable? (Target: <800 lines)
- Are agent boundaries clear to users? (Validation: Write usage examples)

**Recommendation to test first:** Option B (Design+Test)
- Matches forge's forge-context pattern (generation + validation)
- Keeps iteration loop tight (edit → test → verify)
- Can split later if agent.md exceeds 800 lines

---

## 🧪 Iteration Protocol

Follow this process for each spike branch:

### Phase 1: Create Spike Branch (5-10 minutes)

```bash
# From main/feature branch
git checkout -b spike/[decision]-[approach]

# Examples:
git checkout -b spike/forge-as-submodule
git checkout -b spike/makefile-build
git checkout -b spike/centralized-tests
git checkout -b spike/design-test-agent
```

### Phase 2: Implement Minimal Structure (30-60 minutes)

Create just enough structure to test the decision:

**For Forge Integration (Decision 1):**
```bash
# Option A: Submodule
git submodule add https://github.com/sealablab/moku-instrument-forge.git libs/forge

# Option B: Copy
cp -r ../moku-instrument-forge/forge/ forge/

# Option C: External
# Document API endpoints, create wrapper script
```

**For VHDL Build (Decision 2):**
```bash
# Option A: Makefile
vim Makefile  # Add targets: build-libs, build-probes, test

# Option B: Python script
vim scripts/build_all.py

# Option C: Test runner integration
vim tests/run.py  # Add --build flag
```

**For Test Infrastructure (Decision 3):**
```bash
# Option A: Centralized
vim tests/run_all.py  # Orchestrates libs + probes tests

# Option B: Distributed
vim libs/volo-platform-vhdl/tests/run.py
vim probes/DS1140_PD/tests/run.py

# Option C: Pytest plugin
vim pytest_cocotb_plugin/plugin.py
```

**For Agent Boundaries (Decision 4):**
```bash
# Create agent context document
vim .claude/agents/probe-design-context/agent.md

# Define scope boundaries
# Write example workflows
# List read/write permissions
```

### Phase 3: Validation Tests (20-30 minutes)

Run the decision criteria validations:

```bash
# Example validation for Build Orchestration:
# 1. Compile utilities
ghdl -a --std=08 libs/volo-platform-vhdl/vhdl/packages/volo_common_pkg.vhd

# 2. Compile probe with utility deps
ghdl -a --std=08 -Plibs/volo-platform-vhdl/vhdl/packages/ probes/DS1140_PD/vhdl/DS1140_PD_fsm.vhd

# 3. Run CocotB tests
pytest probes/DS1140_PD/tests/ -v

# 4. Check CI/CD compatibility
act -j test  # Or commit to trigger GitHub Actions
```

### Phase 4: Document Results (10-15 minutes)

Create spike report:

```bash
# Create results document
vim spike-reports/[decision]-[approach]-results.md
```

**Report Template:**
```markdown
# Spike: [Decision] - [Approach]

**Date:** YYYY-MM-DD
**Branch:** spike/[decision]-[approach]
**Outcome:** ✅ Viable / ⚠️ Needs Work / ❌ Not Viable

## What Was Tested

- [List validation criteria tested]

## Results

### ✅ What Worked
- [Successes]

### ❌ What Didn't Work
- [Blockers, issues]

### ⚠️ Concerns
- [Potential future issues]

## Recommendation

[Continue with this approach / Try alternative / Hybrid approach]

## Next Steps

[If continuing: next validation tests]
[If pivoting: which alternative to try]
```

### Phase 5: Iterate or Commit (Variable)

**If spike is viable:**
```bash
# Clean up spike for merge
git rebase -i HEAD~N  # Squash commits
git checkout main
git merge spike/[decision]-[approach]
```

**If spike needs refinement:**
```bash
# Create v2 spike
git checkout -b spike/[decision]-[approach]-v2
# Refine based on learnings
```

**If spike is not viable:**
```bash
# Archive and try alternative
git tag archive/spike-[decision]-[approach]
git checkout main
git branch -D spike/[decision]-[approach]
# Create new spike with different approach
```

---

## 🎓 Example: First Iteration (Forge Integration)

Here's a walkthrough of testing Decision 1 (Forge Integration):

### Step 1: Create Spike

```bash
git checkout -b spike/forge-as-copy
```

### Step 2: Implement Structure

```bash
# Copy forge code into BPD repo
cp -r /tmp/moku-instrument-forge/forge/ .
cp -r /tmp/moku-instrument-forge/platform/ .

# Update pyproject.toml
vim pyproject.toml
# Add forge as local package:
# [tool.uv.workspace]
# members = ["forge", "libs/basic-app-datatypes"]
```

### Step 3: Validation Tests

```bash
# Test 1: Can we generate VHDL shim?
python -m forge.generator.generate_package probes/DS1140_PD/spec/DS1140_PD_app.yaml

# Expected output: probes/DS1140_PD/generated/*.vhd

# Test 2: Does generated VHDL compile?
ghdl -a --std=08 probes/DS1140_PD/generated/DS1140_PD_custom_inst_shim.vhd

# Test 3: Can we customize VHDL template?
vim forge/templates/shim_template.vhd.j2
# Add custom VHDL comment
python -m forge.generator.generate_package probes/DS1140_PD/spec/DS1140_PD_app.yaml
# Verify customization appears in output
```

### Step 4: Document Results

```markdown
# Spike: Forge Integration - Copy Code

**Outcome:** ✅ Viable

## Results

### ✅ What Worked
- Forge generates valid VHDL shim from YAML spec
- GHDL compiles generated code without errors
- Can customize templates (added probe-specific headers)
- uv workspace handles forge as local package

### ❌ What Didn't Work
- None (all validations passed)

### ⚠️ Concerns
- Forge code is 5,000+ LOC - large copy
- Manual merging needed if forge upstream updates
- May diverge from forge over time

## Recommendation

**Continue with copy approach**, but:
1. Tag forge version copied (e.g., forge-v2.0-copied-2025-11-03)
2. Document customizations in forge/CUSTOMIZATIONS.md
3. Schedule quarterly reviews of forge upstream for useful updates

## Next Steps

Test Decision 2 (VHDL Build Orchestration) now that forge integration validated.
```

### Step 5: Commit Spike

```bash
git add .
git commit -m "spike: Validate forge-as-copy integration (VIABLE)"
git checkout main
git merge spike/forge-as-copy
```

---

## 🗂️ Test Mono-Repo Structure

When ready to create test repo on GitHub:

### Proposed Structure

```
moku-custom-BPD/  (test repo)
├── forge/                    # Copied from moku-instrument-forge
├── libs/                     # Git submodules
│   ├── basic-app-datatypes/
│   ├── moku-models/
│   ├── riscure-models/
│   └── volo-platform-vhdl/  # NEW: Extracted VHDL utilities
├── probes/                   # Probe applications
│   └── DS1140_PD/
│       ├── spec/             # YAML specification
│       ├── generated/        # Generated VHDL (from forge)
│       ├── vhdl/             # Hand-written FSM
│       └── tests/            # CocotB integration tests
├── .claude/
│   ├── agents/
│   │   ├── probe-design-context/
│   │   ├── deployment-context/
│   │   ├── hardware-debug-context/
│   │   └── workflow-coordinator/
│   ├── commands/
│   └── shared/
├── tests/                    # Test infrastructure (run.py)
├── scripts/                  # Build scripts (build_all.py or Makefile)
├── docs/
├── llms.txt                  # Entry point (not CLAUDE.md)
└── pyproject.toml            # uv workspace config
```

### GitHub Repo Creation (when ready)

On GitHub.com (works on iPad):
1. Navigate to https://github.com/sealablab/
2. Click "New repository"
3. Name: `test-moku-custom-BPD` (or `moku-custom-BPD-spike`)
4. Description: "Test mono-repo for BPD architecture validation (spike branches)"
5. Private repo
6. Initialize with README
7. Clone locally and add spike structures

---

## 📊 Success Criteria

Know when the design is "good enough" to implement:

### Minimum Viable Architecture

✅ **All 4 decisions validated** via spike branches
✅ **Can generate VHDL** from YAML spec using forge
✅ **Can compile VHDL** across submodules (libs + probes)
✅ **Can run CocotB tests** for utilities and probes
✅ **Agent boundaries documented** (clear read/write scopes)

### Quality Thresholds

✅ **Build time:** <2 minutes for full build (libs + probes)
✅ **Test time:** <5 minutes for full test suite (P1 tests)
✅ **Agent context:** <800 lines per agent.md
✅ **Documentation:** Quick ref (<400 lines) + full docs available

### Integration Tests

✅ **End-to-end workflow works:**
1. Write YAML spec
2. Generate VHDL via forge
3. Compile VHDL with utilities
4. Run CocotB tests
5. Deploy to Moku (conceptual, don't need hardware)

✅ **Developer workflow smooth:**
1. Clone repo with `--recurse-submodules`
2. Run `uv sync`
3. Run build command (Makefile/script/test runner)
4. Edit probe FSM
5. Re-run tests (<1 minute for single probe)

---

## 🔄 Iterative Design Process

### Iteration 1: Validate Core Decisions (Estimated: 6-8 hours)

**Goal:** Spike all 4 decisions, identify viable approaches

**Tasks:**
1. Create spike branch for Decision 1 (forge integration)
2. Validate basic code generation works
3. Create spike branch for Decision 2 (VHDL build)
4. Validate compilation across submodules
5. Create spike branch for Decision 3 (test infrastructure)
6. Validate CocotB tests run
7. Create spike branch for Decision 4 (agent boundaries)
8. Draft agent.md with clear scopes

**Deliverables:**
- 4 spike branches with validation results
- Spike reports for each decision
- Recommended approach for each decision

### Iteration 2: Integrate and Refine (Estimated: 4-6 hours)

**Goal:** Combine validated approaches, identify integration issues

**Tasks:**
1. Merge viable spikes into test mono-repo structure
2. Test end-to-end workflow (YAML → VHDL → compiled → tested)
3. Identify friction points (slow builds, complex commands, etc.)
4. Refine based on issues discovered
5. Write developer getting-started guide

**Deliverables:**
- Working test mono-repo with basic DS1140_PD example
- Build/test commands documented
- Integration issues identified and resolved

### Iteration 3: Polish and Document (Estimated: 3-4 hours)

**Goal:** Production-ready architecture with complete documentation

**Tasks:**
1. Write agent contexts (probe-design-context, workflow-coordinator)
2. Create llms.txt entry point
3. Add CI/CD workflows (.github/workflows/)
4. Write migration guide (EZ-EMFI → moku-custom-BPD)
5. Document architectural decisions (ADRs)

**Deliverables:**
- Complete agent system (4 agents, clear boundaries)
- llms.txt + full documentation
- CI/CD workflows
- Migration guide ready to execute

**Total estimated time:** 13-18 hours (vs original 8-12h estimate, more realistic than 32-46h worst-case)

---

## 🚀 Next Session Checklist

When picking up this work on your dev laptop:

### Environment Setup

```bash
# Verify tools available
ghdl --version        # VHDL compiler
python --version      # Python 3.10+
uv --version          # uv package manager
git --version         # Git

# Clone both repos
git clone --recurse-submodules https://github.com/sealablab/EZ-EMFI.git
git clone --recurse-submodules https://github.com/sealablab/moku-instrument-forge.git

# Load context
cd EZ-EMFI
git checkout claude/review-bad-main-commit-011CUmSeqtepjpr5MAjxV2iF
```

### Context Loading

```bash
# Quick summary (5 minutes)
head -100 ARCHITECTURE_COMPARISON_ANALYSIS.md
head -100 FORGE_ARCHITECTURE_ANALYSIS.md

# Full context (if needed, 30 minutes)
# Read Section 10 of ARCHITECTURE_COMPARISON_ANALYSIS.md
# Read Section 12 of FORGE_ARCHITECTURE_ANALYSIS.md
# Read original planning doc: monorepo-refactor-pickup-here.md
```

### Start First Spike

```bash
# Create first spike branch
git checkout -b spike/forge-as-copy

# Follow "Example: First Iteration" section above
# Test forge integration (30-60 minutes)
# Document results (10 minutes)
# Commit or iterate
```

---

## 📝 Prompt for Next Claude Code Session

**Copy this when starting work:**

```
I'm continuing the mono-repo architecture design for moku-custom-BPD.

Context loaded:
- Read docs/MONO_REPO_ITERATION_PROMPT.md
- Reviewed ARCHITECTURE_COMPARISON_ANALYSIS.md (Sections 2, 3, 10)
- Reviewed FORGE_ARCHITECTURE_ANALYSIS.md (Sections 2, 4, 12)

Current task: [Iteration 1 / Iteration 2 / Iteration 3]
Testing: Decision [1/2/3/4] - [Approach]
Branch: spike/[decision]-[approach]

Please help me:
1. [Implement spike structure / Run validation tests / Document results]
2. [Next specific task]

Files I need you to create/edit:
- [List files]
```

---

## 📚 Additional References

**If you need more context:**

- **Forge Agent Examples:** `/tmp/moku-instrument-forge/.claude/agents/forge-context/agent.md`
- **Forge Test Suite:** `/tmp/moku-instrument-forge/forge/tests/`
- **EZ-EMFI Current Tests:** `tests/run.py`, `tests/conftest.py`
- **Package Contract:** `/tmp/moku-instrument-forge/.claude/shared/package_contract.md`

**Key commits to reference:**

- **Planning doc:** EZ-EMFI @ `b0cb32bb` (feature/BAD-main)
- **Forge Phase 6:** moku-instrument-forge @ `e036c2b` (main)
- **Analysis added:** EZ-EMFI @ `d9aa8c5` (claude/review-bad-main-commit-011CUmSeqtepjpr5MAjxV2iF)

---

**Ready to iterate!** Start with Decision 1 (Forge Integration) when on dev laptop.
