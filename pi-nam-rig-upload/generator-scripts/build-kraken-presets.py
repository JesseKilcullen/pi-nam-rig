#!/usr/bin/env python3
"""
Build the six Kraken presets, and their snapshots, into "Default Bank".

Replaces every preset in that bank. Leaves "Factory Presets" untouched.
Design and rationale: pipedal-tones.md

Run with pipedald STOPPED:
    sudo systemctl stop pipedald
    python3 build-kraken-presets.py
    sudo systemctl start pipedald
"""

import datetime
import glob
import json
import os
import re
import shutil
import sys

BANK = "/var/pipedal/presets/Default+Bank.bank"
NAM_DIR = "NeuralAmpModels/Factory Models"
KRAKEN = NAM_DIR + "/Victory VX Kraken - A2"
TS9 = NAM_DIR + "/Ibanez TS9 Tube Screamer"
SUNFACE = NAM_DIR + "/Sunface RCA"
SF300 = NAM_DIR + "/Behringer SF300 Super Fuzz (Secret Mode 1.5!!)"
CE2W = NAM_DIR + "/BOSS CE-2w"
BIGMUFF = NAM_DIR + "/EHX Big Muff Pi"
# Verified against the Pi. Note the pipe and the spaces in the filename --
# another entry for the "filenames lie" list. The pack holds exactly one
# capture: BD-2W in MODE_C (the Waza custom mode), level 4, tone 5, gain 6.
BLUESDRIVER = (NAM_DIR +
               "/Boss Blues Driver Waza/BOSS BD-2W | L4 T5 G6 MODE_C.nam")
# Two genuinely different fuzz circuits for preset 6, not two settings of
# one pedal: germanium Fuzz Face vs silicon Big Muff. Both verified on the Pi.
FUZZ_LOW = SUNFACE + "/SunFace RCA V7 F10 C10.nam"
FUZZ_HIGH = BIGMUFF + "/Big Muff Pi T5 S9.nam"
IR_DIR = "CabIR/Factory IRs"
RV_DIR = "ReverbImpulseFiles"

P = "http://two-play.com/plugins/"
# Not a TooB plugin: the pitch shifter built from TONE3000's engine (see
# lv2-pitch-shift/ in this repo). It lives in /usr/lib/lv2/PitchShiftTone3000.lv2.
PITCH_URI = "https://github.com/JesseKilcullen/pi-nam-rig/lv2-pitch-shift#mono"

NAMES = {
    "toob-tuner": "TooB Tuner",
    "toob-noise-gate": "TooB Noise Gate",
    "toob-input_stage": "TooB Input Stage",
    "toob-nam": "TooB Neural Amp Modeler",
    "toob-cab-ir": "TooB Cab IR",
    "toob-three-band-eq": "TooB 3 Band EQ (Mono)",
    "toob-parametric-eq": "TooB Parametric EQ (Mono)",
    "toob-chorus": "TooB CE-2 Chorus",
    "toob-delay": "TooB Delay",
    "toob-multi-echo-stereo": "TooB Multi-Tap Delay (Stereo)",
    "toob-freeverb": "TooB Freeverb",
    "toob-convolution-reverb-stereo": "TooB Convolution Reverb (Stereo)",
    "toob-graphiceq": "TooB Graphic Eq",
    "toob-three-band-eq-stereo": "TooB 3 Band EQ (Stereo)",
    PITCH_URI: "Pitch Shift (TONE3000 engine)",
}


ATOM_PATH = "http://lv2plug.in/ns/ext/atom#Path"
ATOM_STRING = "http://lv2plug.in/ns/ext/atom#String"


def path_prop(value):
    """The cached display copy: a JSON *string* nested inside a JSON value.
    separators match PiPedal's own writer exactly (no space after comma)."""
    return json.dumps({"otype_": "Path", "value": value},
                      separators=(",", ": "))


def lv2_state(paths):
    """The state PiPedal actually restores into the plugin.

    This is the one that matters -- pathProperties alone leaves the file
    selector empty and no model loaded. Empty slots are atom#String, real
    paths are atom#Path; that distinction is copied from PiPedal's own output.
    """
    if not paths:
        return [False, {}]
    return [True, {
        key: {
            "flags": 3,
            "atomType": ATOM_PATH if value else ATOM_STRING,
            "value": value,
        }
        for key, value in paths.items()
    }]


_next_id = [100]


def item(short, controls, paths=None, enabled=True):
    """paths maps a full property URI to a plain relative path string.
    Both pathProperties and lv2State are derived from it.

    `short` is a TooB plugin's name ("toob-delay"), or a full plugin URI for
    anything else (the pitch shifter)."""
    paths = paths or {}
    _next_id[0] += 1
    return {
        "instanceId": _next_id[0],
        "uri": short if "://" in short else P + short,
        "isEnabled": enabled,
        "controlValues": [{"key": k, "value": v} for k, v in controls.items()],
        "pluginName": NAMES[short],
        "midiBindings": [],
        "midiChannelBinding": None,
        "stateUpdateCount": 1 if paths else 0,
        "lv2State": lv2_state(paths),
        "lilvPresetUri": "",
        "pathProperties": {k: path_prop(v) for k, v in paths.items()},
        "title": "",
        "useModUi": False,
        "iconColor": "default",
        "sideChainInputId": -1,
    }


# ---- reusable blocks -------------------------------------------------

def tuner():
    return item("toob-tuner", {"MUTE": 0, "REFFREQ": 440, "THRESHOLD": -60})


def gate(threshold, hold=100, release=330, reduction=-60, attack=1,
         hysteresis=-6):
    # `reduction` is -60..-6 dB. -60 is a full mute, and a full mute is what
    # makes gate action *audible* as a click on the way in and out -- on a
    # high-gain preset it reads as crackle on note tails. -40..-45 kills the
    # hiss just as well and its transitions disappear.
    # `hysteresis` is the gap between the open and close thresholds. At -6 a
    # decaying note sitting near the threshold opens and shuts repeatedly
    # (chatter); widening it costs nothing.
    return item("toob-noise-gate", {
        "attack": attack, "gate_level": -60, "hold": hold,
        "hysteresis": hysteresis, "reduction": reduction, "release": release,
        "threshold": threshold, "trigger_led": 0,
    })


def pitch_shift(semitones=0):
    """The settings menu's Pitch Shift (pi_relay.py moves `semitones` and
    switches `power` with it). Power is OFF by default: a powered-off
    shifter is a bit-exact, zero-latency passthrough, so presets sound and
    measure exactly as before until the shift is used. Window 1 = 30 ms (the
    shifter's own default; covers bass and drop tunings). Tonality 20000 =
    off, a pure shift. `latency` is an output port the host fills in."""
    return item(PITCH_URI, {
        "semitones": semitones, "step": 1, "tonality": 20000, "window": 1,
        "power": 0, "latency": 0,
    })


def eq3_stereo(gain, bass=5, mid=5, treble=5):
    """TooB 3 Band EQ (Stereo). Used flat as a plain level stage (see Opeth)."""
    return item("toob-three-band-eq-stereo", {
        "bass": bass, "control": 0, "gain": gain, "in": 0, "inR": 0,
        "mid": mid, "notify": 0, "out": 0, "outR": 0, "treble": treble,
    })


def graphic_eq():
    """The settings menu's Level and EQ. Everything flat: the menu moves
    `level` and the seven band gains per preset."""
    controls = {"gain_%dhz" % hz: 0
                for hz in (100, 200, 400, 800, 1600, 3200, 6400)}
    controls["level"] = 0
    return item("toob-graphiceq", controls)


def input_stage(trim=0, locut=80, bright=0):
    return item("toob-input_stage", {
        "filter": 0, "trim": trim, "trimOut": -35, "gate_t": -120,
        "gate_out": 0, "locut": locut, "bright": bright, "brightf": 1300,
        "hicut": 13000, "in": 0, "out": 0, "control": 0, "notify": 0,
    })


# toneStack: 0=Bassman 1=JCM8000 2=Baxandall 3=Bypass (plugin default).
# Amp instances use Baxandall so bass/mid/treble actually do something --
# the capture's own tone stack is frozen at whatever the author dialled in,
# so this is the only way to voice it. Pedal captures get Bypass.
TONESTACK_BAXANDALL = 2
TONESTACK_BYPASS = 3


def nam(model, input_gain, bass, mid, treble, output_gain=0, gate_db=-120,
        tone_stack=TONESTACK_BAXANDALL, enabled=True, threaded=False):
    # `buffer` is the control the UI labels "Threaded" -- it moves NAM
    # inference off the audio thread, at the cost of one extra buffer of
    # latency (1.33 ms at 64x3 / 48 kHz).
    #
    # It is not a marginal tweak. Measured on preset 5, one NAM instance,
    # everything else identical:
    #
    #     Threaded=0   45.3% of one core
    #     Threaded=1   17.9%
    #
    # 2.5x cheaper. The earlier guidance was to enable it only where a preset
    # has 2 NAM instances; that was too conservative -- the win is just as
    # large with one, so it is now on everywhere.
    # `modelSize` is labelled "Quality" (0..1) -- the A2 slimmable submodel
    # selector. 0 is the plugin default and what the factory presets use.
    return item("toob-nam", {
        "bass": bass, "buffer": 1 if threaded else 0, "calibration": 0,
        "gate": gate_db, "gateOut": 0, "inputCalibrationMode": 0,
        "inputGain": input_gain, "inputGainOut": -35, "mid": mid,
        "modelSize": 0, "outputCalibration": 0, "outputGain": output_gain,
        "toneStack": tone_stack, "treble": treble, "version": 1,
    }, {P + "toob-nam#modelFile": model}, enabled=enabled)


def pedal(model, input_gain=-10, output_gain=-6, enabled=True, threaded=False):
    """A pedal capture in front of an amp capture. Tone stack bypassed --
    a stompbox has no business carrying an amp tone stack."""
    return nam(model, input_gain, 5, 5, 5, output_gain=output_gain,
               gate_db=-120, tone_stack=TONESTACK_BYPASS, enabled=enabled,
               threaded=threaded)


# PiPedal's parallel/split node. NOT an LV2 plugin -- it is internal to the
# host, so its URI is not under P and there is no .ttl for it (check_ranges()
# therefore skips it, which is fine). Schema read off Factory+Presets.bank,
# which has fourteen of them.
SPLIT_URI = "uri://two-play/pipedal/pedalboard#Split"

# splitType, mapped by reading the factory presets:
#   0 A/B  -- one chain or the other, chosen by `select`
#   1 MIX  -- both chains run and are summed, balanced by `mix`
#   2 L/R  -- one chain per output channel, using panL/volL/panR/volR
SPLIT_AB, SPLIT_MIX, SPLIT_LR = 0, 1, 2


def split(top, bottom, split_type=SPLIT_MIX, mix=0, select=0,
          pan_l=-1, vol_l=0, pan_r=1, vol_r=0):
    """A parallel split. `top` and `bottom` are lists of items.

    With SPLIT_MIX both chains run constantly -- this is a blend, not a
    switch, so both NAM instances cost you whether you can hear them or not.

    `mix` runs about -1..+1 with 0 an even blend. WHICH SIGN FAVOURS WHICH
    CHAIN IS UNVERIFIED -- there is no TTL to read it from and the factory
    presets only show that the values skew negative. Assumed here: negative
    favours `top`. If the heavier snapshots come out cleaner instead of
    dirtier, flip the signs in snapshots_for().
    """
    _next_id[0] += 1
    return {
        "instanceId": _next_id[0],
        "uri": SPLIT_URI,
        "isEnabled": True,
        "controlValues": [
            {"key": "splitType", "value": split_type},
            {"key": "select", "value": select},
            {"key": "mix", "value": mix},
            {"key": "panL", "value": pan_l},
            {"key": "volL", "value": vol_l},
            {"key": "panR", "value": pan_r},
            {"key": "volR", "value": vol_r},
        ],
        # both empty strings in PiPedal's own output, not "default"
        "pluginName": "",
        "iconColor": "",
        "midiBindings": [],
        "midiChannelBinding": None,
        "stateUpdateCount": 0,
        "lv2State": [False, {}],
        "lilvPresetUri": "",
        "pathProperties": {},
        "title": "",
        "useModUi": False,
        "sideChainInputId": -1,
        "topChain": top,
        "bottomChain": bottom,
    }


def flatten(items):
    """Every item, including those nested inside Split chains.

    Depth-first, split node before its own children, top chain before bottom.
    Everything that walks a preset must use this: snapshots have to carry a
    value for EVERY item or the omitted ones reset to plugin defaults (trap
    2), and preflight/check_ranges would otherwise silently skip nested
    captures. Confirmed against the factory bank -- "Huge Lead 2" has 6
    top-level items plus 3 nested, and its snapshots carry 9 values.
    """
    out = []
    for it in items:
        out.append(it)
        for key in ("topChain", "bottomChain"):
            out.extend(flatten(it.get(key) or []))
    return out


def short_name(uri):
    """The key snapshot selectors use. LV2 plugins are P-prefixed; the Split
    node is not, so it selects as ("Split", 0). The pitch shifter selects as
    ("pitch-shift", 0): its URI fragment is just "mono"."""
    if uri.startswith(P):
        return uri[len(P):]
    if uri == PITCH_URI:
        return "pitch-shift"
    return uri.rsplit("#", 1)[-1]


def with_menu_plugins(items):
    """Add the two plugins the footswitch box's settings menu drives, to any
    preset's chain. Done here, once, so every preset gets them and a
    regenerate can never drop them.

    Pitch Shift goes in front of the first amp/pedal capture or Split: it
    wants the clean guitar signal, and a fuzz or amp after it should react
    to the shifted note.

    Graphic EQ goes right after the preset's main EQ, i.e. at the end of the
    mono part of the chain and BEFORE the chorus/delay/reverb. Not at the
    very end: it is a mono plugin, and PiPedal feeds a mono plugin only the
    LEFT channel of a stereo signal, so after a stereo reverb it would
    collapse the reverb's width. (Level and EQ behave the same here as at
    the end; the wet effects just sit after them.)
    """
    items = list(items)

    first_amp = next(i for i, it in enumerate(items)
                     if it["uri"].endswith("toob-nam")
                     or it["uri"] == SPLIT_URI)
    items.insert(first_amp, pitch_shift())

    eq_shorts = ("toob-three-band-eq", "toob-parametric-eq")
    last_eq = max(i for i, it in enumerate(items)
                  if short_name(it["uri"]) in eq_shorts)
    items.insert(last_eq + 1, graphic_eq())
    return items


def cab_ir(wav):
    return item("toob-cab-ir", {
        "control": 0, "direct_mix": -40, "in": 0, "loading_state": 0,
        "notify": 0, "out": 0, "predelay": 0, "reverb_mix": 0,
        # -40 dB is this control's minimum, i.e. off. -100 was out of range
        # and clamped -- harmless here (slots 2 and 3 have no IR loaded) but
        # it made check_ranges() noisy enough to hide real problems.
        "reverb_mix2": -40, "reverb_mix3": -40, "time": 1.5,
    }, {
        P + "toob-cab-ir#impulseFile": IR_DIR + "/" + wav,
        P + "toob-cab-ir#impulseFile2": "",
        P + "toob-cab-ir#impulseFile3": "",
    })


def eq3(bass, mid, treble, gain=0):
    return item("toob-three-band-eq",
                {"bass": bass, "mid": mid, "treble": treble, "gain": gain})


def peq(locut, lmf_c, lmf_lvl, lmf_q, hmf_c_khz, hmf_lvl, hicut_khz, gain=0):
    """Parametric EQ. MIND THE UNITS -- they are not consistent within this
    single plugin, and out-of-range values are clamped silently:

        loCut   20-350    Hz     |  lfC    30-450   Hz
        lmfC    129-2500  Hz     |  hmfC   0.6-7.5  kHz
        hfC     1-16      kHz    |  hiCut  1-21     kHz
        *Level  -15..15   dB     |  *Q     0.5-3.0

    Low bands in Hz, high bands in kHz. Passing 9000 for a 9 kHz hiCut clamps
    to 21 kHz -- the filter fully open, doing nothing at all. That is exactly
    what had happened to presets 4, 5 and 6 until check_ranges() caught it, so
    the two kHz arguments are named for their unit.
    """
    return item("toob-parametric-eq", {
        "control": 0, "gain": gain, "hfC": 2, "hfLevel": 0, "hiCut": hicut_khz,
        "hmfC": hmf_c_khz, "hmfLevel": hmf_lvl, "hmfQ": 1.5, "in": 0,
        "lfC": 120, "lfLevel": 0, "lmfC": lmf_c, "lmfLevel": lmf_lvl,
        "lmfQ": lmf_q, "loCut": locut, "notify": 0, "out": 0,
    })


def chorus(rate, depth, dry_wet):
    return item("toob-chorus",
                {"depth": depth, "dryWet": dry_wet, "in": 0, "out": 0,
                 "outr": 0, "rate": rate})


def delay(ms, feedback, level):
    return item("toob-delay",
                {"delay": ms, "feedback": feedback, "level": level})


def multi_echo():
    # level* and direct are PERCENT (0-100, direct 0-200, default 100), NOT dB.
    # Getting this wrong is what made Ambient silent: direct 0 killed the dry
    # path and negative levels clamped to 0, killing the wet path too.
    # master is the only dB control here.
    return item("toob-multi-echo-stereo", {
        "bypass": 1,
        # Levels and feedback raised, and tap 3 brought in, for a wetter
        # Ambient. Only that preset calls this.
        "tap1": 1, "delay1": 500, "level1": 45, "feedback1": 38, "pan1": -0.4,
        "tap2": 1, "delay2": 750, "level2": 35, "feedback2": 32, "pan2": 0.4,
        "tap3": 1, "delay3": 1000, "level3": 20, "feedback3": 22, "pan3": 0,
        "tap4": 0, "delay4": 1250, "level4": 0, "feedback4": 0, "pan4": 0,
        "direct": 100, "master": 0, "tails": 1,
        "inl": 0, "outl": 0, "inr": 0, "outr": 0,
    })


def freeverb(dry_wet, room, damping=0.35):
    return item("toob-freeverb", {
        "bypass": 1, "damping": damping, "dryWet": dry_wet, "inL": 0,
        "inR": 0, "outL": 0, "outR": 0, "roomSize": room, "tails": 1,
    })


def conv_reverb(wav, mix, time=3.0):
    # `time` truncates the IR, in SECONDS (max 30 = use all of it). Shorter =
    # less convolution work. The default of 30 was needlessly expensive.
    return item("toob-convolution-reverb-stereo", {
        "bypass": 1, "control": 0, "decay": 0, "direct_mix": 0, "inL": 0,
        "inR": 0, "loading_state": 0, "notify": 0, "outL": 0, "outR": 0,
        "pan": 0, "predelay": -1, "predelay_new": 1, "reverb_mix": mix,
        "start": 1, "stretch": 1, "tails": 1, "time": time, "width": 1,
    }, {P + "toob-impulse#impulseFile": RV_DIR + "/" + wav})


# ---- snapshots -------------------------------------------------------
#
# A snapshot is NOT a sparse diff, despite looking like one. Verified in
# PiPedal source, src/AudioHost.cpp -> IndexedSnapshotValue:
#
#   * The constructor pre-fills EVERY input control with the plugin's TTL
#     default, then overwrites only the keys the snapshot lists. A key you
#     omit is reset to the PLUGIN DEFAULT -- not left at the preset's value.
#   * An item with no SnapshotValue at all gets isEnabled=true and every
#     control defaulted. So every snapshot must carry a value for every item.
#   * ApplyValues() calls SetBypass(isEnabled) and THEN SetControl() on every
#     input control -- including the lv2:enabled ("bypass") port where the
#     plugin has one. For those plugins the `bypass` control value therefore
#     WINS over isEnabled. snap_value() keeps the two in step.
#     lv2:enabled semantics: 1 = active, 0 = bypassed.
#   * At snapshot-apply time the realtime path is fed from `pathProperties`;
#     the SetLv2State call in ApplyValues is commented out. Preset *load*
#     still restores from lv2State (see item()). So write BOTH, from one
#     source -- exactly as item() does.
#
# Hence the rule: build every snapshot value FROM its item, then override.
# Never hand-write a snapshot value.


class rel:
    """A relative change: rel(+3.5) means 'this item's value, plus 3.5'.

    Used instead of absolute numbers so snapshots survive re-voicing. Levels
    are about to be matched preset by preset, and every one of those edits
    would otherwise have to be mirrored into four snapshots by hand.
    """

    def __init__(self, amount):
        self.amount = amount


def snap_value(it, enabled=None, controls=None, paths=None):
    """One complete SnapshotValue, derived from the item it shadows."""
    controls = dict(controls or {})
    base = {c["key"]: c["value"] for c in it["controlValues"]}
    merged = dict(base)

    unknown = sorted(set(controls) - set(base))
    if unknown:
        raise KeyError("%s has no control %s" % (it["pluginName"], unknown))

    if enabled is None:
        enabled = it["isEnabled"]
    # Keep the lv2:enabled port in step with isEnabled. SetControl runs after
    # SetBypass, so leaving this at the item's value would silently re-enable
    # (or mute) the plugin the moment the snapshot is applied.
    if "bypass" in merged and "bypass" not in controls:
        merged["bypass"] = 1 if enabled else 0
    merged.update(controls)

    for key, value in list(merged.items()):
        if isinstance(value, rel):
            merged[key] = base[key] + value.amount

    paths = dict(paths or {})
    base_paths = {k: json.loads(v)["value"]
                  for k, v in it["pathProperties"].items()}
    unknown = sorted(set(paths) - set(base_paths))
    if unknown:
        raise KeyError("%s has no path property %s"
                       % (it["pluginName"], unknown))
    base_paths.update(paths)

    return {
        "instanceId": it["instanceId"],
        "isEnabled": enabled,
        "controlValues": [{"key": k, "value": v} for k, v in merged.items()],
        "lv2State": lv2_state(base_paths),
        "pathProperties": {k: path_prop(v) for k, v in base_paths.items()},
    }


def snapshot(name, color, items, changes=None):
    """A complete snapshot over `items`.

    `changes` is keyed by (plugin short name, nth occurrence) -- so the second
    toob-nam in a preset is ("toob-nam", 1). An unmatched key raises rather
    than silently doing nothing; a typo there is otherwise invisible.
    """
    changes = dict(changes or {})
    values = []
    seen = {}
    for it in flatten(items):
        short = short_name(it["uri"])
        nth = seen.get(short, 0)
        seen[short] = nth + 1
        values.append(snap_value(it, **changes.pop((short, nth), {})))
    if changes:
        raise KeyError("snapshot %r: no such item(s) %s"
                       % (name, sorted(changes)))
    return {"name": name, "color": color, "isModified": False,
            "values": values}


# Valid `color` keys are the Material palette names in
# vite/src/pipedal/MaterialColors.tsx: grey blueGrey red pink purple
# deepPurple indigo blue lightBlue cyan teal green lightGreen lime yellow
# amber orange deepOrange brown. Anything else silently falls back to grey.

PEDAL = ("toob-nam", 0)    # the pedal capture, where a preset has one
AMP = ("toob-nam", 1)      # the amp capture in presets that have a pedal
AMP0 = ("toob-nam", 0)     # the amp capture in presets that don't
GATE = ("toob-noise-gate", 0)
EQ3 = ("toob-three-band-eq", 0)
EQ3S = ("toob-three-band-eq-stereo", 0)
GEQ = ("toob-graphiceq", 0)
PITCH = ("pitch-shift", 0)
PEQ = ("toob-parametric-eq", 0)
DELAY = ("toob-delay", 0)
FREEVERB = ("toob-freeverb", 0)
CHORUS = ("toob-chorus", 0)
MECHO = ("toob-multi-echo-stereo", 0)
CONVERB = ("toob-convolution-reverb-stereo", 0)
SPLIT = ("Split", 0)
# Preset 6's flattened order is: split, then top chain (fuzz, Kraken), then
# bottom chain (Tweed). flatten() emits the split node before its children
# and the top chain before the bottom, so the fuzz is still the first
# toob-nam even though it now lives inside the split rather than ahead of it.
# Three toob-nam instances -- one past the old cap of 2, which testing on the
# Pi 4 disproved (handoff 6.13).
MASSIVE_FUZZ = ("toob-nam", 0)
MASSIVE_TOP = ("toob-nam", 1)
MASSIVE_BOT = ("toob-nam", 2)


def snapshots_for(name, items):
    """Snapshot 1 of every preset is that preset's home sound, and the rest
    are ordered most-useful-first. The footswitch count is still undecided,
    so a 3-switch layout has to lose the least important snapshot rather than
    an arbitrary one."""
    if name == "1 Clean":
        s = [
            # By-ear edit, folded in from the live bank (2026-10-04): a touch
            # of 800 Hz and a level lift on the Graphic EQ for the home sound.
            snapshot("Clean", "green", items, {
                GEQ: {"controls": {"gain_800hz": 4, "level": 8}},
            }),
            # Inserted at slot 2, not appended, because this file's own rule
            # is most-useful-first so a 3-switch layout degrades gracefully
            # -- a drive toggle on a clean amp beats "Wash". Nothing is bound
            # to a footswitch yet, so there is no muscle memory to break.
            # Move the line if you disagree.
            snapshot("Drive", "lime", items, {
                PEDAL: {"enabled": True},
            }),
            snapshot("Solo", "amber", items, {
                AMP: {"controls": {"outputGain": rel(+3.5)}},
                EQ3: {"controls": {"treble": rel(+0.5)}},
                DELAY: {"controls": {"level": rel(+10)}},
            }),
            snapshot("Dry", "blueGrey", items, {
                DELAY: {"enabled": False},
                FREEVERB: {"enabled": False},
            }),
            snapshot("Wash", "lightBlue", items, {
                DELAY: {"controls": {"delay": 520, "feedback": rel(+12),
                                     "level": rel(+18)}},
                FREEVERB: {"controls": {"dryWet": 0.38, "roomSize": 0.70}},
            }),
        ]

    elif name == "2 Ambient":
        s = [
            # Glass keeps the Fender Tweed, as asked -- and it has to be the
            # one that does, because snapshot 1 is built to equal the item
            # values and the preset opens on it (selectedSnapshot 0). So the
            # ITEM stays Fender and the other three snapshots override the
            # capture to the Kraken, rather than the other way round.
            # By-ear edit, folded in from the live bank (2026-10-04): the
            # 3-band EQ's gain raised to 5.58 (was the -2 trim) for Glass only.
            snapshot("Glass", "lightBlue", items, {
                EQ3: {"controls": {"gain": 5.583333}},
            }),
            # Kraken Gain-I G5 -- the lowest-gain Gain-I capture that
            # exists (the pack runs G5/G7/G8/G10, each with a TrebleBoost
            # variant). inputGain -14 rather than the Fender's -12 keeps it
            # from breaking up: this is an ambient bed, not a crunch.
            snapshot("Swell", "cyan", items, {
                AMP: {"paths": {P + "toob-nam#modelFile":
                                KRAKEN + "/Kraken_Gain-I_G5.nam"},
                      "controls": {"inputGain": -14}},
                CHORUS: {"controls": {"dryWet": 0.75}},
                MECHO: {"controls": {"master": rel(+3), "level1": 58,
                                     "level2": 48}},
                CONVERB: {"controls": {"reverb_mix": rel(+3)}},
            }),
            snapshot("Fuzz", "purple", items, {
                AMP: {"paths": {P + "toob-nam#modelFile":
                                KRAKEN + "/Kraken_Gain-I_G5.nam"},
                      "controls": {"inputGain": -14}},
                PEDAL: {"enabled": True},
            }),
            # The Sunface pack's C3/C5/C8 captures ARE the rolled-back guitar
            # volume positions and would be more authentic here, but their
            # exact filenames aren't verified and a wrong one is a silently
            # dead snapshot. Dropping inputGain into the same capture loses
            # drive the same way with no filename risk. Swap it later if you
            # confirm the names -- preflight() will catch a bad guess.
            snapshot("Fuzz Rolled Off", "deepPurple", items, {
                AMP: {"paths": {P + "toob-nam#modelFile":
                                KRAKEN + "/Kraken_Gain-I_G5.nam"},
                      "controls": {"inputGain": -14}},
                PEDAL: {"enabled": True, "controls": {"inputGain": rel(-7)}},
            }),
        ]

    elif name == "3 Crunch":
        s = [
            snapshot("Crunch", "orange", items),
            snapshot("Raw", "amber", items, {
                PEDAL: {"enabled": False},          # TS9 boost out
            }),
            # The trailing space in "G8 .nam" is real -- see the filename
            # traps note. preflight() checks it.
            snapshot("Push", "deepOrange", items, {
                AMP: {"paths": {P + "toob-nam#modelFile":
                                KRAKEN + "/Kraken_Gain-I_G8 .nam"}},
            }),
            snapshot("Lead", "red", items, {
                AMP: {"controls": {"outputGain": rel(+3)}},
                EQ3: {"controls": {"mid": rel(+1)}},
                DELAY: {"controls": {"level": rel(+10), "feedback": rel(+8)}},
            }),
        ]

    elif name == "4 HG Rhythm":
        s = [
            snapshot("Rhythm", "red", items),
            snapshot("Solo", "deepOrange", items, {
                AMP0: {"controls": {"outputGain": rel(+3.5)}},
                PEQ: {"controls": {"hmfLevel": rel(+2)}},
                FREEVERB: {"controls": {"dryWet": 0.14}},
            }),
            snapshot("Tight", "blueGrey", items, {
                GATE: {"controls": {"threshold": rel(+7), "hold": 40,
                                    "release": 140}},
                PEQ: {"controls": {"loCut": 110}},
            }),
            snapshot("Wide", "indigo", items, {
                FREEVERB: {"controls": {"dryWet": 0.16, "roomSize": 0.40}},
                PEQ: {"controls": {"hiCut": 13}},      # kHz, see peq()
            }),
        ]

    elif name == "5 HG Lead":
        s = [
            snapshot("Lead", "deepOrange", items),
            snapshot("Rhythm", "brown", items, {
                AMP0: {"controls": {"outputGain": rel(-3)}},
                DELAY: {"controls": {"level": rel(-14)}},
                CONVERB: {"controls": {"reverb_mix": rel(-6)}},
            }),
            snapshot("Solo+", "red", items, {
                AMP0: {"controls": {"outputGain": rel(+2.5)}},
                DELAY: {"controls": {"feedback": rel(+8), "level": rel(+8)}},
            }),
            snapshot("Dry", "blueGrey", items, {
                DELAY: {"enabled": False},
                CONVERB: {"enabled": False},
            }),
        ]

    elif name == "6 Massive":
        KRK = KRAKEN + "/Kraken_Gain-"

        def massive(top_capture, top_gain, mix, fuzz=None):
            """The Tweed in the bottom chain never moves -- only the top
            capture, the blend, and whether the fuzz is in."""
            return {
                MASSIVE_TOP: {
                    "paths": {P + "toob-nam#modelFile": top_capture},
                    "controls": {"inputGain": top_gain}},
                SPLIT: {"controls": {"mix": mix}},
                MASSIVE_FUZZ: ({"enabled": True,
                                "paths": {P + "toob-nam#modelFile": fuzz}}
                               if fuzz else {"enabled": False}),
            }

        s = [
            # By-ear edit, folded in from the live bank (2026-10-04): saved
            # with the pitch shifter on, down 5 semitones.
            snapshot("Massive", "teal", items, {
                PITCH: {"controls": {"semitones": -5, "power": 1}},
            }),
            # Gain-I G5 -> Gain-I G7 -> Gain-II G8. The channel change to
            # Gain-II is the last step, rather than swapping the clean amp
            # out, which was too abrupt a jump.
            snapshot("Heavier", "amber", items,
                     massive(KRK + "I_G7.nam", -10, -0.30)),
            snapshot("Heaviest", "red", items,
                     massive(KRK + "II_G8.nam", -8, -0.20)),
            # Fuzz Low / Fuzz High are different CIRCUITS, not two levels
            # of one: germanium Fuzz Face vs silicon Big Muff. Both keep
            # the full amp blend behind them. Top capture matches Heaviest
            # (Gain-II G8, same -8/0 gain) on request, 2026-09-10 -- not G5.
            # Fuzz Low's own capture is the softer/cleaner-guitar-volume
            # SunFace V7 F10 C3 (not the hot C10 used elsewhere), so the
            # "low" in the name is the fuzz circuit itself, not just a lower
            # amp gain under it.
            snapshot("Fuzz Low", "orange", items,
                     massive(KRK + "II_G8.nam", -8, -0.10,
                             fuzz=SUNFACE + "/SunFace RCA V7 F10 C3.nam")),
            snapshot("Fuzz High", "deepPurple", items,
                     massive(KRK + "II_G8.nam", -8, 0.10, fuzz=FUZZ_HIGH)),
        ]

    else:
        raise KeyError("no snapshot design for preset %r" % name)

    # Snapshot.MAX_SNAPSHOTS is 6 (vite/src/pipedal/Pedalboard.tsx), and the
    # array is fixed-length with nulls for the empty slots.
    if len(s) > 6:
        raise ValueError("%s: %d snapshots, max 6" % (name, len(s)))
    return s + [None] * (6 - len(s))


LV2_DIR = "/usr/lib/lv2/ToobAmp.lv2"
LV2_TTL_GLOBS = (LV2_DIR + "/*.ttl",
                 "/usr/lib/lv2/PitchShiftTone3000.lv2/pitch_shift.ttl")


def _port_ranges(text):
    """symbol -> (minimum, maximum) for one plugin's chunk of a .ttl.

    Deliberately a scanner rather than a parser: it walks bracket-balanced
    blocks and pulls lv2:symbol / lv2:minimum / lv2:maximum out of each. Good
    enough to catch a value that is out of range, which is all this is for.
    """
    ranges = {}
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "[":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0 and start is not None:
                block = text[start:i]
                symbol = re.search(r'lv2:symbol\s+"([^"]+)"', block)
                lo = re.search(r"lv2:minimum\s+(-?[\d.eE+]+)", block)
                hi = re.search(r"lv2:maximum\s+(-?[\d.eE+]+)", block)
                if symbol and lo and hi:
                    ranges[symbol.group(1)] = (float(lo.group(1)),
                                               float(hi.group(1)))
                start = None
    return ranges


def _all_port_ranges():
    """plugin URI -> {symbol: (min, max)}, read off the installed TTLs."""
    result = {}
    paths = [p for g in LV2_TTL_GLOBS for p in sorted(glob.glob(g))]
    for path in paths:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        # Plugin declarations start at column 0 with <uri>. Everything up to
        # the next such line belongs to that plugin.
        marks = [(m.start(), m.group(1))
                 for m in re.finditer(r"(?m)^<(https?://[^>]+)>", text)]
        for n, (pos, uri) in enumerate(marks):
            end = marks[n + 1][0] if n + 1 < len(marks) else len(text)
            found = _port_ranges(text[pos:end])
            if found:
                result.setdefault(uri, {}).update(found)
    return result


def check_ranges(built):
    """Warn about control values the host would silently clamp.

    Out-of-range values are clamped without complaint, which is exactly how
    `reduction: -70`, `hicut: 20000` and a 30 s convolution tail all survived
    unnoticed. Warnings only, and skipped entirely if the TTLs can't be read
    -- a parse problem here must never block a rebuild.
    """
    try:
        ranges = _all_port_ranges()
    except Exception as e:                      # noqa: BLE001 - never fatal
        print("range check skipped (%s)" % e)
        return
    if not ranges:
        print("range check skipped: no port ranges found in " + LV2_DIR)
        return

    warnings = []
    for entry in built:
        preset = entry["preset"]
        places = [("item", it) for it in flatten(preset["items"])]
        for snap in preset["snapshots"]:
            if snap:
                places += [(snap["name"], v) for v in snap["values"]]
        by_id = {it["instanceId"]: it
                 for it in flatten(preset["items"])}
        for where, holder in places:
            uri = holder.get("uri") or by_id[holder["instanceId"]]["uri"]
            plugin_ranges = ranges.get(uri)
            if not plugin_ranges:
                continue
            for control in holder["controlValues"]:
                bounds = plugin_ranges.get(control["key"])
                if not bounds:
                    continue
                lo, hi = bounds
                value = control["value"]
                if value < lo or value > hi:
                    warnings.append(
                        "  %-12s %-16s %-14s %-10s %s not in [%g, %g]"
                        % (preset["name"], where, uri.rsplit("/", 1)[-1],
                           control["key"], value, lo, hi))
    if warnings:
        print("\nOUT OF RANGE -- these will be silently clamped:")
        for line in warnings:
            print(line)
        print("")
    else:
        print("range check: all control values within their TTL ranges")


def report(built):
    for entry in built:
        preset = entry["preset"]
        snaps = [x["name"] for x in preset["snapshots"] if x]
        print("  %-12s %d plugins  %d snapshots: %s"
              % (preset["name"], len(flatten(preset["items"])),
                 len(snaps), ", ".join(snaps)))


def backup_dir():
    """Where to put the backup.

    This script runs under sudo, and under sudo os.path.expanduser("~") is
    /root -- so backups silently landed somewhere the user can't even list.
    Prefer the invoking user's home, which is where anyone would look.
    """
    user = os.environ.get("SUDO_USER")
    if user:
        try:
            import pwd
            return pwd.getpwnam(user).pw_dir
        except (KeyError, ImportError):
            pass
    return os.path.expanduser("~")


AUDIO_ROOT = "/var/pipedal/audio_uploads"


def preflight(built):
    """Every capture and IR referenced anywhere must actually exist.

    Worth doing because the failure mode is silent: a NAM path that doesn't
    resolve gives an empty file selector and no model, not an error. Known
    traps this catches -- "Kraken_Gain-I_G8 .nam" has a trailing space, and
    the Gain-II boost files are misspelled "TebleBoost" with no r.
    """
    missing = []
    seen = set()
    for entry in built:
        preset = entry["preset"]
        holders = list(flatten(preset["items"]))
        for snap in preset["snapshots"]:
            if snap:
                holders += snap["values"]
        for holder in holders:
            for raw in holder.get("pathProperties", {}).values():
                value = json.loads(raw)["value"]
                if not value or (preset["name"], value) in seen:
                    continue
                seen.add((preset["name"], value))
                if not os.path.exists(os.path.join(AUDIO_ROOT, value)):
                    missing.append((preset["name"], value))
    if missing:
        print("\nMISSING FILES -- nothing was written:\n")
        for preset_name, value in missing:
            print("  %-14s %s" % (preset_name, value))
        sys.exit("\n%d referenced file(s) not found under %s"
                 % (len(missing), AUDIO_ROOT))

# ---- the six presets -------------------------------------------------

CLEAN_CAP = NAM_DIR + "/1960 Fender Tweed Deluxe 5E3 - Clean.nam"
IR_1960TV = "M25 UL 1960TV 4x12 SM57 2.00in 0.0in 7603.wav"
IR_1960TV_OA30 = "M25 UL 1960TV 4x12 SM57 2.00in 0.0in OA30 7603.wav"
IR_JCM800 = "Marshall JCM800 Lead 1960 A (4- SM57, eoc).wav"


def presets():
    # Third element is the preset's master Output Volume (output_volume_db)
    # -- the fader after everything, used for cross-preset level-matching
    # (2026-09-10 pass). Defaults to 0 where omitted.
    return [
        ("1 Clean", [
            tuner(),
            # Raised from -90 on request -- -90 never closed on idle hum/hiss
            # (see session notes on the front gate). -80 is still deliberately
            # loose for a clean amp so it doesn't chop quiet playing.
            gate(-80),
            input_stage(trim=0, locut=80),
            # Blues Driver, bypassed by default -- the "Drive" snapshot is
            # the toggle. Low output_gain because this is an edge-of-breakup
            # push on an already-clean Tweed, not a lead boost. Adding it
            # makes the amp the SECOND toob-nam in this preset, so preset 1's
            # snapshots now select it with AMP, not AMP0.
            pedal(BLUESDRIVER, input_gain=-10, output_gain=-4, enabled=False,
                  threaded=True),
            nam(CLEAN_CAP, -12, 5, 5, 6, threaded=True),
            cab_ir(IR_1960TV),
            eq3(4.5, 4.5, 6.5, gain=-2),
            delay(380, 18, 12),
            freeverb(0.18, 0.45),
        ], 8),
        ("2 Ambient", [
            tuner(),
            gate(-80),
            # Germanium fuzz FIRST -- fuzz circuits want to see the guitar
            # directly. Bypassed by default; stomp it on for fuzzy ambient
            # swells. C10 = guitar volume full; the C3/C5/C8 captures in the
            # same pack are the rolled-back cleanup positions, and swapping
            # this capture per snapshot is how you get the volume-knob sweep.
            pedal(SUNFACE + "/SunFace RCA V7 F10 C10.nam",
                  input_gain=-12, output_gain=-8, enabled=False,
                  threaded=True),
            input_stage(trim=2, locut=90),
            nam(CLEAN_CAP, -14, 4, 5, 6, threaded=True),
            cab_ir(IR_1960TV),
            # Added during the 2026-09-10 level-match pass -- pure loudness
            # trim for this preset, not a tone-shaping EQ.
            eq3(5, 5, 5, gain=-2),
            # Deeper and wetter than before, per request for more modulation.
            chorus(0.28, 0.55, 0.55),
            # CE-2W capture removed: it was a 3rd NAM instance, and 3 does not
            # fit on a Pi 4 (see notes on preset 6). It also couldn't have
            # worked -- NAM is time-invariant, so no LFO, no chorus. Add it in
            # the UI temporarily if you still want to hear that for yourself.
            multi_echo(),
            # -4 rather than -6: more reverb across the whole preset. Kept
            # clear of 0 dB deliberately, because Swell adds rel(+3) on top
            # and check_ranges() could not be run to confirm this control's
            # ceiling (Pi was offline).
            conv_reverb("St. Margaret's Church.wav", -4),
        ], 3),
        ("3 Crunch", [
            tuner(),
            gate(-60),
            input_stage(trim=0, locut=85),
            # TS9 with drive at 0 and level at 10: pure level into the amp,
            # no dirt of its own. The classic tightening boost.
            pedal(TS9 + "/Ibanez-TS9-D0-T6-L10.nam", threaded=True),
            nam(KRAKEN + "/Kraken_Gain-I_G7.nam", -8, 5, 6, 5, threaded=True),
            cab_ir(IR_JCM800),
            eq3(4.5, 5.5, 5),
            delay(340, 22, 8),
            freeverb(0.12, 0.35),
        ]),
        ("4 HG Rhythm", [
            tuner(),
            # Threshold lowered from -45 (it was chopping tails) and the
            # transition softened. NOT the crackle fix -- the gate was
            # observed open, LED lit, while the crackle was audible.
            gate(-55, hold=90, release=220, reduction=-45, attack=3,
                 hysteresis=-12),
            # Crackle here was output headroom, nothing else. Ruled out, in
            # order, each by test rather than argument: DSP load (9.4% here,
            # 0 underruns); the front noise gate (observed open, LED lit,
            # while the crackle was audible); the OA30 cab IR (48 kHz mono,
            # same format as presets 1-2 which are clean); a missing
            # input_stage high-pass (added in the UI, no change); and the
            # NAM's own internal gate, which was -70 here and in 6 and
            # nowhere else -- set to -120 in the UI and the crackle stayed,
            # so it is not the cause. Left at the -120 default anyway, which
            # matches every other preset; -70 is a hiss preference, not a
            # crackle fix, and tones.md says only reach for it if the front
            # gate leaves hiss between chugs.
            #
            # outputGain -4, not 0. "Rhythm" at 0 was clean but "Solo" was
            # not, and Solo is the same chain with rel(+3.5) output and
            # rel(+2) presence -- up to +5.5 dB. So the clip threshold sat
            # between them. -4 puts Solo at -0.5, just under the level that
            # was already known good, and every snapshot follows through
            # rel(). Confirmed by the 2026-09-10 level-match pass against
            # preset 3 -- output_volume_db stays 0 here, no further trim
            # needed.
            nam(KRAKEN + "/Kraken_Gain-II_G8.nam", -6, 5, 5.5, 5.5,
                output_gain=-4, threaded=True),
            cab_ir(IR_1960TV_OA30),
            peq(90, 350, -3, 1.0, 2.2, 1.5, 12),
            freeverb(0.06, 0.25),
        ]),
        ("5 HG Lead", [
            tuner(),
            gate(-50, hold=80, release=250),
            input_stage(trim=4, locut=95),
            nam(KRAKEN + "/Kraken_Gain-II_G10_TebleBoost.nam", -6, 4.5, 6,
                5.5, threaded=True),
            cab_ir(IR_JCM800),
            # hiCut dropped from 13 to 9.5 kHz on request, 2026-09-10.
            peq(100, 800, 2, 1.2, 2.5, 2, 9.5),
            delay(375, 32, 20),
            conv_reverb("Arthur Sykes Rymer Auditorium.wav", -10),
        ], -2),
        # Massive: two amps in PARALLEL and summed, not switched -- a Kraken
        # on top with a clean Tweed underneath to put weight and body back
        # under it. The Tweed stays put in EVERY snapshot; heaviness comes
        # from walking the top capture up the ladder
        # (Gain-I G5 -> Gain-I G7 -> Gain-II G8) and shifting the blend
        # toward it. Swapping the clean amp out entirely was too big a jump.
        #
        # THREE NAM INSTANCES, and it holds on a Pi 4 -- tested 2026-09-05.
        # That disproves the old cap of 2 (handoff 6.2), which came from a
        # pre-`Threaded` measurement; Threaded turned out to be worth
        # 2.5-3.7x (6.6). The only xruns observed were on changing preset
        # while still playing, which is the documented graph-rebuild gap and
        # not specific to this preset. All three instances run constantly: a
        # blend is not a switch, and a bypassed instance still costs.
        # Still the heaviest preset in the bank by a distance -- re-measure
        # with pipedal-probe.py after any change here.
        #
        # ONE cab IR, after the split, shared by both chains. Two would be a
        # second convolution for no musical gain.
        ("6 Massive", [
            tuner(),
            gate(-55, hold=90, release=260, reduction=-45, attack=3,
                 hysteresis=-12),
            input_stage(trim=0, locut=85),
            split(
                # top: the dirty path, fuzz INTO the Kraken. The fuzz lives
                # inside this chain, so it hits the Kraken only -- the Tweed
                # underneath stays clean, and that is what holds the note
                # definition together on the fuzz snapshots. Bypassed at
                # home; the two fuzz snapshots switch it on and pick the
                # circuit.
                # Kraken inputGain is low because G5 is already the
                # lowest-gain Gain-I capture and this is the clean-ish home
                # sound; the heavier snapshots drive it harder.
                [pedal(FUZZ_LOW, input_gain=-12, output_gain=-8,
                       enabled=False, threaded=True),
                 nam(KRAKEN + "/Kraken_Gain-I_G5.nam", -14, 5, 5.5, 5.5,
                     threaded=True)],
                # bottom: the clean blend, identical in every snapshot.
                # -3 dB so it supports rather than dominates.
                [nam(CLEAN_CAP, -12, 5.5, 5, 5.5, output_gain=-3,
                     threaded=True)],
                split_type=SPLIT_MIX, mix=0),
            cab_ir(IR_1960TV),
            peq(85, 400, -2, 1.0, 2.5, 1, 11, gain=2),
            # wet: mod, delay and reverb. EMT 140 is the only reverb IR that
            # is already 48 kHz stereo and needs no resampling, so it is the
            # cheap one -- and this preset has the least CPU to spare.
            chorus(0.25, 0.50, 0.40),
            delay(420, 30, 20),
            conv_reverb("EMT 140 Medium 2.wav", -5, time=2.9),
        ]),
        # Preset 6 "Loathe" was removed on request -- it never sounded right
        # and it was the source of the crackle hunt. If it comes back, it
        # needs preamp-only/no-cab captures and a level-matched output, not a
        # revival of the old values. The HM-2, SF300, Big Muff and Peavey
        # 6505 captures are all still on the Pi.
    ]


def main():
    # --dry-run reads only: it builds everything in memory and runs both
    # preflight checks against the real captures and the real TTLs, then
    # exits. Needs no sudo and no service stop, so it can be run while
    # pipedald is live to prove a change is safe before committing to it.
    dry_run = "--dry-run" in sys.argv[1:]

    if not os.path.exists(BANK):
        sys.exit("bank not found: " + BANK)

    if not dry_run:
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = os.path.join(backup_dir(), "bank-backup-" + stamp + ".json")
        shutil.copy2(BANK, backup)
        if os.environ.get("SUDO_UID"):
            # otherwise the backup is root-owned and the user can't manage it
            os.chown(backup, int(os.environ["SUDO_UID"]),
                     int(os.environ.get("SUDO_GID", -1)))
        print("backup written to", backup)

    with open(BANK) as f:
        bank = json.load(f)

    st = os.stat(BANK)

    built = []
    next_id = 1
    for entry in presets():
        # Third element is output_volume_db, from the 2026-09-10
        # level-match pass. Defaults to 0 where a preset omits it.
        name, items, *rest = entry
        items = with_menu_plugins(items)
        output_volume_db = rest[0] if rest else 0
        built.append({
            "instanceId": next_id,
            "preset": {
                "name": name,
                "input_volume_db": 0,
                "output_volume_db": output_volume_db,
                "items": items,
                "nextInstanceId": _next_id[0] + 1,
                "snapshots": snapshots_for(name, items),
                # 0 = the preset opens on its home snapshot. Snapshot 1 is
                # built to equal the item values, so the two always agree.
                "selectedSnapshot": 0,
                "selectedPlugin": [i["instanceId"] for i in flatten(items)
                                   if i["uri"].endswith("toob-nam")][-1],
            },
        })
        next_id += 1

    preflight(built)
    check_ranges(built)

    if dry_run:
        report(built)
        print("")
        print("--dry-run: nothing written. Re-run without the flag, "
              "with pipedald stopped, to commit.")
        return

    # bank name left alone on purpose: PiPedal derives the .bank filename from
    # it, so renaming here would orphan the file. Rename in the UI instead.
    bank["presets"] = built
    bank["nextInstanceId"] = next_id
    bank["selectedPreset"] = 1

    tmp = BANK + ".tmp"
    with open(tmp, "w") as f:
        json.dump(bank, f, indent=1)
    json.load(open(tmp))                      # parse-check before swapping in
    os.replace(tmp, BANK)
    os.chown(BANK, st.st_uid, st.st_gid)
    os.chmod(BANK, st.st_mode)

    print("wrote %d presets:" % len(built))
    report(built)


if __name__ == "__main__":
    main()
