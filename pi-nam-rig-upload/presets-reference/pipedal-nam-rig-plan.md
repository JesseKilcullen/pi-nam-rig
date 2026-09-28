# PiPedal + NAM Footswitch Rig — Build Plan

> ### STATUS 2026-09-06 - read the handoff first
>
> **[`pipedal-session-handoff.md`](./pipedal-session-handoff.md)** has the
> current state; this is the master plan and is deliberately not rewritten as
> things land. Phases 0-2 are **done** (6 presets x 4 snapshots, verified);
> **Phase 3's MIDI layer is proven and its layout is settled at 10 switches
> (handoff §5a) - but every Phase 3 section below still describes the old
> 6-switch design**; Phase 4 is deferred.
>
> **Known-wrong sections, each carrying an inline correction:**
>
> | Section | What's wrong |
> |---|---|
> | **§13.B** | **The virmidi wiring does not work on PiPedal 2.x.** Worst one - it cost most of a session. Port 1 receives nothing |
> | §10, §13.A | The 6-switch map and CC 20-26 table are superseded — first by the 10-switch layout, then (2026-09-12) by the current 6×6 `pico-footswitch-v2` design in `pipedal-hardware-v2.md`, which is the one to build from |
> | §13.C | Test script is the old 3-snapshot map. The 10-switch replacement (`miditest-10sw.sh`) is now itself archived — see below |
> | §13.D | Wiring diagram shows 6 switches; superseded twice over, current design is `pipedal-hardware-v2.md` |
> | §13.F | `code.py`'s config table has been rewritten twice since; current firmware is `pico-footswitch-v2/code.py` |
> | §13.G | The two-CCs-from-one-press tuner trick is unnecessary - TooB Tuner has a `MUTE` port |
> | §10 | Says `bank +/-` where it means `preset +/-` - and the settled layout uses neither |
> | §15 | "Does direct snapshot-N select exist?" - resolved, it does |
>
> For preset/snapshot mechanics use
> [`pipedal-presets-howto.md`](./pipedal-presets-howto.md).

**Goal:** Raspberry Pi running Neural Amp Modeler captures, controlled by 6 footswitches
(3 snapshots + bank up/down + tuner/mute), output into a real amp cab. All prices AUD.

**Later goal (Phase 5, Pi 5 only):** run two amp sims in parallel and blend them. Not part of the
current build — see §13 Phase 5.

**Status:** Phases 0 and 1 **complete**. **Design A selected** — one NAM instance per preset, the
capture (`modelFile`) swapped per snapshot, which tested **seamless** on this rig. DSP load ~27% of
one core with the full chain. No Pi 5, no new interface. Phase 2 next.
**Last updated:** 2026-09-04

### Measured environment (as built)

| | |
|---|---|
| Pi address | `192.168.0.73`, hostname `pipedal`, user `jesse` |
| SSH | key-based (ed25519, no passphrase) from the Windows laptop — non-interactive commands work |
| PiPedal | `2.0.110` · services **`pipedald`** + **`pipedaladmind`**, both active |
| Interface | `hw:U192k` / `UMC204HD 192k`. **The card number drifts** (3, then 1 on 2026-09-05). PiPedal stores it by *name*, which is why that's a non-event — never pin the number |
| Audio thread | `ppdl_alsaDriver`, RT priority 90. Its CPU against one core **is** the DSP load |
| Captures | `/var/pipedal/audio_uploads/NeuralAmpModels/Factory Models/` (12 files, all A2) |
| Audio config | `/var/pipedal/AudioConfig.json` — 48 kHz, buffer 64, 3 periods |

> ⚠️ **Card numbers are not stable.** The UMC204HD came up as card **3**, not the card 2 assumed by
> the `hw:2,0` examples in §12 and §13.B/§13.C. Always run `arecord -l` / `amidi -l` and use what
> you actually see.

> ⚠️ **`pipedal-phase2.md` is referenced throughout this document but does not exist in Downloads.**
> §12, §13 Phase 2 and §16 all point at it — including the NAM Calibration correction in its §4 and
> the shutdown-button design in its §11a. It needs writing or retrieving before Phase 2.

### Files

| File | What it is |
|---|---|
| [`pipedal-session-handoff.md`](./pipedal-session-handoff.md) | **Start a new session here.** Current state, environment, the six built presets, and the gotchas that cost time |
| [`pipedal-today.md`](../archive/pipedal-today.md) | **Start here.** Short version — everything doable with just the Pi 4, an SD card and the UMC204HD |
| [`pipedal-phase2.md`](../archive/pipedal-phase2.md) | **Phase 2.** Heatsink, 3 presets × 3 snapshots, level matching, backup — the step after `pipedal-today.md` |
| [`pipedal-data-model.md`](./pipedal-data-model.md) | **Reference.** Banks / presets / snapshots — multiplicity, what a snapshot can and can't change, the on-disk JSON layout |
| [`pipedal-setup.sh`](../pi-scripts/pipedal-setup.sh) | Stepped setup + diagnostics for the Pi. One command per phase — run `./pipedal-setup.sh` for the list |
| [`pico-footswitch-code.py`](./pico-footswitch-code.py) | Phase 3 Pico firmware. Save to `CIRCUITPY/code.py` |

---

## 1. Hardware

### Already owned
| Item | Notes |
|---|---|
| Raspberry Pi 4 | Must run **64-bit** Pi OS bookworm — 40% faster audio code than 32-bit |
| Behringer UMC204HD | Class compliant. Users who couldn't get the UMC**202**HD working on a Pi 4 reported the **204HD worked perfectly** |

### What you buy, and when

> **Before you know anything, the only purchase is an SD card (~$20).**
> Phase 1 — the test that decides the whole architecture — costs **nothing**. Don't pre-buy.

| Phase | Item | AUD | Required? |
|---|---|---|---|
| **0** Setup | SD card, 32 GB | ~$20 | **Yes** — only guaranteed spend |
| **0** | 3A USB-C PSU | ~$25 | Only if you don't already have the Pi 4's supply |
| **1** Decisive test | — | **$0** | Uses the UMC204HD you own. No heatsink needed (§7) |
| **2** Build structure | Heatsink (Altronics H0608, 5 mm) | **$3.95** | **Yes** — required from here on. 5 mm clears a HAT, so it also covers Phase 4 |
| **3** Footswitch | Pi Pico + 6 momentary footswitches + wire + USB cable | ~$60 | **Yes**, unless you buy a controller instead ($159–399, §13.I) |
| **4** HAT | Audio HAT | ~$175 | **Optional** — form factor only. No second heatsink needed if you bought H0608 |

**Running total to a working prototype: ~$95** (SD card + heatsink + Pico and switches), on top of
the Pi 4 and UMC204HD you already own.

**You do NOT need** a monitor, keyboard, mouse or micro-HDMI cable — enabling SSH in the Raspberry
Pi Imager (§8.0) means the entire build happens from your laptop.

### SSD instead of an SD card?

**Works on a Pi 4** (USB mass-storage boot; no NVMe, so SATA SSD + USB 3.0 adapter). **But don't,
not yet.** All four Pi 4 USB ports share one VL805 controller, which the UMC204HD is already on,
and PiPedal's latency docs name "competing USB device bus traffic" as an xrun cause. Not a
bandwidth problem — interrupt and scheduling jitter. Plus a bus-powered SSD worsens the
under-voltage risk (§7).

The concern behind the question is valid: SD corruption is the classic Pi failure and it's caused
by abrupt power loss, which is what a pedal does every time. Cheaper fixes, in order:

1. **Image the working card to your laptop** after Phase 1 passes (Win32DiskImager or `dd`).
   Corruption then costs 10 minutes, not a rebuild. Free, and the real answer.
2. **High-endurance card** if it keeps happening — Altronics' $79.95/32 GB cards are overpriced
   but genuinely the right product for power-cycle abuse.
3. **`sudo poweroff` instead of pulling power.** Worth a soft-shutdown switch at enclosure time.

**Revisit at Phase 4:** a HAT moves audio to I²S and frees the USB bus entirely, so SSD + HAT is
coherent in a way SSD + USB interface isn't.

#### Does an SSD create a clearance problem with the heatsink or HAT?

**Pi 4: no.** A USB SSD sits *beside* the Pi on a cable — it never enters the vertical stack. The
only clearance constraint is heatsink height under the HAT, which H0608 (5 mm) already solves.
The two questions are independent.

**Pi 5: everything fits, but the parts choice matters.**

```
   ┌──────────────────────────────┐
   │      Audio HAT               │  ← stacking header + 15-20mm standoffs
   └──────────────────────────────┘
   ┌──────────────────────────────┐
   │   Active Cooler (fan)        │  ← Pi 5 wants active cooling
   ├──────────────────────────────┤
   │      Raspberry Pi 5          │
   ├──────────────────────────────┤
   │   NVMe Base + SSD            │  ← underneath: GPIO header stays free
   └──────────────────────────────┘
```

- **NVMe underneath, not on top.** The **Pimoroni NVMe Base** mounts below the Pi 5, leaving the
  GPIO header and whole top surface free — reviews name this as what makes it work with audio
  HATs. The **official M.2 HAT+ mounts on top** and would fight the audio HAT for the header
  (and only takes 2230/2242, not standard 2280).
- **Active Cooler + HAT stacks** with a stacking header (8.5 mm plastic, 10 mm pins) plus 15 mm
  standoffs; 18–20 mm gives better airflow. The official M.2 HAT+ ships with spacers that clear
  the Active Cooler, and Blokas states Pisound **v1.2** supports Pi 5 with Active Cooler.
- **The USB objection vanishes on a Pi 5** — NVMe is on PCIe, so there's no contention with audio
  at all. SSD is a clean win there, unlike on the Pi 4.

> Taller standoffs raise the HAT's ¼" jacks further above the board. Measure before cutting an
> enclosure panel.

### If you end up needing a Pi 5

**Get the 4GB.** All Pi 5 variants share the same CPU (2.4 GHz quad Cortex-A76), and NAM is
CPU-bound — extra RAM buys zero audio performance. OS Lite plus PiPedal plus a few NAM captures
is a few hundred MB. 2GB would work; 8/16GB is wasted money here.

**Two mandatory extras:**

| Item | AUD | Why |
|---|---|---|
| Official **27W USB-C PSU** | $25.37 | Pi 5 caps total USB port current at **600 mA** unless it detects a USB-C PD 5V/5A supply, which raises it to **1.6 A**. The UMC204HD is bus-powered — a Pi 4 supply boots the board but won't unlock the higher limit |
| **Active Cooler** | $9.95 | Pi 5 runs hot. Stacks under a HAT with taller standoffs (see above) |

microSD and micro-HDMI carry over from the Pi 4 unchanged. Pisound needs board rev **v1.2** for
Pi 5.

#### Active cooling on a Pi 5, and how it affects the HAT

**Passive cooling is not an option here.** A passive Pi 5 under sustained load throttles at
~200 seconds and then sits pinned just above 85 °C. NAM is exactly that load. With the Active
Cooler it stabilises at **60–63 °C** and the fan never needs full speed.

**Fan noise doesn't matter for you.** 35–40 dB under load — relevant for a silent hi-fi streamer,
irrelevant next to a 60W valve combo. (Argon THRML is ~30 dB if it ever bothers you.)

**The stack, and what it needs:**

```
   ┌──────────────────────────────┐
   │      Audio HAT               │
   └──────────────────────────────┘
        ▲ GPIO riser / stacking header (8.5mm plastic, 10mm pins)
        ▲ 15mm standoffs minimum, 18-20mm for airflow
   ┌──────────────────────────────┐
   │   Active Cooler (fan)        │
   ├──────────────────────────────┤
   │      Raspberry Pi 5          │
   ├──────────────────────────────┤
   │   NVMe Base + SSD            │  ← underneath, no conflict with anything above
   └──────────────────────────────┘
```

- **Pisound v1.2 explicitly supports Pi 5 with the Active Cooler.** Get that revision.
- ⚠️ **Check standoff length.** Audio HATs commonly ship 12 mm spacers, which don't clear the
  Active Cooler. Budget ~$10 for a **GPIO riser** and 18–20 mm standoffs.
- Don't sandwich the fan tight against the HAT; 18–20 mm keeps intake airflow reasonable.
- The riser raises the HAT's ¼" jacks. Measure before cutting an enclosure panel.
- **H0608 (the 5 mm Pi 4 heatsink) is not a Pi 5 solution** — passive won't hold.

> Board prices not captured — Core Electronics blocks automated fetching and Pi Australia showed
> $288 with most variants unavailable, which looks wrong. Check Core Electronics and Little Bird
> directly. Accessory prices above are from Pi Australia.

### Conditional purchases — only if a test says so

| Trigger | Buy | AUD |
|---|---|---|
| Phase 1 forces Design B (3 NAM instances won't fit on the Pi 4) | Raspberry Pi 5 **4GB** + 27W PSU + Active Cooler | board TBC + $25.37 + $9.95 |
| Latency is the complaint after Phase 1 | Audient iD4 MkII | $285 |
| Pisound comes back in stock before Phase 4 | Blokas Pisound | ~$165 |
| `get_throttled` shows under-voltage (§7) | Powered USB hub | ~$30 |

### Perth shopping list — Altronics (Northbridge or Balcatta)

Catalogue numbers verified on altronics.com.au. **Per-store stock not verified** — every product
page has a store stock checker, or ring ahead.

| Item | Cat # | AUD | Phase |
|---|---|---|---|
| **Raspberry Pi Pico H** (pre-soldered headers) | **Z6421B** | $15.00 | 3 |
| — bare Pico RP2040, if you'd rather solder | Z6421 | $8.95 | 3 |
| **DPDT *Momentary* Footpad Switch × 6** | **S1152A** | $9.15 ea = **$54.90** | 3 |
| **Pi heatsink, 5 mm** — "doesn't interfere with HATs" | **H0608** | $3.95 | 2 (and 4) |
| — alt: 3-piece red set (CPU/USB/RAM) | H0607 | $3.50 | 2 |
| Hookup wire, 26AWG light duty | W2250 red / W2251 black | $0.35/m | 3 |

**≈ $75 for the whole Altronics run.**

> ⚠️ **Get the momentary switch.** `S1152A` is momentary. `S1150A` ($9.15) and `S1155` ($13.75) are
> *alternate* — they latch down and stay there, which is wrong for this. DPDT is fine; use one pole.

> ⚠️ **Don't buy the SD card at Altronics.** Their microSD range is high-endurance industrial —
> $79.95 for 32 GB. Get a normal A2 card from Officeworks or JB for $15–25.

#### Which Pico?

Any of them work. Pin names `GP0`–`GP28` are identical on RP2040 and RP2350, CircuitPython
supports both, and all are micro-USB — [`pico-footswitch-code.py`](./pico-footswitch-code.py) runs
unchanged on any. **Don't buy the Pico W** (Z6424, $19.95); you're not using WiFi, it's a wired
USB MIDI device. The **H** variant is worth the extra $6 because pre-soldered headers mean no
soldering on the Pico at all — jumper wires straight to the switches.

**Cable:** every Pico, including the Pico 2, is **micro-USB B** on the board. Both the Pi 4 and
Pi 5 have the same host ports — 2× USB 3.0 + 2× USB 2.0, all **USB-A**. So you want a
**USB-A → micro-USB B** cable, and it's the same on either board.

> The USB-C port on both the Pi 4 and Pi 5 is **power input only**, not a host port — you can't
> plug peripherals into it.

> ⚠️ **It must be a data cable, not charge-only.** Many cheap micro-USB cables (especially ones
> bundled with power banks) wire only the power pins — the Pico lights up but never appears as a
> USB device. An old phone sync cable is fine.

You also need to reach the Windows laptop to flash CircuitPython and save `code.py`. Same cable if
that laptop has USB-A; otherwise add a USB-C → micro-USB B cable or a C-to-A adapter. In normal
operation the Pi powers the Pico over this cable — no separate supply.

### UMC204HD caveat
Solid workhorse, not a latency champion. Expect to settle around **64×3** buffers rather than
the 16×4 an Audient iD4 (2.5 ms) or a good HAT (~2.1 ms) manages. Fine for building and
validating the whole rig.

---

## 1.1 Long-term audio I/O — do you always need an interface?

**You always need an ADC and a DAC.** The Pi 4 has neither: no audio input of any kind, and the
3.5 mm jack is PWM output only. Guitar cannot go directly into the Pi.

But "interface" doesn't have to mean a USB box. There are two shapes:

```
   OPTION A — USB interface (what you have now)

     Guitar ──► [UMC204HD] ──USB──► [ Pi 4 ]
                     │
                     └── MAIN OUT ──► Amp

   • Works today, already owned, zero spend
   • Separate box + USB cable + its own power draw
   • USB audio stack sits between you and the SoC


   OPTION B — HAT  ◄── the long-term answer

     Guitar ──► [ HAT ]  ← sits on the 40-pin GPIO header
                  ║        I²S straight into the SoC, no USB stack
                [ Pi 4 ]
                  ║
                  └──► Amp

   • One stack, no cables between converter and Pi
   • Powered from the header
   • The right form factor once this goes in an enclosure
```

### The HAT: Blokas Pisound — decided

| | |
|---|---|
| Price | ~$165 *(€99 converted)* |
| Connectors | **¼" TRS in and out** — guitar and amp cables plug straight in |
| Input | 100 kΩ, gain **0 to +40 dB**, supports instrument level |
| MIDI | DIN-5 in and out (note: the UMC204HD has this too) |
| SNR | 110 dB, Burr-Brown |
| Latency | ~2.1 ms |
| Power | <300 mA from GPIO header |
| Pi support | Pi 4 needs rev **v1.1+**; Pi 5 needs **v1.2** |
| Stock | **Sold out at source since 6 Aug 2026**, no ETA. Restock notification signed up 2026-09-02 |

**Recommendation: Pisound.** Not for latency — both land around 2.1 ms — but for the three things
that matter in a pedal build: ¼" jacks so guitar and amp cables plug straight in, an input that
actually expects instrument level, and MIDI DIN in. Pi + Pisound = guitar in, amp out, footswitch
in, one clean stack, no USB anything.

**Pi model caveat:** Pisound supports Pi 4 at board revision **v1.1+**. Pi 5 support requires
**v1.2**. If you end up on a Pi 5, check the revision before ordering.

### Is Pisound actually *better* than the UMC204HD, or just smaller?

Both. But it's not a clean win.

| | Winner |
|---|---|
| **Reliability** | **Pisound** — no USB enumeration (kills the "device vanished after reboot" problem), no USB bus contention as an xrun source, no bus-power draw. Can't develop a flaky cable. **The strongest argument** |
| **Latency** | **Pisound** — ~2.1 ms vs ~6–8 ms. Real, but 6–8 ms is already under the ~10 ms detection threshold, so measurable more than perceptible |
| **Form factor** | **Pisound** — the point of the whole exercise |
| **Guitar input impedance** | **UMC204HD** — proper Hi-Z INSTR switch vs Pisound's 100 kΩ. On the spec that matters most for a guitar input, the Behringer wins |
| **General usefulness** | **UMC204HD** — 2 in / 4 out, Midas preamps, phantom power. You can record with it. Pisound is stereo in/out, no mic pres |
| **MIDI DIN** | **Tie** — the UMC204HD has DIN in/out too. Not a Pisound advantage |
| **Audio quality for this job** | **Tie** — the valve amp and Celestions dominate either way |

**Verdict:** a dedicated-appliance upgrade, not a sound-quality one. If this becomes a boxed pedal
you rely on, Pisound is right and robustness carries it. If it stays a bench rig, the Behringer is
the more useful piece of gear. A buffered pedal in front neutralises the impedance gap.

### On the Pisound's 100 kΩ

That's instrument-*friendly*, not textbook Hi-Z — a real amp input is ~1 MΩ. Passive pickups into
100 kΩ will shed a little top end compared to plugging into your amp. Most people won't care, and
**any always-on buffered pedal in front fixes it completely** — you likely already own one. For the
boxed build, a buffer board goes inside the enclosure: see **§13.3**, ordered with the Pisound.

### Availability — what to do while Pisound is out of stock

Ranked, given Pisound has no restock date:

| Option | AUD | Pros | Cons |
|---|---|---|---|
| **Keep the UMC204HD** | $0 | Owned, works, real Hi-Z input, MIDI DIN already on it, the model reported working on a Pi 4 | Separate box, USB stack, ~64×3 buffers, awkward to enclose |
| **Audient iD4 MkII** | $285 (Brisbane Sound Group, from $365) | **2.5 ms measured on PiPedal**, best all-rounder in that thread. Proper instrument input | Still a USB box — solves latency, not form factor |
| MOTU M2 | ~$296 (Derringers) | 3.3 ms measured, 120 dB SNR | As above |
| Wait for Pisound | ~$165 | Still the best fit | No ETA |

**Decision rule after Phase 1:**
- Latency and CPU both fine → **buy nothing.** Revisit only when you build the enclosure.
- Latency is the complaint → **Audient iD4.** Biggest single improvement, available now.
- Only the box shape bothers you → wait for the Pisound restock.

**Perth logistics:** no one local stocks audio HATs — mail order from Pakronics (VIC) or Core
Electronics (NSW). **Altronics** (Balcatta) and **Jaycar** are good for the Phase 3 enclosure,
¼" jacks, footswitches and hookup wire.

### What this means for the plan

**Nothing changes for Phases 0–2.** Use the UMC204HD you already own; it's a perfectly good
development interface. The HAT is a Phase 4 form-factor decision, and you'll judge it far better
once you've heard the rig working and know whether you even need lower latency.

---

## 2. Signal chain — development rig (Phases 0–3)

> This is the rig you build and test with, using hardware you already own.
> The target rig after the HAT goes on is in **§13.3** — different diagram, same software.

```
   Guitar
     │ 1/4" TS
     ▼
┌──────────────────────────────────────────┐
│  Behringer UMC204HD                      │
│                                          │
│   INPUT 1 (combo)                        │
│     ├─ LINE/INSTR switch ....... INSTR   │  ← Hi-Z for guitar
│     ├─ 48V ...................... OFF    │
│     └─ GAIN ......... peaks around -6dB  │
│                                          │
│   MIX knob ......... FULLY to PLAYBACK   │  ← CRITICAL (gotcha 1)
│   DIRECT MONITOR ................ off    │
└───┬────────────────────────────┬─────────┘
    │ USB-B  (also bus-powers    │ MAIN OUT L
    │         the interface)     │ standard 1/4" guitar cable
    ▼                            ▼
┌─────────────────────┐   ┌──────────────────────────┐
│  Raspberry Pi 4     │   │  Amp FX RETURN           │
│   • 64-bit Pi OS    │   │  (power amp in)          │
│   • PiPedal         │   │  NOT the front input     │
└─────────┬───────────┘   └──────────────────────────┘
          │ wifi / hotspot
          ▼
   Phone or laptop browser → PiPedal web UI
```

Cab sim stays **off** — use "no cab" captures from TONE3000 rather than disabling cab sim after
the fact. Bonus: no IR convolution in the chain is real CPU saved.

> **On cables:** TRS and TS are *both* 1/4". "1/4 inch" is the barrel size; TRS (tip-ring-sleeve,
> balanced) vs TS (tip-sleeve, unbalanced) is the conductor count. The Main Out is balanced TRS,
> the amp's FX return is unbalanced TS — **just use a normal 1/4" guitar cable.** Plugging TS into
> that output grounds the cold leg, which is safe on the Behringer's IC outputs and standard
> practice. Costs ~6 dB, which the output knob and the amp's level switch more than cover.

### 2.1 The amp: Blackstar HT Stage 60

60W all valve — 2× ECC83 + 1× ECC82 preamp, **2× EL34** power valves, 2×12 Celestions, **serial FX
loop with a −10/+4 dB level switch**. Serial is what you want; the **FX Return** is your power amp in.

**The catch — don't stack two power amps.** Most TONE3000 captures are preamp *and* power amp with
no cab. Into your FX return that gives:

```
   NAM (preamp + power amp) ──► real EL34 power amp ──► real Celestions
                                        ▲
                                one power amp too many     ← flubby low end
```

**Use preamp-only captures instead.** They exist on TONE3000, taken through an amp's FX *send*:

```
   NAM (preamp only) ──────────► real EL34 power amp ──► real Celestions
```

Your EL34s and Celestions then do the job they were built for. Full-amp captures still work and
plenty of people run them this way — just know what you're layering.

**Your Celestions are the cab sim.** Running cab-off into a real 2×12 means every capture gets that
speaker's voice — a Fender capture through Celestions won't sound like a Fender. That's the trade
for amp-in-the-room feel, and it caps how much captures actually differentiate.

**What the FX Return actually connects to** — the power amp, not the speakers:

```
  Guitar ─► INPUT ─► PREAMP ────────────────────► FX SEND ─┐
                     (gain, 3 channels,                     │
                      EQ, ISF, reverb)                      │  [normally your pedals]
                                                            │
            ┌───────────────────────────────────────────────┘
            ▼
        FX RETURN ─► PHASE INVERTER ─► EL34s ─► OUTPUT TRANSFORMER ─► CELESTIONS
            ▲                          └──────────── power amp ─────────────┘
            │
   ◄── interface Main Out plugs in here
```

You **cannot** feed the speakers directly — they need watts, your interface puts out milliwatts at
line level, and the speaker jack is an output.

> ⚠️ **Never plug anything into the speaker output jack.** On a valve amp, running the output
> transformer without a proper speaker load can damage it. Leave the speaker jacks alone.

**Setup:**

- **FX Return**, not Send
- Loop level switch: start at **+4 dB**, drop to **−10** if too quiet (the TS cable already cost 6 dB)
- **Presence and Resonance** are power-amp feedback controls, so they should still work via the
  return — your remaining tone shaping. Verify by ear
- **Bypassed:** preamp, ISF, all three channel voicings, EQ, onboard reverb
- ⚠️ **Check whether Master volume still works from the return.** On many amps it sits before the FX
  send, leaving the interface output as your *only* level control. **Start the interface output at
  zero** and bring it up

---

## 3. Infrastructure — what actually runs on the Pi

**You write no code for Phases 0–2.** PiPedal is a packaged application installed from a `.deb`.
The only code in this entire project is the Pico firmware in Phase 3 (~50 lines of CircuitPython).

```
┌─ Raspberry Pi 4 ── 64-bit Raspberry Pi OS bookworm ────────────────┐
│                                                                    │
│  systemd                                                           │
│   │                                                                │
│   ├── pipedald ................. C++ server, runs unprivileged     │
│   │    ├── embedded web server ............... :80                 │
│   │    ├── WebSocket event bus ............... async JSON          │
│   │    ├── LV2 plugin host (TooB NAM, effects)                     │
│   │    └── realtime audio thread ──► ALSA ──► UMC204HD (USB)       │
│   │                                                                │
│   └── pipedaladmind ............ privileged helper                 │
│        └── shutdown, reboot, hotspot, system config                │
│                                                                    │
│  ALSA MIDI in ◄── USB MIDI (Pico, Phase 3)                         │
│               ◄── snd-virmidi (software testing, Phase 3 step 1)   │
│                                                                    │
│  Filesystem (all created by the installer — you make nothing):     │
│    /etc/pipedal/config ......... configuration                     │
│    /etc/pipedal/react .......... compiled web app assets           │
│    /var/pipedal ................ presets, banks, downloaded NAM    │
└────────────────────────────────────────────────────────────────────┘
          ▲                                    ▲
          │ WebSocket (persistent)             │ WebSocket
          │                                    │
   ┌──────┴───────┐                    ┌───────┴────────┐
   │ Phone browser│                    │ Laptop browser │
   │  React app   │                    │   React app    │
   └──────────────┘                    └────────────────┘

   Both clients see the SAME state, live. See §4.
```

---

## 4. The web UI — yes to everything you asked

The React client talks to `pipedald` over a **persistent WebSocket** exchanging async JSON.
Critically, from the architecture docs:

> "Changes to the state of the server application are propagated to **all connected web clients**
> via events that are fired by the server application over the web socket."

So:

- **Change presets/settings/sounds from the browser?** Yes — it's the primary interface. Build
  pedalboards, tweak knobs, create snapshots, download NAM captures, configure audio and MIDI.
- **Does it reflect footswitch changes live?** Yes. Stomp switch 2, and the snapshot highlights
  on your phone in real time. The footswitch and the UI are two inputs to the same state.
- **Multiple devices at once?** Yes — phone and laptop stay in sync.

There's also a **PiPedal Remote** Android app (Google Play) that finds the Pi via Bonjour, if you
prefer that to a browser tab.

### Do you need the web UI running to play? No.

The UI is a **client**, not the engine. `pipedald` is a systemd service that hosts the audio
engine *and* the web server in one process — it starts at boot and runs regardless of whether any
browser is connected.

```
   pipedald (systemd, always running)
     ├── audio engine ......... runs with zero clients connected
     ├── MIDI input ........... footswitches work with zero clients connected
     └── web server ........... sits there waiting for a browser
                                     ▲
                                     │ optional, connect only when you
                                     │ want to change something
                              phone / laptop
```

Power on the Pi with no screen, no phone, nothing — it loads the last preset and makes noise.
Footswitches keep working. You only open a browser when you want to *edit*.

Two related points:

- **Never run a browser on the Pi itself** while playing. That's GPU load, and it's exactly what
  §8.8 tells you to avoid — the docs cite it as the difference between 15 ms and sub-5 ms.
- A browser on your **phone** costs the Pi essentially nothing (a WebSocket and some JSON), so
  leaving it open on a music stand during a rehearsal is fine.

---

## 5. Preset vs snapshot — the core concept

- **Preset** = *the rig*. Which plugins exist and how they're wired. Changing preset rebuilds
  the graph → **audible gap**.
- **Snapshot** = *a photograph of every knob and switch on that rig*. No rebuild → **seamless**,
  reverb tails survive. **Max 6 snapshots per preset.**
- A snapshot **cannot** add, remove or re-order a plugin. Structure is fixed by the preset.

From the PiPedal source (`src/Pedalboard.hpp`), what a snapshot stores per plugin:

```cpp
class SnapshotValue {
    uint64_t instanceId_;
    bool isEnabled_ = true;                             // on/off (bypass)
    std::vector<ControlValue> controlValues_;           // every knob
    Lv2PluginState lv2State_;
    std::map<std::string, std::string> pathProperties_; // file selections (NAM model, IR)
};
```

So snapshots **can** flip pedals on/off, change any knob, **and** change which NAM capture is
loaded. Whether that last one is *silent* is the Phase 1 test.

> Note: there were bugs where bypass state wasn't captured in snapshots (including one specific
> to TooB Convolution Reverb). Fixed — just be on a current version.

### Rig layout

```
BANK  "Live Set"
│
├── PRESET 1 "Bank A"     ◄── plugin graph is FIXED inside a preset
│   │
│   │   [Tuner] → [Gate] → [TooB NAM] → [Drive] → [Delay] → [Rev] → [Gain]
│   │
│   ├── Snapshot 1  "Clean"    NAM=Fender    Drive off  Delay off
│   ├── Snapshot 2  "Crunch"   NAM=Vox       Drive off  Delay off
│   └── Snapshot 3  "Lead"     NAM=Marshall  Drive ON   Delay ON
│                                     ▲            ▲
│                        pathProperties_      isEnabled_
│                        (seamless? = Phase 1)  (always seamless)
│
├── PRESET 2 "Bank B"  ── same structure, 3 more snapshots
└── PRESET 3 "Bank C"  ── etc.
```

---

## 6. NAM A2 Lite vs A2 Full — which captures to download

| | **A2 Full** | **A2 Lite** |
|---|---|---|
| Built for | Pro audio, DAWs, powerful multi-FX | Embedded devices, pedals, mini modelling amps |
| Accuracy | Maximum | Reduced — simplified internal structure |
| CPU | 30–40% *less* than A1 | Runs at 50% CPU on a **$3 ARM Cortex-M7** |

**Naming trap:** "A2-Nano" was the original name for **A2-Lite**, used in early blog posts before
launch and renamed to avoid confusion with the existing A1-Nano. Same thing.

**What people actually say about the quality gap:** Lite models keep most of the dynamic
character intact but simplify the model internals. In a well-tuned studio you'll likely hear
*some* difference — but on stage or in a practice room it's unlikely you'd notice. Some hosts
auto-select the variant that fits their CPU budget.

**For this build:** you're going through a real amp cab in a room. The Lite/Full gap is the least
significant variable in your signal path.

**But note the sequencing:** A2 *Full* uses 30–40% less CPU than A1 Standard, so a single A2 Full
instance may well fit on a Pi 4 where A1 Standard wouldn't.

- **Design A (1 NAM instance):** try **A2 Full** first. If CPU is tight, drop to Lite.
- **Design B (3 NAM instances):** **A2 Lite only.** Not negotiable on a Pi 4.

---

## 7. Heatsink, power, and thermals

> **DONE 2026-09-04:** H0608 fitted *before* the Phase 1 measurements. **50.1 °C under full load**,
> `get_throttled` `0x0` including sticky bits — so the Phase 1 numbers are valid and don't need
> re-baselining. Board running in open air, not in a case. No under-voltage, so the powered USB hub
> is not needed.

### Can you run Phase 0/1 without a heatsink? Yes.

Bench sessions are short and you're validating *behaviour*, not endurance. Just watch the
temperature, because throttling silently invalidates your CPU measurements.

- Pi 4 soft-throttles at **80°C**, hard-throttles at **85°C**
- Run the board **in open air** — a closed case with no fan is *worse* than a bare board
- If you see sustained >75°C or `get_throttled` returns anything but `0x0`, stop trusting the
  numbers and come back with a heatsink

```bash
vcgencmd measure_temp              # one-off reading
watch -n 2 vcgencmd measure_temp   # live, Ctrl-C to quit
vcgencmd get_throttled             # 0x0 = healthy
```

`get_throttled` bits: `0`=under-voltage now, `1`=ARM freq capped, `2`=throttled now,
`3`=soft temp limit; bits `16-19` = the same four *since boot*.

Get a heatsink before Phase 2. Thermal throttling is a documented xrun cause.

### Power — worth watching

- Use a proper **3A USB-C** supply. Under-voltage causes throttling *and* audio glitches, and it
  presents identically to a "PiPedal problem".
- The **UMC204HD is USB bus-powered**, drawing from the Pi. This should be within budget, but if
  `get_throttled` shows under-voltage bits, a powered USB hub between Pi and interface is the fix.

---

## 8. Phase 0 — full setup walkthrough

Each step below opens with a **Using:** line listing exactly what it needs.

There's a companion script that does the mechanical parts: **[`pipedal-setup.sh`](../pi-scripts/pipedal-setup.sh)**.
It's stepped, not a single blind run — one command per phase, because there are reboot points and
steps where you have to listen and judge. `./pipedal-setup.sh` with no arguments lists everything.

### 8.0 Fresh install — Raspberry Pi Imager

**Using:** Windows laptop · microSD card · card reader or SD adapter. *Pi stays unplugged.*

You need a 32 GB SD card, a card reader, and another computer. Install **Raspberry Pi Imager** from
raspberrypi.com/software.

**Choose Device:** Raspberry Pi 4

**Choose OS:** `Raspberry Pi OS (other)` → **Raspberry Pi OS Lite (64-bit)**

> **Lite, not Desktop.** You're going headless anyway (§8.8), so Lite means no GPU contention
> ever and one less step. You still get a full console login on an HDMI screen with a keyboard.
> The only reason to pick Desktop is wanting a browser *on* the Pi — you don't, you'll use your
> phone, and the plan explicitly says never run a browser on the Pi while playing.
> **Must be 64-bit either way.**

**Choose Storage:** your SD card.

Click **Next** → *"Would you like to apply OS customisation settings?"* → **Edit Settings**.

#### General tab

| Field | Set it to |
|---|---|
| Set hostname | `pipedal` — makes it reachable as `pipedal.local` |
| Set username and password | your username + a real password. There is no default `pi`/`raspberry` any more |
| Configure wireless LAN | your SSID + password |
| **Wireless LAN country** | **AU** — don't skip this, Wi-Fi may not come up without it |
| Set locale settings | Time zone `Australia/Perth`, keyboard layout to match your keyboard |

#### Services tab

- **Enable SSH** → *Use password authentication* (or paste a public key)

This is the one that matters most: with SSH on, you do the whole build from your laptop instead of
hunching over a keyboard plugged into the Pi.

#### Then

**Save** → Yes to apply → Yes to erase → **Write**. Takes a few minutes.

### 8.1 First boot and getting the script across

**Using:** Pi 4 · microSD · USB-C PSU · UMC204HD + USB-B cable · laptop (PowerShell). *No monitor, keyboard or HDMI cable.*

Card in, power on, wait 60–90 seconds. From your laptop:

```bash
ssh <your-username>@pipedal.local
```

If `pipedal.local` doesn't resolve, get the IP from your router and use that instead.

Copy the script over (run this on your laptop, not the Pi):

```bash
scp pipedal-setup.sh <your-username>@pipedal.local:~/
```

Then on the Pi:

```bash
chmod +x pipedal-setup.sh
./pipedal-setup.sh check          # read-only, safe, tells you where you stand
```

`check` verifies aarch64, OS and kernel version, boot target, temperature and throttling state,
capture devices, whether PiPedal is installed and running, and lists MIDI inputs. Run it any time
something looks wrong.

### 8.2 The ordered run

**Using:** laptop (SSH session into the Pi)

```bash
./pipedal-setup.sh check
sudo ./pipedal-setup.sh update      # then: sudo reboot
./pipedal-setup.sh audio            # with the UMC204HD plugged in
sudo ./pipedal-setup.sh install
sudo ./pipedal-setup.sh headless    # skip if you used Lite — already console-only
```

Everything below is what those steps do and what to check by hand.

### 8.3 Update the OS (what `update` does)

**Using:** laptop (SSH)

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

### 8.4 Confirm the interface is seen (what `audio` does)

**Using:** laptop (SSH) · UMC204HD plugged into the Pi

Plug in the UMC204HD, then:

```bash
lsusb                # should list the Behringer
aplay  -l            # playback devices
arecord -l           # capture devices — the UMC204HD must appear here
```

If it's not in `arecord -l`, nothing downstream will work. Check the USB cable first.

> **Do you need Behringer drivers? No.** The UMC204HD is USB Audio Class compliant — the kernel's
> built-in `snd_usb_audio` handles it. No vendor Linux driver exists or is needed (Behringer's
> download is the Windows ASIO driver). Confirm it's bound with `lsmod | grep snd_usb_audio`.

#### Two known UMC quirks on Linux

**If you get silence or glitching that buffer changes don't fix**, try the implicit-feedback
option. A UMC202HD user needed this to get the device working at all — it's a kernel
implicit-feedback handling issue on some revisions of this family:

```bash
# test it now (unplug the interface first)
sudo modprobe -r snd_usb_audio
sudo modprobe snd_usb_audio implicit_fb=1

# make it permanent
echo "options snd_usb_audio implicit_fb=1" | sudo tee /etc/modprobe.d/behringer.conf
sudo reboot
```

**If the interface vanishes after a reboot**, unplug and replug the USB cable. One UMC204HD user
reported exactly this; another on different hardware never saw it. System-dependent, so check
`arecord -l` after every boot until you know which camp you're in. This is also a small argument
for moving to a HAT eventually — a board on the GPIO header can't fail to enumerate.

Encouraging data point from the same thread: users ran the 204HD at **buffer 64, 3 periods with no
xruns** — exactly the 64×3 this plan targets. A kernel newer than 5.15 matters; bookworm ships 6.x.

### 8.5 Install PiPedal (what `install` does)

**Using:** laptop (SSH) · Pi needs internet

Latest release is **v2.0.110** (28 July 2026). Grab the arm64 `.deb` from the
[releases page](https://github.com/rerdavies/pipedal/releases) — verify the exact filename there,
the asset list didn't render when I checked.

```bash
mkdir -p ~/Downloads && cd ~/Downloads
wget https://github.com/rerdavies/pipedal/releases/download/v2.0.110/pipedal_2.0.110_arm64.deb

sudo apt-get install ./pipedal_2.0.110_arm64.deb
```

> **You MUST use `apt-get`.** Per the install docs: `apt` will not install downloaded packages,
> and `dpkg -i` will not pull dependencies.

**Directories to create: none.** The package builds `/etc/pipedal/config`, `/etc/pipedal/react`
and `/var/pipedal`. NAM captures download into PiPedal's own storage via the web UI.

### 8.6 Verify the services

**Using:** laptop (SSH)

```bash
systemctl status pipedald
systemctl status pipedaladmind
pipedalconfig --help          # full option list lives here, not in the docs
```

### 8.7 Reach the web UI

**Using:** phone or laptop browser · same wifi as the Pi

```bash
hostname -I                   # note the Pi's IP
```

From your phone or laptop on the same network:

- `http://<pi-ip>/`
- or `http://raspberrypi.local/` (substitute your hostname)
- from the Pi itself: `http://127.0.0.1/`

Walk the onboarding page when it appears.

### 8.8 Configure audio

**Using:** phone (browser) · UMC204HD · guitar · amp

Hamburger menu → **Settings** → **Audio Device Settings**:

- Select the UMC204HD
- Sample rate **48 kHz**
- Buffers: start at **64×3**
- **Set the input channel** — PiPedal's docs warn many two-input interfaces present the guitar on
  the *right* channel only

On the interface: INSTR switch in, 48V off, **MIX knob fully to PLAYBACK**.

Play. You should hear guitar.

### 8.9 Go headless before you measure anything (what `headless` does)

**Using:** laptop (SSH). *Nothing on the Pi's HDMI — that's the point.*

This is a big deal, not a nicety. The docs state a system struggling to hit 15 ms with a desktop
running "could easily be able to achieve sub-5ms latency" headless. Headless here means *nothing
using the GPU*.

```bash
sudo raspi-config
#  1 System Options → S5 Boot / Auto Login → B1 Console  (or B2 Console Autologin)
sudo reboot
```

Now unplug the monitor and drive it from your phone. To get the desktop back later:
`sudo systemctl set-default graphical.target`

### 8.10 Hotspot (for playing away from your network)

**Using:** phone · laptop (SSH). *Do this at home where you can still recover it.*

Not needed at home, but set it up once so it's there.

> **Configured:** network **pipedal**, password *(redacted — see `secrets.local.md`)*, channel 6, trigger "No ethernet connection".
> Full details in [`../QUICK-REFERENCE.md`](../QUICK-REFERENCE.md).

Onboarding page **or** Settings menu → **Auto-Hotspot configuration** dialog. Choose when it
activates:

- No ethernet connection
- Always on
- Not at home
- No remembered Wi-Fi connections

When the hotspot is live, connect your phone to the Pi's network and browse to the normal
hostname, or fall back to **`http://172.23.0.2`**.

Command-line fallback if the dialog misbehaves: `pipedalconfig --help` and look for the hotspot
options.

**Test it properly:** pick "Always on" temporarily, reboot, connect your phone to the Pi's SSID,
confirm the UI loads, then set it back to your preferred trigger. Do this at home where you can
still plug a monitor in if it locks you out.

---

## 9. Monitoring, logs and debugging

**Using:** laptop (SSH, ideally two windows) · phone for the CPU meter

**Nothing to build.** PiPedal logs to the systemd journal already.

```bash
# Live tail while you play — the one you'll use most
journalctl -u pipedald -f

# This boot, whole journal
journalctl -b0 | less

# Service health
systemctl status pipedald pipedaladmind

# Restart after config changes
pipedalconfig --stop          # stops pipedald AND pipedaladmind
sudo systemctl restart pipedald
```

**CPU load:** shown in the PiPedal web UI — this is your primary Phase 1 instrument. For a second
opinion, `htop` on the Pi.

**Thermals:** `vcgencmd measure_temp` and `vcgencmd get_throttled` (see §7).

**If you need verbose logging**, stop the service and run the daemon by hand:

```bash
sudo systemctl stop pipedald
pipedald /etc/pipedal/config /etc/pipedal/react -port 0.0.0.0:8080 -log-level debug
```

Then browse to `http://<pi-ip>:8080/`. Ctrl-C and `sudo systemctl start pipedald` to go back.

### Suggested monitoring layout for Phase 1

Three terminals over SSH, or three tmux panes:

```
┌────────────────────────┬────────────────────────┐
│ journalctl -u pipedald │ watch -n 2 \           │
│   -f                   │   vcgencmd measure_temp│
├────────────────────────┴────────────────────────┤
│ htop                                            │
└─────────────────────────────────────────────────┘
        + PiPedal web UI on your phone (CPU meter)
```

---

## 10. Footswitch mapping

```
   ┌─────┐  ┌─────┐  ┌─────┐   ┌─────┐  ┌─────┐   ┌─────┐
   │  1  │  │  2  │  │  3  │   │  4  │  │  5  │   │  6  │
   └──┬──┘  └──┬──┘  └──┬──┘   └──┬──┘  └──┬──┘   └──┬──┘
      │        │        │         │        │         │
   snap 1   snap 2   snap 3    bank +   bank −    tune+mute
    CC 20    CC 21    CC 22     CC 23    CC 24    CC 25+26
      │        │        │         │        │         │
      └────────┴────────┘         └───┬────┘      toggle
           seamless                 gap OK
              │                        │            │
              └───────────┬────────────┴────────────┘
                          │ USB MIDI
                          ▼
            PiPedal → Settings → System MIDI Bindings
```

> ## ⚠️ THE DIAGRAM ABOVE IS SUPERSEDED — 2026-09-06
>
> The settled layout is **10 switches in two pages** (handoff §5a), proven
> end-to-end on the rig with no hardware:
>
> ```
>      [RESET]  [MUTE]                              [PWR] ← Pi GPIO3, momentary
>
>   PRESETS    [P1][P2][P3]        [PAGE UP]  page := 1
>   SNAPSHOTS  [S1][S2][S3]        [PAGE DN]  page := 0
>
>   page 0: presets 1,2,3  snapshots 1,2,3
>   page 1: presets 4,5,6  snapshots 4,5,6
> ```
>
> Why 6 switches wasn't enough: the bank has **4–5 snapshots per preset and 6
> presets**, so three snapshot switches left the 4th and 5th unreachable by
> foot. Paging fixes that with 1 press to anything on the current page, 2
> across pages.
>
> `bank ±` is gone, and so is `preset ±` — the preset row sends **absolute
> Program Change**, which needs no binding and cannot drift.

~~**Switch 6 sends two CCs from one press**~~ — **not needed.** TooB Tuner has its own `MUTE`
control, so one CC does it. See §13.G's correction.

**The fallback is no longer needed.** Direct snapshot-N select was confirmed to exist (§15), so
this primary layout stands. `prevSnapshot`/`nextSnapshot` do also exist if you ever want them.

> WARNING: **`bank ±` in the diagram above is wrong for this rig.** All six tones live in **one**
> bank (`Default Bank`), so Next/Previous **Bank** would jump to `Factory Presets` — not between
> your tones. What you want on those switches is **Next/Previous Preset** (`nextProgram` /
> `prevProgram`; labelled "Next Preset" / "Previous Preset" in the UI). Bank bindings only become
> useful once you have more than one bank of your own.

---

## 11. Latency expectations

PiPedal docs state **sub-4 ms is achievable on a Pi 4** with a good USB interface on the stock
PREEMPT kernel — no RT kernel needed. Measured round-trip on a MOTU M2 at 48 kHz:

| Buffer | Round-trip |
|---|---|
| 16 samples | 3.9–4.2 ms |
| 32–64 samples | mid-range, more stable |
| 128 samples | 9.2–14.6 ms |

With NAM eating CPU on a Pi 4 + UMC204HD, realistically **~6–8 ms**.

For perspective: sound travels ~1 foot per millisecond, so standing 5 feet from a cab already
costs 5 ms you don't notice. Player detection threshold is ~10 ms+. This will not feel spongy.

Sample rate: prefer 48 kHz. ALSA shows no significant latency difference vs 44.1.

---

## 12. Phase 1 — the decisive test (15 min) ⭐ **COMPLETE — Design A on the Pi 4**

### Result, 2026-09-04

Run on headphones out of the UMC204HD, not into the amp — the question was about the audio engine,
so the cab was not needed. Cab sim plugin in the chain to make preamp-heavy captures listenable.

**Model swap inside a snapshot IS seamless on this rig. Design A selected.**

Built as preset `New`: **one** TooB NAM instance, three snapshots differing only in
`pathProperties → toob-nam#modelFile`:

| Snapshot | Capture |
|---|---|
| Clean | `1960 Fender Tweed Deluxe 5E3 - Clean.nam` |
| Crunch | `1960 Fender Tweed Deluxe 5E3 - Crunch.nam` |
| Gain | `[AMP] MESA.MKVII-90W-CH3-MKIIB Pony Rawness - BLEND #3.nam` |

Chain: `[tuner] → [noise-gate] → [NAM] → [cab-sim] → [delay]`.

Switching was clean on a ringing chord and while picking. The only artefact is a faint noise-floor
cut dropping from high gain to clean — expected, and real amps do the same. So §5's worry that
"storing `pathProperties_` ≠ silent swap" turned out not to bite here.

**Design B was never built or tested.** No preset on the Pi has more than one NAM instance
(verified by reading every bank file). It isn't needed — Design A works and costs a third of the CPU.

| Measurement | Result | Target |
|---|---|---|
| **DSP load** — **1 NAM** + tuner + gate + cab sim + delay | **~27–28%** of one core, peak 36% | < 70% ✅ |
| `pipedald` whole process | ~30% | — |
| Temp under load — H0608 fitted, open air | **50.1 °C** | < 75 °C ✅ |
| `get_throttled` | **`0x0`**, incl. sticky since-boot bits 16–19 | `0x0` ✅ |
| Buffer | **64 × 3 @ 48 kHz**, clean first try | 64×3 ✅ |
| Underruns during ~1h45m of play | **1** — coincided with SSH sampling, likely self-inflicted | 0 ⚠️ |
| Underruns at engine startup | 2, both 18 s after boot. Ignore | — |

Measured on `ppdl_alsaDriver` (RT priority 90) rather than the UI meter — that thread's CPU against
one core *is* the DSP load.

> ⚠️ **The 27% figure is ONE NAM instance.** An earlier revision of this section labelled it as
> three; that was wrong. Design B would cost roughly triple the NAM share, so it has **not** been
> shown to fit and shouldn't be assumed to. It also isn't needed.

### What this settles, and what it doesn't

**Settled:** the seamless-swap question that gated the whole architecture. Design A — the cheap
option, and the one §12's decision tree called "comfortable" — is the one you're building. It's
also the design a future Phase 5 parallel blend would want.

**Still open:** whether the A2 slimmable size can be selected. TooB NAM exposes a **`modelSize`**
control (currently `0` in every snapshot), which is very likely the A2 submodel selector. An
earlier note here claimed no such selector existed — that was wrong. Untested either way, and
irrelevant at 27% load.

### Optional, now that there's headroom

1. **Push the buffers down.** 64×3 was this plan's *target*, not a limit found by testing. Try
   **32×3**, then **32×4**. Halving the buffer roughly doubles *relative* DSP load — expect ~55%,
   which is affordable. Per §11 that moves ~6–8 ms toward the 4 ms range. **Deferred by choice:**
   latency at 64×3 already feels fine, so this is a want-to, not a need-to.
2. **Use A2 Full captures.** With one instance there was never any doubt.
3. **Get preamp-only, no-cab captures** — see below.
> ⚠️ **The captures used for this test are the wrong ones for the amp.** There are **no TONE3000
> downloads on the Pi** — the test ran on PiPedal's bundled Factory Models. Those are **full-amp**
> captures and several **include a cab**: `MRSH JM50LD I Crunch2 FAT CAB`,
> `BCAT ER30 EF86 Edge BAL CAB`, `[AMP] FMAN.JOSE-Mes4x12-V.PRES`. Into the HT Stage 60's FX return
> that's §2.1's two-power-amps problem plus cab-on-cab through the Celestions. Harmless for this
> test, wrong for playing. Also check you aren't running the cab sim plugin *and* a `CAB` capture
> at the same time.

### Original test procedure (kept — re-run this after the HAT goes on)

**Using:** Pi 4 · UMC204HD · guitar · amp · phone (PiPedal UI) · laptop (SSH for monitoring). **Nothing to buy.**

Everything downstream depends on this.

- [ ] Log into TONE3000 inside PiPedal, download 3 captures (see §6 for Full vs Lite)
- [ ] Build one preset: `[Gate] → [TooB NAM] → [Delay]`
- [ ] Set interface input gain (peaks near 0 dBFS), then the plugin's Input Gain per capture.
      **Not NAM Calibration** — see the correction in `pipedal-phase2.md` §4
- [ ] Two snapshots pointing at *different* captures. **Pick two that sound wildly different**
      (clean Fender vs high-gain Marshall) so you can hear whether the switch landed at all
- [ ] **Verify the snapshot actually changes the model before testing for glitches.** Tap
      snapshot 1 → TooB NAM shows capture A. Tap snapshot 2 → shows capture B. If both show the
      same model, `pathProperties_` isn't being recalled and a "clean" result means nothing
- [ ] Hold a sustained chord, switch snapshots, listen hard for a click or dropout
- [ ] Repeat while actively picking — catches gaps between notes that a ringing chord hides
- [ ] Watch the CPU meter with 1, 2, then 3 NAM instances loaded — **record the numbers**
- [ ] Confirm temp stayed under 75°C and `get_throttled` is `0x0`, or the numbers don't count

**How to create and switch snapshots (no MIDI needed yet):** set the controls how you want, hit the
**snapshot button (camera icon)** in the preset editor, save to a slot. Switch between them by
tapping in **Performance View**.

**Both hands are on the guitar — two ways round that:**

1. Phone on a music stand. Strum a big open chord, let it ring, tap with your picking hand. An
   open chord rings 5–10 seconds; that's plenty.
2. **Hands-free, and the better test.** Set up virtual MIDI early and let a delayed command fire
   the switch while you play:
   ```bash
   sudo ./pipedal-setup.sh midi     # once
   # bind CC 20 → next snapshot in Settings → System MIDI Bindings, then:
   sleep 5; amidi -p hw:2,0 -S "B0 14 7F"
   ```
   Hit enter, pick up the guitar, strum — it switches at 5 seconds with both hands on the neck.

**If your ears aren't sure:** record the amp on your phone and look at the waveform. A 20 ms
dropout is obvious as a dip, and far more reliable than trying to catch it live.

```
        Does swapping the NAM model in a snapshot glitch?
                            │
        ┌───────────────────┴───────────────────┐
      CLEAN                                CLICK / DROP
        │                                       │
   ── DESIGN A ──                          ── DESIGN B ──
   1 NAM instance                          3 NAM instances
   model swaps per snapshot                snapshots toggle bypass
   ~1× NAM CPU                             ~3× NAM CPU
   try A2 Full first                       A2 Lite only
   Pi 4: comfortable                       Pi 4: marginal
   → build it out                          → likely need a Pi 5
        ▲
        │
   ◄── ACTUAL RESULT, 2026-09-04: the swap was CLEAN.
       Design A, as this tree hoped. 1 NAM + tuner + gate
       + cab sim + delay = 27% of one core, 50 °C, A2 Full.
       Design B never built — not needed.
```

**Pi 4 CPU reality check:** a Pi 4 is reported to handle ~two NAM instances (one standard +
one lite/feather) plus effects at 64/2. NAM A2 buys roughly one additional instance vs A1. The
big TooB NAM optimisations in v1.4.87 are **Cortex-A76 / Pi 5 only** — the Pi 4 doesn't get them.

> Design A is also what a future parallel blend would need (Phase 5) — another reason to expect it.
> Nothing to act on now.

**Design B escape hatch:** one NAM instance plus snapshot-switched drive/EQ/boost in front.
Three usable tones off one amp capture is how a real amp rig works anyway, and it's a fraction
of the CPU. Worth trying before spending on a Pi 5.

---

## 13. Phases 2, 3, 4 and 5

### Phase 2 — Build the structure

**Full walkthrough: [`pipedal-phase2.md`](../archive/pipedal-phase2.md).**

**Using:** phone (PiPedal UI) · guitar · amp · heatsink H0608 fitted to the Pi

**Design: A** — each preset holds **one** NAM instance; snapshots swap its `modelFile`. Verified
seamless on this rig. Snapshots also carry bypass and knob state for everything else in the chain.

- [x] Fit the heatsink — done 2026-09-04. **No re-baseline needed**: it was fitted before the
      Phase 1 measurements, so 50.1 °C / `0x0` already reflect it
- [ ] *(Optional, deferred by choice — 64×3 latency feels fine)* Push buffers to 32×3, then 32×4
      before building the nine snapshots. Expect ~55% DSP load; you have the room
- [ ] Cab sim decision: **bypassed** into the amp's FX return, **on** for headphones. Bypass is
      stored *per snapshot*, so set it in all three and re-save each one
- [x] Confirm headless boot target — confirmed `multi-user.target`
- [ ] Nine preamp-only, no-cab **A2 Full** captures, gains set per capture **by ear** — *not* NAM Calibration (see `pipedal-phase2.md` §4)
- [ ] Three presets × three snapshots each, per §5, **Design A** — one NAM per preset,
      identical plugin graph in all three presets, drive **before** the NAM
- [ ] Level-match all nine snapshots at playing volume
- [ ] Re-measure CPU on the *full* chain; keep the busiest snapshot under ~70%
- [ ] Settle the §15 open question — direct "snapshot N" binding or next/prev only? It decides
      the Phase 3 footswitch layout
- [ ] Hotspot tested at home, then set back to its normal trigger
- [ ] Back up `/var/pipedal` + `/etc/pipedal/config` off the Pi

### Phase 3 — Footswitch

**Using:** laptop (SSH + flashing) · Pi · Pico H · 6× S1152A switches · hookup wire ·
USB-A→micro-USB B **data** cable · soldering iron (switch lugs only — the Pico H has headers,
so jumper wires push straight on)

**Code inventory for the whole project:** Phases 0, 1, 2 and 4 involve **no code you write** —
packaged software and shell commands only. The only program in this build is `code.py` on the
Pico, about 40 lines. Everything below is that, plus the shell used to test it.

#### 13.A MIDI bytes — the 60-second primer

Every message is a status byte plus data bytes, written in hex:

| Message | Bytes | Notes |
|---|---|---|
| Program Change | `C0 nn` | `nn` = program **0–127** |
| Control Change | `B0 cc vv` | `cc` = controller, `vv` = value |
| Note On | `90 nn vv` | |

The **low nibble of the status byte is the channel**: channel 1 = `C0`, channel 2 = `C1`, …
channel 16 = `CF`.

> **Off-by-one trap:** program numbers on the wire are 0–127, but UIs usually *display* 1–128.
> "Preset 1" is very often `C0 00`, not `C0 01`. If everything lands one preset off, this is why.

We'll use **CC 20–26**. Those are undefined/general-purpose in the MIDI spec, so nothing else
will fight us for them.

> ⚠️ **The table below is superseded** by the settled 10-switch layout
> (handoff §5a). CC 20–26 is still the right range, but the assignments changed:
>
> | CC | Switch | Binds to |
> |---|---|---|
> | 20–25 | S1–S3 across two pages | **snapshot 1–6** — direct select |
> | 26 | MUTE | **TooB Tuner `MUTE`** (per-plugin binding, ×6 presets) |
> | — | P1–P3 across two pages | **Program Change 0–5** — no binding needed |
>
> Two changes of substance: the preset row uses **absolute Program Change**
> rather than next/prev preset, which is what makes the paging drift-proof; and
> the tuner needs **one** CC, not two, because TooB Tuner has its own `MUTE`
> port (§13.G correction).
>
> **Never assign CC 0** — `B0 00 vv` is MIDI Bank Select and would switch you
> into `Factory Presets`.

| CC | Switch | Binds to |
|---|---|---|
| 20 / 21 / 22 | 1 / 2 / 3 | snapshot 1 / 2 / 3 |
| 23 / 24 | 4 / 5 | next / previous preset (bank) |
| 25 | 6 | TooB Tuner plugin enable |
| 26 | 6 | output gain → −inf (mute) |

#### 13.B Prove the MIDI layer with no hardware

> ## ⚠️ THIS SECTION IS WRONG — corrected 2026-09-06
>
> **Do not follow the two-port / `aconnect` recipe below.** It does not work on
> PiPedal 2.x and it fails *silently*, with no error anywhere. It cost most of
> a session.
>
> The first paragraph below is correct. The conclusion drawn from it is not:
> **virmidi does not forward sequencer-in to that port's sequencer-out
> subscribers.** Events sent to `0-1`'s sequencer port become readable at the
> **rawmidi** device `hw:0,1` — so step 4's `amidi -p hw:0,1 -d` check *passes*
> and the transport looks proven — but a **sequencer** client subscribed to
> `0-1` receives nothing. PiPedal 2.x reads MIDI through the ALSA sequencer
> (`AlsaSequencer::ReadMessage`, called from `AlsaDriver::ReadMidiData`,
> `src/AlsaDriver.cpp:1706`), so it is a sequencer client, and it got nothing.
>
> Proved by subscribing `aseqdump` to each port in turn: `16:0` received the
> CC, `17:0` received nothing.
>
> ### What to do instead
>
> **Use ONE port for both ends. No `aconnect` at all.**
>
> ```bash
> sudo modprobe snd-virmidi
> amidi -l                                  # note the card number - it drifts
> # PiPedal -> Settings -> Select MIDI input = "Virtual Raw MIDI <card>-0"
> amidi -p hw:<card>,0 -S "C0 00"           # write to the SAME port
> ```
>
> **Verify delivery objectively — do this before trusting your ears.** PiPedal's
> sequencer client is 128 and its input pool counts every event delivered:
>
> ```bash
> cat /proc/asound/seq/clients | sed -n '/Client 128/,/^Client 129/p'
> ```
>
> `Alloc success` increments once per delivered event. **`aconnect -l` showing a
> subscription is NOT proof of delivery** — that is precisely what misled us.
>
> Two further traps found the same day:
> - **Persisting `snd-virmidi` in `/etc/modules` renumbers your cards.** It
>   loads before USB enumeration, so virmidi took card 0 and the UMC204HD moved
>   to 4. Audio was fine (stored by name), but **the MIDI device is stored with
>   the card number baked into the name**, so it broke silently on reboot.
> - **Snapshot bindings must be "Trigger on any value".** Rising edge fires
>   once and then never again — see §13.F's correction.
>
> `pipedal-setup.sh midi` is fixed and now does the right thing.
> Handoff §6.18–19 has the full write-up.

**Using:** laptop (two SSH windows) · phone (PiPedal UI). *No Pico or switches yet.*

`snd-virmidi` creates four virtual MIDI devices. Each bridges a rawmidi device to the ALSA
sequencer: **write** to a virmidi rawmidi device and it comes out that device's sequencer port;
sequencer events sent **to** that port become readable at the rawmidi device.

~~So we use two of them — send on port 0, have PiPedal listen on port 1, and wire 0 → 1.~~
**Wrong — see the correction above. Use one port.**

```bash
# 1. Create the virtual ports
sudo modprobe snd-virmidi

# 2. See what appeared — note the card number, it varies with what else is plugged in
amidi -l
```

Expect something like:

```
Dir Device    Name
IO  hw:2,0    Virtual Raw MIDI 2-0
IO  hw:2,1    Virtual Raw MIDI 2-1
IO  hw:2,2    Virtual Raw MIDI 2-2
IO  hw:2,3    Virtual Raw MIDI 2-3
```

```bash
# 3. Wire port 0 → port 1 through the sequencer
aconnect -l                                                   # list clients & numbers
aconnect 'Virtual Raw MIDI 2-0':0 'Virtual Raw MIDI 2-1':0    # or use the numeric IDs
```

**4. Prove the transport works before involving PiPedal at all.** Two terminals:

```bash
# Terminal A — listen
amidi -p hw:2,1 -d

# Terminal B — send
amidi -p hw:2,0 -S "C0 00"
```

Terminal A should print `C0 00`. **If it doesn't, stop here** — fix the plumbing before blaming
PiPedal. If `aconnect` won't cooperate, skip virmidi entirely and plug in any USB MIDI keyboard;
the rest of the phase is identical.

**5. Point PiPedal at it.** `Settings → MIDI`, select **Virtual Raw MIDI 2-1** as the input, then
configure `Settings → System MIDI Bindings`. Fire messages from Terminal B and watch the UI
respond in real time.

Persist the module across reboots:

```bash
echo snd-virmidi | sudo tee -a /etc/modules
```

#### 13.C A test script for all six switches

> ⚠️ **Superseded twice over.** The script below is the old 3-snapshot +
> bank±/tuner map and its `PORT="hw:2,0"` card number is stale.
> `miditest-10sw.sh`, written 2026-09-06 to replace it, tested the 10-switch
> layout that was itself superseded by the current 6×6 `pico-footswitch-v2`
> design (`pipedal-hardware-v2.md`) — it's been moved to `archive/` as of
> 2026-09-12, since its own setup instructions rely on the broken virmidi
> port-wiring that handoff §6.18 disproves.
>
> No dedicated test script exists yet for the current design's full CC/PC
> mapping. Absolute Program Change and CC20 (snapshot force) were bench-tested
> manually via `amidi -p hw:0,0 -S "C0 00"` etc. on 2026-09-12 — see
> `pipedal-hardware-v2.md` §5.1 and `pipedal-session-handoff.md` §6.27-28.
> (Note: `mido`/`python-rtmidi` do **not** work for this against `snd-virmidi`
> — use `amidi -S` directly.)
>
> **Run `snapshots` twice.** A second pass that does nothing means the bindings
> are on "Trigger on rising edge" — see §13.F.

Save as `~/miditest.sh`, then `chmod +x ~/miditest.sh`:

```bash
#!/usr/bin/env bash
# Fire each footswitch message in turn, 2s apart.
# Watch the PiPedal UI on your phone and confirm each one does what you expect.
PORT="hw:2,0"          # adjust to match your `amidi -l` output

send() {
    printf '%-16s %s\n' "$1" "$2"
    amidi -p "$PORT" -S "$2"
    sleep 2
}

send "SW1 snapshot 1" "B0 14 7F"    # CC 20
send "SW2 snapshot 2" "B0 15 7F"    # CC 21
send "SW3 snapshot 3" "B0 16 7F"    # CC 22
send "SW4 bank up"    "B0 17 7F"    # CC 23
send "SW5 bank down"  "B0 18 7F"    # CC 24
send "SW6 tuner ON"   "B0 19 7F"    # CC 25
send "SW6 mute ON"    "B0 1A 7F"    # CC 26
send "SW6 tuner OFF"  "B0 19 00"
send "SW6 mute OFF"   "B0 1A 00"
```

`./pipedal-setup.sh miditest` fires exactly this sequence.

Once all five do the right thing, the Pico just has to reproduce these exact bytes.

#### 13.D Wiring the Pico

**Using:** Pico H · 6× S1152A · hookup wire · jumper wires · soldering iron for the switch lugs.
*Pi not involved at this step.*

> ⚠️ **It's 10 switches now, not 6** (handoff §5a). The wiring *principle* below
> is unchanged — every switch shorts a GP pin to GND, internal pull-ups, no
> resistors — but the pin list is:
>
> | Pins | Switches |
> |---|---|
> | GP2, GP3, GP4 | P1, P2, P3 (preset row) |
> | GP5, GP6, GP7 | S1, S2, S3 (snapshot row) |
> | GP8, GP9 | PAGE ▲, PAGE ▼ |
> | GP10, GP11 | RESET, MUTE |
> | GP15 *(optional)* | page LED — anode → 330 Ω → pin, cathode → GND |
>
> **Two things do NOT go on the Pico:**
> - **The power button** wires to the **Pi's** GPIO3 and GND — header pins 5
>   and 6 — with `dtoverlay=gpio-shutdown`. That gives shutdown *and* wake from
>   halt, and GPIO3 is the only pin that can wake a halted Pi 4. It cannot be a
>   MIDI switch: the Pico is powered from the Pi, so it's dead when the Pi is
>   off. **Must be momentary, not a latching toggle** — a held-low line stops
>   it booting.
> - **The power LED** likewise goes to a Pi GPIO:
>   `dtoverlay=act-led,gpio=19` + `dtparam=act_led_trigger=default-on` gives
>   solid-while-running, dark-when-halted. `act-led` is *required* on a Pi 4B.
>   Do **not** use `gpio-poweroff` — it disables GPIO3 wake and demands an
>   external power-cut circuit.
>
> Cost with 10 switches: **~$112** (10 × S1152A @ $9.15 = $91.50, Pico H $15,
> wire, plus ~$3 for the GPIO3 momentary button).

Switches short the pin to GND; internal pull-ups mean the pin reads HIGH idle, LOW when stomped.
No resistors, no extra parts.

```
        Raspberry Pi Pico
        ┌────────────────┐
   USB ═╡                │
        │   GP2 ●────────┼──[SW1]──┐
        │   GP3 ●────────┼──[SW2]──┤
        │   GP4 ●────────┼──[SW3]──┤
        │   GP5 ●────────┼──[SW4]──┼── all switch commons
        │   GP6 ●────────┼──[SW5]──┤   tied together to GND
        │   GP7 ●────────┼──[SW6]──┘
        │   GND ●────────┼─────────┘
        └────────────────┘
```

#### 13.E Flashing CircuitPython

**Using:** Windows laptop · Pico · USB-A→micro-USB B **data** cable

1. Download the CircuitPython `.uf2` for Raspberry Pi Pico from circuitpython.org
2. Hold **BOOTSEL**, plug the Pico into USB → an `RPI-RP2` drive appears
3. Drag the `.uf2` onto it → it reboots as a `CIRCUITPY` drive
4. Download the Adafruit CircuitPython Bundle, copy the **`adafruit_midi/`** folder into
   `CIRCUITPY/lib/`
5. Save `code.py` (below) to the root of `CIRCUITPY` — it runs the moment you save

#### 13.F `code.py`

Full file: [`pico-footswitch-code.py`](./pico-footswitch-code.py) — save it to `CIRCUITPY/code.py`.

> ⚠️ **`code.py` was rewritten 2026-09-06** for the 10-switch 2-page layout. The
> config table below no longer exists. The old 5-switch file is kept as
> `pico-footswitch-code.py.5switch-orig`. Read the header of the current file —
> it documents the whole layout and both traps.
>
> **What changed, and why it matters:**
>
> - **No `toggle` flag any more.** Every switch sends a plain 127 and never a
>   release. Toggling is done *host-side*: bind with **"Trigger on any value"**
>   (system) or **"Toggle on any value"** (per-plugin).
> - **This is not optional.** `SystemMidiBinding::IsTriggered`
>   (`src/AudioHost.cpp:344`) does
>   `value >= 0x64 && lastControlValue < 0x64`, storing `lastControlValue`
>   every time. With a pedal that only ever sends 127, **"rising edge" fires
>   exactly once and is then dead forever.** This is the single most likely way
>   to waste an afternoon on working hardware.
> - **The preset row sends `ProgramChange`, not CC.** Absolute, 0-based,
>   clamped. No binding, no host state, no drift.
> - **The Pico holds one page bit** — and that's safe, because every message it
>   sends is an absolute destination. §13.H's warning about state in the pedal
>   applies to *relative* stepping, which this design does not use.
> - **RESET gaps its two messages** by `RESET_GAP_S` (0.6 s, a guess until
>   `./miditest-10sw.sh reset` is run) to stay out of the deferred-MIDI window
>   — see the note in §13.G's correction and handoff §6.26.

~~The whole configuration is one table at the top:~~ *(superseded)*

```python
# (pin, (CC numbers to send), toggle?, label)
#
#   toggle=False -> sends 127 on every press   (triggers: next preset etc.)
#   toggle=True  -> alternates 127 / 0          (on-off: tuner + mute)
SWITCHES = (
    (board.GP2, (20,),   False, "snapshot 1"),
    (board.GP3, (21,),   False, "snapshot 2"),
    (board.GP4, (22,),   False, "snapshot 3"),
    (board.GP5, (23,),   False, "bank up"),
    (board.GP6, (24,),   False, "bank down"),
    (board.GP7, (25, 26), True, "tuner + mute"),
)
MIDI_CHANNEL = 1
DEBOUNCE_S = 0.03       # raise if a stomp registers twice
```

Everything else is debounce and edge detection. To change what a switch *does*, rebind the CC in
PiPedal — don't reflash.

**Watch it work:** the `print()` output goes to the CircuitPython serial console. From the Pi:

```bash
amidi -l                        # the Pico should now appear as a USB MIDI device
screen /dev/ttyACM0 115200      # or: tio /dev/ttyACM0
```

Then point PiPedal's MIDI input at the Pico instead of the virmidi port. The bindings from 13.B
carry straight over — same CCs.

#### 13.G Switch 6: tuner and mute

> ⚠️ **Simpler than this — corrected 2026-09-06.** This section's own advice
> ("check whether TooB Tuner has its own mute control first") was the right
> instinct: **it does.** `ToobTuner.ttl:77` declares
> `lv2:symbol "MUTE"`, `lv2:toggled`, 0–1, default 0.
>
> So **one CC on one control does the whole job.** Drop CC 26's gain trick and
> the two-CCs-from-one-press mechanism entirely:
>
> | Field | Value |
> |---|---|
> | Dialog | **Settings → MIDI Bindings** — the *per-plugin* one, not System |
> | Plugin / control | TooB Tuner → `MUTE` |
> | Binding type | Control, **CC 26** |
> | Toggle type | **"Toggle on any value"** |
>
> **Three things to know:**
>
> 1. **It is per-preset, not global.** `midiBindings_` is a field on
>    `PedalboardItem` (`src/Pedalboard.hpp:94`), so it lives *inside* the
>    preset — **create it in all six.** Snapshots don't store bindings, so it
>    survives snapshot changes.
> 2. **Any snapshot change un-mutes you.** Every snapshot in the bank stores
>    `MUTE: 0` (checked, all 26), and `ApplySnapshotValue()` merges snapshot
>    control values over live ones. Structural, not a settings bug. Arguably
>    fine behaviour — "stomp a snapshot to leave the tuner" — but you cannot
>    mute, change snapshot, and stay muted.
> 3. **The tuner readout is only in the web UI.** The footswitch gives you a
>    silent stage mute; the needle is on your phone. Until the §13.I LED work
>    happens, treat that switch as a mute first and a tuner second.
>
> Mute lands pre-everything (the tuner is item 1 in all six presets), so
> delay and reverb tails ring out and decay rather than cutting dead — usually
> the nicer behaviour.
>
> Handoff §6.25 has the full write-up.

~~PiPedal has **no system MIDI binding for the tuner and no global mute.**~~ That part is still
true — but it doesn't matter, because the plugin has its own `MUTE` control. The tuner is a plugin
(**TooB Tuner**), so you build this from the same parts as everything else — plugin bypass and a
gain control.

**Chain placement:**

```
[TooB Tuner] → [Gate] → [TooB NAM] → [Drive] → [Delay] → [Gain]
      ▲                                                    ▲
  early: sees raw guitar                          late: muting kills
  regardless of what's                            the whole chain
  bypassed downstream
```

Switch 6 sends **two CCs from one press** — CC 25 to enable TooB Tuner, CC 26 to pull the gain to
−inf — and alternates 127/0 so a second press exits. That's the payoff for building your own
controller; most commercial ones can't send two messages from one switch.

Two alternatives if that gets awkward:

- **Check whether TooB Tuner has its own mute control first.** Plenty of tuner plugins do. If so,
  one CC does everything and you can drop CC 26.
- **A dedicated "Tune" snapshot** with tuner on and gain at zero. Elegant, but it costs a snapshot
  slot in *every* preset and you only get six per preset.

#### 13.H Variant: if PiPedal needs absolute preset numbers

The design above is a **dumb pedal, smart host** — five CCs, all meaning assigned in PiPedal.
That works because PiPedal has *relative* bindings (next/previous snapshot, next/previous preset),
so nothing needs to track state.

If it turns out PiPedal can only select presets by absolute number, the Pico has to count. Swap
the send block for:

```python
from adafruit_midi.program_change import ProgramChange

SNAPSHOTS_PER_BANK = 3
NUM_BANKS = 4
bank = 0

# ... inside the falling-edge branch:
if i < 3:                                   # SW1-3: absolute preset
    midi.send(ProgramChange(bank * SNAPSHOTS_PER_BANK + i))
elif i == 3:                                # SW4: bank up
    bank = (bank + 1) % NUM_BANKS
else:                                       # SW5: bank down
    bank = (bank - 1) % NUM_BANKS
```

Prefer the dumb-pedal version wherever possible. State in the pedal is state that can drift out of
sync with the host — stomp bank-up while PiPedal is on a different preset and the two disagree
with no way to resolve it.

#### 13.I Remaining

- [ ] LEDs for current-snapshot indication (needs the Pico to *receive* MIDI, not just send)
- [ ] Enclosure

Note the UMC204HD has **MIDI DIN in/out** on the back, so a DIN controller is a valid alternative
to USB MIDI if you'd rather go that way.

**If you'd rather buy than solder** (AUD):

| Controller | AUD |
|---|---|
| MeloAudio MIDI Commander | $159–249 (Amazon AU, fluctuates) |
| Nektar Pacer | $399 (Mega Music) |
| Morningstar MC6 MkII | ~$320–350 used, Reverb AU |
| Morningstar MC6 Pro | $619 |

---

### Phase 4 — Fit the HAT

**Using:** Pi · Pisound · input buffer + 9V supply · shielded cable · low-profile heatsink · laptop (SSH) · phone. *UMC204HD kept as the rollback.*

**Do not start this until Phases 0–3 work end to end.** This phase changes the one component
every measurement depends on, so everything else must be a known-good baseline first.

#### 13.1 Before you buy — three checks

1. **Board revision.** Pisound needs **v1.1+** for Pi 4, **v1.2** for Pi 5. Confirm before ordering.
2. **Cooling clearance.** The HAT sits on the 40-pin header directly over the SoC. **Your Phase 2
   heatsink probably won't fit underneath.** Budget for a low-profile heatsink. That Blokas
   specifically calls out "v1.2 supports Pi 5 *with Active Cooler*" tells you clearance is a real
   constraint they had to design around.
3. **Record your baseline.** Before anything comes apart, write down current buffer size, latency,
   CPU at 3 NAM instances, and temperature. Without this you can't prove the HAT helped.
4. **Order an input buffer at the same time.** Pisound's input is 100 kΩ, not the ~1 MΩ your
   UMC204HD gives you. See the buffer note under 13.3 — buy it in the same order so you're not
   waiting twice.

```
        PHYSICAL STACK — check this fits before ordering

        ┌─────────────────────────────────────┐
        │        Pisound HAT                  │  ¼" jacks + MIDI DIN
        │                                     │  face outward
        └──┬───────────────────────────────┬──┘
           │ 40-pin header      standoffs  │
        ┌──┴───────────────────────────────┴──┐
        │   ▓▓▓ low-profile heatsink ▓▓▓      │  ← tall heatsink or
        │        Raspberry Pi 4               │     Active Cooler
        └─────────────────────────────────────┘     will NOT fit
```

> The HAT's female socket swallows all 40 GPIO pins. Irrelevant here — PiPedal binds to MIDI, not
> GPIO, so the footswitch was always going to be a MIDI device.

#### 13.2 Install

**Using:** Pi powered OFF · Pisound · standoffs · laptop (SSH) once it's back up

Power off, seat the HAT on the header, secure with standoffs. Then:

```bash
curl https://blokas.io/pisound/install.sh | sh
sudo pisound-config
```

> That's Blokas' official method. If piping curl to a shell bothers you, download and read
> `install.sh` first — it sets up their APT repo and installs the packages.

**You may not even need it.** Per the Blokas docs, "the Audio and MIDI functionality should work
even without The Pisound Software installed, as the driver is integrated into the Linux Kernel."
The package adds the `pisound-btn` daemon (the user button) and `pisound-config`. PiPedal only
needs the kernel driver.

Verify:

```bash
aplay -l         # pisound should be listed
arecord -l       # pisound must be here, or nothing works
amidi -l         # the DIN MIDI ports should appear
```

#### 13.3 Target signal chain

```
   Guitar
     │ ¼" TS
     ▼
 ┌──────────────┐
 │ Input buffer │  ← presents 1 MΩ to the pickup, outputs low Z
 └──────┬───────┘     shielded cable, own 9V supply
        ▼
 ┌──────────────────────────────────────────────┐
 │  Pisound HAT                                 │
 │    IN  ......... 100 kΩ, gain knob 0–+40 dB  │
 │    MIDI DIN IN ◄──────────── footswitch      │
 │    OUT ......... 0–2.1 V RMS                 │
 └───┬──────────────────────────────────┬───────┘
     ║ 40-pin header (I²S — no USB)     │ standard 1/4" cable
     ▼                                  ▼
 ┌─────────────────────┐        ┌──────────────────────┐
 │  Raspberry Pi 4     │        │  Amp FX RETURN       │
 │   • low-profile HS  │        │  (power amp in)      │
 │   • PiPedal         │        └──────────────────────┘
 └─────────┬───────────┘
           │ wifi / hotspot
           ▼
     Phone browser → PiPedal web UI

   No USB audio. No USB MIDI. No separate box. One stack.
```

**The input buffer — why, and the rules**

Pisound's input is **100 kΩ**. A passive pickup wants ~1 MΩ (which your UMC204HD's INSTR switch
already gives you). At 100 kΩ you lose a little top end and presence. A unity-gain buffer in front
presents 1 MΩ to the guitar and drives a low impedance into the HAT, making the 100 kΩ irrelevant.

**Don't design the circuit — use a proven one.** AMZ MOSFET buffer, Klon-style buffer or a simple
JFET buffer all have published, tested schematics and available PCB kits. A 9V buffer kit is far
more likely to work first time than something improvised.

| | |
|---|---|
| Component cost | a few dollars |
| **Realistic project cost** | **$20–40** with shielded cable, connectors and a clean supply |

Two things that will make it *worse* if you get them wrong:

- ⚠️ **Don't power it from the Pi's 5V rail.** Switching noise goes straight into your signal path.
  Give it its own 9V supply inside the enclosure.
- ⚠️ **Shield the input wiring and keep the buffer away from the Pi.** A 1 MΩ input is an antenna
  for digital hash.

**A/B it when you fit it** — straight into the Pisound vs through the buffer. Into EL34s and
Celestions, which roll off hard above ~5 kHz, you may not hear much. Worth knowing either way.

#### 13.4 Updated infrastructure

Only the two edges change — everything in the middle is identical:

```
┌─ Raspberry Pi 4 ── 64-bit Raspberry Pi OS bookworm ────────────────┐
│                                                                    │
│  systemd                                                           │
│   ├── pipedald ................. unchanged                         │
│   │    ├── embedded web server ............... :80                 │
│   │    ├── WebSocket event bus                                     │
│   │    ├── LV2 plugin host (TooB NAM, effects)                     │
│   │    └── realtime audio thread                                   │
│   │           │                                                    │
│   │           └─► ALSA ─► I²S ─► Pisound      ◄── WAS: USB ─► UMC  │
│   │                                                                │
│   └── pipedaladmind ............ unchanged                         │
│                                                                    │
│  ALSA MIDI in ◄── DIN-5 on the HAT            ◄── WAS: USB MIDI    │
│                                                                    │
│  (+ pisound-btn daemon, optional — the user button)                │
└────────────────────────────────────────────────────────────────────┘
```

#### 13.5 Reconfigure PiPedal

- [ ] `Settings → Audio Device Settings` → select **pisound**
- [ ] **Push the buffers down.** You couldn't before; now try **32×4**, then **16×4**
- [ ] Re-check the input channel — it's a different card, don't assume
- [ ] Set the Pisound gain knob for peaks around -6 dB (with the buffer in circuit)
- [ ] A/B the buffer in vs out — record whether you can actually hear it
- [ ] **Re-set your input gain staging.** The entire input path has changed, so every capture's
      Input Gain needs revisiting (this is gain staging, not the NAM Calibration feature — §4 of
      `pipedal-phase2.md`)
- [ ] Re-verify temps with the new low-profile heatsink under a HAT (less airflow than bare board)

#### 13.6 Move the footswitch to DIN (optional)

| | **Keep Pico on USB** | **Move to MIDI DIN** |
|---|---|---|
| Work | None — it already works | Add a DIN-5 socket + resistors to the Pico |
| Result | One USB cable remains | Zero USB. Also opens up any commercial DIN controller |

No wrong answer. Keeping USB is free and the cable is hidden inside the enclosure anyway.

#### 13.7 Verify — fill this in

| | Baseline (UMC204HD) | After (Pisound) |
|---|---|---|
| Buffer | | |
| Round-trip latency | | |
| CPU @ 3 NAM | | |
| Temp under load | | |
| `get_throttled` | | |

#### 13.8 Rollback

Cheap and easy, which is why you keep the UMC204HD:

1. Plug the USB interface back in, reselect it in Audio Device Settings. Done — the HAT can stay
   physically fitted.
2. If the overlay itself misbehaves, comment out the `dtoverlay` line in
   `/boot/firmware/config.txt` and reboot.

---

### Phase 5 — Parallel amp blending (later, Pi 5 only)

**Using:** Pi 5 · everything from Phase 4. *Not part of the current build.*

**Not part of the current build.** Nothing in Phases 0–4 depends on this, and it needs hardware you
don't have. Recorded so the earlier phases don't paint you into a corner.

Running two amp sims in parallel means **both instances run constantly** — you're mixing them, not
switching between them. PiPedal handles the routing fine (Split nodes, plus a Channel Routing
dialog); CPU is the only limit.

Data point from the pi-stomp community: *"with a pi5, you should be able to run at least 2 NAM
instances."* So two parallel NAMs is roughly the **Pi 5 ceiling**, and beyond a Pi 4.

| | Instances always running | Verdict |
|---|---|---|
| Parallel blend + **Design A** (swap models per snapshot) | 2 | Feasible on a Pi 5 |
| Parallel blend + **Design B** (3 instances per bank) | 6 | Not happening on anything |

**What this means for the earlier phases:** only that Design A is the path that keeps this option
open. Design A is already the expected outcome for CPU reasons alone, so **there is nothing to do
differently now.**

When you get here:

- **Requires a Pi 5.** Not optional.
- Use **A2 Lite** — two Lite in parallel is far more achievable than two Full.
- Both captures share your EL34s and Celestions, so you're blending gain structures and EQ curves,
  not cabs and mics. Useful, but less dramatic than blending into an FRFR.
- Your output is **mono** — one cable to one FX return, so a parallel blend sums to mono before it
  leaves the Pi. Real stereo would need two amps (the UMC204HD does have Main Out L and R).

---

## 14. Gotchas

1. **MIX knob fully to PLAYBACK.** Anywhere toward INPUT and you'll hear dry analog guitar
   blended over the processed signal — thin, phasey, easy to misdiagnose as a PiPedal problem.
2. **Check the input channel.** Many two-input interfaces present the guitar on the *right*
   channel only.
3. **FX return, not the front input.** Into the front of the amp, the amp's preamp re-colours the
   capture and nothing sounds right.
4. **64-bit OS**, and **`apt-get`** not `apt` for the .deb.
5. **Go headless before measuring latency** — the GPU/desktop penalty is large.
6. **Watch temperature and under-voltage** — both silently corrupt your CPU measurements.
7. Boot time is ~30s+. No instant-on, no bypass on power loss. Fine for prototyping.

### Interfaces to avoid
ToneX One, Zoom GCE-3, Positive Grid RIFF — all crash PiPedal.
M-Audio M-Track Solo — terrible S/N (60 dBA).

---

## 15. Open questions

| Question | Status |
|---|---|
| Does a direct "go to snapshot N" MIDI binding exist, or only next/prev? | **RESOLVED — it exists.** `snapshot1`..`snapshot6` ("Snapshot 1".."Snapshot 6" in the UI), plus prev/next Snapshot *and* prev/next Preset. Verified in source: `src/Storage.cpp` (canonical list), `src/AudioHost.cpp` (dispatch), `vite/src/pipedal/SystemMidiBindingsDialog.tsx` (labels). Use the §10 primary layout |
| Is a snapshot NAM model swap audibly silent? | **RESOLVED 2026-09-04: YES, on this rig.** Preset `New`, one NAM instance, three snapshots differing only in `modelFile` — clean on a ringing chord and while picking. → **Design A** |
| Will 3 NAM instances fit on the Pi 4? | **Still unknown — and no longer relevant.** Design A works, so Design B was never built. The measured 27% is **one** instance; do not read it as three |
| Can the A2 slimmable size be selected? | **Open.** TooB NAM exposes a **`modelSize`** control (`0` in every snapshot), very likely the A2 submodel selector. §6's "drop to Lite" may therefore be reachable after all. Untested; irrelevant at 27% |
| Why did `./pipedal-setup.sh check` report "not installed"? | **RESOLVED + FIXED 2026-09-04.** `set -uo pipefail` combined with `grep -q`. grep exits on first match, `systemctl` then takes SIGPIPE and returns **141**, `pipefail` propagates that as the pipeline status, and the `if` reads it as failure. **A match is what caused the false negative** — which is why it never reproduced when the grep was run by hand. Fixed at lines 69 and 72: `grep -q X` → `grep X >/dev/null` so grep drains the pipe. Both copies patched, `check` now reports `pipedald active` / `pipedaladmind active` |
| Is PipeWire a problem? | Running on the Pi (3 processes). PiPedal opens ALSA `hw:U192k` directly and no glitching was observed, so it appears harmless. **Prime suspect if unexplained dropouts ever appear** |
| Does PiPedal enumerate `snd-virmidi` ports? | Likely (standard ALSA rawmidi), untested. Fallback: any USB MIDI keyboard |
| **Pisound Micro** (€69, ~$115) | **Checked.** Ships with *no connectors soldered* — the analog front end is your problem. But it has **12 analog + 25 digital GPIO** for pots and encoders with a mapper tool, so it could replace both the audio HAT and the Pico in a fully custom build. Input impedance not published |

---

## 16. Final shopping list

> ### ✅ RESOLVED 2026-09-04 — **Path A**, exactly as written
>
> Phase 1 came out the way this list hoped: **the model swap was clean, so Design A it is.**
> Design B was never built and isn't needed.
>
> **So: buy the Path A list. Ignore Path B.** Concretely —
> - **No Pi 5, no 27W PSU, no Active Cooler** (~$35 + board saved). Not needed to make the rig work.
> - **H0608 heatsink is correct and already fitted.** Path B's "except H0608" note doesn't apply.
> - **Audient iD4 ($285) is closed** — that was the "latency is the complaint" branch, and latency
>   isn't the complaint. Buffers were never pushed to their limit. It's also still a USB box.
> - **Powered USB hub closed** — no under-voltage.
> - **Remaining spend: Path A only, ~$76** (Pico H, 6× S1152A, shutdown button, wire).
>
> **Still live, deliberately deferred:**
> - **Audio HAT (Pisound ~$165)** — Phase 4, unchanged. Always a *portability and form factor*
>   decision, never a latency one; a USB box plus cable doesn't go in a pedal enclosure. Out of
>   stock, on the notify list.
> - **Pi 5** — roadmap, as an *expansion* option rather than a rescue: more headroom, the Pi 5-only
>   Cortex-A76 TooB NAM optimisations, and Phase 5 parallel blending.
>
> ⚠️ **Ordering trap:** decide the Pi *before* the HAT. Pisound needs board rev **v1.2** for a Pi 5
> (§13.1), so buying a HAT first can lock you out of the Pi 5 upgrade.

Branched, because Phase 1 decides which path you're on. **Nothing here is buyable until Phase 1
is done** except the Phase 0 row.

### Buy now — Phase 0/1

| Item | Where | AUD |
|---|---|---|
| microSD 32 GB, A2 | Officeworks / JB — **not** Altronics | $15–25 |

That's it. Phase 1 runs on the Pi 4 and UMC204HD you own.

---

### Path A — Pi 4 survives (Design A: 1 NAM instance)

| Item | Cat # / where | AUD |
|---|---|---|
| Pi heatsink 5 mm | Altronics **H0608** | $3.95 |
| Raspberry Pi Pico H | Altronics **Z6421B** | $15.00 |
| DPDT momentary footpad switch × 6 | Altronics **S1152A** | $54.90 |
| SPST momentary push button — shutdown/wake on GPIO3 | Altronics / Jaycar, cat # TBC | ~$3 |
| Hookup wire 26AWG | Altronics **W2250 / W2251** | ~$2 |
| **USB-A → micro-USB B** data cable (old Android phone cable) | have one? | – |
| **Subtotal** | | **~$76** |

*Optional, Phase 4 form factor:*

| Item | AUD |
|---|---|
| Blokas Pisound (out of stock — on notify list) | ~$165 |
| Input buffer kit + shielded cable + 9V supply | $20–40 |

---

### Path B — Pi 5 needed (Design B: 3 NAM instances)

Everything in Path A **except H0608** (passive won't hold on a Pi 5), plus:

| Item | AUD |
|---|---|
| Raspberry Pi 5 **4GB** | TBC — check Core Electronics / Little Bird |
| Official 27W USB-C PSU | $25.37 |
| Active Cooler | $9.95 |
| **Subtotal** | **~$35 + board** |

*Optional, Phase 4 form factor — note the extra mounting hardware:*

| Item | AUD |
|---|---|
| Blokas Pisound **v1.2** (Pi 5 requires v1.2) | ~$165 |
| Input buffer kit + shielded cable + 9V supply | $20–40 |
| GPIO riser / stacking header | ~$5 |
| 18–20 mm standoffs | ~$5 |

*Optional storage, Pi 5 only — NVMe is on PCIe so no audio contention:*

| Item | AUD |
|---|---|
| Pimoroni NVMe Base (mounts **underneath**, keeps GPIO free) | TBC |
| NVMe SSD | TBC |

---

### Don't buy

| Item | Why |
|---|---|
| Pico W (Z6424) | No WiFi needed — wired USB MIDI device |
| S1150A / S1155 switches | Latching, not momentary |
| A 7th footpad switch for shutdown | A stompable shutdown is a liability. Hand-operated button, back panel — `pipedal-phase2.md` §11a |
| Altronics microSD | High-endurance industrial, $79.95/32 GB |
| Official Pi 5 M.2 HAT+ | Mounts on top, fights the audio HAT for the header |
| USB SSD on a Pi 4 | Shares the VL805 controller with your audio |
| Raspberry Pi Codec Zero ($35.20) | Mic/line input, AUX via pin headers not sockets. Worse guitar input than the UMC204HD you own |
| Second heatsink for Phase 4 (Pi 4 path) | H0608 already clears a HAT |

---

## 17. Sources

- [PiPedal](https://rerdavies.github.io/pipedal/) · [Documentation index](https://rerdavies.github.io/pipedal/Documentation.html)
- [Installing PiPedal](https://rerdavies.github.io/pipedal/Installing.html)
- [Configuring After Installation](https://rerdavies.github.io/pipedal/Configuring.html)
- [Headless Operation](https://rerdavies.github.io/pipedal/HeadlessOperation.html)
- [Command-Line Configuration](https://rerdavies.github.io/pipedal/CommandLine.html)
- [PiPedal Architecture](https://rerdavies.github.io/pipedal/Architecture.html)
- [How to Debug PiPedal](https://rerdavies.github.io/pipedal/Debugging.html)
- [Optimizing Audio Latency](https://rerdavies.github.io/pipedal/AudioLatency.html)
- [An Intro to Snapshots](https://rerdavies.github.io/pipedal/Snapshots.html)
- [NAM Calibration](https://rerdavies.github.io/pipedal/NamCalibration.html)
- [Building Presets](https://rerdavies.github.io/pipedal/BuildingPresets.html)
- [Releases](https://github.com/rerdavies/pipedal/releases) · [source: Pedalboard.hpp](https://github.com/rerdavies/pipedal/blob/main/src/Pedalboard.hpp)
- [Audio interface compatibility #329](https://github.com/rerdavies/pipedal/discussions/329) · [Latency #201](https://github.com/rerdavies/pipedal/discussions/201)
- [NAM Types Guide: Nano, Feather, Lite & Standard](https://www.tone3000.com/blog/understanding-nam-types)
- [NAM A2: The Complete Guide](https://www.tone3000.com/guides/nam-a2-the-complete-guide)
- [PiPedal now supports TONE3000](https://www.tone3000.com/blog/pipedal-now-supports-tone3000)
- [Behringer UMC204HD on Linux (Ardour forum)](https://discourse.ardour.org/t/behringer-umc204hd-and-umc404hd/104756)
