# PiPedal — Presets & Snapshots

**Updated 2026-09-12.** Regenerated directly from `build-kraken-presets.py` and
`add-muse-opeth-presets.py` (the source of truth for both), plus the live bank for
the three by-ear tweaks made this session. Covers all **8** presets, including Muse
and Opeth, and the 2026-09-10 level-match pass.

Snapshot 1 of every preset is its home sound and equals the preset's item
values, so the two always agree. The rest are ordered most-useful-first, so a
3-switch footswitch layout loses the least important one rather than an
arbitrary one. Free slots are left in every preset. Presets 7-8 (Muse, Opeth)
are footswitch-unreachable by design — encoder/OLED-browse-only, see
`pipedal-next-steps.md` §1.

## The eight presets

| # | Preset | What it's for | Amp capture | Pedal | Cab IR | Master Output Volume |
|---|---|---|---|---|---|---|
| 1 | Clean | Clean bed with a drive toggle on top | Fender Tweed 5E3 Clean | Boss BD-2W Waza *(off)* | 1960TV 4x12 | **+8 dB** |
| 2 | Ambient | Washy, modulated, long-tail textures | Fender Tweed / Kraken Gain-I G5 | Sunface RCA fuzz *(off)* | 1960TV 4x12 | **+3 dB** |
| 3 | Crunch | Edge-of-breakup rhythm, TS9-tightened | Kraken Gain-I G7 | Ibanez TS9 `D0-T6-L10` | JCM800 1960A | 0 |
| 4 | HG Rhythm | Tight palm-muted high gain | Kraken Gain-II G8 | — | 1960TV 4x12 OA30 | 0 |
| 5 | HG Lead | Boosted, singing, wet lead | Kraken Gain-II G10 TrebleBoost | — | JCM800 1960A | **-2 dB** |
| 6 | Massive | **Two amps in parallel, blended.** Gets heavier by snapshot | Kraken Gain-I/II *(top)* + Tweed Clean *(bottom, always on)* | SunFace / Big Muff, into the Kraken *(off at home)* | 1960TV 4x12 | 0 |
| 7 | Muse | JCM800-family rhythm/lead, Big Muff chaos-fuzz break | JCM800 2203/OD808 Gain 7 | EHX Big Muff Pi T5 S9 *(off)* | JCM800 1960A | 0 |
| 8 | Opeth - Ghost Reveries | Prog-death chug, HM-2 buzzsaw texture | JCM800 2203/OD808 Gain 7 (same capture as Muse) | BOSS HM-2 "Chainsaw" *(off)* | JCM800 1960A | 0 |

Master Output Volume is the preset-level fader applied after everything else
— the main tool the 2026-09-10 level-match pass used to bring all 8 presets to
comparable loudness. It's on top of, not instead of, each NAM instance's own
`outputGain` (see the gain-staging table below).

Preset 1 is the only one that changes amp *character* per snapshot via a
pedal; presets 2 and 6 swap the amp capture itself. **Preset 6 is the only
parallel one** — a PiPedal Split node in Mix mode, so both amps run and are
summed rather than switched. Muse and Opeth share the same amp capture
(JCM800 2203/OD808 Gain 7) — neither is a verified match for either band's
actual studio rig (no Diezel VH4, no exact Ghost Reveries capture on this
Pi); both are a reasonable starting point built from what's already
installed.

## Snapshots, and how each differs

### 1 Clean

| # | Snapshot | Difference from home |
|---|---|---|
| 1 | **Clean** | Home. Tweed, delay and a little room. |
| 2 | **Drive** | Blues Driver **on** — edge-of-breakup push, not a lead boost. Only change. |
| 3 | **Solo** | Louder and brighter: amp +3.5 dB, treble +0.5, more delay. |
| 4 | **Dry** | Delay and reverb **off**. Naked amp. |
| 5 | **Wash** | Long: delay out to 520 ms with more feedback, big reverb. |

### 2 Ambient

Glass is the only snapshot on the Fender; the other three move to the
low-gain Kraken for more body under the effects.

| # | Snapshot | Difference from home |
|---|---|---|
| 1 | **Glass** | Home. **Fender Tweed**, chorus + multi-tap delay + church reverb. |
| 2 | **Swell** | **Kraken Gain-I G5.** Everything wetter — chorus, all three delay taps, more reverb. |
| 3 | **Fuzz** | **Kraken G5** + Sunface fuzz **on**. |
| 4 | **Fuzz Rolled Off** | Same as Fuzz with the fuzz driven 7 dB softer — the guitar-volume-rolled-back sound. |

### 3 Crunch

| # | Snapshot | Difference from home |
|---|---|---|
| 1 | **Crunch** | Home. G7 with the TS9 in front as a clean boost. |
| 2 | **Raw** | TS9 **off**. Looser, less tight low end. |
| 3 | **Push** | Amp capture swapped to **G8** — more gain, same everything else. |
| 4 | **Lead** | +3 dB, mid +1, delay louder and longer-tailed. |

### 4 HG Rhythm

| # | Snapshot | Difference from home |
|---|---|---|
| 1 | **Rhythm** | Home. Tight G8, low-mid cut, barely any reverb. |
| 2 | **Solo** | +3.5 dB, presence +2, more reverb. |
| 3 | **Tight** | Faster, harder gate and `loCut` up to 110 Hz — staccato chugs. |
| 4 | **Wide** | Bigger room, `hiCut` 12 → 13 kHz — slightly brighter, not rolled back. |

### 5 HG Lead

| # | Snapshot | Difference from home |
|---|---|---|
| 1 | **Lead** | Home. Treble-boosted G10, delay and hall reverb. |
| 2 | **Rhythm** | −3 dB and much drier — the same amp as a rhythm sound. |
| 3 | **Solo+** | +2.5 dB with more delay feedback and level. |
| 4 | **Dry** | Delay and reverb **off**. |

### 6 Massive

The only parallel preset. A Split in **Mix** mode sums two chains:

```
top:     fuzz -> Kraken Gain-I/II
bottom:  Tweed Clean  (always on, never changes)
```

The fuzz lives **inside the top chain**, so it hits the Kraken only — the
Tweed underneath stays clean, and that is what holds the note definition
together on the fuzz snapshots. Heaviness comes from the top capture walking
up the ladder plus the blend shifting toward it.

| # | Snapshot | Top (dirty) | Fuzz | mix |
|---|---|---|---|---|
| 1 | **Massive** | Kraken Gain-I **G5** | off | 0 |
| 2 | **Heavier** | Kraken Gain-I **G7**, driven harder | off | −0.30 |
| 3 | **Heaviest** | Kraken **Gain-II G8** — channel change | off | −0.20 |
| 4 | **Fuzz Low** | Kraken **Gain-II G8** (matches Heaviest, since 2026-09-10) | **SunFace RCA V7 F10 C3** — softer/cleaner-guitar-volume capture (not the hot C10 used elsewhere) | −0.10 |
| 5 | **Fuzz High** | Kraken **Gain-II G8** | **Big Muff Pi T5 S9** — silicon, huge sustain | +0.10 |

Fuzz Low and Fuzz High are different **circuits**, not two levels of one
pedal. Both fuzz snapshots' top capture was moved from G5 to G8 (matching
Heaviest) on 2026-09-10, and Fuzz Low's own fuzz capture softened from the
hot `SunFace V7 F10 C10` to the gentler `V7 F10 C3` — the fuzz supplies the
dirt now, so this keeps the top amp's gain consistent with the rest of the
heavy end of the bank rather than an outlier.

**Three NAM instances, and the Pi 4 handles it** (tested 2026-09-05). All
three run constantly — a blend is not a switch, and a bypassed instance still
costs. Still the heaviest preset in the bank by a distance, so re-measure
after any change here. Only xruns seen were on changing preset mid-playing,
which is the graph-rebuild gap rather than this preset.

⚠️ **The `mix` sign is unverified.** There is no TTL for the Split node, so
`check_ranges()` cannot validate it and the factory presets only show that
values skew negative; negative is *assumed* to favour the top chain. If
Heavier and Heaviest come out cleaner rather than dirtier, flip the signs.

### 7 Muse

Encoder/OLED-browse-only — not on the direct 6-switch footswitch layout.

| # | Snapshot | Difference from home |
|---|---|---|
| 1 | **Rhythm** | Home. JCM800/OD808 Gain 7, chorus + delay + a little room. |
| 2 | **Fuzz Lead** | Big Muff **on** in front of the amp — the "Plug In Baby"/"Hysteria" chaos-fuzz break. Only change. |
| 3 | **Clean Arp** | Amp capture swapped to **1960 Gibson Rhythm King - Edge of Breakup**, inputGain −14, outputGain **0** *(lifted from −1, 2026-09-12 — read quiet next to the amp snapshots)*, more chorus/reverb. |
| 4 | **Big Ambient** | Delay out to 480 ms with more feedback/level, bigger reverb. |
| 5 | **Solo Boost** | +3.5 dB, mid +1, treble +0.5, more delay. |

### 8 Opeth - Ghost Reveries

Encoder/OLED-browse-only — not on the direct 6-switch footswitch layout. Same
gate shape as "4 HG Rhythm" — proven tight-but-not-choppy for percussive
high-gain riffing.

| # | Snapshot | Difference from home |
|---|---|---|
| 1 | **Chug** | Home. JCM800/OD808 Gain 7, tight gate, dark-ish PEQ, short delay/room. |
| 2 | **Buzzsaw** | BOSS HM-2 "Chainsaw" **on** in front of the amp — the classic Swedish death-metal buzzsaw. Only change. |
| 3 | **Heavy** | Amp capture swapped to **Peavey 6505 1992 Lead - Chug**, inputGain −8, outputGain **−3** *(dropped from −1, 2026-09-12 — too hot next to the rest of the bank on real speakers)*. |
| 4 | **Lead** | +3 dB, PEQ `hmfLevel` +2, more delay feedback/level. |
| 5 | **Clean Prog** | Amp capture swapped to **1960 Fender Tweed Deluxe 5E3**, inputGain −14, outputGain **0** *(lifted from −1, 2026-09-12 — same "clean read quiet" fix as Muse's Clean Arp)*, PEQ opened up (`loCut` 80, `hiCut` 14 kHz), longer wetter delay/reverb. |

## Gate settings

| Preset | threshold | hold | release | reduction | attack | hysteresis |
|---|---|---|---|---|---|---|
| 1 Clean | −80 | 100 | 330 | −60 | 1 | −6 |
| 2 Ambient | −80 | 100 | 330 | −60 | 1 | −6 |
| 3 Crunch | −60 | 100 | 330 | −60 | 1 | −6 |
| 4 HG Rhythm | −55 | 90 | 220 | −45 | 3 | −12 |
| 5 HG Lead | −50 | 80 | 250 | −60 | 1 | −6 |
| 6 Massive | −55 | 90 | 260 | −45 | 3 | −12 |
| 7 Muse | −70 | 90 | 250 | −50 | 2 | −9 |
| 8 Opeth | −55 | 90 | 220 | −45 | 3 | −12 *(same shape as 4 HG Rhythm)* |

`reduction` sits well short of a full mute (−60 floor) everywhere except
presets 1-3 and 5, deliberately: a full mute is what makes gate action
audible as a click on note tails, especially on the high-gain presets.
`hysteresis` is widened on the high-gain presets (4, 6, 8) to stop a decaying
note near the threshold from chattering open/shut.

## NAM gain staging

| Preset | Pedal in / out | Amp in / out | Amp bass / mid / treble |
|---|---|---|---|
| 1 Clean | −10 / −4 *(Blues Driver, off at home)* | −12 / 0 | 5 / 5 / 6 |
| 2 Ambient | −12 / −8 *(Sunface fuzz, off at home)* | −14 / 0 | 4 / 5 / 6 |
| 3 Crunch | −10 / −6 *(TS9)* | −8 / 0 | 5 / 6 / 5 |
| 4 HG Rhythm | — | −6 / **−4** | 5 / 5.5 / 5.5 |
| 5 HG Lead | — | −6 / 0 | 4.5 / 6 / 5.5 |
| 6 Massive *(top)* | −12 / −8 *(fuzz, off at home)* | −14 / 0 | 5 / 5.5 / 5.5 |
| 6 Massive *(bottom)* | — | −12 / **−3** | 5.5 / 5 / 5.5 |
| 7 Muse | −10 / −8 *(Big Muff, off at home)* | −8 / **−1** | 5 / 5.5 / 5.5 |
| 8 Opeth | −10 / −8 *(HM-2, off at home)* | −8 / **−1** | 5 / 5 / 5.5 |

These are the **item-level (home snapshot) values**; several snapshots
override `outputGain` further via `rel()` deltas on top of this baseline —
see the per-preset tables above. Every NAM instance runs `Threaded` on and
`Quality` (`modelSize`) 0. Pedal captures use tone stack Bypass, amp captures
Baxandall. Presets 1, 2, 3, 7 and 8 run 2 NAM instances; preset 6 runs 3
(§ below). 4 simultaneous instances is untested.

**Levels: matched (2026-09-10 pass, tweaked further 2026-09-12).** The
primary tool was each preset's **master Output Volume** (see the preset
table above), not NAM's `outputGain` — that control sits mid-chain, before
Cab IR/EQ/Reverb, so it's better used for headroom than for final loudness
matching. On top of that pass, three snapshot-level `outputGain` values were
tuned by ear on studio monitors on 2026-09-12: Muse "Clean Arp" and Opeth
"Clean Prog" both −1 → 0, Opeth "Heavy" −1 → −3. See the per-preset tables
above and `pipedal-next-steps.md` §1.

## Preset 6 detail: three NAM instances

**Three NAM instances, and the Pi 4 handles it** (tested 2026-09-05). The old
cap of 2 was a pre-`Threaded` measurement and is superseded — `Threaded`
alone is worth 2.5–3.7×. 4 simultaneous instances is untested. All three of
preset 6's instances run constantly, since a blend is not a switch and a
bypassed instance still costs.

## Historical DSP figures — do not trust

The DSP-load figures that used to live in this section (measured 2026-09-05,
before preset 1 gained a second NAM instance, Ambient gained a delay tap, and
before Muse/Opeth existed) have been removed rather than carried forward
wrong. **Preset 6 is the heaviest in the bank by a wide margin** — it runs
three NAM instances plus chorus, delay and reverb, and plays clean, but no
number has ever been captured for it. If you need current load figures for
any preset, run `pipedal-probe.py` rather than trusting anything written down
here — see `pipedal-presets-howto.md` §7 for the measurement caveats
(the probe's own websocket connection is itself a load).
