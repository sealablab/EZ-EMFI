# moku-instrument-forge: Comprehensive Architecture Analysis

**Repository:** https://github.com/sealablab/moku-instrument-forge
**Analysis Date:** 2025-11-03
**Branches Examined:** main (latest: e036c2b)

---

## Executive Summary

**moku-instrument-forge** is a mature, production-ready code generation platform that transforms YAML specifications into deployable Moku custom instruments. It demonstrates **architectural best practices** for:
- Multi-agent AI systems (5 specialized agents)
- Git submodule composition (3 external libraries)
- Documentation-driven development (28 reference docs)
- Type-safe code generation (25 types, Pydantic validation)

**Key Metrics:**
- **Codebase:** 157 files, ~15,000 LOC (Python + VHDL)
- **Tests:** 69 passing (100% coverage on critical paths)
- **Agents:** 5 agents, 3,233 total lines of context
- **Documentation:** 28 markdown files, production-ready
- **Submodules:** 3 (basic-app-datatypes, moku-models, riscure-models)

---

## 1. Repository Structure

### 1.1 High-Level Organization

```
moku-instrument-forge/
├── forge/                    # Core generation engine (Python)
│   ├── generator/            # YAML → VHDL codegen (5 modules)
│   ├── models/               # Pydantic models (10 files)
│   ├── templates/            # Jinja2 VHDL templates (3 files)
│   ├── vhdl/                 # Frozen VHDL type packages
│   └── tests/                # Test suite (1,789 LOC, 69 tests)
│
├── libs/                     # Git submodules (external dependencies)
│   ├── basic-app-datatypes/  # Type system (25 types)
│   ├── moku-models/          # Platform specs (Go/Lab/Pro/Delta)
│   └── riscure-models/       # Probe hardware specs
│
├── platform/                 # Moku VHDL infrastructure
│   ├── common/               # Shared VHDL packages
│   └── loader/               # BRAM loaders
│
├── apps/                     # Generated applications
│   └── DS1140_PD/            # Example EMFI probe
│       ├── spec/             # YAML specification
│       │   └── DS1140_PD_app.yaml
│       ├── generated/        # Generated VHDL
│       │   ├── DS1140_PD_custom_inst_shim.vhd
│       │   └── DS1140_PD_custom_inst_main.vhd
│       └── README.md         # App-specific docs
│
├── docs/                     # Documentation (28 files, 12,000+ words)
│   ├── architecture/         # Design docs (5 files)
│   ├── reference/            # API docs (6 files)
│   ├── guides/               # User guides (6 files)
│   ├── examples/             # Walkthroughs (3 files)
│   └── debugging/            # Debug guides (1 file)
│
├── .claude/                  # Agent system (AI-optimized)
│   ├── agents/               # 5 specialized agents
│   │   ├── forge-context/
│   │   ├── deployment-context/
│   │   ├── docgen-context/
│   │   ├── hardware-debug-context/
│   │   └── workflow-coordinator/
│   ├── commands/             # 6 slash commands
│   │   ├── forge.md
│   │   ├── deployment.md
│   │   ├── debug.md
│   │   ├── docgen.md
│   │   ├── workflow.md
│   │   └── platform.md
│   └── shared/               # Shared knowledge files
│       ├── package_contract.md
│       ├── type_system_quick_ref.md
│       ├── riscure_probe_integration.md
│       └── SERENA_MIGRATION_ASSESSMENT.md
│
├── .github/workflows/        # CI/CD (GitHub Actions)
├── scripts/                  # Utility scripts
├── llms.txt                  # Root-level AI context (319 lines)
├── README.md                 # Project overview (546 lines)
└── pyproject.toml            # Python package config
```

### 1.2 Key Characteristics

**Domain:** Pure Python code generation (no VHDL compilation in main repo)
**Build System:** uv workspace with git submodules
**Test Framework:** pytest (Python only, no CocotB)
**CI/CD:** GitHub Actions (test.yml, not yet active)
**Documentation Strategy:** Comprehensive markdown (28 files)

---

## 2. Agent System Architecture

### 2.1 Agent Overview

**5 Specialized Agents (3,233 total lines):**

| Agent | Lines | Purpose | Scope |
|-------|-------|---------|-------|
| **forge-context** | 753 | YAML → Package generation | Read/write `forge/`, `apps/`, read-only `libs/` |
| **docgen-context** | 820 | Package → Docs/UI/APIs | Read-only package dir, write `apps/*/docs/` |
| **hardware-debug-context** | 646 | FSM debugging via oscilloscope | Read-only everything, hardware monitoring |
| **deployment-context** | 556 | Package → Deployed hardware | Read-only package, write to Moku device |
| **workflow-coordinator** | 458 | Orchestrates multi-stage workflows | Calls other agents, no direct file I/O |

**Total Agent Content:** 3,233 lines (average 647 lines/agent)

### 2.2 Agent Boundaries (from forge-context/agent.md)

```markdown
### ✅ Read & Write Access
- `forge/generator/` - Code generation engine
- `forge/models/` - Pydantic models
- `forge/templates/` - Jinja2 templates
- `forge/tests/` - Test suite
- `apps/*/*.yaml` - Application specifications
- `apps/*/` - Generated package directories

### ✅ Read-Only Access
- `libs/basic-app-datatypes/` - Type system (25 types)
- `libs/moku-models/` - Platform specifications
- `forge/vhdl/` - Frozen VHDL type packages

### ❌ No Write Access
- `libs/` - External submodules (submit PRs upstream)
- Deployment scripts (use deployment-context)
- Hardware testing (use hardware-debug-context)
```

**Key Design Pattern:** Strict read/write boundaries prevent agent scope creep.

### 2.3 Slash Commands → Agent Mapping

| Command | Agent | Description |
|---------|-------|-------------|
| `/workflow new-probe` | workflow-coordinator | Full pipeline (validate → generate → deploy → docs) |
| `/generate` | forge-context | YAML → Package generation |
| `/validate` | forge-context | YAML schema validation |
| `/map-registers` | forge-context | Show register packing analysis |
| `/deploy` | deployment-context | Package → Moku hardware |
| `/discover` | deployment-context | Find Moku devices on network |
| `/gen-docs` | docgen-context | Generate markdown documentation |
| `/gen-ui` | docgen-context | Generate Textual TUI |
| `/gen-python-api` | docgen-context | Generate Python API classes |
| `/debug-fsm` | hardware-debug-context | FSM state monitoring |
| `/monitor-state` | hardware-debug-context | Live FSM transitions |

**Pattern:** Each slash command loads a specific agent context via `.claude/commands/*.md`.

---

## 3. Documentation Architecture

### 3.1 llms.txt Strategy - CORRECTED

**Multi-Layer llms.txt Architecture (4 files total)**

**CORRECTION:** moku-instrument-forge uses **progressive disclosure across repositories** with llms.txt files in BOTH root AND submodules:

```
moku-instrument-forge/
├── llms.txt (319 lines)                          # Main entry point
└── libs/
    ├── basic-app-datatypes/llms.txt (237 lines)  # Type system reference
    ├── moku-models/llms.txt (147 lines)          # Platform specs
    └── riscure-models/llms.txt (187 lines)       # Probe specifications
```

**Root llms.txt (319 lines) - Main Entry Point:**

1. **Quick Reference** (lines 1-55)
   - What is this?
   - Core workflow diagram
   - Agent system overview
   - Package contract
   - Common commands

2. **Type System** (lines 57-76)
   - BasicAppDataTypes overview
   - Most common types
   - **Links to authoritative sources** (points to submodule llms.txt!)

3. **Register Mapping** (lines 78-113)
   - Automatic packing strategies
   - Example efficiency analysis
   - Visual register layout

4. **Platform Support** (lines 115-125)
   - Moku Go/Lab/Pro/Delta comparison table

5. **Documentation Map** (lines 127-200)
   - User guides
   - Debugging guides
   - Agent system references
   - API documentation

6. **Project Structure** (lines 152-178)
   - Full directory tree
   - Purpose of each directory

7. **Dependencies** (lines 180-198)
   - Core Python dependencies
   - Submodule versions
   - Optional deployment tools

8. **Design Principles** (lines 200-208)
   - Type safety
   - Automatic packing
   - Platform agnostic
   - Context isolation
   - Package contract

9. **Common Tasks** (lines 210-293)
   - Create new instrument workflow
   - Deploy to hardware
   - Debug FSM
   - Generate documentation

10. **Examples & Troubleshooting** (lines 271-319)
    - Minimal YAML spec
    - Common error messages

**Key Pattern:** Root llms.txt serves as **entry point**, then **delegates** to submodule llms.txt for domain-specific details (e.g., "complete type catalog at libs/basic-app-datatypes/llms.txt").

### 3.2 Nested CLAUDE.md Strategy - CORRECTED

**CORRECTION:** moku-instrument-forge **DOES** use nested CLAUDE.md files in submodules!

**Actual Documentation Hierarchy:**
```
moku-instrument-forge/
├── llms.txt                              # Entry point (AI-optimized)
├── README.md                             # Human entry point
├── .claude/                              # Root agent system
│   ├── agents/*.md                       # Agent contexts
│   ├── commands/*.md                     # Slash commands
│   └── shared/*.md                       # Shared knowledge
├── docs/                                 # Project documentation
│   ├── README.md                         # Documentation index
│   ├── architecture/*.md                 # Design docs
│   ├── reference/*.md                    # API reference
│   ├── guides/*.md                       # User guides
│   └── examples/*.md                     # Walkthroughs
└── libs/                                 # SUBMODULES (each with own docs!)
    ├── basic-app-datatypes/
    │   ├── llms.txt                      # Type system quick ref
    │   └── .claude/commands/library.md   # Library context
    ├── moku-models/
    │   ├── llms.txt                      # Platform specs quick ref
    │   ├── CLAUDE.md (260 lines!)        # Full submodule context
    │   └── .claude/settings.local.json   # Claude settings
    └── riscure-models/
        ├── llms.txt                      # Probe specs quick ref
        └── CLAUDE.md (255 lines!)        # Full submodule context
```

**Contrast with EZ-EMFI:**
- **EZ-EMFI:** Top-level `CLAUDE.md` + slash commands load additional context
- **forge:** NO root `CLAUDE.md`, BUT submodules have their own CLAUDE.md
- **Pattern:** Progressive disclosure ACROSS repository boundaries

**Architectural Advantage:**
- Root `llms.txt` is concise entry point (319 lines)
- Submodules have full context docs (CLAUDE.md) for deep work
- Each submodule is self-documenting (can be used standalone)
- No context ambiguity at each level

### 3.3 Documentation Layers - CORRECTED

**Layer 1: AI Entry Point (Root)**
- `llms.txt` (319 lines, ultra-concise)
- Purpose: Bootstrap AI understanding in <2 minutes
- Pattern: Points to submodule docs for details

**Layer 2: Submodule Quick References**
- `libs/basic-app-datatypes/llms.txt` (237 lines) - Complete type catalog
- `libs/moku-models/llms.txt` (147 lines) - Platform specs summary
- `libs/riscure-models/llms.txt` (187 lines) - Probe specs summary
- Purpose: Domain-specific quick references

**Layer 3: Submodule Deep Context**
- `libs/moku-models/CLAUDE.md` (260 lines) - Full platform model guide
- `libs/riscure-models/CLAUDE.md` (255 lines) - Full probe integration guide
- `libs/basic-app-datatypes/.claude/commands/library.md` (81 lines) - Library context
- Purpose: Deep dive into submodule architecture and usage

**Layer 4: Root Agent Contexts**
- `.claude/agents/*/agent.md` (5 files, 3,233 lines total)
- Purpose: Deep domain expertise for forge-specific tasks

**Layer 5: Shared Knowledge**
- `.claude/shared/*.md` (4 files)
- Purpose: Cross-agent reference docs (type system, package contract)

**Layer 6: User Documentation**
- `docs/**/*.md` (28 files, ~12,000 words)
- Purpose: Human-readable guides, references, examples

**Layer 7: App-Specific Docs**
- `apps/DS1140_PD/README.md` (66 lines)
- Purpose: Generated application documentation

**Key Pattern:** **Progressive disclosure ACROSS repository boundaries** - start with root llms.txt, delegate to submodule docs for domain details, drill down to CLAUDE.md for deep work.

### 3.4 Submodule Documentation Details

**basic-app-datatypes (Type System Library):**
```
libs/basic-app-datatypes/
├── llms.txt (237 lines)                # Complete type catalog
│   ├── 23 type definitions with bit widths
│   ├── Conversion formulas
│   ├── Platform-aware serialization examples
│   └── Usage patterns
└── .claude/
    └── commands/library.md (81 lines)  # Library development context
```

**Key Content:** Authoritative source for all 23 BasicAppDataTypes, including voltage types (12), time types (10), and boolean (1). Root llms.txt references this as "complete type catalog."

**moku-models (Platform Specifications):**
```
libs/moku-models/
├── llms.txt (147 lines)                # Quick platform reference
│   ├── Core models (MokuConfig, SlotConfig)
│   ├── Platform comparison table
│   ├── Basic usage patterns
│   └── Links to full docs
├── CLAUDE.md (260 lines)               # Full development guide
│   ├── Detailed model documentation
│   ├── Multi-slot configuration examples
│   ├── Routing validation workflows
│   ├── Integration with parent projects
│   └── Development workflow
└── .claude/
    └── settings.local.json             # Claude Code settings
```

**Key Content:** Complete Pydantic models for Moku Go/Lab/Pro/Delta platforms, used by both EZ-EMFI (parent project in CLAUDE.md) and moku-instrument-forge (git submodule).

**riscure-models (Probe Hardware Specifications):**
```
libs/riscure-models/
├── llms.txt (187 lines)                # Quick probe reference
│   ├── DS1120A port summary
│   ├── Voltage compatibility checking
│   ├── Typical wiring patterns
│   └── Integration examples
└── CLAUDE.md (255 lines)               # Full integration guide
    ├── Complete port specifications
    ├── Voltage safety validation
    ├── Moku platform integration
    ├── Development workflow
    └── Future enhancements roadmap
```

**Key Content:** Riscure DS1120A/DS1121A probe models for voltage-safe wiring validation with Moku platforms.

**Documentation Philosophy:**
- **llms.txt**: Fast lookup for common tasks (<5 min read)
- **CLAUDE.md**: Deep context for development work (15-30 min read)
- **Standalone**: Each submodule can be used independently in other projects

---

## 4. Git Submodules

### 4.1 Submodule Configuration

```ini
[submodule "libs/basic-app-datatypes"]
    path = libs/basic-app-datatypes
    url = https://github.com/sealablab/basic-app-datatypes.git
    branch = main

[submodule "libs/moku-models"]
    path = libs/moku-models
    url = https://github.com/sealablab/moku-models.git
    branch = main

[submodule "libs/riscure-models"]
    path = libs/riscure-models
    url = https://github.com/sealablab/riscure-models.git
    branch = main
```

**Key Characteristics:**
- All submodules in `libs/` directory (consistent path structure)
- All track `main` branch (not pinned to specific commits)
- All from same GitHub org (sealablab)

### 4.2 Submodule Roles

**basic-app-datatypes (Type System)**
- **Purpose:** 25 type definitions (voltage, time, boolean)
- **Exports:** `BasicAppDataTypes` enum, type converters, type registry
- **Dependencies:** Zero (standalone library)
- **Documentation:** `llms.txt` (authoritative type catalog)
- **Used By:** forge/generator, forge/models, apps/*/generated VHDL

**moku-models (Platform Specifications)**
- **Purpose:** Hardware specs for Moku Go/Lab/Pro/Delta
- **Exports:** `MokuConfig`, `SlotConfig`, routing patterns
- **Dependencies:** Pydantic
- **Documentation:** `MOKU_PLATFORM_SPECIFICATIONS.md`, `routing_patterns.md`
- **Used By:** deployment-context, platform-aware code generation

**riscure-models (Probe Hardware)**
- **Purpose:** Riscure FI/SCA probe specifications
- **Exports:** Probe datasheets, voltage validation models
- **Dependencies:** Pydantic
- **Documentation:** `docs/probes/*.md`
- **Used By:** hardware-debug-context, voltage clamping logic

### 4.3 Dependency Graph

```
moku-instrument-forge (root)
├─── forge/generator/          → basic-app-datatypes (type resolution)
├─── forge/models/             → basic-app-datatypes (Pydantic models)
├─── deployment-context/       → moku-models (platform specs)
│                              → basic-app-datatypes (type conversion)
├─── hardware-debug-context/   → riscure-models (probe specs)
│                              → moku-models (platform limits)
└─── docgen-context/           → basic-app-datatypes (API generation)
```

**Critical Insight:** All submodules are **read-only** from forge's perspective. Changes require upstream PRs.

---

## 5. Package Contract (manifest.json)

### 5.1 Contract Purpose

**From `.claude/shared/package_contract.md`:**

> **Key Principle:** Downstream contexts should NOT need to parse YAML or understand the forge generation pipeline. The package provides all necessary metadata in JSON format.

**Package Directory Structure:**
```
apps/<app_name>/
├── <app_name>_custom_inst_shim.vhd     # Generated VHDL shim
├── <app_name>_custom_inst_main.vhd     # Generated VHDL main template
├── manifest.json                        # Package metadata (REQUIRED)
├── control_registers.json               # Initial CR values (REQUIRED)
└── <app_name>.yaml                      # Original spec (OPTIONAL)
```

**Required Files:**
1. `manifest.json` - Complete package metadata
2. `control_registers.json` - Initial CR6-CR15 values

**Optional Files:**
- `*.vhd` - VHDL source (for reference, not parsed by downstream)
- `*.yaml` - Original spec (for reference)

### 5.2 manifest.json Schema (Partial)

```json
{
  "app_name": "DS1140_PD",
  "version": "1.0.0",
  "platform": "moku_go",
  "datatypes": [
    {
      "name": "intensity",
      "datatype": "voltage_output_05v_s16",
      "default_value": 3000,
      "bit_width": 16
    },
    // ... 7 more signals
  ],
  "register_mappings": {
    "CR6": {
      "signals": [
        {"name": "arm_timeout", "bits": "31:16"},
        {"name": "intensity", "bits": "15:0"}
      ]
    },
    // ... CR7, CR8
  },
  "efficiency_stats": {
    "bits_used": 67,
    "bits_available": 96,
    "efficiency_pct": 69.8
  },
  "generated_at": "2025-11-03T10:33:35Z"
}
```

**Key Design Decision:** manifest.json is the **source of truth** for all downstream consumers.

---

## 6. Code Generation Pipeline

### 6.1 Generation Workflow

```
User YAML Spec
      │
      ▼
┌─────────────────────┐
│ Pydantic Validation │  (forge/models/yaml_spec.py)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Type Resolution     │  (basic-app-datatypes registry)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Register Packing    │  (forge/generator/register_mapper.py)
│  - first_fit        │  3 packing strategies
│  - best_fit         │
│  - type_clustering  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ VHDL Generation     │  (forge/generator/vhdl_generator.py)
│  - Jinja2 templates │  (forge/templates/*.j2)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Package Assembly    │  (forge/generator/package_assembler.py)
│  - manifest.json    │
│  - control_registers.json
│  - *.vhd files      │
└─────────────────────┘
```

### 6.2 Template System

**Jinja2 Templates (3 files):**

1. **shim_template.vhd.j2** (Shim Layer)
   - Maps Control Registers to friendly signal names
   - Auto-generated, DO NOT EDIT
   - Example: `CR6[31:16]` → `arm_timeout`

2. **main_template.vhd.j2** (Main Template)
   - Application logic skeleton
   - User edits this file to add FSM/logic
   - Includes signal declarations from type system

3. **package_template.vhd.j2** (Type Package)
   - VHDL type definitions from BasicAppDataTypes
   - Voltage converters, time converters
   - Frozen at v1.0.0 (not regenerated)

**Key Insight:** Only shim/main regenerated per app, type package is stable.

---

## 7. Testing Strategy

### 7.1 Test Structure

```
forge/tests/                         (1,789 LOC)
├── test_generator.py                # Code generation (16 tests)
├── test_integration.py              # End-to-end (9 tests)
├── test_models.py                   # Pydantic validation
├── test_packing.py                  # Register packing algorithms
└── fixtures/
    ├── minimal_spec.yaml
    ├── multi_channel_spec.yaml
    └── expected_outputs/
```

**Test Coverage:**
- **Unit Tests:** Individual functions (type resolution, register packing)
- **Integration Tests:** Full YAML → Package workflow
- **Validation Tests:** Pydantic schema enforcement
- **Golden Tests:** Compare generated VHDL to known-good outputs

**Total:** 69 tests passing (100% on critical paths)

### 7.2 Test Philosophy

**From test suite analysis:**
- No CocotB (VHDL simulation) in forge repo
- Pure Python testing (pytest)
- Fast (<10s for full suite)
- No hardware dependencies
- Golden file comparison for VHDL output

**Contrast with EZ-EMFI:**
- EZ-EMFI has CocotB tests (VHDL simulation)
- Slow (~2-5 minutes for full suite)
- Requires GHDL installation

**Architectural Lesson:** Forge delegates VHDL testing to consumer repos (like EZ-EMFI).

---

## 8. Recent Documentation (Phase 6)

### 8.1 Documentation Generation Phase

**Timeline:** Phase 6 completed on 2025-11-03 (commit e036c2b)

**Generated Documentation:**
```
docs/
├── README.md                        # Documentation index (185 lines)
├── architecture/                    # 5 files
│   ├── overview.md                  # System architecture
│   ├── code_generation.md           # Generator internals
│   ├── agent_system.md              # 5 agents explained
│   ├── submodule_integration.md     # Forge ↔ libs boundaries
│   └── design_decisions.md          # Design rationale
├── reference/                       # 6 files
│   ├── type_system.md               # BasicAppDataTypes guide
│   ├── yaml_schema.md               # YAML v2.0 spec
│   ├── register_mapping.md          # Packing algorithms
│   ├── manifest_schema.md           # manifest.json spec
│   ├── vhdl_generation.md           # Code generation pipeline
│   └── python_api.md                # Pydantic models
├── guides/                          # 6 files (user-facing)
│   ├── getting_started.md           # 30-min tutorial
│   ├── user_guide.md                # Comprehensive usage
│   ├── yaml_guide.md                # Writing YAML specs
│   ├── deployment_guide.md          # Hardware deployment
│   ├── migration_guide.md           # Manual → forge migration
│   └── troubleshooting.md           # Common issues
├── examples/                        # 3 files
│   ├── minimal_walkthrough.md       # 3-signal example
│   ├── multi_channel_walkthrough.md # 6-signal example
│   └── common_patterns.md           # Best practices
└── debugging/                       # 1 file
    └── fsm_observer_pattern.md      # FSM debugging
```

**Total Documentation:** 28 markdown files, ~12,000 words

### 8.2 Documentation Quality

**Characteristics:**
- Comprehensive (covers all use cases)
- Example-driven (walkthroughs for each feature)
- Reference-complete (every Pydantic model documented)
- Troubleshooting-focused (common errors + solutions)
- Architecture-explained (design rationale for all decisions)

**Example: docs/guides/getting_started.md structure:**
1. Prerequisites (tools, knowledge)
2. Installation (git clone + uv sync)
3. Quick validation (verify install)
4. First instrument (minimal YAML)
5. Generate package (run forge)
6. Verify output (check manifest.json)
7. Next steps (deployment, docs generation)

**Estimated reading time:** 30 minutes (per design goal)

---

## 9. Design Patterns & Principles

### 9.1 Core Principles (from llms.txt)

1. **Type Safety**
   - Pydantic validation catches errors before hardware deployment
   - Compile-time type checking via BasicAppDataTypes enum
   - Default value range validation

2. **Automatic Register Packing**
   - 50-75% efficiency vs manual allocation
   - Three strategies (first_fit, best_fit, type_clustering)
   - Automated bit-level packing

3. **Platform Agnostic**
   - Same YAML works on Go/Lab/Pro/Delta
   - Platform-specific details in moku-models submodule
   - No platform conditionals in user YAML

4. **Context Isolation**
   - Clean agent boundaries
   - Minimal context pollution
   - Read-only external dependencies

5. **Package Contract**
   - manifest.json is source of truth
   - No downstream YAML parsing
   - Stable JSON schema

### 9.2 Architectural Patterns

**Pattern 1: Agent as Domain Expert**
- Each agent owns a specific workflow stage
- Agents don't call other agents directly (via workflow-coordinator)
- Strict read/write boundaries enforced

**Pattern 2: Git Submodules for Libraries**
- External dependencies as submodules
- All submodules read-only from forge perspective
- Version pinning via git commits (not package managers)

**Pattern 3: JSON as Integration Layer**
- manifest.json decouples generation from consumption
- Stable schema enables independent evolution
- Human-readable + machine-parseable

**Pattern 4: Progressive Disclosure Documentation**
- llms.txt (entry point, 319 lines)
- Agent contexts (domain-specific, 500-800 lines each)
- Full docs (comprehensive, 12,000+ words)

**Pattern 5: Template-Driven Code Generation**
- Jinja2 templates for VHDL generation
- Golden file testing for output validation
- Template versioning independent of generator logic

---

## 10. Key Takeaways for moku-custom-BPD Migration

### 10.1 What EZ-EMFI Can Learn from Forge

1. **Multi-Layer llms.txt Strategy**
   - Root llms.txt as main entry point (concise, <400 lines)
   - Submodule llms.txt for domain-specific quick refs
   - CLAUDE.md in submodules for deep context (when needed)
   - Use slash commands for context loading (progressive disclosure)

2. **Strict Agent Boundaries**
   - Define read/write scopes explicitly
   - Prevent agent scope creep via documentation

3. **Package Contract Pattern**
   - Define JSON schemas for inter-component communication
   - Avoid parsing complex formats (YAML) in multiple places

4. **Progressive Disclosure Docs**
   - Start with quick reference (< 400 lines)
   - Drill down to agent contexts (500-800 lines)
   - Full docs for deep dives (thousands of lines)

5. **Submodule Consistency**
   - All submodules in `libs/` directory
   - Consistent path structure reduces import confusion

### 10.2 What Forge Does NOT Have (That BPD Needs)

1. **VHDL Build Orchestration**
   - Forge generates VHDL but doesn't compile it
   - BPD needs: Makefile or build script for GHDL
   - **Missing in planning doc**

2. **CocotB Test Infrastructure**
   - Forge has pytest (Python only)
   - BPD needs: CocotB runner, test fixtures, VHDL simulation
   - **Partially addressed in planning doc (Q3)**

3. **VHDL Utilities as Code**
   - Forge has frozen VHDL type packages (static)
   - BPD needs: Evolving VHDL utilities (volo_*, ds1120_pd_*)
   - **Addressed in planning doc (volo-platform-vhdl submodule)**

4. **Hardware Validation Workflow**
   - Forge deployment-context assumes firmware works
   - BPD needs: Oscilloscope validation, FSM debugging, iterative testing
   - **Not addressed in planning doc**

5. **TUI Application Development**
   - Forge docgen-context generates TUI skeletons
   - BPD needs: Full TUI apps with runtime state management
   - **Not addressed in planning doc**

### 10.3 Critical Architectural Gaps in BPD Planning Doc

| Gap | Forge Has? | EZ-EMFI Has? | BPD Needs? | Planning Doc Coverage |
|-----|-----------|--------------|------------|----------------------|
| **Forge integration strategy** | N/A | ❌ No | ✅ Yes | ❌ Not specified |
| **VHDL build orchestration** | ❌ No | ✅ Yes (tests/run.py) | ✅ Yes | ❌ Not specified |
| **CocotB test runner** | ❌ No | ✅ Yes (tests/run.py) | ✅ Yes | ⚠️ Q3 asks but no design |
| **Submodule path normalization** | ✅ Yes (libs/*) | ⚠️ Inconsistent | ✅ Yes | ❌ Not mentioned |
| **Package contract for VHDL** | ✅ Yes (manifest.json) | ❌ No | ✅ Yes | ❌ Not mentioned |
| **Hardware validation workflow** | ⚠️ Partial | ✅ Yes (.serena/memories/) | ✅ Yes | ❌ Not mentioned |
| **Version pinning strategy** | ⚠️ Implicit (git) | ❌ No | ✅ Yes | ❌ Not mentioned |

**Summary:** Planning doc focuses on file reorganization but misses **7 critical architectural integration points**.

---

## 11. Forge Architecture Scorecard

### Strengths

✅ **Clear Domain Boundaries:** Each agent has well-defined read/write scopes
✅ **Composable Design:** Git submodules enable independent library evolution
✅ **Type Safety:** Pydantic + BasicAppDataTypes catch errors early
✅ **Documentation Maturity:** 28 comprehensive docs, production-ready
✅ **Test Coverage:** 69 tests, fast suite (<10s)
✅ **Package Contract:** JSON decouples generation from consumption
✅ **Progressive Disclosure:** llms.txt → agents → full docs

### Limitations (Not Weaknesses)

⚠️ **Pure Code Generation:** Doesn't handle VHDL compilation/simulation
⚠️ **No Hardware Validation:** Assumes generated firmware works
⚠️ **Python-Only Tests:** No CocotB/VHDL validation
⚠️ **Deployment Conceptual:** CloudCompile integration not implemented
⚠️ **Submodules Not Pinned:** Tracks `main` branch (not specific commits)

**Note:** These are **intentional design choices**, not flaws. Forge delegates VHDL testing to consumer repos.

---

## 12. Recommendations for BPD Refactor

### 12.1 ADOPT from Forge

1. ✅ **Agent Architecture**
   - Use forge's 5-agent pattern as template
   - Adapt forge-context → probe-design-context
   - Reuse deployment-context, hardware-debug-context as-is

2. ✅ **Multi-Layer Documentation Strategy**
   - Root llms.txt as concise entry point (<400 lines)
   - Submodule llms.txt for domain quick refs
   - Submodule CLAUDE.md for deep context (moku-models pattern)
   - Progressive disclosure across repository boundaries

3. ✅ **Submodule Path Consistency**
   - Move all submodules to `libs/`
   - Follow pattern: `libs/basic-app-datatypes/`, `libs/moku-models/`, `libs/volo-platform-vhdl/`
   - Each submodule self-documents (llms.txt + optional CLAUDE.md)

4. ✅ **Package Contract Pattern**
   - Define JSON schemas for VHDL utilities
   - Example: `volo_utilities_manifest.json` with available utilities, interfaces

5. ✅ **Progressive Disclosure Docs**
   - Root llms.txt (~300-400 lines)
   - Submodule llms.txt (quick refs, ~150-250 lines each)
   - Submodule CLAUDE.md (deep dive, ~250-300 lines when needed)
   - Agent contexts (500-800 lines each)
   - Full guides (as needed)

### 12.2 ADAPT from Forge (Don't Copy Directly)

1. ⚠️ **Agent Boundaries**
   - Forge: forge-context (Python code gen)
   - BPD: probe-design-context (VHDL + CocotB)
   - **Adaptation needed:** Add VHDL compilation + test execution to scope

2. ⚠️ **Test Infrastructure**
   - Forge: pytest (fast, Python-only)
   - BPD: pytest + CocotB (slow, VHDL simulation)
   - **Adaptation needed:** Hybrid test runner

3. ⚠️ **Deployment Context**
   - Forge: deployment-context (deploy package)
   - BPD: deployment-context + hardware-validation-context
   - **Adaptation needed:** Add oscilloscope validation workflow

### 12.3 EXTEND Beyond Forge

1. **VHDL Build Orchestration**
   - Forge doesn't need this (no VHDL compilation)
   - BPD needs: Makefile or `scripts/build_vhdl.py`
   - **New component:** build-context agent?

2. **Hardware Validation Workflow**
   - Forge assumes deployment works
   - BPD needs: Deploy → Validate → Debug loop
   - **New component:** Enhance hardware-debug-context

3. **TUI Application Development**
   - Forge generates TUI skeletons
   - BPD needs: Full TUI apps with state management
   - **New component:** tui-dev-context agent?

---

## 13. Summary

### moku-instrument-forge is a **mature, well-architected code generation platform** that demonstrates:

✅ **Clean separation of concerns** (5 agents, clear boundaries)
✅ **Composable design** (3 git submodules, stable interfaces)
✅ **Comprehensive documentation** (28 files, production-ready)
✅ **Type-safe code generation** (Pydantic + BasicAppDataTypes)
✅ **Progressive disclosure** (llms.txt → agents → full docs)

### Key Architectural Insights:

1. **Multi-layer documentation strategy** (root llms.txt → submodule llms.txt → submodule CLAUDE.md)
2. **Package contract pattern** (manifest.json as source of truth)
3. **Agent boundaries enforced via documentation** (read/write scopes)
4. **Git submodules for libraries** (all in `libs/`, each self-documenting)
5. **Delegates VHDL testing to consumer repos** (forge is pure Python)
6. **Progressive disclosure across repo boundaries** (each submodule standalone)

### For moku-custom-BPD Migration:

**ADOPT:** Agent architecture, llms.txt, submodule consistency, package contract
**ADAPT:** Agent scopes (add VHDL compilation), test infrastructure (add CocotB)
**EXTEND:** Build orchestration, hardware validation, TUI development

**Critical Gap:** Planning doc underestimates integration complexity by treating forge as "just copy agents." Reality: Need to design **build orchestration + test infrastructure** from scratch (not present in forge).

---

**Analysis Complete: 2025-11-03**
**Repositories Cross-Referenced:**
- moku-instrument-forge @ e036c2b (main)
- EZ-EMFI @ b0cb32b (feature/BAD-main)

**Next Steps:**
1. Answer: How should forge integrate with BPD? (submodule, copy, external tool?)
2. Design: VHDL build orchestration system for BPD
3. Design: CocotB test runner integration with agent system
4. Prototype: volo-platform-vhdl submodule structure

