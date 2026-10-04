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

from midi_logic import (
    FootswitchState,
    BrowseState,
    EditMenu,
    MODE_PRESET,
    MODE_SNAPSHOT,
    PAGE_ROOT,
    PAGE_BANDS,
    PAGE_SLIDER,
    PARAM_LEVEL,
    PARAM_PITCH,
    CC_EDIT_BASE,
    CC_EDIT_REQUEST,
    CC_SAVE,
    PAGE_SAVE,
    SAVE_PENDING_TEXT,
)


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


class TestEditMenu(unittest.TestCase):
    def opened(self):
        m = EditMenu()
        m.press_menu_key()
        return m

    def test_boots_inactive(self):
        self.assertFalse(EditMenu().active)

    def test_menu_key_opens_on_root_with_level_selected(self):
        m = EditMenu()
        self.assertEqual(m.press_menu_key(), [])
        self.assertTrue(m.active)
        self.assertEqual((m.page, m.cursor), (PAGE_ROOT, 0))
        self.assertEqual(m.items(), ("Level", "EQ", "Pitch Shift", "Save"))

    def test_menu_key_on_root_closes(self):
        m = self.opened()
        m.press_menu_key()
        self.assertFalse(m.active)

    def test_scrolling_wraps(self):
        m = self.opened()
        m.rotate(-1)
        self.assertEqual(m.cursor, 3)
        m.rotate(1)
        self.assertEqual(m.cursor, 0)

    def test_level_opens_slider_and_requests_its_value(self):
        m = self.opened()
        msgs = m.push()
        self.assertEqual((m.page, m.param), (PAGE_SLIDER, PARAM_LEVEL))
        self.assertEqual(msgs, [("cc", CC_EDIT_REQUEST, PARAM_LEVEL)])
        self.assertEqual(m.title(), "Level")

    def test_pitch_opens_slider(self):
        m = self.opened()
        m.rotate(2)
        msgs = m.push()
        self.assertEqual((m.page, m.param), (PAGE_SLIDER, PARAM_PITCH))
        self.assertEqual(msgs, [("cc", CC_EDIT_REQUEST, PARAM_PITCH)])
        self.assertEqual(m.title(), "Pitch Shift")

    def test_eq_lists_seven_bands_then_opens_that_bands_slider(self):
        m = self.opened()
        m.rotate(1)
        self.assertEqual(m.push(), [])
        self.assertEqual(m.page, PAGE_BANDS)
        self.assertEqual(m.items(), ("100", "200", "400", "800", "1.6k", "3.2k", "6.4k"))
        m.rotate(3)                        # 800 Hz
        msgs = m.push()
        self.assertEqual((m.page, m.param), (PAGE_SLIDER, 4))
        self.assertEqual(msgs, [("cc", CC_EDIT_REQUEST, 4)])
        self.assertEqual(m.title(), "EQ 800")

    def test_slider_turns_send_relative_cc(self):
        m = self.opened()
        m.push()                           # Level slider
        self.assertEqual(m.rotate(1), [("cc", CC_EDIT_BASE + PARAM_LEVEL, 65)])
        self.assertEqual(m.rotate(-1), [("cc", CC_EDIT_BASE + PARAM_LEVEL, 63)])
        self.assertEqual(m.rotate(5), [("cc", CC_EDIT_BASE + PARAM_LEVEL, 69)])

    def test_slider_cc_value_stays_in_midi_range_on_a_huge_spin(self):
        m = self.opened()
        m.push()
        self.assertEqual(m.rotate(500)[0][2], 127)
        self.assertEqual(m.rotate(-500)[0][2], 1)

    def test_band_slider_uses_its_own_cc(self):
        m = self.opened()
        m.rotate(1); m.push()              # EQ list
        m.rotate(6); m.push()              # 6.4k = param 7
        self.assertEqual(m.rotate(1), [("cc", CC_EDIT_BASE + 7, 65)])

    def test_save_sends_the_save_cc_and_shows_pending_until_the_relay_answers(self):
        m = self.opened()
        m.rotate(3)
        self.assertEqual(m.push(), [("cc", CC_SAVE, 127)])
        self.assertEqual(m.page, PAGE_SAVE)
        self.assertEqual(m.title(), "Save")
        self.assertEqual(m.save_text, SAVE_PENDING_TEXT)
        m.set_save_result("Saved!")
        self.assertEqual(m.save_text, "Saved!")

    def test_turning_on_the_save_page_does_nothing(self):
        m = self.opened()
        m.rotate(3); m.push()
        self.assertEqual(m.rotate(1), [])
        self.assertEqual(m.page, PAGE_SAVE)

    def test_back_and_push_leave_the_save_page_for_the_root_on_save(self):
        m = self.opened()
        m.rotate(3); m.push()
        m.press_menu_key()
        self.assertEqual((m.page, m.cursor, m.active), (PAGE_ROOT, 3, True))
        m.push()                                   # save again
        self.assertEqual(m.save_text, SAVE_PENDING_TEXT)   # not the old result
        m.push()                                   # push on the result page also goes back
        self.assertEqual((m.page, m.cursor), (PAGE_ROOT, 3))

    def test_list_turns_send_nothing(self):
        m = self.opened()
        self.assertEqual(m.rotate(1), [])

    def test_back_from_slider_returns_to_where_you_came_from(self):
        m = self.opened()
        m.rotate(2); m.push()              # Pitch slider
        m.press_menu_key()
        self.assertEqual((m.page, m.cursor, m.active), (PAGE_ROOT, 2, True))

        m.rotate(-1); m.push()             # EQ list
        m.rotate(2); m.push()              # 400 slider
        m.press_menu_key()
        self.assertEqual((m.page, m.cursor), (PAGE_BANDS, 2))
        m.press_menu_key()
        self.assertEqual((m.page, m.cursor), (PAGE_ROOT, 1))
        m.press_menu_key()
        self.assertFalse(m.active)

    def test_pushing_on_a_slider_also_goes_back(self):
        m = self.opened()
        m.push()
        m.push()
        self.assertEqual(m.page, PAGE_ROOT)
        self.assertTrue(m.active)

    def test_other_footswitch_cancels_from_any_depth(self):
        m = self.opened()
        m.rotate(1); m.push(); m.push()    # EQ -> 100 slider
        m.cancel()
        self.assertFalse(m.active)

    def test_reopening_starts_fresh_at_the_top(self):
        m = self.opened()
        m.rotate(1); m.push(); m.push()
        m.cancel()
        m.press_menu_key()
        self.assertEqual((m.page, m.cursor), (PAGE_ROOT, 0))

    def test_slider_shows_dashes_until_the_relay_answers(self):
        m = self.opened()
        m.push()
        self.assertEqual(m.slider_value(), ("--", None))
        m.set_value(PARAM_LEVEL, "+3.5 dB", 62)
        self.assertEqual(m.slider_value(), ("+3.5 dB", 62))

    def test_a_stale_value_is_not_shown_when_a_slider_reopens(self):
        m = self.opened()
        m.push()
        m.set_value(PARAM_LEVEL, "+3.5 dB", 62)
        m.press_menu_key(); m.push()
        self.assertEqual(m.slider_value(), ("--", None))


if __name__ == "__main__":
    unittest.main()
