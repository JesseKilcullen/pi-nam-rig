# code.py — v2 footswitch firmware for PiPedal, per pipedal-hardware-v2.md.
# CircuitPython on a Raspberry Pi Pico. Save to the root of CIRCUITPY as code.py.
#
# All the mode/mapping decisions live in midi_logic.py (plain Python, no
# CircuitPython imports) so they can be unit-tested on a laptop before any
# hardware exists — see test_midi_logic.py. This file only does I/O: reading
# switches, driving LEDs, and turning midi_logic's output into real MIDI.
#
# Setup:
#   1. Flash CircuitPython (hold BOOTSEL, plug in, drag the .uf2)
#   2. Copy into CIRCUITPY/lib/: adafruit_midi/, adafruit_displayio_ssd1306/,
#      adafruit_display_text/, adafruit_display_shapes/ (all from the
#      Adafruit CircuitPython bundle). rotaryio is a CircuitPython built-in
#      -- nothing to add to lib/ for the encoder itself.
#   3. Copy midi_logic.py, pitch.py, oled_display.py AND this file to the
#      root of CIRCUITPY
#   4. Saving triggers a reload; open the serial console to see the printed log
#
# Wiring: pipedal-hardware-v2.md §4 (switches/LEDs), §4.1 (OLED), and §4.2
# (preset-browse rotary encoder). Every switch/mode-select/reset/tuner/
# encoder-push input shorts to GND, internal pull-ups, no external
# resistors. Each LED gets its own series resistor to GND (§4).
#
# RESET (the back-left switch) is the settings-menu key: it opens
# Level / EQ / Pitch Shift on the OLED, the encoder scrolls and (on a slider)
# changes the value, and RESET steps back one page. The encoder only sends
# relative steps -- pi_relay.py applies them to PiPedal and replies with the
# value to show. See midi_logic.EditMenu.
#
# The OLED shows a 3x2 grid of preset or snapshot names (whichever mode the
# footswitches are in, matching their physical layout), live tuner
# note+cents while tuner_mute is on, or the preset-browse preview while
# scrolling the rotary encoder (§4.2) -- but only once pi_relay.py is
# running on the Pi and sending data over this same USB MIDI cable.
# Without it, the screen shows the 2 s "OLED OK" boot splash and then sits
# blank/empty; that's expected, not a fault on this end.
#
# The shutdown button is NOT on the Pico — Pisound's own onboard button
# handles that (pipedal-hardware-v2.md §7).

import time
import board
import digitalio
import rotaryio
import usb_midi
import adafruit_midi
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange
from adafruit_midi.system_exclusive import SystemExclusive

from midi_logic import (
    FootswitchState,
    BrowseState,
    EditMenu,
    CC_TUNER_NOTE,
    CC_TUNER_CENTS,
    SYSEX_MANUFACTURER_ID,
    SYSEX_SNAPSHOT_LIST_SUBTYPE,
    SYSEX_PRESET_LIST_SUBTYPE,
    SYSEX_FULL_PRESET_LIST_SUBTYPE,
    SYSEX_EDIT_VALUE_SUBTYPE,
    SYSEX_SAVE_RESULT_SUBTYPE,
    MODE_PRESET,
    PAGE_SLIDER,
    PAGE_SAVE,
)
from pitch import note_name
import oled_display

# ── config ────────────────────────────────────────────────────────
ROW = (board.GP2, board.GP3, board.GP4, board.GP5, board.GP6, board.GP7)
MODE_PRESET_PIN = board.GP8
MODE_SNAPSHOT_PIN = board.GP9
RESET_PIN = board.GP10
TUNER_MUTE_PIN = board.GP11
LED_PRESET_PIN = board.GP12
LED_SNAPSHOT_PIN = board.GP13
# Preset-browse rotary encoder (pipedal-hardware-v2.md §4.2). A and B are
# read by rotaryio's hardware quadrature decoder, not the debounce loop
# below -- only the push switch needs debouncing like a normal footswitch.
ENCODER_A_PIN = board.GP19
ENCODER_B_PIN = board.GP20
ENCODER_SW_PIN = board.GP21

MIDI_CHANNEL = 1        # 1-16, as displayed in PiPedal
DEBOUNCE_S = 0.03       # 30 ms — raise if a stomp registers twice
BROWSE_TIMEOUT_S = 3.0  # no activity this long while browsing -> cancel, no selection made
# ──────────────────────────────────────────────────────────────────

midi = adafruit_midi.MIDI(
    midi_in=usb_midi.ports[0],
    midi_out=usb_midi.ports[1],
    out_channel=MIDI_CHANNEL - 1,   # library counts 0-15
    # Default (30) is far too small once the Browse preset list is in play:
    # up to BROWSE_MAX_PRESETS (24) names, ~11 bytes each -- comfortable
    # margin over the ~270 bytes that message can actually reach.
    in_buf_size=350,
)

# Confirmed on the real SR1230/A-6329 (2026-09-23): .position advances by
# exactly 1 per mechanical detent, so one browse.rotate() step per click.
encoder = rotaryio.IncrementalEncoder(ENCODER_A_PIN, ENCODER_B_PIN)


def make_input(pin):
    io = digitalio.DigitalInOut(pin)
    io.direction = digitalio.Direction.INPUT
    io.pull = digitalio.Pull.UP     # pressed == False
    return io


def make_output(pin):
    io = digitalio.DigitalInOut(pin)
    io.direction = digitalio.Direction.OUTPUT
    io.value = False
    return io


# Every debounced input, paired with the FootswitchState method it triggers
# on a falling edge (press). Row switches are handled separately since they
# need an index.
row_inputs = [make_input(p) for p in ROW]
mode_preset_input = make_input(MODE_PRESET_PIN)
mode_snapshot_input = make_input(MODE_SNAPSHOT_PIN)
reset_input = make_input(RESET_PIN)
tuner_mute_input = make_input(TUNER_MUTE_PIN)
encoder_sw_input = make_input(ENCODER_SW_PIN)

led_preset = make_output(LED_PRESET_PIN)
led_snapshot = make_output(LED_SNAPSHOT_PIN)
# Onboard LED as a MIDI-arrival indicator (OLED-BLANK-HANDOFF.md step 1):
# lit briefly whenever a SysEx with our manufacturer ID arrives, so delivery
# from pi_relay.py can be confirmed while plugged into the Pi, no serial needed.
led_onboard = make_output(board.LED)
LED_ONBOARD_BLINK_S = 0.15
led_onboard_off_at = 0.0

state = FootswitchState()
browse = BrowseState()
menu = EditMenu()
oled_display.init()
oled_display.show_splash()
time.sleep(2.0)

# Latest data pushed from pi_relay.py — the Pico never guesses this itself,
# it just displays whatever the relay last sent. See pi_relay.py's
# docstring for why it's safe for this to lag a footswitch press slightly.
# Both grids are cached at all times (not just whichever mode is showing)
# so flipping PRESET/SNAPSHOT mode redraws instantly with no round-trip —
# that flip is local-only on the Pico, nothing gets sent to the relay.
display_state = {
    "snapshot_names": [""] * 6,
    "snapshot_highlight": None,
    "preset_names": [""] * 6,
    "preset_highlight": None,
    "tuner_note": None,   # MIDI note number, or None if no valid pitch yet
    "tuner_cents": 0,
    "browse_names": [],        # full bank list, NOT padded to 6 -- variable length
    "browse_current_index": None,  # where the actually-loaded preset sits in that list
}


def refresh_display():
    if menu.active and not state.tuner_mute_on:
        if menu.page == PAGE_SLIDER:
            text, fraction = menu.slider_value()
            oled_display.show_slider(menu.title(), text, fraction)
        elif menu.page == PAGE_SAVE:
            oled_display.show_browse("Save", menu.save_text)
        else:
            oled_display.show_menu_list(menu.title(), menu.items(), menu.cursor)
    elif state.tuner_mute_on:
        note = display_state["tuner_note"]
        oled_display.show_tuner(
            note_name(note) if note is not None else None,
            display_state["tuner_cents"],
        )
    elif browse.active:
        names = display_state["browse_names"]
        total = len(names)
        name = names[browse.cursor] if 0 <= browse.cursor < total else ""
        oled_display.show_browse("{}/{}".format(browse.cursor + 1, total), name)
    elif state.mode == MODE_PRESET:
        oled_display.show_grid(display_state["preset_names"], display_state["preset_highlight"])
    else:
        oled_display.show_grid(display_state["snapshot_names"], display_state["snapshot_highlight"])


def poll_midi_in():
    """Non-blocking: decode whatever pi_relay.py has sent since last time."""
    global led_onboard_off_at
    msg = midi.receive()
    if msg is None:
        return

    if isinstance(msg, SystemExclusive) and msg.manufacturer_id == bytes([SYSEX_MANUFACTURER_ID]):
        led_onboard.value = True
        led_onboard_off_at = time.monotonic() + LED_ONBOARD_BLINK_S
        print("sysex in:", len(msg.data), "bytes, subtype", msg.data[0] if msg.data else None)

    if isinstance(msg, SystemExclusive) and msg.manufacturer_id == bytes([SYSEX_MANUFACTURER_ID]) \
            and len(msg.data) >= 2:
        subtype = msg.data[0]

        if subtype in (SYSEX_SNAPSHOT_LIST_SUBTYPE, SYSEX_PRESET_LIST_SUBTYPE):
            highlight_byte = msg.data[1]
            # Anything outside 0-5 (including the 127 "none" sentinel) means
            # no highlight -- oled_display.show_grid treats it the same way.
            highlight = highlight_byte if 0 <= highlight_byte < 6 else None
            names = [n.decode("ascii", "replace") for n in bytes(msg.data[2:]).split(b"\x00")]
            names = (names + [""] * 6)[:6]   # defensive pad/truncate to exactly 6

            if subtype == SYSEX_SNAPSHOT_LIST_SUBTYPE:
                display_state["snapshot_names"] = names
                display_state["snapshot_highlight"] = highlight
            else:
                display_state["preset_names"] = names
                display_state["preset_highlight"] = highlight
            refresh_display()

        elif subtype == SYSEX_EDIT_VALUE_SUBTYPE and len(msg.data) >= 3:
            menu.set_value(
                msg.data[1],
                bytes(msg.data[3:]).decode("ascii", "replace"),
                msg.data[2],
            )
            refresh_display()

        elif subtype == SYSEX_SAVE_RESULT_SUBTYPE:
            menu.set_save_result(bytes(msg.data[1:]).decode("ascii", "replace"))
            refresh_display()

        elif subtype == SYSEX_FULL_PRESET_LIST_SUBTYPE:
            current_byte = msg.data[1]
            display_state["browse_current_index"] = current_byte if current_byte != 127 else None
            payload = bytes(msg.data[2:])
            display_state["browse_names"] = (
                [n.decode("ascii", "replace") for n in payload.split(b"\x00")] if payload else []
            )
            refresh_display()
    elif isinstance(msg, ControlChange):
        if msg.control == CC_TUNER_NOTE:
            display_state["tuner_note"] = msg.value
            refresh_display()
        elif msg.control == CC_TUNER_CENTS:
            display_state["tuner_cents"] = msg.value - 64
            refresh_display()


def send(messages):
    for msg in messages:
        kind = msg[0]
        if kind == "cc":
            midi.send(ControlChange(msg[1], msg[2]))
        elif kind == "pc":
            midi.send(ProgramChange(msg[1]))
        print(msg)


def update_leds():
    preset_on, snapshot_on = state.led_state()
    led_preset.value = preset_on
    led_snapshot.value = snapshot_on


update_leds()
refresh_display()

# (input, last_state, last_change_time) tracked per-pin; a plain list keeps
# this readable without pulling in extra structure for 10 switches.
# The encoder's own A/B rotation isn't here -- rotaryio decodes that in
# hardware, polled separately below. Only its push switch needs debouncing
# like a normal footswitch.
watched = (
    [(io, "row", i) for i, io in enumerate(row_inputs)]
    + [
        (mode_preset_input, "mode_preset", None),
        (mode_snapshot_input, "mode_snapshot", None),
        (reset_input, "reset", None),
        (tuner_mute_input, "tuner_mute", None),
        (encoder_sw_input, "encoder_sw", None),
    ]
)
last_state = [True] * len(watched)
last_change = [0.0] * len(watched)

last_encoder_position = encoder.position
last_browse_activity = 0.0

while True:
    now = time.monotonic()

    for idx, (io, kind, arg) in enumerate(watched):
        val = io.value
        if val == last_state[idx]:
            continue
        if now - last_change[idx] < DEBOUNCE_S:
            continue
        last_change[idx] = now
        last_state[idx] = val
        if val:  # rising edge == released, ignore
            continue

        # Any footswitch/mode press other than the encoder's own switch
        # cancels an in-progress browse -- the footswitch's own action
        # below still runs as normal, it just also clears browse state.
        if kind != "encoder_sw":
            browse.cancel()
        # Likewise any footswitch other than RESET (the menu key) and the
        # encoder leaves the settings menu and then does its normal job.
        if kind not in ("encoder_sw", "reset"):
            menu.cancel()

        if kind == "row":
            send(state.press_row(arg))
        elif kind == "mode_preset":
            state.press_mode_preset()
        elif kind == "mode_snapshot":
            state.press_mode_snapshot()
        elif kind == "reset":
            send(menu.press_menu_key())
        elif kind == "tuner_mute":
            send(state.press_tuner_mute())
        elif kind == "encoder_sw":
            print("encoder push, menu active:", menu.active, "browse active:", browse.active)
            if menu.active:
                send(menu.push())
            elif browse.active:
                send(browse.confirm())
        update_leds()
        refresh_display()   # e.g. tuner_mute toggling swaps which screen shows

    position = encoder.position
    delta = position - last_encoder_position
    if delta != 0:
        last_encoder_position = position
        last_browse_activity = now
        print("encoder position", position, "delta", delta)
        if menu.active:
            send(menu.rotate(delta))
        else:
            browse.rotate(delta, len(display_state["browse_names"]), display_state["browse_current_index"])
        refresh_display()

    if browse.active and (now - last_browse_activity) > BROWSE_TIMEOUT_S:
        browse.cancel()
        refresh_display()

    poll_midi_in()
    if led_onboard.value and now >= led_onboard_off_at:
        led_onboard.value = False
    time.sleep(0.001)
