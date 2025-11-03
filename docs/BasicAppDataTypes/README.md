# BasicAppDataTypes Implementation

**Feature Branch:** `feature/BAD-main`
**Status:** Planning Complete, Implementation Pending
**Created:** 2025-11-02

## Overview

BasicAppDataTypes is a fundamental upgrade to the EZ-EMFI custom instrument architecture providing:
- Type-safe data serialization between Python and VHDL
- Automatic register mapping with 50-75% space savings
- Built-in support for voltage, time, and boolean types

## Git Workflow

### Branch Structure

```
main
└── feature/BAD-main (feature branch - YOU ARE HERE)
    ├── feature/BAD/P1 (phase 1: type system)
    ├── feature/BAD/P2 (phase 2: register mapping)
    ├── feature/BAD/P3 (phase 3: package model)
    ├── feature/BAD/P4 (phase 4: code generation)
    ├── feature/BAD/P5 (phase 5: testing)
    └── feature/BAD/P6 (phase 6: documentation)
```

### Workflow Summary

1. **Each phase gets its own branch** off `feature/BAD-main`
2. **Work is done on phase branch** with frequent commits
3. **Phase is merged back** to `feature/BAD-main` with merge commit (--no-ff)
4. **Repeat** for all 6 phases
5. **Final merge** to `main` when all phases complete

### Detailed Workflow

See [BAD_MASTER_Orchestrator.md](./BAD_MASTER_Orchestrator.md#git-workflow) for complete workflow details.

## Phase Overview

| Phase | Description | Branch | Files |
|-------|-------------|--------|-------|
| 1 | Core type system | `feature/BAD/P1` | `basic_app_datatypes.py` |
| 2 | Register mapping | `feature/BAD/P2` | `register_mapper.py` |
| 3 | Package model | `feature/BAD/P3` | `reg_package.py` |
| 4 | Code generation | `feature/BAD/P4` | Templates, generator |
| 5 | Testing | `feature/BAD/P5` | Test suite |
| 6 | Documentation | `feature/BAD/P6` | User guides |

## Starting a Phase

```bash
# From feature/BAD-main
git checkout feature/BAD-main
git checkout -b feature/BAD/P{N}

# Open the phase prompt
cat docs/BasicAppDataTypes/BAD_Phase{N}_*.md
```

## Completing a Phase

```bash
# Commit your work
git add .
git commit -m "feat(BAD/P{N}): Complete Phase {N} - <description>"

# Create completion summary
# Write docs/BasicAppDataTypes/BAD_Phase{N}_COMPLETE.md

# Merge to feature branch
git checkout feature/BAD-main
git merge --no-ff feature/BAD/P{N} -m "Merge Phase {N}: <description>"

# Update orchestrator status table
```

## Progress Tracking

Track progress in [BAD_MASTER_Orchestrator.md](./BAD_MASTER_Orchestrator.md#phase-status-tracker)

## Files

- `BAD_MASTER_Orchestrator.md` - Master index and workflow
- `BAD_Phase1_TypeSystem.md` - Phase 1 prompt
- `BAD_Phase2_RegisterMapping.md` - Phase 2 prompt
- `BAD_Phase3_RegPackage.md` - Phase 3 prompt
- `BAD_Phase4_CodeGeneration.md` - Phase 4 prompt
- `BAD_Phase5_Testing.md` - Phase 5 prompt
- `BAD_Phase6_Documentation.md` - Phase 6 prompt
- `BAD_Phase{N}_COMPLETE.md` - Generated phase summaries

## Quick Reference

```bash
# Check current phase status
git branch --list "feature/BAD/*"

# See what's merged
git log --oneline --graph feature/BAD-main

# View phase commits
git log --oneline --grep="feat(BAD/P"

# Start next phase
git checkout feature/BAD-main
git checkout -b feature/BAD/P{next}
```

## Notes

- Each phase prompt is self-contained and can run in fresh Claude session
- Phase summaries cascade forward (each reads previous summaries)
- Merge commits preserve phase history
- Status tracked in orchestrator

---

**Next Action:** Start Phase 1 - See `BAD_Phase1_TypeSystem.md`
