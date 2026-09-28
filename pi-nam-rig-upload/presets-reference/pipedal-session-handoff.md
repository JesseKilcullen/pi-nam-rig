# PiPedal — Session Handoff

**Updated 2026-09-12.** Originally written 2026-09-06; kept for §5's raw MIDI binding symbols and
§6's corrections/traps, not for status (see the callouts below and `pipedal-next-steps.md`).
Read this, then the doc you need from §7.

> **2026-09-10:** §1 (State) and §4 (Next, in order) are superseded by
> `pipedal-next-steps.md` — read that for current status. This doc's
> remaining live value is §5's raw MIDI binding symbols (confirmed from
> source) and §6 (corrections/traps) — keep those, don't re-derive them.
>
> **2026-09-12: §5a is ALSO superseded.** The "10 switches, 2 pages" layout
> below was the *settled* design as of 2026-09-06, but it was later replaced
> by the current 6×6 `pico-footswitch-v2` design in `pipedal-hardware-v2.md`
> — that doc is the one to build from now, not §5a. `miditest-10sw.sh` (which
> tests §5a's layout, and whose setup instructions repeat the broken
> port-0-to-port-1 virmidi wiring §6.18 disproves) has been moved to
> `archive/`. What's still true and worth keeping from §5a: the *reasoning*
> that absolute PC/CC addressing can't drift (still applies to the current
> design), and that Program Change needs no MIDI binding at all — both
> re-confirmed on the current design 2026-09-12, see `pipedal-hardware-v2.md`
> §5.1 and §6.27-28 below.

Doing footswitch/MIDI work? Go to `pipedal-hardware-v2.md` for the current
layout. **§6.18–28 here are still live** — §18 in particular contradicts
`pipedal-setup.sh` and plan §13.B as they were written, and cost most of a
session.

Doing preset/snapshot work? Go straight to
[`pipedal-presets-howto.md`](./pipedal-presets-howto.md) — it is self-contained
and has a paste-in prompt at the top.

---

## 1. State

| Phase | |
|---|---|
| 0 Setup | **Done.** PiPedal 2.0.110 |
| 1 Decisive test | **Done. Design A** — one NAM per preset, capture swapped per snapshot, seamless |
| 2 Build structure | **Built and verified.** 6 presets on the Pi. **Levels not matched — the one real gap** |
| 3 Footswitch | **MIDI layer proven end-to-end 2026-09-06, no hardware.** Layout settled: **10 switches, 2 pages** (§5a). Firmware written. Parts not bought (**~$112**, up from $76) |
| 4 Audio HAT | Deferred deliberately |

**Timing is fine and always was:** **0 underruns in 240 s** unobserved on the
heaviest, 55–60 °C, `throttled=0x0`. Staying at 64×3.

**"Nothing crackles" was wrong** — presets 4 and 6 did, and it cost most of a
session. It was **output level**, not timing (§6.10). Loathe has since been
removed.

**DSP figures below are STALE** (measured 2026-09-05, pre-changes). Preset 1
gained a second NAM instance and Ambient gained a delay tap. Re-run
`pipedal-probe.py` before trusting them.

| Preset | DSP (stale) | | Preset | DSP (stale) |
|---|---|---|---|---|
| 1 Clean | 9.6% | | 4 HG Rhythm | 9.4% |
| 2 Ambient | 29.4% | | 5 HG Lead | 19.6% |
| 3 Crunch | 13.4% | | 6 Massive | **unmeasured, 3 NAM, plays clean** |

## 2. Environment

| | |
|---|---|
| Pi | `ssh jesse@192.168.0.73`, host `pipedal`, key auth |
| Services | **`pipedald`** + **`pipedaladmind`** (not `pipedal`) |
| Interface | UMC204HD as `hw:U192k`. **Card number drifts — never pin it** |
| Audio | 48 kHz, buffer **64×3**. Governor `performance`, pinned 1500 MHz |
| Plugins | **TooB only.** No OD/dist/fuzz plugins exist — dirt comes from NAM captures |
| OS | Debian 13 trixie, aarch64, kernel 6.18, headless |
| Banks | `Factory Presets` (untouched) · `Default Bank` (mine) |

`jesse` is in `sudo` but **not** `pipedal_d`, and `sudo` needs a password — so
an assistant can read, `scp` and `--dry-run`, but **you** must run the commit.

## 3. The six presets

All tuner-first. `Threaded` on for all eleven instances. Presets 1, 2 and 3
sit at 2 NAM instances; **preset 6 runs 3, which the Pi 4 handles fine**
(§6.13) — and all three run constantly, because it is a blend, not a switch.

| # | Name | Amp | Pedal | Snapshots (1 = home) |
|---|---|---|---|---|
| 1 | Clean | Fender Tweed 5E3 | Boss BD-2W *(off)* | Clean · **Drive** · Solo · Dry · Wash |
| 2 | Ambient | Fender Tweed 5E3, **Kraken Gain-I G5** on snapshots 2–4 | Sunface fuzz *(off)* | Glass · Swell · Fuzz · Fuzz Rolled Off |
| 3 | Crunch | Kraken Gain-I G7 | TS9 `D0-T6-L10` | Crunch · Raw · Push *(→G8)* · Lead |
| 4 | HG Rhythm | Kraken Gain-II G8 | — | Rhythm · Solo · Tight · Wide |
| 5 | HG Lead | Kraken Gain-II G10 TrebleBoost | — | Lead · Rhythm · Solo+ · Dry |
| 6 | Massive | **Parallel:** Kraken Gain-I/II *(top)* + Tweed Clean *(bottom, always on)* | SunFace / Big Muff, in front of the split *(off at home)* | Massive · Heavier · Heaviest · Fuzz Low · Fuzz High |

**Preset 6 is now "Massive"** — the first parallel preset in the bank, using a
PiPedal Split node in Mix mode (§6.15). **Loathe was removed** on request — it
never sounded right and it was the source of the crackle hunt. Its captures (6505, HM-2, SF300, Big Muff) are all
still on the Pi. A revival needs preamp-only/no-cab captures and a matched
output, not the old values.

Slot 6 is free in presets 1 and 6; slots 5–6 in the rest. Capture swapping is
now the main mechanism, not the exception: Crunch/Push, Ambient
Swell/Fuzz/Fuzz Rolled Off, and all four of Massive's non-home snapshots.

Per-snapshot detail with a one-line description of every preset and snapshot:
`pipedal-preset-tables.md`.

**Captures on the Pi:** Victory VX Kraken A2 (16) · TS9 (5) · ProCo Rat (49) ·
BOSS HM-2 (11) · Behringer SF300 (5) · Sunface RCA (8) · **Big Muff (25, not
2)** · Blues Driver Waza (1) · CE-2w (1) · 11 factory amps. No Super Kraken
(VX100) capture exists on TONE3000. Kraken Gain-I runs **G5**/G7/G8/G10, each
with a TrebleBoost variant — G5, not G7, is the floor (§6.11).

## 4. Next, in order

1. **Level-match the six.** Still the one real gap, and now also the crackle
   fix — same control, same pass (§6.10). Only preset 4 has a non-zero
   `outputGain` (−4, for headroom rather than matching). Reference = preset 3;
   trim each amp-NAM `outputGain` at playing volume. **Not** NAM Calibration
   (`pipedal-phase2.md` §4). Do this before footswitches, and re-listen to
   4/5 — their EQ only started working on 2026-09-05 (§6.5).
2. **Rename `Default Bank` in the UI** (not in JSON).
3. **Back up the good state:** `pipedal-phase2.md` §12.
4. ~~**Prove the footswitch layout with no hardware.**~~ **DONE 2026-09-06.**
   Program Change, all six snapshot CCs, and empty-slot no-ops all verified on
   the rig via `snd-virmidi`. Layout settled at 10 switches (§5a). Still
   untested: `reset`, `defer`, `mute` — run `./miditest-10sw.sh <those>`.
   **`RESET_GAP_S` in `code.py` is a guess (0.6 s) until `reset` is run.**
5. **Then Phase 3** — buy the parts (~$112, §5a), wire per §5a, flash
   `pico-footswitch-code.py`. Firmware is written for the settled layout.
6. **Wire the power button + LED.** GPIO3 momentary = shutdown *and* wake
   (`dtoverlay=gpio-shutdown`, button across header pins 5 and 6).
   LED: `dtoverlay=act-led,gpio=19` + `dtparam=act_led_trigger=default-on`
   → solid while running, dark when halted. **Untested: whether the pin
   actually goes low at halt** — check with `sudo poweroff` on the onboard
   LED first, no wiring needed. Do **not** use `gpio-poweroff`: it disables
   GPIO3 wake and needs an external power-cut circuit.

Deferred: DI/no-cab captures + bypassing `toob-cab-ir` for the Blackstar HT
Stage 60 FX return (whole gain path changes, re-level after; bypass is stored
per snapshot, so there is no global switch). GPIO3 shutdown switch not wired.

## 5. MIDI bindings — settled from source

Direct snapshot select **exists**. Read from `rerdavies/pipedal` @ main
(`src/Storage.cpp`, `src/AudioHost.cpp`,
`vite/src/pipedal/SystemMidiBindingsDialog.tsx`), so it needed no Pi.

| Symbol | UI label |
|---|---|
| `snapshot1`..`snapshot6` | **Snapshot 1..6** — direct select |
| `prevProgram` / `nextProgram` | **Previous / Next Preset** |
| `prevSnapshot` / `nextSnapshot` | relative; skip empty slots, wrap |
| `prevBank` / `nextBank` | bank, **not** preset |
| hotspot × 2, `shutdown`, `reboot` | |

That list is exhaustive: **no tuner binding and no global mute.** Build those
from plugin bypass + a gain control, or give them a snapshot slot.

> **Bank ≠ Preset.** All six tones are presets in *one* bank, so `nextBank`
> jumps to `Factory Presets`. For stepping your tones use
> `nextProgram`/`prevProgram`. The plan's §10 diagram says "bank ±" and is
> wrong on this; it carries a correction note.

~~Intent: most switches on direct snapshots, 1–2 on preset up/down. **Switch
count deliberately still open.**~~ **Settled — see §5a.**

**Also verified 2026-09-06, on the rig:** Program Change selects a preset by
**absolute 0-based index within the current bank**, clamped to the last preset
if too high (`Storage::GetPresetByProgramNumber`, `src/Storage.cpp:1093`;
dispatched at `AudioHost.cpp:981` *before* any binding is consulted). **It
needs no binding at all.** PC 0 = `1 Clean`, PC 5 = `6 Massive`. This is what
makes §5a's paging drift-proof, and it means `nextProgram`/`prevProgram` are
not used by this rig.

## 5a. The settled footswitch layout — 10 switches, 2 pages

Proven end-to-end 2026-09-06 with `snd-virmidi`, no hardware.

```
     [RESET]  [MUTE]                                   [PWR]  ← Pi GPIO3, momentary
                                                              (NOT on the Pico)
  PRESETS    [P1][P2][P3]        [PAGE UP]   page := 1
  SNAPSHOTS  [S1][S2][S3]        [PAGE DN]   page := 0

  page 0: presets 1,2,3  snapshots 1,2,3     page 1: presets 4,5,6  snapshots 4,5,6
```

| Switch | Sends | Binding |
|---|---|---|
| P1–P3 | Program Change `page*3+slot` → PC 0–5 | **none** — built in |
| S1–S3 | CC `20 + page*3 + slot` → CC 20–25 | **Snapshot 1–6**, "Trigger on any value" |
| PAGE ▲ / ▼ | nothing — Pico-local state | none |
| RESET | PC 0, then CC 20 after `RESET_GAP_S` | none (reuses Snapshot 1) |
| MUTE | CC 26 | per-plugin: TooB Tuner `MUTE`, "Toggle on any value", **×6 presets** |
| PWR | nothing | GPIO3 + `dtoverlay=gpio-shutdown` |

**Why it can't drift:** every message names an absolute destination. The page
counter only picks *which* absolute message to send, so Pico and host can never
disagree in a way that matters. The plan's §13.H warning is about *relative*
bank stepping — not this. And with exactly two pages, ▲/▼ are **absolute page
selectors**, not a toggle: ▼ always means 1–3, ▲ always means 4–6, nothing to
remember. A single shift switch would have been worse.

**Presses:** 1 to any preset or snapshot on the current page, 2 across pages,
2–3 to change both.

**Dead switches, by design:** presets 2/3/4/5 have 4 snapshots so S5/S6 do
nothing there; presets 1 and 6 have 5 so only S6 is dead. Verified silent —
`Pedalboard::ApplySnapshot()` returns false on an empty slot and fires no
change. Room to fill them later (6 is the cap).

**Cost ~$112:** 10 × S1152A @ $9.15 = $91.50, Pico H $15, wire, plus a
momentary pushbutton (~$3) for GPIO3. Was $76 for the old 6-switch plan.

Firmware: `pico-footswitch-code.py` (rewritten for this; the old 5-switch
version is kept as `pico-footswitch-code.py.5switch-orig`).
Test script: `miditest-10sw.sh`.

## 6. Corrections — don't re-derive these

1. **Design A is what's built**, not B. One NAM per preset; capture swapped per
   snapshot is seamless. B was never built and doesn't fit.
2. **27% DSP was ONE NAM instance**, not three. The "cap at 2" that followed
   is **superseded — 3 instances hold on the Pi 4** (§6.13). That original
   test predates `Threaded` being on everywhere (§6.6). Still true: a
   bypassed instance costs nearly as much as an active one, so bypassing does
   not buy back a slot.
3. **`pipedald` was always the right service name.** The "wrong name" claim was
   a `grep -q` + `pipefail` bug in `pipedal-setup.sh check`, since fixed.
4. **The MIDI snapshot question was answered wrongly by pessimism.** Direct
   bindings exist; the 1.3.53 release note documented it and was missed.
5. **The parametric EQ was mis-voiced in presets 4, 5 and 6 from the first
   build.** `hiCut`/`hmfC` are **kHz**, so `hiCut: 9000` clamped to the 21 kHz
   rail — filter fully open. Loathe's "dark EQ, hiCut 9k" had never once
   applied. Nobody heard it; only found by adding `check_ranges()`.
6. **`Threaded` (`buffer`) was under-used.** Measured 45.3% → 17.9% on one NAM
   instance. Old rule was "only with 2 instances" — too conservative. Now on
   everywhere; worst case fell 47.3% → 29.5%.
7. **Sporadic underruns were the measurement, not the rig.** `pipedal-probe.py`
   holds a websocket open and re-reads the boot journal per sample. Unobserved:
   0 in 240 s.
8. **Backups were landing in `/root`** — under `sudo`, `~` is root's home.
   Fixed; now uses `SUDO_USER`'s home and chowns to them.
9. Earlier fixes, still true: `toneStack` default 3 = Bypass (amps use 2);
   `multi-echo` levels are percent not dB; `pathProperties` without `lv2State`
   loads no models.
10. **The crackle on presets 4 and 6 was OUTPUT LEVEL.** Not timing, not the
    gate, not the cab IR. Isolated by preset 4's `Rhythm` being clean while
    `Solo` — identical chain, `outputGain rel(+3.5)` and `hmfLevel rel(+2)` —
    crackled; and by −6 dB on Loathe's `outputGain` removing it outright.
    **Ruled out, each by test rather than argument, in this order:** DSP load
    (preset 4 runs 9.4% with 0 underruns); the front `toob-noise-gate` (its
    trigger LED was observed lit, i.e. gate *open*, while the crackle was
    audible); the OA30 cab IR (measured 48 kHz mono, identical format to the
    presets that are clean — and the JCM800 IR that presets 3/5 use is
    actually the *hottest* of the three at +32.5 dB `sum|h|`); a missing
    `input_stage` high-pass (added in the UI, no change); and the NAM's own
    internal `gate` (was −70 on 4 and 6 and nowhere else — set to −120, the
    crackle stayed). **Don't re-run any of these five.**
    The specific clipping stage was never pinned down. Headphones crackle,
    monitors on the main outs did not for preset 4 — but Loathe still did, and
    acoustic feedback through speakers confounds that comparison. Note the
    output VU meter sits around halfway while this happens: chugging has 12–18
    dB of crest factor and the meter is not a true-peak meter, so it hides it.
    Cab IRs carry **+30 to +32 dB of worst-case gain**, so the post-cab signal
    is far hotter than the NAM's own output suggests.
11. **Two more filename traps**, on top of the `G8 .nam` trailing space and
    `TebleBoost`: the Blues Driver capture is
    `Boss Blues Driver Waza/BOSS BD-2W | L4 T5 G6 MODE_C.nam` — a **pipe
    character** in the filename — and the Kraken Gain-I pack runs
    **G5**/G7/G8/G10, so G5 is available when you want the least gain. G7 is
    not the floor.
12. **Adding a pedal capture renumbers the amp.** The snapshot selectors are
    `(uri, index)`, so `AMP0 = ("toob-nam", 0)` silently starts pointing at
    the *pedal* the moment you put one in front. Preset 1 hit this when the
    Blues Driver went in — `Solo` had to move from `AMP0` to `AMP` or it would
    have boosted the pedal instead of the amp, with no error. Check the
    selectors whenever you add or remove a NAM instance.
13. **Parallel is NOT Pi-5-only — Phase 5 of the plan is stale on this.**
    That assessment reasons that parallel means "both instances run
    constantly" as though that were the expensive part. It isn't: parallel vs
    series is *routing*, and two instances cost the same either way. Loathe's
    `Chainsaw` snapshot already ran two active NAM instances at **29.5% on
    the Pi 4**. The Phase 5 note also predates the `Threaded` discovery
    (§6.6, worth 2.5–3.7×). Preset 6 now does parallel on the Pi 4. What is
    still true from Phase 5: a parallel blend sums before it leaves the Pi.
    **AND THE 2-INSTANCE CAP IS ALSO DISPROVEN.** Preset 6 runs **three**
    NAM instances — a fuzz into a Kraken on the top chain, a clean Tweed on
    the bottom, summed — and it plays clean on the Pi 4. Tested 2026-09-05.
    The only xruns were on changing preset *while still playing*, which is
    the graph-rebuild gap (`pipedal-data-model.md`), not this preset. The old
    cap came from a pre-`Threaded` measurement (§6.2 vs §6.6). **4 instances
    is untested.** The exact DSP figure has not been captured — run
    `pipedal-probe.py` if you want the number on record.
14. **PiPedal Split node schema**, read off `Factory+Presets.bank` (fourteen
    examples) since it is undocumented and is *not* an LV2 plugin:
    - uri `uri://two-play/pipedal/pedalboard#Split`, with `pluginName` and
      `iconColor` both **empty strings**, not `"default"`
    - children in **`topChain`** / **`bottomChain`** (not `*Children`)
    - controls `splitType` `select` `mix` `panL` `volL` `panR` `volR`
    - `splitType`: **0 = A/B** (chosen by `select`), **1 = Mix** (both run,
      summed, balanced by `mix`), **2 = L/R** (uses the pan/vol pairs)
    - no `.ttl` exists, so `check_ranges()` skips it — nothing validates
      these values for you
    - **`mix` sign is unverified.** Assumed negative favours `top`. Flip it
      in `snapshots_for()` if Massive's heavier snapshots sound cleaner.
15. **Anything that walks a preset must use `flatten()`.** Split children are
    nested, so `preset["items"]` no longer means "all items". Snapshots must
    carry a value for **every** item including nested ones or the omitted
    ones reset to plugin defaults (trap 2) — verified against the factory
    bank, where a 6-item preset with 3 nested carries 9 snapshot values.
    `snapshot()`, `preflight()`, `check_ranges()`, `selectedPlugin` and
    `report()` were all updated; anything new must be too.
16. **Sunface C3/C5/C8 cleanup captures DO exist**, with confirmed names
    (`SunFace RCA V7 F10 C3/C5/C8.nam`, plus V8 Cleanup variants). Ambient's
    "Fuzz Rolled Off" comment records these as unverified and rolls
    `inputGain` back instead — that can now be done properly if wanted.
17. **Run the crackle/tone tests in the UI before rebuilding.** Every
    conclusion above came from a one-knob UI change, not from a rebuild. Four
    plausible theories died that way in minutes each; rebuilding to test each
    one would have taken an hour and buried the evidence.

--- added 2026-09-12, confirming absolute Program Change ---

27. **`mido`/`python-rtmidi`'s ALSA sequencer backend does not work against `snd-virmidi` the way
    `amidi -S` does.** Confirmed while re-verifying §5's Program Change claim with
    `pico-footswitch-v2/pipedal_pc_probe.py`: it sent PC 0-5 and CC20, PiPedal's UI never moved, and
    client 128's Input pool `Alloc success` (`/proc/asound/seq/clients`) didn't increment at all.
    Switching to `amidi -p hw:0,0 -S "C0 00"` etc. worked immediately (counter incremented, preset
    changed). Likely cause, consistent with §6.18's virmidi dispatch quirk: `mido`'s ALSA backend
    opens its own sequencer client and addresses events *directly to* the virmidi port as a
    destination; virmidi only rebroadcasts to other sequencer subscribers (PiPedal, in this case)
    for bytes written into the **rawmidi character device** side of that same port. Bench-only —
    a real USB-MIDI Pico won't have this quirk — but don't reach for `mido` against virmidi again;
    use `amidi -S` for any future bench test.
28. **§5's Program Change claim is now independently re-confirmed, resolving a doc contradiction.**
    `pipedal-hardware-v2.md` §1/§5.1 and `pipedal-next-steps.md` had both been carrying this as
    still-open/untested since this doc's original 2026-09-06 verification. Re-tested 2026-09-12 via
    `amidi -p hw:0,0 -S "C0 00"` through `"C0 05"`: all six loaded the correct preset, 0-indexed, no
    MIDI binding required. `"B0 14 7F"` (CC20=127) correctly forced snapshot 1. Both other docs
    updated to match.

--- added 2026-09-06, from getting MIDI working ---

18. **`pipedal-setup.sh midi` and plan §13.B were WRONG, and cost most of a
    session.** They said: write to virmidi port 0, point PiPedal at port
    **1**, and `aconnect 0→1`. **virmidi does not forward sequencer-in to that
    port's sequencer-out subscribers.** Events arriving at `0-1` are readable
    at the *rawmidi* device `hw:0,1` — so `amidi -p hw:0,1 -d` sees them and
    the transport looks proven — but a **sequencer** client subscribed to
    `17:0` gets nothing. PiPedal 2.x reads MIDI through the ALSA sequencer
    (`AlsaSequencer::ReadMessage`, called from `AlsaDriver::ReadMidiData`,
    `AlsaDriver.cpp:1706`), so it received nothing, silently, with no error.
    Proved by subscribing `aseqdump` to each port: `16:0` got the CC, `17:0`
    got nothing.
    **Use ONE port for both ends and no `aconnect`.** PiPedal input =
    `Virtual Raw MIDI <card>-0`, and write to `hw:<card>,0`.
    `pipedal-setup.sh` is fixed and carries this as an inline comment.
19. **The definitive "did MIDI arrive?" test — use this first, always.**
    PiPedal's ALSA sequencer client is 128, and its input pool counts every
    delivered event:
    ```bash
    cat /proc/asound/seq/clients | sed -n '/Client 128/,/^Client 129/p'
    ```
    `Alloc success` increments once per event actually delivered. Fire a
    message, watch the number. This replaces all guessing from ears and from
    the UI — `aconnect -l` showing a subscription is **not** proof of
    delivery, which is exactly what misled us.
20. **Snapshot bindings MUST be "Trigger on any value", never "Trigger on
    rising edge".** `SystemMidiBinding::IsTriggered` (`AudioHost.cpp:344`)
    does `value >= 0x64 && lastControlValue < 0x64`, and stores
    `lastControlValue = value` every time. The pedal sends **127 on every
    press with no release**, so rising-edge fires exactly **once** and then is
    dead forever. Same trap in a different guise for the per-plugin tuner
    mute: use **"Toggle on any value"** (`MidiBindingView.tsx:579`).
21. **`inputMidiDevices` in `JackChannelSelection.json` is a dead red
    herring.** It is `[ ]` and that is fine — legacy from the Jack era.
    Chasing it wasted time. The live path is `MidiDevices.json` →
    `AlsaSequencer`.
22. **Persisting `snd-virmidi` in `/etc/modules` renumbers your cards.** It now
    loads early at boot, *before* USB enumeration, so virmidi took card **0**
    and the UMC204HD moved to **4** (it had been 3, with virmidi at 4 when
    loaded by hand). Audio was unaffected — PiPedal stores that by name
    (`hw:U192k`) — but **the MIDI device is stored with the card number baked
    into the name** (`"seq:Virtual Raw MIDI 4-1/VirMIDI 4-1"`), so it broke
    silently. Re-select the input after any reboot that reorders cards. This
    is virmidi-only: the Pico will enumerate under its own USB name.
23. **Changing the MIDI input in the UI takes effect live — no restart
    needed.** An earlier claim in this session that it required
    `systemctl restart pipedald` was wrong; the subscription appeared
    immediately under the old pid. The restart appeared to be needed only
    because the port was wrong either way (§18).
24. **MIDI and UI snapshot changes are the SAME code path.** UI →
    `PiPedalSocket.cpp:1548`; MIDI → `PiPedalModel.cpp:1300`. Both call
    `PiPedalModel::SetSnapshot()`. So a difference you *hear* between
    stomping and tapping is levels or how hard you're playing — never the
    control surface. A click heard while sweeping snapshots on presets 4 and 6
    by MIDI turned out to be §6.10 again; the same sweep on preset 3 was
    clean.
25. **TooB Tuner has its own `MUTE` port** — `ToobTuner.ttl:77`,
    `lv2:toggled`, 0–1, default 0. So §13.G's "two CCs from one press" trick
    is unnecessary; one CC on one control does it. **But:** per-plugin
    `midiBindings_` live on `PedalboardItem` (`Pedalboard.hpp:94`), i.e.
    *inside the preset* — so the binding must be created in **all six
    presets**; there is no global version. And **every snapshot stores
    `MUTE: 0`** (checked, all 26), while `ApplySnapshotValue()` ends with
    `isEnabled(snapshotValue->isEnabled_)` and merges control values — so
    **any snapshot change un-mutes you.** Structural, not a settings bug.
    Mute is placed pre-everything (tuner is item 1 in all six presets), so
    delay/reverb tails ring out and decay rather than cutting dead.
26. **Suspected upstream bug: the deferred-MIDI buffer mangles what it
    replays.** MIDI arriving while a Program Change is still loading is
    buffered (`AudioHost.cpp:1049`) and replayed after the rebuild. But the
    writer emits **one** header byte (`= (uint8_t)event.size`) while
    `ProcessDeferredMidiMessages` consumes **two** (`deviceIndex` then
    `messageCount`) — and the writer's own bounds check reserves `+2`, so the
    asymmetry looks unintended. **Consequence: don't send two messages
    back-to-back across a preset change, and don't double-stomp across one.**
    `code.py`'s RESET deliberately gaps its PC and CC by `RESET_GAP_S` to stay
    out of that window. `./miditest-10sw.sh defer` provokes it on purpose —
    **not yet run.**

## 7. Documents (all under `~/Desktop/pipedal 2/pipedal/` on the laptop — NOT
`~/Downloads`, this table was wrong about that)

**Read `pipedal-next-steps.md` first, always — it's the current status/next-steps doc and
supersedes this doc's §1/§4.** Table below is what each file is *for*, not a priority order.

| File | |
|---|---|
| **`pipedal-next-steps.md`** | **Current status & next steps — read this first.** Supersedes this doc's §1/§4 and `pipedal-nam-rig-plan.md`'s phase framing |
| **`pipedal-hardware-v2.md`** | **Current footswitch/OLED hardware design — read this for MIDI/footswitch work**, not §5a below (superseded, see top of this doc) |
| **`pipedal-presets-howto.md`** | **Preset/snapshot/bank work — start here for that.** Traps, generator API, verification, rollback |
| `pipedal-session-handoff.md` | This file. Live value: §5's raw MIDI binding symbols, §6's corrections/traps |
| `pipedal-preset-tables.md` | Flat per-preset/per-snapshot reference, all 8 presets. Regenerated from the scripts 2026-09-12 — was stale/6-preset-only before that |
| `pipedal-data-model.md` | Banks/presets/snapshots reference |
| `pipedal-nam-rig-plan.md` | Master plan, ~1800 lines. Deliberately not rewritten as things land — carries inline corrections instead. Hardware/shopping-list sections superseded by `pipedal-hardware-v2.md` |
| `pipedal-bunnings-list.md`, `pipedal-footswitch-build-guide.md`, `enclosure-templates/pipedal-footswitch-drill-template.svg`, `enclosure-templates/pipedal-footswitch-backwall-drill-template.svg` | Enclosure build — tools, step-by-step, to-scale drill templates. Design done, nothing physically built yet |
| `build-kraken-presets.py` | The generator for presets 1-6. Also on the Pi at `~/`. Identical copy lives in `generator-scripts/` — keep both in sync if you edit either |
| `add-muse-opeth-presets.py` | Layers presets 7-8 (Muse, Opeth) on top of the six. Also on the Pi at `~/`, also duplicated in `generator-scripts/` — **this duplication bit us 2026-09-12** (the `generator-scripts/` copy silently missed a same-day edit); check both if either seems out of date |
| `pipedal-probe.py` | DSP load / xrun measurement. Also on the Pi at `~/` |
| `pipedal-setup.sh` | Setup + diagnostics. `check` bug fixed; **`midi`/`miditest` corrected 2026-09-06 (§6.18)** |
| `pico-footswitch-v2/` | **Current firmware directory** — `code.py` (Pico), `pi_relay.py`/`pipedal-tuner-relay.service` (Pi-side OLED relay), `oled_display.py`, `pitch.py`, `midi_logic.py`, unit tests, and standalone diagnostics (`pipedal_pc_probe.py`, `tuner_freq_probe.py`, `midi_monitor.py`). Only ever copied to the Pi file-by-file so far, not as a whole directory |
| `archive/` | Historical docs (`pipedal-phase2.md`, `pipedal-tones.md`, `pipedal-today.md`, `pipedal-stereo.md`, `pipedal-tone-plan.md`, `pipedal-diy-audio-frontend.md`, `pipedal-pisound-micro-variant.md`) plus `miditest-10sw.sh` (moved 2026-09-12 — tested the now-superseded 10-switch layout, §5a, and its own setup instructions repeat the broken virmidi wiring §6.18 disproves). No replacement test script exists yet for the current 6×6 `pico-footswitch-v2` design's full CC/PC mapping; PC/CC20 alone were bench-tested manually via `amidi -S`, see §6.27-28 |

Not a document: `~/pipedal-src/x/pipedal-main` is an unpacked copy of the
PiPedal source (~254 MB) used to settle §5 and the snapshot traps. Safe to
delete; re-fetch from
`https://codeload.github.com/rerdavies/pipedal/zip/refs/heads/main`.
