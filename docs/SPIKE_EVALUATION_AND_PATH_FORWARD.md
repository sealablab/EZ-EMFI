# Spike Evaluation and Path Forward to Monorepo

**Date:** 2025-11-04
**Spike Repo:** [moku-spike-redux](https://github.com/sealablab/moku-spike-redux)
**Status:** ✅ All 4 architectural decisions validated (3.75h actual vs 6-8h estimated)

---

## Executive Summary

**Verdict: 🎯 ALL SPIKES SUCCESSFUL - READY FOR PRODUCTION MONOREPO**

All 4 critical architectural decisions were validated in **3.75 hours** (47% faster than estimated). The spike testing methodology proved highly effective at identifying the right approaches before committing to full migration.

**Key Achievements:**
- ✅ Forge integration: Git submodule approach validated (60 min)
- ✅ VHDL build: Cocotb/pytest pattern validated, build: 0.27s (440x faster than goal)
- ✅ Test infrastructure: Pytest discovery validated, 0.00s discovery time
- ✅ Agent boundaries: probe-design-context defined (564 lines, no conflicts)

**Recommendation:** Proceed to **Iteration 2** - Create production monorepo with validated architecture.

---

## 1. Spike-by-Spike Evaluation

### Spike 1: Forge as Git Submodule ✅

**Question:** Can we use `moku-instrument-forge` as a git submodule?

**Result:** ✅ **SUCCESS** - All 5 validation tests passed

**What Was Validated:**
1. Forge imports successfully with `sys.path` manipulation
2. Forge submodule dependencies accessible (basic-app-datatypes, moku-models, riscure-models)
3. YAML loading via `BasicAppsRegPackage.from_yaml()` works
4. VHDL generation function callable
5. uv dependency management works with submodules

**Performance:**
- Import time: < 1 second
- Disk space: ~5 MB (forge + submodules)
- Time to validate: 60 minutes

**Caveats:**
- Requires `git clone --recurse-submodules` or `git submodule update --init --recursive`
- Needs `sys.path` manipulation (could create helper script)
- Boolean YAML values must use `true/false` not `0/1`

**Recommendation:** ✅ **Use forge as git submodule in production**

**Rationale:**
- Clean version control (forge updates via `git submodule update`)
- No code duplication (single source of truth)
- Easy to track forge version (git commit hash)
- All forge features accessible
- Beats alternatives (copy = duplication, PyPI = not published)

**Production Requirements:**
- Add `.gitmodules` with forge submodule
- Document `git clone --recurse-submodules` in README
- Create `scripts/setup_forge_path.py` helper
- Pin forge to specific commit/tag (not `main`)
- Test on clean clone

---

### Spike 2: VHDL Build Orchestration ✅

**Question:** How to orchestrate VHDL compilation across platform/forge/probe code?

**Result:** ✅ **SUCCESS** - Cocotb/pytest pattern works perfectly

**What Was Validated:**
1. Clean file organization (platform/forge/probe separation)
2. Cocotb/pytest pattern without Makefiles
3. Compilation successful for 6 VHDL files
4. Composable structure (easy to add probes/packages)

**Performance:**
- Build time: **0.27 seconds** ⚡
- Goal: < 120 seconds
- **440x faster than goal!**

**Structure Validated:**
```
libs/platform/          # Platform VHDL packages
libs/volo-platform-vhdl/  # Forge packages (fsm_observer, volo_voltage_pkg)
probes/*/generated/     # Probe-specific generated code
```

**Build Pattern:**
- `test_configs.py` declares sources + dependencies
- `run_test.py` uses `cocotb_tools.runner` API
- No Makefiles needed
- Python handles orchestration

**Caveats:**
- Compilation order matters (packages before entities, main before shim)
- All files compile to same `work` library by default
- May want separate libraries for large codebases (future optimization)

**Recommendation:** ✅ **Use cocotb/pytest + test_configs.py pattern**

**Rationale:**
- Already proven in EZ-EMFI
- No Makefiles (Python orchestration more maintainable)
- Extremely fast builds (0.27s for 6 files)
- Composable (easy to add probes and libraries)
- Clear dependency declaration

**Production Requirements:**
- Use exact structure validated in spike
- Keep `test_configs.py` pattern for dependency declaration
- Consider library separation for large codebases (future optimization)

---

### Spike 3: Centralized Test Infrastructure ✅

**Question:** How to organize CocotB tests across libs/ and probes/ directories?

**Result:** ✅ **SUCCESS** - Pytest discovers tests instantly across entire monorepo

**What Was Validated:**
1. Discover volo tests in `libs/volo-platform-vhdl/tests/`
2. Discover probe tests in `probes/*/tests/`
3. Run subset execution (all tests / volo only / probe only)
4. Shared fixtures accessible via import
5. Fork-bomb prevention (exclude custom runners)

**Performance:**
- Test discovery: **0.00 seconds** (< 5s goal)
- **5000x faster than goal!**
- Volo tests found: 2 tests
- Probe tests found: 2 tests
- Fork bombs: 0
- Import errors: 0

**Configuration Pattern:**
```toml
[tool.pytest.ini_options]
python_files = "test_*.py"
testpaths = ["libs", "probes"]
norecursedirs = [".venv", "sim_build", "__pycache__", ".git"]
addopts = "--ignore=tests/run.py --ignore=tests/test_configs.py"
```

**Key Insights:**
- **Use `testpaths` for inclusion** (only search `libs/` and `probes/`)
- **Use `addopts --ignore` to exclude custom runners** (prevents fork bombs)
- **Shared fixtures in `tests/conftest.py`** (importable, not auto-discovered)
- **Helper modules** (not `test_*.py`) ignored by pytest

**Caveats:**
- Custom test runners (like `tests/run.py`) MUST be excluded
- `testpaths` excludes `tests/` directory by design
- Shared fixtures must be explicitly imported

**Recommendation:** ✅ **Use pytest with explicit testpaths configuration**

**Rationale:**
- Clean separation (platform tests in `libs/`, probe tests in `probes/`)
- Instant test discovery across entire monorepo
- Flexible execution (all tests or subset by directory)
- Shared infrastructure (conftest.py reusable)
- Fork-bomb safe (proper exclusion of custom runners)

**Production Requirements:**
- Use exact pyproject.toml config validated in spike
- Document test execution patterns in README
- Consider pytest-xdist for parallel execution (`pytest -n auto`)

---

### Spike 4: Agent Boundary Definition ✅

**Question:** What should `probe-design-context` agent scope be?

**Result:** ✅ **SUCCESS** - Agent defined (564 lines), R/W scope prevents conflicts

**What Was Validated:**
1. agent.md exists and complete (564 lines)
2. R/W scope clearly defined (no overlap with other agents)
3. Tool access defined (GHDL, CocotB, pytest, git)
4. Workflow example demonstrates complete iteration
5. Agent size < 800 lines (readable in single session)

**Scope Decision:** **Design+Test** (not deployment)

**R/W Boundaries:**
```
Read & Write:  probes/*/vhdl/, probes/*/tests/, .claude/shared/
Read-Only:     libs/, forge/, probes/*/generated/
No Access:     Deployment configs, hardware debugging
```

**Tool Access:**
- GHDL (compile VHDL)
- CocotB + pytest (test execution)
- Git (commit, but not deploy)
- Forge (read generated files to understand interface)

**Workflow:**
```
1. Read forge-generated interface (probes/*/generated/)
2. Design FSM states (READY, ARMED, FIRING, etc.)
3. Write VHDL (probes/*/vhdl/fsm.vhd)
4. Write tests (probes/*/tests/test_progressive.py)
5. Compile with GHDL
6. Run tests with pytest
7. Commit if passing
8. Hand off to deployment-context
```

**Handoff Points:**
- → deployment-context: After tests pass (ready for hardware)
- → hardware-debug-context: If hardware behavior differs from simulation
- → forge-context: If interface needs modification (update YAML)
- → workflow-coordinator: For multi-step orchestration

**Zero Overlap Validation:**

| Agent | R/W Scope | No Overlap |
|-------|-----------|------------|
| forge-context | `forge/`, `apps/` | ✅ |
| probe-design-context | `probes/*/vhdl/`, `probes/*/tests/` | ✅ |
| deployment-context | Deployment configs, hardware | ✅ |

**Caveats:**
- Agent cannot fix bugs in `libs/` (read-only, hand off to maintainer)
- Agent cannot deploy to hardware (hand off to deployment-context)
- Agent size limit (800 lines) requires discipline

**Recommendation:** ✅ **Use probe-design-context agent with defined R/W permissions**

**Rationale:**
- Clear boundaries (no overlap with forge-context or deployment-context)
- Right tools (GHDL/CocotB match FSM design workflow)
- Complete workflow (can iterate on FSM design without handoffs)
- Handoff clarity (knows when to delegate)
- Manageable size (564 lines fits in single context window)

**Production Requirements:**
- Create `.claude/agents/probe-design-context/agent.md`
- Configure Claude Code tool permissions (if available)
- Test agent with real probe design task

---

## 2. Overall Architecture Validated

### Monorepo Structure (Validated)

```
moku-custom-BPD/                    # Proposed production repo name
├── forge/                          # Git submodule: moku-instrument-forge
│   ├── generator/                  # Code generation (YAML → VHDL)
│   └── libs/                       # Submodules (basic-app-datatypes, etc.)
├── libs/
│   ├── platform/                   # Platform-specific VHDL packages
│   │   └── common/
│   │       └── custom_inst_common_pkg.vhd
│   └── volo-platform-vhdl/         # Generic utilities (future submodule)
│       └── vhdl/
│           ├── packages/           # volo_voltage_pkg, etc.
│           ├── debugging/          # fsm_observer (from Q1 decision)
│           └── loader/             # volo_bram_loader
├── probes/
│   ├── DS1120_PD/                  # DS1120A probe driver
│   │   ├── generated/              # Forge output (shim + main template)
│   │   ├── vhdl/                   # Custom FSM logic
│   │   └── tests/                  # Progressive CocotB tests
│   └── DS1140_PD/                  # DS1140A probe driver
│       ├── generated/
│       ├── vhdl/
│       └── tests/
├── tests/
│   ├── conftest.py                 # Shared fixtures (importable)
│   ├── run.py                      # Custom runner (excluded from pytest)
│   └── test_configs.py             # Build configuration
├── scripts/
│   └── setup_forge_path.py         # Helper for forge imports
├── .claude/
│   ├── agents/
│   │   ├── probe-design-context/   # FSM design agent (564 lines)
│   │   ├── forge-context/          # Code generation (from forge repo)
│   │   ├── deployment-context/     # Hardware deployment
│   │   └── hardware-debug-context/ # Oscilloscope debugging
│   └── commands/
│       ├── vhdl.md
│       ├── python.md
│       └── test.md
├── pyproject.toml                  # Python dependencies + pytest config
└── README.md                       # Getting started guide
```

### Build System (Validated)

**Pattern:** Cocotb/pytest + test_configs.py

**Build Flow:**
```python
# test_configs.py
TESTS_CONFIG = {
    "ds1140_pd_build_validation": TestConfig(
        sources=[
            Path("libs/platform/common/custom_inst_common_pkg.vhd"),
            Path("libs/volo-platform-vhdl/vhdl/packages/basic_app_types_pkg.vhd"),
            Path("probes/DS1140_PD/generated/DS1140_PD_custom_inst_main.vhd"),
            Path("probes/DS1140_PD/vhdl/DS1140_PD_fsm.vhd"),
        ],
        toplevel="DS1140_PD_custom_inst_main",
        ghdl_args=["--std=08"],
    )
}

# run_test.py
runner = get_runner("ghdl")
runner.build(sources=config.sources, hdl_toplevel=config.toplevel, build_args=config.ghdl_args)
runner.test(hdl_toplevel=config.toplevel, test_module=config.test_module)
```

**Benefits:**
- No Makefiles (Python orchestration)
- Clear dependency declaration
- Fast builds (0.27s for 6 files)
- Easy to extend (add probes/packages)

### Test Infrastructure (Validated)

**Pattern:** Pytest with explicit testpaths

**Pytest Config:**
```toml
[tool.pytest.ini_options]
python_files = "test_*.py"
testpaths = ["libs", "probes"]
norecursedirs = [".venv", "sim_build", "__pycache__", ".git"]
addopts = "--ignore=tests/run.py --ignore=tests/test_configs.py"
```

**Test Execution:**
```bash
pytest                          # Run all tests (libs + probes)
pytest libs/                    # Run all library tests
pytest probes/                  # Run all probe tests
pytest probes/DS1140_PD/        # Run single probe tests
pytest -n auto                  # Parallel execution (pytest-xdist)
```

**Benefits:**
- Instant discovery (0.00s)
- Flexible execution (all/subset)
- Fork-bomb safe (excludes custom runners)
- Parallel execution ready

### Agent Architecture (Validated)

**Agents:**
1. **forge-context** (from forge repo)
   - Domain: Code generation (YAML → VHDL)
   - R/W: `forge/`, `apps/`
   - Tools: Jinja2, Pydantic, YAML

2. **probe-design-context** (new, validated)
   - Domain: FSM design (custom logic)
   - R/W: `probes/*/vhdl/`, `probes/*/tests/`
   - Tools: GHDL, CocotB, pytest, git

3. **deployment-context** (from forge repo)
   - Domain: Hardware deployment
   - R/W: Deployment configs, hardware
   - Tools: Moku API, CloudCompile

4. **hardware-debug-context** (from forge repo)
   - Domain: Oscilloscope debugging
   - R/W: Debug logs, hardware
   - Tools: Oscilloscope, Moku API

**Agent Flow:**
```
forge-context (YAML → VHDL)
    ↓
probe-design-context (FSM design + tests)
    ↓
deployment-context (Deploy to hardware)
    ↓ (if issues)
hardware-debug-context (Debug with oscilloscope)
```

**Zero Overlap:** All agents have distinct R/W scopes, preventing conflicts.

---

## 3. Path Forward to Monorepo

### Phase 1: Create Production Repo (Estimated: 2-3 hours)

**Task:** Create `moku-custom-BPD` repository with validated architecture

**Steps:**
1. **Create repo on GitHub** (5 min)
   ```bash
   gh repo create sealablab/moku-custom-BPD --public --description "Mono-repo for Moku custom EMFI probe drivers"
   git clone git@github.com:sealablab/moku-custom-BPD.git
   cd moku-custom-BPD
   ```

2. **Add forge as submodule** (10 min)
   ```bash
   git submodule add https://github.com/sealablab/moku-instrument-forge.git forge
   git submodule update --init --recursive
   # Pin forge to specific commit (not main)
   cd forge && git checkout <stable-commit-hash> && cd ..
   git add forge
   git commit -m "Add forge as submodule at <commit-hash>"
   ```

3. **Create directory structure** (15 min)
   ```bash
   mkdir -p libs/platform/common
   mkdir -p libs/volo-platform-vhdl/vhdl/{packages,debugging,loader}
   mkdir -p probes/{DS1120_PD,DS1140_PD}/{generated,vhdl,tests}
   mkdir -p tests
   mkdir -p scripts
   mkdir -p .claude/agents/{probe-design-context,deployment-context,hardware-debug-context}
   mkdir -p .claude/commands
   ```

4. **Copy validated files from spike** (30 min)
   - `pyproject.toml` (with pytest config)
   - `tests/conftest.py` (shared fixtures)
   - `tests/run.py` (custom runner)
   - `tests/test_configs.py` (build config template)
   - `.claude/agents/probe-design-context/agent.md` (from spike)

5. **Create setup helper** (15 min)
   ```python
   # scripts/setup_forge_path.py
   import sys
   from pathlib import Path

   def setup_forge_path():
       forge_path = Path(__file__).parent.parent / "forge"
       sys.path.insert(0, str(forge_path))

       libs_path = forge_path / "libs"
       for lib_dir in libs_path.iterdir():
           if lib_dir.is_dir():
               sys.path.insert(0, str(lib_dir))
   ```

6. **Create README with getting started** (30 min)
   - Clone instructions (with `--recurse-submodules`)
   - Python environment setup (`uv sync`)
   - Test execution (`pytest`)
   - Agent usage patterns

7. **Create .gitignore** (5 min)
   ```
   .venv/
   __pycache__/
   *.pyc
   sim_build/
   .pytest_cache/
   work-obj08.cf
   *.vcd
   *.ghw
   ```

8. **Initial commit and push** (5 min)
   ```bash
   git add .
   git commit -m "feat: Initial monorepo structure with validated architecture

   - Add forge as submodule (validated in spike 1)
   - Create directory structure (libs/, probes/, tests/)
   - Add pytest config (validated in spike 3)
   - Add probe-design-context agent (validated in spike 4)
   - Add setup helper for forge imports
   - Document getting started in README

   All architectural decisions validated in moku-spike-redux.
   See: https://github.com/sealablab/moku-spike-redux"
   git push origin main
   ```

**Validation:**
- [ ] Repo clones with `--recurse-submodules`
- [ ] `uv sync` works
- [ ] Forge imports work with setup helper
- [ ] Pytest discovers no tests (expected, no tests yet)
- [ ] README clear for new contributors

---

### Phase 2: Migrate DS1140_PD (Estimated: 3-4 hours)

**Task:** Migrate DS1140_PD probe from EZ-EMFI to moku-custom-BPD

**Steps:**

1. **Extract volo utilities** (60 min)
   - Copy `fsm_observer.vhd` → `libs/volo-platform-vhdl/vhdl/debugging/`
   - Copy `volo_voltage_pkg.vhd` → `libs/volo-platform-vhdl/vhdl/packages/`
   - Copy `volo_bram_loader.vhd` → `libs/volo-platform-vhdl/vhdl/loader/`
   - Copy other volo utilities as needed
   - **Validation:** Compile volo utilities standalone

2. **Copy platform packages** (30 min)
   - Copy `custom_inst_common_pkg.vhd` → `libs/platform/common/`
   - Update imports if needed
   - **Validation:** Compile platform packages standalone

3. **Copy DS1140_PD VHDL** (45 min)
   - Copy generated files → `probes/DS1140_PD/generated/`
   - Copy custom logic → `probes/DS1140_PD/vhdl/`
   - Update imports to use `libs/` structure
   - **Validation:** Compile DS1140_PD with dependencies

4. **Copy DS1140_PD tests** (45 min)
   - Copy tests → `probes/DS1140_PD/tests/`
   - Update test_configs.py with DS1140_PD config
   - Update imports
   - **Validation:** Run tests, confirm pass

5. **Commit migration** (10 min)
   ```bash
   git add .
   git commit -m "feat: Migrate DS1140_PD from EZ-EMFI

   - Extract volo utilities to libs/volo-platform-vhdl/
   - Add platform packages to libs/platform/
   - Migrate DS1140_PD probe (generated + custom VHDL + tests)
   - Update imports to use monorepo structure
   - All tests passing

   Source: EZ-EMFI commit <hash>"
   git push
   ```

**Validation:**
- [ ] All VHDL compiles without errors
- [ ] All tests pass
- [ ] Build time < 2 seconds
- [ ] Test discovery < 1 second
- [ ] Zero import errors

---

### Phase 3: Migrate DS1120_PD (Estimated: 2-3 hours)

**Task:** Migrate DS1120_PD probe from EZ-EMFI to moku-custom-BPD

**Steps:**

1. **Copy DS1120_PD VHDL** (45 min)
   - Copy generated files → `probes/DS1120_PD/generated/`
   - Copy custom logic → `probes/DS1120_PD/vhdl/`
   - Update imports to use `libs/` structure
   - **Validation:** Compile DS1120_PD with dependencies

2. **Copy DS1120_PD tests** (45 min)
   - Copy tests → `probes/DS1120_PD/tests/`
   - Update test_configs.py with DS1120_PD config
   - Update imports
   - **Validation:** Run tests, confirm pass

3. **Run all tests** (15 min)
   ```bash
   pytest                          # All tests
   pytest probes/DS1120_PD/        # DS1120_PD only
   pytest probes/DS1140_PD/        # DS1140_PD only
   pytest -n auto                  # Parallel execution
   ```

4. **Commit migration** (10 min)
   ```bash
   git add .
   git commit -m "feat: Migrate DS1120_PD from EZ-EMFI

   - Migrate DS1120_PD probe (generated + custom VHDL + tests)
   - Update imports to use monorepo structure
   - All tests passing (DS1120_PD + DS1140_PD)
   - Parallel test execution validated

   Source: EZ-EMFI commit <hash>"
   git push
   ```

**Validation:**
- [ ] DS1120_PD compiles without errors
- [ ] DS1120_PD tests pass
- [ ] DS1140_PD tests still pass (no regression)
- [ ] Parallel execution works (`pytest -n auto`)

---

### Phase 4: Polish and Document (Estimated: 2-3 hours)

**Task:** Clean up monorepo, improve documentation, prepare for production use

**Steps:**

1. **Create CLAUDE.md** (45 min)
   - Document monorepo structure
   - Explain agent boundaries
   - Add quick start for each context (vhdl/python/test)
   - Link to forge documentation
   - Document spike learnings

2. **Create development workflows** (30 min)
   - Create `.claude/commands/vhdl.md` (VHDL development context)
   - Create `.claude/commands/python.md` (Python tooling context)
   - Create `.claude/commands/test.md` (Testing context)

3. **Add CI/CD skeleton** (optional, 45 min)
   - Create `.github/workflows/test.yml`
   - Run tests on push (pytest)
   - Lint VHDL (ghdl --syntax-only)
   - Lint Python (ruff)

4. **Update README with workflows** (30 min)
   - Add "How to add a new probe" guide
   - Add "How to update forge" guide
   - Add "How to run tests" guide
   - Add troubleshooting section

5. **Final commit** (10 min)
   ```bash
   git add .
   git commit -m "docs: Complete monorepo documentation and workflows

   - Add CLAUDE.md with monorepo patterns
   - Add .claude/commands/ for context switching
   - Add development workflow guides
   - Update README with comprehensive guides
   - (Optional) Add CI/CD skeleton

   Monorepo ready for production use!"
   git push
   ```

**Validation:**
- [ ] CLAUDE.md comprehensive and accurate
- [ ] README covers all common workflows
- [ ] Context commands tested with Claude Code
- [ ] (Optional) CI/CD passes

---

### Timeline Summary

| Phase | Description | Estimated Time | Deliverable |
|-------|-------------|----------------|-------------|
| **1** | Create production repo | 2-3h | Empty monorepo with structure |
| **2** | Migrate DS1140_PD | 3-4h | DS1140_PD working in monorepo |
| **3** | Migrate DS1120_PD | 2-3h | Both probes in monorepo |
| **4** | Polish and document | 2-3h | Production-ready monorepo |
| **Total** | | **9-13 hours** | moku-custom-BPD repo ready |

**Original estimate:** 13-18 hours (Iteration 1 + 2 + 3)
**Spike time saved:** 4-5 hours (validated approaches, no trial-and-error)
**Actual estimate:** 9-13 hours ✅

---

## 4. Recommended Monorepo Name

### Option 1: `moku-custom-BPD` ⭐ **RECOMMENDED**

**Rationale:**
- **Descriptive:** "custom-BPD" = custom Biasing and Probing Device
- **Consistent with forge:** Matches `moku-instrument-forge` naming pattern
- **Clear purpose:** Anyone seeing the repo knows it's for custom Moku instruments
- **Acronym precedent:** BPD already used in planning documents

**Full name:** `sealablab/moku-custom-BPD`

**Pros:**
- ✅ Self-documenting name
- ✅ Matches forge naming convention
- ✅ Clear scope (custom instruments, not general Moku development)
- ✅ Short and memorable

**Cons:**
- ⚠️ "BPD" might not be universally understood (but used in planning docs)

---

### Option 2: `moku-emfi-probes`

**Rationale:**
- **Explicit:** "emfi-probes" = EMFI probe drivers
- **Clear technology:** EMFI (Electromagnetic Fault Injection)
- **Specific:** More specific than "custom-BPD"

**Full name:** `sealablab/moku-emfi-probes`

**Pros:**
- ✅ Technology-explicit (EMFI)
- ✅ Clear purpose (probe drivers)
- ✅ Easy to understand

**Cons:**
- ⚠️ Less flexible if you add non-EMFI probes in future
- ⚠️ Longer name

---

### Option 3: `moku-probe-drivers`

**Rationale:**
- **Generic:** "probe-drivers" = any probe type
- **Flexible:** Can add other probe types later
- **Simple:** Easy to understand

**Full name:** `sealablab/moku-probe-drivers`

**Pros:**
- ✅ Generic (not limited to EMFI)
- ✅ Simple and clear
- ✅ Flexible for future expansion

**Cons:**
- ⚠️ Less specific (could be any probe type)
- ⚠️ Doesn't convey "custom instrument" aspect

---

### Naming Recommendation: `moku-custom-BPD` ⭐

**Final recommendation:** Use **`moku-custom-BPD`**

**Reasoning:**
1. **Consistency:** Matches `moku-instrument-forge` naming pattern
2. **Precedent:** "BPD" already used in planning documents
3. **Scope:** Conveys this is for custom Moku instruments (not general development)
4. **Memorable:** Short, distinctive, easy to remember
5. **Flexible:** Can include multiple probe types under "BPD" umbrella

**GitHub URL:** `https://github.com/sealablab/moku-custom-BPD`

---

## 5. Critical Success Factors

### Before Starting Phase 1

✅ **Prerequisites:**
- [ ] Spike results reviewed and understood
- [ ] All 4 architectural decisions approved
- [ ] Team aligned on monorepo structure
- [ ] Naming decision finalized

✅ **Risk Mitigation:**
- [ ] Backup EZ-EMFI repo (git tag before migration)
- [ ] Test forge submodule on fresh clone
- [ ] Validate pytest config on clean environment
- [ ] Review agent boundaries with team

### During Migration (Phase 2-3)

✅ **Validation Gates:**
- [ ] After each phase: All tests pass
- [ ] After each phase: Build time < 2 seconds
- [ ] After each phase: Commit with clear message
- [ ] Before next phase: Code review (optional)

✅ **Rollback Plan:**
- Keep EZ-EMFI repo intact during migration
- Use git tags for each phase completion
- If issues: Roll back to previous phase tag
- Document issues in spike repo for future reference

### After Migration (Phase 4)

✅ **Production Readiness:**
- [ ] Documentation complete (README, CLAUDE.md, workflows)
- [ ] All tests passing
- [ ] Agent boundaries tested
- [ ] Team onboarded to new structure
- [ ] (Optional) CI/CD configured

✅ **Archive Plan:**
- [ ] Tag `moku-spike-redux` as "validated"
- [ ] Add link to production repo in spike README
- [ ] Update EZ-EMFI README: "Migrated to moku-custom-BPD"
- [ ] Consider archiving EZ-EMFI (or mark as legacy)

---

## 6. Key Learnings from Spikes

### What Worked Exceptionally Well

1. **Spike methodology itself**
   - Time-boxed experiments (30-90 min each)
   - Clear validation criteria
   - Quick & dirty approach (no polish needed)
   - **Result:** Validated 4 decisions in 3.75h vs 6-8h estimated (47% faster)

2. **Cocotb/pytest pattern**
   - No Makefiles needed
   - Python orchestration more maintainable
   - Extremely fast builds (0.27s)
   - **Lesson:** Trust patterns that already work in EZ-EMFI

3. **Forge as submodule**
   - Clean version control
   - No code duplication
   - Easy to update
   - **Lesson:** Git submodules appropriate for mono-repo dependencies

4. **Agent boundary definition**
   - R/W scope prevents conflicts
   - Clear handoff points
   - Manageable size (< 800 lines)
   - **Lesson:** Define boundaries BEFORE writing code

### What Required Attention

1. **Git submodule initialization**
   - Must document `--recurse-submodules` clearly
   - Post-clone hook could help
   - **Mitigation:** Add to README prominently

2. **Custom runner exclusion**
   - Pytest tried to collect `tests/run.py` (fork bomb)
   - Required explicit `--ignore` flag
   - **Lesson:** Always exclude custom runners from pytest discovery

3. **Agent size discipline**
   - Easy to let agent docs grow large
   - Required separate validation doc for examples
   - **Lesson:** Keep agent.md concise, use separate docs for extended examples

### Architectural Insights

1. **Progressive disclosure works across repos**
   - Root llms.txt → submodule llms.txt → submodule CLAUDE.md
   - Allows detailed documentation without overwhelming root
   - **Validated in forge, applies to BPD monorepo**

2. **Test infrastructure scales well**
   - 0.00s discovery for entire monorepo
   - Can run all tests or subset by directory
   - **Monorepo won't slow down testing**

3. **Build orchestration is composable**
   - Easy to add new probes (just add to probes/)
   - Easy to add new packages (just add to libs/)
   - **Structure supports growth**

4. **Agent architecture prevents conflicts**
   - Zero R/W scope overlap
   - Clear handoff points
   - **Design validated before implementation**

---

## 7. Next Steps (Immediate)

### For User (Now)

1. **Review this evaluation** ✅
   - Confirm spike results accurately represented
   - Approve architectural decisions
   - Approve monorepo name (`moku-custom-BPD`)

2. **Create production repo** (5 min)
   ```bash
   gh repo create sealablab/moku-custom-BPD --public \
     --description "Mono-repo for Moku custom EMFI probe drivers (DS1120-PD, DS1140-PD)"
   ```

3. **Decide on migration timeline**
   - Schedule 2-3 hour blocks for each phase
   - Estimate: 9-13 hours total across 4 phases
   - Could spread over 1-2 weeks

### For Assistant (After Approval)

1. **Execute Phase 1** (2-3h)
   - Create initial monorepo structure
   - Add forge as submodule
   - Create README and setup scripts
   - Initial commit

2. **Execute Phase 2** (3-4h)
   - Migrate DS1140_PD
   - Validate tests pass
   - Commit

3. **Execute Phase 3** (2-3h)
   - Migrate DS1120_PD
   - Validate both probes work
   - Commit

4. **Execute Phase 4** (2-3h)
   - Polish documentation
   - Add workflows
   - Final validation

---

## 8. Open Questions

### Q1: Should we migrate tools/ directory from EZ-EMFI?

**Context:** EZ-EMFI has `tools/` directory with Python TUI apps

**Options:**
- **A:** Migrate to `moku-custom-BPD/tools/`
- **B:** Keep in separate repo (not part of monorepo)
- **C:** Migrate to forge (if general-purpose)

**Recommendation:** Depends on tool scope
- If probe-specific: Migrate to `probes/*/tools/`
- If general-purpose: Keep separate or migrate to forge
- If deployment-related: Migrate to monorepo

**Decision needed:** User input on tool scope

---

### Q2: Should we create volo-platform-vhdl as separate repo or inline?

**Context:** Q1 decision says fsm_observer should be in volo-platform-vhdl

**Options:**
- **A:** Inline in `libs/volo-platform-vhdl/` (simpler, validated in spike)
- **B:** Separate repo + submodule (more reusable, adds complexity)

**Spike validated:** Inline approach (option A)

**Recommendation:** Start with inline (option A)
- Simpler to migrate
- Can extract to separate repo later if needed
- Spike validated this approach

**Decision:** Recommend inline (user can override)

---

### Q3: Should we archive EZ-EMFI after migration?

**Options:**
- **A:** Archive (read-only, clear signal that monorepo is canonical)
- **B:** Keep active (allow parallel development)
- **C:** Delete (not recommended)

**Recommendation:** Archive after migration complete
- Add README: "Migrated to moku-custom-BPD"
- Tag final commit: `v1.0.0-final-before-migration`
- Archive on GitHub (read-only)

**Decision needed:** User preference

---

## 9. Summary

### Executive Decision Required

✅ **Approve architectural decisions** (all 4 spikes successful)
✅ **Approve monorepo name:** `moku-custom-BPD`
✅ **Schedule migration:** 9-13 hours across 4 phases
✅ **Answer open questions** (Q1-Q3 above)

### Ready to Execute

All architectural decisions validated. Path forward clear. Production monorepo structure defined. Team can proceed with confidence.

**Next action:** User approves → Assistant executes Phase 1 (create production repo)

---

**Status:** ✅ **READY FOR PRODUCTION MIGRATION**

**Confidence Level:** High (all spikes passed, validated approaches, clear path forward)

**Risk Level:** Low (spike methodology de-risked architecture, proven patterns)

---

**Document Version:** 1.0
**Date:** 2025-11-04
**Author:** Claude (AI assistant) based on spike results from moku-spike-redux
**Reviewed By:** Pending user review
