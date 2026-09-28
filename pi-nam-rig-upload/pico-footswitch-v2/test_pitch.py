# test_pitch.py — verifies pitch.py's Hz -> note/cents math.
#
# Run:
#   python3 -m unittest test_pitch.py -v

import unittest

from pitch import hz_to_note_cents, midi_note_to_note_cents, note_name


class TestHzToNoteCents(unittest.TestCase):
    def test_a4_dead_on(self):
        note, cents = hz_to_note_cents(440.0)
        self.assertEqual(note, 69)
        self.assertAlmostEqual(cents, 0.0, places=3)

    def test_a4_sharp(self):
        # ~10 cents sharp
        note, cents = hz_to_note_cents(440.0 * 2 ** (10 / 1200))
        self.assertEqual(note, 69)
        self.assertAlmostEqual(cents, 10.0, places=1)

    def test_a4_flat(self):
        note, cents = hz_to_note_cents(440.0 * 2 ** (-15 / 1200))
        self.assertEqual(note, 69)
        self.assertAlmostEqual(cents, -15.0, places=1)

    def test_low_e_open_string(self):
        # E2, ~82.41 Hz
        note, cents = hz_to_note_cents(82.41)
        self.assertEqual(note, 40)
        self.assertAlmostEqual(cents, 0.0, delta=1.0)

    def test_alternate_reference_frequency(self):
        note, cents = hz_to_note_cents(432.0, ref_frequency=432.0)
        self.assertEqual(note, 69)
        self.assertAlmostEqual(cents, 0.0, places=3)

    def test_silence_rejected(self):
        self.assertIsNone(hz_to_note_cents(0))
        self.assertIsNone(hz_to_note_cents(-1))
        self.assertIsNone(hz_to_note_cents(5))

    def test_crosses_semitone_boundary_rounds_to_nearer_note(self):
        # Slightly under halfway to A#4 should still round to A4.
        note, cents = hz_to_note_cents(440.0 * 2 ** (49 / 1200))
        self.assertEqual(note, 69)
        self.assertAlmostEqual(cents, 49.0, places=1)


class TestMidiNoteToNoteCents(unittest.TestCase):
    def test_real_reading_of_a_played_d(self):
        # Actual FREQ value logged on the Pi while a D was played.
        note, cents = midi_note_to_note_cents(25.9342175)
        self.assertEqual(note_name(note)[:-1], "D")
        self.assertAlmostEqual(cents, -6.6, places=1)

    def test_sharp_side(self):
        note, cents = midi_note_to_note_cents(69.3)
        self.assertEqual(note, 69)
        self.assertAlmostEqual(cents, 30.0, places=6)

    def test_no_pitch_sentinel_rejected(self):
        self.assertIsNone(midi_note_to_note_cents(-1.0))
        self.assertIsNone(midi_note_to_note_cents(None))


class TestNoteName(unittest.TestCase):
    def test_middle_c(self):
        self.assertEqual(note_name(60), "C4")

    def test_a4(self):
        self.assertEqual(note_name(69), "A4")

    def test_sharp(self):
        self.assertEqual(note_name(61), "C#4")

    def test_low_e2(self):
        self.assertEqual(note_name(40), "E2")


if __name__ == "__main__":
    unittest.main()
