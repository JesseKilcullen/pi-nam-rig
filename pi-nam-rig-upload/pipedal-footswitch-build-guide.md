# Footswitch box — build guide

Step-by-step for actually drilling, cutting, and wiring the footswitch enclosure. References
`pipedal-hardware-v2.md` for the why; this is the how, in order, with exactly which bit/fastener
each step needs. Tools/consumables: `enclosure-build-reference/pipedal-bunnings-list.md`.

## 0. Before you start

- Print `enclosure-templates/pipedal-footswitch-drill-template.svg` (lid) and `enclosure-templates/pipedal-footswitch-backwall-drill-template.svg`
  (back wall) at **100% / "actual size"** — not "fit to page."
- Measure each printout's 50mm calibration bar with a ruler. If it's not exactly 50mm, your
  printer rescaled the page — fix that before anything else, every hole position depends on it.
- **Measure your actual HB5050's panel dimensions and wall thickness.** Every number in
  `pipedal-hardware-v2.md` §2.1-2.3a was computed from nominal/estimated dimensions, not a
  measurement of your physical box. If your panel differs from 222×146mm (lid) or the wall
  thickness differs meaningfully from ~2-3mm, re-check clearances before drilling — §2.1 already
  found this layout tight, and §2.3a found a near-miss between the OLED and the USB coupler that
  only cleared because of a deliberate repositioning.
- Dry-fit every part (switches, LEDs, OLED, USB coupler) against the printed template before
  transferring a single mark to metal.

## 1. Mark every hole

**Using:** printed templates, masking tape, the Trojan centre punch.

Both SVGs now carry a small solid black dot at the exact center of every drilled hole (added
2026-09-12), plus their own drill-bit legend printed below the panel outline — use the dot, not
the circle outline, as your punch target; eyeing the center of a printed circle is exactly the
kind of error that erodes the tight LED-to-mode-button clearance in §2.1.

1. Tape both printouts to the panel/wall in their correct orientation (back-left corner = origin,
   per the templates' own coordinate system).
2. Centre-punch straight through the paper at every marked hole center — the punch dents the metal
   so the drill bit can't wander when you start.
3. Peel the templates off. You should have 18 punch marks: 10× ⌀12mm (RESET, TUNER/MUTE, SW1-6,
   PRESET, SNAPSHOT), 2× ⌀5mm (LEDs), 4× ⌀3mm (OLED mounting), 1× ⌀24mm (USB coupler bore),
   1× ⌀7.1mm (preset-browse encoder, §4.2) — plus the OLED cutout outline traced or re-marked
   directly (it's a rectangle, not a punch point).

## 2. Drill the round holes

**Using:** Craftright 3pc Step Drill Set, your existing metric HSS set, CDT cutting oil, a drill.

Work smallest to largest so the panel stays rigid for as long as possible.

**Pilot hole first, on every mark, before the bit sizes below.** Run a **⌀2-3mm** twist bit
straight through each punch dent first — even the ones whose final size is only ⌀3mm/⌀5mm. The
punch dent stops the bit wandering at the start of the hole, but on thin aluminium a bit this size
can still walk sideways mid-hole; a pilot hole gives the bigger bit (or the step drill's point) a
true hole to register in instead of a dimple, so the final hole ends up centred on your mark. This
matters most for the step-drill holes (⌀12mm, ⌀24mm) — the step drill's first step is 4mm, which is
already too big to self-centre reliably from a punch mark alone. If you don't have a ⌀2-3mm bit
spare, the OLED-mounting ⌀3mm step below doubles as the pilot for everything else once you've done
those four.

| Holes | Qty | Bit | From |
|---|---|---|---|
| OLED mounting screws | 4 | **⌀3mm** | your existing HSS set (the step bit starts at 4mm, too big) |
| USB coupler mounting screws | 2 | **⌀3.5mm** (or 3mm if that's the closest you have) | your existing HSS set |
| PRESET LED, SNAPSHOT LED | 2 | **⌀5mm** | your existing HSS set |
| Preset-browse encoder (§4.2) | 1 | **⌀7.1mm** — an odd size the step bit's even increments won't hit exactly; use the closest bit in your HSS set (~7mm), the encoder's own nut/washer covers minor slop | your existing HSS set |
| RESET, TUNER/MUTE, SW1-6, PRESET, SNAPSHOT | 10 | **⌀12mm**, step drill's #1 bit (4-32mm) | Craftright 3pc set |
| USB coupler bore | 1 | **⌀24mm**, step drill's #1 bit (4-32mm) | Craftright 3pc set |

A drop of cutting oil on each hole before drilling, especially the 12mm and 24mm steps — keeps the
bit cutting instead of grabbing/work-hardening the aluminium. Deburr every hole with a file as you
go, don't leave it all to the end.

## 3. Cut the OLED window

**Using:** Ryobi Essential Rotary Tool + metal cutting disc, then a sanding drum or grinding stone
attachment, your existing files.

1. Drill a small pilot hole inside the waste area (any leftover HSS bit, 3-4mm) — the cutting disc
   needs an access point since this cutout doesn't touch the panel edge.
2. Cut with the metal disc **just inside** the marked line (leave ~0.5-1mm), around most of the
   perimeter, but leave a small uncut tab on one side rather than cutting all the way through —
   stops the waste piece breaking free while the disc is still spinning against it.
3. Snap/tap the tab, remove the waste piece.
4. Switch to the sanding drum/grinding stone attachment. Open the hole up to the actual marked
   line and soften the edge in the same pass, test-fitting the OLED bezel as you go.

## 4. Test-fit everything before wiring

Push every switch, LED, the OLED, and the encoder into its hole. Screw the USB coupler in with the
M3 hardware (next step). Confirm nothing binds, the OLED sits flush, the encoder's knob clears the
OLED bezel and turns freely, and the coupler's flange sits flat against the back wall. Fix now, not
after you've soldered wires to everything.

## 5. Fasten the panel-mount parts

| Part | Fasteners | Notes |
|---|---|---|
| Switches (×10) | Whatever nut/washer shipped with the Tayda A-1874 order | The switch's own datasheet lists several optional washer/nut fittings (plain washer ⌀16mm, toothed washer, spring washer) — **check what actually came in the box** before assuming you need to source anything extra. If nothing came with it, a plain M12×0.75 nut is the minimum; Bunnings doesn't stock this thread size, that'd need to come from Tayda/an electronics supplier |
| LEDs (×2) | None — friction-fit or a dab of glue from behind once wired | No screws; these just push into the 5mm hole |
| OLED (×4 screws) | Whatever screws shipped with the OLED module | Check the module's packaging before buying anything — many of these ship with their own small screws/standoffs. Only source separate M2.5/M3 hardware if it genuinely didn't come with any |
| USB coupler (×2 screws) | **M3×10mm bolts + nuts** (Pinnacle 20-pack, see `enclosure-build-reference/pipedal-bunnings-list.md`) | Confirmed needed — this connector's clearance holes ship empty |
| Preset-browse encoder (§4.2) | M7×0.75 hex nut + washer, included with the part | Confirmed from the datasheet (both Tayda A-6329 and Jaycar SR1230 show "NUT 1PC"/"WASHER 1PC") — nothing to source separately |

## 6. Mount the Pico

**Using:** Scotch-Mount Extreme double-sided mounting tape, electrical tape (or a scrap of thin
plastic sheet), see `enclosure-build-reference/pipedal-bunnings-list.md`.

Decided against drilling into the enclosure (breaks the sealed rating, and the panel's too thin —
~2-3mm — for a safe blind/partial hole) and against 3D-printed brackets. Adhesive is the actual
plan here, not a fallback — the Pico is light (a few grams) and stationary once installed, well
within what a proper mounting tape holds long-term.

**Mount it on the underside of the lid, not the case floor** — see `pipedal-hardware-v2.md` §4 for
why: every switch, both LEDs, the OLED, and the encoder are all lid-mounted, so keeping the Pico
with them means only the single USB-coupler cable crosses the lid/body split when you open the
case, instead of ~36 individual wires. Suggested spot: the open gap between the two switch rows —
see `wiring/pipedal-footswitch-wiring-layout.svg` for the to-scale position, X≈85-137, Y≈98-119.
Not yet confirmed against your physical box — check it clears both switch rows and the OLED module
before taping anything down. Two parts to this, do both:

1. **Insulation first, underneath where the Pico will sit** — a layer of electrical tape or a small
   cut piece of thin plastic sheet on the lid, at that spot. This isn't about the mount failing
   being likely, it's that the Pico's underside has exposed solder pads/pins sitting against bare
   conductive aluminium — if the board ever did shift, this is what stops that being a short instead
   of just a rattle. Costs nothing, no reason to skip it.
2. **Mounting tape on top of that**, Pico pressed up against the lid. No need to drill through the
   Pico's own mounting holes or match standoff sizes — a properly-sized piece of quality mounting
   tape is simpler and just as reliable for something this light.

**Ongoing:** since reflashing the Pico goes through the detachable USB coupler (no need to open the
case for that anymore), there's no other routine reason you'd be looking inside this box. Get in
the habit of a **shake test** — pick the box up, gently tilt/shake it, listen for a rattle — before
gigs or on some periodic schedule. That's the actual way you'd catch a loosening mount early, since
nothing in here is instrumented to tell you.

## 7. Wiring

**Using:** soldering iron, solder, the 300mm F-F jumper wires, AWG22 hookup wire, heat-shrink/tape.

Follow `pipedal-hardware-v2.md` §2.4 for the complete wire-by-wire table, or the reorganized,
bench-ready versions in `wiring/`: [`pipedal-footswitch-wiring-reference.md`](./wiring/pipedal-footswitch-wiring-reference.md)
(pin lookup by component + connection-type legend), [`pipedal-footswitch-wiring-procedure.md`](./wiring/pipedal-footswitch-wiring-procedure.md)
(step-by-step with test checkpoints), and [`pipedal-footswitch-wiring-layout.svg`](./wiring/pipedal-footswitch-wiring-layout.svg)
(to-scale physical layout with wire routing). In short:

1. **Ground bus first** — twist-and-solder (or a small terminal strip) joining every switch common,
   both LED cathodes, and the OLED ground, with one wire from that bus to the Pico's `GND`.
2. **Switches** — one wire per switch from its signal lug to its Pico `GPx` pin (§2.4's table has
   the exact pin per switch), cut the F-F jumper's far connector off and solder it to the lug.
3. **LEDs** — anode through its 330Ω-1kΩ resistor to its Pico `GPx` pin, cathode to the ground bus.
4. **OLED** — no soldering, the ribbon jumper plugs straight onto both headers (§4.1).
5. **USB coupler** — micro-USB-B-to-USB-A cable, micro-B end into the Pico, USB-A end into the
   coupler's inside face. No soldering here either, both ends are factory connectors.
6. **Preset-browse encoder (§4.2)** — 5 wires: A → GP19, B → GP20, C (common) → ground bus,
   push-switch leg 1 → GP21, push-switch leg 2 → ground bus.
7. **Bundle the loose wire slack** — cable ties at a couple of adhesive-backed mount points, keeping
   runs away from the switch bodies, the OLED, and the encoder shaft. Lower stakes than the Pico's
   own mount — if a cable clip lets go, a wire just droops, it doesn't risk a short.

## 8. Flash the Pico

**Do this before §6 (mounting), not here — it's listed at this point for completeness, but BOOTSEL
is much easier to reach on a bare, unmounted board.** Full step-by-step:
[`wiring/pipedal-pico-flashing-guide.md`](./wiring/pipedal-pico-flashing-guide.md).

Per `pipedal-hardware-v2.md` §4.1's setup list: CircuitPython + `adafruit_displayio_ssd1306`,
`adafruit_display_text`, `adafruit_display_shapes`, `adafruit_midi` libraries, then `midi_logic.py`,
`pitch.py`, `oled_display.py`, `code.py` copied to `CIRCUITPY`. The encoder itself needs no library
— `rotaryio` is a CircuitPython built-in.

## 9. First power-up

1. Plug the outside USB-A-to-USB-A cable into the Pi. Confirm the OLED shows "OLED OK" for 2
   seconds at boot. If it stays blank, check the SPI clock is 1 MHz in `oled_display.py`, and
   that the panel board's resistor jumpers are set to SPI, not IIC (see `pipedal-hardware-v2.md`
   §4.1). After the splash the grid stays blank until `pi_relay.py` sends names; that's normal.
2. Press every switch, confirm the right MIDI lands in PiPedal (`Settings → System MIDI Bindings`
   or `midi_monitor.py` from a laptop).
3. Run `pi_relay.py` on the Pi (`pipedal-next-steps.md` §2.5 has the full bring-up checklist from
   here — the 3x2 grid, then the tuner, then the preset-browse encoder).
