--------------------------------------------------------------------------------
-- File: DS1140_PD_custom_inst_main.vhd
-- Generated: 2025-11-03 00:51:54
-- Generator: tools/generate_custom_inst_v2.py
-- Template Version: 2.0 (BasicAppDataTypes)
--
-- ⚠️  GENERATED TEMPLATE - CUSTOMIZE FOR YOUR APPLICATION ⚠️
-- This is a starting point template. Implement your application logic here.
--
-- Description:
--   Main application logic for DS1140_PD.
--   Receives typed signals from shim, implements application behavior.
--
-- Platform: Moku:Go
-- Clock Frequency: 125 MHz
--
-- Application Signals (from register mapping):
--   arm_probe: std_logic - Arm the probe driver (one-shot operation)
--   force_fire: std_logic - Manual trigger for testing (bypasses threshold detection)
--   reset_fsm: std_logic - Reset state machine to READY state
--   arm_timeout: unsigned(15 downto 0) - Maximum time in armed state before timeout
--   firing_duration: unsigned(7 downto 0) - FSM duration in FIRING state (NOT EM pulse - that's hardware-fixed at 50ns)
--   cooling_duration: unsigned(7 downto 0) - FSM duration in COOLING state (thermal recovery period)
--   trigger_threshold: signed(15 downto 0) - Voltage threshold for trigger detection (Moku Go/Lab/Pro: ±25V ADC range)
--   intensity: signed(15 downto 0) - Pulse amplitude control (0-3.3V to DS1120A, hardware clamped at probe)
--
-- References:
--   - DS1140_PD_interface.yaml
--   - DS1140_PD_custom_inst_shim.vhd (auto-generated register mapping)
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library WORK;
use WORK.basic_app_types_pkg.all;
use WORK.basic_app_voltage_pkg.all;
use WORK.basic_app_time_pkg.all;
entity DS1140_PD_custom_inst_main is
    generic (
        CLK_FREQ_HZ : integer := 125000000  -- Moku:Go clock frequency
    );
    port (
        ------------------------------------------------------------------------
        -- Clock and Reset
        ------------------------------------------------------------------------
        Clk                : in  std_logic;
        Reset              : in  std_logic;  -- Active-high reset
        global_enable      : in  std_logic;  -- Combined VOLO ready signals
        ready_for_updates  : out std_logic;  -- Handshake to shim

        ------------------------------------------------------------------------
        -- Application Signals (Typed - from BasicAppDataTypes)
        ------------------------------------------------------------------------
        arm_probe : in std_logic;        force_fire : in std_logic;        reset_fsm : in std_logic;        arm_timeout : in unsigned(15 downto 0);        firing_duration : in unsigned(7 downto 0);        cooling_duration : in unsigned(7 downto 0);        trigger_threshold : in signed(15 downto 0);        intensity : in signed(15 downto 0)    );
end entity DS1140_PD_custom_inst_main;

architecture rtl of DS1140_PD_custom_inst_main is

    ----------------------------------------------------------------------------
    -- Internal Signals
    ----------------------------------------------------------------------------
    -- TODO: Add your application-specific signals here

    -- Example state machine (customize for your application)
    type state_t is (IDLE, ACTIVE, DONE);
    signal state : state_t;

    ----------------------------------------------------------------------------
    -- Time Conversion Signals (if needed for time-based datatypes)
    ----------------------------------------------------------------------------
    signal arm_timeout_cycles : unsigned(31 downto 0);  -- arm_timeout converted to clock cycles
    signal firing_duration_cycles : unsigned(31 downto 0);  -- firing_duration converted to clock cycles
    signal cooling_duration_cycles : unsigned(31 downto 0);  -- cooling_duration converted to clock cycles

begin

    ------------------------------------------------------------------------
    -- Ready for Updates
    --
    -- Drive this signal based on your application's update policy:
    --   '1' = Safe to update registers (typical: always ready)
    --   '0' = Hold current values (use during critical operations)
    ------------------------------------------------------------------------
    ready_for_updates <= '1';  -- TODO: Customize based on your application

    ------------------------------------------------------------------------
    -- Time to Cycles Conversions
    --
    -- Convert time durations to clock cycles using platform-aware functions
    ------------------------------------------------------------------------
    -- Convert arm_timeout (ms) to clock cycles
    arm_timeout_cycles <= ms_to_cycles(arm_timeout, CLK_FREQ_HZ);
    -- Convert firing_duration (ns) to clock cycles
    firing_duration_cycles <= ns_to_cycles(firing_duration, CLK_FREQ_HZ);
    -- Convert cooling_duration (ns) to clock cycles
    cooling_duration_cycles <= ns_to_cycles(cooling_duration, CLK_FREQ_HZ);

    ------------------------------------------------------------------------
    -- Main Application Logic
    --
    -- TODO: Implement your application behavior here
    --
    -- Available inputs:
    --   - arm_probe: std_logic - Arm the probe driver (one-shot operation)
    --   - force_fire: std_logic - Manual trigger for testing (bypasses threshold detection)
    --   - reset_fsm: std_logic - Reset state machine to READY state
    --   - arm_timeout: unsigned(15 downto 0) - Maximum time in armed state before timeout
    --     (arm_timeout_cycles contains clock-cycle equivalent)
    --   - firing_duration: unsigned(7 downto 0) - FSM duration in FIRING state (NOT EM pulse - that's hardware-fixed at 50ns)
    --     (firing_duration_cycles contains clock-cycle equivalent)
    --   - cooling_duration: unsigned(7 downto 0) - FSM duration in COOLING state (thermal recovery period)
    --     (cooling_duration_cycles contains clock-cycle equivalent)
    --   - trigger_threshold: signed(15 downto 0) - Voltage threshold for trigger detection (Moku Go/Lab/Pro: ±25V ADC range)
    --   - intensity: signed(15 downto 0) - Pulse amplitude control (0-3.3V to DS1120A, hardware clamped at probe)
    --
    -- Outputs to drive:
    ------------------------------------------------------------------------
    MAIN_PROC: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                state <= IDLE;
                -- TODO: Initialize output signals
            elsif global_enable = '1' then
                -- TODO: Implement your state machine / application logic
                case state is
                    when IDLE =>
                        -- Example: Wait for trigger condition
                        state <= IDLE;

                    when ACTIVE =>
                        -- Example: Perform main operation
                        state <= DONE;

                    when DONE =>
                        -- Example: Return to idle
                        state <= IDLE;

                    when others =>
                        state <= IDLE;
                end case;
            end if;
        end if;
    end process MAIN_PROC;

end architecture rtl;