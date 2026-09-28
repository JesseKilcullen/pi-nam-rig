#!/usr/bin/env python3
"""pi_relay.py — persistent Pi-side daemon feeding the Pico's OLED.

Three jobs, all sourced live from PiPedal over its WebSocket (see
pipedal_ws.py) — nothing is hardcoded, so renaming/reordering
presets/snapshots in PiPedal just works:

  1. SNAPSHOT grid. Subscribes to onPedalboardChanged / onSelectedSnapshotChanged
     and forwards all 6 snapshot names (of the currently loaded preset) plus
     which one's active, as a MIDI SysEx message.

  2. PRESET grid. Calls getPresets (+ subscribes to onPresetsChanged) and
     forwards the first 6 preset names in the bank plus which one's active
     (or "none" if the active preset is beyond position 6 -- see
     pipedal_ws.build_preset_grid's docstring), as a MIDI SysEx message.

  3. Live TUNER Hz. Subscribes to TooB Tuner's FREQ control-output port
     via monitorPort (see tuner_freq_probe.py for how that was confirmed
     safe/cheap) and forwards note number + cents offset to the Pico as
     two Control Change messages.

The Pico picks which grid to show locally (PRESET vs SNAPSHOT mode is
whichever mode-select footswitch was pressed last) and caches both grids
at all times so flipping mode redraws instantly with no round-trip.

IMPORTANT — direction and why this can't clash with PiPedal's own MIDI
input: this script only WRITES to the Pico (a brand new Pi -> Pico
direction, going straight to code.py's midi.receive()). It never reads
the Pico's MIDI-out stream (the one carrying footswitch presses to
PiPedal) — the Pico decides locally, from its own tuner_mute_on state,
whether to show the tuner screen or a names grid (see midi_logic.py).
That sidesteps the question of whether two processes can safely share one
ALSA MIDI read side.

New wire conventions, on top of the CCs in pipedal-hardware-v2.md §3:

  CC28  tuner note number      value = MIDI note (0-127), only meaningful
                                while the Pico's local tuner_mute_on is set
  CC29  tuner cents offset     value = round(cents) + 64 (64 == 0 cents),
                                clamped 0-127
  SysEx (manufacturer 0x7D "non-commercial"):
        data[0] = 0x01 (snapshot grid) or 0x02 (preset grid)
        data[1] = highlight index 0-5, or 0xFF for "none highlighted"
        data[2:] = up to 6 names, each 7-bit ASCII, 0x00-separated

Setup:
    pip install websockets mido python-rtmidi

Usage:
    python3 pi_relay.py --list                       # find the Pico's MIDI port
    python3 pi_relay.py --midi-port "Pico" --host pipedal.local
"""

import argparse
import asyncio
import glob
import os
import sys
import time

try:
    import websockets
except ImportError:
    sys.exit("websockets not installed. Run: pip install websockets")

try:
    import mido
except ImportError:
    sys.exit("mido not installed. Run: pip install mido python-rtmidi")

from pipedal_ws import (
    PiPedalClient,
    find_tuner_instance_id,
    build_snapshot_grid,
    build_preset_grid,
    build_full_preset_list,
    GRID_SIZE,
)
from pitch import midi_note_to_note_cents
from midi_logic import (
    CC_TUNER_NOTE,
    CC_TUNER_CENTS,
    SYSEX_MANUFACTURER_ID,
    SYSEX_SNAPSHOT_LIST_SUBTYPE,
    SYSEX_PRESET_LIST_SUBTYPE,
    SYSEX_FULL_PRESET_LIST_SUBTYPE,
    GRID_HIGHLIGHT_NONE,
    BROWSE_MAX_PRESETS,
)

# 3 columns x ~42px/cell at scale=1 leaves room for about this many
# characters per cell (oled_display.py's show_grid truncates to match).
GRID_NAME_MAX_LEN = 6
# Browse mode uses the big two-line tuner-style font instead -- more room
# per name (oled_display.py's show_browse truncates to match).
BROWSE_NAME_MAX_LEN = 10
FREQ_UPDATE_RATE_SECONDS = 1.0 / 20.0
USB_WATCH_INTERVAL_SECONDS = 1.0
# USB enumerates before CircuitPython has finished booting code.py (plus its
# 2 s OLED splash), so names sent the instant the port appears can be lost.
PICO_BOOT_WAIT_SECONDS = 5.0


def pico_usb_devnum(product_substring: str):
    """The Pico's USB device number, or None if it isn't plugged in. The
    kernel assigns a fresh number on every (re)connect, so a change means
    the Pico was unplugged/replugged -- and rebooted, losing its cached names."""
    for product_path in glob.glob("/sys/bus/usb/devices/*/product"):
        try:
            with open(product_path) as f:
                if product_substring.lower() not in f.read().lower():
                    continue
            with open(os.path.join(os.path.dirname(product_path), "devnum")) as f:
                return f.read().strip()
        except OSError:
            continue
    return None


async def wait_for_pico_reconnect(product_substring: str):
    """Returns once the Pico disconnects or re-enumerates. mido keeps
    'sending' to the old ALSA port after a replug, silently reaching
    nothing, so the only reliable recovery is a fresh process."""
    initial = pico_usb_devnum(product_substring)
    while True:
        await asyncio.sleep(USB_WATCH_INTERVAL_SECONDS)
        if pico_usb_devnum(product_substring) != initial:
            return


def ascii_7bit(s: str, max_len: int) -> bytes:
    """Truncate and strip to plain 7-bit ASCII — SysEx data bytes must be
    0-127, and the Pico's tiny bitmap font can't render most of Unicode
    anyway."""
    cleaned = "".join(c if 32 <= ord(c) < 127 else "?" for c in (s or ""))
    return cleaned[:max_len].encode("ascii", errors="replace")


class Relay:
    def __init__(self, midi_out_port_name: str):
        self.midi_out = mido.open_output(midi_out_port_name)
        self.pedalboard: dict = {}
        self.tuner_instance_id = None
        self.sub_handle = None
        self.client: PiPedalClient = None  # set once connected

    def _send_name_list(self, subtype: int, index_byte: int, names, name_max_len: int):
        """Shared wire encoder for every '<subtype> <index byte> <0x00-separated
        names>' SysEx — the 3x2 grids and the full Browse list all use this
        same shape, just with different name counts/lengths."""
        data = [subtype, index_byte]
        for i, name in enumerate(names):
            if i > 0:
                data.append(0x00)
            data += list(ascii_7bit(name, name_max_len))
        self.midi_out.send(mido.Message("sysex", data=[SYSEX_MANUFACTURER_ID] + data))

    def send_grid(self, subtype: int, names, highlight):
        highlight_byte = GRID_HIGHLIGHT_NONE if highlight is None else highlight
        self._send_name_list(subtype, highlight_byte, names[:GRID_SIZE], GRID_NAME_MAX_LEN)

    def send_snapshot_grid(self):
        names, highlight = build_snapshot_grid(self.pedalboard)
        self.send_grid(SYSEX_SNAPSHOT_LIST_SUBTYPE, names, highlight)
        print(f"snapshot grid -> {names} highlight={highlight}")

    async def refresh_preset_data(self):
        """One getPresets fetch feeds both the 3x2 preset grid (first 6
        only) and the full Browse list (up to BROWSE_MAX_PRESETS) — no
        reason to ask PiPedal for the same thing twice."""
        response = await self.client.request("getPresets")

        grid_names, highlight = build_preset_grid(response)
        self.send_grid(SYSEX_PRESET_LIST_SUBTYPE, grid_names, highlight)
        print(f"preset grid -> {grid_names} highlight={highlight}")

        full_names, current_index = build_full_preset_list(response, BROWSE_MAX_PRESETS)
        index_byte = GRID_HIGHLIGHT_NONE if current_index is None else current_index
        self._send_name_list(SYSEX_FULL_PRESET_LIST_SUBTYPE, index_byte, full_names, BROWSE_NAME_MAX_LEN)
        print(f"browse list -> {len(full_names)} presets, current_index={current_index}")

    def send_tuner(self, freq_value: float):
        # FREQ is a fractional MIDI note number, not Hz -- see pitch.py.
        result = midi_note_to_note_cents(freq_value)
        if result is None:
            return
        note_number, cents = result
        cents_byte = max(0, min(127, round(cents) + 64))
        self.midi_out.send(mido.Message("control_change", control=CC_TUNER_NOTE, value=note_number))
        self.midi_out.send(mido.Message("control_change", control=CC_TUNER_CENTS, value=cents_byte))

    async def on_pedalboard_changed(self, pedalboard: dict):
        self.pedalboard = pedalboard
        self.send_snapshot_grid()
        # A preset change means a different preset is now selected, so the
        # preset grid's highlight needs refreshing too. Re-requesting
        # getPresets (rather than assuming onPresetsChanged also fires
        # here) is the certain way to get the fresh selectedInstanceId.
        await self.refresh_preset_data()
        await self.resubscribe_tuner()

    async def on_selected_snapshot_changed(self, selected_snapshot: int):
        self.pedalboard["selectedSnapshot"] = selected_snapshot
        self.send_snapshot_grid()

    async def on_presets_changed(self, presets_response: dict):
        grid_names, highlight = build_preset_grid(presets_response)
        self.send_grid(SYSEX_PRESET_LIST_SUBTYPE, grid_names, highlight)
        print(f"preset grid (pushed update) -> {grid_names} highlight={highlight}")

        full_names, current_index = build_full_preset_list(presets_response, BROWSE_MAX_PRESETS)
        index_byte = GRID_HIGHLIGHT_NONE if current_index is None else current_index
        self._send_name_list(SYSEX_FULL_PRESET_LIST_SUBTYPE, index_byte, full_names, BROWSE_NAME_MAX_LEN)
        print(f"browse list (pushed update) -> {len(full_names)} presets, current_index={current_index}")

    async def resubscribe_tuner(self):
        """A preset change rebuilds the plugin graph, so any previous
        instanceId (and its monitorPort subscription) is stale."""
        if self.sub_handle is not None:
            await self.client.send("unmonitorPort", self.sub_handle)
            self.sub_handle = None

        self.tuner_instance_id = find_tuner_instance_id(self.pedalboard)
        if self.tuner_instance_id is None:
            print("No TooB Tuner in this preset — tuner display disabled until one is loaded.")
            return

        self.sub_handle = await self.client.request(
            "monitorPort",
            {"instanceId": self.tuner_instance_id, "key": "FREQ", "updateRate": FREQ_UPDATE_RATE_SECONDS},
        )
        print(f"Subscribed to FREQ on tuner instance {self.tuner_instance_id} (handle={self.sub_handle})")

    async def on_push(self, message_name, header, body):
        if message_name == "onPedalboardChanged":
            # Unlike the currentPedalboard reply, the push wraps the board as
            # {clientId, pedalboard}; accept either shape.
            if isinstance(body, dict) and "snapshots" not in body and isinstance(body.get("pedalboard"), dict):
                body = body["pedalboard"]
            elif isinstance(body, dict) and "snapshots" not in body:
                print(f"onPedalboardChanged: unexpected body keys {list(body)}")
            await self.on_pedalboard_changed(body)
        elif message_name == "onSelectedSnapshotChanged":
            await self.on_selected_snapshot_changed(body)
        elif message_name == "onPresetsChanged":
            # Same wrapping as onPedalboardChanged: {clientId, presets: <getPresets reply>}.
            if isinstance(body, dict) and isinstance(body.get("presets"), dict):
                body = body["presets"]
            await self.on_presets_changed(body)
        elif message_name == "onMonitorPortOutput":
            self.send_tuner(body["value"])


async def run(host: str, port: int, midi_out_port_name: str, usb_product: str):
    url = f"ws://{host}:{port}/pipedal"
    relay = Relay(midi_out_port_name)

    print(f"Connecting to {url} ...")
    async with websockets.connect(url) as ws:
        client = PiPedalClient(ws, relay.on_push)
        relay.client = client

        client_id = await client.request("hello")
        print(f"Connected. clientId={client_id}")

        pedalboard = await client.request("currentPedalboard")
        await relay.on_pedalboard_changed(pedalboard)

        print("Relay running. Ctrl-C to quit.")
        ws_closed = asyncio.ensure_future(client.run_forever())
        pico_gone = asyncio.ensure_future(wait_for_pico_reconnect(usb_product))
        done, _ = await asyncio.wait({ws_closed, pico_gone}, return_when=asyncio.FIRST_COMPLETED)
        if pico_gone in done:
            print("Pico disconnected/reconnected on USB -- exiting so systemd restarts the relay and resends names.")
        else:
            ws_closed.result()   # surface the connection error, if any
            print("PiPedal websocket closed -- exiting so systemd restarts the relay.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="list MIDI output ports and exit")
    ap.add_argument("--midi-port", help="Pico's MIDI port name (substring match)")
    ap.add_argument("--host", default="pipedal.local", help="PiPedal host (default pipedal.local)")
    ap.add_argument("--port", type=int, default=80, help="PiPedal web port (default 80)")
    args = ap.parse_args()

    if args.list or not args.midi_port:
        names = mido.get_output_names()
        if not names:
            print("No MIDI output ports visible.")
        else:
            print("Available MIDI output ports:")
            for n in names:
                print(" ", n)
        if not args.midi_port:
            print('\nRe-run with --midi-port "<name from above>" to start the relay.')
        return

    matches = [n for n in mido.get_output_names() if args.midi_port.lower() in n.lower()]
    if not matches:
        sys.exit(f"No port matching {args.midi_port!r}. Run --list to see options.")
    if len(matches) > 1:
        sys.exit(f"Ambiguous match for {args.midi_port!r}: {matches}")

    print(f"Found {matches[0]!r}; waiting {PICO_BOOT_WAIT_SECONDS:.0f}s for the Pico to finish booting ...")
    time.sleep(PICO_BOOT_WAIT_SECONDS)

    try:
        asyncio.run(run(args.host, args.port, matches[0], args.midi_port))
    except KeyboardInterrupt:
        print("\nStopped.")
        return
    # Any other way out of run() means the relay can no longer reach the Pico
    # or PiPedal; non-zero so systemd restarts it (see the .service file).
    sys.exit(1)


if __name__ == "__main__":
    main()
