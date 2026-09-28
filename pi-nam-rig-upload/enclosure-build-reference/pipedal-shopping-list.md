  # Footswitch box — Shopping List (Jaycar + Bunnings + other)

**Updated 2026-09-12.** Everything still needed to build the footswitch box, pulled together from
`pipedal-hardware-v2.md` §9 and `pipedal-bunnings-list.md` into one list. The Tayda order ($72 AUD)
is already done and isn't repeated here — see `pipedal-hardware-v2.md` §9.1 for what's in it.

## Jaycar

| Item | Code | Price | For |
|---|---|---|---|
| Sealed diecast aluminium enclosure, 222×146×55mm | **HB5050** | $39.95 | The footswitch box itself |
| Rotary encoder w/ pushbutton | **SR1230** | $10.25 | Preset-browse encoder, `pipedal-hardware-v2.md` §4.2 |
| Matching D-shaft knob for the encoder | **HK7786**, 20mm, 1/4" (6.35mm) flattened-side shaft + grub screw | $3.40 | Fits the SR1230 above |

## Bunnings

Store: Bayswater (stock not verified — Bunnings blocks scripted stock checks, use each page's own
store checker).

| Item | Approx price | For |
|---|---|---|
| Trojan 125mm Auto Centre Punch | — | Marking hole centres before drilling — spring-loaded, no hammer needed |
| Craftright 3pc Step Drill Set | ~$15 | Round holes — 12mm switches, ⌀24mm USB coupler bore |
| Ryobi Essential Rotary Tool RRT090 | ~$69 | Cutting the rectangular OLED window (~58×30mm) |
| Ryobi 32mm Cutting Disc — 5 Pack | — | Metal-rated cutting discs — the rotary tool's bundled accessories likely don't include one |
| Pinnacle M3×10mm Zinc Plated Round Head Bolts and Nuts — 20 Pack | — | Mounting the USB-A panel coupler |
| CDT Cutting Oil 350g | — | Keeps the step bit and cutting disc cutting cleanly in the aluminium, not work-hardening the edge |
| Scotch-Mount Extreme Double-Sided Mounting Tape, 2.5cm×1.5m | — | Mounting the Pico to the case floor — no drilling, no bracket |
| Narva 19×19mm Black Cable Tie Mounts — 5 Pack | — | Anchor points for bundling loose wire slack |

**Already have, don't rebuy:** safety glasses, gloves, masking tape, files, a small metric HSS
drill bit set (need 3mm/3.4mm/5mm plus the closest to ⌀7.1mm for the encoder hole), and electrical
tape or a scrap of thin plastic sheet for insulating under the Pico. Masking tape is not a
substitute for the last one — it isn't a reliable electrical insulator.

## Neither Jaycar nor Bunnings

| Item | Where | Status |
|---|---|---|
| USB-A female-to-female D-series panel mount coupler | Amazon AU — "tunghey," ASIN B0D77L812F | **Bought, 2026-09-12** |
| Micro-USB-B→USB-A cable | Anywhere / an old phone cable | Only needed if you don't already have a spare, $0-10 |

## Not on this list — deliberately

The Jaycar **HB6129** electronics enclosure and the Pi 5 / Active Cooler / Pisound HAT stack from
`pipedal-hardware-v2.md` §8 aren't here. That's the separate Audio HAT phase, explicitly
**deferred** per `pipedal-session-handoff.md` — it's not part of the current Pi 4 build. Don't buy
it unless you've decided to un-defer that phase.

## Notes

- Drill the OLED cutout **inside** the marked line with margin — easier to trim more later than to
  fix an overshoot.
- Verify panel thickness once you have the actual HB5050 in hand — several clearance/fit numbers
  in `pipedal-hardware-v2.md` were computed against an estimated 2-3mm panel thickness, not a
  measurement.

Related: [`pipedal-hardware-v2.md`](../pipedal-hardware-v2.md) §9 ·
[`pipedal-bunnings-list.md`](./pipedal-bunnings-list.md) ·
[`pipedal-footswitch-build-guide.md`](../pipedal-footswitch-build-guide.md)
