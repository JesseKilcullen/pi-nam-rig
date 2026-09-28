# DIY guitar-in / headphone-out audio front end for the Pi — exploratory only

Not part of the build plan — this is a "what would it actually take" sketch, kept separate from
`pipedal-hardware-v2.md` on purpose. If you decide to build this, fold it in there; until then
it's just notes.

**Goal:** replicate the two things Pisound actually does for you — a guitar-level input that
doesn't kill your pickup's top end, and a usable audio output — using a bare ADC chip, a bare
DAC chip, some op-amps, and ¼" jacks, wired straight into the Pi's GPIO header. Tested on
headphones first, per your last message, with a tap for line-level amp output later.

## 1. Block diagram

```
                    ┌─────────────┐        ┌──────────────────┐
Guitar ──[¼" TS]───►│ INPUT BUFFER│───────►│  PCM1808 ADC      │──I²S──┐
                    │  TL072      │        │  breakout module  │       │
                    │  (§3)       │        └──────────────────┘       │
                    └─────────────┘                                    ▼
                                                              ┌──────────────────┐
                                                              │  Raspberry Pi     │
                                                              │  GPIO header      │
                                                              │  (I²S, §5)        │
                                                              └──────────────────┘
                                                                        │
                    ┌─────────────┐        ┌──────────────────┐       │
Headphones ◄[¼"TRS]─┤ HP BUFFER   │◄───────┤  PCM5102A DAC     │◄─I²S──┘
                    │ TL072/NE5532│        │  breakout module  │
                    │ + TLE2426   │        └──────────┬────────┘
                    │ virtual gnd │                    │
                    └─────────────┘                    ▼
                                                  [¼" TS line out]──► amp FX return, later
```

## 2. Parts list (BOM)

| # | Part | Real part | Where | Approx AUD | Notes |
|---|---|---|---|---|---|
| 1 | ¼" mono TS jack (guitar in) | generic 6.35mm mono socket | Tayda / Jaycar | $1-2 | |
| 2 | ¼" mono TS jack (line out, tap to amp) | generic 6.35mm mono socket | Tayda / Jaycar | $1-2 | |
| 3 | ¼" stereo TRS jack (headphones) | generic 6.35mm stereo socket | Tayda / Jaycar | $2-4 | |
| 4 | Input buffer op-amp | **TL072** (dual, JFET input) | Jaycar / Altronics / Tayda | $1-2 | FET input = naturally high impedance, good for guitar |
| 5 | Headphone buffer op-amp | **TL072** or **NE5532** (dual) | Jaycar / Altronics / Tayda | $1-2 | second dual op-amp, one channel per ear |
| 6 | Virtual-ground / rail splitter | **TLE2426** | Tayda / element14 (not Jaycar/Altronics stock) | $3-5 | standard part in single-supply headphone amps |
| 7 | ADC breakout | **PCM1808** stereo ADC module | generic import (AliExpress/eBay) | $10-15 landed | outputs I²S straight to the Pi header |
| 8 | DAC breakout | **PCM5102A** stereo DAC module | generic import (AliExpress/eBay), or Jaycar/Core stock similar "PCM5102 DAC" boards | $8-12 | same deal, I²S in |
| 9 | Resistors: 1MΩ ×1, 100kΩ ×2, 10kΩ ×2, 47-100Ω ×2 | generic | Jaycar / Altronics / Tayda | ~$2 total | bias network + gain-setting + headphone series protection |
| 10 | Capacitors: 100nF film ×3, 10-100µF electrolytic ×4, 100nF ceramic ×6 | generic | Jaycar / Altronics / Tayda | ~$4 total | coupling + decoupling |
| 11 | Perfboard + 40-pin GPIO header/jumper wires | generic | Jaycar / Altronics / Tayda | $5-10 | no real "HAT PCB" — perfboard is the honest version of this |
| 12 | (optional) 3.3V LDO regulator, e.g. **AMS1117-3.3** | generic | Tayda | $1-2 | only if you want the analog side on its own clean rail instead of tapping the Pi's 3.3V |

**Total: roughly $40-60 AUD in parts.** Cheaper than Pisound (~$160 AUD landed when it restocks)
or Pisound Micro (~$110-115 AUD), which matches what was flagged before — real money saved, at
the cost of everything in §7.

## 3. Input stage — guitar buffer (TL072, one half of the dual package)

```
                          +3V3 (from Pi header)
                            │
                     R3    ┌┴┐
                  ┌──1MΩ───┤ │
                  │        └┬┘         C2
                  │       node A ──10µF──► GND   (bias smoothing)
                  │         │
   Guitar         │        R4
   ¼" TS ──C1─────┴────────1MΩ──┐
   (tip)   100nF                │        GND
                                 ▼
                          ┌──────────────┐
                          │  TL072 (½)   │
                     node A (bias) ──►+IN │
                          │          -IN ◄┼── feedback (see gain below)
                          │          OUT ─┼──► C3 ──► to PCM1808 "L IN"
                          └──────────────┘    100nF
```

- **R3/R4 (both 1MΩ) form the bias divider** at the Pi's 3.3V rail, giving a mid-rail reference
  (~1.65V) so the AC guitar signal has somewhere to sit — single-supply op-amps can't swing
  around 0V like a guitar signal wants to natively.
- **C1 (100nF) blocks DC** from the guitar cable into the bias node; **R4 (1MΩ) is what the
  guitar pickup actually "sees"** as input impedance — this is the whole reason for this stage.
  Compare: Pisound's own input impedance is only 100kΩ (a genuine limitation the main plan flags
  in §1.1); this DIY version can be *better* on this one spec if you want it to.
- **Gain:** wire OUT straight back to -IN (unity gain, safest first) or add a feedback
  resistor pair (R_fb from OUT to -IN, R_g from -IN to bias node) for a bit of boost if the
  signal's too quiet going into the ADC. Start at unity — you can always add gain in
  software (PiPedal's per-capture Input Gain) instead of fighting with resistor values.
- **C3 (100nF) couples into the PCM1808's L IN pin.** Most PCM1808 breakout boards already
  include their own input biasing/coupling network on-board — check the specific module's
  schematic before assuming this cap is even needed; some boards want a raw AC signal, some
  already expect one referenced to their own bias point.

## 4. ADC → Pi GPIO (I²S)

| PCM1808 pin | Pi GPIO (physical pin) | Signal |
|---|---|---|
| BCK | GPIO18 (pin 12) | Bit clock — **Pi drives this, acting as I²S master** |
| LRCK | GPIO19 (pin 35) | Frame/word clock — Pi drives this too |
| DOUT | GPIO20 (pin 38) | ADC's digital audio → Pi ("PCM_DIN" from the Pi's perspective) |
| SCKI | onboard crystal on most breakout boards, or derived from BCK — check your specific module | System clock the PCM1808 needs; not all breakout boards expose this the same way |
| VCC/GND | Pi 3.3V + GND | Power |

## 5. Pi GPIO → DAC (I²S)

| Pi GPIO (physical pin) | PCM5102A pin | Signal |
|---|---|---|
| GPIO18 (pin 12) | BCK | Same bit clock line as the ADC — **both chips share one clock, driven by the Pi** |
| GPIO19 (pin 35) | LCK | Same frame clock line as the ADC |
| GPIO21 (pin 40) | DIN | Pi's processed audio → DAC ("PCM_DOUT" from the Pi's perspective) |
| VCC/GND | Pi 3.3V + GND | Power |

**This is the trickiest part of the whole build, software-wise, not hardware-wise.** A single
manufactured HAT ships with one overlay that presents its ADC+DAC as one ALSA sound card. Here
you've got two independent breakout boards sharing the same I²S clock lines, and Linux needs to
be told they're one device via a `simple-audio-card` (or `audio-graph-card`) device-tree overlay
— this is a documented, well-trodden path for exactly this PCM1808+PCM5102A combo (it's a common
DIY pairing), but it's real device-tree work, not a checkbox in `raspi-config`.

## 6. Headphone output stage (per channel — duplicate for L and R)

```
   PCM5102A          TLE2426                    TL072 (½, one per channel)
   OUT (L or R) ──C4─┤          node V ──────────►+IN                       R5
   ~2Vrms line level 100nF      (virtual GND)      │           OUT ────47Ω──┬──► ¼" TRS
                                                    -IN ◄───────┘            │    (tip=L,
                                                     (unity buffer,          │     ring=R)
                                                      OUT wired to -IN)      │
                                                                      C5 ────┴──► GND
                                                                      100µF   (coupling,
                                                                                blocks DC
                                                                                offset into
                                                                                headphones)
```

- **TLE2426 creates a stable virtual ground** at the midpoint of whatever single supply you're
  running (3.3V or 5V), which is what lets a single-supply op-amp drive headphones referenced
  around that virtual ground instead of true 0V. This is the standard trick in basically every
  single-supply DIY headphone amp (the "CMoy" design, if you want to read more — same idea here).
- **R5 (47-100Ω) in series with the output** protects the op-amp if the headphone jack ever
  gets shorted (jack half-inserted, cable fault) and slightly current-limits into low-impedance
  cans — a cheap insurance resistor, not a tone component.
- **C5 (100µF) blocks any DC offset** from reaching the headphones directly — small DC offsets
  from an imperfect virtual ground are normal in this topology; the cap is what keeps that off
  your eardrums instead of just a "pop" on power-up.
- **Line-out tap for later (feeding the amp):** take the signal straight from the PCM5102A's
  OUT pin (before this headphone buffer) into the second ¼" TS jack (#2 in the BOM). That's
  already line level and doesn't need the headphone buffering at all — this is exactly the
  same signal the main plan's Pisound design would hand to your amp's FX return.

## 7. Risks and gotchas — the honest list

**Software/config:**
- **The dual-codec device-tree overlay is the single biggest unknown.** If you can't get
  `simple-audio-card` to present both chips as one clean ALSA device, none of the hardware
  matters. Budget real time for this before soldering anything, and search for others who've
  paired this exact ADC+DAC combo — you're very unlikely to be the first.
- **No HAT EEPROM** means no auto-detected overlay — you're manually adding `dtoverlay=` lines
  to `config.txt` and keeping track of exactly what you wired where.

**Analog/noise:**
- **Ground loop hum is the most likely first result, not a rare edge case.** Digital Pi noise
  bleeding into an unshielded perfboard analog front end is the classic DIY-audio-on-Pi failure
  mode. A manufactured HAT solves this with layout discipline you're now responsible for
  yourself — keep analog and digital grounds/routing separated as much as perfboard allows,
  and don't expect it to be silent on the first try.
- **No input protection.** Real products put ESD/overvoltage protection on every external jack.
  A perfboard build plugging straight into GPIO-connected chips has none — a static discharge
  from a cable, or a wiring mistake shorting the wrong pin, risks the ADC/DAC chip or, worse,
  the Pi's GPIO pins themselves (those aren't cheap to replace on a Pi 5).
- **Headphone drive is genuinely limited.** A TL072/NE5532-based buffer will happily drive
  higher-impedance headphones (~100Ω+) at reasonable volume, but low-impedance, power-hungry
  in-ear monitors may end up quiet or thin. Fine for testing the concept; not a substitute for
  a real headphone amp if that turns out to matter to you.

**Mechanical/practical:**
- **This lives on perfboard, not a PCB** — durable enough for bench testing, not for something
  you gig with. Treat it as a prototype that proves the concept, same spirit as the Codec Zero
  discussion earlier: this answers "does a DIY front end work at all," not "is this the final
  build."
- **Time cost is the real price**, not the ~$50 in parts. Soldering, debugging hum, and getting
  the device-tree binding right easily adds up to more hours than the money saved is worth,
  unless the build itself is the point.

**Bottom line:** this is a legitimate, well-trodden DIY path (PCM1808 + PCM5102A is a known
pairing in the hobbyist Pi-audio scene), and it would genuinely work if you push through the
device-tree step. But given Pisound Micro exists at a similar price with the ADC/DAC/power/
layout problems already solved for you — leaving you to add exactly the jacks and buffer stages
above — this is more "worth doing if you want to learn it" than "worth doing to save money."
