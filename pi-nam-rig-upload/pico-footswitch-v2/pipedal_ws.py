"""pipedal_ws.py — minimal client for PiPedal's WebSocket protocol.

Shared by tuner_freq_probe.py (one-shot diagnostic) and pi_relay.py (the
persistent daemon that feeds the Pico's OLED). Protocol details reverse
engineered from the open-source rerdavies/pipedal repo — see the notes in
tuner_freq_probe.py's docstring for how each piece was confirmed:

  - src/PiPedalSocket.cpp / src/PiPedalModel.hpp — monitorPort, hello,
    onPedalboardChanged, onSelectedSnapshotChanged message shapes.
  - vite/src/pipedal/PiPedalSocket.tsx — wire framing:
    [{message, replyTo?}, body?] for requests,
    [{reply, message}, body?] for replies,
    server-initiated pushes (onPedalboardChanged, onMonitorPortOutput) look
    like requests FROM the server and must be acked the same way.

Needs: pip install websockets
"""

import asyncio
import json

TUNER_URI = "http://two-play.com/plugins/toob-tuner"
FREQ_PORT_SYMBOL = "FREQ"


def find_tuner_instance_id(pedalboard: dict):
    """Recurse through items (and split-effect topChain/bottomChain) looking
    for a loaded TooB Tuner instance. Returns None if not found."""

    def walk(items):
        for item in items or []:
            if item.get("uri") == TUNER_URI:
                return item.get("instanceId")
            for key in ("topChain", "bottomChain"):
                sub = item.get(key)
                if isinstance(sub, dict):
                    found = walk(sub.get("items"))
                    if found is not None:
                        return found
        return None

    return walk(pedalboard.get("items"))


def current_snapshot_name(pedalboard: dict) -> str:
    """pedalboard.snapshots[pedalboard.selectedSnapshot].name, defensively."""
    snapshots = pedalboard.get("snapshots") or []
    idx = pedalboard.get("selectedSnapshot")
    if idx is None or not (0 <= idx < len(snapshots)):
        return ""
    snap = snapshots[idx]
    return (snap or {}).get("name", "") if snap else ""


GRID_SIZE = 6  # matches the 6 footswitches in a row


def build_snapshot_grid(pedalboard: dict):
    """Returns (names, highlight_index) for the 3x2 OLED grid in SNAPSHOT
    mode. names is always length 6 (blank-padded); highlight_index is
    0-5, or None if nothing's selected. Snapshots are already capped at 6
    by PiPedal itself, so there's no "beyond position 6" case here like
    there is for presets."""
    snapshots = (pedalboard.get("snapshots") or [])[:GRID_SIZE]
    names = [(s or {}).get("name", "") for s in snapshots]
    names += [""] * (GRID_SIZE - len(names))

    idx = pedalboard.get("selectedSnapshot")
    highlight = idx if idx is not None and 0 <= idx < len(snapshots) else None
    return names, highlight


def build_full_preset_list(presets_response: dict, max_count: int):
    """Returns (names, current_index) for the rotary-encoder Browse
    feature — NOT capped at 6 like build_preset_grid, capped at max_count
    instead (BrowseState.rotate's SysEx message has to fit in the Pico's
    MIDI input buffer). current_index is where the actually-loaded preset
    sits in this (possibly truncated) list, or None if it's not in the
    truncated portion at all (an extremely large bank) — BrowseState
    treats that the same as "unknown," starting the cursor at 0."""
    all_presets = presets_response.get("presets") or []
    shown = all_presets[:max_count]
    names = [p.get("name", "") for p in shown]

    selected_id = presets_response.get("selectedInstanceId")
    current_index = None
    for i, p in enumerate(shown):
        if p.get("instanceId") == selected_id:
            current_index = i
            break
    return names, current_index


def build_preset_grid(presets_response: dict):
    """Returns (names, highlight_index) for the 3x2 OLED grid in PRESET
    mode. Only the first 6 presets in bank order are shown -- that matches
    what the footswitches actually do (PC 0-5, hardcoded). If the active
    preset is beyond position 6 (reachable only via some other means, e.g.
    a future preset-browse feature), highlight_index is None -- none of
    the 6 shown cells is the active one, so nothing should be highlighted."""
    all_presets = presets_response.get("presets") or []
    shown = all_presets[:GRID_SIZE]
    names = [p.get("name", "") for p in shown]
    names += [""] * (GRID_SIZE - len(names))

    selected_id = presets_response.get("selectedInstanceId")
    highlight = None
    for i, p in enumerate(shown):
        if p.get("instanceId") == selected_id:
            highlight = i
            break
    return names, highlight


class PiPedalClient:
    """Thin wrapper around the websocket: request/reply matching, plus a
    callback for unsolicited server pushes (onPedalboardChanged,
    onSelectedSnapshotChanged, onMonitorPortOutput, ...).

    on_push(message_name: str, header: dict, body) is called for every
    message that isn't a reply to one of our own requests. If the push
    carries a replyTo, this class acks it automatically after on_push
    returns — callers don't need to know that server pushes are
    technically "requests" needing a reply.
    """

    def __init__(self, ws, on_push):
        self._ws = ws
        self._on_push = on_push
        self._next_code = 0
        self._pending = {}
        # Pushes are handed to a separate worker via this queue rather than
        # awaited inside the reader loop: on_push handlers call request()
        # themselves (e.g. getPresets after onPedalboardChanged), and that
        # reply can only be read by the reader loop — so awaiting on_push
        # there would deadlock. The single worker keeps pushes in order.
        self._push_queue = asyncio.Queue()
        # Start reading immediately, in the background — request() below
        # awaits a Future that only gets resolved by this loop, so it must
        # already be running before the first request() call, not started
        # later via run_forever(). Without this, request() deadlocks:
        # nothing is ever reading the reply that would resolve its Future.
        loop = asyncio.get_event_loop()
        self._reader_task = loop.create_task(self._reader_loop())
        self._push_task = loop.create_task(self._push_worker())

    async def request(self, message, body=None):
        self._next_code += 1
        code = self._next_code
        fut = asyncio.get_event_loop().create_future()
        self._pending[code] = fut
        header = {"message": message, "replyTo": code}
        payload = [header] if body is None else [header, body]
        await self._ws.send(json.dumps(payload))
        return await fut

    async def send(self, message, body=None):
        """Fire-and-forget — no reply expected (e.g. unmonitorPort)."""
        header = {"message": message}
        payload = [header] if body is None else [header, body]
        await self._ws.send(json.dumps(payload))

    async def run_forever(self):
        """Block until the background reader loop exits (e.g. connection
        closed or errored). The reader itself started in __init__, not here
        — this just keeps the caller alive and surfaces its exception."""
        await self._reader_task

    async def _reader_loop(self):
        async for raw in self._ws:
            msg = json.loads(raw)
            header = msg[0]
            body = msg[1] if len(msg) > 1 else None

            if "reply" in header:
                fut = self._pending.pop(header["reply"], None)
                if fut and not fut.done():
                    fut.set_result(body)
                continue

            message_name = header.get("message")
            if message_name == "error":
                raise RuntimeError(f"Server error: {body}")

            # Ack straight away — the server only needs to know it arrived;
            # handling happens in _push_worker so this loop never blocks.
            reply_to = header.get("replyTo", -1)
            if reply_to is not None and reply_to != -1:
                await self._ws.send(json.dumps(
                    [{"reply": reply_to, "message": message_name}, True]
                ))

            self._push_queue.put_nowait((message_name, header, body))

    async def _push_worker(self):
        while True:
            message_name, header, body = await self._push_queue.get()
            try:
                await self._on_push(message_name, header, body)
            except Exception as e:
                # One bad push shouldn't kill the whole relay.
                print(f"on_push({message_name}) failed: {e!r}")
