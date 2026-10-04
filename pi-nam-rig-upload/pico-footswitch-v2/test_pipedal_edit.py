# test_pipedal_edit.py — the Pi-side half of the settings menu, against a fake
# PiPedal connection. Run: python3 -m unittest test_pipedal_edit -v

import asyncio
import unittest

import copy

from midi_logic import PARAM_LEVEL, PARAM_EQ_FIRST, PARAM_PITCH
from pipedal_edit import (
    EditController,
    TUNER_URI,
    SAVED_TEXT,
    SAVE_FAILED_TEXT,
    snapshot_value,
    GRAPHIC_EQ_URI,
    PITCH_SHIFT_URI,
    PARAMS,
    format_value,
    fraction_percent,
    snap,
)


class FakeClient:
    def __init__(self, pedalboards=None):
        self.sent = []
        self.requests = []
        self._pedalboards = list(pedalboards or [])

    async def send(self, message, body=None):
        self.sent.append((message, body))

    async def request(self, message, body=None):
        self.requests.append(message)
        # the last canned pedalboard repeats once the list runs out
        return self._pedalboards.pop(0) if len(self._pedalboards) > 1 else self._pedalboards[0]


def pedalboard(level=0.0, band_400=0.0, semitones=0.0, power=0.0, with_plugins=True, mute=0.0):
    items = [{"instanceId": 1, "uri": TUNER_URI, "controlValues": [{"key": "MUTE", "value": mute}]}]
    if with_plugins:
        items.append({"instanceId": 2, "uri": PITCH_SHIFT_URI, "controlValues": [
            {"key": "semitones", "value": semitones}, {"key": "power", "value": power}]})
        # A split chain, to prove nested plugins are found too.
        items.append({"instanceId": 3, "uri": "uri://two-play/pipedal/pedalboard#Split", "controlValues": [],
                      "topChain": {"items": [{"instanceId": 4, "uri": GRAPHIC_EQ_URI, "controlValues": [
                          {"key": "level", "value": level}, {"key": "gain_400hz", "value": band_400}]}]},
                      "bottomChain": {"items": []}})
    return {"items": items}


class Harness:
    def __init__(self, **kw):
        self.client = FakeClient()
        self.shown = []
        self.ctl = EditController(self.client, 22, lambda *a: self.shown.append(a))
        self.ctl.load_pedalboard(pedalboard(**kw))

    def step(self, param, n):
        asyncio.run(self.ctl.apply_steps(param, n))

    def sets(self):
        return [(b["instanceId"], b["symbol"], b["value"]) for m, b in self.client.sent if m == "setControl"]


class TestHelpers(unittest.TestCase):
    def test_format_value(self):
        self.assertEqual(format_value(PARAMS[PARAM_LEVEL], 3.5), "+3.5 dB")
        self.assertEqual(format_value(PARAMS[PARAM_LEVEL], -12.0), "-12.0 dB")
        self.assertEqual(format_value(PARAMS[PARAM_LEVEL], 0.0), "0.0 dB")
        self.assertEqual(format_value(PARAMS[PARAM_PITCH], 7.0), "+7 st")
        self.assertEqual(format_value(PARAMS[PARAM_PITCH], -2.0), "-2 st")
        self.assertEqual(format_value(PARAMS[PARAM_PITCH], 0.0), "0 st")

    def test_fraction_is_centred_on_zero(self):
        self.assertEqual(fraction_percent(PARAMS[PARAM_LEVEL], 0.0), 50)
        self.assertEqual(fraction_percent(PARAMS[PARAM_LEVEL], -30.0), 0)
        self.assertEqual(fraction_percent(PARAMS[PARAM_LEVEL], 30.0), 100)
        self.assertEqual(fraction_percent(PARAMS[PARAM_PITCH], 12.0), 75)

    def test_snap_clamps_and_rounds_to_the_step(self):
        self.assertEqual(snap(PARAMS[PARAM_LEVEL], 0.7), 0.5)
        self.assertEqual(snap(PARAMS[PARAM_LEVEL], 99), 30.0)
        self.assertEqual(snap(PARAMS[PARAM_PITCH], -99), -24.0)
        self.assertEqual(snap(PARAMS[PARAM_PITCH], 2.6), 3.0)


class TestApplySteps(unittest.TestCase):
    def test_level_steps_half_a_db_per_click_on_the_graphic_eq(self):
        h = Harness(level=1.0)
        h.step(PARAM_LEVEL, 2)
        self.assertEqual(h.sets(), [(4, "level", 2.0)])
        self.assertEqual(h.shown[-1], (PARAM_LEVEL, "+2.0 dB", 53))

    def test_steps_accumulate_from_the_last_value(self):
        h = Harness()
        h.step(PARAM_LEVEL, 1)
        h.step(PARAM_LEVEL, 1)
        h.step(PARAM_LEVEL, -3)
        self.assertEqual([v for _, _, v in h.sets()], [0.5, 1.0, -0.5])

    def test_eq_band_uses_its_own_symbol(self):
        h = Harness(band_400=-3.0)
        h.step(PARAM_EQ_FIRST + 2, 4)
        self.assertEqual(h.sets(), [(4, "gain_400hz", -1.0)])
        self.assertEqual(h.shown[-1][1], "-1.0 dB")

    def test_eq_band_clamps_at_plus_minus_15(self):
        h = Harness(band_400=14.5)
        h.step(PARAM_EQ_FIRST + 2, 10)
        self.assertEqual(h.sets(), [(4, "gain_400hz", 15.0)])
        h.step(PARAM_EQ_FIRST + 2, 10)           # already at the limit: nothing more to send
        self.assertEqual(len(h.sets()), 1)
        self.assertEqual(h.shown[-1][1], "+15.0 dB")

    def test_pitch_moves_a_semitone_per_click_and_powers_on(self):
        h = Harness()
        h.step(PARAM_PITCH, -2)
        self.assertEqual(h.sets(), [(2, "semitones", -2.0), (2, "power", 1.0)])
        self.assertEqual(h.shown[-1], (PARAM_PITCH, "-2 st", 46))

    def test_pitch_powers_off_when_it_returns_to_zero(self):
        h = Harness(semitones=1.0, power=1.0)
        h.step(PARAM_PITCH, -1)
        self.assertEqual(h.sets(), [(2, "semitones", 0.0), (2, "power", 0.0)])

    def test_pitch_range_is_two_octaves(self):
        h = Harness(semitones=23.0, power=1.0)
        h.step(PARAM_PITCH, 5)
        self.assertEqual(h.sets()[0], (2, "semitones", 24.0))

    def test_preset_without_the_plugins_reports_it_and_sends_nothing(self):
        h = Harness(with_plugins=False)
        h.step(PARAM_LEVEL, 1)
        h.step(PARAM_PITCH, 1)
        self.assertEqual(h.client.sent, [])
        self.assertEqual(h.shown, [(PARAM_LEVEL, "no plugin", 50), (PARAM_PITCH, "no plugin", 50)])

    def test_unknown_param_is_ignored(self):
        h = Harness()
        h.step(99, 1)
        self.assertEqual((h.client.sent, h.shown), ([], []))

    def test_setcontrol_body_carries_the_client_id(self):
        h = Harness()
        h.step(PARAM_LEVEL, 1)
        self.assertEqual(h.client.sent[0], ("setControl",
                         {"clientId": 22, "instanceId": 4, "symbol": "level", "value": 0.5}))


class TestReportAndRefresh(unittest.TestCase):
    def test_report_sends_the_current_value(self):
        h = Harness(level=-4.5)
        h.ctl.report(PARAM_LEVEL)
        self.assertEqual(h.shown, [(PARAM_LEVEL, "-4.5 dB", 42)])

    def test_report_with_no_plugin(self):
        h = Harness(with_plugins=False)
        h.ctl.report(PARAM_PITCH)
        self.assertEqual(h.shown, [(PARAM_PITCH, "no plugin", 50)])

    def test_loading_a_new_preset_replaces_old_values(self):
        h = Harness(level=5.0)
        h.ctl.load_pedalboard(pedalboard(level=-2.0))
        h.ctl.report(PARAM_LEVEL)
        self.assertEqual(h.shown[-1][1], "-2.0 dB")

    def test_changes_made_in_the_web_ui_are_picked_up(self):
        h = Harness()
        h.ctl.on_control_changed(4, "level", 6.0)
        h.step(PARAM_LEVEL, 1)
        self.assertEqual(h.sets(), [(4, "level", 6.5)])


class TestTunerMute(unittest.TestCase):
    def test_switch_on_mutes_the_tuner_and_off_unmutes(self):
        h = Harness()
        asyncio.run(h.ctl.set_mute(True))
        asyncio.run(h.ctl.set_mute(False))
        self.assertEqual(h.sets(), [(1, "MUTE", 1.0), (1, "MUTE", 0.0)])

    def test_repeating_the_same_state_sends_nothing(self):
        h = Harness()
        asyncio.run(h.ctl.set_mute(True))
        asyncio.run(h.ctl.set_mute(True))
        self.assertEqual(h.sets(), [(1, "MUTE", 1.0)])

    def test_a_newly_loaded_preset_is_muted_if_the_switch_is_on(self):
        h = Harness()
        asyncio.run(h.ctl.set_mute(True))
        h.ctl.load_pedalboard(pedalboard(mute=0.0))        # new preset arrives unmuted
        asyncio.run(h.ctl.apply_mute())
        self.assertEqual(h.sets()[-1], (1, "MUTE", 1.0))

    def test_a_preset_saved_while_muted_is_unmuted_on_load_when_the_switch_is_off(self):
        h = Harness()
        h.ctl.load_pedalboard(pedalboard(mute=1.0))        # saved with MUTE on
        asyncio.run(h.ctl.apply_mute())
        self.assertEqual(h.sets(), [(1, "MUTE", 0.0)])

    def test_nothing_to_do_when_the_preset_matches(self):
        h = Harness()
        asyncio.run(h.ctl.apply_mute())
        self.assertEqual(h.sets(), [])

    def test_no_tuner_in_the_preset_is_fine(self):
        h = Harness()
        h.ctl.load_pedalboard({"items": []})
        asyncio.run(h.ctl.set_mute(True))
        self.assertEqual(h.client.sent, [])

    def test_a_snapshot_never_stores_the_tuner_muted(self):
        item = {"instanceId": 1, "uri": TUNER_URI, "isEnabled": True,
                "controlValues": [{"key": "MUTE", "value": 1}, {"key": "REFFREQ", "value": 440}]}
        stored = snapshot_value(item)["controlValues"]
        self.assertEqual({c["key"]: c["value"] for c in stored}, {"MUTE": 0, "REFFREQ": 440})
        self.assertEqual(item["controlValues"][0]["value"], 1)   # the live item is untouched


def saveable(selected=1, modified=True):
    """A pedalboard as PiPedal reports it: live values differ from the stored snapshot."""
    pb = pedalboard(level=3.0, semitones=-2.0, power=1.0)
    for item in pb["items"]:
        item.setdefault("isEnabled", True)
        item.setdefault("lv2State", [False, {}])
        item.setdefault("pathProperties", {})
    pb["items"][2]["topChain"]["items"][0].update(isEnabled=True, lv2State=[False, {}], pathProperties={})
    pb["snapshots"] = [
        {"name": "Clean", "color": "blue", "isModified": False, "values": [{"instanceId": 1, "stale": True}]},
        {"name": "Drive", "color": "red", "isModified": modified, "values": [{"instanceId": 1, "stale": True}]},
    ]
    pb["selectedSnapshot"] = selected
    return pb


class TestSave(unittest.TestCase):
    def run_save(self, *pedalboards):
        """pedalboards: what PiPedal reports on each successive read (the last repeats)."""
        client = FakeClient(list(pedalboards))
        ctl = EditController(client, 22, lambda *a: None)
        text = asyncio.run(ctl.save(settle_seconds=0, poll_seconds=0))
        return client, text

    def test_stores_live_values_in_the_selected_snapshot_then_saves_the_preset(self):
        before = saveable(selected=1)
        after = copy.deepcopy(before)
        after["snapshots"][1]["isModified"] = False
        client, text = self.run_save(before, after)

        self.assertEqual([m for m, _ in client.sent], ["setSnapshots", "saveCurrentPreset"])
        body = client.sent[0][1]
        self.assertEqual(body["selectedSnapshot"], 1)
        saved = body["snapshots"][1]
        self.assertFalse(saved["isModified"])
        by_id = {v["instanceId"]: v for v in saved["values"]}
        self.assertEqual(sorted(by_id), [1, 2, 3, 4])            # every plugin: the split node and what is inside it
        self.assertEqual({c["key"]: c["value"] for c in by_id[4]["controlValues"]}["level"], 3.0)
        self.assertEqual({c["key"]: c["value"] for c in by_id[2]["controlValues"]}["semitones"], -2.0)
        self.assertEqual(set(by_id[2]), {"instanceId", "isEnabled", "controlValues", "lv2State", "pathProperties"})
        self.assertEqual(text, SAVED_TEXT)

    def test_other_snapshots_are_left_alone(self):
        before = saveable(selected=1)
        after = copy.deepcopy(before)
        after["snapshots"][1]["isModified"] = False
        client, _ = self.run_save(before, after)
        untouched = client.sent[0][1]["snapshots"][0]
        self.assertEqual(untouched["values"], [{"instanceId": 1, "stale": True}])
        self.assertEqual(untouched["name"], "Clean")

    def test_snapshot_still_marked_modified_afterwards_is_a_failure(self):
        before = saveable(selected=1)
        client, text = self.run_save(before, copy.deepcopy(before))   # PiPedal still says modified
        self.assertEqual(text, SAVE_FAILED_TEXT)

    def test_the_preset_is_only_saved_once_pipedal_reports_the_snapshot_stored(self):
        before = saveable(selected=1)                                  # modified
        still = copy.deepcopy(before)                                  # still modified on the first poll
        done = copy.deepcopy(before)
        done["snapshots"][1]["isModified"] = False
        client, text = self.run_save(before, still, done)
        # three reads happened before the save went out (initial, poll 1, poll 2)
        self.assertEqual([m for m, _ in client.sent], ["setSnapshots", "saveCurrentPreset"])
        self.assertEqual(client.requests[:3], ["currentPedalboard"] * 3)
        self.assertEqual(text, SAVED_TEXT)

    def test_a_lost_snapshot_selection_is_restored_and_the_preset_saved_again(self):
        before = saveable(selected=1)
        stored = copy.deepcopy(before)
        stored["snapshots"][1]["isModified"] = False
        lost = copy.deepcopy(stored)
        lost["selectedSnapshot"] = -1                                  # PiPedal cleared it while saving
        client, text = self.run_save(before, stored, lost, stored)
        self.assertEqual([m for m, _ in client.sent],
                         ["setSnapshots", "saveCurrentPreset", "setSnapshot", "saveCurrentPreset"])
        self.assertEqual(client.sent[2][1], 1)
        self.assertEqual(text, SAVED_TEXT)

    def test_no_snapshot_selected_just_saves_the_preset(self):
        before = saveable(selected=-1)
        client, text = self.run_save(before, copy.deepcopy(before))
        self.assertEqual([m for m, _ in client.sent], ["saveCurrentPreset"])
        self.assertEqual(text, SAVED_TEXT)

    def test_snapshot_value_copies_the_live_plugin(self):
        item = {"instanceId": 9, "isEnabled": False, "controlValues": [{"key": "a", "value": 1}],
                "lv2State": [True, {"x": 1}], "pathProperties": {"p": "q"}, "uri": "ignored", "title": "ignored"}
        self.assertEqual(snapshot_value(item), {"instanceId": 9, "isEnabled": False,
                         "controlValues": [{"key": "a", "value": 1}], "lv2State": [True, {"x": 1}],
                         "pathProperties": {"p": "q"}})


if __name__ == "__main__":
    unittest.main()
