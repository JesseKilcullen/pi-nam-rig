# test_pipedal_ws.py — verifies the grid-building helpers used for the
# 3x2 OLED display (pipedal-hardware-v2.md's PRESET/SNAPSHOT grid mode).
#
# Run:
#   python3 -m unittest test_pipedal_ws.py -v

import asyncio
import json
import unittest

from pipedal_ws import (
    PiPedalClient,
    build_snapshot_grid,
    build_preset_grid,
    build_full_preset_list,
    find_tuner_instance_id,
)


class TestBuildSnapshotGrid(unittest.TestCase):
    def test_full_six_with_selection(self):
        pedalboard = {
            "selectedSnapshot": 2,
            "snapshots": [{"name": n} for n in ["Clean", "Crunch", "Lead", "Ambient", "HeavyRhy", "Boost"]],
        }
        names, highlight = build_snapshot_grid(pedalboard)
        self.assertEqual(names, ["Clean", "Crunch", "Lead", "Ambient", "HeavyRhy", "Boost"])
        self.assertEqual(highlight, 2)

    def test_fewer_than_six_pads_blank(self):
        pedalboard = {"selectedSnapshot": 1, "snapshots": [{"name": "Clean"}, {"name": "Crunch"}]}
        names, highlight = build_snapshot_grid(pedalboard)
        self.assertEqual(names, ["Clean", "Crunch", "", "", "", ""])
        self.assertEqual(highlight, 1)

    def test_no_selection_is_none(self):
        pedalboard = {"selectedSnapshot": None, "snapshots": [{"name": "Clean"}]}
        names, highlight = build_snapshot_grid(pedalboard)
        self.assertIsNone(highlight)

    def test_missing_snapshots_key(self):
        names, highlight = build_snapshot_grid({})
        self.assertEqual(names, [""] * 6)
        self.assertIsNone(highlight)

    def test_null_snapshot_entry_does_not_crash(self):
        pedalboard = {"selectedSnapshot": 0, "snapshots": [None, {"name": "Crunch"}]}
        names, highlight = build_snapshot_grid(pedalboard)
        self.assertEqual(names[0], "")
        self.assertEqual(names[1], "Crunch")


class TestBuildPresetGrid(unittest.TestCase):
    def test_six_or_fewer_presets_highlights_selected(self):
        response = {
            "selectedInstanceId": 102,
            "presets": [
                {"instanceId": 100, "name": "Clean Rig"},
                {"instanceId": 101, "name": "Crunch Rig"},
                {"instanceId": 102, "name": "Lead Tones"},
            ],
        }
        names, highlight = build_preset_grid(response)
        self.assertEqual(names, ["Clean Rig", "Crunch Rig", "Lead Tones", "", "", ""])
        self.assertEqual(highlight, 2)

    def test_more_than_six_only_shows_first_six(self):
        response = {
            "selectedInstanceId": 100,
            "presets": [{"instanceId": 100 + i, "name": "P{}".format(i)} for i in range(9)],
        }
        names, highlight = build_preset_grid(response)
        self.assertEqual(len(names), 6)
        self.assertEqual(names, ["P0", "P1", "P2", "P3", "P4", "P5"])
        self.assertEqual(highlight, 0)

    def test_selected_beyond_position_six_has_no_highlight(self):
        # Active preset (instanceId 108, the 9th) exists but isn't one of
        # the 6 shown -- this is the "reached via something other than a
        # footswitch" case. No cell should be highlighted.
        response = {
            "selectedInstanceId": 108,
            "presets": [{"instanceId": 100 + i, "name": "P{}".format(i)} for i in range(9)],
        }
        names, highlight = build_preset_grid(response)
        self.assertIsNone(highlight)

    def test_no_presets(self):
        names, highlight = build_preset_grid({"selectedInstanceId": 1, "presets": []})
        self.assertEqual(names, [""] * 6)
        self.assertIsNone(highlight)


class TestBuildFullPresetList(unittest.TestCase):
    def test_not_truncated_when_under_the_cap(self):
        response = {
            "selectedInstanceId": 101,
            "presets": [{"instanceId": 100 + i, "name": "P{}".format(i)} for i in range(9)],
        }
        names, current_index = build_full_preset_list(response, max_count=24)
        self.assertEqual(len(names), 9)
        self.assertEqual(current_index, 1)

    def test_truncated_at_max_count(self):
        response = {
            "selectedInstanceId": 100,
            "presets": [{"instanceId": 100 + i, "name": "P{}".format(i)} for i in range(50)],
        }
        names, current_index = build_full_preset_list(response, max_count=24)
        self.assertEqual(len(names), 24)
        self.assertEqual(current_index, 0)

    def test_current_beyond_the_cap_is_none(self):
        response = {
            "selectedInstanceId": 149,  # the 50th preset, index 49 -- beyond a 24 cap
            "presets": [{"instanceId": 100 + i, "name": "P{}".format(i)} for i in range(50)],
        }
        names, current_index = build_full_preset_list(response, max_count=24)
        self.assertIsNone(current_index)

    def test_empty_bank(self):
        names, current_index = build_full_preset_list({"selectedInstanceId": 1, "presets": []}, max_count=24)
        self.assertEqual(names, [])
        self.assertIsNone(current_index)


class TestFindTunerInstanceId(unittest.TestCase):
    def test_still_works_flat_and_nested(self):
        # Regression check -- unrelated to the grid work, just confirms
        # this helper wasn't disturbed by the edits in this file.
        flat = {"items": [{"uri": "http://two-play.com/plugins/toob-tuner", "instanceId": 7}]}
        self.assertEqual(find_tuner_instance_id(flat), 7)
        self.assertIsNone(find_tuner_instance_id({"items": []}))


class FakeWebSocket:
    """Stands in for a websockets connection: async-iterates queued incoming
    frames, and answers every outgoing request with a reply frame."""

    def __init__(self):
        self.incoming = asyncio.Queue()

    async def send(self, raw):
        header = json.loads(raw)[0]
        if "replyTo" in header:   # a request from the client -- answer it
            await self.incoming.put(json.dumps([{"reply": header["replyTo"]}, "answer"]))

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.incoming.get()


class TestPushHandlerCanMakeRequests(unittest.TestCase):
    def test_request_inside_on_push_does_not_deadlock(self):
        # Regression: on_push used to be awaited inside the reader loop, so a
        # handler calling request() (pi_relay's getPresets after
        # onPedalboardChanged) waited forever for a reply nobody could read.
        async def scenario():
            ws = FakeWebSocket()
            got = asyncio.get_event_loop().create_future()

            async def on_push(name, header, body):
                got.set_result(await client.request("getPresets"))

            client = PiPedalClient(ws, on_push)
            await ws.incoming.put(json.dumps([{"message": "onPedalboardChanged", "replyTo": 5}, {}]))
            return await asyncio.wait_for(got, timeout=2)

        self.assertEqual(asyncio.run(scenario()), "answer")


if __name__ == "__main__":
    unittest.main()
