#!/usr/bin/env python3
"""Drive PiPedal over its websocket and measure DSP load + xruns per preset
and per snapshot.

Exists because the only other way to load a preset is to tap the UI, and
answering "does Ambient or Loathe still crackle?" means visiting 6 presets and
24 snapshots while watching the journal. Read-only as far as the preset files
go -- it selects things, it never edits them.

Protocol, from vite/src/pipedal/PiPedalSocket.tsx:
    ws://<host>:80/pipedal, text frames carrying
    [{"message": "<name>"}, <arg>]
so "load preset 3" is  [{"message":"loadPreset"},3]  and "snapshot 2" is
[{"message":"setSnapshot"},1].

No websocket library on the Pi, hence the hand-rolled framing below. Client
frames must be masked; server frames are not.

    python3 pipedal-probe.py                  # sweep presets and snapshots
    python3 pipedal-probe.py --presets-only
    python3 pipedal-probe.py --dwell 8        # longer settle+measure window
"""

import argparse
import base64
import glob
import json
import os
import re
import socket
import struct
import subprocess
import sys
import time

BANK = "/var/pipedal/presets/Default+Bank.bank"


# ---- minimal websocket client ----------------------------------------

class WebSocket:
    def __init__(self, host, port=80, path="/pipedal", timeout=10):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            "GET %s HTTP/1.1\r\n"
            "Host: %s:%d\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: %s\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n" % (path, host, port, key)
        )
        self.sock.sendall(req.encode())
        self.buf = b""
        while b"\r\n\r\n" not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise IOError("handshake closed early")
            self.buf += chunk
        head, self.buf = self.buf.split(b"\r\n\r\n", 1)
        if b"101" not in head.split(b"\r\n")[0]:
            raise IOError("upgrade refused: %r" % head.split(b"\r\n")[0])

    def send(self, message, arg=None):
        payload = json.dumps([{"message": message}] +
                             ([arg] if arg is not None else [])).encode()
        header = bytearray([0x81])
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        mask = os.urandom(4)
        header += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def _recv_exact(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise IOError("closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def drain(self, seconds):
        """Read and discard whatever the server pushes for a while.

        PiPedal streams VU and monitor updates constantly; if nobody reads
        them the socket buffer fills and the server blocks, which would skew
        exactly the measurement being taken.
        """
        end = time.time() + seconds
        self.sock.settimeout(0.25)
        try:
            while time.time() < end:
                try:
                    b0b1 = self._recv_exact(2)
                except (socket.timeout, IOError):
                    continue
                length = b0b1[1] & 0x7F
                if length == 126:
                    length = struct.unpack(">H", self._recv_exact(2))[0]
                elif length == 127:
                    length = struct.unpack(">Q", self._recv_exact(8))[0]
                if b0b1[1] & 0x80:
                    self._recv_exact(4)
                if length:
                    self._recv_exact(length)
        finally:
            self.sock.settimeout(10)

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


# ---- measurement -----------------------------------------------------

def audio_threads():
    """tid -> (name, utime+stime) for the realtime audio threads."""
    out = {}
    for path in glob.glob("/proc/*/task/*/stat"):
        try:
            raw = open(path).read()
        except Exception:
            continue
        name = raw[raw.find("(") + 1:raw.rfind(")")]
        if not (name.startswith("ppdl_alsaDriver")
                or name.startswith("ppdl_lv2_worker")
                or name.startswith("ppdl_rtsvc")):
            continue
        fields = raw[raw.rfind(")") + 2:].split()
        out[path] = (name, int(fields[11]) + int(fields[12]))
    return out


HZ = os.sysconf("SC_CLK_TCK")


def xrun_count():
    try:
        out = subprocess.run(
            ["journalctl", "-u", "pipedald", "-b", "--no-pager"],
            capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return None
    return len(re.findall(r"(?i)underrun|xrun", out))


def measure(ws, dwell):
    """DSP load over `dwell` seconds, plus the xrun delta across it."""
    x0 = xrun_count()
    before = audio_threads()
    t0 = time.time()
    ws.drain(dwell)
    elapsed = time.time() - t0
    after = audio_threads()
    x1 = xrun_count()

    total = 0.0
    for key, (name, ticks) in after.items():
        if key in before:
            total += (ticks - before[key][1]) / HZ / elapsed * 100
    delta = None if (x0 is None or x1 is None) else x1 - x0
    return total, delta


def temp():
    try:
        return int(open("/sys/class/thermal/thermal_zone0/temp").read()) / 1000.0
    except Exception:
        return float("nan")


# ---- main ------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--dwell", type=float, default=5.0,
                    help="seconds to measure at each stop (default 5)")
    ap.add_argument("--settle", type=float, default=2.0,
                    help="seconds to ignore after a switch (default 2)")
    ap.add_argument("--presets-only", action="store_true")
    args = ap.parse_args()

    bank = json.load(open(BANK))
    presets = [(e["instanceId"], e["preset"]["name"],
                [s["name"] if s else None
                 for s in (e["preset"].get("snapshots") or [])])
               for e in bank["presets"]]
    original = bank.get("selectedPreset", presets[0][0])

    ws = WebSocket(args.host)
    ws.drain(1.0)

    print("dwell=%.0fs settle=%.0fs   temp at start %.1f C\n"
          % (args.dwell, args.settle, temp()))
    print("%-14s %-17s %7s  %6s" % ("preset", "snapshot", "DSP%", "xruns"))
    print("-" * 50)

    worst = []
    for instance_id, name, snaps in presets:
        ws.send("loadPreset", instance_id)
        ws.drain(args.settle)
        load, xruns = measure(ws, args.dwell)
        flag = "  <-- xruns!" if xruns else ""
        print("%-14s %-17s %6.1f%%  %6s%s"
              % (name, "(as loaded)", load,
                 "-" if xruns is None else xruns, flag))
        worst.append((load, name, "(as loaded)"))

        if args.presets_only:
            continue
        for index, snap_name in enumerate(snaps):
            if not snap_name:
                continue
            ws.send("setSnapshot", index)
            ws.drain(args.settle)
            load, xruns = measure(ws, args.dwell)
            flag = "  <-- xruns!" if xruns else ""
            print("%-14s %-17s %6.1f%%  %6s%s"
                  % ("", snap_name, load,
                     "-" if xruns is None else xruns, flag))
            worst.append((load, name, snap_name))
        # leave each preset on its home snapshot
        ws.send("setSnapshot", 0)
        ws.drain(0.5)

    # put the rig back where it was found
    ws.send("loadPreset", original)
    ws.drain(1.0)
    ws.close()

    worst.sort(reverse=True)
    print("\nheaviest:")
    for load, name, snap in worst[:5]:
        print("  %6.1f%%  %s / %s" % (load, name, snap))
    print("\ntemp at end %.1f C" % temp())
    print("restored selectedPreset=%s" % original)


if __name__ == "__main__":
    main()
