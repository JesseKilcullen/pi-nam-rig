#!/usr/bin/env python3
"""tuner_freq_probe.py — proof of concept for the "Live tuner note + cents"
feature in pipedal-hardware-v2.md §4.1.

Short version: this isn't really reverse-engineering. PiPedal's WebSocket
protocol is a plain JSON request/reply scheme, fully readable in the
open-source repo (rerdavies/pipedal), and it already has a general-purpose
"monitorPort" call used by the web UI's own VU meters and tuner dial
(GxTunerControl.tsx). TooB Tuner's pitch output is just another LV2 control
output port, symbol "FREQ" (see ToobTuner.ttl), URI
http://two-play.com/plugins/toob-tuner. See pipedal_ws.py for the client
plumbing (shared with pi_relay.py, the real daemon this fed into).

This script is now just a diagnostic: connect, subscribe, print Hz. Use it
to sanity-check the websocket side in isolation before trusting pi_relay.py
end to end.

Setup:
    pip install websockets

Usage:
    python3 tuner_freq_probe.py --host pipedal.local
    python3 tuner_freq_probe.py --host 192.168.1.50 --port 80
"""

import argparse
import asyncio
import sys

try:
    import websockets
except ImportError:
    sys.exit("websockets not installed. Run: pip install websockets")

from pipedal_ws import PiPedalClient, find_tuner_instance_id, FREQ_PORT_SYMBOL

UPDATE_RATE_SECONDS = 1.0 / 30.0


async def on_push(message_name, header, body):
    if message_name == "onMonitorPortOutput":
        print(f"\rFREQ = {body['value']:8.2f} Hz   ", end="", flush=True)


async def run(host: str, port: int):
    url = f"ws://{host}:{port}/pipedal"
    print(f"Connecting to {url} ...")

    async with websockets.connect(url) as ws:
        client = PiPedalClient(ws, on_push)

        client_id = await client.request("hello")
        print(f"Connected. clientId={client_id}")

        pedalboard = await client.request("currentPedalboard")
        instance_id = find_tuner_instance_id(pedalboard)
        if instance_id is None:
            sys.exit(
                "No TooB Tuner plugin found in the current pedalboard/preset.\n"
                "Load a preset that has TooB Tuner in the chain, then re-run."
            )
        print(f"Found TooB Tuner instance {instance_id}. Subscribing to FREQ...")

        sub_handle = await client.request(
            "monitorPort",
            {"instanceId": instance_id, "key": FREQ_PORT_SYMBOL, "updateRate": UPDATE_RATE_SECONDS},
        )
        print(f"Subscribed (handle={sub_handle}). Play a note / enable the tuner in the UI.")
        print("Ctrl-C to quit.\n")

        await client.run_forever()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", required=True, help="Pi hostname or IP, e.g. pipedal.local")
    ap.add_argument("--port", type=int, default=80, help="PiPedal web port (default 80)")
    args = ap.parse_args()

    try:
        asyncio.run(run(args.host, args.port))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
