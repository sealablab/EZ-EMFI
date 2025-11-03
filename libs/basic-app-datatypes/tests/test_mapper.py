"""
Unit tests for RegisterMapper (core mapping algorithm).

Tests the pure Python mapping algorithm with zero dependencies.
Integration tests with Pydantic are in python_tests/test_bad_register_mapper.py.
"""

import pytest
from basic_app_datatypes import BasicAppDataTypes
from basic_app_datatypes.mapper import RegisterMapper, RegisterMapping, MappingReport


class TestRegisterMapping:
    """Test RegisterMapping dataclass."""

    def test_single_bit_vhdl_slice(self):
        """Test VHDL generation for single-bit (boolean)."""
        mapping = RegisterMapping(
            name="enable",
            datatype=BasicAppDataTypes.BOOLEAN,
            cr_number=6,
            bit_slice=(31, 31)
        )
        assert mapping.to_vhdl_slice() == "app_reg_6(31)"

    def test_multi_bit_vhdl_slice(self):
        """Test VHDL generation for multi-bit types."""
        mapping = RegisterMapping(
            name="intensity",
            datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
            cr_number=6,
            bit_slice=(31, 16)
        )
        assert mapping.to_vhdl_slice() == "app_reg_6(31 downto 16)"

    def test_bit_width_calculation(self):
        """Test bit_width() method."""
        mapping = RegisterMapping(
            name="threshold",
            datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
            cr_number=7,
            bit_slice=(15, 0)
        )
        assert mapping.bit_width() == 16


class TestRegisterMapperValidation:
    """Test RegisterMapper input validation."""

    def test_empty_input(self):
        """Test mapping empty list returns empty result."""
        mapper = RegisterMapper()
        result = mapper.map([])
        assert result == []

    def test_duplicate_names(self):
        """Test that duplicate names raise ValueError."""
        mapper = RegisterMapper()
        items = [
            ("intensity", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
            ("intensity", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S8),  # Duplicate name
        ]
        with pytest.raises(ValueError, match="Duplicate names"):
            mapper.map(items)

    def test_overflow_detection(self):
        """Test detection when types don't fit in 384 bits."""
        mapper = RegisterMapper()
        # 25 x 16-bit values = 400 bits > 384 limit
        items = [(f"val_{i}", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16)
                 for i in range(25)]

        with pytest.raises(ValueError, match="Cannot fit.*384 available bits"):
            mapper.map(items)

    def test_type_too_large_rejected(self):
        """Test that types >32 bits are rejected (Phase 2 limitation)."""
        mapper = RegisterMapper()
        # PULSE_DURATION_NS_U32 is 32-bit (should work)
        items = [("timer", BasicAppDataTypes.PULSE_DURATION_NS_U32)]
        result = mapper.map(items)
        assert len(result) == 1

        # If we had a 48-bit type, it should fail
        # (Not implemented in Phase 1, so we can't test this yet)

    def test_invalid_strategy(self):
        """Test that invalid strategy raises ValueError."""
        mapper = RegisterMapper()
        items = [("test", BasicAppDataTypes.BOOLEAN)]

        with pytest.raises(ValueError, match="Unknown packing strategy"):
            mapper.map(items, strategy="invalid_strategy")


class TestFirstFitStrategy:
    """Test first_fit packing strategy."""

    def test_simple_sequential_packing(self):
        """Test basic sequential packing within single register."""
        mapper = RegisterMapper()
        items = [
            ("intensity", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),  # 16 bits
            ("threshold", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),  # 16 bits
        ]

        mappings = mapper.map(items, strategy="first_fit")

        # Should fit in single register (CR6)
        assert len(mappings) == 2
        assert all(m.cr_number == 6 for m in mappings)

        # Check bit positions (MSB-first packing)
        assert mappings[0].bit_slice == (31, 16)  # First item at MSB
        assert mappings[1].bit_slice == (15, 0)   # Second item below

    def test_multi_register_packing(self):
        """Test packing across multiple registers."""
        mapper = RegisterMapper()
        items = [
            ("v1", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),  # 16 bits
            ("v2", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),  # 16 bits
            ("v3", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),  # 16 bits (CR7)
        ]

        mappings = mapper.map(items, strategy="first_fit")

        assert len(mappings) == 3
        # First two in CR6
        assert mappings[0].cr_number == 6
        assert mappings[1].cr_number == 6
        # Third in CR7
        assert mappings[2].cr_number == 7
        assert mappings[2].bit_slice == (31, 16)  # New register, start at MSB

    def test_boolean_packing(self):
        """Test packing multiple booleans."""
        mapper = RegisterMapper()
        items = [
            ("enable", BasicAppDataTypes.BOOLEAN),
            ("armed", BasicAppDataTypes.BOOLEAN),
            ("trigger", BasicAppDataTypes.BOOLEAN),
        ]

        mappings = mapper.map(items, strategy="first_fit")

        # All should fit in CR6
        assert all(m.cr_number == 6 for m in mappings)
        # Sequential single-bit positions
        assert mappings[0].bit_slice == (31, 31)
        assert mappings[1].bit_slice == (30, 30)
        assert mappings[2].bit_slice == (29, 29)

    def test_mixed_sizes(self):
        """Test packing types of different sizes."""
        mapper = RegisterMapper()
        items = [
            ("voltage", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),      # 16 bits
            ("time_ns", BasicAppDataTypes.PULSE_DURATION_NS_U8),        # 8 bits
            ("enable", BasicAppDataTypes.BOOLEAN),                      # 1 bit
        ]

        mappings = mapper.map(items, strategy="first_fit")

        # Should all fit in CR6 (16 + 8 + 1 = 25 bits < 32)
        assert all(m.cr_number == 6 for m in mappings)
        assert mappings[0].bit_slice == (31, 16)  # voltage
        assert mappings[1].bit_slice == (15, 8)   # time_ns
        assert mappings[2].bit_slice == (7, 7)    # enable


class TestBestFitStrategy:
    """Test best_fit packing strategy."""

    def test_sorts_by_size(self):
        """Test that best_fit sorts types by size (largest first)."""
        mapper = RegisterMapper()
        items = [
            ("small", BasicAppDataTypes.PULSE_DURATION_NS_U8),     # 8 bits
            ("large", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),   # 16 bits
            ("tiny", BasicAppDataTypes.BOOLEAN),                   # 1 bit
        ]

        mappings = mapper.map(items, strategy="best_fit")

        # Should be sorted: large (16), small (8), tiny (1)
        assert mappings[0].name == "large"
        assert mappings[1].name == "small"
        assert mappings[2].name == "tiny"

    def test_better_efficiency_than_first_fit(self):
        """Test that best_fit can be more efficient than first_fit."""
        mapper = RegisterMapper()
        items = [
            ("a", BasicAppDataTypes.PULSE_DURATION_NS_U8),     # 8 bits
            ("b", BasicAppDataTypes.PULSE_DURATION_NS_U8),     # 8 bits
            ("c", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),   # 16 bits
            ("d", BasicAppDataTypes.PULSE_DURATION_NS_U8),     # 8 bits
        ]

        first_fit = mapper.map(items, strategy="first_fit")
        best_fit = mapper.map(items, strategy="best_fit")

        # Both should work, but best_fit might use fewer registers
        # (In this case both use 1 register, but best_fit is more organized)
        assert len(first_fit) == 4
        assert len(best_fit) == 4

        # Best fit should place largest first
        assert best_fit[0].datatype == BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16


class TestTypeClusteringStrategy:
    """Test type_clustering packing strategy."""

    def test_groups_by_type_family(self):
        """Test that type_clustering groups related types together."""
        mapper = RegisterMapper()
        items = [
            ("time1", BasicAppDataTypes.PULSE_DURATION_NS_U8),
            ("voltage_out", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
            ("time2", BasicAppDataTypes.PULSE_DURATION_MS_U16),
            ("voltage_in", BasicAppDataTypes.VOLTAGE_INPUT_25V_S16),
            ("bool1", BasicAppDataTypes.BOOLEAN),
        ]

        mappings = mapper.map(items, strategy="type_clustering")

        # Extract names in order
        names = [m.name for m in mappings]

        # Voltage outputs should come first
        assert names.index("voltage_out") < names.index("time1")
        # Voltage inputs should come after outputs
        assert names.index("voltage_in") < names.index("time1")
        # Time types should be together
        time_indices = [names.index("time1"), names.index("time2")]
        assert abs(time_indices[0] - time_indices[1]) == 1  # Adjacent
        # Boolean should be last
        assert names.index("bool1") == len(names) - 1


class TestDS1140PDExample:
    """Test DS1140_PD register mapping (real-world example)."""

    def test_ds1140_pd_mapping(self):
        """Test mapping DS1140_PD types and verify register savings."""
        mapper = RegisterMapper()

        # DS1140_PD datatypes (from spec)
        ds1140_types = [
            ("arm_probe", BasicAppDataTypes.BOOLEAN),                          # 1 bit
            ("force_fire", BasicAppDataTypes.BOOLEAN),                         # 1 bit
            ("reset_fsm", BasicAppDataTypes.BOOLEAN),                          # 1 bit
            ("clock_divider", BasicAppDataTypes.PULSE_DURATION_NS_U8),         # 8 bits
            ("arm_timeout", BasicAppDataTypes.PULSE_DURATION_MS_U16),          # 16 bits
            ("firing_duration", BasicAppDataTypes.PULSE_DURATION_NS_U8),       # 8 bits
            ("cooling_duration", BasicAppDataTypes.PULSE_DURATION_NS_U8),      # 8 bits
            ("trigger_threshold", BasicAppDataTypes.VOLTAGE_INPUT_25V_S16),    # 16 bits
            ("intensity", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),           # 16 bits
        ]

        mappings = mapper.map(ds1140_types, strategy="best_fit")

        # Calculate registers used
        registers_used = len(set(m.cr_number for m in mappings))

        # Current manual system: 9 types = 9 registers (one per type)
        # With packing: Should use 3-4 registers
        assert registers_used <= 4, f"Expected ≤4 registers, got {registers_used}"

        # Verify 50%+ register savings
        manual_registers = 9
        savings_percent = ((manual_registers - registers_used) / manual_registers) * 100
        assert savings_percent >= 50, f"Expected ≥50% savings, got {savings_percent:.1f}%"

        # Verify total bits
        total_bits = sum(m.bit_width() for m in mappings)
        expected_bits = 1 + 1 + 1 + 8 + 16 + 8 + 8 + 16 + 16  # 75 bits
        assert total_bits == expected_bits


class TestMappingReport:
    """Test MappingReport generation."""

    def test_report_generation(self):
        """Test generating report from mappings."""
        mapper = RegisterMapper()
        items = [
            ("intensity", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
            ("threshold", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
        ]

        mappings = mapper.map(items)
        report = mapper.generate_report(mappings)

        assert report.total_bits_used == 32  # Two 16-bit values
        assert report.total_bits_available == 384
        assert report.efficiency_percent == pytest.approx((32/384) * 100)
        assert len(report.register_map) == 1  # One register used (CR6)

    def test_ascii_art_output(self):
        """Test ASCII art visualization."""
        mapper = RegisterMapper()
        items = [
            ("enable", BasicAppDataTypes.BOOLEAN),
            ("voltage", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
        ]

        mappings = mapper.map(items, strategy="best_fit")
        report = mapper.generate_report(mappings)
        ascii_art = report.to_ascii_art()

        # Should contain register visualization
        assert "CR 6" in ascii_art or "CR6" in ascii_art  # Accept either format
        assert "enable" in ascii_art
        assert "voltage" in ascii_art
        assert "Efficiency" in ascii_art

    def test_markdown_output(self):
        """Test Markdown table generation."""
        mapper = RegisterMapper()
        items = [("test", BasicAppDataTypes.BOOLEAN)]

        mappings = mapper.map(items)
        report = mapper.generate_report(mappings)
        markdown = report.to_markdown()

        # Should contain table headers
        assert "| CR  | Bit Slice | Name | Type | Width |" in markdown
        assert "test" in markdown

    def test_vhdl_comments_output(self):
        """Test VHDL comment generation."""
        mapper = RegisterMapper()
        items = [("enable", BasicAppDataTypes.BOOLEAN)]

        mappings = mapper.map(items)
        report = mapper.generate_report(mappings)
        vhdl = report.to_vhdl_comments()

        # Should contain VHDL-style comments
        assert "-- CR6:" in vhdl
        assert "enable" in vhdl

    def test_json_output(self):
        """Test JSON serialization."""
        mapper = RegisterMapper()
        items = [
            ("intensity", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
            ("enable", BasicAppDataTypes.BOOLEAN),
        ]

        mappings = mapper.map(items)
        report = mapper.generate_report(mappings)
        json_data = report.to_json()

        # Verify structure
        assert "mappings" in json_data
        assert "summary" in json_data
        assert len(json_data["mappings"]) == 2
        assert json_data["summary"]["bits_used"] == 17  # 16 + 1
        assert json_data["summary"]["registers_used"] == 1


class TestDeterminism:
    """Test that mappings are deterministic and reproducible."""

    def test_same_input_same_output(self):
        """Test that identical inputs produce identical mappings."""
        mapper = RegisterMapper()
        items = [
            ("a", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
            ("b", BasicAppDataTypes.PULSE_DURATION_MS_U16),
            ("c", BasicAppDataTypes.BOOLEAN),
        ]

        mapping1 = mapper.map(items, strategy="best_fit")
        mapping2 = mapper.map(items, strategy="best_fit")

        assert mapping1 == mapping2

    def test_order_independence_best_fit(self):
        """Test that best_fit produces same result regardless of input order."""
        mapper = RegisterMapper()

        items_order1 = [
            ("small", BasicAppDataTypes.PULSE_DURATION_NS_U8),
            ("large", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
        ]

        items_order2 = [
            ("large", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
            ("small", BasicAppDataTypes.PULSE_DURATION_NS_U8),
        ]

        mapping1 = mapper.map(items_order1, strategy="best_fit")
        mapping2 = mapper.map(items_order2, strategy="best_fit")

        # Best fit should produce same result (sorted by size)
        assert mapping1 == mapping2


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_type(self):
        """Test mapping a single type."""
        mapper = RegisterMapper()
        items = [("solo", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16)]

        mappings = mapper.map(items)

        assert len(mappings) == 1
        assert mappings[0].cr_number == 6
        assert mappings[0].bit_slice == (31, 16)  # MSB-aligned

    def test_all_32_bit_types(self):
        """Test packing all types that exactly fill registers."""
        mapper = RegisterMapper()
        # 12 x 32-bit values = 384 bits (exactly fills all registers)
        items = [(f"timer_{i}", BasicAppDataTypes.PULSE_DURATION_NS_U32)
                 for i in range(12)]

        mappings = mapper.map(items)

        # Should use exactly 12 registers (CR6-CR17)
        assert len(set(m.cr_number for m in mappings)) == 12
        assert min(m.cr_number for m in mappings) == 6
        assert max(m.cr_number for m in mappings) == 17

    def test_nearly_full_register(self):
        """Test packing that nearly fills a register."""
        mapper = RegisterMapper()
        items = [
            ("a", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),  # 16 bits
            ("b", BasicAppDataTypes.PULSE_DURATION_NS_U8),    # 8 bits
            ("c", BasicAppDataTypes.PULSE_DURATION_NS_U8),    # 8 bits (total 32)
        ]

        mappings = mapper.map(items, strategy="first_fit")

        # Should exactly fill CR6
        assert all(m.cr_number == 6 for m in mappings)
        assert sum(m.bit_width() for m in mappings) == 32
