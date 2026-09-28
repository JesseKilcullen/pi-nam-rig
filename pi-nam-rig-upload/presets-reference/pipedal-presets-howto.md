# Building & fixing PiPedal presets, snapshots and banks

Everything needed to change a tone, add a snapshot, or fix a broken preset.
Self-contained — this is the only doc a session needs for preset work.

---

## 0. Paste this into a new session

```
Read ~/Downloads/pipedal-presets-howto.md first, then: <WHAT I WANT>

Pi: ssh jesse@192.168.0.73 (key auth, no passphrase). Service: pipedald.
Presets are generated, never hand-edited: ~/build-kraken-presets.py on the Pi,
master copy in ~/Downloads on this laptop.
Always run --dry-run and show me the output before asking me to commit.
I have to run the sudo lines myself; sudo needs a password on a TTY.
```

---

## 1. Rules

1. **Presets are generated, not edited.** Change `build-kraken-presets.py`, not
   the JSON, not the UI. The script rebuilds all six from scratch, so it is
   idempotent — re-running fixes anything saved over by accident.
2. **`--dry-run` before every commit.** Read-only, no `sudo`, service stays up.
   It runs both preflight checks against the real captures and the real TTLs.
3. **Stop `pipedald` before writing.** It holds this state in memory and
   rewrites the files on any change. Edits made while it runs will vanish.
4. **Never edit the bank's internal `name`,** or rename a bank outside the UI —
   PiPedal derives the filename from the name and you'll orphan the file.

## 2. The loop

```bash
# on the laptop, after editing ~/Downloads/build-kraken-presets.py
scp ~/Downloads/build-kraken-presets.py jesse@192.168.0.73:/home/jesse/

# on the Pi — read-only, safe with the service running
python3 ~/build-kraken-presets.py --dry-run

# commit (needs a password, so a human runs these three)
sudo systemctl stop pipedald
sudo python3 ~/build-kraken-presets.py
sudo systemctl start pipedald
```

Backs up to `~/bank-backup-<timestamp>.json` (the invoking user's home, not
root's), writes to a temp file, re-parses to prove valid JSON, then swaps in
and preserves `pipedal_d` ownership. **Refresh the browser tab afterwards.**

### Rollback

```bash
sudo systemctl stop pipedald
sudo cp ~/bank-backup-<timestamp>.json /var/pipedal/presets/Default+Bank.bank
sudo chown pipedal_d:pipedal_d /var/pipedal/presets/Default+Bank.bank
sudo systemctl start pipedald
```

## 3. Where things are

| | |
|---|---|
| Bank (mine) | `/var/pipedal/presets/Default+Bank.bank` |
| Bank (factory) | `/var/pipedal/presets/Factory+Presets.bank` — **do not touch** |
| Bank list | `/var/pipedal/presets/index.banks` |
| Captures | `/var/pipedal/audio_uploads/NeuralAmpModels/Factory Models/` |
| Cab IRs | `/var/pipedal/audio_uploads/CabIR/Factory IRs/` |
| Reverb IRs | `/var/pipedal/audio_uploads/ReverbImpulseFiles/` |
| Plugin TTLs | `/usr/lib/lv2/ToobAmp.lv2/*.ttl` — the only truth on ranges/units |
| Generator | `~/build-kraken-presets.py` (Pi) · `~/Downloads/` (laptop) |
| Probe | `~/pipedal-probe.py` — see §7 |

Files are `pipedal_d:pipedal_d`, mode 664, dir setgid `drwxrwsr-x`. `jesse` is
in `sudo` but **not** in `pipedal_d`, and `sudo` needs a password — so an
assistant can read, `scp` and `--dry-run`, but cannot commit.

## 4. Data model, in short

```
BANK  →  PRESET (= the rig: which plugins, in what order)  →  SNAPSHOT
          switching = graph rebuild = audible GAP            = every control
                                                               switching = SEAMLESS
```

- **Max 6 snapshots per preset**, a fixed array with `null` holes.
- A snapshot **cannot add, remove or re-order a plugin** — `values[].instanceId`
  is a foreign key into `items[].instanceId`. Put the whole chain in the preset
  up front, even where a snapshot leaves half of it bypassed.
- Swapping a NAM `modelFile` inside a snapshot **is seamless on this rig**.
- **3 NAM instances fit on a Pi 4** — tested 2026-09-05 on preset 6, which
  runs a fuzz, a Kraken and a clean amp with the last two in parallel. The old
  "max 2" rule came from a **pre-`Threaded`** measurement, and `Threaded` is
  worth 2.5–3.7× and is now on everywhere. The only xruns were on changing
  preset *while still playing*, which is the graph-rebuild gap, not this
  preset. **4 is untested.** Capture swapping is still cheaper than an extra
  instance, and a bypassed instance still costs — so prefer swapping where it
  gives the same result.

Full detail: [`pipedal-data-model.md`](./pipedal-data-model.md).

## 5. The generator

```
item(short, controls, paths, enabled)   one plugin. Writes pathProperties AND
                                        lv2State from one source — see trap 1
tuner() gate() input_stage() nam() pedal() cab_ir() eq3() peq()
chorus() delay() multi_echo() freeverb() conv_reverb()

presets()               -> [(name, [items...])]        the six rigs
snapshots_for(name, it) -> [snapshot|None] * 6         the snapshot designs
snapshot(name, color, items, changes)   complete snapshot, built from items
snap_value(it, enabled, controls, paths)
rel(+3.5)               "this item's value, plus 3.5"
preflight(built)        every .nam/.wav must exist          ABORTS
check_ranges(built)     every value inside its TTL range    WARNS
```

### Change a knob

Edit the call in `presets()`. Snapshots inherit it automatically, and `rel()`
deltas move with it — that is why they exist.

### Add or change a snapshot

In `snapshots_for()`, keyed by `(plugin short name, nth occurrence)`:

```python
snapshot("Lead", "red", items, {
    AMP:   {"controls": {"outputGain": rel(+3)}},
    DELAY: {"controls": {"level": rel(+10)}},
    PEDAL: {"enabled": False},
    AMP:   {"paths": {P + "toob-nam#modelFile": KRAKEN + "/Kraken_Gain-I_G8 .nam"}},
})
```

Selectors: `PEDAL`/`AMP` (presets with a pedal capture), `AMP0` (without),
`GATE EQ3 PEQ DELAY FREEVERB CHORUS MECHO CONVERB`. A selector or control key
that doesn't exist **raises** rather than silently doing nothing.

**Snapshot 1 is the preset's home sound** and must equal the item values
(`selectedSnapshot: 0` relies on it). Order the rest most-useful-first, so a
3-switch layout loses the least important one.

Colours (else silently grey): `grey blueGrey red pink purple deepPurple indigo
blue lightBlue cyan teal green lightGreen lime yellow amber orange deepOrange
brown`.

### Add a plugin to a preset

Add it to the `items` list. Every snapshot picks it up automatically because
snapshots are generated from the items — this is the whole reason not to
hand-write them.

## 6. The seven traps

All silent. All have been hit at least once.

**1. `pathProperties` alone does nothing (preset load).** The file a preset
restores lives in `lv2State`. Writing only `pathProperties` gives valid-looking
paths and *every file selector empty*. `item()` derives both from one source.
Empty slots use `atom#String`, real paths `atom#Path`. The convolution reverb's
key is `toob-impulse#impulseFile`, not its own URI. **Verify `lv2State`, not
`pathProperties`** — reading back the field you wrote proves nothing.

**2. A snapshot is NOT a sparse diff.** On apply, every input control is
pre-filled with the plugin's **TTL default**, then only the listed keys are
overwritten. An omitted control **resets to the plugin default**; an item with
no `SnapshotValue` at all is **un-bypassed and fully defaulted**. So every
snapshot carries a value for every item, and every value lists every control.
Build from the item and override — never hand-write.
*(`src/AudioHost.cpp`, `IndexedSnapshotValue`.)*

**3. The `bypass` control beats `isEnabled`.** `ApplyValues()` calls
`SetBypass(isEnabled)` and *then* `SetControl()` on every input control,
including the `lv2:enabled` port. So the listed `bypass` value wins. Set both
consistently — `snap_value()` does. **`lv2:enabled`: 1 = active, 0 = bypassed**,
so TooB's `"bypass": 1` means *on*, which reads backwards.

**4. For snapshots, `pathProperties` is the field that matters** — the opposite
of trap 1. `ApplyValues()` feeds the realtime thread from `pathProperties`; its
`SetLv2State` call is commented out. Preset *load* still uses `lv2State`. Write
both.

**5. Out-of-range values are clamped silently, and units are inconsistent.**
`toob-parametric-eq` splits units *inside one plugin* — `loCut`/`lfC`/`lmfC` in
**Hz**, `hmfC`/`hfC`/`hiCut` in **kHz**. `hiCut: 9000` clamps to 21 kHz, i.e.
filter fully open. That mis-voiced three presets from the first build and nobody
heard it. Other known ones: `multi-echo` levels are **percent** not dB
(`direct` defaults to 100; 0 kills the dry path); `noise-gate reduction` is
−60..−6; conv reverb `time` is **seconds** and truncates the IR.
**Don't memorise — `check_ranges()` reads the TTLs and tells you.**

**6. Filenames lie.** `Kraken_Gain-I_G8 .nam` has a **trailing space**. Gain-II
boost files are misspelled **`TebleBoost`** (no r) while Gain-I ones are
`TrebleBoost`. `preflight()` catches these; a bad path is otherwise an empty
selector and no model, with no error.

**7. Two NAM controls aren't named what they do.**
`buffer` = the **Threaded** toggle — moves inference off the audio thread for
1.33 ms of latency, and is worth **2.5–3.7×** in CPU. On everywhere now.
`modelSize` = **Quality** (0–1), the A2 slimmable submodel selector; left at 0.
Also `toneStack`: 0=Bassman 1=JCM8000 2=Baxandall **3=Bypass (default)** — at
Bypass, `bass`/`mid`/`treble` do nothing. Amps use 2, pedal captures 3.

## 7. Verifying

### On disk — completeness and paths

```bash
ssh jesse@192.168.0.73 'python3 -c "
import json
b=json.load(open(\"/var/pipedal/presets/Default+Bank.bank\"))
for e in b[\"presets\"]:
    p=e[\"preset\"]; s=[x for x in (p.get(\"snapshots\") or []) if x]
    print(p[\"name\"], \"items\", len(p[\"items\"]),
          \"snaps\", len(s), \"vals\", [len(x[\"values\"]) for x in s])
"'
```

**`vals` must equal `items` for every snapshot** — that is trap 2 in one line.

### Load and xruns

```bash
python3 ~/pipedal-probe.py                 # all presets + all snapshots
python3 ~/pipedal-probe.py --presets-only
python3 ~/pipedal-probe.py --dwell 10
```

Drives PiPedal's websocket (`ws://…:80/pipedal`, frames of
`[{"message":"loadPreset"},<id>]`), because the only other way to load a preset
is tapping the UI. Restores `selectedPreset` on exit. Selects, never edits.

> **The probe is itself a load** — it holds a websocket open (PiPedal streams VU
> data to any client) and re-reads the whole boot journal per sample. Its
> numbers are good for *comparing* presets, but any underrun rate measured
> while probing is an **upper bound**. To judge real stability: park it, close
> the browser tab, disconnect, *then* count. Measured that way the rig showed
> **0 underruns in 240 s** on its heaviest preset.
>
> Also: changing a control live sets `isModified` on the current snapshot and
> that **does** hit disk. Send `setSnapshot` afterwards — it clears the flag on
> every snapshot.

### Sanity

```bash
journalctl -u pipedald -b --no-pager | grep -iE "underrun|Audio started"
vcgencmd measure_temp; vcgencmd get_throttled     # want 0x0
```

2 underruns per service start are normal engine init. The wall of
`WebServer: asio ... Bad file descriptor` on shutdown is harmless noise.

## 8. When it breaks

| Symptom | Cause |
|---|---|
| **Total silence after a reboot or USB replug** | Stale `AudioConfig.json`. **Reapply Audio Device Settings in the UI** before debugging anything else. Cost an hour once |
| File selectors empty, no model loaded | Trap 1 — `lv2State` not written |
| A control resets when switching snapshots | Trap 2 — omitted from that snapshot |
| A plugin un-bypasses itself on snapshot switch | Trap 2 or 3 |
| An EQ/filter does nothing | Trap 5 — wrong unit, clamped to the rail |
| A snapshot switch does nothing at all | Empty slot. `ApplySnapshot` returns false on `null`, silently. `prev/nextSnapshot` skip empties; direct `snapshotN` does not |
| Preset sounds right, snapshot doesn't | Trap 4 — `pathProperties` missing from the snapshot value |
| Changes vanish | `pipedald` was running when you wrote |
| Crackling | >2 NAM instances, or a 96 kHz 4-channel reverb IR. Only **EMT 140 Medium 2** is 48 kHz/stereo and needs no resampling |
| Card number changed | Irrelevant — stored by name as `hw:U192k`. Never pin the number |

---

Related: [`pipedal-data-model.md`](./pipedal-data-model.md) ·
[`pipedal-session-handoff.md`](./pipedal-session-handoff.md) ·
[`pipedal-phase2.md`](../archive/pipedal-phase2.md) §8b
