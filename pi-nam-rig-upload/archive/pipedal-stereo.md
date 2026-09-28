# Stereo — bolt-on, or design-in?

Whether you can add a second output side later, or have to plan for it now.
Full detail: [`pipedal-nam-rig-plan.md`](../pipedal-nam-rig-plan.md) ·
Tone and preset design: [`pipedal-tone-plan.md`](./pipedal-tone-plan.md) ·
Current step: [`pipedal-phase2.md`](../pipedal-phase2.md)

---

## 1. The answer

**Stereo is a bolt-on.** Nothing you are about to build in Phase 2 forecloses it, and nothing you
can buy now makes it easier. Build Phase 2 mono, exactly as written.

| Question | Answer |
|---|---|
| Does PiPedal do stereo at all? | **Yes.** Stereo is its maximum — the host accepts "mono or stereo" plugins only |
| Does the UMC204HD foreclose it? | **No — it's the best thing you own for it.** 4 playback channels; MAIN OUT L *and* R are already live and already carrying your mono signal, right now (§5.1) |
| Does the Pisound foreclose it? | **No**, but it's *worse* for stereo — one TRS jack, so you need a breakout cable (§5) |
| Do the 3 presets × 3 snapshots need rebuilding? | **No.** Re-save the snapshots, keep the captures, keep the levels. See §8 |
| Do the 9 captures need re-choosing or re-calibrating? | **No** — unless the second side is an FRFR, which changes what a capture has to contain (§4) |
| Is anything genuinely a from-the-start decision? | **One thing, and it's free:** chain order. §8.1 |
| Should you build stereo now? | **No.** §9 |

The reason it's a bolt-on is one sentence from PiPedal's own snapshot documentation:

> "You can actually re-order plugins within a preset, or remove plugins without affecting the
> control settings in a snapshot."

So the expensive part of Phase 2 — nine chosen captures, their input/output gain trims, nine
level-matched snapshots — survives a restructure. The only thing that costs you is *adding* a
plugin, and the cost is walking the snapshots and re-saving them.

**The whole question is a hardware and money question, not a software one.** You own one amp with
one mono FX return. Stereo starts at the price of a second thing to plug into, and the honest
cheapest useful version is headphones (§2, option 1).

---

## 2. What stereo actually plugs into

You have one mono destination. Every option below is about buying a second one. Prices AUD.

```
                        ┌────────────────────── today ──────────────────────┐
   Guitar ──► Pi ──► UMC204HD ── MAIN OUT L ──► Blackstar FX RETURN ──► 2×12
                                 MAIN OUT R ──► (nothing — carrying the same signal)
                        └───────────────────────────────────────────────────┘

   OPTION 1  headphones only        OUT L/R ──► PHONES jack on the interface
   OPTION 2  one powered FRFR       OUT L ──► Blackstar FX RETURN
                                    OUT R ──► FRFR      ← needs a DIFFERENT capture (§4)
   OPTION 3  second valve amp       OUT L ──► Blackstar FX RETURN
                                    OUT R ──► amp 2 FX RETURN
   OPTION 4  small solid-state      OUT R ──► its power-amp / aux / FX return input
   OPTION 5  stereo to FOH only     OUT L/R ──► 2 × DI ──► desk (stereo in the PA / IEMs)
                                    stage stays mono — fed from a DI thru, or from
                                    the Aux route on outs 3/4 (RCA pair B — §3.5, §5.1)
```

| # | Second side | AUD | What it sounds like | What breaks |
|---|---|---|---|---|
| **1** | **Headphones into the interface's PHONES jack** | **$0** if you own any | Genuine, obvious stereo. The only place stereo is unambiguously worth it | Nothing. Doesn't touch the stage rig. **Start here** |
| **2** | Powered FRFR / powered monitor | see §2.1 | Two *different* voices, not one wide one — the FRFR has no Celestions | Needs a **full-amp + cab** capture on that side, or a Power Stage + Cab IR block (§4). Second box to carry and power |
| **3** | Second valve amp | $600–2500+ used | The real thing, and the reason people do this | Weight, mains, hum (§6), level matching two power amps, mono-summing at FOH |
| **4** | Small solid-state combo with a line/FX-return input | see §2.1 | Lopsided. The 60W valve side dominates and the small amp reads as an artefact | Same as 3 plus an obvious level and voice mismatch |
| **5** | Stereo only into the desk / IEMs, stage stays mono | cost of 2 DI channels | Correct answer for a working band. Stereo where it's heard, mono where it isn't | Engineer has to want two channels. Many won't give you one |

> **The Blackstar already has a speaker-emulated output**, which the plan's §2.1 doesn't mention.
> It's a mono, post-power-amp, cab-emulated line out — useful for a silent-stage or FOH feed, but
> it is *downstream* of your rig, so it can never carry a stereo signal from the Pi. For Option 5
> the two sides have to come off the interface, not off the amp.

> **Options 2, 3 and 4 all put a second mains-powered box on the floor connected to the first by
> an unbalanced signal path.** That is the textbook ground loop. Read §6 before spending anything.

### 2.1 Prices — second-side hardware

Checked September 2026. **Verify before buying** — the two figures marked ⚠ come from a research
pass I could not independently confirm, and guitar retail pricing in Australia moves constantly.

| What | AUD | Where | Notes |
|---|---|---|---|
| **Headphones you already own** | **$0** | — | Into the interface's PHONES jack. **Start here** |
| Powered FRFR — HeadRush FRFR-108 MKII | **$509** | Joondalup Music (Perth) — **sold out** at time of writing | The obvious Perth option, and the closest one to you |
| Same unit, interstate | ~$429 ⚠ | Belfield Music (Sydney), reported | Worth a price-match ask at Joondalup or Derringers, both advertise matching |
| Studio monitor as the second side — JBL 305P MkII (single) | ~$199 ⚠ | clearance, reported | Cheapest way to hear the idea on a real speaker. Not gig-loud |
| Second valve amp, used | $600–2500+ | Gumtree / Reverb / Facebook | The real thing. Also the heaviest and the loudest way to find out you don't need stereo |
| **Ground-loop isolator — Behringer HD400** | **~$39** | Musiclab and most AU retailers | 2-channel 1:1 transformer. **Buy this *before* the second box, not after you hear hum** (§6) |
| Passive DI, per channel (Option 5) | $60–120 | Altronics, Jaycar, music retail | Or borrow the desk's. Two channels needed for stereo to FOH |

> **The order that matters:** headphones ($0) → decide if you care → one powered speaker → and only
> then a second amp. Each step tells you whether the next one is worth it, and step one is free.

> ⚠️ **The HD400 (or any 1:1 isolation transformer) is not optional** once a second mains-powered
> box is involved. The alternative people reach for — lifting the mains earth pin — is a genuine
> electrocution risk on a valve amp. Don't. Isolate the *signal*, never the earth.

---

## 3. Does PiPedal do stereo? Verified

Yes, and the docs are thin on it, so this section is checked against the source rather than the
manual. Everything here is from `rerdavies/pipedal` and `rerdavies/ToobAmp` on `main`/`master`.

### 3.1 The five facts that matter

| # | Fact | Where it's proven |
|---|---|---|
| 1 | PiPedal is a **mono-or-stereo** host. Nothing wider exists | *"Must have mono or stereo audio inputs and outputs"* — `WhichLv2PluginsAreSupported.md` |
| 2 | **Your mono chain is already being copied to both device outputs** | `Lv2Pedalboard::Prepare()` — if the device has 2 outputs and the chain ends mono, it pushes `outputs[0]` twice |
| 3 | **A mono signal auto-widens into a stereo plugin.** No adapter, no split needed | `Lv2Pedalboard::PrepareItems()` — 1 input buffer into a plugin with ≥2 audio inputs feeds `inputBuffers[0]` to *both* |
| 4 | ⚠️ **A mono plugin placed after a stereo one silently throws the right channel away** | Same function — 2 input buffers into a 1-input plugin connects `inputBuffers[0]` only. Not summed. Discarded |
| 5 | **An L/R Split always outputs stereo**, whatever is inside it | `forceStereo = (splitType == 2)` in `Lv2Pedalboard.cpp`; `numberOfOutputPorts = 2` in `SplitEffect::SetChainBuffers()` |

Fact 4 is the entire "design-in" question, and it is free to get right. See §8.1.

Fact 2 means you can test part of this tonight: plug a cable into **MAIN OUT R** instead of L and
you should hear exactly what you hear now.

### 3.2 The three split types

PiPedal's Split node has three modes (`SplitEffect.hpp`: `Ab = 0, Mix = 1, Lr = 2`). Only one of
them can put audio on different output channels:

| Split type | What it does | Can it make L/R? |
|---|---|---|
| **A/B** | One `select` control, hard-switches between the two branches | **No.** Sets left and right blend identically |
| **Mix** | One `mix` control, crossfades the two branches | **No.** Same — one coefficient drives both channels |
| **L/R** | Four controls: **Pan L, Vol L** (top branch) and **Pan R, Vol R** (bottom branch) | **Yes.** The only one with pan |

The naming is confusing and worth knowing before you open the dialog: on an **L/R** split,
*"Pan L / Vol L"* means **the top branch**, and *"Pan R / Vol R"* means **the bottom branch** —
they are not the left and right output channels. Pan range is −1 to +1, default 0. Vol bottoms out
at −60 dB, and at the bottom of its range the code sets that branch's gain to zero — a real mute,
not a fade.

**Fed a mono input, both branches get the same mono guitar** (`lrTopMonoMono` and
`lrBottomMonoMono` both copy `inputs[0]`). Fed a stereo input, top gets L and bottom gets R. So
with your mono guitar an L/R split is a dry/wet or dual-amp splitter, which is exactly what you'd
want it for.

And the reason this matters for the bolt-on question: **an L/R split with both pans at 0 is
mono.** Pan 0 gives `left = 1.0, right = 1.0` — both branches go to both outputs at full level, so
L and R come out identical. Pan the branches to −1 and +1 and it's stereo. Those four values are
ordinary control values, which means **they are stored in snapshots** — one preset can be mono in
one snapshot and stereo in the next, no rebuild.

### 3.3 Which TooB plugins are actually stereo

Counted from the LV2 manifests in `ToobAmp/src/ToobAmp.lv2/ttl.in/`. This table is the thing to
keep, because Fact 4 above turns a wrong order here into a silently half-dead rig.

| Plugin | Audio in → out | Use it |
|---|---|---|
| **TooB Neural Amp Modeler** | **1 → 1** | **Mono. There is no stereo NAM.** Two amp models = two instances |
| TooB Power Stage | 1 → 1 | Mono — inside a branch |
| TooB Cab IR / Cab Simulator | 1 → 1 | Mono — inside a branch |
| TooB Noise Gate, Tuner, Volume, Tone Stack, Input Stage | 1 → 1 | Mono |
| **TooB Delay** | **1 → 1** | **Mono.** A stereo delay has to come from another collection (§3.4) |
| TooB Flanger, Convolution Reverb, 3 Band EQ, Parametric EQ, Tone | 1 → 1 | Mono versions |
| **TooB CE-2 Chorus** | **1 → 2** | **Mono→stereo widener.** The cheapest way to hear stereo at all |
| **TooB BF-2 Stereo Flanger** | **1 → 2** | Same — widens on its own |
| TooB Freeverb | 2 → 2 | Stereo |
| TooB Convolution Reverb (Stereo) | 2 → 2 | Stereo |
| TooB Tremolo (Stereo) | 2 → 2 | Stereo |
| TooB 3 Band EQ (Stereo) / Parametric EQ (Stereo) / Tone (Stereo) | 2 → 2 | Stereo |
| **TooB Mix** | 2 → 2 | Vol L, Pan L, Vol R, Pan R, **Phase L, Phase R**. Your mono-compatibility test rig (§6) |

The two `1 → 2` plugins are the interesting ones: drop a **TooB CE-2 Chorus** at the end of an
otherwise mono chain and the chain is stereo from there on, with no split, no restructure and no
second NAM.

**You can see all of this in the editor.** PiPedal draws stereo connections as a thick double line
and mono as a thin single one (`PedalboardView.tsx`, `stereoStrokeOuter` / `stereoStrokeInner`).
Where the line goes from fat to thin is where your right channel died.

### 3.4 If you want a stereo delay

TooB's delay is mono. Stereo and ping-pong delays come from the other collections PiPedal's own
docs recommend — `sudo apt install calf-plugins`, `invada-studio-plugins-lv2`, `dpf-plugins-lv2`,
`dragonfly-reverb-lv2` — and PiPedal picks up new LV2 bundles automatically. Confirm the port
count by the connector thickness in the editor before you trust it, and remember every one of
these is CPU you're spending on a Pi 4 that's already tight.

### 3.5 Where output channels are configured

Two different dialogs, both under **Settings → Audio Device Settings**:

```
   Select Channels  (2-channel devices)        Channel Routing  (v2.0.103+)
   ─────────────────────────────────────       ──────────────────────────────────────
     ○ Stereo                                   MAIN route  L → phys channel [0]
     ○ Mono (left channel only)                             R → phys channel [1]
     ○ Mono (right channel only)                 AUX  route  L → [-1]  (off)
                                                            R → [-1]  (off)
   For devices with more channels it
   becomes a checkbox list, one per            Defaults, from ChannelRouterSettings.hpp:
   physical channel.                             mainOutputChannels = {0, 1}
                                                 mainInputChannels  = {1, 1}  ← both from
                                                                        the RIGHT input
```

Notes that matter:

- **Output must be set to "Stereo"** for any of this to work. PiPedal collapses the selection to
  mono if both sides point at the *same* physical channel (`normalizeChannelSelection()` in
  `ChannelRouterSettings.cpp`), and then builds the pedalboard with one output buffer — a stereo
  chain loses its right channel before it ever reaches a jack. Two **different** channels is what
  makes a stereo pedalboard. Unconfigured defaults to 2, so out of the box you are already stereo.
- The **Channel Routing** dialog is **global, not per-preset**. You cannot have one preset stereo
  and another mono at the routing level — but you can at the plugin level, which is better anyway.
- Guitar processing happens on the **Main** route only. Aux is passthrough: a dry unprocessed
  guitar send for re-amping, a backing track in, a vocal mic. From the in-app help: *"If the Main
  and Aux routes share output channels, then the results of the Main and Aux signals are summed
  together on those output channels."*
- The default input is `{1, 1}` — both sides taken from physical channel 1, the **right** input.
  That is the "guitar is on the right channel" default the plan's gotcha 2 warns about.

---

## 4. The FRFR problem — the non-obvious one

This is the option most people land on, and for your rig specifically it has a catch that costs
either CPU or a rebuild of your capture choices.

Your captures are **preamp-only, cab-off** on purpose: the real EL34s and real Celestions are
downstream (see §2.1 of the plan). An FRFR has neither. Send the same signal to both and the FRFR
side is a naked preamp — thin, fizzy, no power-amp compression, no speaker rolloff.

So the two sides need **different processing**, not different pans:

```
   Guitar ─► [Gate] ─► [Drive] ─► [TooB NAM]  ← ONE instance, preamp-only
                                       │
                              ┌── L/R Split ──┐
                     Pan L = -1               Pan R = +1
                     (top → left)             (bottom → right)
                              │                       │
                        (empty branch)      [TooB Power Stage] ─► [TooB Cab IR]
                              │                       │              ↑ mono plugins,
                              ▼                       ▼                inside a branch,
                       OUT L ─► Blackstar      OUT R ─► FRFR           so no collapse
                                FX RETURN
```

Both TooB Power Stage and TooB Cab IR are mono `1 → 1` blocks, which is *correct* here — inside a
branch of a split fed by a mono input, each branch is mono. The split node itself is the
mono→stereo boundary. **This design costs one power-amp sim plus one IR convolution, not a second
NAM**, so it is the only two-amp-sounding option that plausibly fits a Pi 4.

The alternative — a full-amp-with-cab capture on the FRFR side — means a **second NAM instance**,
which is the Pi 5 wall (§7 of this doc, Phase 5 of the plan). Don't.

> **Trap.** If you take the shortcut and just pan the same preamp-only NAM to both sides, you will
> conclude that stereo sounds bad. It isn't stereo that sounds bad, it's a preamp with no power amp
> and no speaker.

> **The two branches will not be time-aligned.** A cab IR is a convolution, and depending on how
> it's partitioned it can add latency the empty branch doesn't have. Asymmetric branches are the
> single most likely source of a mono-compatibility problem in this design — so if you build it,
> §6.2's TooB Mix test is not optional.

---

## 5. Hardware, per interface

| | **UMC204HD** (owned) | **Blokas Pisound** (Phase 4) | **Audient iD4 MkII** (plan's latency option) |
|---|---|---|---|
| USB playback channels | **4** | 2 | 2 |
| Output jacks you can plug an amp into | **MAIN OUT L and R — two separate ¼" TRS jacks** | **ONE ¼" TRS jack** carrying both channels | 2 line outs |
| Extra outputs | **4 × RCA:** "PLAYBACK OUTPUTS A 1 & 2" and "B 3 & 4" | none | none |
| Getting two amps out of it | **Two ordinary guitar cables. That's it** | **Needs a TRS→dual-TS insert cable.** No breakout in the box | Two cables |
| Input | 2 channels, real Hi-Z INSTR switch | One TRS jack, stereo or dual-mono, 100 kΩ | 2 channels, instrument input |
| Verdict for stereo | **Best of the three.** Two jacks, already there, zero spend | Works, but a cable and a soldering-iron-adjacent problem you don't have today | No stereo advantage over what you own |

### 5.1 The UMC204HD, resolved

The "2 in / 4 out" marketing resolves cleanly. From Behringer's own quick-start guide spec table,
the Output → Type row reads verbatim: *"1 x ¼" stereo (Phones), 2 x ¼" TRS (Main Line Out), 4 x
RCA (Playback Line Out)"* — six analog jacks plus phones, carrying **four** USB playback channels:

```
   USB ch 1/2  ─┬──► MAIN OUT L / R            2 × ¼" TRS   ← your amp lives here
                └──► PLAYBACK OUTPUTS A 1 & 2  2 × RCA      ← same channels, different jacks
   USB ch 3/4   ───► PLAYBACK OUTPUTS B 3 & 4  2 × RCA      ← genuinely separate
   selectable   ───► PHONES                    1 × ¼" stereo
                     ▲
                MONITOR A/B switch picks 1-2 or 3-4 — for the HEADPHONES ONLY
```

- **Stereo out of it really is just "use both channels."** MAIN OUT L and R are independent USB
  playback channels. Two guitar cables, done.
- **PiPedal can address all four.** On Linux the device presents a single 4-channel PCM
  (`hw:U192k,0`, positions `FL FR RL RR`) — confirmed in ALSA's own upstream UCM profile for this
  device, which maps hw channels 0,1 to "Line A" and 2,3 to "Line B". PiPedal's Channel Routing
  dialog stores physical channel *indices*, so channels 3/4 are reachable as indices 2 and 3.
- **Channels 3/4 are only on RCA**, so using them for an amp means an RCA→¼" TS cable or adaptors,
  and they're unbalanced. Fine for a short run to a powered speaker; not what you want for a
  long cable to a second valve amp.
- **The MONITOR A/B switch does not mute anything.** It selects the headphone source (1-2 vs 3-4).
  All six analog jacks stay live. One secondary review claims you can only use one RCA set at a
  time; the official guide, the German and French editions and the spec table all disagree.

> **The front-panel STEREO/MONO switch is a decoy.** Behringer's guide: it *"activates mono
> monitoring of audio signals connected to INPUT 1 and INPUT 2."* It affects the zero-latency
> **input**-monitoring path only, not USB playback. It cannot mono your PiPedal output and it
> cannot be the cause if stereo doesn't work. (Neither can the MIX knob, which is the plan's
> gotcha 1 — but with MIX fully to PLAYBACK, as §2 of the plan requires, both of these are out
> of circuit anyway.)

> **The USB quirks are already handled for you.** The Linux kernel carries an explicit entry for
> `0x1397:0x0508` — `QUIRK_FLAG_PLAYBACK_FIRST | QUIRK_FLAG_GENERIC_IMPLICIT_FB` in
> `sound/usb/quirks.c`. `GENERIC_IMPLICIT_FB` is documented as *"same as implicit_fb=1 option"*,
> so on a current kernel the plan's manual `./pipedal-setup.sh implicitfb` step is already applied
> automatically. Keep it as a diagnostic, not a required step. None of this is channel-count
> related — there is no quirk touching how many outputs the device reports.

**Choosing the Pisound does not prevent stereo, but it makes stereo slightly worse.** Its output is
a single unbalanced stereo ¼" jack (Blokas: *"Audio output is DC coupled and can be accessed via
the female ¼" (6.35 mm) stereo jack connector"*, max 2.1 Vrms into 1 kΩ). Two amps means an insert
cable and a splitter dangling off the one jack you were trying to tidy up.

> **Pisound + a normal TS guitar cable shorts the ring to ground.** You get the left channel and
> the right output is shorted out. Harmless *today*, because a mono chain is duplicated to both
> channels anyway (§3.1 fact 2) — so you hear the correct thing and never notice. It stops being
> harmless the day you build a real stereo chain. Different situation from the plan's TRS/TS note
> in §2, which is about the Behringer's *balanced* output losing 6 dB; the Pisound out is
> *unbalanced stereo*, so there's no 6 dB loss and no cold leg — there's a discarded right channel.

**Other interfaces:** don't go shopping. Every stereo-out interface PiPedal works with is
2-out-or-more; stereo is not a feature you buy, and the plan's avoid-list (ToneX One, Zoom GCE-3,
Positive Grid RIFF, M-Audio M-Track Solo — §14) is unchanged by this question. **You already own
the 4-output box** — outs 3/4 (RCA pair B) are a *third* destination if you ever want amp + FRFR +
a dry DI feed to the desk, using the Channel Routing dialog's Aux route (§3.5).

---

## 6. What breaks when you go stereo into two amps

Software is free. This is the part that costs you gigs.

### 6.1 ⚠️ Ground loop hum between two mains-powered amps

Two earthed amps joined by an unbalanced ¼" cable gives the signal two paths to earth, and the
difference between them arrives as 50 Hz hum. Premier Guitar's description is exact:

> "If you connect those amps together with a guitar cable to your board (via a passive Y-cable or
> a second input jack), you are creating a new path for ground currents via the shield of the
> guitar cable."

**The fix is a 1:1 isolation transformer in the signal path** — a DI or line isolator on one side.
That breaks the audio-side loop while every mains earth stays intact:

> "A safer and more effective solution is an isolation transformer at the input of your guitar amp.
> The transformer can transmit your guitar signal without a ground connection, while maintaining
> the safety ground of the amplifier through its power cable."

⚠️ **Never lift a mains earth pin, and never use a "cheater" adapter, to kill hum.** Your HT Stage
60 has 300–500 V rails inside it. Seymour Duncan, on exactly this rig:

> "UNDER NO CIRCUMSTANCES should you try to be clever by removing or 'lifting' the line ground from
> one of your amps. In a fault scenario, the resulting electric shock could very easily kill you."

The failure path is the chassis → the jack sleeves → the cable shield → your strings → you. If a
"ground lift" switch on a DI box fixes it, that's fine — that switch lifts the *audio* shield, not
the mains earth. The pin in the wall stays where it is.

### 6.2 Mono compatibility

Someone will sum your two sides — a FOH engineer with one guitar channel, a phone recording, a
room where both cabs hit the same wall. Whatever cancels, cancels.

A common way modulation effects create width is by **inverting the phase of the wet signal on one
channel** — inaudible in stereo, gone completely when summed. Whether TooB's CE-2 Chorus and BF-2
Stereo Flanger do it that way is not documented, so **test rather than assume**: the two cheapest
ways to get stereo (§3.3) are also the two likeliest to disappear in mono.

**Test it in five minutes without buying anything.** Put **TooB Mix** at the end of the chain and
use its Pan L / Pan R / Phase L / Phase R controls:

| Set | Tells you |
|---|---|
| Pan L and Pan R both to centre | What FOH hears when they sum you. If it thins out or the effect vanishes, that's your answer |
| Phase R inverted | Whether you have a polarity problem, or a genuine phase-vs-frequency problem you can't switch away |

### 6.3 Two different amps is not stereo

Stereo means the same signal, differently placed. Your Blackstar into Celestions on one side and
*anything else* on the other is a **dual-amp rig** — two voices, two EQ curves, two power amps.
That can be great (Seymour Duncan: EL34 + 6V6 "has the potential to produce a mighty alliance"),
but it is not what a stereo chorus was designed for and it will not image; it will just sound like
two amps. Matched cabs are what makes stereo effects *work*, and you are never going to have that.

### 6.4 Level matching two power amps

You will be matching a 60 W valve amp against something with an entirely different sensitivity,
via two output knobs and an FX-loop level switch, by ear, at volume. Two knobs is one more variable
than the plan's §6 level-matching pass already asks you to control, and it drifts every time either
amp's master moves. Practical rule: set the Blackstar as the reference and never touch it again;
trim the second side only.

### 6.5 Unbalanced runs

Your MAIN OUT is balanced TRS; both amps' FX returns are unbalanced TS. Two unbalanced runs to two
boxes is twice the antenna and twice the loop. If the second amp is more than a couple of metres
away, that's when an isolator earns its money regardless of hum.

### 6.6 Nobody can hear it

The consensus among people who do this live is that the stereo sweet spot on a stage is roughly
"standing in the middle", and that most of an audience is not in it. Beyond a few metres the two
sources sum acoustically and you are back to mono with comb filtering. The honest case for a
stereo rig is **for the player**, and the honest place to put it is **headphones or IEMs**, which
is Option 1 and Option 5 in §2.

---

## 7. CPU and latency on a Pi 4

**Latency does not change.** ALSA buffers are sized in *frames*; channels are interleaved inside a
frame. Going stereo does not move the buffer size and does not move round-trip latency. What it
moves is CPU, and CPU is what eventually forces you to bigger buffers — so the effect on latency is
indirect and only appears if you overspend.

**Stereo does not double the DSP.** It doubles only the blocks that are actually running two
channels:

| Block | Mono cost | Stereo cost | Note |
|---|---|---|---|
| **TooB NAM, one instance before the split** | 1× | **1×** | **Unchanged. This is the whole point** |
| Gate, drive, tuner, EQ before the split | 1× | 1× | Unchanged |
| CE-2 Chorus / BF-2 Flanger (1→2) | 1× | ~1× | It was already doing the work; you're just keeping both outputs |
| Stereo reverb, stereo EQ, stereo tremolo (2→2) | 1× | **~2×** | Two channels of the same maths |
| **Convolution Reverb (Stereo)** | 1× | **~2×** | Two IR convolutions. The most expensive doubling on the list |
| Split node itself | – | negligible | A per-sample blend of four coefficients |
| Power Stage + Cab IR on one side only (§4) | – | **+1 of each** | One extra IR, not one extra NAM |
| **Two NAM instances panned L/R** | 1× | **2×** | See below |

**The line that matters:**

```
   stereo effects after ONE mono amp model        two amp models panned L/R
   ───────────────────────────────────────        ─────────────────────────────
   cost: one extra reverb/EQ/chorus               cost: a second NAM instance
   fits: yes, on your Pi 4, if §7 of              fits: no. This is the Phase 5
         pipedal-phase2.md left you                     wall — the pi-stomp figure
         headroom under ~70%                            is ~2 NAM instances on a
                                                        **Pi 5**, and 2 is the ceiling
```

**Two NAM instances panned hard L and hard R is exactly the same CPU bill as the plan's Phase 5
parallel amp blend** (§13 Phase 5). Same two instances, both running constantly; the only
difference is whether the mixer sends them to one output or two. So the plan's Phase 5 conclusion
applies unchanged: **that version of stereo needs a Pi 5, and there is nothing to do differently
now.** Note also that PiPedal's docs say calibration "generally only works for the first NAM plugin
in an effect chain" — in a *parallel* split each branch has its own first NAM, so that caveat
doesn't bite here, but it does rule out chaining NAMs in series.

The §4 FRFR design is the interesting middle: real two-sided sound, one NAM.

---

## 8. The bolt-on verdict — what's reversible

| Decision | Reversible later? | Cost of reversing |
|---|---|---|
| Interface choice (UMC204HD now, Pisound later) | **Yes** | Nothing on the UMC. On a Pisound, one insert cable (§5) |
| Output set to "Mono (left only)" in Audio Device Settings | **Yes** | One radio button |
| Presets built as mono chains in Phase 2 | **Yes** | Add a plugin at the end; re-save each snapshot |
| Snapshot control values (levels, gains, drive settings) | **Yes, they survive** | Nothing — reordering and removing plugins doesn't touch them |
| **The 9 captures and their input/output gain trims** | **Yes, they survive** | Nothing, *unless* the second side is an FRFR (§4) |
| Snapshot count (max 6 per preset) | Yes | You're using 3. Room to add a mono/stereo pair if you ever want it |
| Chain **order** — mono blocks after stereo blocks | **Yes, but** | Free to fix, silent if you don't notice. §8.1 |
| Two NAM instances panned L/R | **No — hardware** | A Pi 5 |
| Buying a second amp | n/a | The actual expense, and the actual decision |

### 8.1 The one thing to get right now, at zero cost

**Chain-order convention: everything mono goes before everything stereo, and stereo blocks go
last.** That is all. It costs nothing, it's what §5 of `pipedal-phase2.md` already draws, and it's
the one habit that makes the conversion a two-minute job instead of a re-plan.

Your Phase 2 chain, and where it would go stereo:

```
   [Tuner] → [Gate] → [Drive] → [TooB NAM] → [Delay] → [Reverb] → [Gain]
     1→1      1→1       1→1        1→1         1→1        ???       1→1
                                                           │
                                       stereo widener goes HERE, at the end ──┐
                                                                              │
   Stereo-ready order — same plugins, mono today:                             │
                                                                              ▼
   [Tuner] → [Gate] → [Drive] → [TooB NAM] → [Delay] → [Gain] → [Chorus/Reverb, stereo]
     ────────────────── all mono, unchanged ──────────────────    ── stereo tail ──
```

Two concrete consequences for the chain you are about to build:

- **TooB Delay is mono (1→1) and TooB Gain/Volume is mono (1→1).** In the plan's order
  `Delay → Reverb → Gain`, if you ever make the Reverb stereo, the **Gain after it kills the right
  channel** (§3.1 fact 4). Put the level-matching Gain *before* the stereo tail, or use a stereo
  block for it.
- The plan's `Reverb` slot is the natural stereo boundary. Pick **TooB Freeverb** or **Convolution
  Reverb (Stereo)** (both 2→2) when you get there and everything upstream stays exactly as it is.

**Do NOT pre-build a split.** An L/R split with both pans at 0 is genuinely mono-identical (§3.2),
so it's technically free — but both branches still *run*, so anything you park in the unused branch
costs CPU forever, and an empty branch is one more thing to misread at 11 pm before a gig. There is
no benefit: adding it later is a two-minute job.

**Nothing to buy now.** Not a cable, not an output block, not a spare interface channel. The UMC's
MAIN OUT R is already free and already live.

---

## 9. Recommendation

**Build Phase 2 mono, exactly as written, with the chain order in §8.1. Then plug headphones into
the interface and add a TooB CE-2 Chorus at the end of one preset.** That is the whole
recommendation and it costs nothing.

Reasoning, given your specific constraints:

- **One mono amp.** Every stereo option except headphones and FOH requires buying a second
  destination. Stereo is not a feature of the Pi; it's a feature of owning two amps.
- **A Pi 4 that's already CPU-constrained.** The version of stereo you'd actually want — two amp
  models — is the Phase 5 blend, and the plan already deferred that to a Pi 5 for exactly this
  reason. The cheap version (stereo effects after one NAM) you can try tonight for free.
- **Phase 2 about to be built.** Nine captures and nine level-matched snapshots is the expensive
  work, and PiPedal's snapshot docs say plainly that reordering and removing plugins doesn't
  disturb it. There is no rebuild penalty to pay later, so paying anything now is pure waste.
- **Stereo is a nice-to-have.** And on a stage, for an audience, largely inaudible (§6.6).

**Cheapest sensible first step, in order:**

1. **Headphones, $0.** Interface PHONES jack, chain ends in a CE-2 Chorus. This is where stereo is
   real, and it is the only place you'll hear what you're deciding about.
2. **One powered FRFR** with the Power Stage + Cab IR design in §4, *if* step 1 convinced you and
   *if* §7 of `pipedal-phase2.md` says you have CPU headroom. One box, one extra cable, no second
   valve amp, no hum problem (an active speaker on its own mains still needs the isolator check —
   §6.1 — but it's one loop, not two power amps fighting).
3. **Everything else — later, or never.**

**The trigger condition that would justify going further:** you are playing a room where FOH will
take two guitar channels, *or* you have moved to a Pi 5 for other reasons and Phase 5's parallel
blend is on the table anyway. Absent one of those, a second amp buys you weight, hum and a
mono-compatibility problem.

---

## 10. What to do now vs later

**Now — Phase 2, all free:**

- [ ] Build the chain with **all mono blocks first, stereo tail last** (§8.1)
- [ ] Put the level-matching **Gain before** where a stereo reverb would go, not after
- [ ] Leave Audio Device Settings output on **Stereo** (not "Mono (left only)")
- [ ] Confirm fact 2 by ear: move your amp cable from **MAIN OUT L to MAIN OUT R**. Same sound =
      confirmed, and you've proved both outputs work before you ever need them
- [ ] Open the **Channel Routing** dialog once and note whether it lists 2 or 4 output channels
      (§11, first row — this is the five-minute answer)
- [ ] Look at the back of the Blackstar and count the FX loop jacks (§11, last row)
- [ ] **Buy nothing**

**Optional, still free, once Phase 2 is signed off:**

- [ ] Add **TooB CE-2 Chorus** to the end of one preset, listen on headphones, and watch the
      connector go from thin to thick in the editor
- [ ] Put **TooB Mix** after it, centre both pans, and hear what FOH would hear (§6.2)
- [ ] Note the CPU delta in the meter. That number is your budget for everything in §7

**Later, only if the trigger in §9 fires:**

- [ ] Powered FRFR + the §4 split design (one NAM, Power Stage + Cab IR on the FRFR side)
- [ ] 1:1 isolation DI before you plug the second box in — not after you hear hum (§6.1)
- [ ] Re-save all snapshots in every preset you restructured (PiPedal docs: new plugins have no
      stored values in existing snapshots)
- [ ] Re-run §6 of `pipedal-phase2.md` — level matching, with the second side in the room

**Never:**

- [ ] Two NAM instances on the Pi 4
- [ ] ⚠️ A lifted mains earth or a cheater plug to fix hum (§6.1)
- [ ] ⚠️ Anything in the Blackstar's speaker output jack (§2.1 of the plan)

---

## 11. Open questions

| Question | Status |
|---|---|
| Does PiPedal's Channel Routing dialog actually list 4 output channels for the UMC204HD? | **Very likely, unverified on your box — and 5 minutes of your time.** ALSA exposes 4 (§5.1); PiPedal addresses whatever ALSA reports. Open the dialog and count, or run `aplay -l` on the Pi |
| Is RCA pair A electrically identical to MAIN OUT, and does the MAIN OUT knob attenuate it? | **Partly unresolved.** The shared "1 & 2" labelling makes the channel identity certain; the guide says the knob *"adjusts the output level at the L & R MAIN OUT"* and says nothing about the RCAs. Secondary sources say the RCAs are fixed-level. Only matters if you use RCA pair A |
| Are the MAIN OUTs actually balanced? | **Not officially stated.** Behringer's guide says only *"2 x ¼" TRS (Main Line Out)"* — the word "balanced" never appears. Doesn't change anything: §2 of the plan already tells you to use a normal TS guitar cable |
| TooB Mix's pan law — do both pans at centre give a true sum on both outputs? | **Probably, untested.** Verified for the *Split* node (`applyHardPan`: pan 0 → L = 1.0, R = 1.0). TooB Mix has the same control names but its DSP source isn't in the ToobAmp repo. Confirm by ear before trusting it as your mono check |
| Is an L/R split with an empty branch and Vol −60 dB truly zero-cost? | **Unresolved.** Both branches always run; an empty branch is a buffer copy, which should be free, but this was not measured. Irrelevant if you follow §8.1 and don't pre-build one |
| ¼" TRS → dual ¼" TS insert cable, Australian price | **Not found** at Altronics or Jaycar. Altronics **P6074B** (3.5 mm TRS → 2× 6.35 mm TS, $29.95) shows the price bracket. A music retailer will have the ¼" version (Hosa YPP-117 class); price unverified |
| Does the Blackstar HT Stage 60 have exactly one FX send and one FX return? | **Assumed mono, unverified.** Reviews confirm a send, a return and the −10/+4 dB switch but not the jack count. **Look at the back of your amp** — this is the fastest check in this document |
| Is §3 still true of *your* installed PiPedal? | **Read from source on `main`, not from the manual.** PiPedal's documentation index has no page on splits, stereo or channel routing — the one sentence in *Building Presets* is the entire coverage. Behaviour like the right-channel discard is an implementation detail and could change. The editor's thin-vs-thick connector line is your live check |
| Does the plan's "calibrate all 9 captures individually" hold up? | **No, and it's not a stereo question** — see the note under §7 and `pipedal-tone-plan.md`. PiPedal's own doc says calibration is *one* voltmeter measurement of your guitar, is explicitly optional, and that TONE3000 models are *"mostly (with rare exceptions) not calibrated"* — so the control is disabled for most of them. Raised here only because it changes the answer to "does going stereo mean redoing the calibration work?" from *no, it survives* to *there was less of it than the plan implies* |

---

## 12. Sources

- [PiPedal — Which LV2 Plugins does PiPedal support?](https://rerdavies.github.io/pipedal/WhichLv2PluginsAreSupported.html) — *"Must have mono or stereo audio inputs and outputs"*
- [PiPedal — An Intro to Snapshots](https://rerdavies.github.io/pipedal/Snapshots.html) — reordering/removing doesn't affect snapshot values; adding does
- [PiPedal — How to Build Presets](https://rerdavies.github.io/pipedal/BuildingPresets.html) — stereo modulation last in the chain
- [PiPedal — Configuring After Installation](https://rerdavies.github.io/pipedal/Configuring.html) — Audio Device Settings, input/output channel selection
- [PiPedal — Using LV2 Audio Plugins](https://rerdavies.github.io/pipedal/UsingLv2Plugins.html) — Calf / Invada / DPF / Dragonfly collections
- [PiPedal — NAM Calibration](https://rerdavies.github.io/pipedal/NamCalibration.html) — calibration is one guitar-voltage measurement, is optional, and only applies to the first NAM in a chain
- [PiPedal — Release Notes](https://rerdavies.github.io/pipedal/ReleaseNotes) — Channel Routing dialog (v2.0.103), L/R Split volume defaults (v1.5.98), TooB Mix phase controls (v1.5.95)
- source: [`Lv2Pedalboard.cpp`](https://github.com/rerdavies/pipedal/blob/main/src/Lv2Pedalboard.cpp) — mono→stereo auto-widening, right-channel discard, mono-duplicated-to-both-outputs, `forceStereo`
- source: [`SplitEffect.hpp`](https://github.com/rerdavies/pipedal/blob/main/src/SplitEffect.hpp) · [`SplitEffect.cpp`](https://github.com/rerdavies/pipedal/blob/main/src/SplitEffect.cpp) — `SplitType {Ab, Mix, Lr}`, `applyHardPan`, pan/vol ranges, `PostMixStereo`
- source: [`ChannelRouterSettings.hpp`](https://github.com/rerdavies/pipedal/blob/main/src/ChannelRouterSettings.hpp) · [`.cpp`](https://github.com/rerdavies/pipedal/blob/main/src/ChannelRouterSettings.cpp) — main/aux output channel index vectors; `normalizeChannelSelection()` collapsing duplicate channels to mono
- source: [`SelectChannelsDialog.tsx`](https://github.com/rerdavies/pipedal/blob/main/vite/src/pipedal/SelectChannelsDialog.tsx) — Stereo / Mono (left) / Mono (right)
- source: [`PedalboardView.tsx`](https://github.com/rerdavies/pipedal/blob/main/vite/src/pipedal/PedalboardView.tsx) — stereo connections drawn as a double line
- source: [ToobAmp LV2 manifests](https://github.com/rerdavies/ToobAmp/tree/master/src/ToobAmp.lv2/ttl.in) — audio port counts for every TooB plugin
- [PiPedal discussion #259 — Custom 2-input Neural Network](https://github.com/rerdavies/pipedal/discussions/259) — the developer on L/R splitters and separate NAM instances per branch
- [Blokas Pisound — product page](https://blokas.io/pisound/) · [Audio connectors](https://blokas.io/pisound/docs/audio/) — one ¼" stereo jack in, one out
- [Behringer UMC204HD product page](https://www.behringer.com/en/products/0805-AAS) — "2 input, 4 output USB recording interface". Note its rear-panel copy ("¼" TRS, RCA and XLR") is wrong: the XLR outputs are a UMC**404**HD feature. Trust the quick-start guide below over the web page
- Behringer *U-PHORIA UMC404HD/UMC204HD/UMC202HD/UMC22/UM2 Quick Start Guide* — official spec table and control list ([archived copy](https://archive.org/details/manualzilla-id-7069370))
- [ALSA UCM profile for the UMC204HD](https://github.com/alsa-project/alsa-ucm-conf/blob/master/ucm2/USB-Audio/Behringer/UMC204HD-HiFi.conf) · [the UCM author on its 4 channels](https://github.com/alsa-project/alsa-ucm-conf/pull/128) — `HWChannels 4`, Line A = hw 0,1 / Line B = hw 2,3
- [`sound/usb/quirks.c`](https://github.com/torvalds/linux/blob/master/sound/usb/quirks.c) — `0x1397:0x0508` gets `QUIRK_FLAG_PLAYBACK_FIRST | QUIRK_FLAG_GENERIC_IMPLICIT_FB` · [the original ALSA commit](https://github.com/torvalds/linux/commit/ae8b1631561a3634cc09d0c62bbdd938eade05ec)
- [Launchpad #1883608 — AlsaInfo for a UMC204HD](https://bugs.launchpad.net/ubuntu/+source/pulseaudio/+bug/1883608/+attachment/5384183/+files/AlsaInfo.txt) — `channels=4`, `Front Left - Front Right - Rear Left - Rear Right`
- [Blackstar HT Stage 60 quick start guide](https://www.manualsdir.com/manuals/758612/blackstar-ht-stage-60-quick-start.html) — series FX loop, speaker-emulated output
- [Premier Guitar — The Shocking Truth About Ground Loops](https://www.premierguitar.com/pro-advice/state-of-the-stomp/ground-loop-isolator) — why two amps loop; isolation transformer; do not lift the mains earth
- [Seymour Duncan — Multi-Amp Rigs 101](https://www.seymourduncan.com/blog/latest-updates/multi-amp-rigs-101) — level matching, hum, the mains-earth warning
- [Radial Engineering — How Pros Run Stereo Guitar Rigs](https://www.radialeng.com/blog/how-pros-run-stereo-guitar-rigs) — wet/dry/wet, isolation over long unbalanced runs
- [Fractal forum — Does your band run mono or stereo guitars live?](https://forum.fractalaudio.com/threads/does-your-band-run-mono-or-stereo-guitars-live.139872/) · [Gearspace — Live sound: mono or stereo?](https://gearspace.com/threads/live-sound-mono-or-stereo.406059/) — the sweet-spot reality
- Pricing, checked Sept 2026: [Joondalup Music — HeadRush FRFR-108 MKII, $509 AUD](https://joondalupmusic.com.au/products/headrush-frfr-108-mkii-8-full-range-powered-speaker)
  (sold out at time of writing) · [Derringers](https://www.derringers.com.au/products/headrush-frfr-108-mk2-powered-speaker-for-guitar) and
  [Mooloolaba Music](https://www.mooloolabamusic.com.au/headrush-frfr-108-mkii) also stock it and advertise price matching ·
  [HeadRush product page](https://www.headrushfx.com/products/frfr108mk2/index.html) for specs
- Figures marked ⚠ in §2.1 (the ~$429 interstate FRFR and the ~$199 JBL clearance) are from a
  research pass that was not independently re-checked. Treat them as leads, not quotes
