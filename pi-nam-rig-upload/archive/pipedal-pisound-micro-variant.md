# Pisound Micro — variant, if you swap it in for the Pisound HAT

Applies against `pipedal-nam-rig-plan.md` §1.1 (Pisound decision) and §13.1 (electronics box
stack). Nothing about the footswitch box (`pipedal-hardware-v2.md`) changes — this only affects
the electronics box.

## 1. What it actually is

**Pisound Micro is a bare board, not a finished product.** Where the original Pisound ($165 AUD,
€99) is a complete, assembled HAT with ¼" jacks, gain/volume pots, a shutdown button, and MIDI
DIN sockets already mounted, Pisound Micro (€69, ~$115 AUD at similar conversion) is a stripped
component board aimed at people building custom audio hardware. Per Blokas' own docs: **"comes
with no headers pre-installed, to offer complete freedom for integration into your projects."**
That framing matters — you're not buying a cheaper Pisound, you're buying a different kind of
product that happens to solve the same ADC/DAC problem.

| | Pisound (original) | Pisound Micro |
|---|---|---|
| Price | ~$165 AUD (€99) | ~$115 AUD (€69) |
| Audio jacks | 2× ¼" TRS, pre-mounted | **None — bare pads, you solder your own** |
| Gain/volume control | Physical pots on the board | Software (ALSA mixer) only — no pot |
| Shutdown button | Built in (`pisound-btn` daemon, §7 of hardware-v2) | **None — you build your own** |
| MIDI I/O | 2× DIN-5, pre-mounted | 1×1, bare pads — DIN-5/3.5mm/2.5mm, your choice, your soldering |
| Codec | Burr-Brown, 192kHz/24-bit | Analog Devices ADAU1961, 96kHz/24-bit |
| Guitar/Hi-Z input | 100kΩ (borderline, §1.1 of main plan) | **Not specified anywhere in the docs** — looks line/aux-level oriented, not instrument-oriented |
| Mounting | Stacks on GPIO header only | GPIO header **or** 40-way ribbon cable **or** hand-wired — your choice |
| GPIO usage | Consumes pins for its own connectors | Passes all 40 pins through to a duplicate header — nothing lost |
| Maturity | Established, years in the field | Newer; Blokas' own copy says they're "thoroughly testing other boards" still |

## 2. What changes for this build

### 2.1 You become responsible for the analog front end
No jacks means no jacks — you pick ¼" TS/TRS connectors, wire them to Pisound Micro's input/output
pads by hand, and mount them in the electronics box panel yourself (vs. the original Pisound's
jacks being pre-positioned on the board edge, which mostly dictates where the panel cutout goes
for you).

**Likely a bigger problem than it looks:** the original Pisound's 100kΩ input was already called
out in the main plan (§1.1) as *instrument-friendly, not textbook Hi-Z*, and "any always-on
buffered pedal in front fixes it completely." Pisound Micro's spec sheet only lists **Line Input
gain (up to 35.25dB)** and **Aux Input gain (up to 6dB)** — nothing framed for a passive guitar
pickup at all. Treat an external buffer/DI in front of it as **required, not optional**, unless
you test otherwise. That buffer was already recommended for the original Pisound (§13.3 of the
main plan) — here it stops being a nice-to-have.

### 2.2 No hardware gain/volume knobs
The original Pisound has physical pots you can nudge by feel mid-set. Pisound Micro's gain is
codec-register-level, set through ALSA — meaning either you set it once during setup and leave
it, or you're opening the PiPedal web UI / SSH session to change it. Not a dealbreaker (PiPedal's
own input-gain-per-capture already lives in software, per the main plan's Phase 1/2), but it's one
more knob you lose the ability to nudge without a screen in front of you.

### 2.3 No shutdown button — you build one
The main plan's whole shutdown story (`pipedal-hardware-v2.md` §7) is "Pisound's own onboard
button handles this, one less part, one less hole to drill." Pisound Micro has no equivalent.
You'd need to add back:
- A momentary pushbutton, wired to a free GPIO
- The standard Raspberry Pi `gpio-shutdown` device-tree overlay (well-documented, standard Pi
  technique — not exotic, just an extra part and an extra hole in the enclosure)

This isn't a reliability risk — `gpio-shutdown` is a mainstream, well-trodden Pi feature — but it
undoes the "one less part" win the original Pisound gave you for free.

### 2.4 MIDI DIN — you can just skip it
Pisound Micro's MIDI needs its own connectors soldered on (DIN-5, or a 3.5mm/2.5mm TRS-MIDI
jack). **You probably don't need this at all.** Your entire footswitch chain is USB MIDI
(Pico → Pi, `pipedal-hardware-v2.md`), not DIN MIDI — the original Pisound's DIN ports were never
load-bearing for this build either. Leaving Pisound Micro's MIDI pads unpopulated is a legitimate
simplification, not a loss.

### 2.5 Mounting flexibility — genuinely useful here
This is the one place Pisound Micro is a clear upside. It can sit directly on the GPIO header like
a normal HAT, **or** be connected via a 40-way ribbon cable and mounted elsewhere in the box. The
main plan's electronics-box side view (`pipedal-hardware-v2.md` §8) already flags the Pi 5 +
Active Cooler + HAT stack as tight (~45-55mm used of 80mm internal height) and stresses "dry-fit
before drilling." Pisound Micro being cable-mountable means you could tuck it flat against a side
wall instead of stacking it on standoffs above the Active Cooler — this could ease that clearance
problem rather than fighting it. Whether it's worth the trade depends on how tight the dry-fit
turns out to be.

It also passes through all 40 GPIO pins to a duplicate header, so nothing here competes with the
shutdown-button GPIO from §2.3 or anything else you might add later.

## 2.6 Two mounting layouts, and what each one costs you to wire

**Option A — stacked, like the original Pisound.** Simplest to build, but inherits the same
tight-clearance problem the main plan already flagged for the Pi 5 + Active Cooler + HAT stack
(`pipedal-hardware-v2.md` §8, ~45-55mm used of 80mm internal height).

```
   OPTION A — stacked on the GPIO header (2x20, 2.54mm)

      ┌──────────────────────────────┐
      │      Pisound Micro           │  ← bare board, jacks wired off the edge
      └──────────────────────────────┘
           ▲ standoffs, tall enough to clear the Active Cooler
      ┌──────────────────────────────┐
      │   Active Cooler (fan)        │
      ├──────────────────────────────┤
      │      Raspberry Pi 5          │
      └──────────────────────────────┘

   Same clearance math as the original Pisound stack — no better, no worse.
   Jack wires run a short distance off the board edge to the panel.
```

**Option B — ribbon-mounted, off to the side.** The genuinely new option this variant unlocks
(§2.5) — trades a little more wiring for headroom in the vertical stack.

```
   OPTION B — 40-way IDC ribbon cable, board mounted flat against a side wall

      ┌──────────────────────────────┐
      │   Active Cooler (fan)        │  ← nothing stacked above the Pi at all
      ├──────────────────────────────┤
      │      Raspberry Pi 5          │──┐
      └──────────────────────────────┘  │ 40-way ribbon, GPIO header → duplicate
                                         │ header on Pisound Micro
      ┌──────────────────────────────┐  │
      │      Pisound Micro           │◄─┘  (flat against a side wall, own standoffs)
      └──────────────────────────────┘
             │        │           │
             ▼        ▼           ▼
        ¼" IN    ¼" OUT      shutdown button (§2.3)
        (via buffer/DI, §2.1)
```

Option B is the one worth dry-fitting first if the Active Cooler clearance is the thing worrying
you — it turns a height problem into a floor-space problem instead, which the 171×121mm
electronics box (`pipedal-hardware-v2.md` §8) may or may not have spare.

## 3. Does it make things less reliable or less sturdy?

**Not the board itself — the assembly around it.**

- **Enumeration/bus reliability:** identical story to the original Pisound. Both are I²S HATs, so
  neither has USB enumeration risk, bus contention, or bus-power draw concerns — the whole reason
  the main plan preferred a HAT over the UMC204HD (§1.1) applies equally to either Pisound
  variant.
- **Mechanical sturdiness is now on you.** The original Pisound's jacks, pots and button are
  factory-soldered onto a board designed to take the mechanical stress of cables being plugged
  and unplugged, and gigging vibration. With Pisound Micro, *you* solder the jacks to bare pads
  and *you* decide how they're strain-relieved and panel-mounted. Done carefully (jacks
  panel-mounted to the enclosure, not left hanging on wire alone; solder joints given strain
  relief) it can be just as sturdy — but that robustness is now a function of your build quality,
  not something you get by default from the part.
- **Field maturity is lower.** The original Pisound is an established product with years of user
  reports (which is how the main plan sourced its Pi 4/Pi 5 revision compatibility notes, §1.1).
  Pisound Micro is newer — Blokas' own product page says they're still "thoroughly testing other
  boards" for compatibility. Officially Pi 5 is listed as supported, but there's less accumulated
  field experience to lean on if something's odd.
- **Net:** no inherent reliability disadvantage in the silicon or the audio path. The risk this
  variant adds is entirely in the extra DIY assembly (jacks, MIDI connectors, shutdown button, Hi-Z
  buffering) — more places for a shortcut or a rushed solder joint to bite you later, compared to
  a finished product you just bolt on and plug in.

## 4. What you'd need to add to the shopping list

On top of what `pipedal-hardware-v2.md` §9 and the main plan's electronics-box list already cover
(Pi 5, Active Cooler, USB-C PSU), swap the Pisound line for:

| Qty | Part | Notes |
|---|---|---|
| 1 | Pisound Micro | €69 (~$115 AUD) |
| 2 | ¼" TS/TRS panel-mount jacks | For guitar in / amp out — pick to match the enclosure's ¼" IN/OUT cutout already planned |
| 1 | 2×20 header (2.54mm) **or** 40-way IDC ribbon cable | Mounting method, pick one (§2.5) |
| 1 | Momentary pushbutton, panel-mount | Replaces the onboard `pisound-btn` (§2.3) |
| — | Buffered pedal / DI, always-on ahead of the input | Treat as required, not optional (§2.1) — you may already own one, per the main plan's note on the original Pisound |
| — | Hookup wire, solder | For jack-to-pad and button-to-GPIO wiring |
| skip | MIDI DIN/3.5mm/2.5mm jacks | Not needed — USB MIDI already covers footswitch control (§2.4) |

Rough extra spend beyond the bare board: **$15-30 AUD** in jacks/button/header, plus whatever a
buffer pedal costs if you don't already own one — landing close to, or above, the original
Pisound's all-in price once assembly parts are counted, with meaningfully more soldering and
enclosure-design work in exchange for the lower board price and the mounting flexibility in §2.5.

## 5. Recommendation

Stick with the original Pisound unless you specifically want the extra 37 passthrough GPIOs, the
lower board price is what's blocking you, or the mounting flexibility turns out to solve a real
clearance problem once you dry-fit the electronics box. Pisound Micro is a legitimate part for a
custom audio-hardware project — but this build already has a from-scratch footswitch box, Pico
firmware, and an OLED to sort out. Pisound Micro adds a second from-scratch project (jacks, a
Hi-Z front end, a shutdown button) on the audio side too, for a part that isn't clearly cheaper
once you count what you have to add back.
