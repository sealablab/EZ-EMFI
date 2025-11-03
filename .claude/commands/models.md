# Moku Models Development Mode

You are now in **moku-models submodule development mode**.

---

## Submodule Context

**Location**: `moku-models/` (git submodule)
**Repository**: `github.com/sealablab/moku-models`
**Purpose**: Pydantic data models for Moku platform deployment and configuration

**IMPORTANT**: Work within the `moku-models/` directory. This is a **separate git repository**.

---

## Quick Reference

**All 4 Moku Platforms Supported:**
```python
from moku_models import (
    MOKU_GO_PLATFORM,     # 2 slots, 2 I/O, 125 MHz, 16 DIO
    MOKU_LAB_PLATFORM,    # 2 slots, 2 I/O, 500 MHz, no DIO
    MOKU_PRO_PLATFORM,    # 4 slots, 4 I/O, 1.25 GHz, no DIO
    MOKU_DELTA_PLATFORM   # 3 slots, 8 I/O, 5 GHz, 32 DIO (flagship)
)
```

**Core Models:**
- `MokuConfig` - THE central deployment abstraction
- `SlotConfig` - Per-slot instrument configuration
- `MokuConnection` - Signal routing between ports/slots
- `MokuDeviceInfo` / `MokuDeviceCache` - Device discovery

---

## Key Documentation

**Within Submodule:**
- `moku-models/CLAUDE.md` - **Read this first** for AI context
- `moku-models/llms.txt` - Quick reference for LLMs
- `moku-models/README.md` - Installation and usage
- `moku-models/docs/MOKU_PLATFORM_SPECIFICATIONS.md` - **Detailed hardware specs**
- `moku-models/datasheets/` - Official Liquid Instruments datasheets

**From Parent Repo:**
- `.serena/memories/platform_models.md` - Platform overview (may be outdated vs submodule)
- `.serena/memories/mcc_routing_concepts.md` - Routing patterns

---

## File Structure

```
moku-models/
├── CLAUDE.md                           # Start here for AI context
├── llms.txt                            # LLM quick reference
├── README.md                           # Human-friendly docs
├── moku_models/
│   ├── __init__.py                     # Public API (import from here)
│   ├── moku_config.py                  # MokuConfig, SlotConfig
│   ├── routing.py                      # MokuConnection
│   ├── discovery.py                    # Device discovery
│   └── platforms/
│       ├── moku_go.py                  # Moku:Go (2 slots, 125 MHz)
│       ├── moku_lab.py                 # Moku:Lab (2 slots, 500 MHz)
│       ├── moku_pro.py                 # Moku:Pro (4 slots, 1.25 GHz)
│       └── moku_delta.py               # Moku:Delta (3 slots, 5 GHz)
├── docs/
│   └── MOKU_PLATFORM_SPECIFICATIONS.md # Comprehensive specs from datasheets
└── datasheets/
    ├── Datasheet-MokuGo.pdf
    ├── Datasheet-MokuLab.pdf
    ├── Datasheet-MokuPro.pdf
    └── Datasheet-MokuDelta.pdf
```

---

## Common Tasks

### Add New Platform
1. Create `moku_models/platforms/moku_xxx.py`
2. Define platform class with specs from datasheet
3. Export constant: `MOKU_XXX_PLATFORM`
4. Update `platforms/__init__.py` and main `__init__.py`
5. Add to README.md platform table

### Query Platform Specs
```python
from moku_models import MOKU_DELTA_PLATFORM

platform = MOKU_DELTA_PLATFORM
print(f"Clock: {platform.clock_mhz} MHz")
print(f"Slots: {platform.slots}")
print(f"I/O: {len(platform.analog_inputs)}IN/{len(platform.analog_outputs)}OUT")

# Get port details
in1 = platform.get_analog_input_by_id('IN1')
print(f"IN1: {in1.resolution_bits}-bit @ {in1.sample_rate_msa} MSa/s")
```

### Validate Configuration
```python
from moku_models import MokuConfig, SlotConfig, MokuConnection, MOKU_GO_PLATFORM

config = MokuConfig(
    platform=MOKU_GO_PLATFORM,
    slots={1: SlotConfig(instrument='Oscilloscope')},
    routing=[MokuConnection(source='IN1', destination='Slot1InA')]
)

errors = config.validate_routing()
if errors:
    print(f"Validation failed: {errors}")
```

---

## Git Workflow (Submodule)

**Working in submodule:**
```bash
cd moku-models/
git status                    # Check submodule status
git add <files>
git commit -m "Add feature"
git push origin main          # Push to moku-models repo

# After pushing submodule:
cd ..                         # Back to parent EZ-EMFI
git add moku-models           # Update submodule reference
git commit -m "Update moku-models to vX.Y.Z"
git push                      # Push parent
```

**Updating submodule in parent:**
```bash
git submodule update --remote moku-models  # Pull latest from remote
git add moku-models
git commit -m "Update moku-models submodule"
```

---

## Design Principles

1. **Pure Data Models** - No deployment logic, just Pydantic validation
2. **Type Safety** - Catch errors before hardware deployment
3. **Single Source of Truth** - Same models for simulation AND hardware
4. **Moku API Aligned** - Port naming matches 1st-party `moku` library

---

## Important Notes

- **Lab/Pro have NO DIO headers** (only Go and Delta support DIO)
- **Delta modeled in 3-slot mode** (8-slot advanced mode not yet supported)
- **Port naming**: Use `IN1`-`IN8`, `OUT1`-`OUT8` (not `Input1`, `Output1`)
- **Slot virtual ports**: `Slot1InA`, `Slot2OutB`, etc. (A/B/C/D channels)

---

## When to Use This Context

**Use `/models` when:**
- Adding new Moku platform support
- Updating platform specifications
- Debugging Pydantic validation errors
- Working on data model structure
- Adding new fields to MokuConfig/SlotConfig

**Use `/python` when:**
- Writing deployment scripts that USE moku-models
- Creating TUI apps
- Building utilities

**Use `/moku` when:**
- Deploying to hardware
- Working with Moku API directly

---

## Context Switching

**Working on Python scripts?** → `/python`
**Deploying to hardware?** → `/moku`
**Working on tests?** → `/test`
**Working on VHDL?** → `/vhdl`

---

Now in moku-models submodule development mode. Read `moku-models/CLAUDE.md` for detailed context.
