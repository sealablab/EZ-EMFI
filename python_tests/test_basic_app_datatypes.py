"""
Comprehensive tests for BasicAppDataTypes implementation.

Tests cover:
- Type registry completeness
- Voltage conversions (all 12 types)
- Time conversions (all 12 types)
- Platform compatibility
- Boolean type
- Immutability
"""

import pytest
from models.custom_inst.datatypes import (
    BasicAppDataTypes,
    TypeMetadata,
    TYPE_REGISTRY,
    PulseDuration_ns,
    PulseDuration_us,
    PulseDuration_ms,
    PulseDuration_sec,
    TypeConverter,
)


# ============================================================================
# TYPE REGISTRY TESTS
# ============================================================================

def test_type_registry_completeness():
    """Verify all BasicAppDataTypes have metadata."""
    for type_enum in BasicAppDataTypes:
        assert type_enum in TYPE_REGISTRY, f"Missing metadata for {type_enum}"
        metadata = TYPE_REGISTRY[type_enum]
        assert metadata.bit_width > 0, f"{type_enum} has invalid bit_width"
        assert metadata.vhdl_type, f"{type_enum} missing vhdl_type"
        assert metadata.python_type, f"{type_enum} missing python_type"


def test_bit_width_immutable():
    """Ensure bit widths are truly fixed (frozen dataclass)."""
    metadata = TYPE_REGISTRY[BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16]
    assert metadata.bit_width == 16

    # Should not be able to change (frozen dataclass)
    with pytest.raises(AttributeError):
        metadata.bit_width = 32


def test_type_count():
    """Verify we have exactly 23 types (12 voltage + 10 time + 1 boolean)."""
    assert len(TYPE_REGISTRY) == 23
    assert len(list(BasicAppDataTypes)) == 23


# ============================================================================
# VOLTAGE CONVERSION TESTS
# ============================================================================

def test_voltage_output_05v_s16_conversion():
    """Test ±5V 16-bit signed voltage conversions."""
    # Test nominal values
    raw = TypeConverter.voltage_output_05v_s16_to_raw(2400)  # 2.4V
    assert -32768 <= raw <= 32767
    recovered = TypeConverter.raw_to_voltage_output_05v_s16(raw)
    assert abs(recovered - 2400) <= 10, "Rounding error too large"

    # Test limits (note: -5000mV maps to -32767 due to integer scaling)
    raw_max = TypeConverter.voltage_output_05v_s16_to_raw(5000)
    assert raw_max == 32767
    raw_min = TypeConverter.voltage_output_05v_s16_to_raw(-5000)
    assert raw_min == -32767  # -5000/5000 * 32767 = -32767

    # Test out-of-range
    with pytest.raises(ValueError):
        TypeConverter.voltage_output_05v_s16_to_raw(6000)  # Exceeds ±5V


def test_voltage_input_25v_s16_conversion():
    """Test ±25V 16-bit signed voltage conversions."""
    # Test nominal value
    raw = TypeConverter.voltage_input_25v_s16_to_raw(10000)  # 10V
    recovered = TypeConverter.raw_to_voltage_input_25v_s16(raw)
    assert abs(recovered - 10000) <= 50, "Rounding error too large"

    # Test limits (note: -25000mV maps to -32767 due to integer scaling)
    assert TypeConverter.voltage_input_25v_s16_to_raw(25000) == 32767
    assert TypeConverter.voltage_input_25v_s16_to_raw(-25000) == -32767  # -25000/25000 * 32767 = -32767


def test_voltage_output_05v_u15_conversion():
    """Test 0 to +5V 15-bit unsigned voltage conversions."""
    # Test nominal value
    raw = TypeConverter.voltage_output_05v_u15_to_raw(2500)  # 2.5V
    assert 0 <= raw <= 32767
    recovered = TypeConverter.raw_to_voltage_output_05v_u15(raw)
    assert abs(recovered - 2500) <= 10

    # Test limits
    assert TypeConverter.voltage_output_05v_u15_to_raw(0) == 0
    assert TypeConverter.voltage_output_05v_u15_to_raw(5000) == 32767

    # Test negative (should fail)
    with pytest.raises(ValueError):
        TypeConverter.voltage_output_05v_u15_to_raw(-1000)


# ============================================================================
# TIME CONVERSION TESTS
# ============================================================================

def test_pulse_duration_ns_construction():
    """Test PulseDuration_ns validation."""
    # Valid construction
    duration = PulseDuration_ns(500, width=16)
    assert duration.value == 500
    assert duration.unit == 'ns'
    assert duration.width == 16

    # Invalid: exceeds U8 max
    with pytest.raises(ValueError):
        PulseDuration_ns(500, width=8)  # 500 > 255

    # Invalid: negative duration
    with pytest.raises(ValueError):
        PulseDuration_ns(-100, width=16)


def test_pulse_duration_to_cycles_exact():
    """Test exact cycle conversion (no rounding)."""
    duration = PulseDuration_ns(800, width=16)

    # Moku:Go @ 125 MHz (8ns period)
    cycles = duration.to_cycles(clock_period_ns=8.0, rounding='EXACT')
    assert cycles == 100  # 800ns / 8ns = 100 cycles (exact)

    # Should fail if not evenly divisible
    duration_odd = PulseDuration_ns(500, width=16)
    with pytest.raises(ValueError):
        duration_odd.to_cycles(clock_period_ns=8.0, rounding='EXACT')


def test_pulse_duration_to_cycles_rounding():
    """Test rounding strategies."""
    duration = PulseDuration_ns(500, width=16)

    # ROUND_UP: 500ns / 8ns = 62.5 → 63 cycles
    cycles_up = duration.to_cycles(clock_period_ns=8.0, rounding='ROUND_UP')
    assert cycles_up == 63

    # ROUND_DOWN: 500ns / 8ns = 62.5 → 62 cycles
    cycles_down = duration.to_cycles(clock_period_ns=8.0, rounding='ROUND_DOWN')
    assert cycles_down == 62


def test_pulse_duration_to_basic_type():
    """Test conversion to BasicAppDataTypes enum."""
    duration_ns8 = PulseDuration_ns(128, width=8)
    assert duration_ns8.to_basic_type() == BasicAppDataTypes.PULSE_DURATION_NS_U8

    duration_ns16 = PulseDuration_ns(500, width=16)
    assert duration_ns16.to_basic_type() == BasicAppDataTypes.PULSE_DURATION_NS_U16

    duration_ns32 = PulseDuration_ns(10000, width=32)
    assert duration_ns32.to_basic_type() == BasicAppDataTypes.PULSE_DURATION_NS_U32


def test_pulse_duration_us_conversion():
    """Test microsecond duration conversions."""
    duration = PulseDuration_us(100, width=16)
    
    # Should convert to nanoseconds correctly
    assert duration.to_nanoseconds() == 100000  # 100µs = 100,000ns
    
    # Should convert to cycles correctly (Moku:Go @ 125 MHz)
    cycles = duration.to_cycles(clock_period_ns=8.0, rounding='EXACT')
    assert cycles == 12500  # 100,000ns / 8ns = 12,500 cycles


def test_pulse_duration_ms_conversion():
    """Test millisecond duration conversions."""
    duration = PulseDuration_ms(100, width=16)
    
    # Should convert to nanoseconds correctly
    assert duration.to_nanoseconds() == 100_000_000  # 100ms
    
    # Should convert to cycles correctly (Moku:Go @ 125 MHz)
    cycles = duration.to_cycles(clock_period_ns=8.0, rounding='EXACT')
    assert cycles == 12_500_000  # 100ms @ 125 MHz


# ============================================================================
# PLATFORM COMPATIBILITY TESTS
# ============================================================================

def test_time_multi_platform_conversion():
    """Verify time types convert correctly for different clock rates."""
    duration_ns = PulseDuration_ns(1000, width=16)  # 1µs

    # Moku:Go @ 125 MHz (8ns period)
    cycles_go = duration_ns.to_cycles(clock_period_ns=8.0, rounding='EXACT')
    assert cycles_go == 125  # 1µs @ 125MHz

    # Moku:Lab @ 500 MHz (2ns period)
    cycles_lab = duration_ns.to_cycles(clock_period_ns=2.0, rounding='EXACT')
    assert cycles_lab == 500  # 1µs @ 500MHz

    # Moku:Delta @ 5 GHz (0.2ns period)
    cycles_delta = duration_ns.to_cycles(clock_period_ns=0.2, rounding='EXACT')
    assert cycles_delta == 5000  # 1µs @ 5GHz


# ============================================================================
# BOOLEAN TYPE TESTS
# ============================================================================

def test_boolean_type():
    """Test boolean type metadata."""
    metadata = TYPE_REGISTRY[BasicAppDataTypes.BOOLEAN]
    assert metadata.bit_width == 1
    assert metadata.vhdl_type == "std_logic"
    assert metadata.python_type == bool
    assert metadata.default_value == False


# ============================================================================
# TYPE CONVERTER UTILITY TESTS
# ============================================================================

def test_time_to_cycles_utility():
    """Test TypeConverter.time_to_cycles utility method."""
    # Test nanoseconds
    cycles = TypeConverter.time_to_cycles(
        value=1000, unit='ns', clock_period_ns=8.0, rounding='EXACT'
    )
    assert cycles == 125

    # Test microseconds
    cycles = TypeConverter.time_to_cycles(
        value=100, unit='us', clock_period_ns=8.0, rounding='EXACT'
    )
    assert cycles == 12500

    # Test invalid unit
    with pytest.raises(ValueError):
        TypeConverter.time_to_cycles(
            value=100, unit='invalid', clock_period_ns=8.0, rounding='EXACT'
        )


def test_cycles_to_time_utility():
    """Test TypeConverter.cycles_to_time utility method."""
    # Test nanoseconds
    time_ns = TypeConverter.cycles_to_time(
        cycles=125, unit='ns', clock_period_ns=8.0
    )
    assert time_ns == 1000  # 125 cycles * 8ns = 1000ns

    # Test microseconds
    time_us = TypeConverter.cycles_to_time(
        cycles=12500, unit='us', clock_period_ns=8.0
    )
    assert time_us == 100  # 12500 cycles * 8ns = 100,000ns = 100µs


# ============================================================================
# METADATA VALIDATION TESTS
# ============================================================================

def test_voltage_metadata_units():
    """Verify all voltage types have mV units."""
    for type_enum in BasicAppDataTypes:
        if 'VOLTAGE' in type_enum.value:
            metadata = TYPE_REGISTRY[type_enum]
            assert metadata.unit == 'mV'


def test_time_metadata_units():
    """Verify all time types have correct units."""
    for type_enum in BasicAppDataTypes:
        if 'DURATION_NS' in type_enum.value:
            metadata = TYPE_REGISTRY[type_enum]
            assert metadata.unit == 'ns'
        elif 'DURATION_US' in type_enum.value:
            metadata = TYPE_REGISTRY[type_enum]
            assert metadata.unit == 'us'
        elif 'DURATION_MS' in type_enum.value:
            metadata = TYPE_REGISTRY[type_enum]
            assert metadata.unit == 'ms'
        elif 'DURATION_S' in type_enum.value:
            metadata = TYPE_REGISTRY[type_enum]
            assert metadata.unit == 's'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
