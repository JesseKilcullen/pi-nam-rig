# Phase 2 — Build the structure

From "one preset proved the concept" to **a rig you could take to rehearsal**: heatsink on,
**Shipped as 6 presets × 4 snapshots** (this doc still says 3×3 in places — see §13). Levels **not** matched yet; not backed up yet. Current state: [`pipedal-session-handoff.md`](./pipedal-session-handoff.md).
Full detail: [`pipedal-nam-rig-plan.md`](./pipedal-nam-rig-plan.md) ·
Data model: [`pipedal-data-model.md`](./pipedal-data-model.md) ·
Previous step: [`pipedal-today.md`](./pipedal-today.md)

**No code, no soldering, nothing to buy but a $3.95 heatsink.** The Pico and footswitches are
Phase 3 — everything here is driven from your phone and one SSH window.

---

## 0. Before you start

**Phase 1 is finished.** Results, 2026-09-04:

| From Phase 1 | Yours |
|---|---|
| Snapshot NAM model swap — clean or glitch? | **Clean / seamless** |
| Design chosen | **Design A — one NAM instance, capture swapped per snapshot.** Build as this doc was originally written |
| Buffer size that ran clean | **64 × 3 @ 48 kHz** (staying here; latency feels fine) |
| DSP load, **1 NAM** + tuner + gate + cab sim + delay | **~27–28%** of one core, peak 36% |
| Temp under load / `get_throttled` | **50.1 °C** / **`0x0`** |

Built as preset `New`: `[tuner] → [gate] → [NAM] → [cab-sim] → [delay]`, with three snapshots
differing only in `pathProperties → toob-nam#modelFile`:

| Snapshot | Capture |
|---|---|
| Clean | `1960 Fender Tweed Deluxe 5E3 - Clean.nam` |
| Crunch | `1960 Fender Tweed Deluxe 5E3 - Crunch.nam` |
| Gain | `[AMP] MESA.MKVII-90W-CH3-MKIIB Pony Rawness - BLEND #3.nam` |

**So §5 below is correct as written and §5b is unused.** Design B — three instances toggling
bypass — was never built and isn't needed. Note the 27% figure is **one** instance, so don't treat
it as evidence that three would fit.

**Steps 1–3 are already done** (see the markers on each). Start at **§4**.

### On the bench

- Pi 4, powered down, and its 3A USB-C supply
- **Altronics H0608 heatsink** (5 mm — the one that still clears a HAT in Phase 4)
- Isopropyl alcohol + a lint-free cloth (or an alcohol prep wipe)
- UMC204HD, 2 × 1/4" cables, guitar, Blackstar HT Stage 60 — wired as in `pipedal-today.md` §6
- Phone (PiPedal UI) and laptop (one SSH window)

**Still don't need:** monitor, keyboard, micro-HDMI, WSL.

Budget ~2 hours. Steps 4–6 are the slow part — that's you listening, not the Pi working.

---

## 1. Fit the heatsink — ✅ DONE 2026-09-04

> **Done.** H0608 fitted 2026-09-04, *before* the Phase 1 measurements. Nothing below needs doing.

**Using:** Pi 4 · H0608 · isopropyl · laptop (SSH, to shut down cleanly)
**This is the only step where the Pi is off.**

Shut down properly. The quickest route is your **phone** — PiPedal's Settings dialog has
shutdown/restart menu items, so you never need a terminal for this. From the SSH window you
already have open, it's:

```bash
sudo shutdown -h now
```

Wait for the **green** LED to stop flickering and go dark, then unplug the USB-C.
(§11 covers what actually happens if you yank the power, and how to make that safe.)

1. Unplug the interface USB cable too, so nothing is dangling while you press on the board.
2. Wipe the top of the big square chip in the middle of the board (the SoC, marked `BCM2711`)
   with isopropyl. Let it dry — 30 seconds.
3. Peel the backing off the heatsink's thermal pad. **Don't touch the exposed adhesive.**
4. Sit it square on the SoC and press firmly for ~30 seconds. The pad is the thermal path; a
   corner not making contact is worse than it looks.
5. If your kit came with the two small sinks, they go on the RAM chip (next to the SoC) and the
   **VL805 USB controller** (small chip near the USB ports). Both optional; the VL805 one is
   the more useful of the two since your interface hangs off it.

> **Get the placement right before you press.** The pad is single-use adhesive, so it won't
> reposition cleanly — but it *does* come off if you want it off later. Twist the sink gently
> sideways (never pry it straight up, that's how you lift a chip), or warm it with a hairdryer
> first, then clean the residue with isopropyl. Two-minute job. Don't cover the two black
> rectangles at the board edge — that's the wifi/Bluetooth antenna.

> **If you later want active cooling**, the H0608 is not in your way — but a fan probably isn't
> the answer either. On a Pi 4, passive plus open air is the quiet option, and a fan next to a
> guitar rig is a noise source you have to live with. If §2's temps throttle, try **airflow over
> the bare board** (any 5 V fan pointed at it) before buying a cooler. Note that GPIO-powered
> fans and fan-in-case solutions fight the Pisound HAT for the 40-pin header in Phase 4 — that
> conflict, not the adhesive, is the thing to plan around.

Reconnect the interface, then power, and wait 90 seconds.

---

## 2. Re-baseline thermals — ✅ NOT NEEDED (this section's premise is wrong)

> **Skip this.** The heading claims Phase 1's numbers are stale because the heatsink went on
> afterwards. It didn't — the heatsink was fitted **before** those measurements, so **50.1 °C** and
> `get_throttled` `0x0` already include it. No re-baseline required.
>
> One thing here is still worth doing, though: Phase 1 was bursty playing, not sustained. When you
> do §6's level-matching pass you'll be playing for a solid stretch anyway — check the temp at the
> end of it and you get the 10-minute soak for free.

**Using:** laptop (SSH) · phone (PiPedal UI) · guitar · amp

```bash
./pipedal-setup.sh check       # sanity: aarch64, services up, interface seen
./pipedal-setup.sh monitor     # live temp + throttle state
```

Read **idle** temp first. Then load it up: play through 1 NAM instance for 10 minutes straight
and read it again.

| | Result |
|---|---|
| Idle temp, heatsink fitted | |
| Temp after 10 min playing | |
| `get_throttled` | |

**`get_throttled` must be `0x0`.** Anything else and every CPU number you take today is fiction —
`0x1` / `0x10000` bits mean under-voltage (suspect the PSU or the bus-powered interface, not
PiPedal), temperature bits mean airflow.

Target: comfortably under 70 °C playing. Bare board in open air, not in a drawer.

---

## 3. Go headless — ✅ DONE (confirmed `multi-user.target`)

> **Done.** `systemctl get-default` returns `multi-user.target`, and `./pipedal-setup.sh check`
> reports `console — good, no GPU contention`. Nothing to run.

**Using:** laptop (SSH)

Pi OS **Lite** has no desktop, so you're mostly there already — this just pins the boot target so
nothing ever grabs the GPU. The docs put the difference at ~15 ms vs sub-5 ms.

```bash
sudo ./pipedal-setup.sh headless
systemctl get-default        # want: multi-user.target
```

If it already says `multi-user.target`, you're done — skip the reboot.

---

## 4. Choose and prepare 9 captures

**Using:** phone (PiPedal UI, logged into TONE3000)

*Shipped as six presets × four snapshots, and the captures stayed full-amp-with-cab because the rig is on headphones — preamp-only/DI is now a Blackstar-FX-return concern. The rules below still hold; the arithmetic doesn't.*

Three presets × three snapshots = **9 captures**. Rules, all from the plan:

- **Preamp-only.** Your EL34s are the power amp — full-amp captures stack two of them (§2.1).
- **No cab.** Your Celestions are the cab. Pick "no cab" captures rather than switching cab sim
  off after the fact — it saves the IR convolution too.
- **A2 Full.** Measured DSP load is ~27% with three instances, so Full is affordable and Lite is not required — despite §6 of the plan calling Lite "not negotiable" for Design B. That was an A1-era estimate.
- Group them so each preset is one *amp family*, and the three snapshots inside it are that amp's
  clean / crunch / lead. That way a bank change is a change of amp, not a change of song.

A workable starting set:

| Preset | Amp family | Snapshot 1 | Snapshot 2 | Snapshot 3 |
|---|---|---|---|---|
| 1 "Clean" | Fender-ish | clean | edge-of-breakup | + drive/delay |
| 2 "Crunch" | AC30 / Vox-ish | clean-ish | crunch | + drive |
| 3 "Lead" | Marshall-ish | rhythm | high gain | + drive/delay |

**Level-match each capture by ear — not with NAM Calibration.** I had this wrong in an earlier
draft. NAM Calibration is not a per-capture routine and mostly won't be available to you:

- It's **one voltmeter measurement of your guitar's output** in dBU, entered once — not something
  you run per capture.
- It only works if the `.nam` file carries **calibration metadata from the model author**, and
  TONE3000 captures are, in PiPedal's own words, "mostly (with rare exceptions) not calibrated."
  For those, the Input Calibration control is **greyed out**.
- The doc is blunt about it: *"There is no requirement to perform this calibration step."*

What to do instead, per capture, and it *is* the highest-value work in Phase 2:

1. Set the **interface** input gain once, so your hardest strum peaks near 0 dBFS. Then leave it.
2. Per capture, set the plugin's **Input Gain** so the model breaks up where you want it to — this
   is the "am I hitting the front of the amp hard or soft" control.
3. Per capture, set **Output Gain** for loudness matching (§6 does this pass properly).

> If a capture *does* come with calibration metadata, use it — it's a convenient starting point,
> not a requirement. Nothing else in this doc depends on it.

---

## 5. Build Preset 1 as the template

**Using:** phone (PiPedal UI) · guitar · amp

Build the **full** chain now, even where a snapshot leaves half of it bypassed. A snapshot can
flip pedals on and off and turn any knob, but it **cannot add, remove or re-order a plugin** —
whatever the preset doesn't contain, no snapshot can reach.

```
[TooB Tuner] → [Gate] → [Drive] → [TooB NAM] → [Cab IR] → [Delay] → [Reverb] → [Gain]
                            ▲          ▲            ▲                            ▲
                    before the model:  capture      bypassed into the        level match
                    a pedal into an    swaps per    amp's FX return,         per snapshot
                    amp                snapshot     ON for headphones
                                       (Design A —
                                       verified seamless)
```

> **One NAM instance.** The capture is swapped by changing `pathProperties → modelFile` per
> snapshot. Phase 1 confirmed that's seamless on this rig, which is why you don't need three
> instances and don't pay 3× the NAM CPU.

> **Drive placement.** §5 of the plan draws it *after* the NAM; put it **before**. A dirt pedal
> in front of an amp is what your ears expect.

> **Free future-proofing: keep all mono blocks before all stereo ones.** TooB Delay and TooB
> Volume are mono (1→1), and a mono plugin placed after a stereo one silently discards the right
> channel. Costs nothing today, and it's the only decision that would otherwise force a rebuild if
> you ever go stereo. (`pipedal-stereo.md` is referenced here but does not exist in Downloads.)

Then, per snapshot: set every knob, hit the **snapshot button (camera icon)**, save to a slot.

| | Snapshot 1 | Snapshot 2 | Snapshot 3 |
|---|---|---|---|
| Tuner | off | off | off |
| Gate | on | on | on (harder) |
| Drive | **off** | **off** | **on** |
| **NAM capture** | **clean** | **breakup** | **lead** |
| Cab IR | on for headphones / **off** into the amp | ← same | ← same |
| Delay | off | off | on |
| Reverb | on, low | on, low | on |
| Gain | reference | matched | matched |

⚠️ **Cab IR bypass is stored per snapshot**, like every other bypass. Switching from headphones to
the amp means turning it off in **all three** snapshots and re-saving each one — there's no global
toggle. Easy to set two and forget the third, then wonder why one sound is muddy.

**Max 6 snapshots per preset**, so three leaves you headroom to add a "quiet verse" later.

### 5b. Escape hatch — NOT needed, kept for reference only

> **You don't need this.** It was the fallback for "Design B won't fit on a Pi 4" — but three
> instances run at ~27%, so real Design B is available and sounds like three amps rather than one
> amp with pedals. Keep this only if you later want a *fourth* tone without a fourth instance.

If Phase 1 glitched, the NAM row stops moving and the pedals in front do the work:

| | Snapshot 1 | Snapshot 2 | Snapshot 3 |
|---|---|---|---|
| NAM capture | **one capture, never changes** | ← same | ← same |
| Drive | off | on, low gain | on, high gain + level |
| EQ / boost | flat | flat | mids up |

Pick the capture that takes a boost well — an edge-of-breakup capture, not a fully clean one and
not a saturated one. This is how a real one-channel amp rig works, and it costs ~1/3 the CPU.

---

## 6. Match the levels (don't skip this either)

**Using:** guitar · amp at rehearsal volume · phone

Step 4's Input Gain set how hard you hit the model. It did nothing about the fact that a clean capture and a
high-gain capture, at the same knob settings, are wildly different loudnesses.

1. Pick **preset 1 / snapshot 2** as your reference and set the amp for it.
2. Play the same 4-bar riff through every one of the 9 snapshots in turn.
3. Adjust each snapshot's **output Gain** until they sit at the same perceived loudness — the lead
   sounds fuller, not louder. Re-save each snapshot after you adjust it.
4. Leave the interface output knob and the amp alone for the whole pass. One variable at a time.

Do this at something near playing volume. Levels matched at bedroom volume don't hold up at
rehearsal volume.

---

## 7. Measure the real thing

**Using:** phone (CPU meter) · laptop (`./pipedal-setup.sh monitor`)

Phase 1 measured a bare NAM. This is the full chain, which is what you'll actually run.

| | Result |
|---|---|
| CPU — full chain, snapshot 1 | |
| CPU — full chain, snapshot 3 (drive + delay + reverb on) | |
| Buffer size that runs clean | |
| Temp after 10 min at snapshot 3 | |
| xruns in `journalctl -u pipedald -f` over 10 min | |

Headroom rule: if the busiest snapshot sits above **~70% CPU**, back off before Phase 3. In order
of what to try:

1. **Turn on TooB NAM's `Threaded` button** — it moves the NAM computation to its own thread, which
   is the single biggest lever you have on a Pi 4. Cost: one extra audio buffer of latency. Added
   in 1.4.87, and it's the reason a 2-NAM blend is even worth testing (see `pipedal-tone-plan.md`).
2. Drop the reverb, or the delay's tail length.
3. Raise the buffer size — latency you can feel, but xruns you can *hear*.

A rig that xruns once a set is worse than one that's slightly less pretty.

> **A2 "Lite vs Full" may be a control, not a download.** Captures on the Pi report
> `"architecture":"SlimmableContainer"` — a single slimmable file wrapping WaveNet submodels
> selected by `max_value`. And TooB NAM exposes a **`modelSize`** control (currently `0` in every
> snapshot), which is very likely the selector for which submodel runs. So §6's "drop to Lite"
> might be a knob rather than a re-download. **Untested** — and irrelevant at ~27% load with one
> instance. `Threaded` remains the bigger CPU lever if you ever need one.

If it crackles, walk the buffers up in this order: `64×3` → `64×4` → `128×3`.

---

## 8. Duplicate for presets 2 and 3

**Using:** phone (PiPedal UI)

Copy preset 1 rather than building from scratch — identical graphs across all three presets is
what makes Phase 3's footswitch bindings behave predictably.

1. Duplicate preset 1 → rename → swap the three NAM captures → recalibrate → re-match levels.
2. Repeat for preset 3.
3. Put all three in one bank, **ordered the way you'd switch on stage.** Bank changes rebuild the
   plugin graph, so there *is* an audible gap — that's expected and fine between songs, not
   mid-song.

Sanity check when you're done: switch between all three presets, then all nine snapshots, and
confirm each one is loading the capture you think it is. Silent mis-recall is the failure mode
here, and it's much cheaper to catch now than to discover with a footswitch under your boot.

---

### 8b. Can presets be built by script instead of the UI?

**Partly — and §8 is exactly where it's worth it.** Verified on the Pi 2026-09-04.

**There is no documented API for authoring presets.** `pipedalconfig` is service and system
config only — install, start/stop, port, hotspot. Nothing about presets. The React client drives
an undocumented WebSocket JSON protocol, which is real but reverse-engineering it isn't worth the
effort here.

**What works: the on-disk bank files are plain JSON.**

```
/var/pipedal/presets/index.banks          # bank list, selectedBank
/var/pipedal/presets/<Bank+Name>.bank     # everything else
```

Structure, confirmed by reading the live files:

```
bank
 └─ presets[]
     └─ preset { name, input_volume_db, output_volume_db, selectedSnapshot,
                 items[], snapshots[] }
         ├─ items[]      = the plugin chain, in order
         │    { instanceId, uri, isEnabled, controlValues[{key,value}], pathProperties{} }
         └─ snapshots[]  = 6 slots (null = empty)
              { name, color, isModified, values[] }
                 └─ values[] = per instanceId: isEnabled, controlValues, lv2State, pathProperties
```

`snapshots[].values[]` maps 1:1 onto the `SnapshotValue` struct in §5 of the plan — so everything
a snapshot can hold is right there and writable.

The NAM capture is a **JSON string nested inside** a `pathProperties` value:

```json
"pathProperties": {
  "http://two-play.com/plugins/toob-nam#modelFile":
    "{\"otype_\": \"Path\",\"value\": \"NeuralAmpModels/Factory Models/....nam\"}"
}
```

Double-encoded, so you parse the outer object, then parse that string, edit `value`, and
re-serialise.

> ### ⚠️ THE TRAP: `pathProperties` is only a cached copy
>
> Setting `pathProperties` alone **does not select the file.** Verified the hard
> way on 2026-09-04: six presets built with correct, existing paths in
> `pathProperties`, and every file selector in the UI came up empty with no model
> loaded.
>
> The state PiPedal actually restores into a plugin lives in **`lv2State`**:
>
> ```json
> "lv2State": [true, {
>   "http://two-play.com/plugins/toob-nam#modelFile": {
>     "flags": 3,
>     "atomType": "http://lv2plug.in/ns/ext/atom#Path",
>     "value": "NeuralAmpModels/Factory Models/Kraken_Gain-I_G7.nam"
>   }
> }]
> ```
>
> `[false, {}]` means no state — which is what an item built from scratch gets by
> default, and why nothing loads. **Write both fields, derived from one source**,
> so they can't drift apart.
>
> Three details that are easy to get wrong:
>
> - **Empty slots use `atom#String`, not `atom#Path`.** The Cab IR's unused
>   `impulseFile2` / `impulseFile3` are `String` with `value: ""`.
> - **The convolution reverb's key is `toob-impulse#impulseFile`** — not its own
>   plugin URI. Don't assume the property namespace matches the plugin.
> - `stateUpdateCount` is 0 on a stateless item; set it to 1+ when you add state.
>
> **Verify the right field.** Reading back `pathProperties` after writing it
> proves nothing — it just agrees with itself. Check `lv2State[0]` is `true` and
> that `lv2State[1][key]["value"]` matches, then confirm the file exists on disk.
>
> Working implementation: `build-kraken-presets.py` (`item()` / `lv2_state()`).

> ⚠️ **Stop `pipedald` before editing, or your changes vanish.** It holds this state in memory and
> rewrites the files on any change, so a live edit gets clobbered on the next UI action.
>
> ```bash
> sudo systemctl stop pipedald
> sudo cp /var/pipedal/presets/Default+Bank.bank ~/bank-backup.json   # always
> #   ... edit ...
> sudo systemctl start pipedald
> ```
>
> Files are owned by `pipedal_d:pipedal_d` — preserve ownership and mode, or PiPedal can't write
> them afterwards. `python3` is already on the Pi; there's none on the Windows laptop.

**Where scripting actually earns its keep — and where it doesn't:**

| Task | Best done |
|---|---|
| Building preset 1's chain | **UI.** One-off, and you need to hear it |
| Setting Input/Output Gain by ear (§4, §6) | **UI.** Not automatable — it's a listening job |
| Duplicating preset 1 → 2 and 3 with three new capture paths | **Script.** Pure mechanical path substitution |
| The 9-snapshot bypass matrix (exactly one NAM on) | **Script.** Nine near-identical edits is where hand-editing makes mistakes |
| Verifying every snapshot points at the capture you think | **Script.** One pass over the JSON beats tapping through 9 snapshots |

That last one is worth doing regardless of how you build them — §8's "silent mis-recall" is the
failure mode here, and a script reads the truth off disk instead of trusting the UI.

---

## 9. Settle the Phase 3 mapping question

**Using:** laptop (SSH) · phone (PiPedal UI). *No Pico yet.*

~~The one unresolved question in the plan~~ **— SETTLED, see the box below.** Does PiPedal offer **"go to snapshot N"**, or only
next/previous? The answer decides the footswitch layout, so resolve it now — the Pico firmware
gets written in Phase 3 either way, but only if you know which layout it's driving.

Open **Settings → System MIDI Bindings** on your phone and read the action list.

> ### SETTLED - no UI trip needed
>
> **Direct snapshot-N bindings exist.** The earlier "go in expecting the fallback" advice was
> **wrong**, and so was the reasoning behind it: the release notes *do* mention this, in 1.3.53 -
> *"New System Midi Bindings for snapshot selection, and for previous and next bank"* - which was
> missed because only the later 1.5.95 Next/Previous Snapshot note was found. The "one agent
> report" was right.
>
> Confirmed in source (`rerdavies/pipedal` @ main), so it did not need the Pi:
> `src/Storage.cpp` builds the canonical binding list, `src/AudioHost.cpp` dispatches each
> symbol, and `vite/src/pipedal/SystemMidiBindingsDialog.tsx` maps symbols to UI labels.
>
> **Use the primary layout.** The steps below are now optional verification only.

```bash
sudo ./pipedal-setup.sh midi      # virtual MIDI ports, no hardware needed
./pipedal-setup.sh miditest       # fires test messages
```

Bind CC 20/21/22 and try them:

| Outcome | Phase 3 layout |
|---|---|
| Direct "select snapshot N" exists | `[snap 1] [snap 2] [snap 3] [bank−] [bank+] [tune/mute]` — the plan's §10 map |
| Only next/prev snapshot | `[snap−] [snap+] [tap/mute] [bank−] [bank+]` — the §10 fallback |

Write down which one, and the CC numbers that worked. That's the input to `code.py`.

---

## 10. Hotspot, once, at home

**Using:** phone · laptop (SSH)

Set it up now while you can still recover the Pi if it locks you out.

Settings → **Auto-Hotspot configuration** → temporarily choose **Always on** → reboot → connect
your phone to the Pi's SSID → confirm the UI loads (fall back to `http://172.23.0.2`) → then set
it to **"No remembered Wi-Fi connections"** and reboot again.

Command-line fallback if the dialog misbehaves: `pipedalconfig --help`.

---

## 11. Powering off without killing the SD card

**Using:** phone (PiPedal UI) · laptop (SSH, only if it's already open)

**No, you don't need to SSH in every time.** PiPedal's web UI has shutdown and restart in its
Settings dialog — that's what the `pipedaladmind` service exists for (see §3 of the plan). Phone
out, two taps, wait for the green LED to go dark, pull the plug.

**How real is the risk?** Not a coin flip — it's a small chance per yank that compounds over
months. What corrupts a card is a **write in flight**, and in this rig the writes happen when you
*save a preset*, not while you play. One specific reason to care: PiPedal 1.2.47 fixed a defect
where removing power within ~5 minutes of saving presets or banks could lose them. Fixed, but the
shape of the problem stands — **after an editing session, always shut down cleanly.** After a
session where you only played, a yank is very unlikely to hurt you.

Three ways to stop worrying about it, in increasing effort:

| Option | What it costs | When it's right |
|---|---|---|
| Shut down from the phone UI | Nothing. Just a habit | **Now.** Do this by default |
| **Overlay filesystem** — root fs becomes a RAM copy-on-write layer, SD goes read-only | Nothing persists: preset edits vanish on reboot | Before the first gig. Power-yank becomes safe *by construction* |
| `gpio-shutdown` + a momentary switch — a physical clean-shutdown stomp | One switch, one config line | Phase 3, while you're already wiring switches |

**The overlay is the real answer for a pedal**, and it's built into Pi OS:

```bash
sudo raspi-config
#  4 Performance Options → Overlay File System → enable
sudo reboot
```

Then the workflow splits cleanly, which suits how you'll actually use this:

```
   overlay OFF  ──►  building, editing presets, downloading captures, calibrating
   overlay ON   ──►  playing and gigging: power yank is harmless, nothing to remember
```

Turn it off the same way when you want to change something. Don't enable it during Phase 2 — you're
writing presets constantly and every change would evaporate.

### 11a. The physical shutdown switch — worth doing, and it's two wires

One momentary switch across **GPIO3 and GND** gives you a clean shutdown *and* a power-on, because
the Pi's firmware treats GPIO3 specially: pulling it low while running triggers an orderly
shutdown, and pulling it low again **while halted wakes the board and boots it**. Same switch,
both directions. **GPIO3 is the only pin that does both** — this is why you don't get to pick a
nicer pin.

```
      Pi 40-pin header, top-left corner
                                            momentary SPST, normally open
    pin 1  [3V3] [5V]  pin 2                (either way round — it's a
    pin 3  [GP2] [5V]  pin 4                 dumb short, no polarity)
    pin 5  [GP3] [GND] pin 6   ◄── here      ┌───────┐
    pin 7  [GP4] [TXD] pin 8            ─────┤  o   o├─────
                                             └───────┘
    pin 5 ──────────────────────────────────────┘   └────────── pin 6
```

Then one line in `/boot/firmware/config.txt`:

```bash
sudo nano /boot/firmware/config.txt
# add at the end:
dtoverlay=gpio-shutdown,gpio_pin=3,active_low=1,gpio_pull=up,debounce=100
sudo reboot
```

Test it before you trust it: press once → the green LED does its shutdown flicker and stops.
Press again → it boots.

> ⚠️ **Do not put this in the footswitch row.** `gpio-shutdown` fires on the press — there is no
> hold-for-3-seconds option — so a switch sitting next to your snapshot stomps is one mis-step
> from killing the rig mid-song. Mount it on the **back or side panel**, recessed, or somewhere
> your foot can't reach. This is a hand-operated button, not a footswitch.

**What it is not:** a power switch. The Pi still draws standby current after halt — the switch
gives you clean *stop and start*, not isolation. Your mains switch or the USB-C plug is still what
actually turns it off.

| Detail | Value |
|---|---|
| Part | Any **SPST momentary** push button, ~$2–4 at Altronics or Jaycar. **Not** latching |
| Wiring | Pin 5 (GPIO3) ←→ pin 6 (GND). No resistor — the overlay enables the internal pull-up |
| Config file | `/boot/firmware/config.txt` on bookworm (older guides say `/boot/config.txt`) |
| Caveat | GPIO3 is also **I2C1 SCL**. Fine today; it would fight I2C hardware like an OLED screen |

**Two things that change this later:**

- **Phase 3 (Pico).** You *could* have the Pico hold-detect a footswitch and pull GPIO3 low, which
  buys you the 3-second hold that `gpio-shutdown` lacks. **Don't** — the Pico is USB-powered *by
  the Pi*, so once the Pi halts the Pico is dead and can't wake it. You'd lose the power-on half.
  Wire the button straight to the header.
- **Phase 4 (Pisound).** The Pisound has its own button, and **hold >5 s = clean shutdown** is its
  default action (`pisound-btn`, remappable with `pisound-config`). At that point the GPIO3 switch
  is redundant for shutdown — though the Pisound button, being software, almost certainly can't
  wake a halted board. Keep the GPIO3 switch if you want the power-on.

---

## 12. Back it up — you just did the expensive part

**Using:** laptop (SSH, then PowerShell)

Nine calibrated captures and nine matched snapshots is hours of work living on one SD card that
gets its power yanked every time you use it as a pedal.

On the Pi:

```bash
sudo tar czf ~/pipedal-backup-$(date +%F).tar.gz /var/pipedal /etc/pipedal/config
ls -lh ~/pipedal-backup-*.tar.gz
```

Then from PowerShell on the laptop:

```powershell
scp <user>@<PI-IP>:~/pipedal-backup-*.tar.gz $HOME\Downloads\
```

`/var/pipedal` is presets, banks and downloaded captures; `/etc/pipedal/config` is your audio and
MIDI setup. It'll be a few hundred MB — the captures dominate. Keep it somewhere that isn't the Pi.

Also worth doing once: a full SD card image from the laptop (Win32DiskImager or `dd` from a Linux
box), so a dead card is a 10-minute restore rather than a rebuild.

---

## 13. Done when

*Updated 2026-09-05. The scope grew from 3 presets × 3 snapshots to **6 × 4**,
and the captures stayed full-amp-with-cab because the rig is on headphones —
preamp-only/DI is now a Blackstar-FX-return concern, not a Phase 2 one.*

- [x] Heatsink fitted, `get_throttled` = `0x0`, 50.1 °C under load
- [x] `systemctl get-default` = `multi-user.target`
- [x] **6 presets × 4 snapshots**, built by script, verified on disk
- [x] Busiest preset well under ~70% CPU with no xruns — **~29.5%**, 0 underruns in 240 s unobserved, 55–60 °C
- [x] Snapshot switching seamless with the full chain loaded
- [x] Footswitch *layout question* settled — direct `snapshot1..6` bindings exist (handoff §5)
- [ ] **All six presets level-matched at playing volume** (**not** NAM Calibration — §4) ← the one real gap
- [ ] CC numbers chosen and recorded, switch count decided (§9)
- [ ] Hotspot tested and set back to its normal trigger
- [ ] Backup tarball copied off the Pi (§12)
- [ ] You know how to shut down from your phone, and whether you want the overlay filesystem (§11)
- [ ] Shutdown/wake switch on GPIO3 wired and tested both directions, mounted out of stomping range (§11a)
- [ ] *Deferred:* preamp-only/DI captures + cab-IR bypass for the Blackstar FX return

Then **Phase 3** is a shopping trip and ~40 lines of CircuitPython:

| Item | Altronics cat # | AUD |
|---|---|---|
| Raspberry Pi Pico H | Z6421B | $15.00 |
| SPST momentary push button — shutdown/wake (§11a) | any small panel-mount, cat # TBC in store | ~$3 |
| DPDT momentary footpad switch × 6 | S1152A | $54.90 |
| Hookup wire 26AWG | W2250 / W2251 | ~$2 |
| USB-A → micro-USB B **data** cable | old Android cable | – |

Firmware is already written: [`pico-footswitch-code.py`](./pico-footswitch-code.py).

---

## If something breaks

**Using:** laptop (SSH)

```bash
./pipedal-setup.sh check          # first stop for anything
journalctl -u pipedald -f         # live logs, Ctrl-C to quit
```

| Symptom | Fix |
|---|---|
| Temps *worse* after the heatsink | Pad not seated — lift and re-press, or the board's in a case with no airflow |
| `get_throttled` shows under-voltage | 3A supply; if it persists, powered USB hub between Pi and interface |
| Snapshot recalls the wrong capture | Re-save the snapshot; confirm you're on a current PiPedal (older versions dropped bypass state) |
| A snapshot can't reach a pedal you want | Structure is fixed by the preset — add the plugin to the preset, then re-save all its snapshots |
| One capture is much louder / harsher | Its Input/Output Gain need setting — see §4. Not a calibration problem |
| Everything sounds thin and phasey | MIX knob to PLAYBACK. Always this |
| CPU fine but occasional crackle | Buffers `64×4` then `128×3`; check for xruns in the journal |
| Preset change has a gap | Expected — graph rebuild. Snapshots are the seamless ones |
| Pi won't boot after the heatsink | Unplug, reseat the SD card, check nothing shorted against the sink's base |
| Preset edits keep reverting after a reboot | Overlay filesystem is on — turn it off in `raspi-config` to edit (§11) |
| Presets lost after a power yank | Shut down from the UI, and be on a current PiPedal (1.2.47+ fixed a 5-minute write window) |
| Shutdown switch does nothing | `dtoverlay` line missing/typo'd, or you rebooted before saving `config.txt`. Must be **GPIO3** — other pins shut down but won't wake |
| Shutdown switch works, won't wake the Pi | Wake needs GPIO3 specifically, and the board must be *halted*, not unplugged |
