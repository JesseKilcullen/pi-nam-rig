#!/usr/bin/env python3
"""pipedal_pc_probe.py — answers open question #1 in pipedal-hardware-v2.md §5:
"Does PiPedal accept absolute Program Change to select a preset?"

Needs NO footswitch hardware at all — just the Pi with PiPedal running and
its ALSA MIDI port visible. Run this on the Pi itself (or wherever amidi/mido
can see PiPedal's MIDI-in port).

It sends Program Change 0-5 and CC20 (force snapshot 1) one at a time,
pausing between each so you can watch PiPedal's UI and confirm the preset
actually changed. It does NOT verify PiPedal's response automatically —
PiPedal has no documented feedback protocol for this (see §4.1's note about
the undocumented WebSocket) — so this is a guided manual test, not an
automated pass/fail.

Setup:
    pip install mido python-rtmidi

Usage:
    python3 pipedal_pc_probe.py --list          # find PiPedal's port name
    python3 pipedal_pc_probe.py --port "PiPedal"  # run the probe
"""

import argparse
import sys
import time

try:
    import mido
except ImportError:
    sys.exit(
        "mido not installed. Run: pip install mido python-rtmidi\n"
        "(python-rtmidi is the backend mido needs for real ALSA/USB ports.)"
    )

MIDI_CHANNEL = 0  # 0-indexed for mido; matches MIDI_CHANNEL=1 in code.py


def list_ports():
    names = mido.get_output_names()
    if not names:
        print("No MIDI output ports visible. Is PiPedal running?")
        return
    print("Available MIDI output ports:")
    for n in names:
        print(" ", n)


def run_probe(port_name, delay):
    with mido.open_output(port_name) as port:
        for preset in range(6):
            input(
                "\nPress Enter to send Program Change {} (\"Preset {}\" in "
                "PiPedal's UI, if 1-indexed there)...".format(preset, preset + 1)
            )
            port.send(mido.Message("program_change", program=preset, channel=MIDI_CHANNEL))
            print("  sent PC {}".format(preset))
            time.sleep(delay)

        input("\nPress Enter to send CC20=127 (force snapshot 1)...")
        port.send(mido.Message("control_change", control=20, value=127, channel=MIDI_CHANNEL))
        print("  sent CC20=127")

    print(
        "\nDone. Compare what you sent against what PiPedal's UI showed at "
        "each step:\n"
        "  - If PC 0 selected the first preset in the list, PC is 0-indexed "
        "there (matches midi_logic.py's press_row/press_reset).\n"
        "  - If it was off by one, PiPedal expects 1-indexed PC and code.py's "
        "ProgramChange(index) calls need a +1.\n"
        "  - If nothing changed at all, PiPedal isn't bound to Program "
        "Change for preset select — check its MIDI binding UI (§13.A of "
        "pipedal-nam-rig-plan.md) before trusting this whole approach."
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="list MIDI output ports and exit")
    ap.add_argument("--port", help="MIDI output port name (substring match)")
    ap.add_argument("--delay", type=float, default=0.3, help="seconds to pause after each send")
    args = ap.parse_args()

    if args.list or not args.port:
        list_ports()
        if not args.port:
            print("\nRe-run with --port \"<name from above>\" to start the probe.")
        return

    matches = [n for n in mido.get_output_names() if args.port.lower() in n.lower()]
    if not matches:
        sys.exit("No port matching {!r}. Run --list to see options.".format(args.port))
    if len(matches) > 1:
        sys.exit("Ambiguous match for {!r}: {}".format(args.port, matches))

    run_probe(matches[0], args.delay)


if __name__ == "__main__":
    main()
