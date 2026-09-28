# PiPedal Footswitch Rig — Hardware Design v2

Supersedes §10 and §13.A–F of `presets-reference/pipedal-nam-rig-plan.md` for the physical control layout and Pico
firmware. Everything else in that file (audio chain, PiPedal internals, Phase 4/5) still applies.
Firmware itself lives in [`pico-footswitch-v2/`](./pico-footswitch-v2/), not inline in either doc.

## 1. Status

- **Software:** 6 presets × 6 snapshots, built and working. Snapshot switching over MIDI is
  tested. **Preset switching over MIDI is now tested too (2026-09-12)** — absolute Program Change,
  0-indexed, confirmed on the rig via `amidi -p hw:0,0 -S "C0 00"` etc. (bench, no Pico). See §5.1.
- **Hardware:** nothing bought yet except the Pi, wire, and a heatsink.

## 2. Footswitch box — physical layout

Two rows of 3 footswitches double as **preset select** or **snapshot select**, depending on
mode. PRESET/SNAPSHOT mode-select footswitches sit at the end of their respective row, each with
an indicator LED. RESET and TUNER/MUTE are pushed to the **back corners** (not clustered
top-left) — they don't need to be easy to hit mid-song, and moving them out to the corners frees
the whole back-center strip for the OLED without cramming the two against each other. Every
switch is the same type — momentary, no toggles.

Rows and mode-selects are now **spread across the full 222mm width** rather than bunched on the
left — more room between switches for a boot to land without clipping its neighbour, and it uses
the box's actual width instead of leaving the right-hand third empty.

```
┌───────┐                                                    ┌────────────┐
│ RESET │                                                    │ TUNER/MUTE │
└───────┘                                                    └────────────┘

                        ┌────────────────┐
                        │  OLED (2.42")  │   ← preset/snapshot name (+ tuner, §4.1)
                        └────────────────┘

   ┌────┐          ┌────┐          ┌────┐            ┌────────┐[LED]
   │ 1  │          │ 2  │          │ 3  │            │ PRESET │
   └────┘          └────┘          └────┘            └────────┘

   ┌────┐          ┌────┐          ┌────┐            ┌──────────┐[LED]
   │ 4  │          │ 5  │          │ 6  │            │ SNAPSHOT │
   └────┘          └────┘          └────┘            └──────────┘
```

### 2.1 Hole sizes and a drill layout — from the actual datasheets, not guesses

Pulled the real datasheets for the ordered parts (Tayda A-1874 footswitch, A-7502 OLED) instead
of estimating. One thing changed as a result: **the OLED's PCB is 72×43mm** — physically bigger
than the rough sketch above assumed room for. 43mm of depth is a lot to spend out of a 146mm-deep
box once you also need the back row and two switch rows, so the layout below is tighter,
front-to-back, than the original ASCII sketch implied. It still fits — see the numbers — but
there's less spare margin than "35mm for the OLED, 40mm between rows" suggested.

| Part | Hole | Source |
|---|---|---|
| Footswitch (A-1874), ×10 — includes RESET/TUNER-MUTE, same part | **⌀12mm**, M12×0.75 thread | Tayda's own dimension drawing (`A-1874.pdf`) |
| LED, ×2 | **⌀5mm** | Standard T1-3/4 LED body diameter |
| OLED (A-7502) mounting screws, ×4 | **⌀3mm**, at 68.0×38.8mm spacing (rectangle) | Tayda's product dimension diagram |
| OLED viewing cutout | **~58×30mm** rectangle | Sized a couple mm over the 55.01×27.49mm active area, staying inside the 62.1×39mm bezel frame so the plastic bezel covers the cut edges — don't cut exactly to the active-area size, there's no tolerance for a hand-cut edge at that size |

**Footswitch base — confirmed from the actual A-1874 datasheet** (`SF12N-0202-20R-M`, fetched
2026-09-12; Tayda's site returns 403 to most automated fetchers, but it's reachable directly). The
switch is NOT just a ⌀12mm round bushing — it has a **13.4×12.1mm square anti-rotation bezel** on
the **front/outside** face of the panel (around the cap, not inside the box), only marginally
bigger than the round hole (+0.7mm each side in X, +0.05mm in Y) so it doesn't change any spacing
conclusion, but it DOES tighten the PRESET/SNAPSHOT-to-LED clearance from the previously assumed
8mm to a confirmed **7.3mm edge-to-edge** (still fine — not re-flagging §2.1's LED-spacing fix,
just noting the real number). The bezel isn't keyed to the round hole, so each switch can be
rotated to whichever angle clears its neighbours best — orient PRESET's and SNAPSHOT's narrow
(12.1mm) side toward their LED for max margin. Also confirmed from the same drawing: cap ⌀10mm,
~8.5mm above the mounting surface (matches the ~9mm estimate already used); bushing M12×0.75,
13mm body (matches). **Nut/washer options, real numbers** (was a guess before): hex nut M12×0.75,
14mm across-flats (≈16.2mm across corners), 2mm thick; plain washer ⌀16mm OD, 0.5mm thick;
20-tooth washer same ⌀16mm; PA66 (plastic) washer ⌀18.8mm OD, 1.4mm thick; spring washer ⌀15.2mm
OD. Shown on `enclosure-templates/pipedal-footswitch-drill-template.svg` as a dashed square on every switch, and the
washer figure on `pipedal-footswitch-lid-underside-view.svg` is now this confirmed ⌀16mm plain-
washer number rather than an assumption — still check what actually shipped with your order,
since several washer types are offered.

**Coordinates below** — origin at the **back-left corner** of the panel, X across the 222mm
width (increasing rightward), Y front-to-back the 146mm depth (increasing toward the player).
Same caveat as ever: **these come from the box's nominal outer dimensions, not a measurement of
your actual lid** — diecast walls/corner radii typically eat a few mm of usable panel area.
Transfer this to a paper template cut to your panel's *actual* measured size, dry-fit every part,
and adjust before drilling anything.

| Part | X (mm) | Y (mm) |
|---|---|---|
| RESET | ~~20~~ **22** | 15 |
| TUNER/MUTE | ~~202~~ **198** | 15 |
| OLED mounting hole (×4) | 77 / 145 | 32.6 / 71.4 (all 4 combinations) |
| OLED viewing cutout, centered on | 111 | 52 |
| Switch 1 | 28.5 | 88 |
| Switch 2 | 83.5 | 88 |
| Switch 3 | 138.5 | 88 |
| PRESET mode button | 193.5 | 88 |
| PRESET LED | ~~210~~ **177** (moved left of PRESET, by request, purely for symmetry — see below) | 88 |
| Switch 4 | 28.5 (unchanged) | 128 |
| Switch 5 | 83.5 | 128 |
| Switch 6 | 138.5 | 128 |
| SNAPSHOT mode button | 193.5 (unchanged) | 128 |
| SNAPSHOT LED | ~~210~~ **177** (moved left of SNAPSHOT, by request, purely for symmetry — see below) | 128 |

**Corner-post fix, 2026-09-12** — the physical HB5050 chassis turned out not to be a hollow box:
each of the 4 corners has a full-height internal boss (floor to lid) for a lid-mounting screw,
confirmed by opening the actual enclosure, not from any datasheet. Went through several revisions
as measurements got more precise, **including one wrong diagonal assignment** — the first read of
"which corners have the big post" turned out to be described from a flipped viewing angle and had
it backwards. **Final numbers below**, re-confirmed against the fixed reference points (RESET/
TUNER-MUTE/SW4/SNAPSHOT) rather than ambiguous "top-left/bottom-right" language. The posts are
asymmetric **per corner (diagonal), not per side**:

| Corner | Hole | Post size | Zone |
|---|---|---|---|
| Back-left | RESET | Small: 11mm × 11mm | X:[0,11], Y:[0,11] |
| Back-right | TUNER/MUTE | Big: 13mm (X) × 22mm (Y) | X:[209,222], Y:[0,22] |
| Front-left | SW4 | Big: 13mm × 22mm | X:[0,13], Y:[124,146] |
| Front-right | SNAPSHOT | Small: 11mm × 11mm | X:[211,222], Y:[135,146] |

There's also a smaller secondary hole next to each post, running along the long (top/bottom)
edges — **confirmed not structural**, safe to drill through or grind away, so it isn't added to
the zones above. **The boundary alone isn't sufficient regardless** — a hole centered exactly on
the boundary still has its washer/body overhanging into the post. The real requirement is hole
center ≥ post size + washer radius (8mm, confirmed ⌀16mm plain washer) + a small buffer, cleared
via whichever axis the hole doesn't already clear (a corner post only blocks where its X-range AND
Y-range both overlap a hole's footprint):
- Big-post corners: ≥13+8+2 = **23mm**
- Small-post corners: ≥11+8+2 = **21mm**

**Net result, checked against every hole:**
- **RESET** (back-left, small post): Y=15 doesn't clear the small zone with buffer, but X does.
  Moved **20→22**.
- **TUNER/MUTE** (back-right, big post): needs X≤199. Moved **202→198**.
- **SW4** (front-left, big post): needs X≥23 — original X=28.5 already clears by 5.5mm.
  **Unchanged.**
- **SNAPSHOT** (front-right, small post): needs X≤201 — original X=193.5 already clears by 7.5mm.
  **Unchanged.**
- **Neither LED is actually forced to move.** SNAPSHOT's LED at X=210 doesn't reach into its
  (now small, 11mm) corner zone's Y-band at all — its footprint stops 4.5mm short of Y=135, so it
  clears regardless of X. That "must flip" conclusion only held under the earlier, incorrect
  diagonal assignment.

**Both LEDs moved anyway, by request, not by necessity** — kept at **X=177** (left of their
switch, 16.5mm spacing, same as originally chosen when the move looked forced) purely for visual
symmetry between the two rows: both now read SW-SW-SW-LED-mode-button. Functionally this is a
preference, not a requirement — X=210 (right side) would have worked equally well for both once
the diagonal was corrected.

**Side effects, checked:** row B is back to the original even 55.0mm SW4/SW5/SW6 spacing (matching
row A) since SW4 didn't move. Both rows' LED chain segments match: SW3/SW6-to-LED 38.5mm,
LED-to-mode-button 16.5mm.

**USB coupler position** (see §2.3a) — TUNER/MUTE moving to X=198 (a bit more than the 2mm first
thought, since it's now known to be on the big-post corner) still leaves a comfortable gap. It's
at **X=170**, its original position, with ~10mm/~9mm clearance to the OLED and TUNER/MUTE
respectively.

**Files updated with these positions:** `print-templates-v2/pipedal-footswitch-lid-print.svg` and
`print-templates-v2/pipedal-footswitch-backwall-print.svg` — diagram-only, print-ready, with the
corner-post danger zones shaded on the lid one. **Not yet updated:** the original standalone
templates (`enclosure-templates/pipedal-footswitch-drill-template.svg`,
`enclosure-templates/pipedal-footswitch-backwall-drill-template.svg`), the combined fold-over templates, the underside
view, and the internal elevation all still show the pre-corner-post positions — treat those as
stale until/unless they're regenerated to match.

**LED position corrected 2026-09-12** — was X=205 (11.5mm from the mode button, center-to-center).
Between a ⌀12mm switch hole and a ⌀5mm LED hole, that left only **3mm of metal web** between the
two hole edges (11.5 − 6 − 2.5), which is inside typical hand-drilling error (±0.5–1mm) and risks
the two holes breaking into each other or cracking the thin web. Moved to **X=210** (16.5mm
spacing), giving an **8mm web** — still close, but with real margin. Checked against the panel
edge too: 210 is 12mm from the X=222 edge, i.e. 9.5mm clear of the LED's own hole edge, comparable
to RESET/TUNER-MUTE's 20mm-from-corner margins. Nothing else on the layout moved as a result.

Gaps this leaves, so you can see where the slack (or lack of it) actually is: ~9mm clear between
the RESET/TUNER-MUTE row and the OLED's top edge; ~8.5mm clear between the OLED's bottom edge and
the switch bodies in row A; ~40mm pitch between row A and row B (unchanged from the original
plan); ~12mm clear from row B to the front edge. None of these are generous — this is a "measure
twice" enclosure, not one with room to eyeball it.

**These are still estimates, not measurements** — cut a paper template to the enclosure's actual
dimensions and dry-fit the switches and OLED before drilling, same caveat as the electronics-box
stack in §8.

### 2.2 Top view — every hole, to scale, with sizes and center-to-center spacing

**Use [`enclosure-templates/pipedal-footswitch-drill-template.svg`](./enclosure-templates/pipedal-footswitch-drill-template.svg) instead
of the ASCII sketch below for anything you're actually going to mark or drill from.** ASCII can't
be to true scale — text characters aren't square, so distances in a text diagram are only ever
approximate. The SVG is a real vector drawing at 1:1 mm scale: open it in a browser and print at
**100% / "actual size"** (not "fit to page"), then check the 50mm calibration bar it includes
against a ruler before trusting it — if that bar doesn't measure exactly 50mm, your printer
rescaled the page and the holes will be off. It has every hole at its true diameter and position,
plus the center-to-center dimensions (55.0mm between switches in a row, 16.5mm from a mode button
to its LED, 68.0×38.8mm OLED hole spacing, and the front-to-back spacing between rows) drawn
directly on it rather than left in a table you'd have to cross-reference by hand.

⌀ is the diameter symbol — `⌀12` means a 12mm-diameter hole, same notation used on the switch's
own datasheet.

**On measuring technique:** the SVG dimensions everything from the same fixed corner (0,0),
not hole-to-next-hole in a chain. That's deliberate — if you instead measure "55mm from switch 1
to switch 2, then another 55mm to switch 3," any small error in the first measurement carries
into every hole after it. Marking every hole from the same two reference edges (a ruler laid
along the back edge for X, another along the left edge for Y) keeps errors from compounding,
which matters more here than usual given how tight §2.1 already found this layout to be.

The ASCII version below is kept for a quick-reference overview only — not for marking anything.

```
 X→   0      22       77        111        145     177  193.5 198       222
 Y↓                     │          │          │
   0 ┌──────────────────────────────────────────────────────────────────┐ back edge
     │  ⌀12                                                      ⌀12    │
  15 │  (RESET)                                              (TUNER/MUTE)│
     │                                                                   │
     │              ⌀3 ●──────────68.0mm──────────● ⌀3                   │
  33 │                 │                           │                    │
     │                 │      ┌───────────────┐    │                    │
     │                 │38.8mm│  OLED cutout  │    │                    │
     │                 │      │   ~58 × 30mm   │    │                    │
  71 │                 │      └───────────────┘    │                    │
     │              ⌀3 ●───────────────────────────● ⌀3                  │
     │                                                                   │
     │  ⌀12         ⌀12        ⌀12         ⌀5      ⌀12                  │
  88 │ (SW1)        (SW2)      (SW3)      (LED)   (PRESET)              │
     │                                                                   │
     │  ⌀12         ⌀12        ⌀12         ⌀5      ⌀12                  │
 128 │ (SW4)        (SW5)      (SW6)      (LED)   (SNAPSHOT)            │
     │                                                                   │
 146 └──────────────────────────────────────────────────────────────────┘ front edge
                                                                    (player side)
```

(RESET/TUNER-MUTE/LED positions reflect the corner-post fix, §2.1 above — this ASCII sketch is not
to true scale, see `print-templates-v2/pipedal-footswitch-lid-print.svg` for the actual to-scale,
printed-and-punched template.)

Every hole size in one place:

| Hole | Diameter | Qty |
|---|---|---|
| Footswitches (RESET, TUNER/MUTE, SW1–6, PRESET, SNAPSHOT) | ⌀12mm | 10 |
| LEDs (PRESET, SNAPSHOT indicators) | ⌀5mm | 2 |
| OLED mounting screws | ⌀3mm | 4 |
| OLED viewing window | ~58×30mm rectangle | 1 |
| Preset-browse encoder (§4.2) | ⌀7.1mm | 1 |

**See also [`pipedal-footswitch-internal-elevation.svg`](./enclosure-templates/pipedal-footswitch-internal-elevation.svg)**
for a to-scale version of this side view — the footswitch understack, OLED, Pico, and USB coupler
all drawn to the same Y/Z scale with real dimensions, plus the clearances between them.

**Also see [`pipedal-footswitch-lid-underside-view.svg`](./enclosure-templates/pipedal-footswitch-lid-underside-view.svg)**
— the lid layout flipped front-to-back (X unchanged) to show the view from inside the box looking
up, with each footswitch's actual body/nut-washer footprint (⌀12mm solid, ⌀16mm typical washer
dashed) and the USB coupler's footprint projected from the back wall onto the same X-Y plan,
showing its 28.6mm protrusion and real (non-overlapping) clearance to TUNER/MUTE.

### 2.3 Side view — cross-section, panel to floor

Looking at the box from the side (through, say, the SW2/SW5 column), showing what's stacked
between the lid and the floor. Heights below are built from the A-1874 switch datasheet and the
A-7502 OLED module — **except panel/wall thickness, which Jaycar doesn't publish and I couldn't
pull from their site; typical diecast aluminium is 2–3mm, but measure yours before trusting the
clearance numbers below.**

```
                    ▲
     button cap    ~9mm    ┌──┐
     above panel    ▼     ┌┘  └┐          ← ⌀10mm cap, sits ~9mm above the panel
                          │ SW │            surface — this is your boot-clearance number
   ══════════════════════╧════╧══════════════════════  ← LID / drilled panel (thickness
                          │    │                          unconfirmed, ~2-3mm typical)
                    ▲     │M12 │
   nut + washer   ~3mm    │thd │
                    ▼     ├────┤
                          │    │
   switch body    ~13mm   │ SW │  "M" body from the datasheet
                    ▼     │body│
                          ├────┤
   solder lugs     ~4mm   │ ╷╷╷│  ← 3 lugs, ~4mm pitch — this is where wires solder on
                    ▼     └╵╵╵┘
                                              ~20mm total below the panel, per switch
   ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  (clear air — wiring/slack lives here)

   ┌─────────────┐                                    ┌──────────────┐
   │ OLED module │  ~8-13mm (standoffs + PCB +         │  Pico, taped  │  a few mm — flat
   │ on standoffs│   components on the back)           │  to the LID   │  against the lid,
   └─────────────┘                                    └──────────────┘  not the floor

   ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  (clear air below both — nothing else
                                                                down here but coiled wire slack)

   ════════════════════════════ BOX FLOOR ══════════════════════════════

   Box interior height: 55mm nominal (HB5050). Switch stack alone uses ~20mm of that below the
   panel; the OLED module hangs a further ~8-13mm. **The Pico is also lid-mounted now** (§4, moved
   off the floor for serviceability — see the note there), taped flat to the lid in the open gap
   between the two switch rows, a few mm thick — nowhere near the floor. That leaves the entire
   ~35mm+ remaining interior height as clear air for wire slack, not shared with any component
   sitting down at the floor. Tight sideways (X/Y, per §2.1/§2.2), not tight vertically.
```

```
   BACK WALL (the only wall with anything through it — one hole/connector):

   ┌──────────────────────────────────────────────────────┐
   │                                                        │
   │                    ┌──────────┐                        │
   │                    │   USB    │  ← detachable coupler,  │
   │                    │ coupler  │    §2.3a. Pico is        │
   │                    └──────────┘    powered over this    │
   │                                     same USB link.       │
   └──────────────────────────────────────────────────────┘

   No audio jacks, no power connector, nothing else through any wall of this box — that's all in
   the electronics box (§8), not this one.
```

#### 2.3a The back-wall connector — decided: panel-mount USB-A coupler

**Use [`enclosure-templates/pipedal-footswitch-backwall-drill-template.svg`](./enclosure-templates/pipedal-footswitch-backwall-drill-template.svg)**
for the actual hole layout — same to-scale/print-at-100% approach as §2.2, don't mark from the
diagram above (it's schematic, not dimensioned).

**Orientation — corrected 2026-09-12, an earlier version of this note had it backwards.** This
template is the TRUE view from **outside** the enclosure, standing behind the box facing it. That
means **X is mirrored relative to the lid template's page layout** — increasing X (toward
TUNER/MUTE) is drawn going *left* here, not right. Reasoning: the lid template's left/right matches
the *player's own* left/right when they stand at the front looking toward the back (facing away
from themselves — their right hand points toward increasing X, hence TUNER/MUTE is drawn on the
right). To look at the *outside* of the back wall you have to stand behind the box facing the
*opposite* direction — facing the box — so your right and left swap relative to that same X-axis.
Dimension labels on the template still cite the same true X values as the lid template (the
connector is still "X=170"); only its drawing position is mirrored (page position = 222 − true X)
so left/right looks correct once you're actually standing outside behind the box holding the
printout up to the panel. Tape it to the back wall's **outside** surface — that also matches how
the coupler physically fits, with its flange flush against that face and its body protruding
inward behind the panel.

Decided against both alternatives that were on the table:
- **Not** the Pico's own micro-USB port exposed directly through the wall — no strain relief at
  all, and micro-USB ports are fragile enough (a handful of tiny solder pads) that a cable getting
  tugged in normal use is a real risk to the Pico itself, not a theoretical one.
- **Not** a captive cable through a grommet — works, but isn't detachable at the box.

**Going with:** a USB-A female-to-female **panel-mount coupler** (bought, not built) — the
connector's own mounting screws take the mechanical strain of plugging/unplugging, not the
Pico's port or a glued joint. Two cables either side of it:
1. **Inside:** an ordinary micro-USB-B-to-USB-A cable (already on the parts list, §9.1) — micro-B
   into the Pico, USB-A into the coupler's inside face.
2. **Outside:** an ordinary USB-A-to-USB-A cable to the Pi.

The coupler itself never touches the Pico's connector shape at all — both its faces are plain
USB-A, matching the cable on each side of it, which is why "USB-A to USB-A" is right even though
the Pico is USB-B.

**Part found:** USB 3.0 Type-A female-to-female D-series panel mount coupler, "tunghey" brand,
Amazon AU (ASIN B0D77L812F). USB 3.0-labeled is fine — the connector shape hasn't changed, no
speed requirement here, it's just what was in stock with a proper dimensioned diagram. Real specs
read off that listing's own drawing, not estimated:

| Feature | Size |
|---|---|
| Mounting flange | 26×31mm |
| Round bore for the connector barrel | ⌀23.7mm |
| Mounting screws | 2× ⌀3.4mm (M3), diagonal D-pattern, 19mm horizontal × 24mm vertical apart |
| **Body depth behind the panel** | **28.6mm** |

That last one is the number that actually mattered here — it's deeper than a simple round-hole
jack, and it protrudes forward into the box from the back wall. This is a separate clearance
question from §2.3's lid-to-floor stack-up: that one's about the lid and floor, this one's about
the back wall and whatever sits just inside it.

**Checked, not just flagged:** with this connector centered on the wall (X=111mm, same X as the
OLED module), the 28.6mm protrusion clears the OLED's hang-down from the lid by only **1.9mm** —
smaller than the wall-thickness uncertainty already flagged in §2.3. That's not a real margin.

**Fix, applied at the time:** position moved to **X=170mm**, not centered. That sat in the clear
49mm-wide gap between the OLED's footprint (X 75-147) and TUNER/MUTE (X 196-208), giving ~10mm and
~13mm of actual clearance on either side instead of 1.9mm. Vertically it's still centered on the
wall (Z=27.5mm) — the sideways shift alone was enough to clear everything, no need to fight over
vertical margin too.

**Re-checked 2026-09-12 against the corner-post fix (§2.1) — still X=170mm, unchanged.** A corner
post discovered inside the physical chassis forced TUNER/MUTE to move from X=202, which briefly
looked like it would also force this connector to move (down to X=164, then X=167, through a
couple of rough-measurement passes, before a corrected diagonal put TUNER/MUTE on the *big*-post
corner at X=198 instead of the small one) — but even at X=198, the gap this connector sits in
stays comfortable enough for X=170: **~10mm to the OLED, ~9mm to TUNER/MUTE.** Worth knowing this
number moved and came back, in case an older intermediate note or file still shows X=164/167 — the
current, correct value matches this section's original finding. See
`print-templates-v2/pipedal-footswitch-backwall-print.svg` for the current template; the older
`enclosure-templates/pipedal-footswitch-backwall-drill-template.svg` is unaffected (also shows X=170) but is stale for
the OTHER reason already noted (its own §2.1 hole positions, unrelated to this connector, are
outdated).

Same caveat as everywhere else in this section: this was checked against nominal/estimated
dimensions (switch datasheet, OLED listing, this connector's listing), not a physical dry-fit.
Re-verify once you actually have the enclosure and the connector in hand.

### 2.4 Full internal wiring diagram

**Bench-ready versions of everything in this section** — regrouped by component with a
solder/plug-in/mechanical/taped connection-type legend, a step-by-step procedure with test
checkpoints, and a to-scale physical layout SVG with wire routing — live in `wiring/`:
[`pipedal-footswitch-wiring-reference.md`](./wiring/pipedal-footswitch-wiring-reference.md),
[`pipedal-footswitch-wiring-procedure.md`](./wiring/pipedal-footswitch-wiring-procedure.md),
[`pipedal-footswitch-wiring-layout.svg`](./wiring/pipedal-footswitch-wiring-layout.svg). This
section remains the source of truth if the two ever disagree.

Every wire, one place. `GND` is a single shared return — every switch common and both LED
cathodes tie back to the Pico's `GND` pin (or a small internal ground bus if that's easier to
route than 12 wires converging on one pin — a shared strip of wire with all the grounds soldered
to it, one wire from that strip to the Pico, is the usual way to do this without stacking 12
wires on one tiny pad).

```
                              Raspberry Pi Pico H
                    ┌───────────────────────────────────┐
     USB ═══════════╡ (to the Pi — data + power, §7)     │
                    │                                     │
   SW1 common ──────┤ GND                                 │
   SW2 common ──────┤ GND     (all switch commons +       │
   SW3 common ──────┤ GND      both LED cathodes land      │
   SW4 common ──────┤ GND      on GND — use a ground        │
   SW5 common ──────┤ GND      bus/strip, not 12 wires      │
   SW6 common ──────┤ GND      on one pin)                  │
   RESET common ────┤ GND                                 │
   TUNER/MUTE common┤ GND                                 │
   PRESET-btn common┤ GND                                 │
   SNAPSHOT-btn com. ┤ GND                                │
   LED PRESET cathode (−) ┤ GND                            │
   LED SNAPSHOT cathode(−)┤ GND                            │
                    │                                     │
   SW1 signal ───────┤ GP2                                 │
   SW2 signal ───────┤ GP3                                 │
   SW3 signal ───────┤ GP4                                 │
   SW4 signal ───────┤ GP5                                 │
   SW5 signal ───────┤ GP6                                 │
   SW6 signal ───────┤ GP7                                 │
   PRESET-btn signal ┤ GP8                                 │
   SNAPSHOT-btn signal┤ GP9                                │
   RESET signal ──────┤ GP10                               │
   TUNER/MUTE signal ─┤ GP11                                │
   LED PRESET anode ──┤ GP12 ──[330Ω–1kΩ resistor, in series]──▶│
   LED SNAPSHOT anode ┤ GP13 ──[330Ω–1kΩ resistor, in series]──▶│
                    │                                     │
   OLED SCK ──────────┤ GP14 (SPI0 SCK)                    │
   OLED MOSI ─────────┤ GP15 (SPI0 MOSI)                   │
   OLED RES ──────────┤ GP16                                │
   OLED DC ───────────┤ GP17                                │
   OLED CS ───────────┤ GP18                                │
   OLED VCC ──────────┤ 3V3(OUT)   ⚠ 3.3V only — never VBUS/5V│
   OLED GND ──────────┤ GND                                 │
                    │                                     │
   Encoder C (common)┤ GND      (same ground bus as        │
   Encoder SW leg 2 ─┤ GND       everything else above)     │
   Encoder A ─────────┤ GP19                                │
   Encoder B ─────────┤ GP20                                │
   Encoder SW leg 1 ──┤ GP21                                │
                    └───────────────────────────────────┘
```

Every switch is wired the same way — this is a DPDT switch used as SPST, so only 2 of its 3 lugs
matter per the datasheet's schematic (`PUSH: 1-2 ON`): one lug to the Pico's `GND`, the other to
its own dedicated `GPx` signal pin. Leave the third lug (pin 3/3') unconnected — it's the
normally-closed side you don't need.

| Wire run | From | To | Notes |
|---|---|---|---|
| SW1 | switch lug 1 | Pico GP2 | |
| SW1 GND | switch lug 2 | ground bus | |
| SW2 | switch lug 1 | Pico GP3 | |
| SW2 GND | switch lug 2 | ground bus | |
| SW3 | switch lug 1 | Pico GP4 | |
| SW3 GND | switch lug 2 | ground bus | |
| SW4 | switch lug 1 | Pico GP5 | |
| SW4 GND | switch lug 2 | ground bus | |
| SW5 | switch lug 1 | Pico GP6 | |
| SW5 GND | switch lug 2 | ground bus | |
| SW6 | switch lug 1 | Pico GP7 | |
| SW6 GND | switch lug 2 | ground bus | |
| PRESET mode button | switch lug 1 | Pico GP8 | |
| PRESET mode GND | switch lug 2 | ground bus | |
| SNAPSHOT mode button | switch lug 1 | Pico GP9 | |
| SNAPSHOT mode GND | switch lug 2 | ground bus | |
| RESET | switch lug 1 | Pico GP10 | |
| RESET GND | switch lug 2 | ground bus | |
| TUNER/MUTE | switch lug 1 | Pico GP11 | |
| TUNER/MUTE GND | switch lug 2 | ground bus | |
| LED PRESET anode (+, long leg) | via 330Ω–1kΩ resistor | Pico GP12 | resistor can sit at either end of this run |
| LED PRESET cathode (−, short leg/flat side) | — | ground bus | |
| LED SNAPSHOT anode (+, long leg) | via 330Ω–1kΩ resistor | Pico GP13 | |
| LED SNAPSHOT cathode (−, short leg/flat side) | — | ground bus | |
| OLED, ×7 | ribbon jumper (§4.1) | GP14/15/16/17/18, 3V3(OUT), GND | no solder — plugs onto both headers |
| Encoder A | pin A | Pico GP19 | §4.2 |
| Encoder B | pin B | Pico GP20 | §4.2 |
| Encoder common | pin C | ground bus | §4.2 |
| Encoder push switch | SW1 | Pico GP21 | §4.2 |
| Encoder push switch GND | SW2 | ground bus | §4.2 |

Suggested wire colours (not load-bearing, just sanity-saving when you're debugging later): red for
every GPIO signal wire, black for every ground-bus wire, a third colour (e.g. yellow) for the two
LED anode wires so they're visually distinct from switch signal wires at a glance.

| Qty | Function |
|---|---|
| 6 | Preset 1–6 or Snapshot 1–6, depending on mode |
| 1 | Mode select: PRESET (+ indicator LED) |
| 1 | Mode select: SNAPSHOT (+ indicator LED) |
| 1 | Reset → Preset 1 / Snapshot 1 |
| 1 | Tuner + mute |
| 1 | OLED, 2.42" 128×64 — preset/snapshot name now, tuner display stretch goal (§4.1) |

**Mode behaviour:**
- Mode lives only in the Pico's memory, set by whichever mode-select footswitch was pressed
  last.
- Selecting a preset auto-selects snapshot 1 on it, then returns to SNAPSHOT mode — you almost
  always want a snapshot right after a preset change.
- Boots into SNAPSHOT mode.

## 3. MIDI mapping

| Control | Mode | Message | Meaning |
|---|---|---|---|
| Row FS 1–6 | SNAPSHOT | `B0 14 7F` … `B0 19 7F` (CC20–25) | Select snapshot 1–6 |
| Row FS 1–6 | PRESET | `C0 00` … `C0 05`, then `B0 14 7F` | Select preset 1–6, force snapshot 1 |
| Mode selects | — | local Pico state only, no MIDI | Switches what the row means |
| Reset | — | `C0 00` then `B0 14 7F` | Force Preset 1 / Snapshot 1, back to SNAPSHOT mode |
| Tuner/mute | toggles | `B0 1A 7F`/`00` + `B0 1B 7F`/`00` (CC26/27) | Tuner on/off + gain −inf on/off |

**Pi → Pico direction (§4.1's OLED feature), separate address space, never sent by the Pico:**

| Message | Meaning |
|---|---|
| CC28 | Tuner note number (MIDI note 0–127) |
| CC29 | Tuner cents offset, `value = round(cents) + 64` (64 = in tune), clamped 0–127 |
| SysEx `F0 7D 01 <hl> <name0> 00 <name1> 00 ... 00 <name5> F7` | **Snapshot grid**: all 6 snapshot names of the current preset, `<hl>` = highlighted index 0-5 or 127 for none. Sent on every `onPedalboardChanged`/`onSelectedSnapshotChanged` push |
| SysEx `F0 7D 02 <hl> <name0> 00 ... 00 <name5> F7` | **Preset grid**: first 6 preset names in the bank (matching what PC0-5 actually select), `<hl>` as above. Sent from `getPresets` + `onPresetsChanged` |
| SysEx `F0 7D 03 <cur> <name0> 00 <name1> 00 ... F7` | **Full preset-browse list** (§4.2) — up to `BROWSE_MAX_PRESETS` (24) preset names, variable count, `<cur>` = the actually-loaded preset's position in this list, or 127 if unknown/beyond the cap. Sent alongside the preset grid, same triggers |

These ride the same USB MIDI cable as the footswitch CCs above without conflict — see
`pi_relay.py`'s docstring for why (short version: it's a brand new direction, Pi writing to the
Pico, which the Pico only ever reads; it never touches the Pico→Pi direction PiPedal itself
listens on).

Program numbers are 0-indexed on the wire — verify with `amidi -l`/`-d` before trusting the UI's
"Preset 1" label (§13.A of the main plan).

**Intentional: switching a snapshot or preset cancels tuner/mute.** Tuner/mute isn't part of
snapshot state (it's a live CC toggle on the Tuner and Gain plugins, §13.G of the main plan), so
recalling any snapshot or preset overwrites it back to that snapshot's stored tuner-off/gain-
normal state. This is kept as-is, on purpose — it means any snapshot/preset footswitch doubles
as a quick way to jump out of tuning mode.

## 4. Pico wiring and firmware

The Pico lives **in the footswitch box**, wired directly to every switch and both LEDs — no
expander chip, no bus. It sends finished MIDI messages out over its own USB cable to the Pi.
Physically secured with mounting tape + an insulation layer, **on the underside of the lid** (not
the case floor) — see `pipedal-footswitch-build-guide.md` §6 for why (no drilling into the sealed
enclosure, no 3D printing) and the reasoning behind the insulation layer.

**Mounted on the lid, not the floor, and this matters for serviceability.** Every switch, both
LEDs, the OLED, and the encoder are all lid-mounted. If the Pico sat on the floor instead, all
~36 of those wires would cross the lid/body split, and you couldn't lift the lid off without
flexing or straining every soldered joint at once. Mounted on the lid alongside everything else,
the **only** thing crossing that split is the single USB cable from the Pico to the back-wall
coupler (§2.3a) — unplug that one cable (it's a factory connector on both ends) and the lid comes
away complete, wiring and all. See `wiring/pipedal-footswitch-wiring-layout.svg` for the suggested
lid position (the open gap between the two switch rows, X≈85-137, Y≈98-119 in this doc's
coordinate system) — not yet confirmed against the physical box, check clearance at dry-fit.

```
        Raspberry Pi Pico
        ┌──────────────────────┐
   USB ═╡ (→ out to the Pi, §7)│
        │  GP2  ●───[Row FS 1]
        │  GP3  ●───[Row FS 2]
        │  GP4  ●───[Row FS 3]
        │  GP5  ●───[Row FS 4]
        │  GP6  ●───[Row FS 5]
        │  GP7  ●───[Row FS 6]
        │  GP8  ●───[Mode: PRESET]
        │  GP9  ●───[Mode: SNAPSHOT]
        │  GP10 ●───[Reset]
        │  GP11 ●───[Tuner/mute]
        │  GP12 ●───[R]──[PRESET LED]──┐
        │  GP13 ●───[R]──[SNAPSHOT LED]┤
        │  GND  ●─── common return for all of the above
        └──────────────────────┘
```

Internal pull-ups, switches short to GND, no resistors on the inputs. Each LED gets a 330 Ω–1 kΩ
series resistor to GND. Edge-triggered with debounce on every switch input.

```python
ROW           = (board.GP2, board.GP3, board.GP4, board.GP5, board.GP6, board.GP7)
MODE_PRESET   = board.GP8
MODE_SNAPSHOT = board.GP9
RESET         = board.GP10
TUNER_MUTE    = board.GP11
LED_PRESET    = board.GP12
LED_SNAPSHOT  = board.GP13

mode = "SNAPSHOT"   # boot default; LED_SNAPSHOT on, LED_PRESET off

# MODE_PRESET falling edge:   mode = "PRESET";   LED_PRESET on,  LED_SNAPSHOT off
# MODE_SNAPSHOT falling edge: mode = "SNAPSHOT"; LED_SNAPSHOT on, LED_PRESET off

# ROW[i] falling edge:
if mode == "SNAPSHOT":
    midi.send(ControlChange(20 + i, 127))
else:  # PRESET
    midi.send(ProgramChange(i))
    midi.send(ControlChange(20, 127))     # force snapshot 1
    mode = "SNAPSHOT"                      # LEDs follow

# RESET falling edge:
midi.send(ProgramChange(0))
midi.send(ControlChange(20, 127))
mode = "SNAPSHOT"
```

## 4.1 OLED display — preset/snapshot names (+ tuner, stretch goal)

2.42" 128×64 SPI OLED (SSD1309, 7-pin: GND/VCC/SCL/SDA/RES/DC/CS) mounted in the footswitch box,
wired straight to the Pico over its hardware SPI0 pins — no change to the single USB cable to the
Pi (USB MIDI is already bidirectional; the Pico just needs firmware that also calls
`midi.receive()`, not just `midi.send()`).

```
   OLED pin   Function              Pico pin
   GND        Ground                GND
   VCC        3.3V power            3V3(OUT)   ⚠ 3.3V logic — do not feed 5V/VBUS
   SCL        SPI clock             GP14 (SCK)
   SDA        SPI data (MOSI)       GP15 (MOSI)
   RES        Reset                 GP16
   DC         Data/Command select   GP17
   CS         Chip select           GP18
```

GP14/15 are the RP2040's hardware SPI0 pins — using those (not arbitrary GPIOs) gets hardware-
accelerated SPI via `busio.SPI`, matching what CircuitPython's SSD1309 `displayio` driver expects.

**Pin budget:** 10 switches + 2 LEDs (GP2–GP13, §4) + 5 OLED signal pins (GP14–GP18) = 17 of the
Pico's 26 usable GPIOs. 9 spare (GP0, GP1, GP19–22, GP26–28), including ADC-capable ones.

**Use a ribbon jumper for the OLED, not 7 loose wires.** The OLED breaks its 7 signals out onto
a single pin header, and the Pico H already has pre-soldered headers (main plan §1) — that's
exactly the case a **female-female Dupont ribbon jumper cable** is for: buy a 10-way (or wider)
ribbon and use 7 of the 10 conductors, or trim it to 7. It plugs straight onto both headers with
no soldering, keeps the 7 wires visibly bundled and colour-coded instead of a loose tangle, and
is easy to unplug later if you need to re-seat the display. Since the OLED sits right in front of
the Pico (§8), the run is short enough that a standard 10–15cm ribbon covers it with slack to
spare — don't bother hunting for a shorter one.

**The switches and LEDs stay loose hookup wire, unchanged.** They don't share a connector — each
switch/LED is its own two-wire run to a physically separate part of the panel — so a ribbon buys
nothing there and would just be harder to route than individual wires.

**Both features are now written — status is "needs hardware to test," not "needs designing."**

| Feature | Status | Notes |
|---|---|---|
| **Preset/snapshot 3x2 grid** | Written, untested on hardware | Idle screen shows a 3x2 grid mirroring the footswitch rows — 6 preset names in PRESET mode, 6 snapshot names in SNAPSHOT mode — with a border around whichever one's active. Names come **live** from PiPedal (not a hardcoded table). `pi_relay.py` fetches the snapshot list from `onPedalboardChanged`/`onSelectedSnapshotChanged`, and the preset list from `getPresets`/`onPresetsChanged`, forwarding both as MIDI SysEx. If the active preset is beyond bank position 6 (unreachable by footswitch), no cell is highlighted — see `pipedal_ws.build_preset_grid`'s docstring/tests. `code.py` decodes it and shows it via `oled_display.show_grid()`. |
| **Live tuner note + cents** | Written, untested on hardware | Confirmed the protocol isn't actually undocumented — it's a plain JSON-over-WebSocket request/reply scheme, fully readable in the open-source `rerdavies/pipedal` repo, with a general `monitorPort` call the web UI itself uses for VU meters and its own tuner dial (`GxTunerControl.tsx`). TooB Tuner's pitch is LV2 control-output port `FREQ` on plugin URI `http://two-play.com/plugins/toob-tuner`. `pi_relay.py` subscribes to it, converts Hz → note+cents (`pitch.py`), and forwards as MIDI CC28/29 to the Pico, which shows it via `oled_display.show_tuner()` whenever `tuner_mute_on` is set. `tuner_freq_probe.py` is the standalone diagnostic used to confirm the websocket side works in isolation. Still fragile across PiPedal versions in the sense that any internal API can change without notice (unlike MIDI bindings, which are public/stable) — that risk stands, just not "unknown protocol" risk. |

**What's actually in `pico-footswitch-v2/` now:**

| File | Role |
|---|---|
| `code.py` | Pico firmware — reads switches, sends footswitch MIDI, polls `midi.receive()` for names/tuner data from the Pi, drives the OLED |
| `midi_logic.py` | Pure-Python footswitch state machine + the single source of truth for every CC/SysEx number, both directions |
| `pitch.py` | Pure-Python Hz → (MIDI note, cents) math, used by `pi_relay.py` |
| `oled_display.py` | SSD1309 driver glue + the three screen layouts (3x2 grid / tuner / preset-browse) |
| `pipedal_ws.py` | Shared PiPedal WebSocket client (request/reply framing, `monitorPort`/pedalboard/preset-grid/browse-list helpers) |
| `pi_relay.py` | **Runs on the Pi**, not the Pico. The persistent daemon: PiPedal websocket → MIDI to the Pico. Install via `pipedal-tuner-relay.service` |
| `tuner_freq_probe.py` | Standalone diagnostic — websocket only, no Pico needed, prints live Hz |
| `pipedal_pc_probe.py` | Standalone diagnostic — answers §5's open question on absolute Program Change, no Pico needed |
| `midi_monitor.py` | Standalone diagnostic — decodes the Pico's live MIDI output on a breadboard, before any enclosure exists |
| `test_midi_logic.py`, `test_pitch.py`, `test_pipedal_ws.py` | Unit tests, no hardware needed: `python3 -m unittest discover` |
| `pipedal-tuner-relay.service` | systemd unit for `pi_relay.py`, installed on the Pi (not the Pico) |

**Driver: confirmed working on hardware (2026-09-23).** There's no CircuitPython driver written
specifically for the SSD1309 controller, so it uses the `adafruit_displayio_ssd1306` driver
against the SSD1309 panel — and that works. **The SPI clock must be slowed to 1 MHz**
(`baudrate=1000000` in `oled_display.py`'s `FourWire(...)`): at FourWire's default 24 MHz the
hand-wired leads silently corrupted every command and the screen stayed blank with no error.
The panel board must also be in SPI mode — its IIC/SPI resistor legend reads "SPI: R8, IIC:
R9-R12"; ours shipped set to SPI.

**Setup, once hardware exists:**
1. Pico: copy `adafruit_displayio_ssd1306`, `adafruit_display_text`, `adafruit_display_shapes`,
   `adafruit_midi` (bundle) plus
   `midi_logic.py`, `pitch.py`, `oled_display.py`, `code.py` to `CIRCUITPY`.
2. Pi: `pip install websockets mido python-rtmidi`, then `python3 pi_relay.py --list` to find the
   Pico's MIDI port name, then install `pipedal-tuner-relay.service` (edit the username/path/port
   name in it first) with `sudo systemctl enable --now pipedal-tuner-relay`.

## 4.2 Preset-browse rotary encoder

Reaches presets beyond the 6 wired to footswitches (PC0-5 only), without the phone UI. Hand-operated
— mounted somewhere reachable near the OLED, not in the footswitch rows; a knob is a finger control,
not a foot control (see the design discussion that led here). Turning it never sends anything to
PiPedal by itself — only pressing the encoder's own switch to confirm does. Any other footswitch or
mode-button press, or 3 seconds of no activity, cancels browsing with nothing selected.

**Part:** Alpha RE111F-21B3-15F-20P — sold as **Tayda A-6329** and **Jaycar SR1230** (identical
mounting spec, confirmed from both datasheets independently, not assumed from the part looking
similar). M7×0.75 threaded bushing, **⌀7.1mm panel hole**, D-shaft 6mm (needs a separate knob —
Tayda A-6888/A-7022, generic 6mm D-shaft fit, not tied to either supplier). 5 pins: **A, C, B**
(quadrature — A/B outputs, C common) + **SW1, SW2** (integrated pushbutton, 5V/10mA rating, plenty
for a 3.3V GPIO input).

**Below-panel depth, confirmed from Alpha's own mechanical drawing** (Mouser-hosted PDF, ref
TW-700111, dated 10-4-05, covering `RE111F-21B3-20F-20P` — same `21B3` bushing/body code as our
`-15F` part, differing only in shaft length, which the part number's own `F` suffix already
tells you): **bushing 7mm long** (M7×0.75, mostly sitting on the front/panel side for the nut,
washer, and knob boss — not into the box) and **body ~10mm deep behind the mounting surface**,
which is the figure that actually matters for interior clearance. That's comfortably inside the
35mm clear interior height (§2.3) — no concern there, and no longer an open question.

```
        Raspberry Pi Pico
        ┌──────────────────────┐
        │  GP19 ●───[Encoder A]
        │  GP20 ●───[Encoder B]
        │  GP21 ●───[Encoder push switch]
        │  GND  ●─── encoder C (common) + one push-switch leg,
        │             same shared ground bus as §4
        └──────────────────────┘
```

A and B are read by CircuitPython's built-in `rotaryio.IncrementalEncoder` — hardware quadrature
decoding, not part of the debounced switch-polling loop. Only the push switch (GP21) goes through
the same debounce logic as every other footswitch. **Confirmed on hardware (2026-09-23):**
`rotaryio` counts exactly one step per mechanical detent on the SR1230/A-6329, in the right
direction, with A/B on GP19/GP20 as drawn.

**Pin budget:** was 17 of 26 used after §4.1 (OLED). Encoder adds 3 more (GP19-21) → **20 of 26
used, 6 spare** (GP0, GP1, GP22, GP26, GP27, GP28).

**Placement:** the natural gap is on the lid, left of the OLED — X=55mm, Y=52mm in the §2.1/§2.2
coordinate system (same Y as the OLED's center, in the open space between it and RESET,
comfortably clear of both — checked at a 2D level only, this is a lid-mounted shaft like a switch,
not a wall-mounted connector, so it doesn't need the 3D depth check §2.3a needed). Now in
`enclosure-templates/pipedal-footswitch-drill-template.svg`, same to-scale/print-at-100% approach as everything else
on that template.

**Firmware:** `midi_logic.BrowseState` (pure Python, unit-tested in `test_midi_logic.py`) tracks
the browse cursor and turns a confirm-press into the same `PC + force-snapshot-1` messages a
footswitch preset-select sends — reusing that mechanism rather than inventing a new one, so it
inherits the same open question in §5 about whether PiPedal actually honours absolute Program
Change for preset selection. `pipedal_ws.build_full_preset_list` (Pi-side) fetches the full bank
list (capped at `BROWSE_MAX_PRESETS` = 24) via `getPresets`, separate from the 6-item grid in
§4.1 which deliberately only shows what the footswitches reach.

## 5. Open questions

1. ~~Does PiPedal accept absolute Program Change to select a preset?~~ **Answered, 2026-09-12: yes,
   0-indexed, no MIDI binding needed.** `amidi -p hw:0,0 -S "C0 00"` through `"C0 05"` all loaded
   the correct preset (PC 0 = "1 Clean" through PC 5 = "6 Massive"), and `"B0 14 7F"` (CC20=127)
   forced snapshot 1 on the loaded preset. Confirmed on the bench via `snd-virmidi`, no Pico
   needed. This settles the contradiction that existed between this doc, `presets-reference/pipedal-session-handoff.md`
   §5, and `pipedal-next-steps.md` — session-handoff's 2026-09-06 claim was right.
   **Caveat found while testing this:** `pico-footswitch-v2/pipedal_pc_probe.py` (uses `mido` /
   `python-rtmidi`'s ALSA sequencer backend) sent nothing PiPedal ever received — confirmed via
   `/proc/asound/seq/clients` client 128's `Alloc success` counter not moving. `mido`'s ALSA
   backend addresses events directly *to* the virmidi port as a sequencer destination; virmidi
   only rebroadcasts-to-subscribers for bytes written into the **rawmidi character device** side
   of the port (`amidi -p hw:0,0 -S ...`), which is the path that actually worked. This is a
   bench-only quirk of virmidi — a real USB Pico won't have it — but don't reach for `mido` against
   virmidi again; use `amidi -S` directly.
2. **Auto-return to SNAPSHOT mode after a preset change** — confirm you want this; it's one line
   to remove in firmware if not.
3. Reset always has the audible preset-change gap (§5 of the main plan) — expected, fine for a
   "get me back to a known state" switch.

## 6. Parts sourcing

Tayda is roughly **half price** per footswitch even after currency conversion: $2.99 USD vs
Altronics' S1152A at $9.15 AUD. Full 10-switch set: ~$30 USD (~$42 AUD) at Tayda vs ~$91.50 AUD
at Altronics. The number that actually decides it is Tayda's shipping quote to Perth (not
confirmed, reportedly ~3 weeks on the cheapest option) — check that before ordering. If you're
in a hurry, Altronics is same-day at Balcatta/Northbridge for the premium.

## 7. Shutdown

**Pisound's own onboard button handles this — no separate pushbutton needed.** Its
`pisound-btn` daemon ships with the Pisound software and already maps hold-5-seconds-and-release
to a clean `sudo shutdown now`. One less part, one less hole to drill.

**No safe-to-unplug LED.** A `gpio-poweroff`-driven LED was considered, but the practical
alternative — wait ~20 seconds after the hold gesture before pulling power — is good enough
here: a Pi OS Lite install running just PiPedal shuts down quickly, and imaging the SD card once
things are working (per the main plan) means an occasional bad shutdown costs a reflash, not a
rebuild.

## 8. Two enclosures, linked by one USB cable

Checked Jaycar's diecast/ABS ranges: nothing is both deep enough for the Pi 5 + Active Cooler +
Pisound HAT stack (~45-55mm) and wide enough for 10 footswitches at once, so it's two boxes:

| Box | Enclosure | Holds |
|---|---|---|
| Footswitch | Jaycar **HB5050**, 222×146×55mm, $39.95 | Everything in §2 — switches, LEDs, Pico |
| Electronics | Jaycar **HB6129**, 171×121×80mm, $23.95 | Pi 5, Active Cooler, Pisound HAT, shutdown via Pisound's button, USB-C power in |

**The only thing crossing between them is one USB cable, carrying MIDI** — the same USB MIDI
link the Pico has always used, just physically between two boxes instead of inside one.

```
┌───────────────────────────── FOOTSWITCH BOX ─────────────────────────────┐
│                                            ┌───────────┐                  │
│                                            │  USB jack │◄─────────────────┼── cable
│                                            │(back wall)│                  │  to the Pi
│                                            └─────┬─────┘                  │
│                                            ┌──────┴──────┐                │
│                                            │  Pico (§4)  │                │
│                                            └─┬──┬──┬──┬──┘                │
│                              short SPI ribbon│  │  │  │                   │
│                              (§4.1)          ▼  │  │  │                   │
│  ┌───────┐              ┌────────────────┐      │  │  │    ┌────────────┐│
│  │ RESET │              │  OLED (2.42")  │      │  │  │    │ TUNER/MUTE ││
│  └───┬───┘              └────────────────┘      │  │  │    └─────┬──────┘│
│      └─────────────────────────────────────────┐│  │  │┌─────────┘       │
│  ┌────┐        ┌────┐        ┌────┐  ┌────────┐││  │  ││                 │
│  │ 1  │        │ 2  │        │ 3  │──┤ PRESET │┘│  │  │└─────────────────┤
│  └────┘        └────┘        └────┘  └────────┘ │  │  │                  │
│  ┌────┐        ┌────┐        ┌────┐  ┌──────────┐│  │                   │
│  │ 4  │        │ 5  │        │ 6  │──┤ SNAPSHOT │┘  │                   │
│  └────┘        └────┘        └────┘  └──────────┘   │                   │
└───────────────────────────────────────────────────────────────────────┘
```

The Pico is mounted close to the back wall near the USB jack (unchanged), with the OLED just in
front of it — that's what keeps the SPI run short per §4.1, rather than routing it across the box
past the switch wiring. RESET and TUNER/MUTE now run their two wires each back to the Pico from
the corners instead of from beside it — longer than before, but still just hookup wire, not worth
a connector over.

```
┌──────────────────── ELECTRONICS BOX — TOP VIEW (171 × 121mm) ────────────────────┐
│   ┌───────────────────────────────────────────────┐                              │
│   │           Pisound HAT (on standoffs,           │      ┌───────────┐          │
│   │           ¼" jacks facing this wall) ──────────┼──────┤ ¼" IN/OUT │          │
│   │        (Pi 5 + Active Cooler underneath,       │      └───────────┘          │
│   │         same footprint, §13.1 main plan)        │                              │
│   └───────────────────────────────────────────────┘                              │
│   ┌───────────┐                                              ┌───────────┐        │
│   │ USB jack  │◄── cable from the Pico                       │ USB-C PWR │──power │
│   └───────────┘                                              └───────────┘        │
└────────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────── ELECTRONICS BOX — SIDE VIEW (80mm internal height) ───────────┐
│  lid clearance ~5mm                                                      │
│  Pisound HAT board + top components ~5-10mm                             │
│  standoffs, tall enough to clear the Active Cooler ~26-28mm             │  80mm
│  Active Cooler above the Pi 5 board ~20-23mm                            │  total
│  Raspberry Pi 5 board ~1.5mm                                             │
│  standoff clearance off the enclosure floor ~5mm                        │
│         ≈ 45-55mm used, ~25-35mm real margin — estimate, not a          │
│         measurement; dry-fit the actual stack before drilling           │
└────────────────────────────────────────────────────────────────────────┘
```

**The USB link, in practice:** either a captive cable through a small round grommet hole in
each box wall (cheapest, and fine since both boxes live together on the same pedalboard), or a
panel-mount USB coupler at each wall if you want it detachable (Jaycar's Type B panel socket,
PS0783, was out of stock in AU when checked — confirm before planning around it).

## 9. Footswitch box — shopping list

Prices checked 2026-09-07. Tayda is USD (~1.39 mid-market, card FX runs higher).

### 9.1 Already got

| Qty | Part | Notes |
|---|---|---|
| 1 | Raspberry Pi Pico H | Already owned — Altronics Z6421B (main plan §1) if you ever need a second |
| 10 | Momentary footswitch, DPDT compact | Tayda order, SKU A-1874 |
| 2 | 5mm LED, PRESET + SNAPSHOT indicators | Tayda order — 5× green (A-1553) + 5× red (A-1554) ordered, only 2 needed, rest are spares |
| 1 pack (10) | Resistor, 330Ω ¼W | Tayda order, SKU A-2325 |
| ~10 ft each | Hook-up wire, AWG22, red + black | Tayda order, SKU A-8520 / A-8519 |
| 1 | OLED display, 2.42" 128×64 SPI, 7-pin (SSD1309) | Tayda order, SKU A-7502 |
| 1 | Female-female Dupont ribbon jumper cable, 10-way (use 7 of 10 for the OLED, §4.1) | Tayda order, SKU A-2375 |

**Tayda order total, including shipping to Perth: $72 AUD** — confirmed at checkout.

### 9.2 Still to buy

| Qty | Part | Link | Price |
|---|---|---|---|
| 1 | Enclosure — Jaycar HB5050, 222×146×55mm | [jaycar.com.au](https://www.jaycar.com.au/sealed-diecast-aluminium-enclosure-222-x-146-x-55mm/p/HB5050) | $39.95 AUD |
| 1 | USB cable (micro-USB B → USB-A, data cable — see main plan §198-210) | old phone cable, or buy new | $0-10 AUD |
| 1 | Rotary encoder w/ pushbutton, §4.2 | Jaycar SR1230 ($10.25) or Tayda A-6329 | ~$2-10 AUD |
| 1 | Matching D-shaft knob, §4.2 | Jaycar **HK7786**, 20mm, 1/4" (6.35mm) flattened-side shaft + grub screw — fits the SR1230 above. (Tayda A-6888/A-7022 also fit, if buying from there instead) | $3.40 AUD |

**This table predates two later decisions — not re-totalled here, see their own docs instead:**
the back-wall USB coupler (§2.3a, not a Bunnings/Tayda/Jaycar item — sourced from Amazon AU) and
the drilling/cutting tools (`enclosure-build-reference/pipedal-bunnings-list.md`, a separate shopping list).

**Not included — comes with the electronics box's own list:** the Pi, HAT, Active Cooler, and
anything local to that box (including the Jaycar HB6129 enclosure, §8).
