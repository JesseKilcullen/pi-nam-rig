#!/usr/bin/env python3
"""
Add "7 Muse", "8 Opeth - Ghost Reveries" and "9 Test" (an experiment preset
modelled on Massive, with every effect) to Default Bank, on top of the
existing six (which are rebuilt unchanged except the noise-gate threshold fix
already applied in build-kraken-presets.py).

This works by loading build-kraken-presets.py as a module and monkey-patching
its presets()/snapshots_for() to add the two new entries, then calling its
own main() -- so preflight(), check_ranges(), the backup, and the atomic
write are all the exact same proven code path, unmodified.

Run exactly like the original (same directory, same rules):
    python3 add-muse-opeth-presets.py --dry-run      # safe, no sudo, no stop
    sudo systemctl stop pipedald
    sudo python3 add-muse-opeth-presets.py
    sudo systemctl start pipedald

Gear used, all already on the Pi -- nothing to download for this version:
  Muse   - amp: JCM800 2203 boosted w/ OD808 (Gain 7) capture
           fuzz (switchable): EHX Big Muff Pi T5 S9
           clean alt (Clean Arp snapshot): 1960 Gibson Rhythm King - Edge of
           Breakup
  Opeth  - amp: same JCM800 2203/OD808 capture (mid-forward, Marshall-ish,
           matches the era/tone family)
           dirt (switchable, "Buzzsaw" snapshot): BOSS HM-2 1986 "Chainsaw"
           capture -- the classic Swedish death-metal buzzsaw
           heavy alt ("Heavy" snapshot): Peavey 6505 1992 Lead - Chug
           clean alt ("Clean Prog" snapshot): 1960 Fender Tweed Deluxe 5E3

Nothing here is a verified match for either band's actual studio tone --
there's no Diezel VH4 (Muse's main amp) or ENGL/exact Ghost Reveries rig
capture on this Pi. This is a reasonable starting point built entirely from
what's already installed; expect to want to re-voice EQ/gain by ear. See the
chat notes for what to download from ToneHunt/Tone3000 for a closer match.
"""

import importlib.util
import os

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "kraken", os.path.join(_here, "build-kraken-presets.py"))
kraken = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kraken)

# Bring the helpers into local scope for readability.
tuner, gate, input_stage = kraken.tuner, kraken.gate, kraken.input_stage
nam, pedal, cab_ir = kraken.nam, kraken.pedal, kraken.cab_ir
eq3, peq, chorus, delay, freeverb = (
    kraken.eq3, kraken.peq, kraken.chorus, kraken.delay, kraken.freeverb)
eq3_stereo = kraken.eq3_stereo
tremolo, split = kraken.tremolo, kraken.split
snapshot, rel = kraken.snapshot, kraken.rel
PEDAL, AMP = kraken.PEDAL, kraken.AMP
GATE, EQ3, PEQ, DELAY, FREEVERB, CHORUS = (
    kraken.GATE, kraken.EQ3, kraken.PEQ, kraken.DELAY, kraken.FREEVERB,
    kraken.CHORUS)
NAM_DIR, IR_JCM800, P = kraken.NAM_DIR, kraken.IR_JCM800, kraken.P
BIGMUFF, CLEAN_CAP = kraken.BIGMUFF, kraken.CLEAN_CAP
KRAKEN, BLUESDRIVER, IR_1960TV = kraken.KRAKEN, kraken.BLUESDRIVER, kraken.IR_1960TV
CONVERB, SPLIT = kraken.CONVERB, kraken.SPLIT
TREM = ("toob-tremolo", 0)
# "9 Test" has a gain pedal and an amp in the top chain and a clean amp in the
# bottom one, so its three toob-nam instances flatten in this order:
TEST_PEDAL, TEST_TOP, TEST_BOT = ("toob-nam", 0), ("toob-nam", 1), ("toob-nam", 2)

MUSE_AMP = NAM_DIR + "/JCM_800_2203_OD8008_Boosted_Amp_Gain_7.nam"
MUSE_FUZZ = BIGMUFF + "/Big Muff Pi T5 S9.nam"
MUSE_CLEAN_ALT = NAM_DIR + "/1960 Gibson Rhythm King - Edge of Breakup.nam"

OPETH_AMP = NAM_DIR + "/JCM_800_2203_OD8008_Boosted_Amp_Gain_7.nam"
OPETH_HM2 = NAM_DIR + "/BOSS HM-2 1986/Chainsaw.nam"
OPETH_HEAVY = NAM_DIR + "/Peavey 6505 1992 Lead - Chug.nam"


def _muse_items():
    return [
        tuner(),
        gate(-70, hold=90, release=250, reduction=-50, attack=2,
             hysteresis=-9),
        input_stage(trim=0, locut=85),
        # Big Muff, bypassed by default -- the "Fuzz Lead" snapshot is the
        # stomp-on, for the "Plug In Baby" / "Hysteria" chaos-fuzz break.
        pedal(MUSE_FUZZ, input_gain=-10, output_gain=-8, enabled=False,
              threaded=True),
        # outputGain trimmed, not inputGain -- this capture is already a
        # boosted/hot one, and outputGain is a clean post-amp level trim so
        # dropping it doesn't change the drive/character, just the loudness.
        # -1, not -6, per the 2026-09-10 level-match pass.
        nam(MUSE_AMP, -8, 5, 5.5, 5.5, output_gain=-1, threaded=True),
        cab_ir(IR_JCM800),
        eq3(4.5, 5, 6),
        chorus(0.22, 0.40, 0.32),
        delay(360, 22, 10),
        freeverb(0.16, 0.40),
    ]


def _opeth_items():
    return [
        tuner(),
        # Same gate shape as "4 HG Rhythm" -- proven tight-but-not-choppy on
        # this rig for percussive high-gain riffing.
        gate(-55, hold=90, release=220, reduction=-45, attack=3,
             hysteresis=-12),
        input_stage(trim=0, locut=95),
        # HM-2, bypassed by default -- "Buzzsaw" stomps it on for the
        # classic Swedish death-metal texture on specific riffs.
        pedal(OPETH_HM2, input_gain=-10, output_gain=-8, enabled=False,
              threaded=True),
        # -1, not -6, per the 2026-09-10 level-match pass.
        nam(OPETH_AMP, -8, 5, 5, 5.5, output_gain=-1, threaded=True),
        cab_ir(IR_JCM800),
        # hiCut 10.3, not 12 -- level-match/EQ pass, 2026-09-10.
        peq(95, 400, -2, 1.2, 2.5, 1, 10.3),
        delay(320, 18, 6),
        freeverb(0.10, 0.30),
    ]


def _test_items():
    """9 Test: an experiment preset modelled on "6 Massive" -- two amp chains
    in parallel (a Kraken behind a gain pedal on top, a clean Tweed
    underneath) and every effect in the bank (chorus, tremolo, delay,
    reverb). Pitch Shift and Graphic EQ come from with_menu_plugins, like
    every other preset. Chain, once those are in:
      tuner > gate > input stage > pitch shift >
      SPLIT[ gain pedal (off at home) > Kraken G5 | Tweed clean ] >
      cab IR > parametric EQ > graphic EQ > chorus > tremolo (off at home) >
      delay > convolution reverb"""
    return [
        tuner(),
        gate(-55, hold=90, release=260, reduction=-45, attack=3,
             hysteresis=-12),
        input_stage(trim=0, locut=85),
        split(
            # the pedal drives the Kraken only; the Tweed stays clean
            [pedal(BLUESDRIVER, input_gain=-10, output_gain=-4,
                   enabled=False, threaded=True),
             nam(KRAKEN + "/Kraken_Gain-I_G5.nam", -14, 5, 5.5, 5.5,
                 threaded=True)],
            [nam(CLEAN_CAP, -12, 5.5, 5, 5.5, output_gain=-3, threaded=True)],
            split_type=kraken.SPLIT_MIX, mix=0),
        cab_ir(IR_1960TV),
        peq(85, 400, -2, 1.0, 2.5, 1, 11, gain=2),
        # Chorus, tremolo and delay are OFF in Clean (the home snapshot); the
        # other snapshots switch them on. The values below are by-ear
        # settings from the live bank (2026-10-06): they are what
        # "Fascination" plays with.
        chorus(0.25, 0.74, 0.5933333, enabled=False),
        tremolo(rate=5.0, depth=0.2133333, enabled=False),
        delay(590.7693, 36.66667, 42.66667, enabled=False),
        # Freeverb, not Massive's 2.9 s convolution reverb: that one's worker
        # threads were ~40% of this preset's CPU and the Pi throttled.
        freeverb(0.3033333, 0.5, damping=0.14),
    ]


_orig_presets = kraken.presets
_orig_snapshots_for = kraken.snapshots_for


def presets():
    return _orig_presets() + [
        ("7 Muse", _muse_items()),
        # Master Output Volume -3 and no stereo level stage, by ear (live
        # bank, 2026-10-06) -- replaces the +12.8 dB 3-band EQ stage the
        # 2026-10-04 fold-in had added after the delay.
        ("8 Opeth - Ghost Reveries", _opeth_items(), -3),
        ("9 Test", _test_items()),
    ]


def snapshots_for(name, items):
    if name == "7 Muse":
        s = [
            snapshot("Rhythm", "red", items),
            snapshot("Fuzz Lead", "purple", items, {
                PEDAL: {"enabled": True},
            }),
            snapshot("Clean Arp", "lightBlue", items, {
                # outputGain -1 -> 0, per studio-monitor testing 2026-09-12 --
                # the clean alt read quiet next to the amp snapshots.
                AMP: {"paths": {P + "toob-nam#modelFile": MUSE_CLEAN_ALT},
                      "controls": {"inputGain": -14, "outputGain": 0}},
                CHORUS: {"controls": {"dryWet": 0.55}},
                FREEVERB: {"controls": {"dryWet": 0.30, "roomSize": 0.55}},
                # By-ear edit, folded in from the live bank (2026-10-04): the
                # clean alt needed a big level lift, done on the 3-band EQ's gain.
                EQ3: {"controls": {"gain": 11.083333}},
            }),
            snapshot("Big Ambient", "teal", items, {
                DELAY: {"controls": {"delay": 480, "feedback": rel(+14),
                                     "level": rel(+16)}},
                FREEVERB: {"controls": {"dryWet": 0.42, "roomSize": 0.75}},
            }),
            snapshot("Solo Boost", "amber", items, {
                AMP: {"controls": {"outputGain": rel(+3.5)}},
                EQ3: {"controls": {"mid": rel(+1), "treble": rel(+0.5)}},
                DELAY: {"controls": {"level": rel(+8)}},
            }),
        ]
    elif name == "8 Opeth - Ghost Reveries":
        s = [
            snapshot("Chug", "red", items, {
                # by ear, live bank 2026-10-06: -2, not the -1 the other
                # snapshots carry
                AMP: {"controls": {"outputGain": -2}},
            }),
            snapshot("Buzzsaw", "green", items, {
                PEDAL: {"enabled": True},
            }),
            snapshot("Heavy", "deepPurple", items, {
                # outputGain -1 -> -3, per studio-monitor testing 2026-09-12 --
                # too hot next to the rest of the bank on real speakers.
                AMP: {"paths": {P + "toob-nam#modelFile": OPETH_HEAVY},
                      "controls": {"inputGain": -8, "outputGain": -3}},
            }),
            snapshot("Lead", "orange", items, {
                AMP: {"controls": {"outputGain": rel(+3)}},
                PEQ: {"controls": {"hmfLevel": rel(+2)}},
                DELAY: {"controls": {"level": rel(+10), "feedback": rel(+8)}},
            }),
            snapshot("Clean Prog", "lightBlue", items, {
                # outputGain -1 -> 0, per studio-monitor testing 2026-09-12 --
                # same "clean read quiet" fix as Muse's Clean Arp.
                AMP: {"paths": {P + "toob-nam#modelFile": CLEAN_CAP},
                      "controls": {"inputGain": -14, "outputGain": 0}},
                PEQ: {"controls": {"loCut": 80, "hiCut": 14}},
                DELAY: {"controls": {"delay": 420, "feedback": rel(+10),
                                     "level": rel(+14)}},
                FREEVERB: {"controls": {"dryWet": 0.30, "roomSize": 0.55}},
            }),
        ]
    elif name == "9 Test":
        # Slot 1 is the home sound ("Clean": every effect off but the
        # reverb) and slot 6 is "Fascination", the by-ear all-effects sound
        # -- put there on request, 2026-10-06. Pedal/Trem/Wash/Dry predate
        # that and keep the original generator values (depth 0.5, 420 ms).
        def fx(chorus_on, trem_on, delay_on, dry_wet=0.4, delay_ms=420,
               feedback=30, level=20, **extra):
            return {
                CHORUS: {"enabled": chorus_on,
                         "controls": {"depth": 0.5, "dryWet": dry_wet}},
                TREM: {"enabled": trem_on, "controls": {"depth": 0.5}},
                DELAY: {"enabled": delay_on,
                        "controls": {"delay": delay_ms, "feedback": feedback,
                                     "level": level}},
                **extra,
            }

        s = [
            snapshot("Clean", "grey", items),
            snapshot("Pedal", "amber", items,
                     fx(True, False, True) | {TEST_PEDAL: {"enabled": True}}),
            snapshot("Trem", "purple", items, fx(True, True, True)),
            snapshot("Wash", "lightBlue", items,
                     fx(True, False, True, dry_wet=0.6, delay_ms=520,
                        feedback=42, level=35)),
            snapshot("Dry", "blueGrey", items, fx(False, False, False)),
            snapshot("Fascination", "teal", items, {
                CHORUS: {"enabled": True},
                TREM: {"enabled": True},
                DELAY: {"enabled": True},
                FREEVERB: {"controls": {"dryWet": 0.75}},
            }),
        ]
    else:
        return _orig_snapshots_for(name, items)

    if len(s) > 6:
        raise ValueError("%s: %d snapshots, max 6" % (name, len(s)))
    return s + [None] * (6 - len(s))


kraken.presets = presets
kraken.snapshots_for = snapshots_for

if __name__ == "__main__":
    kraken.main()
