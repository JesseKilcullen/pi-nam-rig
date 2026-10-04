# PiPedal Rig — Status & Next Steps

**Last updated:** 2026-10-04

This supersedes the phase-by-phase framing in `presets-reference/pipedal-nam-rig-plan.md` / `archive/pipedal-phase2.md`
for tracking *where the build actually is*. Those files still hold the reference detail (signal
chain reasoning, level-matching method, MIDI byte primer); this doc is just the current status and
what's left.

## 0. Pick up here next session

**As of 2026-10-04 the rig has a pitch shifter, a footswitch settings menu and a tuner mute, all
working on the hardware.** The footswitch controller itself (switches, encoder, OLED, relay) has been
working end-to-end since 2026-09-23 — bring-up details: `pico-footswitch-v2/OLED-BLANK-HANDOFF.md`.
Network/hotspot/login details: [`QUICK-REFERENCE.md`](./QUICK-REFERENCE.md).

### What was added 2026-10-04

- **Pitch Shift plugin** (`lv2-pitch-shift/`). TONE3000's new pitch shifter (±24 semitones, low
  latency) ported to plain C++ as its own LV2: TONE3000's own LV2 build never shows up in PiPedal
  because PiPedal **skips plugins whose controls are LV2 patch parameters** ("Has unsupported patch
  parameters"). Bit-identical to the original (`test/compare.sh`). Installed at
  `/usr/lib/lv2/PitchShiftTone3000.lv2`; rebuild/install: `make && sudo make install`, then restart
  `pipedald`. It is in all 8 presets (before the first amp), **powered off by default** (a powered-off
  shifter is a bit-exact, zero-latency passthrough). Reported latency 11/16/21/31 ms for the
  20/30/40/60 ms Buffer; attacks arrive a few ms late because of the onset re-sync.
- **Graphic EQ** (TooB Graphic Eq: seven bands 100 Hz-6.4 kHz at ±15 dB, plus Level ±30 dB) in all
  8 presets, placed right after each preset's main EQ and **before** the chorus/delay/reverb.
  Not at the very end: it is mono, and **PiPedal gives a mono plugin only the left channel of a
  stereo signal**, so after a stereo reverb it would collapse the reverb's width.
- **Settings menu on the RESET switch** (formerly "preset 1 + snapshot 1"). RESET opens
  `Level / EQ / Pitch Shift / Save`; the encoder scrolls and pushes to select; Level and Pitch show a
  ± slider (0.5 dB / 1 semitone per click); EQ lists the seven bands first; RESET goes back one page
  and any other footswitch leaves the menu. Pitch switches itself on whenever the shift is non-zero.
  - **Save** does what PiPedal's UI needs two clicks for: store the live sound in the selected
    snapshot (`setSnapshots`), then save the preset (`saveCurrentPreset`). Without a save, an edit
    only marks the snapshot "modified" and the next preset load throws it away. It waits for PiPedal
    to confirm the snapshot is stored before saving (saving too early makes PiPedal clear the
    snapshot selection) and re-selects it if that still happens.
  - The encoder sends only **relative steps**; `pi_relay.py` applies them to the loaded preset's
    plugins through PiPedal's `setControl` (`pipedal_edit.py`), so every preset keeps its own
    settings and the OLED shows the real value. Wire protocol, Pico → Pi: CC30-38 steps (value
    64 ± clicks), CC39 "report this param", CC40 save; Pi → Pico SysEx 0x04 (a param's value) and
    0x05 (save result). Logic is plain Python with tests: `midi_logic.EditMenu`,
    `pipedal_edit.py` (`cd pico-footswitch-v2 && python3 -m unittest test_midi_logic test_pipedal_edit test_pitch test_pipedal_ws`, 103 tests).
  - The relay now also **reads** the Pico's MIDI (a second ALSA subscriber next to PiPedal's; fine).
- **Tuner mute.** The TUNER/MUTE switch (CC27) mutes the tuner plugin's output (it is first in
  every chain, so everything after it). Done in the relay with absolute on/off, **not** PiPedal MIDI
  bindings (a binding can only toggle and has to be added per preset). A snapshot never stores the
  tuner muted. **Known quirk, accepted:** changing preset unmutes it (the relay re-applies the
  mute on a preset load but PiPedal's rebuild seems to overwrite it), leaving the Pico's screen on
  "tuner" until the switch is pressed again.

### Working on this rig — things that bite

- **The live bank is the source of truth, and the generator now matches it** (2026-10-04: all five
  by-ear edits folded in; `python3 generator-scripts/check-bank-diff.py` on the Pi reports all 8
  presets identical). Re-run that before any regenerate; if it lists differences, those are edits
  a regenerate would overwrite. To change the live bank without regenerating, use an in-place
  additive script like `add-menu-plugins-to-bank.py` / `fill-missing-snapshot-values.py` (both back
  up, check the result and are idempotent).
- **PiPedal writes a split's inner plugins as a plain list** (`topChain`/`bottomChain`), in the
  bank file and over the websocket. Code that walks a pedalboard must handle that (a Save bug on
  preset 6 came from assuming a `{"items": [...]}` wrapper).
- **A snapshot with no stored value for a plugin leaves that plugin alone on recall.** Snapshots
  must carry a value for every plugin or it stops following snapshot changes.
- **Sudo is the user's.** Jesse runs sudo lines himself in a normal terminal (a Claude `!` command
  has no TTY). Pico firmware is pushed by mounting the drive (`sudo mount -o uid=1000,gid=1000 -L
  CIRCUITPY /mnt/circuitpy`), copying `code.py midi_logic.py oled_display.py`, then `sudo umount`.
  The relay runs as `jesse`: `kill $(systemctl show pipedal-tuner-relay -p MainPID --value)` and
  systemd restarts it with the new code, no sudo needed.
- **Do not test Save (or toggle controls) on the live preset while Jesse is playing**: Save stores
  whatever is currently live.

**What's left:**
1. **Finish the hotspot** — configured (network `pipedal`, channel 6, trigger "No ethernet
   connection"). It comes up and a laptop joined it, but **the UI didn't load**. Next steps
   (find the real gateway IP with `ipconfig`, check for a 169.254 address, try a phone) are in
   [`QUICK-REFERENCE.md`](./QUICK-REFERENCE.md).
   **Tuner display: fixed and confirmed (2026-09-24).** TooB Tuner's `FREQ` port is a fractional
   MIDI note number (`units:midiNote` in `ToobTuner.ttl`, -1 = no pitch), not Hz. The relay was
   converting it as Hz, so a played D showed "G#0". Now uses `pitch.midi_note_to_note_cents`.
   Note letters and cents are correct. Known cosmetic quirk, accepted as-is: the octave number
   reads 2 low (open D string shows "D1"; the plugin reports ~26 for it rather than MIDI 50).
   If it ever matters, drop the octave in `pitch.note_name` on the Pico (PiPedal's own UI shows
   the letter only).
2. **Remaining on-hardware checks** (§2.6): encoder Browse (starts near the current preset, push
   loads it + snapshot 1, footswitch or 3 s idle cancels, presets 7-8 reachable). Preset 1 + snapshot 1
   is no longer on the RESET switch — it is preset mode → switch 1, or encoder Browse.
3. **Optional:** the mute surviving a preset change (re-apply it a moment after the load); remove
   the unusable `/usr/lib/lv2/TONE3000.lv2` (`sudo rm -r`); `find_tuner_instance_id` in
   `pipedal_ws.py` still assumes the dict chain shape (harmless, the tuner is never inside a split).

### Earlier (2026-09-12) — generator-script commit (DONE 2026-10-04: see above; kept for history — do not run the commands below blindly, run `check-bank-diff.py` first)

No data at risk from this — every by-ear edit below is
already saved to the live bank file on disk (PiPedal auto-persists snapshot value changes as you
make them; confirmed by reading `/var/pipedal/presets/Default+Bank.bank` directly). What's still
outstanding is purely a housekeeping step: baking those same values into the generator script's
committed run, so a future regenerate can't silently drop them back to old numbers. Do this
whenever convenient, no rush:

```bash
python3 ~/add-muse-opeth-presets.py --dry-run    # confirm still clean first
sudo systemctl stop pipedald
sudo python3 ~/add-muse-opeth-presets.py
sudo systemctl start pipedald
```
Then refresh the browser tab.

**What's queued in that commit:**
- From the 2026-09-10 session: full level-match pass across all 8 presets (master Output Volume,
  EQ gain, NAM outputGain — see §1); HG Lead high-cut 13kHz → 9.5kHz; Opeth high-cut 12kHz →
  10.3kHz; Massive "Fuzz Low"/"Fuzz High" top capture switched to Gain-II G8, "Fuzz Low"'s own fuzz
  capture softened to `SunFace V7 F10 C3`; two stray-enabled pedals fixed (Blues Driver in Clean,
  Sunface fuzz in Ambient).
- From the 2026-09-12 studio-monitor session: Muse "Clean Arp" and Opeth "Clean Prog" `outputGain`
  -1 → 0; Opeth "Heavy" `outputGain` -1 → -3. Verified byte-for-byte against the live bank before
  being added to the script — see §1.

**After that's committed**, everything non-physical on this list is done — buzz resolved, amp
tested, MIDI bench-tested (§2.1, §2.2, §2.5 below). The real next step is §2.4 — build the
footswitch controller. Everything past that point needs the physical hardware in hand.

## 1. Where things stand

- **Presets/snapshots:** the bank has grown to **8 presets** (Clean, Ambient, Crunch, HG Rhythm,
  HG Lead, Massive, Muse, Opeth - Ghost Reveries), snapshot count varies 4-5 per preset (not a
  uniform 6 anymore). **The footswitch controller design is still 6×6** and is not being revised —
  presets 7 (Muse) and 8 (Opeth) are deliberately **encoder/OLED-browse-only**, not on a direct
  footswitch. Keep this distinction in mind in every doc/plan below: "the six" means the
  footswitch-reachable set; 7-8 are extras reachable only via Browse mode once the OLED is wired
  (`pipedal-hardware-v2.md` §4.2).
  Switching snapshots is clean — no click/drop, confirmed even when different NAM captures are
  loaded per snapshot (Design A).
- **Presets are generated, not hand-edited.** `build-kraken-presets.py` builds the six;
  `add-muse-opeth-presets.py` layers Muse/Opeth on top. Both live in this folder and on the Pi at
  `~/`. Workflow, traps and rollback: `presets-reference/pipedal-presets-howto.md`. Current design/MIDI-binding
  reference: `presets-reference/pipedal-session-handoff.md`.
- **Level-matching: done (2026-09-10).** All 8 presets matched via each preset's master Output
  Volume (Clean +8, Ambient +3, HG Lead -2, rest 0), plus EQ `gain` and NAM `outputGain` tweaks on
  several. Values are baked into the generator scripts, not just the live UI — see
  `presets-reference/pipedal-session-handoff.md` and the scripts' inline comments for the specific numbers.
- **Presets:** switching between presets has a small click/drop. Expected — a preset change
  rebuilds the plugin graph (§5 of the main plan); snapshots are the seamless ones. Worth
  double-checking it's *only* the expected graph-rebuild gap and not something extra.
- **Monitoring:** headphones, studio monitors, and now the amp (Blackstar FX return) at real
  volume — all confirmed good as of 2026-09-12. Levels/tones took some getting used to on the amp
  (real speaker rolloff reads differently than flat monitors, see the cab IR note below) but
  nothing outstanding.
- **Right-channel buzz — RESOLVED (2026-09-12).** Confirmed headphone-jack/adapter-specific, not
  PiPedal, not upstream DSP — clean on studio monitors, clean on the amp's Main Out with a plain
  ¼" cable and no adapter. See §3.
- **Muse/Opeth by-ear tweaks — done and baked in (2026-09-12).** Studio-monitor testing surfaced
  three `outputGain` edits, made live in the UI: Muse "Clean Arp" and Opeth "Clean Prog" both
  lifted -1 → 0 (cleans read quiet next to the amp snapshots), Opeth "Heavy" dropped -1 → -3 (too
  hot on real speakers). Verified byte-for-byte against the live bank and folded into
  `add-muse-opeth-presets.py` — nothing else in either preset changed. Not yet committed to the
  live bank file (still needs the stop/run/start sequence — see §0-style commit steps in
  `presets-reference/pipedal-presets-howto.md` §2).
- **Pi 4:** heatsink fitted, no active cooling, temperature is not a concern — don't need to keep
  chasing this in docs or testing.
- **Headless:** already done.
- **Hardware controller: built and wired (2026-09-23).** All switches, both mode LEDs, OLED and
  encoder confirmed on hardware. One broken solder joint on the encoder push switch was found and
  resoldered.
- **Enclosure design:** done — hole sizes/positions confirmed from real datasheets, to-scale drill
  templates (`enclosure-templates/pipedal-footswitch-drill-template.svg`, `enclosure-templates/pipedal-footswitch-backwall-drill-template.svg`),
  USB back-wall connector chosen and sourced (§2.3a), full wiring diagram (§2.4), tool/fastener
  shopping list (`enclosure-build-reference/pipedal-bunnings-list.md`), step-by-step build guide (`pipedal-footswitch-build-guide.md`).
  **Nothing physically built yet** — no metal cut, no parts bought from the Bunnings list, USB
  coupler not yet ordered.
- **Firmware:** `pico-footswitch-v2/` flashed and running on the Pico. Footswitches switch
  presets/snapshots correctly in PiPedal; TUNER/MUTE sends CC26/CC27 as designed. Still targets 6
  presets × up to 6 snapshots — presets 7-8 are encoder-only.
- **OLED — 3x2 grid, live tuner, preset-browse: working on hardware (2026-09-23).**
  - The SSD1306 driver *does* work with the SSD1309 panel. The blank screen was SPI speed:
    FourWire's default 24 MHz was too fast for the hand-wired leads, fixed with
    `baudrate=1000000` in `oled_display.init()`. The panel board is in SPI mode (its IIC/SPI
    resistor jumpers were checked).
  - `rotaryio` counts exactly **1 step per detent** on the SR1230/A-6329, correct direction — no
    divisor needed.
  - Diagnostics left in the firmware: a 2 s "OLED OK" boot splash, the Pico's onboard LED blinks
    on each incoming SysEx from the relay, and serial prints for SysEx arrival and encoder
    turn/push.
- **Pi relay (`pi_relay.py` / `pipedal_ws.py`): working, installed as
  `pipedal-tuner-relay.service`.** Two deadlocks fixed: the original handshake one (reader loop
  now starts in `PiPedalClient.__init__`), and a second where push handlers calling `request()`
  (e.g. `getPresets` after `onPedalboardChanged`) froze the relay after the first
  preset/snapshot change — pushes now run on a separate worker task (regression test in
  `test_pipedal_ws.py`). Also fixed: `onPedalboardChanged` / `onPresetsChanged` push bodies are
  wrapped (`{clientId, pedalboard}` / `{clientId, presets}`), which had caused blank snapshot
  names. Old Pi-side copies backed up in `~/pico-footswitch-v2/backup-before-push-fix/`.
  **Pico replug recovery:** if the Pico drops off USB (e.g. the cable gets bumped), it reboots
  with a blank screen and the old relay kept sending to the dead port. The relay now watches
  the Pico's USB device number, exits with status 1 on any disconnect/reconnect (or websocket
  close), and systemd restarts it, which waits 5 s for the Pico to boot and resends all names.
  The deployed unit still says `Restart=on-failure` (changing it needs sudo); that's enough
  since the relay exits non-zero, but the repo's `.service` file now says `Restart=always`.
- **Archived:** `pipedal-phase2.md` moved to `archive/` — it assumed 3 presets × 3 snapshots and is
  well behind the actual build now. Its level-matching and backup steps are still valid
  methodology, just superseded in practice by the generator scripts + howto doc above.

## 2. Next steps

1. ~~Isolate the right-channel buzz.~~ **Resolved, 2026-09-12** — headphone jack/adapter-specific,
   confirmed clean on monitors and on the amp's Main Out (plain ¼" cable, no adapter). See §3.
2. ~~Test on the amp, not just headphones/monitors, more broadly.~~ **Done, 2026-09-12.** Levels
   and tones confirmed good through the Blackstar FX return at real volume — took some getting
   used to (see §1's cab IR note: a real speaker's own rolloff makes the amp read differently than
   monitors, that's expected, not a fault).
3. ~~Level-match all presets × snapshots.~~ **Done, 2026-09-10** — all 8 presets matched via master
   Output Volume, baked into the generator scripts. See §1.
4. ~~Build the footswitch controller.~~ **Done, 2026-09-23** — see §1.
5. **Test the MIDI switching for real** — footswitch preset/snapshot switching and mode switching
   confirmed 2026-09-23; RESET and the MUTE binding still to confirm:
   - ~~Bench-test with `snd-virmidi` first (no Pico needed).~~ **Done, 2026-09-12** — absolute
     Program Change (0-indexed, no binding needed) and CC20 snapshot-force both confirmed via
     `amidi -p hw:0,0 -S ...`. See `pipedal-hardware-v2.md` §5.1 and `presets-reference/pipedal-session-handoff.md`
     §6.27-28. (Note: `mido`/`python-rtmidi` did **not** work for this bench test — use `amidi -S`,
     not `mido`, against `snd-virmidi`.)
   - With the actual Pico: confirm every remaining CC/PC the firmware sends does the right thing
     in PiPedal (`Settings → System MIDI Bindings`) — PC/CC20 are now proven, but the rest of the
     mapping (other snapshot CCs, mode paging) still needs the real hardware.
   - Confirm mode switching (PRESET/SNAPSHOT), Reset, and Tuner/Mute all behave as in
     `test_midi_logic.py`.
6. **Bring up the OLED.** Mostly done 2026-09-23 — struck-through items confirmed:
   - ~~Flash `code.py` + libraries, confirm the screen lights up.~~ Done (needed the 1 MHz SPI
     fix, see §1).
   - ~~Confirm preset/snapshot names show up correctly when you switch presets/snapshots.~~ Done,
     after the relay push-handling fixes (see §1).
   - Load a preset with TooB Tuner in the chain, hit Tuner/Mute, play a note, confirm the OLED
     switches to note+cents and tracks in real time.
   - Confirm the 3x2 grid shows correctly in both PRESET and SNAPSHOT mode, with the border on
     the actually-active cell, and swaps mode-to-mode instantly (no round-trip lag) since both
     grids are cached on the Pico.
   - Once the encoder's wired: turn it, confirm Browse mode shows on the OLED and starts near
     the currently-loaded preset (not always preset 1); confirm the push switch loads the
     highlighted one and forces snapshot 1; confirm any footswitch press cancels Browse; confirm
     3 seconds of no activity also cancels it. (The `rotaryio` 1-step-per-detent part is
     already confirmed.)
   - ~~Install `pipedal-tuner-relay.service` so the relay survives reboots.~~ Done.
7. ~~Automated CPU + xrun monitoring with a generated report.~~ **Done, and run on the real Pi
   2026-09-10.** `./pipedal-setup.sh report [seconds]` (default 600s) — samples CPU (via
   `/proc/stat` deltas, not `top`) and temp every 2s, counts underruns from `journalctl -u
   pipedald` over the same window, writes a timestamped summary to `~/pipedal-reports/` and prints
   it. Greps for **"underrun"**, not "xrun" — confirmed from PiPedal's own source
   (`src/AlsaDriver.cpp`, `Lv2Log::info("Recovering from ALSA <direction> underrun.")`) that's the
   actual log wording. Two real runs so far: 300s general (peak CPU 55%, 0 underruns) and 60s
   targeted at "4 HG Rhythm" → Solo (peak CPU 32%, 0 underruns) — see §3, this ruled out CPU as the
   cause of the crackle.

## 3. Troubleshooting

### Crackling on louder/higher-gain/more-complex presets — RESOLVED, 2026-09-10

Reported symptom: crackle on both headphones and the amp, worse on complex presets, worse on
loud/sustained playing (chugging, ringing out a note), no visible clipping on the interface input
or PiPedal's output meter, sometimes improved by lowering output gain, hardest to reproduce on "4
HG Rhythm" → Solo.

**Diagnosis, confirmed by measurement, not guesswork:** two real `./pipedal-setup.sh report` runs
(300s general, 60s targeted at HG Rhythm/Solo while trying to trigger it) both came back **0
underruns**, peak CPU 32-55% — well under the ~70% guideline. So this was never a CPU/xrun problem.
That pointed at inter-sample (true-peak) overs — clipping inside a plugin's own internal stage that
a standard sample-peak meter won't show. Confirmed by inspecting the live preset: HG Rhythm/Solo's
NAM `outputGain` was sitting at only -0.5 dB, right at the ceiling.

**Fix applied:** pulled NAM `outputGain` back to give a few dB of real headroom (HG Rhythm now -4,
Solo follows via `rel()`), then did a full level-match pass across all 8 presets on top of that
using each preset's master Output Volume (not NAM's outputGain, which sits mid-chain before Cab
IR/EQ/Reverb) — see §1. Both changes are baked into the generator scripts, not just the live UI.

**Caveat for next time this comes up:** if lowering the final gain stage "fixes" a crackle without
first checking `./pipedal-setup.sh report`, that's not proof it was gain-staging — it just makes an
existing CPU-underrun glitch quieter without fixing the CPU load. Always check the report first;
a masked-but-still-occurring digital glitch is a different (lesser) risk to speakers than genuine
clipping, not the same thing as fixed. Genuine clipping delivers more sustained high-frequency
energy to a driver than clean signal at the same perceived loudness, and is a well-documented real
cause of speaker/tweeter damage in gigging setups.

### Right-channel buzz — RESOLVED, 2026-09-12

Symptom: a slight vibration/buzz from the right channel, signal-dependent (silent when idle/muted),
present across two different sets of headphones, and on every preset including the simplest
("1 Clean") — not a specific preset's gain-staging, since it happens even where there's no hot
NAM capture.

**Diagnosis:** headphone-jack/adapter-specific, not PiPedal, not the interface's DAC/processing
path. Ruled out in order: the headphones themselves (two different pairs, same result); pure
electrical/interference noise (would show in silence too, doesn't); presets/snapshots/DSP (clean
across a full pass on studio monitors); the interface's Main Out generally (clean on the amp's FX
return too). Confirmed with the amp's Main Out via a plain ¼" cable, no 3.5mm adapter at all —
no buzz. Since that's the same result as monitors/amp and the only common factor removed was the
headphone jack + adapter, the fault sits there.

**Not chased further:** no need — the fix in practice is just "don't use that headphone jack/adapter
for critical listening," and monitoring is already confirmed good on monitors and the amp (§1).

## 4. Not needed right now

- Temperature/heatsink docs and testing — already fitted, not an issue, don't keep re-litigating it.
- Active cooling — not using it, don't need it on the Pi 4.
