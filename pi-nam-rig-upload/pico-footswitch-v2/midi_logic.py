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

# ── Settings menu (RESET switch + rotary encoder) ──────────────────────────
# Pico -> Pi: the encoder never sets a value itself. Each turn sends a
# *relative* step to pi_relay.py, which applies it to the live plugin through
# PiPedal's API (so every preset keeps its own values and the OLED shows the
# real number, not a guess).
#   CC30 + param id   value = 64 + steps turned (63 = one click down, 65 = up)
#   CC39              "send me this param's current value", value = param id
# PiPedal also receives these on the same cable and ignores them (it only
# binds CC20-27).
#   CC40              "save the selected snapshot, then the preset" (value 127)
CC_EDIT_BASE = 30
CC_EDIT_REQUEST = 39
CC_SAVE = 40
EDIT_RELATIVE_ZERO = 64

# Pi -> Pico: current value of one param, for the slider page.
#   data = [0x04, param id, fraction 0-100, text bytes...]
# fraction is where the value sits in the param's range (50 == centre).
SYSEX_EDIT_VALUE_SUBTYPE = 0x04
# Pi -> Pico: the result of a save request. data = [0x05, text bytes...]
SYSEX_SAVE_RESULT_SUBTYPE = 0x05
SAVE_PENDING_TEXT = "Saving..."

# Param ids. pi_relay.py's table (pipedal_edit.py) maps each to a plugin
# control; the Pico only needs the ids and the labels.
PARAM_LEVEL = 0
PARAM_EQ_FIRST = 1           # 1-7 = the seven Graphic EQ bands, low to high
PARAM_PITCH = 8
EQ_BAND_LABELS = ("100", "200", "400", "800", "1.6k", "3.2k", "6.4k")

MENU_ROOT_ITEMS = ("Level", "EQ", "Pitch Shift", "Save")
ROOT_LEVEL, ROOT_EQ, ROOT_PITCH, ROOT_SAVE = range(4)
PAGE_ROOT = "root"
PAGE_BANDS = "bands"
PAGE_SLIDER = "slider"
PAGE_SAVE = "save"


class EditMenu:
    """The RESET-switch settings menu: Level / EQ / Pitch Shift.

    RESET opens it and then acts as "back one page" (from the first page it
    closes the menu). The encoder scrolls the list pages and, on a slider
    page, turns into value steps. Pushing the encoder selects an item; on a
    slider it also goes back one page (the value is already live).

    "Save" asks the relay to store the current sound in the selected snapshot
    and then save the preset (what PiPedal's UI needs two clicks for), and
    shows the result. Without it, edits only last until the next preset load.

    Pure logic, like BrowseState: code.py feeds it presses and encoder
    deltas, and sends whatever messages come back.
    """

    def __init__(self):
        self.active = False
        self.page = PAGE_ROOT
        self.cursor = 0
        self.param = None
        # param id -> (text, fraction 0-100), as last reported by the relay
        self.values = {}
        self.save_text = SAVE_PENDING_TEXT

    # ── navigation ──
    def press_menu_key(self):
        """The RESET switch: open the menu, or go back one page."""
        if not self.active:
            self.active = True
            self.page = PAGE_ROOT
            self.cursor = 0
            self.param = None
            return []
        return self.back()

    def back(self):
        if self.page == PAGE_SAVE:
            self.page = PAGE_ROOT
            self.cursor = ROOT_SAVE
        elif self.page == PAGE_SLIDER:
            if self.param is not None and PARAM_EQ_FIRST <= self.param < PARAM_EQ_FIRST + len(EQ_BAND_LABELS):
                self.page = PAGE_BANDS
                self.cursor = self.param - PARAM_EQ_FIRST
            else:
                self.page = PAGE_ROOT
                self.cursor = ROOT_LEVEL if self.param == PARAM_LEVEL else ROOT_PITCH
            self.param = None
        elif self.page == PAGE_BANDS:
            self.page = PAGE_ROOT
            self.cursor = ROOT_EQ
        else:
            self.active = False
        return []

    def cancel(self):
        """Any other footswitch press: leave the menu entirely."""
        self.active = False
        self.param = None

    def rotate(self, delta):
        if self.page == PAGE_SLIDER:
            steps = max(-63, min(63, delta))
            return [("cc", CC_EDIT_BASE + self.param, EDIT_RELATIVE_ZERO + steps)]
        if self.page == PAGE_SAVE:
            return []
        self.cursor = (self.cursor + delta) % len(self.items())
        return []

    def push(self):
        """The encoder's push switch."""
        if self.page in (PAGE_SLIDER, PAGE_SAVE):
            return self.back()
        if self.page == PAGE_BANDS:
            return self._open_slider(PARAM_EQ_FIRST + self.cursor)
        if self.cursor == ROOT_LEVEL:
            return self._open_slider(PARAM_LEVEL)
        if self.cursor == ROOT_EQ:
            self.page = PAGE_BANDS
            self.cursor = 0
            return []
        if self.cursor == ROOT_PITCH:
            return self._open_slider(PARAM_PITCH)
        self.page = PAGE_SAVE
        self.save_text = SAVE_PENDING_TEXT
        return [("cc", CC_SAVE, 127)]

    def _open_slider(self, param):
        self.page = PAGE_SLIDER
        self.param = param
        self.values.pop(param, None)   # don't show a stale number while waiting
        return [("cc", CC_EDIT_REQUEST, param)]

    # ── data from the relay ──
    def set_value(self, param, text, fraction):
        self.values[param] = (text, fraction)

    def set_save_result(self, text):
        self.save_text = text

    # ── what to draw ──
    def items(self):
        return EQ_BAND_LABELS if self.page == PAGE_BANDS else MENU_ROOT_ITEMS

    def title(self):
        if self.page == PAGE_SAVE:
            return "Save"
        if self.page == PAGE_BANDS:
            return "EQ band (Hz)"
        if self.page == PAGE_SLIDER:
            if self.param == PARAM_LEVEL:
                return "Level"
            if self.param == PARAM_PITCH:
                return "Pitch Shift"
            return "EQ {}".format(EQ_BAND_LABELS[self.param - PARAM_EQ_FIRST])
        return "Settings"

    def slider_value(self):
        """(text, fraction 0-100) for the open slider; ("--", None) until the
        relay has answered."""
        return self.values.get(self.param, ("--", None))


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
