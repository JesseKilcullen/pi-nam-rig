# pi-nam-rig

DIY Raspberry Pi guitar rig built on [PiPedal](https://github.com/rerdavies/pipedal) +
[Neural Amp Modeler](https://www.neuralampmodeler.com/), with a Raspberry Pi Pico MIDI
footswitch controller and OLED display.

6 presets × 6 snapshots, switched from a 10-footswitch box over MIDI. The OLED shows the live
preset/snapshot name and a tuner.

## Start here

| Doc | What it covers |
|---|---|
| [`pipedal-next-steps.md`](./pipedal-next-steps.md) | Current status and what's left |
| [`QUICK-REFERENCE.md`](./QUICK-REFERENCE.md) | Network, hotspot, SSH, relay service commands |
| [`pipedal-hardware-v2.md`](./pipedal-hardware-v2.md) | Footswitch box hardware design |
| [`pipedal-footswitch-build-guide.md`](./pipedal-footswitch-build-guide.md) | Build steps |

## Layout

| Folder | Contents |
|---|---|
| `pico-footswitch-v2/` | Pico firmware (CircuitPython), the Pi-side relay, and the RESET-switch settings menu (Level / EQ / Pitch Shift / Save) |
| `lv2-pitch-shift/` | Pitch-shift LV2 plugin for PiPedal (TONE3000's engine, plain C++) |
| `pi-scripts/` | Pi setup and probe scripts |
| `generator-scripts/` | Preset bank generator, plus scripts to change/compare the live bank in place |
| `presets-reference/` | Rig plan, preset tables, how-tos |
| `bank-backups/` | PiPedal bank exports |
| `wiring/` | Wiring layout and reference |
| `enclosure-templates/` | Printable drill/fold templates (SVG) |
| `enclosure-build-reference/` | Enclosure build notes |
| `images/` | Photos and renders |
| `archive/` | Superseded plans, kept for reference |
