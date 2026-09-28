#!/usr/bin/env python3
"""
Add "7 Muse" and "8 Opeth - Ghost Reveries" to Default Bank, on top of the
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
snapshot, rel = kraken.snapshot, kraken.rel
PEDAL, AMP = kraken.PEDAL, kraken.AMP
GATE, EQ3, PEQ, DELAY, FREEVERB, CHORUS = (
    kraken.GATE, kraken.EQ3, kraken.PEQ, kraken.DELAY, kraken.FREEVERB,
    kraken.CHORUS)
NAM_DIR, IR_JCM800, P = kraken.NAM_DIR, kraken.IR_JCM800, kraken.P
BIGMUFF, CLEAN_CAP = kraken.BIGMUFF, kraken.CLEAN_CAP

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


_orig_presets = kraken.presets
_orig_snapshots_for = kraken.snapshots_for


def presets():
    return _orig_presets() + [
        ("7 Muse", _muse_items()),
        ("8 Opeth - Ghost Reveries", _opeth_items()),
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
            snapshot("Chug", "red", items),
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
    else:
        return _orig_snapshots_for(name, items)

    if len(s) > 6:
        raise ValueError("%s: %d snapshots, max 6" % (name, len(s)))
    return s + [None] * (6 - len(s))


kraken.presets = presets
kraken.snapshots_for = snapshots_for

if __name__ == "__main__":
    kraken.main()
