# START HERE: Branch Review Summary

**Branch:** `claude/review-bad-main-commit-011CUmSeqtepjpr5MAjxV2iF`
**Created:** 2025-11-03
**Purpose:** Architecture analysis and iteration planning for mono-repo refactor

---

## 📚 What This Branch Contains

This branch contains a comprehensive review of commit `b0cb32bb` (mono-repo refactor planning document) with three key documents:

### 1. `ARCHITECTURE_COMPARISON_ANALYSIS.md` (7,600 words)
**What it is:** Cross-repository comparison of EZ-EMFI vs moku-instrument-forge

**Key findings:**
- Planning doc underestimates complexity 3-4x (8-12h → 32-46h realistic)
- 7 critical architectural gaps identified
- Submodule path conflicts will break 47 Python files
- 10 risk matrix entries (only 2 addressed in original plan)

**When to read:** Review on dev laptop for full context (30 min read)

### 2. `FORGE_ARCHITECTURE_ANALYSIS.md` (6,800 words)
**What it is:** Deep-dive into moku-instrument-forge architecture patterns

**Key findings:**
- 5-agent system with clear boundaries (3,233 total lines)
- Single llms.txt entry point (not nested CLAUDE.md)
- Package contract pattern (manifest.json as source of truth)
- Git submodule patterns (all in `libs/`)
- Phase 6 documentation (28 production-ready files)

**When to read:** Reference when designing BPD architecture (30 min read)

### 3. `docs/MONO_REPO_ITERATION_PROMPT.md` (662 lines) ⭐ **START HERE**
**What it is:** Iterative design prompt for spike branch validation

**Contains:**
- Quick context summary (5 min read)
- 4 critical architectural decisions to validate
- Spike branch protocol (create → implement → validate → document)
- Complete example walkthrough (forge integration spike)
- 3-iteration design process (13-18h estimated)
- Next session checklist for dev laptop

**When to read:** First thing when picking up work on dev laptop

---

## 🎯 Quick Summary (What You Need to Know)

### The Problem
Original planning doc (commit `b0cb32bb`) proposes big-bang mono-repo migration but:
- ❌ Doesn't specify how forge integrates with BPD
- ❌ Doesn't design VHDL build orchestration
- ❌ Doesn't address submodule path conflicts
- ❌ Doesn't specify test infrastructure
- ❌ Underestimates time by 3-4x

### The Solution
**Iterative spike branch approach** to validate architecture before migration:

1. **Iteration 1:** Test 4 critical decisions via spike branches (6-8h)
2. **Iteration 2:** Integrate validated approaches (4-6h)
3. **Iteration 3:** Polish and document (3-4h)

**Total:** 13-18 hours with validated architecture

### Four Critical Decisions to Validate

| Decision | Options | Recommended First Spike |
|----------|---------|------------------------|
| **1. Forge Integration** | Submodule / Copy / External | `spike/forge-as-copy` |
| **2. VHDL Build** | Makefile / Python script / Test runner | `spike/test-runner-build` |
| **3. Test Infrastructure** | Centralized / Distributed / Pytest plugin | `spike/centralized-tests` |
| **4. Agent Boundaries** | Design-only / Design+Test / Full-cycle | `spike/design-test-agent` |

### Critical Questions Answered

**Q1: Should fsm_observer.vhd be in volo-platform-vhdl (generic utility) or probe-specific?**
- ✅ **Answer:** Generic utility in volo-platform-vhdl/debugging/
- ✅ **Rationale:** User-confirmed, forge docs recommend for "all custom VHDL instruments", used in 3+ modules
- ✅ **Also move:** volo_voltage_pkg.vhd → volo-platform-vhdl/packages/ (dependency)
- 📄 **Full analysis:** `docs/Q1_FSM_OBSERVER_PLACEMENT.md` (363 lines)
- 📅 **Answered:** 2025-11-03 (commit 8e92f1a)

---

## 🚀 Next Steps (Do These in Order)

### Step 1: Create Pull Request (Do Now on iPad)

**Option A: Click this link** (easiest)
```
https://github.com/sealablab/EZ-EMFI/pull/new/claude/review-bad-main-commit-011CUmSeqtepjpr5MAjxV2iF
```

**Option B: Manual on GitHub**
1. Go to https://github.com/sealablab/EZ-EMFI/pulls
2. Click "New pull request"
3. Base: `main`, Compare: `claude/review-bad-main-commit-011CUmSeqtepjpr5MAjxV2iF`
4. Click "Create pull request"

**PR Title:**
```
Architecture Analysis: Mono-Repo Refactor Review
```

**PR Description:** (scroll down to "PR Description Template" section below)

### Step 2: Review on Dev Laptop (Later)

When you're on your dev laptop with full development environment:

```bash
# Clone and setup
git clone --recurse-submodules https://github.com/sealablab/EZ-EMFI.git
cd EZ-EMFI
git checkout claude/review-bad-main-commit-011CUmSeqtepjpr5MAjxV2iF

# Quick context load (5 minutes)
cat docs/MONO_REPO_ITERATION_PROMPT.md | head -100

# Full context load (30 minutes, if needed)
# Read ARCHITECTURE_COMPARISON_ANALYSIS.md
# Read FORGE_ARCHITECTURE_ANALYSIS.md
# Read docs/MONO_REPO_ITERATION_PROMPT.md
```

### Step 3: Start First Spike (On Dev Laptop)

Follow the instructions in `docs/MONO_REPO_ITERATION_PROMPT.md`:

```bash
# Create first spike branch
git checkout -b spike/forge-as-copy

# Follow "Example: First Iteration" section
# Test forge integration (30-60 minutes)
# Document results (10 minutes)
# Commit or iterate
```

### Step 4: Iterate Until Validated (On Dev Laptop)

Create spike branches for each of the 4 decisions, validate, document, iterate.

**Expected:** 2-3 iterations total, 13-18 hours work

**Deliverable:** Validated architecture ready to implement

---

## 📝 PR Description Template

Copy/paste this into GitHub PR description:

```markdown
## Summary

Comprehensive architecture analysis of the mono-repo refactor planning document (commit b0cb32bb).

This PR adds systematic analysis documents and an iterative design prompt for refining the moku-custom-BPD mono-repo architecture.

## Documents Added

### 1. `ARCHITECTURE_COMPARISON_ANALYSIS.md` (7,600 words)
Cross-repository architectural comparison identifying critical gaps:
- Agent Architecture: 5 forge agents (3,233 lines) vs 3 EZ-EMFI agents (1,142 lines)
- Submodule Conflicts: Path inconsistencies will break 47 Python files
- Migration Risks: 10 major risks, only 2 addressed in original plan
- Time Estimate: 8-12h planned → 32-46h realistic (3-4x underestimate)

### 2. `FORGE_ARCHITECTURE_ANALYSIS.md` (6,800 words)
Deep-dive into moku-instrument-forge architecture patterns:
- 5-agent system with clear boundaries
- Single llms.txt entry point (not nested CLAUDE.md)
- Package contract: manifest.json as source of truth
- Git submodules: All in `libs/` (consistent paths)

### 3. `docs/MONO_REPO_ITERATION_PROMPT.md` (662 lines)
Iterative design prompt for spike branch validation:
- 4 critical architectural decisions with validation methods
- Spike branch protocol (create → validate → document → iterate)
- Complete example walkthrough
- 3-iteration process (13-18h estimated)

## Key Findings

### 🚨 Critical Gaps
1. Forge integration strategy not specified
2. VHDL build orchestration not designed
3. Submodule path conflicts not addressed
4. Test infrastructure design missing
5. Version pinning strategy undefined
6. Hardware validation workflow unspecified
7. CI/CD not designed

### ✅ Recommended Approach
**Iterative spike branch validation** instead of big-bang migration:
- Iteration 1: Validate 4 decisions (6-8h)
- Iteration 2: Integrate approaches (4-6h)
- Iteration 3: Polish & document (3-4h)
- **Total: 13-18h with validated architecture**

## Next Steps
1. Review analysis on dev laptop
2. Create spike branches to test decisions
3. Iterate until architecture validated
4. Execute migration with confidence

See `START_HERE.md` on branch for detailed instructions.
```

---

## 🔍 Quick Reference

### Commits on This Branch
- `d9aa8c5`: Added ARCHITECTURE_COMPARISON_ANALYSIS.md + FORGE_ARCHITECTURE_ANALYSIS.md
- `a7d6e79`: Added docs/MONO_REPO_ITERATION_PROMPT.md
- `[current]`: Added START_HERE.md (this file)

### Related Commits/Branches
- Original planning doc: `b0cb32bb` on `feature/BAD-main`
- moku-instrument-forge: https://github.com/sealablab/moku-instrument-forge @ `e036c2b`

### Key Files to Read (in order)
1. `START_HERE.md` (this file) - Branch overview
2. `docs/MONO_REPO_ITERATION_PROMPT.md` - Action plan
3. `ARCHITECTURE_COMPARISON_ANALYSIS.md` - Detailed gaps
4. `FORGE_ARCHITECTURE_ANALYSIS.md` - Reference architecture

---

## 💡 Why This Approach?

**Original Plan Issues:**
- Treated as "file reorganization" (8-12h estimate)
- Actually "architectural integration" (32-46h realistic)
- 7 critical decisions undefined
- High risk of needing to redo work

**Iterative Spike Approach Benefits:**
- Test each decision independently (low risk)
- Validate architecture before committing (high confidence)
- Document learnings as you go (reusable knowledge)
- Adjust approach based on validation results (adaptive)
- Total time: 13-18h (less than big-bang worst case)

**You're using the "measure twice, cut once" principle for architecture design.**

---

## ❓ FAQ

**Q: Do I need to read all 14,000+ words of analysis?**
A: No. Start with `docs/MONO_REPO_ITERATION_PROMPT.md` (quick context summary). Read full analysis only when you need deep context for a specific decision.

**Q: What if I don't have time for 13-18 hours of iteration?**
A: You can do iterations incrementally:
- Day 1: Spike Decision 1 (2-3h)
- Day 2: Spike Decision 2 (2-3h)
- Day 3: Spike Decisions 3+4 (3-4h)
- Day 4: Integration (4-6h)
- Day 5: Polish (3-4h)

**Q: Can I skip the spike branches and just implement?**
A: Not recommended. The 4 decisions are interdependent (e.g., forge integration affects build orchestration). Testing via spikes prevents costly rework.

**Q: What if a spike fails validation?**
A: That's the point! Try alternative approach, document why first approach didn't work. Much better to discover issues in a spike branch than mid-migration.

**Q: Can I work on this from iPad?**
A: For PR creation: Yes. For spike branch work: No (need full dev environment with GHDL, Python, etc.). Spike work requires dev laptop.

---

## 🎯 Success Criteria

You'll know the architecture is validated when:

✅ All 4 decisions have viable spike implementations
✅ End-to-end workflow tested (YAML → VHDL → compiled → tested)
✅ Agent boundaries documented (<800 lines per agent.md)
✅ Build time <2 minutes, test time <5 minutes
✅ Developer workflow is smooth (clone, install, build, test in <5 commands)

---

## 📞 If You Get Stuck

**On iPad (limited environment):**
- Review this README
- Read `docs/MONO_REPO_ITERATION_PROMPT.md` (doesn't require code execution)
- Create PR (web interface)
- Plan next steps (documenting thoughts)

**On Dev Laptop (full environment):**
- Load Claude Code with context: "I'm continuing mono-repo design, read docs/MONO_REPO_ITERATION_PROMPT.md"
- Reference specific sections: "Read Section 10 of ARCHITECTURE_COMPARISON_ANALYSIS.md"
- Ask for help: "I'm on spike/forge-as-copy and validation test 2 is failing"

---

**You're all set!** This README, the analysis docs, and the iteration prompt are all committed to git and pushed to the remote. You can safely close this session and pick up later - everything is saved.

**First thing to do:** Create the PR using the link/instructions above.

**When on dev laptop:** Read `docs/MONO_REPO_ITERATION_PROMPT.md` and start first spike.
