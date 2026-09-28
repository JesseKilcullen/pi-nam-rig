# test_midi_logic.py — verifies the MIDI mapping in pipedal-hardware-v2.md §3
# against midi_logic.py, with zero hardware and zero dependencies.
#
# Run:
#   python3 -m unittest test_midi_logic.py -v
#
# If this passes, the *logic* the Pico will run is correct. It does not
# prove the Pico's wiring, debounce, or USB MIDI transport work — that needs
# midi_monitor.py once you have a Pico on a breadboard (see that file).

import unittest

from midi_logic import FootswitchState, BrowseState, MODE_PRESET, MODE_SNAPSHOT


class TestBootDefaults(unittest.TestCase):
    def test_boots_into_snapshot_mode(self):
        s = FootswitchState()
        self.assertEqual(s.mode, MODE_SNAPSHOT)
        self.assertEqual(s.led_state(), (False, True))


class TestSnapshotMode(unittest.TestCase):
    def test_row_sends_cc20_25(self):
        s = FootswitchState()
        for i in range(6):
            self.assertEqual(s.press_row(i), [("cc", 20 + i, 127)])
            self.assertEqual(s.mode, MODE_SNAPSHOT)  # unchanged

    def test_row_out_of_range_rejected(self):
        s = FootswitchState()
        with self.assertRaises(ValueError):
            s.press_row(6)
        with self.assertRaises(ValueError):
            s.press_row(-1)


class TestPresetMode(unittest.TestCase):
    def test_row_sends_pc_then_forces_snapshot1_then_reverts_mode(self):
        s = FootswitchState()
        s.press_mode_preset()
        self.assertEqual(s.mode, MODE_PRESET)

        msgs = s.press_row(3)
        self.assertEqual(msgs, [("pc", 3), ("cc", 20, 127)])
        # §2: "returns to SNAPSHOT mode" after a preset pick
        self.assertEqual(s.mode, MODE_SNAPSHOT)
        self.assertEqual(s.led_state(), (False, True))

    def test_preset_zero_indexed_on_the_wire(self):
        s = FootswitchState()
        s.press_mode_preset()
        msgs = s.press_row(0)
        self.assertEqual(msgs[0], ("pc", 0))  # "Preset 1" -> C0 00


class TestModeSelectButtons(unittest.TestCase):
    def test_mode_selects_send_no_midi(self):
        s = FootswitchState()
        self.assertEqual(s.press_mode_preset(), [])
        self.assertEqual(s.press_mode_snapshot(), [])

    def test_leds_follow_mode(self):
        s = FootswitchState()
        s.press_mode_preset()
        self.assertEqual(s.led_state(), (True, False))
        s.press_mode_snapshot()
        self.assertEqual(s.led_state(), (False, True))


class TestReset(unittest.TestCase):
    def test_reset_forces_preset1_snapshot1_and_snapshot_mode(self):
        s = FootswitchState()
        s.press_mode_preset()  # start from PRESET mode to prove reset overrides it
        msgs = s.press_reset()
        self.assertEqual(msgs, [("pc", 0), ("cc", 20, 127)])
        self.assertEqual(s.mode, MODE_SNAPSHOT)
        self.assertEqual(s.led_state(), (False, True))


class TestTunerMute(unittest.TestCase):
    def test_toggles_both_ccs_together(self):
        s = FootswitchState()
        self.assertEqual(s.press_tuner_mute(), [("cc", 26, 127), ("cc", 27, 127)])
        self.assertTrue(s.tuner_mute_on)
        self.assertEqual(s.press_tuner_mute(), [("cc", 26, 0), ("cc", 27, 0)])
        self.assertFalse(s.tuner_mute_on)

    def test_tuner_mute_does_not_touch_mode(self):
        s = FootswitchState()
        s.press_mode_preset()
        s.press_tuner_mute()
        self.assertEqual(s.mode, MODE_PRESET)


class TestFullSessionSequence(unittest.TestCase):
    """One press-by-press walk through a realistic session, matching the
    worked example a player would actually do at a gig."""

    def test_typical_session(self):
        s = FootswitchState()

        # Boot: SNAPSHOT mode, hit snapshot 3
        self.assertEqual(s.press_row(2), [("cc", 22, 127)])

        # Switch to PRESET mode, pick preset 5 -> forces snapshot 1, back to SNAPSHOT
        s.press_mode_preset()
        self.assertEqual(s.press_row(4), [("pc", 4), ("cc", 20, 127)])
        self.assertEqual(s.mode, MODE_SNAPSHOT)

        # Hit tuner mid-song
        self.assertEqual(s.press_tuner_mute(), [("cc", 26, 127), ("cc", 27, 127)])

        # Any snapshot press should be usable to escape tuning (Pico's job is
        # just to send the CC; PiPedal's snapshot recall is what cancels the
        # tuner state per §3 "Intentional" note — not re-tested here).
        self.assertEqual(s.press_row(0), [("cc", 20, 127)])

        # Panic -> RESET
        self.assertEqual(s.press_reset(), [("pc", 0), ("cc", 20, 127)])


class TestBrowseState(unittest.TestCase):
    def test_boots_inactive(self):
        b = BrowseState()
        self.assertFalse(b.active)

    def test_zero_presets_is_a_no_op(self):
        b = BrowseState()
        b.rotate(1, preset_count=0)
        self.assertFalse(b.active)

    def test_first_turn_activates_and_starts_from_current(self):
        b = BrowseState()
        b.rotate(1, preset_count=12, current_index=5)
        self.assertTrue(b.active)
        self.assertEqual(b.cursor, 6)

    def test_first_turn_defaults_to_zero_if_current_unknown(self):
        b = BrowseState()
        b.rotate(1, preset_count=12, current_index=None)
        self.assertEqual(b.cursor, 1)

    def test_subsequent_turns_ignore_current_index(self):
        b = BrowseState()
        b.rotate(1, preset_count=12, current_index=5)  # cursor -> 6, active
        b.rotate(1, preset_count=12, current_index=999)  # should NOT jump off 999
        self.assertEqual(b.cursor, 7)

    def test_wraps_at_both_ends(self):
        b = BrowseState()
        b.rotate(-1, preset_count=12, current_index=0)  # enters at 0, then -1
        self.assertEqual(b.cursor, 11)
        b.rotate(1, preset_count=12)
        self.assertEqual(b.cursor, 0)

    def test_fast_spin_moves_more_than_one(self):
        b = BrowseState()
        b.rotate(5, preset_count=12, current_index=0)
        self.assertEqual(b.cursor, 5)

    def test_confirm_returns_pc_and_forces_snapshot_1_and_exits(self):
        b = BrowseState()
        b.rotate(1, preset_count=12, current_index=5)  # cursor -> 6
        msgs = b.confirm()
        self.assertEqual(msgs, [("pc", 6), ("cc", 20, 127)])
        self.assertFalse(b.active)

    def test_cancel_exits_without_selecting(self):
        b = BrowseState()
        b.rotate(1, preset_count=12, current_index=5)
        b.cancel()
        self.assertFalse(b.active)
        # cursor is irrelevant once cancelled, but shouldn't error to read
        self.assertIsInstance(b.cursor, int)


if __name__ == "__main__":
    unittest.main()
