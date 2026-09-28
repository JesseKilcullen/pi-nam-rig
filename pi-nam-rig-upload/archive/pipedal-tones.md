# Five Tones — Victory Kraken rig, Rabea-inspired

> ### STATUS — superseded, kept for rationale
>
> **Read [`pipedal-session-handoff.md`](./pipedal-session-handoff.md) first.** As of 2026-09-05 this doc is *historical*: it describes the
> original **five**-preset, snapshot-free design.
>
> What actually shipped: **six presets, four snapshots each**, plus a TS9
> boost, two fuzz captures and preset 6 (Loathe, Peavey 6505 + HM-2).
> **Control values here are superseded by `build-kraken-presets.py`**,
> which is the only source of truth — and at least one value in this doc
> was wrong in a way nobody could hear: `hiCut`/`hmfC` on the parametric
> EQ are in **kHz**, not Hz.
>
> Still valid and worth reading: the capture choices, the reasoning about
> why there is no overdrive *plugin*, and §6 on level matching.

---

Five **separate presets**, each with its own chain. Tuner first in all of them.
Switching between presets rebuilds the graph, so expect a gap — fine between
songs. (Seamless switching would need snapshots inside one preset; see
[`pipedal-data-model.md`](./pipedal-data-model.md).)

Every control name below is the **real LV2 symbol**, read off your Pi — so these
drop straight into the bank JSON.

Related: [`pipedal-phase2.md`](./pipedal-phase2.md) §8b (writing presets by
script) · [`pipedal-nam-rig-plan.md`](./pipedal-nam-rig-plan.md)

---

## 0. Captures to download first

**There is no Super Kraken (VX100) capture on TONE3000.** The closest — and same
lineage, since the Super Kraken is Victory's evolution of it, developed with
Rabea — is the **VX Kraken**. Download inside PiPedal's TONE3000 integration so
they land on the Pi directly. `.nam` files are platform-independent JSON, so
there is no Linux/Windows distinction and nothing to copy over.

| Pack | Author | Use it for |
|---|---|---|
| [Victory VX Kraken – A2](https://www.tone3000.com/tones/victory-vx-kraken-full-a2-70097) | @leenykeany | **Primary.** 16 captures: Gain I & II at gain 5/7/8/10 + TrebleBoost variants. Retrained for NAM A2 |
| [VX Kraken – DI & Full Amp+Cab](https://www.tone3000.com/tones/victory-vx-kraken-di-full-ampcab-nam-49914) | @sternini75 | The **DI (no cab)** version, for when you go into the Blackstar's FX return |
| [Kraken VX MKII](https://www.tone3000.com/tones/victory-kraken-vxmkii-teaser-tones-from-pack-20full-20di-44405) | @fabianratsak | 40 captures, 20 full + 20 DI. Biggest DI set |

**The Kraken pack has no clean channel** — Gain I and Gain II are both drive
modes. So presets 1 and 2 use a genuinely clean capture. `1960 Fender Tweed
Deluxe 5E3 - Clean.nam` is already on your Pi and suits the chimey brief well.

> **On "DI":** it means preamp **and** power amp minus the cab, not preamp-only.
> True preamp-only Kraken captures do not appear to exist. Irrelevant on
> headphones with a cab sim; it matters for the two-power-amps issue in the main
> plan's section 2.1 once you go into the amp.

### Why there is no overdrive pedal in these chains

TooB ships no OD/dist/fuzz, and it is the only plugin collection installed. You
*can* add `guitarix-lv2` (`sudo apt install guitarix-lv2`, then restart
`pipedald`) for around 100 dirt models. But for a captured amp, gain is better
bought from the capture: the leenykeany pack gives you two channels x four gain
settings **plus TrebleBoost variants** — 16 flavours of the real
boost-into-Kraken relationship. A generic distortion in front of a NAM capture
is a muddier, different thing.

Where a pedal would genuinely earn its place is a **clean boost** for solos
(preset 5 uses `toob-input_stage` `trim` for exactly that) and a **fuzz** for
texture, which no capture covers.

---

## 1. Clean — chimey, glassy

Rabea's brief for the Kraken's clean mode was *"ambient chimey glassy
goodness"*, and he has said he plays chimey cleans and low-gain ambient far more
now. So: bright, open, a little space, nothing squashed.

```
[tuner] -> [noise-gate] -> [input_stage] -> [NAM] -> [cab-ir]
        -> [three-band-eq] -> [delay] -> [freeverb]
```

| Plugin | Settings |
|---|---|
| `toob-tuner` | `MUTE 0`, `REFFREQ 440`, `THRESHOLD -60` |
| `toob-noise-gate` | `threshold -90` (effectively off — cleans do not need it) |
| `toob-input_stage` | `trim 0`, `locut 80`, `bright 0` |
| `toob-nam` | capture **Fender Tweed 5E3 Clean** · `inputGain -12` · `toneStack 3` · `bass 5` `mid 5` `treble 6` · `outputGain 0` · `gate -120` |
| `toob-cab-ir` | `M25 UL 1960TV 4x12 SM57 2.00in 0.0in 7603.wav` · `direct_mix -40` |
| `toob-three-band-eq` | `bass 4.5`, `mid 4.5`, `treble 6.5`, `gain 0` |
| `toob-delay` | `delay 380`, `feedback 18`, `level 12` — air, not a repeat you notice |
| `toob-freeverb` | `dryWet 0.18`, `roomSize 0.45`, `damping 0.35`, `tails 1` |

**Dial by ear:** the NAM's `treble` and the EQ's `treble` do different jobs. The
NAM's sits inside the amp model, before the distortion stage; the EQ's is after
the cab. Push the EQ for glassy, the NAM for bite.

---

## 2. Ambient — washy, modulated, big

Same clean capture, all the space. This is the preset that justifies stereo.

```
[tuner] -> [noise-gate] -> [input_stage] -> [NAM] -> [cab-ir]
        -> [chorus] -> [multi-echo-stereo] -> [convolution-reverb-stereo]
```

Mono blocks first, stereo last — per `pipedal-phase2.md` section 5, a mono
plugin placed after a stereo one silently discards the right channel.

| Plugin | Settings |
|---|---|
| `toob-tuner` | as above |
| `toob-noise-gate` | `threshold -90` |
| `toob-input_stage` | `trim 2`, `locut 90` |
| `toob-nam` | capture **Fender Tweed 5E3 Clean** · `inputGain -14` · `bass 4` `mid 5` `treble 6` |
| `toob-cab-ir` | same 1960TV IR as preset 1 |
| `toob-chorus` | `rate 0.22`, `depth 0.35`, `dryWet 0.40` — slow and wide, not seasick |
| `toob-multi-echo-stereo` | `tap1 1` `delay1 500` `level1 -8` `feedback1 30` `pan1 -0.4` · `tap2 1` `delay2 750` `level2 -12` `feedback2 25` `pan2 0.4` · `tap3 0` `tap4 0` · `master 0` `tails 1` |
| `toob-convolution-reverb-stereo` | `St. Margaret's Church.wav` · `reverb_mix -6` · `time 30` · `width 1` · `tails 1` · `stretch 1` |

**The two taps at 500 and 750 ms** are a 2:3 relationship — one straight, one
dotted-feeling, panned opposite. That is the trick behind most "how is that one
guitar" ambient parts. Try `Koli National Park - Winter.wav` if you want it
enormous, `Jack Lyons Hall, University of York.wav` for something more
controlled.

---

## 3. Crunch — Kraken Gain I, held back

```
[tuner] -> [noise-gate] -> [input_stage] -> [NAM] -> [cab-ir]
        -> [three-band-eq] -> [delay] -> [freeverb]
```

| Plugin | Settings |
|---|---|
| `toob-noise-gate` | `threshold -60`, `hold 100`, `release 330`, `reduction -60` |
| `toob-input_stage` | `trim 0`, `locut 85` |
| `toob-nam` | capture **Kraken Gain-I G7** · `inputGain -8` · `bass 5` `mid 6` `treble 5` |
| `toob-cab-ir` | `Marshall JCM800 Lead 1960 A (4- SM57, eoc).wav` |
| `toob-three-band-eq` | `bass 4.5`, `mid 5.5`, `treble 5`, `gain 0` |
| `toob-delay` | `delay 340`, `feedback 22`, `level 8` |
| `toob-freeverb` | `dryWet 0.12`, `roomSize 0.35` |

**Mid at 5.5–6 is deliberate.** The Victory voicing has real midrange, and that
is what stops the crunch sounding like a scooped metal preset. Use `Gain-I G5`
for closer to edge-of-breakup, `G8` for more shove.

---

## 4. High-gain rhythm — tight, no delay

Rhythm wants control, not size. The gate does real work here, and there is
deliberately no delay — repeats blur fast palm-muted playing.

```
[tuner] -> [noise-gate] -> [NAM] -> [cab-ir] -> [parametric-eq] -> [freeverb]
```

| Plugin | Settings |
|---|---|
| `toob-noise-gate` | `threshold -45`, `attack 1`, `hold 60`, `release 180`, `hysteresis -6`, `reduction -70` |
| `toob-nam` | capture **Kraken Gain-II G8** · `inputGain -6` · `bass 5` `mid 5.5` `treble 5.5` · `gate -70` |
| `toob-cab-ir` | `M25 UL 1960TV 4x12 SM57 2.00in 0.0in OA30 7603.wav` |
| `toob-parametric-eq` | `loCut 90` · `lmfC 350` `lmfLevel -3` `lmfQ 1.0` · `hmfC 2200` `hmfLevel 1.5` `hmfQ 1.5` · `hiCut 12000` |
| `toob-freeverb` | `dryWet 0.06`, `roomSize 0.25` — barely there, just stops it sounding dead |

**The `lmfC 350` / `-3 dB` cut** is the single most useful move on a high-gain
tone: it clears the boxy low-mids without scooping out the character. `loCut 90`
and `hiCut 12000` remove flub and fizz that only ever ate headroom.

**Two gates, on purpose:** `toob-noise-gate` catches the guitar before the
model; the NAM's own `gate` catches what the distortion generates after it. Set
the first, then only reach for the second if it still hisses between chugs.

---

## 5. High-gain lead — boosted, singing, wet

```
[tuner] -> [noise-gate] -> [input_stage] -> [NAM] -> [cab-ir]
        -> [parametric-eq] -> [delay] -> [convolution-reverb-stereo]
```

| Plugin | Settings |
|---|---|
| `toob-noise-gate` | `threshold -50`, `hold 80`, `release 250` |
| `toob-input_stage` | `trim 4` — the clean boost. Level, not dirt |
| `toob-nam` | capture **Kraken Gain-II G10 TrebleBoost** · `inputGain -6` · `bass 4.5` `mid 6` `treble 5.5` |
| `toob-cab-ir` | `Marshall JCM800 Lead 1960 A (4- SM57, eoc).wav` |
| `toob-parametric-eq` | `loCut 100` · `lmfC 800` `lmfLevel 2` `lmfQ 1.2` · `hmfC 2500` `hmfLevel 2` `hmfQ 1.5` · `hiCut 13000` |
| `toob-delay` | `delay 375`, `feedback 32`, `level 20` — dotted 8th at 120 bpm |
| `toob-convolution-reverb-stereo` | `Arthur Sykes Rymer Auditorium.wav` · `reverb_mix -10` · `time 30` · `width 1` |

**Mid at 6 plus the 800 Hz bump** is what makes a lead cut without turning up.
The TrebleBoost capture already does the pedal-in-front job, so `input_stage`
`trim` exists purely for volume — that is your solo boost.

---

## 6. Level matching — do this last, and do not skip it

A clean capture and a Gain-II capture at identical settings are wildly different
loudnesses. Per `pipedal-phase2.md` section 6:

1. Pick **preset 3 (Crunch)** as the reference and set the amp for it.
2. Play the same riff through all six.
3. Adjust each preset's `toob-nam` `outputGain` until they sit at the same
   *perceived* loudness — the lead should sound fuller, not louder.
4. Leave the interface output knob and the amp alone for the whole pass.

Do it near playing volume. Levels matched quietly do not hold up loud.

**Not NAM Calibration.** That is one voltmeter measurement of your guitar's
output, it needs metadata most TONE3000 captures lack, and the PiPedal docs say
outright there is no requirement to do it. `inputGain` and `outputGain` are the
controls that matter.

---

## 7. Going into the Blackstar instead of headphones

Three changes when you plug into the FX return:

- **Bypass `toob-cab-ir`** in all six presets — your Celestions are the cab.
- **Swap to the DI captures** from the MKII or sternini75 packs.
- **Re-check levels.** The whole gain path changed.

Each preset needs bypassing individually — there is no global cab-off switch.
And now that snapshots exist, note that **bypass is stored per snapshot**, so
it is four edits per preset, not one. Do it in the generator, not the UI.

---

## 8. CPU note

Phase 1 measured **~27–28%** of one core with one NAM + tuner + gate + cab-sim +
delay. Presets 2 and 5 are heavier: `toob-cab-ir` and
`toob-convolution-reverb-stereo` are both convolution engines, and preset 2 runs
a multi-tap stereo echo as well. Expect those two to be the most expensive.

Measure with the busiest preset loaded, and keep it under about 70%:

```bash
top -b -H -n 4 -d 2.5 -p $(systemctl show -p MainPID --value pipedald) | grep ppdl_al
```

If either gets tight, in order: swap `toob-cab-ir` for `toob-cab-sim`
(parametric, far cheaper), reduce `multi-echo` to two taps, then turn on TooB
NAM's `Threaded` button, which costs one extra buffer of latency.
