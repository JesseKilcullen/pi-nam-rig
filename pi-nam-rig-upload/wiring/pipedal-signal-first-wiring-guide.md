# Wiring footswitches, OLED, and encoder — ground bus deferred to last

Alternative order to `pipedal-footswitch-wiring-procedure.md`: signal wiring first (footswitches,
OLED, encoder), ground bus built last instead of second. Same end result, same parts, same pin
table in `pipedal-footswitch-wiring-reference.md` — this doc only changes the sequence and what
you leave open in the meantime.

Lug/pin positions and distance estimates, pictured: [`pipedal-signal-first-wiring-diagram.svg`](./pipedal-signal-first-wiring-diagram.svg).

**Why this works electrically:** an unconnected ground wire just means that switch/encoder input
can't complete its circuit yet — the Pico's internal pull-up holds the GPIO pin high regardless, so
it reads as "not pressed" and stays that way until the ground side is joined later. No risk, no
partial-short, nothing to damage — it's simply non-functional until step 4 (the bus) exists. The
OLED is unaffected either way — its ground is one wire in the ribbon cable, going straight to its
own Pico `GND` pin, never through the bus at all.

**What's different from the main procedure doc:** the "test continuity between GPIO and ground
bus" checkpoint in the original step-by-step doesn't work yet, since the bus doesn't exist. You
still get a per-switch check (below), just a different one — the full GPIO-to-ground test happens
once, in a batch, after the bus is built.

**Lug names, so "lug 1/2/3" isn't the only handle on them:** standard switch terminology is
**COM** (common — always in circuit), **NO** (normally open — disconnected at rest, joins COM when
pressed), **NC** (normally closed — the opposite, not used here). Your marked "1 2 3" map to these,
but which specific number is COM vs NO isn't confirmed from a datasheet image, and **it doesn't
matter for this build** — the GPIO and the ground bus can go on either of the two connected lugs,
since a momentary switch just makes/breaks a connection between them symmetrically. So: whichever
of your two marked lugs, call one **COM/lug 1** and the other **NO/lug 2** for your own bookkeeping
and stay consistent per switch — the electrical result is identical either way round.

**Wire length estimates below assume the Pico sits on the back wall, roughly below/near the
encoder side (low X, opposite the USB coupler) — not yet confirmed from your photo.** These are
rough planar distances plus slack, meant to tell you which stock length to reach for, not exact
cut lengths. If the Pico ends up somewhere meaningfully different, treat the longer-distance rows
as the ones to re-check.

| From | Approx. straight-line distance to Pico | Reach with |
|---|---|---|
| RESET, SW1 | ~50-90mm (near side) | 300mm F-F jumper — lots of slack |
| SW2, Encoder | ~90-110mm | 300mm F-F jumper — comfortable |
| SW3, SW4, SW5 | ~110-140mm | 300mm F-F jumper — comfortable |
| SW6, PRESET, SNAPSHOT | ~140-200mm (far side of the panel) | 300mm F-F jumper — tighter, but still fits |
| TUNER/MUTE | ~150-160mm | 300mm F-F jumper — comfortable |

**Bottom line: the 300mm jumpers already on your parts list cover every switch and the encoder**,
even the farthest ones, with room to dress/coil the slack on the near ones rather than cut them
shorter. No need to source or cut custom lengths per switch.

**OLED ribbon — worth double-checking, this one changed.** The original "10-15cm ribbon" guidance
assumed the Pico sat right next to the OLED (the old middle-of-the-lid plan). With the Pico now on
the back wall, the OLED-to-Pico distance is roughly ~90-100mm planar plus routing slack — a 15cm
ribbon is now closer to its limit than "plenty of slack to spare." **Consider a 20cm ribbon
instead** if you're buying one now, or confirm your 15cm actually reaches with slack before you
commit to that spot.

## 1. Footswitches (×10)

Per switch:

1. **Identify the 2 lugs** — look for the `M 1 2 3` stamp (or similar) on the base; wire 1 and 2,
   leave 3 and the opposite face's whole pole unconnected. No marking or unsure? Multimeter
   continuity, unpressed: try pairs until one goes open→closed while held pressed. **Do this check
   now, on the switch alone, before any wire touches it** — it doesn't depend on the Pico or the
   bus, so there's no reason to defer it. Label your pair **COM** and **NO** (either way round,
   see the naming note above) so you're not just tracking bare numbers.
2. Cut a 300mm F-F jumper's far connector off, strip ~5mm, solder it to **lug 1 (COM)**. Plug the
   jumper's remaining female end onto the switch's `GPx` pin (GP2–GP11, per the reference doc's
   table — SW1–6, PRESET, SNAPSHOT, RESET, TUNER/MUTE). Length check: see the distance table above
   — every switch reaches comfortably on the stock 300mm jumper.
3. Solder a second wire onto **lug 2 (NO)** — but leave its *other* end unterminated for now.
   Strip it, twist the strands so they don't fray, and cap it: a small piece of heat-shrink, or
   just a twist of tape, so the bare copper can't touch anything else while it's dangling. **Don't
   plug or solder this end to anything yet.** Cut this one a bit long (similar to the jumper's
   length) rather than short — easier to trim to fit the bus later than to find it's too short.
4. Insulate the COM and NO joints at the switch end as usual (heat-shrink over the lug).

Repeat for all 10. You'll end up with 10 loose, capped ground tails plus the Pico's `GPx` pins all
connected — functionally inert until the bus joins them, which is expected.

- [ ] SW1 — [ ] SW2 — [ ] SW3 — [ ] SW4 — [ ] SW5 — [ ] SW6
- [ ] PRESET — [ ] SNAPSHOT — [ ] RESET — [ ] TUNER/MUTE

## 2. OLED — fully done now, nothing deferred

No soldering, no bus dependency. Plug the 7-of-10-conductor F-F ribbon jumper onto the OLED's
header, then onto the Pico's matching pins:

| OLED pin | Pico pin |
|---|---|
| GND | GND |
| VCC | 3V3(OUT) — **3.3V only, never VBUS/5V** |
| SCL | GP14 |
| SDA | GP15 |
| RES | GP16 |
| DC | GP17 |
| CS | GP18 |

Match by the label printed on your board's silkscreen, not by position (see the reference doc's
OLED section for why). Double-check VCC specifically before anything gets powered on later.

- [ ] Ribbon connected both ends, VCC confirmed on 3V3 not 5V

## 3. Encoder

Same signal-first pattern as the switches. All 5 pins are named on the part itself (no lug-number
guessing here): **A**, **B** (quadrature signal), **C** (their shared common/ground), **SW1**
(push-switch signal), **SW2** (push-switch's other leg, ground). Distance to Pico: ~90-110mm per
the table above — a 300mm jumper on each has plenty of slack.

1. Cut/solder the far end of an F-F jumper to pin **A**, plug the near end onto **GP19**.
2. Cut/solder the far end of an F-F jumper to pin **B**, plug the near end onto **GP20**.
3. Cut/solder the far end of an F-F jumper to the push-switch's **SW1** leg, plug the near end onto
   **GP21**.
4. Solder a wire onto pin **C** (the quadrature common) — cap the far end, same as the switch
   ground tails. Don't join it to anything yet. Cut it long, same reasoning as the switch tails.
5. Solder a wire onto the push-switch's **SW2** leg — cap the far end too.

- [ ] A, B wired to GP19/GP20
- [ ] Push-switch (SW1) wired to GP21
- [ ] C and SW2 wired with capped tails, ready for the bus

## 4. When you're ready to come back for the ground bus

You'll have **12 capped ground tails** waiting (10 switches + encoder's C + SW2) — LEDs aren't
covered by this doc (their 2 cathodes add 2 more if you're deferring those too, using the same
capped-tail approach). Uncap them all, follow
[`pipedal-ground-bus-howto.svg`](./pipedal-ground-bus-howto.svg) and the reference doc's "Ground
bus" section to twist/solder (or terminal-strip) them together with one wire onward to the Pico's
`GND`.

**Once the bus is built, do the full continuity pass** from the main procedure doc's step 9 before
first power-up: `GND` to bare case metal should read open, and each `GPx` pin should read open with
its switch unpressed, closed when pressed. This is your first real chance to catch a lug mixup or a
dry joint from everything you wired in this pass — nothing could be tested end-to-end until now.
