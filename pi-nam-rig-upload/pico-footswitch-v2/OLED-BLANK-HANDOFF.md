# OLED blank screen — session handoff (RESOLVED 2026-09-23)

**Resolved.** OLED, relay and encoder all work end-to-end. Current status and what's left now
live in `../pipedal-next-steps.md` §0. This file is kept as the record of how it was debugged.

## UPDATE (2026-09-23): OLED FIXED — root cause was SPI speed

- **Cause:** `FourWire`'s default 24 MHz SPI was too fast for the hand-wired leads; commands
  were silently corrupted (SPI has no ACK, so no error). Fixed with `baudrate=1000000` in
  `oled_display.init()`. Confirmed: boot splash ("OLED OK") now shows. Proven beforehand with a
  raw-SPI "entire display ON" (0xA5) test that the panel, power, wiring and SPI mode (board is
  set to SPI via the resistors, not IIC) were all fine.
- **Added diagnostics** (deployed to the Pico): `oled_display.show_splash()` for 2 s at boot (the
  normal empty grid is all-black, so a blank screen previously proved nothing); the onboard LED
  blinks 150 ms on every incoming SysEx with our manufacturer ID; serial prints for SysEx
  arrival and encoder turn/push.
- **Encoder:** rotation confirmed correct (1 step per detent, correct direction). Push switch
  missed presses because of a broken solder joint, found by the user and being resoldered.
- **TUNER/MUTE switch:** wiring confirmed working (sends CC26/27 127/0). What remains is only
  the per-preset PiPedal MUTE binding (see bottom).
- **Encoder push joint:** resoldered; push confirmed working on serial.
- **Relay: second deadlock found and fixed.** With the Pico on the Pi, names showed once and
  then went blank after the first switch press. `PiPedalClient._reader_loop` awaited
  `on_push` inline, and `on_pedalboard_changed` → `refresh_preset_data` calls `request()`,
  whose reply only that same loop can read — so the relay froze. Pushes now go through a queue
  to a separate `_push_worker` task (in order, with exceptions logged instead of killing the
  relay). Regression test added: `TestPushHandlerCanMakeRequests` in `test_pipedal_ws.py` — it
  times out against the old code and passes with the fix (15/15 tests pass, run on the Pi).
- **Relay: wrapped push bodies.** `onPedalboardChanged` arrives as `{clientId, pedalboard}` and
  `onPresetsChanged` as `{clientId, presets}` — unlike the plain `currentPedalboard` /
  `getPresets` replies. `pi_relay.on_push` unwraps both. Confirmed in the live log: correct
  names on every change, and `preset grid (pushed update)` now succeeds (was a `KeyError`).
- Deployed to the Pi; old copies in `~/pico-footswitch-v2/backup-before-push-fix/`.

(Original handoff below, kept for history.)

**Status as of this handoff:** footswitches fully working (presets/snapshots switch correctly).
Encoder wired and pin-identified but untestable (its browse feature only shows on the OLED).
TUNER/MUTE switch does nothing yet (separate, understood issue — see bottom). **OLED stays
blank** even after fixing a real bug in the relay chain — that's the open problem this doc is for.

## What's confirmed working (don't re-investigate these)

- **Wiring is not the problem, most likely.** OLED pins confirmed by label (CS/DC/RES/SDA/SCLK/
  VDD/VSS → GP18/GP17/GP16/GP15/GP14/3V3(OUT)/GND). Pico's serial console (via Mu, connected
  directly to a PC with the USB coupler unplugged from the Pi) shows `code.py` running with
  **zero errors or tracebacks** — the SSD1306-driver-against-SSD1309-panel init call
  (`oled_display.py` `init()`) completes without raising. This doesn't *prove* the physical panel
  responds correctly (SPI has no ACK — a driver can "succeed" talking to nothing), but it does
  rule out a Python crash or a fatally wrong pin.
- **`pi_relay.py` had a real, now-fixed deadlock bug**, unrelated to wiring. In `pipedal_ws.py`,
  `PiPedalClient.request()` sends a request and awaits a `Future` that's only ever resolved inside
  `run_forever()`'s read loop — but `run_forever()` wasn't called until *after* the initial
  `hello`/`currentPedalboard` handshake requests, which used `request()`. Classic deadlock: nothing
  was ever reading the reply that would unblock it. **Fixed** by starting the read loop
  (`_reader_loop`, renamed from the old `run_forever` body) as a background task in
  `PiPedalClient.__init__` instead of waiting for an explicit `run_forever()` call. This fix is
  already applied to the local repo copy of `pipedal_ws.py` **and deployed to the Pi**
  (`~/pico-footswitch-v2/pipedal_ws.py`).
- **After that fix, `pi_relay.py` genuinely works**: connects to PiPedal's websocket, logs real
  data — `Connected. clientId=N`, `snapshot grid -> ['Clean', 'Drive', 'Solo', 'Dry', 'Wash', '']`,
  `preset grid -> ['1 Clean', '2 Ambient', ...]`, `Subscribed to FREQ on tuner instance 101`. This
  is real, live PiPedal data, not a hardcoded stub — confirms the whole websocket/PiPedal-API side
  of the chain is fine.
- **`self.midi_out.send(...)` genuinely gets called** right before each of those log lines (checked
  the source directly, not assumed) — so real MIDI SysEx send calls are happening in Python.
- **`pipedal-tuner-relay.service` is installed correctly** on the Pi (`/etc/systemd/system/`,
  enabled, `Environment=PYTHONUNBUFFERED=1` added so its `print()` output actually reaches
  `journalctl` — without that, systemd's default stdout buffering hid all output, which is what
  cost most of this session before finding the real deadlock bug).

## What's NOT yet confirmed — this is the actual open question

**Whether the SysEx bytes `pi_relay.py` sends actually arrive at the Pico's `midi.receive()` at
all.** Tried to verify with `aseqdump -p 32:0` (the Pico's ALSA client:port) — it never showed our
outgoing test sends, **but this is very likely a testing-methodology dead end, not real evidence of
failure**: `aseqdump -p X` appears to only display traffic *originating from* port X (confirmed it
happily showed the Pico's own outgoing switch-press messages), not traffic being *delivered to* X.
Don't trust this tool for this direction — a different verification method is needed (see below).

`code.py`'s receiving side (`poll_midi_in()`, ~line 164) was read and looks logically correct:
checks `isinstance(msg, SystemExclusive)`, matches `manufacturer_id == bytes([SYSEX_MANUFACTURER_ID])`
(`0x7D`), reads subtype/highlight/names, calls `refresh_display()`. It **is** called every iteration
of the main `while True:` loop (confirmed at line 294). Nothing found wrong here on inspection —
but it's never been empirically confirmed to actually fire on a real incoming message.

## Why this is hard to test further: a real Catch-22

The Pico's single USB connection carries **both** the MIDI interface (used for the live PiPedal
connection) **and** the serial/REPL console (used for debugging). It can only be plugged into one
host at a time — the Pi (for real MIDI traffic) or a PC (for serial debugging) — never both at
once. So you can't watch `code.py`'s live behavior via serial *while* it's actually receiving real
relay traffic from the Pi. Any further diagnosis needs to work around this.

## Suggested next steps, in order of effort

1. **Cheapest: add a visible on-Pico indicator that needs no serial console.** The Pico has an
   onboard LED. Add a couple of lines to `poll_midi_in()` in `code.py` — toggle/blink the onboard
   LED the instant a `SystemExclusive` message matching `SYSEX_MANUFACTURER_ID` is received,
   *before* any of the existing subtype logic. Reflash, plug into the Pi as normal, and just watch
   the Pico's own onboard LED (not the OLED) for activity when the relay restarts or a preset
   changes. If it blinks: messages are arriving, so the bug is somewhere in `refresh_display()` /
   `oled_display.show_grid()` / the actual panel hardware. If it never blinks: the bug is earlier —
   either the message never leaves the Pi correctly, or `midi.receive()` isn't seeing it (check
   `usb_midi.ports` setup in `code.py`, and whether `midi` there is reading the same USB MIDI
   `PortIn` the Pi is actually addressing).
2. **If the LED confirms messages ARE arriving but the screen still doesn't update:** the bug is in
   the display path, not the MIDI path. Check `oled_display.show_grid()` and `refresh_display()`
   for a display-group bug (e.g., `_display.root_group` never actually getting reassigned after
   `init()`'s first assignment, a labels-not-updating issue, or genuinely the flagged
   SSD1306-driver-vs-SSD1309-panel incompatibility from `oled_display.py`'s own top-of-file
   comment — that's the next thing to suspect once MIDI delivery itself is confirmed working).
3. **A better MIDI-arrival verification tool than `aseqdump`**, if you want to confirm at the
   Pi/ALSA level instead of adding Pico-side instrumentation: try `amidi -p hw:<card>,0 -d` (dump
   raw incoming bytes on the *rawmidi* character device directly, not the sequencer layer) while
   sending a test SysEx from another terminal — this project's own earlier session notes
   (`presets-reference/pipedal-session-handoff.md` §6.19/§6.27) already found `amidi` more reliable
   than higher-level tools for exactly this kind of "did it really arrive" question. Find the
   Pico's card number via `cat /proc/asound/cards`.
4. **Once OLED is confirmed working:** the encoder becomes testable (its whole browse feature
   displays on the OLED — untestable until this is fixed). Retest it then.

## Separate, understood, not-yet-fixed issue: TUNER/MUTE does nothing

Per `pipedal-hardware-v2.md`, the mute toggle needs a **per-preset** MIDI binding on TooB Tuner's
`MUTE` port ("Toggle on any value"), created individually in **all 6 presets** — there's no global
version. This almost certainly hasn't been set up yet in PiPedal's UI (Settings → System MIDI
Bindings, per-plugin binding on the Tuner instance, not the general system bindings page). Not
related to the OLED problem — separate fix, just a PiPedal UI configuration step, not code.

## Environment notes for whoever picks this up

- Pi currently reachable via **Ethernet** at `192.168.20.32` (hostname `pipedal`) — WiFi setup on
  the new network was never resolved (password kept failing the 4-way handshake on both 2.4G and
  5G bands identically; suspected wrong password or a router PMF/802.11w setting, not pursued
  further, abandoned in favor of Ethernet). This IP will change if Ethernet is unplugged or DHCP
  reassigns — re-check the router's connected-devices list if `ssh jesse@192.168.20.32` stops
  working.
- `sudo` needs a password interactively — can't be run non-interactively over SSH from an
  assistant/script without it. Some `sudo -n` calls worked later in this session without a fresh
  password prompt (likely a cached sudo timestamp from the user's own terminal), but don't rely on
  that being available in a fresh session.
- Files changed this session, all already deployed to both the local repo and the Pi:
  `pico-footswitch-v2/pipedal_ws.py` (the deadlock fix — `_reader_loop` started in `__init__`).
- `pipedal-tuner-relay.service` is installed and enabled on the Pi. To see its live output:
  `journalctl -u pipedal-tuner-relay -f` (with `PYTHONUNBUFFERED=1` now set, output appears in
  real time, unlike before).
