#!/usr/bin/env python3
"""midi_monitor.py — live decoder for the Pico's USB MIDI output.

For once the Pico is flashed and wired to switches on a breadboard (no
enclosure needed yet) — plug its USB cable into whatever machine you're
running this on, and every button press prints a decoded, human-readable
line using the exact same mapping table as midi_logic.py, so a wiring
mistake (wrong pin, swapped rows) shows up immediately as the wrong label
instead of a raw hex dump you have to cross-reference by hand.

Setup:
    pip install mido python-rtmidi

Usage:
    python3 midi_monitor.py --list           # find the Pico's port name
    python3 midi_monitor.py --port "Pico"    # watch it live, Ctrl+C to stop
"""

import argparse
import sys

try:
    import mido
except ImportError:
    sys.exit(
        "mido not installed. Run: pip install mido python-rtmidi\n"
        "(python-rtmidi is the backend mido needs for real ALSA/USB ports.)"
    )

from midi_logic import describe


def to_logic_message(msg):
    if msg.type == "control_change":
        return ("cc", msg.control, msg.value)
    if msg.type == "program_change":
        return ("pc", msg.program)
    return None


def list_ports():
    names = mido.get_input_names()
    if not names:
        print("No MIDI input ports visible. Is the Pico plugged in and running code.py?")
        return
    print("Available MIDI input ports:")
    for n in names:
        print(" ", n)


def watch(port_name):
    print("Listening on {!r}. Ctrl+C to stop.\n".format(port_name))
    with mido.open_input(port_name) as port:
        for msg in port:
            logic_msg = to_logic_message(msg)
            if logic_msg is None:
                print("(unhandled) {}".format(msg))
                continue
            print("{:<28} raw: {}".format(describe(logic_msg), msg))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="list MIDI input ports and exit")
    ap.add_argument("--port", help="MIDI input port name (substring match)")
    args = ap.parse_args()

    if args.list or not args.port:
        list_ports()
        if not args.port:
            print("\nRe-run with --port \"<name from above>\" to start watching.")
        return

    matches = [n for n in mido.get_input_names() if args.port.lower() in n.lower()]
    if not matches:
        sys.exit("No port matching {!r}. Run --list to see options.".format(args.port))
    if len(matches) > 1:
        sys.exit("Ambiguous match for {!r}: {}".format(args.port, matches))

    try:
        watch(matches[0])
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
