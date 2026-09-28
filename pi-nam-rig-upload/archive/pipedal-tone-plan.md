# Tone plan — deciding what sounds this rig makes

Not a build phase. This is the doc you sit down with, guitar in hand, to work out **which sounds
you actually need** and **how they map onto PiPedal's presets, snapshots and plugin graph**.
Sections 1–7 are reference. **§8 is the worksheet** — blank tables, fill them in.

Full detail: [`pipedal-nam-rig-plan.md`](../pipedal-nam-rig-plan.md) ·
Build steps: [`pipedal-today.md`](./pipedal-today.md) → [`pipedal-phase2.md`](../pipedal-phase2.md)
Stereo output is a separate question — see [`pipedal-stereo.md`](./pipedal-stereo.md).

> This doc assumes **Design A** (one NAM instance, capture swaps per snapshot). If Phase 1 says
> the swap glitches, everything here still works — §4 becomes the whole plan instead of the
> default, and the capture column in every table stops moving.

---

## 1. What actually shapes your tone here

Ranked by how much it moves the sound. The top two you cannot change, and they colour everything
below them.

| # | Factor | Yours to change? | Impact |
|---|---|---|---|
| 1 | **2×12 Celestions + the room** | No — fixed | **Huge.** Every capture is heard through this one speaker voice |
| 2 | **EL34 power amp + output transformer** | No — fixed | **Huge.** Sets compression, sag, and how breakup feels |
| 3 | Your hands, guitar, pickup, volume knob | Yes, constantly | **Huge.** Bigger than any capture choice |
| 4 | Gain staging — interface GAIN, NAM Calibration, NAM input level | Yes, once per capture | **Huge, and binary.** Wrong and nothing else you do helps |
| 5 | **Drive / boost / EQ in front of the NAM** | Yes, per snapshot | **Large.** Your main tone-shaping lever, and it's free |
| 6 | Amp **Presence** and **Resonance** | Yes, 2 knobs | Moderate — the only analog tone controls you keep (§2.1 of the plan) |
| 7 | **Which capture** is loaded | Yes, per snapshot | Moderate. Less than you expect — see below |
| 8 | Post-NAM EQ / tone stack | Yes, per snapshot | Moderate |
| 9 | Delay / reverb / modulation | Yes, per snapshot | Ambience only. Doesn't fix a core tone |
| 10 | A2 Lite vs A2 Full | Probably not yours to pick at all — see §5.4 | Negligible in this rig anyway (§6 of the plan) |

**A Fender capture through Celestions is not a Fender.** Here is what survives a capture swap and
what doesn't:

| Survives the swap | Doesn't — your amp overrides it |
|---|---|
| Gain structure — how much, and where it breaks up | Cab voice and speaker breakup |
| The preamp's EQ curve and mid character | Mic choice, mic position, off-axis dullness |
| Compression and note bloom | Room ambience of the capture |
| Harmonic flavour (fizzy vs woody vs glassy) | Power-amp character (yours is EL34, always) |

**The practical consequence:** captures differentiate on *gain and voicing*, not on *"which amp is
in the room"*. So pick captures that differ in **how much gain and what shape of mids** they have.
Three captures that are genuinely clean / crunch / high-gain will give you more usable variety than
twelve Marshall variants, which will mostly sound like each other through your 2×12.

> **Set expectations before you download anything.** If you audition captures hoping to hear
> "a Vox in the room", you will be disappointed and blame the captures. Audition them asking
> "does this break up where I want it to, and are the mids in the right place?" — that question
> the rig answers very well.

---

## 2. The building blocks

PiPedal bundles the **TooB** plugin collection (~37 plugins) and nothing else — no third-party
collections are pulled in by the .deb. It will host any LV2 plugin that has **mono or stereo audio
in/out**, is **not a MIDI instrument**, has **no CV ports**, and doesn't depend on a GUI-only
control. PiPedal never runs a plugin's native X11/GTK window; it builds controls from the plugin's
LV2 metadata, and optionally renders a **MOD UI** if the plugin ships one.

### 2.1 The TooB plugins that matter here

| Plugin | Use in this rig | Position | CPU |
|---|---|---|---|
| **TooB Neural Amp Modeler** | The amp. Loads `.nam` / `.aidax` captures | the amp slot | **Dominant** |
| **TooB ML Amplifier** | 33 built-in neural models of amps **and pedals** — TS9, ProCo Rat, Big Muff, DS-1, MetalZone, Crunchbox, Tumnus, Soldano, Mesa Mk2b, Princeton, Dumble, Rockman. Your drive pedals *and* a cheap second amp (§6) | pre-NAM as a pedal, or its own branch | Low–moderate |
| **TooB Warmer** | Gentle overdrive with slow breakup + mild compression. Edge-of-breakup thickening, not a distortion box | pre-NAM | Low |
| **TooB Tuner** | Chromatic tuner — **has its own `Mute` control** (plus Ref Freq, Threshold) | first | Negligible |
| **TooB Noise Gate** | Threshold, Hysteresis, Range, Attack, Hold, Release. Also does "slow gear" swells | first, after tuner | Negligible |
| **TooB Input Stage** | Trim, Gate T, Lo Cut, Bright, Bright F, Hi Cut. Tightening the signal before the amp | pre-NAM | Negligible |
| **TooB Tone Stack** | Real passive amp EQ: Bass/Mid/Treble + Gain, Model = **Bassman / JCM8000 / Baxandall** | pre- or post-NAM | Negligible |
| **TooB Graphic Eq** | 7-band, guitar-centred bands. The classic mid-hump boost in front of the amp | pre-NAM | Negligible |
| **TooB Parametric EQ** (Mono/Stereo) | 4-band fully parametric. Surgical fixes | post-NAM | Low |
| **TooB 3 Band EQ** (Mono/Stereo) | Basic 3-band; matches the EQ in the desktop NAM plugin | either side | Negligible |
| **TooB Tone** (Mono/Stereo) | One-knob tone control | anywhere | Negligible |
| **TooB Delay** | Delay / Level / Feedback, max 3 s. **No tap tempo, no tempo sync** — you type the ms | post-NAM | Low |
| **TooB Multi-Tap Delay** (Mono/Stereo) | 4-tap echo | post-NAM | Low |
| **TooB Freeverb** | Dry/Wet, Room Size, Damping, **Tails**. Your default reverb | post-NAM, last | Low |
| **TooB Convolution Reverb** (Mono/Stereo) | IR-based reverb. Better; costs real CPU | post-NAM, last | **Moderate–high** |
| **TooB CE-2 Chorus** · **TooB BF-2 Flanger** · **TooB Phaser** · **TooB Tremolo** | Boss CE-2 and BF-2 replicas, MXR Phase 90-ish phaser, tremolo with normal + harmonic modes | see §3 | Low |
| **TooB Mix** | Vol L/R, Pan L/R, **Phase L/R (Normal / Inverted)**. The phase switch is the one blending tool the split doesn't have (§5) | at a merge point | Negligible |
| **TooB Volume** | One Volume knob, −INF at the bottom. Level matching and the mute footswitch | last | Negligible |
| **TooB Spectrum Analyzer** | See what you're doing. Diagnostic — pull it out when you're done | anywhere, temporarily | Low |
| **TooB One-Button Looper** / **TooB 4Looper** | Genuinely the best tone-auditioning tool here: loop 4 bars, then switch snapshots with both hands free | post-NAM | Low |
| **TooB Cab IR** · **TooB Cab Simulator** | Cab sim. **You don't want these** — your Celestions are the cab (§2.1 of the plan) | n/a | n/a |
| **TooB Power Stage** | **Deprecated**, and you already have EL34s. Ignore | n/a | n/a |

> **There is no aggressive TooB distortion pedal.** The `[Drive]` box in the plan's diagrams is
> one of: **TooB ML Amplifier** on a pedal model, **TooB Warmer** for gentle thickening, or a
> GxPlugins drive (§2.3). Pick one now so your snapshot tables name a real plugin.

### 2.2 TooB NAM's own controls — read before adding anything

TooB NAM already contains a gate, a passive tone stack and two gain stages. Half the pedals you
were about to add are inside it already.

| Control | Range / values | What it's for |
|---|---|---|
| **Input Gain** | −40 … +40 dB, default 0 | **Your gain knob.** Drives the capture harder or softer. This is how one capture gives you clean *and* crunch (§4) |
| **Output Gain** | −40 … +40 dB, default 0 | Per-snapshot level matching |
| **Noise Gate** | −120 ("Off") … 0 dB | Built-in gate. Often enough on its own |
| **Threaded** | on / off, default **off** | *"Run computation on a separate thread. This allows more instances of NAM to run simultaneously, but adds one extra audio buffer of latency."* This is the whole blend question — see §5 |
| **Tone → Type** | Bassman / JCM8000 / Baxandall / **Bypass** (default) | A real passive tone stack after the model. Defaults to Bypass; turn it on |
| **Tone → Bass / Mid / Treble** | 0 … 10, default 5 | Your amp EQ, since the Blackstar's preamp EQ is out of circuit |
| **Calibration → Input Calibration** | **Raw** / **Calibrated** (default Calibrated) | Greyed out if the loaded model carries no calibration metadata — that's how you tell |
| **Calibration → Value** | −30 … +12 dBu, default **−6** | Your guitar's output level in dBu. See §10.1 |
| **Calibration → Output Calibration** | **Normalized** (default) / Calibrated / Raw | **Leave on Normalized.** Real-world models' output metadata is frequently wrong |
| *Model* | file property | The `.nam` file. **Not a knob** — it's a path property, which is why the Phase 1 swap test exists |

The model picker has a **DOWNLOAD MODELS FROM TONE3000** button; models fetched through it are
**NAM A2**, where models downloaded from the TONE3000 website by hand may still be A1. Use the
button.

Note what is **not** in that control list: **any A2-Full / A2-Lite selector.** An A2 download is a
single slimmable model that a host can run at either size, so it's a runtime decision, not a file
you choose — and TooB NAM exposes no control for it. See §5.4 and §11.

### 2.3 Third-party collections worth installing

PiPedal's own [Using LV2 Plugins](https://rerdavies.github.io/pipedal/UsingLv2Plugins.html) page
rates these. Restart the PiPedal server (Settings → System → Reboot PiPedal) after installing.

| Collection | Install | Why here |
|---|---|---|
| **GxPlugins** ★★★★★ | `sudo apt install gxplugins` (Bookworm), or PiPedal hosts an arm64 .deb | Circuit-simulation drive pedals. **Your best source of dirt** |
| **DPF Plugins** ★★★★★ | `sudo apt install dpf-plugins-lv2` | Pitch shift, reverbs, 3-band EQ |
| **Dragonfly Reverb** ★★★★☆ | `sudo apt install dragonfly-reverb-lv2` | Better reverbs than Freeverb if CPU allows |
| **MDA** ★★★★☆ | `sudo apt install mda-lv2` | 36 utility effects |
| **Guitarix** ★★★☆☆ | `sudo apt install guitarix-lv2` | Amp models — the cheap second amp in §6 |
| **Zam Plugins** ★★★☆☆ | `sudo apt install zam-plugins` | EQ, compression |
| **Calf** ★★★☆☆ | `sudo apt install calf-plugins` | Flanger, filters, reverb, rotary |
| **Invada Studio** ★★★☆☆ | `sudo apt install invada-studio-plugins-lv2` | Delays, distortion, filters, phaser |
| **x42** ★★☆☆☆ | `sudo apt install x42-plugins` | Compressors, tuners |

> **Install GxPlugins and stop.** Every collection you add is hundreds more entries in the picker,
> and picking is your bottleneck, not plugin availability (§10.6). Add more only when you have a
> specific block you can't build from what's there.

---

## 3. Chain order — where each block goes, and why

One rule underneath all of it: **the NAM instance is an amp, so treat everything before it as
pedals into the front of an amp and everything after it as the FX loop.**

```
  Guitar
    │
    ▼
 ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
 │  Tuner   │──►│   Gate   │──►│  Input   │──►│  Drive / │──┐
 │  (Mute)  │   │          │   │  Stage   │   │  Boost   │  │
 └──────────┘   └──────────┘   └──────────┘   └──────────┘  │
  cleanest       kill noise      lo-cut,        "a pedal     │
  signal         BEFORE you      tighten        into an      │
  first          amplify it      the low end    amp"         │
                                                             │
    ┌────────────────────────────────────────────────────────┘
    ▼
 ┌────────────────────────┐
 │   TooB NAM             │  ◄── the amp. Input Gain = gain knob,
 │   + its Tone Stack     │      Tone Stack = amp EQ, model swaps
 └───────────┬────────────┘      per snapshot (Design A)
             │
             ▼   ── everything past here is the FX loop ──
 ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
 │  Post EQ │──►│   Mod    │──►│  Delay   │──►│  Reverb  │──►│  Volume  │
 └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
   fix what      chorus /        never          last, or       level match
   the room      tremolo         before         second-last    per snapshot.
   does          after the       distortion                    Nothing else
                 amp                                           touches it
    │
    ▼
  Interface Main Out L ──► amp FX RETURN ──► EL34s ──► Celestions
```

| Block | Before or after NAM | Why |
|---|---|---|
| Tuner | **Before** | Needs the rawest signal; pitch detection on a distorted signal is worse. Also where its `Mute` belongs — mute early, kill the whole chain |
| Noise gate | **Before** | Gate the guitar's noise before amplification. After the NAM you're chasing the model's own hiss and you chop sustain |
| Compressor | **Before** | It's a pedal. After the amp it just pumps the reverb tail |
| Wah / filter / phaser | **Before** | Classic position. A wah after distortion sounds synthetic |
| Drive / boost / EQ boost | **Before** | A dirt pedal in front of an amp is what your ears expect, and it's the same slot Design B needs (see the note in Phase 2 §5) |
| **TooB NAM** | — | The amp |
| Post EQ | **After** | Corrective, for the room and the Celestions. Not for making the amp sound different — that's the pre-EQ's job |
| Chorus / flanger / tremolo | **After** | Modulating a distorted signal is the studio-standard order |
| Delay | **After** | Before distortion, you distort the repeats and they turn to mush |
| Reverb | **After**, last of the effects | Same reason, more so |
| Volume / level trim | **Absolute last** | So level matching is one knob per snapshot, independent of everything else |

**Two decisions people get wrong here:**

- **Pre-EQ vs post-EQ are different jobs.** EQ *before* the NAM changes how the model distorts —
  a mid boost in front makes the amp break up harder and more nasally, which is what a Tube
  Screamer actually does. EQ *after* the NAM changes what you hear without changing the
  distortion. If a tone is "not aggressive enough", the fix is before. If it's "too harsh in the
  room", the fix is after.
- **Don't stack gates.** TooB NAM has its own `Noise Gate`. Use either that or a separate TooB
  Noise Gate in front, not both — two gates fighting each other is how you get stuttering decay.

---

## 4. Single-amp sounds — the default, not the consolation prize

**One capture, six usable tones.** This is how every one-channel valve amp rig on earth has worked
for sixty years, it costs one NAM instance, it always works, and it survives any Phase 1 outcome.
Start here, and only reach for §5 once you have a rig you'd gig.

The levers, in order of how much they move the sound:

| Lever | What it gets you | CPU |
|---|---|---|
| **NAM `Input Gain`** | The single biggest one. +6 to +12 dB pushes a capture from clean into crunch; −6 backs it off toward clean. It's the amp's gain knob | free |
| **Drive pedal on/off** | Different *flavour* of gain, not just more. A TS-style mid-hump sounds nothing like the model's own breakup | ~0 |
| **Boost with `Level` up and `Gain` down** | More amp, same pedal character — the classic "clean boost into a cooking amp" | ~0 |
| **Pre-EQ shape** | Mid hump = cuts through, breaks up harder. Mid scoop = huge alone, invisible in a band (§10.4) | ~0 |
| **NAM `Tone Stack` type + B/M/T** | Bassman vs JCM8000 vs Baxandall is a real voicing change, free, already in the plugin | ~0 |
| **Gate threshold** | High-gain snapshots need a harder gate than clean ones. Not tone, but it's why a lead snapshot feels tight | ~0 |
| **Delay / reverb on/off + amount** | Sets *size*. Does not fix a core tone | low |
| **`Output Gain`** | Level only. Keep it that way — this is the level-matching knob (§8.4) | free |

**Pick the capture that takes a boost well.** For a one-capture preset you want an
**edge-of-breakup** capture, not a fully clean one and not an already-saturated one:

```
   clean capture          edge-of-breakup capture       saturated capture
        │                          │                           │
   backs off to clean         backs off to clean          always dirty
   won't get dirty            pushes to crunch/lead       can't clean up
   with Input Gain            with Input Gain             pedals just add mud
        ✗                          ✓ ← this one                 ✗
```

### A worked six-snapshot single-capture preset

Same capture in all six. Only the pedals and the NAM's own knobs move.

| | 1 Clean | 2 Edge | 3 Crunch | 4 Lead | 5 Quiet verse | 6 Ambient |
|---|---|---|---|---|---|---|
| Gate | on, soft | on, soft | on | on, hard | on, soft | on, soft |
| Drive | off | off | **on**, low gain | **on**, high gain | off | off |
| Pre-EQ boost | off | off | off | **on**, mids up | off | off |
| NAM `Input Gain` | −6 dB | 0 dB | +4 dB | +8 dB | −10 dB | −6 dB |
| NAM Tone Stack | Baxandall, flat | Baxandall, flat | JCM8000 | JCM8000, mids up | Baxandall, treble down | Baxandall |
| Delay | off | off | off | **on** | off | **on**, long |
| Reverb | low | low | low | medium | low | **high** |
| `Output Gain` | reference | matched | matched | matched | −3 dB | matched |

Snapshots 1–3 go on footswitches; 4–6 live in the attic (§7). Note that nothing in that table
required a second capture, a second NAM instance, or a split.

> **Test whether you actually need three captures per preset.** Build this preset first, play it
> for a week, and see whether you miss having different amps inside one bank. Plenty of people
> discover that one good capture plus pedals is their whole rig, at which point Design A vs
> Design B stops mattering and you have CPU to spend on §5.

---

## 5. Blended-amp sounds — the parallel-chain question

### 5.1 How PiPedal builds a parallel chain

The "+" button on any pedalboard slot offers **Insert pedal**, **Append pedal**, **Insert split**,
**Append split**. A split node is titled just **"Split"**. It has **exactly two branches** — the UI
calls them **Top** and **Bottom** — and splits can be **nested** inside each other.

```
                    ┌──────────────────────────────┐
                    │  Split      Type: L/R        │
                    │             Vol Top:    0 dB │
   [Gate] ─────────►│             Vol Bottom: 0 dB │────► [Delay] ─► [Reverb] ─► [Volume]
                    │                              │
                    │  ┌─ TOP ───────────────────┐ │
                    │  │ [Drive A] → [NAM #1]    │ │  ◄── amp A
                    │  └─────────────────────────┘ │
                    │  ┌─ BOTTOM ────────────────┐ │
                    │  │ [Drive B] → [NAM #2]    │ │  ◄── amp B
                    │  └─────────────────────────┘ │
                    └──────────────────────────────┘
```

Its seven controls, and the one thing everybody gets wrong about them:

| Control | Range / values | Active in which Type |
|---|---|---|
| **Type** | **A/B** · **Mix** · **L/R** | always |
| **Select** | A · B | **A/B only** |
| **Mix** | −1 (top only) … 0 (50/50) … +1 (bottom only) | **Mix only** |
| **Vol Top** / **Vol Bottom** | −60 dB ("-INF") … +12 dB, default 0 | **L/R only** |
| **Pan Top** / **Pan Bottom** | −1 … +1, default 0 (hard pan law) | **L/R only** |

> ⚠️ **`Type: Mix` gives you one crossfade knob and nothing else.** Reading the source, Mix mode
> calls `mixTo(mix)` and **ignores Vol Top / Vol Bottom / Pan Top / Pan Bottom entirely** — only
> `Type: L/R` calls `mixTo(panL, volL, panR, volR)`. So in Mix mode you cannot level-match the two
> branches at the split; you must do it inside each branch.

**The useful consequence, and it's not obvious: for a mono guitar, use `Type: L/R`, not `Mix`.**
With a *mono* signal arriving at the split, the L/R input functions copy `inputs[0]` into **both**
branches — both branches get the same guitar. So you get a true parallel blend *plus* the
independent **Vol Top / Vol Bottom** trims that Mix mode doesn't give you.

| Type | With a mono guitar into the split | Use it for |
|---|---|---|
| **L/R** | Both branches get the same signal; independent Vol + Pan per branch | **Blending.** This is the one |
| **Mix** | Both branches get the same signal; one crossfade knob | A single "amp A ↔ amp B" morph knob you want on an expression pedal |
| **A/B** | Both branches get the same signal; `Select` hard-picks one, with a short crossfade | Switching between two chains — **but see the CPU warning below** |

Two more facts that matter for rig design:

- **Split controls are snapshot-able** — so `Vol Top` / `Vol Bottom` / `Select` / `Mix` can differ
  per snapshot. Be on a current PiPedal: changing a split's **Type** from a snapshot was a real bug
  (fixed in 1.5.98). Don't change Type per snapshot anyway; keep it fixed and move the volumes.
- **Split controls are MIDI-bindable** individually, so the blend knob can go on an expression
  pedal later.

> ⚠️ **`Type: A/B` does not save CPU.** PiPedal flattens the pedalboard into one flat list of
> process actions and runs every one of them unconditionally each block; `Select` chooses which
> branch reaches the output, it does **not** skip the other branch's DSP. Two NAM instances in an
> A/B split cost the same as two NAM instances in a Mix split. (Derived from the source — confirm
> on the CPU meter before you rely on it.)

### 5.2 What blending two captures actually buys you — and when it's mud

| It buys you | When it turns to mud |
|---|---|
| A composite EQ curve you can't get from one amp — e.g. one amp's low mids under another's top end | Both captures occupy the same frequency range, so you get "both, quieter" plus phase artefacts |
| Thickness on leads: two slightly different distortions sound like a doubled track | Two high-gain captures blended — distortion is already dense; two of it is just fuzzy and undefined |
| Note definition: a tight, low-gain amp under a saturated one restores the pick attack | The clean-ish branch is too loud and the whole thing sounds thin and honky |
| A gain structure that's genuinely between two amps | You're using it to avoid deciding. Two half-good tones don't average into a good one |

**The pairings that work are the complementary ones** — different frequency emphasis, different
gain amounts:

| Pairing | Why it works |
|---|---|
| Clean/low-gain **+** high-gain | The clean branch carries the attack and the low end; the dirty branch carries the sustain and harmonics. **The most reliable blend in this rig** |
| Scooped-mid **+** mid-forward | The composite has both the size and the cut. Fixes §10.4 by construction |
| **Fender-ish + Vox-ish** | The documented classic (Premier Guitar's Super Reverb + AC30): the Vox brings strong mids and chime, the Fender brings scooped, tighter lows. "Attack and sustain, distortion and bell-clear chiming notes" |
| **Fender-ish + Marshall-ish** | Also documented as particularly effective. Fender = scooped mids and glassy top; Marshall = bass cut, treble boost, bite. Near-orthogonal in the midrange, which is the precondition for a blend rather than mud |
| Clean amp **+** high-gain amp for choruses only | Soldano crunch + Fender Hot Rod Deluxe is a documented touring setup: one amp for verses, both for choruses to thicken |
| Two similar high-gain captures | ✗ Don't. This is the classic mistake |

**The test for a good pairing:** are the two amps in *different places in the midrange*? Fender,
Vox and Marshall are the canonical trio precisely because they are. Two amps with the same mid
voicing give you "louder", not "bigger".

> **Worth knowing before you copy a hero rig:** a lot of famous multi-amp setups are **switching,
> not blending**. Eric Johnson's four-rig setup selects one per part; he isn't summing them. The
> best-documented genuine blend is Tool's *10,000 Days* — one guitar split to five heads, each with
> its own cab and mics, mixed down to three tracks. Note "each with its own cab": the thing your
> rig can't do (§1).

> **Your rig blunts the effect.** Both branches go through **the same EL34 power amp and the same
> Celestions** (§2.1 of the plan). Blending two amps into a mic'd FRFR rig works partly because
> the two cabs and two mic positions decorrelate the signals. Here they don't — you're blending
> two *preamps*, which are far more similar to each other than two full rigs. Expect a subtler
> result and more phase interaction, not less.

### 5.3 Phase and alignment — the gotcha that ruins blends

Summing two signals that are almost the same but slightly time-shifted is a comb filter: a fixed
pattern of notches that reads as "thin", "hollow", "phasey", or "the mids disappeared". You can't
EQ it out.

**The one formula worth knowing.** An N-sample offset puts its first notch at `f = SR / (2N)`, and
repeats up the spectrum. At 48 kHz:

| Offset | First notch | What it sounds like |
|---|---|---|
| 1 sample | 24 kHz | Inaudible |
| 2 samples | 12 kHz | Slight loss of air |
| 4 samples | 6 kHz | Top edge dulls — right at the top of a guitar speaker's range |
| **64 samples (one buffer)** | **375 Hz** | ⚠️ **Gutted. This is the `Threaded` mismatch case** |
| Polarity inverted | **0 Hz (DC)** | Thin, quiet, honky mids — the low end goes first |

Two things about your rig specifically. In your favour: the two branches sum **before** they reach
your Celestions, and a guitar speaker only passes roughly 70 Hz – 6 kHz, so it masks small offsets
(4 samples and under) by rolling off the region they damage. Against you: because you're blending
**cab-less preamps**, both branches carry real energy to 15–20 kHz and are highly correlated, which
is exactly the condition comb filtering needs. And nothing masks a 375 Hz notch.

| Cause | Effect | Fix |
|---|---|---|
| **`Threaded` on in one NAM and off in the other** | The threaded branch is **one whole audio buffer late** — 1.33 ms at 64 samples. That's a comb notch around 375 Hz. Devastating | ⚠️ **Set `Threaded` identically on both NAM instances.** Non-negotiable |
| A plugin with internal latency in one branch only (convolution/IR, lookahead limiter) | Same thing, different amount | Keep both branches structurally symmetric, or put latency-adding plugins *after* the merge |
| **A drive/EQ block in one branch only** | The classic cause. Fractal's own docs warn that a Drive block in front of only one of two parallel Amp blocks "may cause phase cancellation because of increased latency in one row" | Put shared pedals **before** the split. If a branch genuinely needs its own drive, expect to A/B it against bypassed and trust your ears |
| Genuine polarity inversion in one of the two captures | Sums to near-silence in the mids; sounds like the blend "does nothing" | Invert one branch and compare (see below) |
| Two different preamp models with different internal group delay | Mild colouration, usually musical | Nothing — this is the part that makes it sound like two amps |

> **Don't assume a quiet branch is a safe branch.** AES listening tests put comb-filter artefacts
> as still audible when the second copy is **up to ~20 dB below** the first — detected at 13–18 dB
> down on real instrument material. So a "subtle" −12 dB parallel blend is comfortably inside the
> audible range, and worth polarity-checking.

**The engineer's trick for finding the best alignment.** Deliberately put the two branches
*out* of polarity, level-match them, and adjust until you hear the **strongest cancellation** —
that's the point of maximum time alignment. Then flip the polarity back and you have the fullest
composite. It's far easier to hear a null appear than to hear a sum improve.

**How to check polarity with only bundled plugins.** Set the split to `Type: L/R`, `Pan Top` hard
left, `Pan Bottom` hard right — now branch A is the L channel and branch B is the R channel. Put
**TooB Mix** after the split with both pans centred, and toggle its **`Phase L`** between *Normal*
and *Inverted*. One of the two will sound obviously fuller; keep that one. Then remember your
output is **mono** into one FX return, so this sum is happening whether you audit it or not — see
[`pipedal-stereo.md`](./pipedal-stereo.md) if you later go stereo.

**Level matching the branches.** Set one branch's `Vol` (or its NAM `Output Gain`) as the
reference, mute the other with `-INF`, get the reference right, then bring the second branch up
from `-INF` until it *adds* without *taking over*. A blend that sounds "wrong" is a level problem
about three times out of four.

### 5.4 The CPU reality — and the one thing that might change it

A blend means **both NAM instances run constantly.** §13 Phase 5 of the plan puts this at
"Pi 5 only", and the pi-stomp community data point is that a **Pi 5** manages ~2 NAM instances.
Nothing here overrides that.

> ⚠️ **Correction to §6 of the plan: A2-Full and A2-Lite are not two downloads.** TONE3000 is
> explicit — *"An A2 download is a single NAM model that can be run as either A2-Full or
> A2-Lite."* A2 models are trained "slimmable", so the size is a **runtime decision made by the
> host**, not a file you choose. Which means "download A2 Lite" is not a thing you can do, and
> whether TooB NAM lets you *pick* Lite is an open question — its control list has no size
> selector (§11). Plan for the possibility that PiPedal simply runs what it runs.

For scale, TONE3000's published A2 figures: A2-Full is **30–40% more performant than A1-Standard**
("you can run three A2-Full models for the same CPU cost as two A1-Standard models"), A2-Lite runs
at **50% CPU on a 600 MHz Cortex-M7**, and in a blind MUSHRA test (105,842 ratings, 1,184
participants) **A2-Lite scored right alongside A1-Standard**. The plan's conclusion holds: the
Lite/Full gap is the least significant variable in your signal path.

But there is one lever the plan doesn't cover: **TooB NAM's `Threaded` control**, whose own
description is *"Run computation on a separate thread. This allows more instances of NAM to run
simultaneously, but adds one extra audio buffer of latency."* A Pi 4 has four cores and PiPedal's
audio thread is one of them, so pushing each NAM onto its own thread is exactly the case
`Threaded` exists for.

| | Cost | Verdict |
|---|---|---|
| 1 × NAM A2 Full | 1× | The Phase 1/2 baseline |
| 2 × NAM A2, both `Threaded` **on** | 2× spread across cores, **+1 buffer latency** | **Measure it.** This is the only Pi 4 blend worth testing |
| 2 × NAM A2, `Threaded` off | 2× on the one audio thread | Don't bother on a Pi 4 |
| 2 × NAM **A1** | Worse again — A2 is 30–40% cheaper | Use the TONE3000 button in PiPedal, which delivers A2 |
| Blend **+** Design A model swaps per snapshot | 2 instances always live | Feasible on a Pi 5 (plan §13) |
| Blend **+** three-instance Design B | 6 instances | Not happening on anything |

> **How to test it honestly, in 20 minutes, before you plan a rig around it.** Build one blend
> preset, both captures downloaded through PiPedal's TONE3000 button so they're **A2**, and
> `Threaded` **on** for both. Then read: CPU on the PiPedal
> meter, `get_throttled` = `0x0`, temp under 70 °C, and **xruns in `journalctl -u pipedald -f`
> over ten minutes of actual playing**. The xrun count is the number that decides it — CPU
> percentage under 70% with xruns is still a fail. If it fails, §6 is your answer and it costs
> nothing.

### 5.5 A concrete blend preset

The reliable pairing: a tight low-gain amp under a saturated one, for leads that keep their attack.

```
[Tuner] → [Gate] → ┌─ Split  Type: L/R ───────────────────────────┐
                   │ TOP    [NAM #1  Fender-ish, clean]           │
                   │        Input Gain −2 · Tone Stack Baxandall  │
                   │        Threaded ON                           │
                   │        Vol Top     −6 dB · Pan Top centre    │
                   │                                              │
                   │ BOTTOM [TooB ML Amp: TS9] → [NAM #2          │
                   │         Marshall-ish, high gain]             │
                   │        Input Gain +6 · Tone Stack JCM8000    │
                   │        Threaded ON                           │
                   │        Vol Bottom   0 dB · Pan Bottom centre │
                   └──────────────────────────────────────────────┘ → [Delay] → [Reverb] → [Vol]
```

Then three snapshots off that one graph, moving only the split volumes and the pedals:

| | 1 "Rhythm" | 2 "Blend lead" | 3 "Clean only" |
|---|---|---|---|
| `Vol Top` (clean amp) | 0 dB | −6 dB | 0 dB |
| `Vol Bottom` (dirty amp) | −60 (`-INF`) | 0 dB | −60 (`-INF`) |
| TS9 (bottom branch) | off | **on** | off |
| NAM #1 `Input Gain` | 0 dB | −2 dB | −4 dB |
| Delay | off | **on** | off |
| Reverb | low | medium | low |

Note snapshot 1 and 3 only use one branch — **but both NAM instances are still running and still
costing CPU** (§5.1). That's the trade: a blend preset costs 2× NAM in every one of its snapshots,
not just the blended one.

> ⚠️ **The TS9 sits in the bottom branch only, and that is the single most common cause of a
> phasey parallel blend** (§5.3). It's there because a boost into the clean amp would defeat the
> point. Two ways out if it sounds hollow rather than thick: move the drive **before** the split
> and accept that it hits both amps, or leave it and use the polarity check. Test it bypassed vs
> engaged with `Vol Top` and `Vol Bottom` equal — if bypassing the TS9 makes the blend suddenly
> *fuller*, it's alignment, not the pedal.

---

## 6. Blending without two NAM instances

Four approximations, ranked. All of them cost **one** NAM instance, so all of them fit on a Pi 4.

| # | Approach | What it gets you | What it doesn't |
|---|---|---|---|
| 1 | **NAM + TooB ML Amplifier in the other branch** | A genuinely different second amp — 33 built-in models including Princeton, Mesa Mk2b, Soldano, Dumble, Blues Jr — at a fraction of NAM's cost. **The best value here by a distance** | ML models are smaller/simpler than NAM captures, so the second amp is the less convincing one. Put the NAM on whichever tone is doing the heavy lifting |
| 2 | **Parallel clean blend** — one branch is the NAM, the other is dry/lightly-EQ'd guitar | Restores pick attack and low-end tightness under a saturated capture. This is the studio "parallel clean" trick, and it's *the* fix for a high-gain tone with no definition | It is not a second amp. Too much and it sounds like an unplugged guitar leaking in — thin, honky, spiky. Start around −12 dB and creep up |
| 3 | **NAM + a guitarix / GxPlugins amp** in the other branch | A second *modelled* amp, cheap, and GxPlugins is PiPedal's top-rated third-party collection | You're now maintaining two very different kinds of amp model. Fine, just more to learn |
| 4 | **Split *after* one NAM into two differently-EQ'd paths** | Genuinely useful as a "two mic positions on one cab" effect — a dark, bass-heavy path under a bright, present one | ⚠️ **This is not two amps.** One distortion, two EQs, summed = a comb filter you designed on purpose. Keep the EQ differences *mild* and mostly non-overlapping, or it just sounds phasey |

```
   Option 1 — the one to build first
                    ┌─ Split  Type: L/R ────────────────────┐
   [Gate] ─────────►│ TOP     [NAM]  ← your good capture    │──► [Delay] → [Reverb]
                    │ BOTTOM  [TooB ML Amplifier]           │
                    │          model: MesaBoogieMk2b Crunch │
                    └───────────────────────────────────────┘
                                 ~1× NAM CPU, not 2×

   Option 2 — parallel clean blend
                    ┌─ Split  Type: L/R ────────────────────┐
   [Gate] ─────────►│ TOP     [Drive] → [NAM, high gain]    │──► [Delay] → [Reverb]
                    │         Vol Top     0 dB              │
                    │ BOTTOM  [TooB Input Stage: Lo Cut up] │
                    │         Vol Bottom  −12 dB            │
                    └───────────────────────────────────────┘
                        the dry branch is the attack, not a tone
```

> **Same phase rules apply (§5.3), and option 2 is the most exposed of the four.** The dry branch
> has essentially zero latency and the NAM branch may not, so if it sounds hollow rather than
> tight, that's alignment, not level. `Threaded` **off** on the single NAM is the safer setting
> here. Don't dismiss it as "too quiet to matter" — comb artefacts stay audible with the second
> copy 20 dB down, so a −12 dB blend is well inside the range where polarity matters. Invert one
> branch and compare before you give up on it.
>
> This is the same problem, and the same fix, as the classic **bass DI + mic'd amp** blend: the DI
> arrives at the speed of electricity and the mic at the speed of sound, so engineers polarity-check
> it as a matter of routine and often high-pass one branch so only one path owns the low end. Rolling
> `Lo Cut` up on the dry branch does exactly that job here.

**Honest summary:** option 1 gets you ~80% of what a two-NAM blend gets you in this rig, because
your fixed EL34s and Celestions already flatten most of the difference between two preamp captures
(§1). Option 2 solves a specific, real problem and is worth building regardless of CPU. Option 4 is
an effect, not a rig feature.

---

## 7. Presets vs snapshots — how to allocate a new sound

The rule, restated from §5 of the plan: a **preset** is the plugin graph, a **snapshot** is every
knob, switch, bypass and capture selection on that graph. Preset change = graph rebuild = audible
gap. Snapshot change = seamless, reverb tails survive. **Max 6 snapshots per preset.**

### The decision

```
        I want a new sound. Where does it go?
                        │
        ┌───────────────┴────────────────┐
   Does it need a plugin, or a           No — only different knob
   wiring change, the current            positions, bypasses, or a
   preset doesn't have?                  different capture
        │                                        │
       YES                                       ▼
        │                                  ► SNAPSHOT
        ├── Can I add that plugin to the      (free, seamless,
        │   preset and leave it bypassed       counts against the 6)
        │   in the other snapshots?
        │        │
        │       YES ──► add it, re-save every existing snapshot ──► SNAPSHOT
        │        │
        │        NO (chain order differs, or it's a split/blend,
        │            or CPU won't take it always-loaded)
        ▼        ▼
   ► NEW PRESET  (gap on change — fine between songs, not mid-song)
```

**Build the superset graph.** Every plugin you might ever want in a preset should be *in* that
preset from the start, bypassed where unused — that is what keeps future sounds in the cheap,
seamless, snapshot column. The cost is CPU for bypassed plugins, which for gates, EQs and drives is
near zero. The exception is a second NAM instance, which you cannot afford to leave loaded (§5).

### Things that force a new preset

| Change | Why |
|---|---|
| Adding a plugin that isn't already in the graph | Snapshots can't add plugins |
| Re-ordering the chain (drive after the amp instead of before) | Snapshots can't re-order |
| Single amp → blended amps | The split is structure, not a knob |
| A second NAM instance | Can't be left loaded on a Pi 4 (§5) |
| More than 6 variations of one rig | Hard limit |

### 3 snapshots or 6?

Six fit in a preset. Your Phase 3 footswitch layout is `[snap 1] [snap 2] [snap 3] [bank−]
[bank+] [tune/mute]` (§10 of the plan) — **three are reachable with one press.**

Good news for that layout: PiPedal's System MIDI Bindings list does include direct
**Snapshot 1 … Snapshot 6** actions, not just Next/Previous Snapshot — so the plan's §15 open
question resolves in favour of the direct-select layout (§11). Six *bindable* snapshots still
means only three *footswitches*, which is the real constraint.

| | 3 snapshots per preset | 6 snapshots per preset |
|---|---|---|
| Reaching snapshot 4–6 | n/a | Needs a bank change (gap) or next/prev walking |
| Presets needed for 9 sounds | 3 | 2 (but 3 of the 9 are awkward to reach) |
| Bank changes during a set | More | Fewer |
| Mental model | "This bank *is* this amp" | "This bank is two amps mashed together" |
| Verdict | **Default.** Do this | Only for a 4th/5th sound in a preset you rarely need live |

**Use 3 as the design unit and treat snapshots 4–6 as an attic** — the quiet-verse variant, the
alternate-tuning level, the one-song-only sound. Reachable when you have a hand free, not under
your boot mid-song. If a fourth sound needs to be footswitchable, it belongs in a new preset.

> **Keep the graph identical across presets.** Phase 2 §8 says to duplicate preset 1 rather than
> build from scratch, and this is the tone-design reason as well as the MIDI reason: identical
> graphs mean snapshot 2 of every preset is "the crunch one", so your feet learn one layout.
> A blend preset breaks that rule by design — which is a reason to have at most one.

---

## 8. The worksheet

Fill these in before you touch PiPedal. Row 1 of each table is an example showing the level of
detail that makes the table useful — replace it or keep it, your call.

### 8.1 Sounds I actually need

Start from **songs and situations**, not from amps. If you can't name where a sound gets used,
it doesn't earn a footswitch.

| Sound name | What it's for | Gain | Amp family | Effects | Single / blend |
|---|---|---|---|---|---|
| *Big Clean* | *Verses, arpeggios, clean-with-a-band* | *clean, edge at hard picking* | *Fender-ish* | *light reverb, no delay* | *single* |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |

Gain column, use these words so the shortlist in §8.3 is searchable: `clean` · `edge of breakup` ·
`crunch` · `high gain` · `lead / saturated`.

**Sanity checks on the finished list:**

- More than 9 rows → you're designing a studio, not a rig. Cut to the ones you'd miss.
- Two rows that differ only in reverb amount → that's one sound, or one snapshot pair at most.
- No `edge of breakup` row → add one. It's the most useful single tone in a valve rig, and the
  capture that does it is the one that takes a boost best (§4).
- Everything is `high gain` → you don't need three presets, you need one and a boost.

### 8.2 Preset / snapshot allocation

Nine slots. Map §8.1's rows into them. Snapshot 1–3 are the footswitchable ones; 4–6 are the attic
(§7).

| | Snapshot 1 | Snapshot 2 | Snapshot 3 | 4–6 (attic) |
|---|---|---|---|---|
| **Preset 1** — *name / amp family* | *Big Clean* | *Crunch* | *Lead* | *— * |
| **Preset 2** — | | | | |
| **Preset 3** — | | | | |

Then confirm the graph you need is the same in all three (§7). If preset 3 is a blend preset, note
it here and expect it to feel different under your feet:

| | Answer |
|---|---|
| Is the plugin graph identical in all three presets? | |
| If not, which preset differs and why? | |
| Which preset is "first song of the set"? | |
| Which single snapshot could you play a whole gig on if something broke? | |

### 8.3 Capture shortlist to download

**Three candidates per slot, maximum.** Fill the *want* column first, then go shopping — searching
TONE3000 with a specific requirement is a different activity from browsing it.

**How to actually find what you need on TONE3000.** Its taxonomy has no "no cab" tag, so the
filter you want is the **Gear** type, not a tag:

| You want | Use |
|---|---|
| **No cab** | Gear = **"Amp Head"** (`gears=amp`) — the site's own guide calls it *"Amplifier only (add a Cabinet IR after it to sound complete)"* |
| **Not** this | Gear = **"Amp + Cab"** (`gears=amp-cab`) — a complete rig, which is exactly what you're avoiding |
| **Preamp-only** | The tag `preamp-only` — a real curated tag: `tone3000.com/search?tags=preamp-only`. The tag `amp only` also exists in the wild |
| **Calibrated captures** | `calibrated=true` — locks the catalogue to tones with at least one calibrated model, which makes §10.1 straightforward |
| Architecture | The **Technical** filter: "A2 – Default", "A1 – Legacy", "Custom" |

Gear = Amp Head plus the `preamp-only` tag is your shortlist. There is **no** `no-cab` or `cab-off`
tag — those phrases appear only in free-text titles and descriptions, so searching for them will
miss most of the catalogue.

> **Download from inside PiPedal, not from the website.** The **DOWNLOAD MODELS FROM TONE3000**
> button in TooB NAM's model picker delivers **NAM A2**; models you fetch from the TONE3000 website
> by hand may still be **A1**, which costs 30–40% more CPU for no benefit. Same models, worse deal.
> (The TONE3000 API's default architecture filter also *excludes* A2 — another reason to let
> PiPedal do the fetching.)

| Slot | What I want | Candidate 1 | Candidate 2 | Candidate 3 | Picked | Calibrated |
|---|---|---|---|---|---|---|
| *P1 / S1* | *Blackface clean, preamp only, no cab, headroom to spare* | | | | | ☐ |
| P1 / S2 | | | | | | ☐ |
| P1 / S3 | | | | | | ☐ |
| P2 / S1 | | | | | | ☐ |
| P2 / S2 | | | | | | ☐ |
| P2 / S3 | | | | | | ☐ |
| P3 / S1 | | | | | | ☐ |
| P3 / S2 | | | | | | ☐ |
| P3 / S3 | | | | | | ☐ |

Every row must be **preamp-only** and **no cab** (§2.1 of the plan). The *Calibrated* box is not
optional — see §10.1.

### 8.4 Level-match pass

One reference snapshot, everything matched to it by ear at playing volume. Record the numbers so a
rebuild doesn't cost you the pass again.

| Snapshot | Output gain (dB) | Notes |
|---|---|---|
| *P1 / S2 — reference* | *0.0* | *amp set here; do not move the amp after this* |
| P1 / S1 | | |
| P1 / S3 | | |
| P2 / S1 | | |
| P2 / S2 | | |
| P2 / S3 | | |
| P3 / S1 | | |
| P3 / S2 | | |
| P3 / S3 | | |

---

## 9. A worked example rig

**One opinionated layout to react to, not a prescription.** Three presets, three footswitchable
snapshots each, identical graph in presets 1 and 2, and preset 3 flagged as the experiment.

Everything below assumes preamp-only, no-cab captures and Design A.

### The graph (presets 1 and 2 — build once, duplicate)

```
[TooB Tuner] → [TooB Noise Gate] → [TooB Input Stage] → [TooB ML Amp: TS9] →
      → [TooB NAM] → [TooB Graphic Eq] → [TooB Delay] → [TooB Freeverb] → [TooB Volume]
```

### Preset 1 — "Clean & Crunch" (Fender-ish family)

| | 1 "Big Clean" | 2 "Edge" | 3 "Crunch" |
|---|---|---|---|
| Capture | blackface clean, preamp only | same | tweed / low-watt breakup |
| NAM `Input Gain` | −4 dB | +2 dB | +5 dB |
| NAM Tone Stack | Baxandall — B 6 / M 5 / T 5 | Baxandall — B 5 / M 6 / T 5 | Bassman — B 4 / M 7 / T 6 |
| TS9 | off | off | **on** — Drive low, Level high |
| Graphic Eq | flat | flat | slight mid bump |
| Gate | soft | soft | medium |
| Delay | off | off | off |
| Freeverb | Dry/Wet low | low | low |

### Preset 2 — "Rock" (Marshall-ish family)

| | 1 "Rhythm" | 2 "Lead" | 3 "Cleanish" |
|---|---|---|---|
| Capture | plexi-ish crunch, preamp only | same | same |
| NAM `Input Gain` | +2 dB | +8 dB | −8 dB |
| NAM Tone Stack | JCM8000 — B 4 / M 6 / T 6 | JCM8000 — B 4 / M 7 / T 6 | JCM8000 — B 5 / M 5 / T 5 |
| TS9 | off | **on** — Drive 9 o'clock, Level 2 o'clock | off |
| Graphic Eq | flat | 800 Hz + 2 dB | flat |
| Gate | medium | **hard** | soft |
| Delay | off | **on** — 380 ms, Feedback low, Level low | off |
| Freeverb | low | medium | low |

Preset 2 deliberately runs **one capture across all three snapshots** — the §4 approach. If Phase 1
says the capture swap is clean, you can put a third capture in snapshot 3; if it glitches, this
preset already works unchanged.

### Preset 3 — "Blend" ⚠️ Pi-5-or-measure-first

```
[Tuner] → [Gate] → ┌─ Split  Type: L/R ──────────────────────┐
                   │ TOP    [NAM #1  clean capture, A2 Lite] │
                   │        Threaded ON                      │
                   │ BOTTOM [TooB ML Amplifier]              │
                   │        model: Soldano highGain          │
                   └─────────────────────────────────────────┘ → [Delay] → [Reverb] → [Vol]
```

Note this is written as **§6 option 1** — one NAM plus TooB ML Amplifier — not two NAM instances.
That version runs on the Pi 4 you have today. Swap the bottom branch to a second `[TooB NAM]`
only after §5.4's ten-minute xrun test passes.

| | 1 "Composite rhythm" | 2 "Composite lead" | 3 "Clean only" |
|---|---|---|---|
| `Vol Top` (NAM, clean) | 0 dB | −5 dB | 0 dB |
| `Vol Bottom` (ML, dirty) | −10 dB | 0 dB | −60 (`-INF`) |
| NAM `Input Gain` | 0 dB | −2 dB | −4 dB |
| Delay | off | **on** | off |
| Freeverb | low | medium | low |

### Why this shape

| Decision | Reason |
|---|---|
| Preset 1 = clean family, preset 2 = rock family | A bank change is a change of *amp*, not a change of song (Phase 2 §4) |
| Presets 1 and 2 share one graph | Snapshot 2 is "the pushed one" in both; your feet learn one layout (§7) |
| Only one blend preset, and it's last | Blends break the shared-graph rule and cost the most CPU. One is a feature; three is a maintenance problem |
| Snapshot 3 of preset 2 is *quieter*, not dirtier | You always need somewhere to go down to. Most rigs have three loud sounds and no quiet one |
| No modulation anywhere | Add it when a song needs it, in the preset that song lives in. Don't put a chorus in every preset "just in case" |

---

## 10. Gotchas specific to tone building

These are on top of the build gotchas in §14 of the plan.

1. **Get the NAM input level right per capture — but calibration is not what Phase 2 implies.**
   PiPedal's own [NAM Calibration doc](https://rerdavies.github.io/pipedal/NamCalibration.html)
   opens with *"This feature isn't what you think it is"*: true calibration needs the model author
   to have embedded the training level in the `.nam` file **and** you to measure your guitar's
   output in dBu with a voltmeter. If the loaded model has no calibration metadata, the
   `Input Calibration` control is greyed out — that's your tell. What to actually do:

   | Case | Do this |
   |---|---|
   | Model **has** calibration metadata | `Input Calibration` = Calibrated, `Value` = **−6 dBu** for humbuckers / **−11 dBu** for single coils, `Input Gain` = 0 dB |
   | Model has **no** metadata | Trim the interface so peaks approach 0 dBFS, then start `Input Gain` at **−12 dB** and adjust by ear |
   | Either case | `Output Calibration` = **Normalized**. Real models' output metadata is often flatly wrong |

   The symptom of getting it wrong is fizz and mud that reads as "bad capture", so you delete a
   good capture and download another one. Only the **first** NAM in a chain is worth calibrating.
   Do it with the guitar in your hands and your normal picking attack.
2. **Level-match at playing volume, not bedroom volume.** Fletcher-Munson means a lead tone
   matched at whisper level will be too bright and too quiet when the EL34s are working. Match the
   nine snapshots in one pass, at the volume you'll actually use, with the amp and interface output
   knob untouched for the whole pass.
3. **Preamp-only, no cab — filter on Gear type, don't trust the name.** A capture called "JCM800
   preamp" may still be an Amp + Cab capture someone named badly, and "no cab" is not a tag you
   can filter on (§8.3). If it sounds flubby and dark, you're stacking two power amps and two cabs
   (§2.1). Bass-heavy and dull = suspect the capture *type* before you suspect your settings.
4. ⚠️ **The mid-range trap.** A scooped-mids high-gain tone is the most satisfying sound to make
   alone and the first thing to vanish under a bass and drums. If a sound is for band use, judge
   it with something else playing — backing track, drum loop, anything. Mids are what you hear from
   the audience; the scoop is what you hear from behind the amp.
5. **Judging tone at low volume lies to you twice** — once on EQ (point 2) and once on gain. Amps
   need less gain than you think at volume, and a capture that seemed lifeless quiet often opens up
   loud. Don't finalise gain settings on the couch.
6. **Decision fatigue is the real failure mode.** Downloading 40 captures is fun for an hour and
   then you have 40 files, no shortlist, and no rig. Cap it: download **at most 3 candidates per
   slot**, A/B them once, pick one, delete the losers. §8's shortlist table exists to enforce this.
7. **A/B two captures back to back, never in isolation.** In isolation everything sounds fine after
   thirty seconds — your ears normalise. Two snapshots and a footswitch is a much better
   audition rig than loading one capture at a time.
8. **Don't chase the recorded tone.** You are playing into a real 2×12 in a room, and the reference
   in your head is a mic'd cab in a mix. They don't match and can't. Judge the rig on whether it
   feels good under your hands and cuts through, not on whether it sounds like the record.
9. **Write down what you changed.** You will make a snapshot better, then worse, then not be able
   to get back. Snapshots are cheap; save an "old" one into a spare slot before you start editing
   a good sound.
10. **One variable at a time.** The single biggest time sink in tone building is changing the
    capture, the drive and the EQ together, hearing an improvement, and not knowing which of the
    three did it.

---

## 11. Open questions

In the style of §15 of the plan. These are the ones this doc could not settle.

| Question | Status |
|---|---|
| Will **2 × NAM A2 Lite with `Threaded` on** run clean on a Pi 4? | **Unresolved, and it's the whole blend question.** Not covered by the plan's §13 Phase 5 (which assumes `Threaded` off). Test per §5.4 — CPU, temp, and **xruns over 10 minutes** |
| Does `Threaded` on **one** NAM instance change its latency relative to the rest of the chain? | **Unresolved.** It adds one buffer *somewhere*; in a single-chain preset that's just latency, but §5.3 depends on it being a whole buffer and identical on both branches. Verify by ear on a blend before trusting it |
| Does `Type: A/B` really process both branches? | **Very likely yes** — PiPedal runs a flat list of process actions unconditionally and `Select` only picks the output. **Source-derived, not measured.** Confirm on the CPU meter: A/B split with two NAMs vs one NAM |
| Is a snapshot NAM capture swap audibly silent? | **Unresolved — this is Phase 1** (plan §12). Everything in §4 works either way; §9 preset 2 is written so it doesn't matter |
| Does a direct "go to snapshot N" MIDI binding exist? | **Resolved: yes.** The System MIDI Bindings action list includes **Snapshot 1–6** as well as Next/Previous Snapshot, Next/Previous Preset and Next/Previous Bank. Verified from source, not from a doc page — **confirm in Settings → System MIDI Bindings** and update plan §15 and Phase 2 §9 |
| Does TooB Tuner have its own mute? | **Resolved: yes** — it has a `Mute` control, which simplifies the plan's §13.G two-CC footswitch trick to one CC |
| Can you choose **A2-Full vs A2-Lite** in TooB NAM at all? | **Unresolved, and it undercuts §6 of the plan and Phase 2 §4.** An A2 download is *one* slimmable model run at either size by the host; TooB NAM's control list has no size selector. So "drop to A2 Lite if CPU is tight" may not be an action you can take. Check the plugin UI; if there's no control, the CPU knob you actually have is `Threaded` and the plugin count |
| How much CPU does **TooB ML Amplifier** use relative to TooB NAM? | **Unresolved.** "Smaller/cheaper models" is documented; no number. §6 option 1 is built on the assumption it's much cheaper — measure it before designing around it |
| Can splits nest arbitrarily deep? | **Probably** — all editing operations recurse with no depth check found, but undocumented and untested. Don't build a rig that needs it |
| Is per-capture NAM calibration actually worth doing? | **Partly resolved, and it contradicts Phase 2 §4.** PiPedal's own NAM Calibration doc says the feature "isn't what you think it is", needs a voltmeter measurement of your guitar's output in dBu, and is impractical for most users. See §10.1 |
| How long is the preset-change gap, in ms? | **Unresolved and undocumented.** Matters only for whether you could get away with a preset change between sections of a song. Assume you can't |
| Does the sum of two cab-less preamp branches comb badly enough to matter *through a real 2×12*? | **Unresolved, and only your ears can settle it.** The physics cuts both ways (§5.3): your Celestions roll off above ~6 kHz and mask small offsets, but they can't mask the 375 Hz notch a one-buffer mismatch creates. Build §6 option 2 first — it's the cheapest way to find out how sensitive your rig is |
| Is there any documentation page for splits? | **No.** Everything in §5.1 comes from PiPedal's source, its release notes and GitHub discussion #259. Expect the UI to differ in wording from this doc |

---

## Sources

Beyond §17 of the plan:

- [Using LV2 Plugins](https://rerdavies.github.io/pipedal/UsingLv2Plugins.html) ·
  [Which LV2 Plugins are supported](https://rerdavies.github.io/pipedal/WhichLv2PluginsAreSupported.html) ·
  [MOD UI Support](https://rerdavies.github.io/pipedal/ModUiSupport.html)
- [GxPlugins](https://rerdavies.github.io/pipedal/GxPlugins.html) ·
  [What PiPedal Is](https://rerdavies.github.io/pipedal/WhatPiPedalIs.html) ·
  [Release Notes](https://rerdavies.github.io/pipedal/ReleaseNotes)
- [ToobAmp plugin source](https://github.com/rerdavies/ToobAmp) — the `.ttl` files are the only
  authoritative control lists; the README undercounts the suite
- [NAM A2: the complete guide](https://www.tone3000.com/guides/nam-a2-the-complete-guide) —
  slimmable single-file A2, the Full/Lite runtime split, CPU and ESR figures ·
  [Get started with TONE3000](https://www.tone3000.com/guides/get-started-with-tone3000) —
  "Amp Head" vs "Amp + Cab" ·
  [TONE3000 API reference](https://www.tone3000.com/api) — the `gears` / `sizes` / `calibrated`
  filter names
- [Comb filter](https://en.wikipedia.org/wiki/Comb_filter) (the `SR/(2N)` null formula) ·
  [SOS: what exactly is comb filtering](https://www.soundonsound.com/sound-advice/q-what-exactly-comb-filtering) ·
  [SOS: using guitar pedals in parallel](https://www.soundonsound.com/techniques/using-guitar-pedals-parallel) ·
  [Premier Guitar: how to use two guitar amps at once](https://www.premierguitar.com/diy/silver-and-black/how-to-use-two-guitar-amps-at-once)
- Split behaviour: [`src/SplitEffect.hpp`](https://github.com/rerdavies/pipedal/blob/main/src/SplitEffect.hpp) ·
  [`src/SplitEffect.cpp`](https://github.com/rerdavies/pipedal/blob/main/src/SplitEffect.cpp) ·
  [`vite/src/pipedal/SplitUiControls.tsx`](https://github.com/rerdavies/pipedal/blob/main/vite/src/pipedal/SplitUiControls.tsx) ·
  [Discussion #259](https://github.com/rerdavies/pipedal/discussions/259)
