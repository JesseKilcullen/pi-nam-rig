"""pipedal_edit.py — applies the Pico's settings-menu encoder steps to the
live PiPedal pedalboard, and reports the resulting value back for the OLED.

The Pico sends *relative* steps (midi_logic.EditMenu); this module owns the
actual numbers. For each step it reads the control's current value, moves it
by one step size, clamps it to the control's range and sends PiPedal a
`setControl`. So every preset keeps its own settings, nothing snaps to a
value the Pico guessed, and the number on the OLED is the real one.

Controls are looked up by plugin URI in whatever preset is loaded, so this
keeps working when presets change. A preset that lacks the plugin just
reports "no plugin".

No network or MIDI code lives here (pi_relay.py wires those in), so the whole
thing is unit-tested with a fake client: test_pipedal_edit.py.
"""

import asyncio
from collections import namedtuple

from midi_logic import PARAM_LEVEL, PARAM_EQ_FIRST, PARAM_PITCH, EQ_BAND_LABELS

GRAPHIC_EQ_URI = "http://two-play.com/plugins/toob-graphiceq"
PITCH_SHIFT_URI = "https://github.com/JesseKilcullen/pi-nam-rig/lv2-pitch-shift#mono"
TUNER_URI = "http://two-play.com/plugins/toob-tuner"
TUNER_MUTE_SYMBOL = "MUTE"

# uri/symbol: which plugin control. low/high: its range in real units (the
# plugin TTLs are the truth). step: real-unit change per encoder click.
Param = namedtuple("Param", "uri symbol low high step unit decimals")

EQ_BAND_SYMBOLS = ("gain_100hz", "gain_200hz", "gain_400hz", "gain_800hz",
                   "gain_1600hz", "gain_3200hz", "gain_6400hz")

PARAMS = {
    PARAM_LEVEL: Param(GRAPHIC_EQ_URI, "level", -30.0, 30.0, 0.5, "dB", 1),
    PARAM_PITCH: Param(PITCH_SHIFT_URI, "semitones", -24.0, 24.0, 1.0, "st", 0),
}
for _i, _symbol in enumerate(EQ_BAND_SYMBOLS):
    PARAMS[PARAM_EQ_FIRST + _i] = Param(GRAPHIC_EQ_URI, _symbol, -15.0, 15.0, 0.5, "dB", 1)
assert len(EQ_BAND_SYMBOLS) == len(EQ_BAND_LABELS)

# The pitch shifter only costs latency/CPU while it is powered, so the relay
# powers it with the shift: on whenever the shift is non-zero.
PITCH_POWER_SYMBOL = "power"

NO_PLUGIN_TEXT = "no plugin"
SAVED_TEXT = "Saved!"
SAVE_FAILED_TEXT = "Failed"
# PiPedal applies setSnapshots/saveCurrentPreset on its own threads and sends
# no reply to wait for, so the save is confirmed by reading the pedalboard back.
SAVE_SETTLE_SECONDS = 0.4
SAVE_POLL_SECONDS = 0.1    # how often to ask whether PiPedal has stored the snapshot
SAVE_POLL_TRIES = 15       # ... for up to ~1.5 s


def format_value(param: Param, value: float) -> str:
    """e.g. "+3.5 dB", "-2 st", "0.0 dB". Zero carries no sign."""
    if abs(value) < 10 ** -(param.decimals + 1):
        value = 0.0
    sign = "+" if value > 0 else ""
    return "{}{:.{d}f} {}".format(sign, value, param.unit, d=param.decimals)


def fraction_percent(param: Param, value: float) -> int:
    """Where the value sits in its range, 0-100 (50 == centre)."""
    span = param.high - param.low
    return max(0, min(100, int(round((value - param.low) / span * 100))))


def snap(param: Param, value: float) -> float:
    """Round to the step grid and clamp to the range."""
    snapped = round(value / param.step) * param.step
    return max(param.low, min(param.high, round(snapped, 6)))


def snapshot_value(item):
    """A snapshot's record of one plugin, taken from the live plugin: the same
    five fields PiPedal itself stores per snapshot. The tuner's MUTE is stored
    as off: it follows the footswitch, and a snapshot saved while tuning must
    not come back silent."""
    controls = item.get("controlValues") or []
    if item.get("uri") == TUNER_URI:
        controls = [dict(c, value=0) if c["key"] == TUNER_MUTE_SYMBOL else c for c in controls]
    return {
        "instanceId": item["instanceId"],
        "isEnabled": item["isEnabled"],
        "controlValues": controls,
        "lv2State": item.get("lv2State", [False, {}]),
        "pathProperties": item.get("pathProperties") or {},
    }


def walk_items(items):
    """Every plugin in a pedalboard, including those inside Split chains."""
    for item in items or []:
        yield item
        for key in ("topChain", "bottomChain"):
            sub = item.get(key)
            if isinstance(sub, dict):
                yield from walk_items(sub.get("items"))


class EditController:
    """client needs `async send(message, body)` (pipedal_ws.PiPedalClient).
    emit(param_id, text, fraction) is called with every value to show."""

    def __init__(self, client, client_id, emit):
        self.client = client
        self.client_id = client_id
        self.emit = emit
        self.instances = {}   # plugin uri -> instanceId (first one in the chain)
        self.values = {}      # (instanceId, symbol) -> last known value
        self.mute_wanted = False   # the tuner switch's state, from the Pico

    def load_pedalboard(self, pedalboard):
        """Refresh the instance ids and values from a currentPedalboard-shaped
        dict. Call on every preset change and before reporting a value."""
        self.instances = {}
        self.values = {}
        for item in walk_items((pedalboard or {}).get("items")):
            uri = item.get("uri")
            instance_id = item.get("instanceId")
            if uri is None or instance_id is None:
                continue
            self.instances.setdefault(uri, instance_id)
            for control in item.get("controlValues") or []:
                self.values[(instance_id, control["key"])] = control["value"]

    def on_control_changed(self, instance_id, symbol, value):
        """PiPedal pushed a change (e.g. made from the web UI)."""
        self.values[(instance_id, symbol)] = value

    def _lookup(self, param_id):
        param = PARAMS.get(param_id)
        if param is None:
            return None, None, None
        instance_id = self.instances.get(param.uri)
        if instance_id is None:
            return param, None, None
        return param, instance_id, self.values.get((instance_id, param.symbol), 0.0)

    def report(self, param_id):
        """Send the param's current value to the Pico."""
        param, instance_id, value = self._lookup(param_id)
        if param is None:
            return
        if instance_id is None:
            self.emit(param_id, NO_PLUGIN_TEXT, 50)
            return
        self.emit(param_id, format_value(param, value), fraction_percent(param, value))

    async def apply_steps(self, param_id, steps):
        """Move a control by `steps` clicks (negative = down) and report it."""
        param, instance_id, current = self._lookup(param_id)
        if param is None:
            return
        if instance_id is None:
            self.emit(param_id, NO_PLUGIN_TEXT, 50)
            return

        new_value = snap(param, current + steps * param.step)
        if new_value != current:
            await self._set(instance_id, param.symbol, new_value)
            if param_id == PARAM_PITCH:
                await self._set(instance_id, PITCH_POWER_SYMBOL, 1.0 if new_value != 0 else 0.0)
        self.emit(param_id, format_value(param, new_value), fraction_percent(param, new_value))

    async def set_mute(self, on):
        """The Pico's TUNER/MUTE switch: mute the tuner plugin's output, which
        silences everything after it (it is first in every chain)."""
        self.mute_wanted = bool(on)
        await self.apply_mute()

    async def apply_mute(self):
        """Make the loaded preset's tuner match the switch. Also called after
        every preset load, since a new preset arrives with its own saved MUTE."""
        instance_id = self.instances.get(TUNER_URI)
        if instance_id is None:
            return
        wanted = 1.0 if self.mute_wanted else 0.0
        if self.values.get((instance_id, TUNER_MUTE_SYMBOL), 0.0) != wanted:
            await self._set(instance_id, TUNER_MUTE_SYMBOL, wanted)

    async def save(self, settle_seconds=SAVE_SETTLE_SECONDS, poll_seconds=SAVE_POLL_SECONDS):
        """What PiPedal's UI needs two clicks for: store the sound as it is
        now in the selected snapshot, then save the preset. (A control moved
        while a snapshot is selected only marks the snapshot "modified"; the
        next preset load or snapshot change throws it away.) Returns the text
        to show on the Pico.

        The order matters and PiPedal gives no reply to wait on: if the preset
        is saved while PiPedal still counts the snapshot as modified, it
        clears the snapshot selection (in memory and on disk), which loses the
        OLED highlight. So the snapshot is stored first and the preset is only
        saved once PiPedal reports it unmodified; and if the selection still
        went missing, it is re-selected and the preset saved again."""
        pedalboard = await self.client.request("currentPedalboard")
        snapshots = pedalboard.get("snapshots") or []
        selected = pedalboard.get("selectedSnapshot")
        has_snapshot = (selected is not None and 0 <= selected < len(snapshots)
                        and snapshots[selected])

        if has_snapshot:
            snapshots[selected]["values"] = [snapshot_value(item) for item in walk_items(pedalboard.get("items"))]
            snapshots[selected]["isModified"] = False
            await self.client.send("setSnapshots", {"snapshots": snapshots, "selectedSnapshot": selected})
            for _ in range(SAVE_POLL_TRIES):
                current = await self.client.request("currentPedalboard")
                stored = (current.get("snapshots") or [None] * (selected + 1))[selected]
                if stored and not stored.get("isModified"):
                    break
                await asyncio.sleep(poll_seconds)

        await self.client.send("saveCurrentPreset")
        await asyncio.sleep(settle_seconds)
        after = await self.client.request("currentPedalboard")

        if has_snapshot and after.get("selectedSnapshot") != selected:
            await self.client.send("setSnapshot", selected)
            await asyncio.sleep(settle_seconds)
            await self.client.send("saveCurrentPreset")
            await asyncio.sleep(settle_seconds)
            after = await self.client.request("currentPedalboard")

        if has_snapshot:
            stored = (after.get("snapshots") or [None] * (selected + 1))[selected]
            if not stored or stored.get("isModified") or after.get("selectedSnapshot") != selected:
                return SAVE_FAILED_TEXT
        return SAVED_TEXT

    async def _set(self, instance_id, symbol, value):
        self.values[(instance_id, symbol)] = value
        await self.client.send("setControl", {
            "clientId": self.client_id,
            "instanceId": instance_id,
            "symbol": symbol,
            "value": value,
        })
