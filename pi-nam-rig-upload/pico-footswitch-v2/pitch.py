"""pitch.py — Hz -> (MIDI note number, cents offset) for the tuner display.

Pure Python, no CircuitPython/board imports, so it's unit-tested the same
way as midi_logic.py (see test_pitch.py) without needing a Pico or a Pi.

This does the same 12-TET math as the web UI's own tuner dial
(GxTunerControl.tsx noteToPitchInfo), just simplified to always-12-TET
since that's what's going on a 128x64 OLED. Runs on the Pi (inside
pi_relay.py) rather than the Pico — CircuitPython's math module has log2,
but keeping this pure Python means it can be tested on a laptop.
"""

import math

A4_MIDI_NOTE = 69
MIN_VALID_HZ = 20.0  # below this, treat as "no signal" rather than a wild note


def hz_to_note_cents(hz: float, ref_frequency: float = 440.0):
    """Returns (note_number, cents) where note_number is 0-127 (MIDI note,
    rounded to nearest semitone) and cents is the offset from that semitone
    in the range [-50, 50]. Returns None if hz isn't a plausible pitch."""
    if hz is None or hz < MIN_VALID_HZ:
        return None

    exact_note = A4_MIDI_NOTE + 12 * math.log2(hz / ref_frequency)
    note_number = round(exact_note)
    if not 0 <= note_number <= 127:
        return None

    cents = (exact_note - note_number) * 100
    return note_number, cents


def midi_note_to_note_cents(value: float):
    """TooB Tuner's FREQ port is NOT Hz: ToobTuner.ttl declares it
    units:midiNote -- a fractional MIDI note number, -1 when there's no
    pitch (confirmed on the Pi, 2026-09-24: a played D read ~25.9, which
    hz_to_note_cents turned into "G#0"). Returns (note_number, cents) like
    hz_to_note_cents, or None if there's no valid pitch."""
    if value is None or value < 0:
        return None
    note_number = round(value)
    if not 0 <= note_number <= 127:
        return None
    return note_number, (value - note_number) * 100


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note_name(note_number: int) -> str:
    """Standard MIDI convention: note 60 = "C4"."""
    octave = note_number // 12 - 1
    return "{}{}".format(NOTE_NAMES[note_number % 12], octave)
