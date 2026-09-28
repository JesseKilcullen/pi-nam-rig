# Footswitch box — wiring procedure

Step-by-step order for actually wiring the box, expanding `pipedal-footswitch-build-guide.md` §7
into full detail with test checkpoints along the way. Pin/wire lookups: see
[`pipedal-footswitch-wiring-reference.md`](./pipedal-footswitch-wiring-reference.md). Physical
layout: [`pipedal-footswitch-wiring-layout.svg`](./pipedal-footswitch-wiring-layout.svg).

Work in this order — each step is testable in isolation with a multimeter before you move on,
which matters more here than usual: the box is aluminium (conductive) and tightly packed, so a
short found after everything's buttoned up costs far more time than one found mid-build.

## 0. Before you start

- [ ] **Pico flashed with CircuitPython + libraries + the 4 firmware files, done on the bare board
  before mounting** — see [`pipedal-pico-flashing-guide.md`](./pipedal-pico-flashing-guide.md).
  BOOTSEL is far easier to reach now than once the Pico is taped in place.
- [ ] All parts test-fitted per build guide §4 — if you haven't re-confirmed this since drilling,
  do it now. Wiring is much harder to redo than a dry-fit.
- [ ] Soldering iron up to temp (~320–350°C for lead-free, lower if using leaded solder), tip
  clean and tinned.
- [ ] Have on hand: the 300mm F-F jumper wires, AWG22 hookup wire, 330Ω–1kΩ resistors (×2),
  heat-shrink or electrical tape, wire strippers, flush cutters, a multimeter set to continuity
  mode.
- [ ] Decide ground bus method now (twist-and-solder vs terminal strip, see the reference doc) —
  it's easier to place before switch wires are already run than to change your mind halfway.

## 1. Mount the Pico on the lid (do this before wiring, not after)

Per build guide §6 / `pipedal-hardware-v2.md` §4: the Pico mounts on the **underside of the lid**,
not the case floor — every switch, LED, the OLED, and the encoder are lid-mounted too, so keeping
the Pico with them means only the USB-coupler cable crosses the lid/body split when the case is
opened, instead of ~36 individual wires. Insulation layer first (electrical tape or thin plastic
sheet on the lid), then double-sided mounting tape, Pico pressed up against it. Suggested position
is in `pipedal-footswitch-wiring-layout.svg` — the open gap between the two switch rows — but
**this isn't measured against your actual box**, only against the nominal panel layout. Confirm it
clears the switch bodies hanging down from both rows and the OLED module before sticking anything
down.

- [ ] Insulation layer placed on the lid
- [ ] Pico taped to the lid, headers accessible from both long edges

## 2. Build the ground bus

Twist-and-solder or terminal strip (§ of the reference doc, pictured step-by-step in
[`pipedal-ground-bus-howto.svg`](./pipedal-ground-bus-howto.svg)) — placed in the open space left
of the OLED (more room there than right next to the Pico on the wall), not right at the Pico
itself. That means **one wire runs the long way from the bus to the Pico's `GND` pin** (~140mm+,
see `pipedal-footswitch-wiring-layout.svg`) — cut that one generously, it's the only ground wire
that has real distance to cover. Build the bus before wires start converging on it; leave that one
long wire connected and ready to plug into the Pico now.

- [ ] Ground bus built and mechanically secure (won't shift when you tug a wire later)
- [ ] One wire from bus → Pico `GND`, connected

## 3. Wire the switches (×10)

Do these one at a time, not all-lugs-then-all-Picos — it's much easier to keep track of which
switch you're on:

0. **Identify this switch's 2 lugs first.** Look for a face on the metal base stamped something
   like `M 1 2 3` (`M` = body-length code, `1 2 3` = the real pin numbers) — wire lugs 1 and 2,
   leave 3 and the whole opposite face alone. No marking, or can't read it? Fall back to a
   multimeter: continuity mode, unpressed, try lug pairs until one goes open→closed while held
   pressed — that's your pair. Either way, a quick multimeter check before soldering is cheap
   insurance. Full method: reference doc's switch section.
1. Cut a 300mm F-F jumper's far connector off, strip ~5mm.
2. Solder that end to the switch's **lug 1** (signal). Leave the third lug in that group, and the
   entire other pole (3 more lugs), unconnected.
3. Run a second wire (or use hookup wire) from **lug 2** to the ground bus, solder both ends.
4. Insulate both new joints (heat-shrink over the lug is tidier than tape in this tight a space).
5. Plug the jumper's remaining female end onto the Pico header pin from the reference doc's table
   (GP2–GP11 depending on which switch).
6. **Test now**, before moving to the next switch: multimeter continuity between that GPIO pin and
   ground bus should read open-circuit with the switch unpressed, closed when pressed. Catches a
   dry joint or a wrong-lug mixup immediately instead of after all ten are done.

Repeat for all 10 (SW1–6, PRESET, SNAPSHOT, RESET, TUNER/MUTE).

- [ ] SW1 wired + tested — [ ] SW2 — [ ] SW3 — [ ] SW4 — [ ] SW5 — [ ] SW6
- [ ] PRESET mode button wired + tested
- [ ] SNAPSHOT mode button wired + tested
- [ ] RESET wired + tested
- [ ] TUNER/MUTE wired + tested

## 4. Wire the LEDs (×2)

1. Identify anode (long leg) vs cathode (short leg / flat side on the body).
2. Solder the resistor in series on the anode lead (either end of the run is fine).
3. Solder a jumper from the resistor's free end to the Pico (GP12 for PRESET, GP13 for SNAPSHOT).
4. Solder the cathode to the ground bus.
5. **Test polarity before pushing the LED into its hole**: touch the Pico's 3V3 pin briefly to the
   anode-side wire (through the resistor, not directly) with the cathode on ground bus — confirm it
   lights. Far easier to fix backwards now than once it's glued in.
6. Push the LED body into its ⌀5mm hole (friction-fit). Add a dab of glue from behind only once
   you're confident you won't need to re-seat it.

- [ ] PRESET LED wired, polarity-tested, seated
- [ ] SNAPSHOT LED wired, polarity-tested, seated

## 5. Connect the OLED

No soldering. Plug a 7-of-10-conductor F-F ribbon jumper onto the OLED's header, then onto the
Pico's matching pins (GP14–18, 3V3(OUT), GND — see the reference doc's table). Double-check the
VCC wire lands on **3V3(OUT), not VBUS/5V** — this is the one OLED mistake that can damage the
display rather than just not light up.

- [ ] Ribbon connected at OLED end
- [ ] Ribbon connected at Pico end, VCC confirmed on 3V3 not 5V

## 6. Wire the encoder

Same pattern as the switches: cut/solder the far end of an F-F jumper to each of the encoder's 5
pins, plug the near end onto the Pico.

| Pin | → |
|---|---|
| A | GP19 |
| B | GP20 |
| C | ground bus |
| SW1 | GP21 |
| SW2 | ground bus |

- [ ] A, B, C wired + tested (continuity flips as you turn the shaft between A/B and C)
- [ ] Push-switch legs wired + tested (continuity closes when pressed)

## 7. USB coupler

No soldering, both ends are factory connectors:

1. Micro-USB-B-to-USB-A cable: micro-B into the Pico, USB-A into the coupler's **inside** face.
2. Confirm the coupler's own M3×10 mounting bolts (build guide §5) are already tight — do this
   before routing the cable so you're not fighting cable tension while you get a screwdriver in.

**This is the one cable that crosses the lid/body split** — the coupler is on the back wall (fixed
to the body), everything else electrical is on the lid with the Pico. Unplug this cable at the
Pico end whenever you need to fully separate the lid from the box; don't rely on stretching it.

- [ ] Inside cable connected, coupler mechanically secure

## 8. Bundle and secure

Cable-tie the loose slack at a couple of adhesive-backed mount points, per build guide §7.7. Keep
runs clear of: switch bodies (don't obstruct travel), the OLED, and the encoder shaft. Nothing
here is electrically load-bearing — a dropped tie just means a drooping wire, not a short — so this
step is about tidiness and long-term reliability, not safety.

- [ ] Wiring bundled, nothing fouling a moving part

## 9. Pre-power checks — do this before the first power-up

The case is bare conductive aluminium and everything above was built inside it. Before plugging
anything in:

- [ ] Multimeter continuity: `GND` (ground bus) to the bare case metal should read **open** —
  nothing is shorting to the enclosure. If it's not open, find the short before proceeding.
- [ ] Multimeter continuity: each `GPx` pin you wired to ground bus should read **open** with its
  switch unpressed. A closed reading with nothing pressed means a solder bridge or a wire on the
  wrong lug.
- [ ] Visual pass: no bare wire touching another bare wire or the case anywhere in the bundle.
- [ ] Shake test (build guide §6): pick the box up, tilt/shake gently, listen for a rattle —
  confirms the Pico's tape mount and the ground bus are both still solid after all the handling
  above.

Once all of these pass, you're ready for `pipedal-footswitch-build-guide.md` §8 (flash the Pico)
and §9 (first power-up).
