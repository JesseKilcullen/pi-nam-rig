# Footswitch box — Bunnings shopping list

For drilling/cutting the footswitch enclosure per `pipedal-hardware-v2.md` §2. Store: Bayswater
(stock not verified — Bunnings blocks scripted stock checks, use each page's own store checker).

## To buy

| Item | Link | Price (AUD) | For |
|---|---|---|---|
| Trojan 125mm Auto Centre Punch | [bunnings.com.au](https://www.bunnings.com.au/trojan-125mm-auto-centre-punch_p0422988) | — | Marking hole centres before drilling — spring-loaded, no hammer needed |
| Craftright 3pc Step Drill Set | [bunnings.com.au](https://www.bunnings.com.au/craftright-3pc-step-drill-set_p0461120) | ~$15 | All the round holes (12mm switches, ⌀24mm USB coupler bore, etc.) |
| Ryobi Essential Rotary Tool RRT090 | [bunnings.com.au](https://www.bunnings.com.au/ryobi-essential-rotary-tool-rrt090_p0456165) | ~$69 | Cutting the rectangular OLED window (~58×30mm) |
| Ryobi 32mm Cutting Disc — 5 Pack | [bunnings.com.au](https://www.bunnings.com.au/ryobi-32mm-cutting-disc-5-pack_p0438403) | — | Metal-rated cutting discs for the rotary tool — the tool's bundled accessories likely don't include one |
| Pinnacle M3 x 10mm Zinc Plated Round Head Bolts and Nuts — 20 Pack | [bunnings.com.au](https://www.bunnings.com.au/pinnacle-m3-x-10mm-zinc-plated-round-head-bolts-and-nuts-20-pack_p0247262) | — | Mounting the USB-A panel coupler (see "Not from Bunnings" below) |
| CDT Cutting Oil 350g | [bunnings.com.au](https://www.bunnings.com.au/cdt-cutting-oil-350g_p0484503) | — | Keeps the step bit and rotary cutting disc cutting cleanly in the aluminium panel, not grabbing/work-hardening the edge |
| Scotch-Mount Extreme Double-Sided Mounting Tape, 2.5cm × 1.5m | [bunnings.com.au](https://www.bunnings.com.au/scotch-mount-extreme-double-sided-mounting-tape-2-5cm-x-1-5m_p3961938) | — | Mounting the Pico to the case floor — no drilling, no 3D-printed bracket needed. See build guide §6 |
| Narva 19×19mm Black Cable Tie Mounts — 5 Pack | [bunnings.com.au](https://www.bunnings.com.au/narva-19-x-19mm-black-uv-weather-resistant-cable-tie-mount-5-pack_p4430668) | — | Anchor points for bundling the loose wire slack — lower stakes than the Pico's own mount, adhesive is fine here |

## Already have — not on the list

Safety glasses, gloves, masking tape, files, metric HSS drill bit set (small sizes — 3mm/3.4mm/5mm
holes for the OLED and LED mounts, plus the closest bit to ⌀7.1mm for the preset-browse encoder,
§4.2 — an odd size the step bit's even increments won't hit exactly). Electrical tape (or a scrap
of thin plastic sheet) for the insulation layer under the Pico, build guide §6 — check you actually
have some; masking tape isn't a substitute, it's not a reliable electrical insulator.

## Not from Bunnings

| Item | Where | Notes |
|---|---|---|
| ~~USB-A female-to-female D-series panel mount coupler~~ | **Bought, 2026-09-12** — Amazon AU, "tunghey," ASIN B0D77L812F | The back-wall connector. See `pipedal-hardware-v2.md` §2.3a and `enclosure-templates/pipedal-footswitch-backwall-drill-template.svg` for the confirmed cutout dimensions and position (X=170mm, not centered — clears the OLED) |
| Preset-browse rotary encoder | Jaycar SR1230 or Tayda A-6329 | See `pipedal-hardware-v2.md` §4.2 — ⌀7.1mm hole, ships with its own nut/washer |
| Matching D-shaft knob | Jaycar **HK7786**, 20mm, 1/4" flattened-side + grub screw, $3.40 (or Tayda A-6888/A-7022, generic 6mm D-shaft, if ordering from there instead) | Fits either encoder above |

## Notes

- Drill the OLED cutout **inside** the marked line with margin — the rotary tool cuts a straight
  edge but it's still far easier to trim a little more than to fix an overshoot.
- Verify panel thickness once you have the actual HB5050 in hand — several of the clearance/fit
  numbers in `pipedal-hardware-v2.md` were computed against an estimated 2-3mm panel thickness,
  not a measurement.
