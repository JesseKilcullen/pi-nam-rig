# PiPedal Data Model — Banks, Presets, Snapshots

How the three levels nest, what each one can change, and which switches are
seamless. Verified by reading the live files on the Pi, 2026-09-04.

Related: [`pipedal-nam-rig-plan.md`](./pipedal-nam-rig-plan.md) ·
[`pipedal-phase2.md`](../archive/pipedal-phase2.md) §8b (editing these files by script)

---

## 1. The three levels in one line each

| Level | What it is | Switching cost |
|---|---|---|
| **Bank** | A folder of presets. One active at a time | gap |
| **Preset** | *The rig* — which plugins exist, in what order | **gap** (graph rebuild) |
| **Snapshot** | *A photograph of every control on that rig* | **seamless** |

---

## 2. Multiplicity

```
  index.banks                            exactly 1
  { selectedBank, nextInstanceId, entries[] }
       │
       │  1 : 0..N          ← 2 banks on your Pi
       ▼
  BANK                      one file per bank
  <Bank+Name>.bank
  { name, selectedPreset, presets[] }
       │
       │  1 : 0..N          ← 17 in "Default Bank"
       ▼
  PRESET                    = the rig
  switching → GRAPH REBUILD → audible gap
  { name, in/out_volume_db,
    selectedSnapshot, items[], snapshots[] }
       │
       ├───────────────────────┐
       │                       │
       │ 1 : 1..N              │ 1 : 0..6
       │ ordered chain         │ fixed array, holes legal
       ▼                       ▼
  ITEM                    SNAPSHOT
  (a plugin)              = photo of every control
  { instanceId,           switching → no rebuild → SEAMLESS
    uri,                  { name, color, isModified,
    isEnabled,              values[] }
    controlValues[],           │
    pathProperties{} }         │ 1 : 0..N   one per ITEM
       ▲                       ▼
       │                  SNAPSHOT VALUE
       │                  { instanceId,      ← FK
       │                    isEnabled,
       │                    controlValues[],
       │                    pathProperties{},
       │                    lv2State }
       │                       │
       └───────────────────────┘
         value.instanceId  →  item.instanceId
```

| Relationship | Multiplicity | Your rig |
|---|---|---|
| install → bank | 1 : 0..N | 2 banks |
| bank → preset | 1 : 0..N | 17 in Default Bank |
| preset → item (plugin) | 1 : 1..N, **ordered** | 5 in preset `New` |
| preset → snapshot | 1 : **0..6**, fixed array | 3 used, 3 empty |
| snapshot → value | 1 : 0..N, **one per item** | 4 values |

---

## 3. The one rule, and why it exists

**A snapshot cannot add, remove or re-order a plugin.**

That isn't a UI limitation, it's structural: `SNAPSHOT VALUE.instanceId` is a
foreign key into `ITEM.instanceId`. A snapshot can only *address* plugins the
preset already contains. It's a **diff against a fixed graph**, not a graph of
its own.

Consequence for building: **put the whole chain in the preset up front**, even
where a snapshot leaves half of it bypassed. To add a reverb to one snapshot you
add it to the *preset*, then re-save every snapshot.

> ⚠️ **"Diff" describes what a snapshot can *address*, not how it is stored.**
> A snapshot is applied as a **complete replacement**, not a patch: any control
> it omits is reset to the plugin's **TTL default**, and any item it has no
> value for is un-bypassed and fully defaulted. See
> `pipedal-session-handoff.md` §5.8 — this is the single easiest way to break a
> preset silently.

### What a snapshot does store, per plugin

| Field | Example from your rig |
|---|---|
| `isEnabled` | bypass on/off |
| `controlValues` | `inputGain: -6`, `gate: -120`, `modelSize: 0` |
| `pathProperties` | **the NAM capture file** — what your 3 snapshots change |
| `lv2State` | plugin internal state |

---

## 4. Seamless vs gap

| Change | Cost |
|---|---|
| Snapshot → snapshot, bypass or knobs | **seamless** |
| Snapshot → snapshot, NAM `modelFile` | **seamless on this rig** (Phase 1 result) |
| Preset → preset | **gap** — graph rebuild |
| Bank → bank | **gap** |

Snapshots are the mid-song switch. Presets are the between-songs switch.

---

## 5. Your actual tree

*As of 2026-09-05. The Phase-1 scratch presets (`New`, `New (2)`, `New (3)`
and the imported factory ones) are gone — the generator replaces every preset
in the bank, so the tree is exactly what `build-kraken-presets.py` says.*

```
index.banks
 │
 ├── BANK "Factory Presets"   (id 1)   untouched
 │
 └── BANK "Default Bank"      (id 2)   ◄── selected
      │                                     (internal name still reads
      │                                      "Factory Presets" — cosmetic, §6)
      ├── PRESET "1 Clean"       8 plugins   4 snapshots, slots 5-6 empty
      ├── PRESET "2 Ambient"     9 plugins   4 snapshots
      ├── PRESET "3 Crunch"      9 plugins   4 snapshots
      ├── PRESET "4 HG Rhythm"   6 plugins   4 snapshots
      ├── PRESET "5 HG Lead"     8 plugins   4 snapshots
      └── PRESET "6 Loathe"      7 plugins   4 snapshots
           │
           │  CHAIN — fixed, identical in every snapshot:
           │  [tuner] → [gate] → [NAM: HM-2] → [NAM: 6505]
           │      → [cab-ir] → [param EQ] → [conv reverb]
           │
           ├── snapshot 1 "Chainsaw"          HM-2 on,  Chainsaw.nam
           ├── snapshot 2 "Chug"              HM-2 off (raw 6505)
           ├── snapshot 3 "Chainsaw 0 Gain"   HM-2 on,  Chainsaw 0 Gain.nam
           ├── snapshot 4 "Wash"              longer reverb tail
           └── slots 5,6 empty
```

Every snapshot carries a value for **every** item in its preset — 7 items means
7 values. That is not tidiness, it is required: see §3's warning.

Two things the *previous* tree proved rather than asserted, still true:

- A preset was seen filling slots **1, 2, 3, 5, 6 with slot 4 empty** — so
  snapshots really are a fixed 6-slot array with nulls, not a list.
- Factory presets have `snapshots: []` — zero snapshots is valid.

---

## 6. On disk

```
/var/pipedal/presets/index.banks         bank list + selectedBank
/var/pipedal/presets/<Bank+Name>.bank    everything else
/etc/pipedal/config                      audio + MIDI setup
```

All plain JSON. The NAM capture is a **JSON string nested inside** a JSON value:

```json
"pathProperties": {
  "http://two-play.com/plugins/toob-nam#modelFile":
    "{\"otype_\": \"Path\",\"value\": \"NeuralAmpModels/....nam\"}"
}
```

Parse the outer object, parse that string, edit `value`, re-serialise both
levels. Same shape for `toob-cab-ir#impulseFile` and the reverb's `impulseFile`.

> ⚠️ **Stop `pipedald` before editing or your changes vanish** — it holds this
> state in memory and rewrites the files on any change. Files are owned by
> `pipedal_d:pipedal_d`; preserve ownership. `python3` is on the Pi, not on the
> Windows laptop. See `pipedal-phase2.md` §8b.

**Cosmetic oddity:** `Default+Bank.bank` has an internal `name` field of
`"Factory Presets"` — it was copied from the factory bank and never renamed. The
`index.banks` entry is what the UI shows, so this is harmless.

---

## 7. Naming trap — fix before Phase 3

§5 of the main plan draws presets *named* **"Bank A", "Bank B", "Bank C"** inside
a bank called "Live Set". That collides with the real `bank` level above.

Your footswitches labelled "bank up / bank down" almost certainly want
**next/previous _preset_** bindings, not next/previous bank. Rename the presets
to something like Clean / Rhythm / Lead and the confusion disappears.
