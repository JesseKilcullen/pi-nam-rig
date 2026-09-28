# midi_logic.py — hardware-agnostic footswitch state machine.
#
# Pure Python, no CircuitPython/board/digitalio/usb_midi imports, so it runs
# and can be unit-tested (test_midi_logic.py) on any machine with plain
# Python 3 — no Pico, no wiring, nothing plugged in.
#
# code.py (the actual firmware) imports this module and is the only piece
# that talks to real GPIO/USB MIDI. Keeping the decision logic here means the
# MIDI mapping in pipedal-hardware-v2.md §3 can be verified before any
# hardware exists.
#
# Messages are returned as plain tuples so tests don't need a MIDI library:
#   ("cc", number, value)   -> Control Change
#   ("pc", number)          -> Program Change

CC_SNAPSHOT_BASE = 20   # CC20-25 select snapshot 1-6 (row index 0-5)
CC_TUNER = 26
CC_MUTE = 27

# Pi -> Pico direction only (pi_relay.py sends these, code.py's oled_display
# reads them). Separate address space from the footswitch CCs above, which
# only ever go Pico -> Pi. See pi_relay.py's docstring for why these two
# directions can share one USB MIDI cable without conflicting.
CC_TUNER_NOTE = 28   # value = MIDI note number (0-127)
CC_TUNER_CENTS = 29  # value = round(cents) + 64 (64 == 0 cents), clamped 0-127

SYSEX_MANUFACTURER_ID = 0x7D  # MMA-reserved "non-commercial / educational"

# data[0] for each SysEx type. Each carries a 3x2 grid update: one highlight
# index byte (0-5, or NO_HIGHLIGHT if the active item isn't one of the 6
# shown) followed by up to 6 names, each 0x00-separated. Pico-side rendering
# is oled_display.show_grid(); Pi-side building is pi_relay.py.
SYSEX_SNAPSHOT_LIST_SUBTYPE = 0x01
SYSEX_PRESET_LIST_SUBTYPE = 0x02
# SysEx data bytes are 7-bit only (0-127) -- 0xFF is NOT valid here, unlike
# a plain CC value. 127 is safely outside the real 0-5 highlight range.
GRID_HIGHLIGHT_NONE = 0x7F

# Full preset list (not capped at 6) for the rotary-encoder Browse feature —
# separate from the 3x2 grid update above, which only ever shows the first
# 6 (what the footswitches reach). data[0] = subtype, data[1:] = names,
# 0x00-separated, no highlight byte (the Pico tracks its own browse cursor
# locally, see BrowseState below).
SYSEX_FULL_PRESET_LIST_SUBTYPE = 0x03
BROWSE_MAX_PRESETS = 24  # plenty for a real bank; caps the SysEx size

MODE_SNAPSHOT = "SNAPSHOT"
MODE_PRESET = "PRESET"


class FootswitchState:
    """Tracks mode + tuner/mute toggle; turns button presses into MIDI messages.

    Matches pipedal-hardware-v2.md §3 exactly. Row indices are 0-5 for
    switches 1-6.
    """

    def __init__(self):
        self.mode = MODE_SNAPSHOT
        self.tuner_mute_on = False

    def press_row(self, index):
        if not 0 <= index <= 5:
            raise ValueError("row index must be 0-5")

        if self.mode == MODE_SNAPSHOT:
            return [("cc", CC_SNAPSHOT_BASE + index, 127)]

        # PRESET mode: select preset, force snapshot 1, drop back to SNAPSHOT
        self.mode = MODE_SNAPSHOT
        return [
            ("pc", index),
            ("cc", CC_SNAPSHOT_BASE, 127),
        ]

    def press_mode_preset(self):
        self.mode = MODE_PRESET
        return []

    def press_mode_snapshot(self):
        self.mode = MODE_SNAPSHOT
        return []

    def press_reset(self):
        self.mode = MODE_SNAPSHOT
        return [
            ("pc", 0),
            ("cc", CC_SNAPSHOT_BASE, 127),
        ]

    def press_tuner_mute(self):
        self.tuner_mute_on = not self.tuner_mute_on
        value = 127 if self.tuner_mute_on else 0
        return [
            ("cc", CC_TUNER, value),
            ("cc", CC_MUTE, value),
        ]

    def led_state(self):
        """Returns (preset_led_on, snapshot_led_on)."""
        return (self.mode == MODE_PRESET, self.mode == MODE_SNAPSHOT)


class BrowseState:
    """The rotary encoder's preset-browse feature: scroll through every
    preset in the bank (not just the 6 on footswitches), preview on the
    OLED, confirm with the encoder's push switch. Nothing is sent to
    PiPedal while scrolling — only confirm() actually selects a preset.

    Pure logic, no MIDI/GPIO here — code.py reads encoder.position deltas
    and the push-switch edge, and calls into this.
    """

    def __init__(self):
        self.active = False
        self.cursor = 0

    def rotate(self, delta, preset_count, current_index=None):
        """delta: +1/-1 (or more, for a fast spin) per encoder step.
        preset_count: how many real presets are currently known (from the
        Pi's full list) — 0 means "not loaded yet", ignore the turn.
        current_index: the actually-loaded preset's position in that same
        full list (or None if unknown/not in it) — used only on the turn
        that *enters* browse mode, so the first turn moves relative to
        what's already playing instead of always jumping to preset 0."""
        if preset_count <= 0:
            return
        if not self.active:
            self.active = True
            base = current_index if current_index is not None else 0
            self.cursor = (base + delta) % preset_count
        else:
            self.cursor = (self.cursor + delta) % preset_count

    def confirm(self):
        """Returns the PC + force-snapshot-1 messages for whichever preset
        is currently under the cursor, same shape as FootswitchState's
        preset-select — and exits browse mode."""
        index = self.cursor
        self.active = False
        return [
            ("pc", index),
            ("cc", CC_SNAPSHOT_BASE, 127),
        ]

    def cancel(self):
        """Any other footswitch/mode press, or a timeout, cancels browse
        without selecting anything."""
        self.active = False


# Reverse mapping used by midi_monitor.py to decode traffic back into
# human-readable control names, kept next to the forward logic so the two
# can't drift apart.
def describe(message):
    kind = message[0]
    if kind == "pc":
        return "preset {}".format(message[1] + 1)
    if kind == "cc":
        _, number, value = message
        if CC_SNAPSHOT_BASE <= number <= CC_SNAPSHOT_BASE + 5:
            return "snapshot {} select ({})".format(
                number - CC_SNAPSHOT_BASE + 1, "on" if value else "off"
            )
        if number == CC_TUNER:
            return "tuner {}".format("on" if value else "off")
        if number == CC_MUTE:
            return "mute {}".format("on" if value else "off")
        return "CC{} = {}".format(number, value)
    return str(message)
