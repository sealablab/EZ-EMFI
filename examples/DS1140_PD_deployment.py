#!/usr/bin/env python3
"""
DS1140_PD Deployment Example

Demonstrates integration between BasicAppsRegPackage and MokuConfig.

Shows how to:
1. Load register interface from YAML
2. Generate register mapping
3. Export to MokuConfig.control_registers
4. Deploy to Moku hardware

Usage:
    python examples/DS1140_PD_deployment.py
"""

from pathlib import Path

# Assumes EZ-EMFI is installed or in PYTHONPATH
# Run: uv pip install -e . from project root
from moku_models import MokuConfig, SlotConfig, MokuConnection, MOKU_GO_PLATFORM
from models.custom_inst.reg_package import BasicAppsRegPackage


def main():
    # Step 1: Load register interface
    print("Loading register interface...")
    interface_path = Path(__file__).parent / "DS1140_PD_interface.yaml"
    reg_interface = BasicAppsRegPackage.from_yaml(interface_path)

    print(f"  App: {reg_interface.app_name}")
    print(f"  Datatypes: {len(reg_interface.datatypes)}")
    print(f"  Strategy: {reg_interface.mapping_strategy}")

    # Step 2: Generate register mapping
    print("\nGenerating register mapping...")
    mappings = reg_interface.generate_mapping()

    print(f"  Mapped to {len(set(m.cr_number for m in mappings))} registers")
    for mapping in mappings:
        msb, lsb = mapping.bit_slice
        print(f"    CR{mapping.cr_number}[{msb}:{lsb}] = {mapping.name}")

    # Step 3: Export to control registers
    print("\nExporting control registers...")
    control_regs = reg_interface.to_control_registers()

    print(f"  Generated {len(control_regs)} control register defaults:")
    for cr_num, value in sorted(control_regs.items()):
        print(f"    CR{cr_num} = 0x{value:08X}")

    # Step 4: Create MokuConfig
    print("\nCreating MokuConfig...")
    config = MokuConfig(
        platform=MOKU_GO_PLATFORM,
        slots={
            1: SlotConfig(
                instrument='CloudCompile',
                bitstream='modules/DS1140-PD/latest/25ff_bitstreams.tar',
                control_registers=control_regs  # ← BAD-generated values!
            ),
            2: SlotConfig(
                instrument='Oscilloscope',
                settings={'sample_rate': 125e6}
            )
        },
        routing=[
            MokuConnection(source='Input1', destination='Slot1InA'),
            MokuConnection(source='Slot1OutA', destination='Output1'),
            MokuConnection(source='Slot1OutA', destination='Slot2InA')
        ]
    )

    print("  ✓ MokuConfig created successfully")
    print(f"  Platform: {config.platform.name}")
    print(f"  Slots: {list(config.slots.keys())}")
    print(f"  Routing: {len(config.routing)} connections")

    # Step 5: Deploy (optional - requires hardware)
    print("\nTo deploy to hardware:")
    print("  uv run python tools/moku_go.py deploy \\")
    print("    --device <ip_address> \\")
    print("    --bitstream modules/DS1140-PD/latest/25ff_bitstreams.tar \\")
    print("    --slot 1")

    print("\n✓ Integration example complete!")


if __name__ == '__main__':
    main()
