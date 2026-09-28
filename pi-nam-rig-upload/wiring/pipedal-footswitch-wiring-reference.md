# Footswitch box — wiring reference

Pin-by-pin lookup for every wire in the box. Source of truth is `pipedal-hardware-v2.md` §2.4
(switches/LEDs), §4.1 (OLED), §4.2 (encoder) — if those ever change, update this doc to match, not
the other way round. This doc just re-groups the same information by *component* and adds the
connection-type/wire-colour info you actually want at the bench, rather than one long GPIO table.

See [`pipedal-footswitch-wiring-procedure.md`](./pipedal-footswitch-wiring-procedure.md) for the
order to do this in, and [`pipedal-footswitch-wiring-layout.svg`](./pipedal-footswitch-wiring-layout.svg)
for where everything physically sits.

## Connection types — the legend

Every wire/joint in this box is one of four types. The SVG uses the same four, so cross-reference
by these names:

| Type | Looks like | Used for |
|---|---|---|
| **Soldered** | Permanent joint, insulated after with heat-shrink or tape | Every switch lug, both LED leads (+ their resistor), both encoder quadrature pins, the encoder's push-switch legs, the ground bus joints (if you twist-and-solder it) |
| **Plug-in** | Dupont socket onto a header pin, or a factory cable connector — no solder, can be unplugged | The Pico-end of every switch/LED F-F jumper (cut only the *far* end, the Pico end stays a female socket on the header), the full OLED ribbon (both ends), both USB cables into/out of the coupler, the ground bus joints (if you use a terminal strip instead of solder) |
| **Mechanical (nut/bolt/screw)** | Metal-to-metal panel fastening, no current-carrying wire involved | Every switch's M12×0.75 bushing nut, the OLED's 4 mounting screws, the USB coupler's 2× M3×10 bolts+nuts, the encoder's M7×0.75 bushing nut |
| **Taped/friction-fit** | Adhesive or a push-fit, no fastener at all | The Pico (double-sided mounting tape, on top of an electrical-tape/plastic-sheet insulation layer), both LED bodies (friction-fit in their ⌀5mm hole, optionally a dab of glue from behind) |

## Switches (×10) — all wired identically

Every switch is a DPDT with 6 lugs total (2 poles × COM/NO/NC), wired as SPST: only 2 lugs matter —
one pole's COM and NO (`PUSH: 1-2 ON` per the A-1874 datasheet).

**Good news — these switches are physically marked.** One face of the metal base is stamped
something like `M 1 2 3`: **`M`** is just the body-length code (matches the `-M` suffix in the full
part number `SF12N-0202-20R-M`, not a pin), and **`1 2 3`** are the datasheet's own pin numbers,
printed right on the part. So:

- **Lug 1 and lug 2** (as marked) = your signal + ground pair — "Lug 1"/"Lug 2" in the table below
  refer to these marked pins directly. Either can be the GPIO side, the other the ground side.
- **Lug 3** on that same marked face = NC, leave it unconnected.
- **The opposite face of the base** (the DPDT's second pole, likely marked the same way or with
  primes) — leave all 3 of those lugs completely unconnected too.

**Verify with a multimeter anyway before soldering** — not because the marking is expected to be
wrong, but it's a free 5-second check: continuity mode, lugs 1 and 2 should read open unpressed,
closed while held pressed. If your marking is missing, worn, or you're unsure which face you're
reading, fall back to finding the pair by multimeter alone: try lug pairs until one goes open→closed
exactly like that, use that pair, leave the third lug of that group and the entire other pole
unconnected — same result, just without trusting a printed number first.

See `pipedal-footswitch-wiring-layout.svg` for an illustration of the 6-lug layout and this method.

| Switch | Function | Lug 1 → | Lug 2 → | Wire colour (signal / ground) |
|---|---|---|---|---|
| SW1 | Preset 1 / Snapshot 1 (mode-dependent) | GP2 | ground bus | red / black |
| SW2 | Preset 2 / Snapshot 2 | GP3 | ground bus | red / black |
| SW3 | Preset 3 / Snapshot 3 | GP4 | ground bus | red / black |
| SW4 | Preset 4 / Snapshot 4 | GP5 | ground bus | red / black |
| SW5 | Preset 5 / Snapshot 5 | GP6 | ground bus | red / black |
| SW6 | Preset 6 / Snapshot 6 | GP7 | ground bus | red / black |
| PRESET | Mode select → PRESET | GP8 | ground bus | red / black |
| SNAPSHOT | Mode select → SNAPSHOT | GP9 | ground bus | red / black |
| RESET | → Preset 1 / Snapshot 1 (after `RESET_GAP_S`) | GP10 | ground bus | red / black |
| TUNER/MUTE | Tuner mute toggle | GP11 | ground bus | red / black |

**Both ends:** switch lug = soldered. Pico end = plug-in (female jumper socket on the `GPx` pin).

**Mounting hardware — two nuts per switch, on purpose.** If your order shipped two hex nuts plus a
washer per switch, that's a jam-nut arrangement, not a mistake: one nut clamps the switch to the
panel, a second locks against the first to stop it backing off. Given these get stomped on
repeatedly, that's exactly the vibration/impact case a lock nut exists for. Order from outside in:
switch body through the panel → washer against the inside face (protects the panel finish, spreads
clamping load) → nut #1 (tightened to clamp the switch) → nut #2 (jam nut, turned down against
nut #1 and held while you snug it).

## LEDs (×2)

| LED | Anode (+, long leg) → | Cathode (−, short leg/flat side) → | Resistor |
|---|---|---|---|
| PRESET indicator | GP12 | ground bus | 330Ω–1kΩ, in series, either end of the run |
| SNAPSHOT indicator | GP13 | ground bus | 330Ω–1kΩ, in series, either end of the run |

Wire colour: **yellow** for both anode runs (distinct from switch signal wires at a glance, per
`pipedal-hardware-v2.md` §2.4), black for both cathode runs. Both leads = soldered (to the resistor
and to the jumper wire); Pico end = plug-in. LED **body** itself is friction-fit in its ⌀5mm hole —
no fastener, optionally a dab of glue from behind once wired.

## Ground bus

See [`pipedal-ground-bus-howto.svg`](./pipedal-ground-bus-howto.svg) for a step-by-step picture of
building this joint (both methods below).

Every switch common (×10), both LED cathodes, and the OLED ground all land on one shared bus, with
a single wire from that bus to the Pico's `GND`. Two ways to build it, pick one:

- **Twist-and-solder**: strip and twist all 13 ground wires together plus one wire going to the
  Pico, solder the joint, insulate with heat-shrink. All-solder, no mechanical parts.
- **Small terminal strip**: screw each ground wire into its own terminal, one terminal wired to the
  Pico. Plug-in-equivalent (screw terminal, not solder) — easier to add/remove a wire later if you
  misdiagnose a fault.

Either way, exactly one wire leaves the bus for the Pico's `GND` pin — never wire multiple grounds
directly onto the Pico's single `GND` pad.

## OLED (2.42" SSD1309, 7-pin)

| OLED pin | Function | Pico pin |
|---|---|---|
| GND | Ground | GND |
| VCC | 3.3V power | 3V3(OUT) — **3.3V only, never 5V/VBUS** |
| SCL | SPI clock | GP14 (hardware SPI0 SCK) |
| SDA | SPI data (MOSI) | GP15 (hardware SPI0 MOSI) |
| RES | Reset | GP16 |
| DC | Data/command select | GP17 |
| CS | Chip select | GP18 |

**Identify pins by the label printed on the board, not by physical position.** Unlike the switches
(unlabeled solder lugs), OLED breakout boards almost universally silkscreen-print each pin's name
right next to it on the PCB — costs the manufacturer nothing to add. The physical left-to-right
order of GND/VCC/SCL/SDA/RES/DC/CS on your specific module isn't confirmed here (varies by board),
but that shouldn't matter: read the 7 printed labels on your board and match each one to its Pico
pin from the table above, regardless of which physical position it's in. If your board's labels are
genuinely unreadable (worn silkscreen, bad photo in the listing), don't guess — that's the one case
this becomes a real risk, since a wrong `VCC` connection can damage the display (see below), unlike
a switch lug mixup which just fails to register a press.

**The one wire that can actually damage something: `VCC` must go to `3V3(OUT)`, never `VBUS`/5V.**
Every other miswiring here (wrong data pin, swapped `RES`/`DC`/`CS`) just means a blank or garbled
screen, fixable by re-checking and re-plugging — no soldering to undo since this is a ribbon jumper.
Double-check this one connection specifically before powering on for the first time.

**No soldering at all** — a 7-of-10-conductor female-female Dupont ribbon jumper plugs straight onto
both the OLED's header and the Pico's. Fully plug-in at both ends. The OLED module's **body** is
mounted mechanically, 4× screws (whatever shipped with the module — check before buying M2.5/M3
separately).

**Header orientation, updated now that the Pico's confirmed on the right wall: if your module's
header is on a side edge (not top/bottom), face it RIGHT — toward the Pico, not toward TUNER/MUTE.**
This flips the earlier version of this note, written before the Pico's final position was known.
With the Pico on the right wall and the encoder sitting between the OLED and that wall (X≈167,
between the OLED's center at 111 and the Pico beyond it), there's no longer a side that avoids the
encoder entirely — facing right is still the shortest path to the Pico, it just means the ribbon
runs near the encoder's knob rather than clear of it. **Dress the ribbon at a slightly different
height than the encoder's own Y position** (route it along the top or bottom of the gap rather than
straight through the middle) so it doesn't foul the rotating shaft, rather than trying to avoid that
side of the panel altogether. Facing left (toward TUNER/MUTE) avoids the encoder but makes for a
much longer, more circuitous run all the way to the opposite wall — not worth it just to dodge one
moving part you can just route around instead.

Not confirmed from a datasheet whether your specific module even has a side-edge header (varies by
board even within "2.42" SSD1309 SPI") — if it's on the top or bottom edge instead, this choice
doesn't apply; check the physical part before deciding.

## Preset-browse encoder (Alpha RE111F, 5-pin)

| Encoder pin | Function | Pico pin |
|---|---|---|
| A | Quadrature output A | GP19 |
| B | Quadrature output B | GP20 |
| C | Common | ground bus |
| SW1 | Push-switch leg 1 | GP21 |
| SW2 | Push-switch leg 2 | ground bus |

All 5 pins = soldered at the encoder, plug-in at the Pico end (cut F-F jumpers, same as the
switches). Encoder **body** is mechanical — M7×0.75 bushing nut + washer (included with the part),
same panel-mount principle as the footswitches.

**Physical pin layout — confirmed from the datasheet AND multimeter-tested.** The Jaycar SR1230
datasheet's drawing is a **front view** — looking at the knob, from outside the box, the same
direction you looked when marking the drill template. That's the opposite face from where you
solder, since wiring happens from inside/underneath. **Mirror it left-right for the side you're
actually working from:**

- Datasheet (front view, knob facing you): bottom 3 pins read **A, C, B** left to right.
- Your wiring view (from below/inside): bottom 3 pins read **B, C, A** left to right instead — same
  left-right flip that applies to the whole panel (see `pipedal-footswitch-wiring-layout.svg`).
  **C stays in the middle either way** — mirroring a row of 3 only swaps the two outer ones.

The datasheet's own signal table also confirms C's role directly — "A (Terminal A-C)", "B (Terminal
B-C)" — C is the shared reference for both.

**Top 2 pins — confirmed as functional SW1/SW2, not mechanical tabs**, by multimeter test: open at
rest, closed only while the shaft is held pressed. Either one can be SW1 or SW2, doesn't matter
which — one to GP21, the other to the ground bus.

## USB coupler (back wall)

No wire pins at all — two factory USB cables, both ends plug-in:

- **Inside:** micro-USB-B-to-USB-A cable, micro-B into the Pico, USB-A into the coupler's inside
  face.
- **Outside:** USB-A-to-USB-A cable, from the coupler's outside face to the Pi.

The coupler's own body is mechanical — 2× M3×10mm bolts + nuts through its flange, into the back
wall.

## Wire colour code (whole box)

Not load-bearing electrically, but keep it consistent — it's what makes a fault findable later
without re-deriving this whole doc:

| Colour | Meaning |
|---|---|
| Red | Every GPIO signal wire — switches, mode buttons, RESET, TUNER/MUTE, encoder A/B/push |
| Black | Every ground-bus wire |
| Yellow | The two LED anode wires only |

## Pico pin budget (for reference)

| Pins used | For |
|---|---|
| GP2–GP13 (12) | 10 switches + 2 LEDs |
| GP14–GP18 (5) | OLED (hardware SPI0 + RES/DC/CS) |
| GP19–GP21 (3) | Encoder (A/B/push) |
| 3V3(OUT), GND | OLED power/ground (shared ground bus for GND) |
| **20 of 26 usable GPIOs used** | 6 spare: GP0, GP1, GP22, GP26, GP27, GP28 |
