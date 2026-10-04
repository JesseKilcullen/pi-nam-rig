# lv2-pitch-shift

A mono pitch-shift LV2 plugin for PiPedal, built from the pitch shifter in
[TONE3000's plugin](https://github.com/tone-3000/tone3000-plugin) (MIT).

TONE3000's own LV2 build exposes its controls as LV2 *patch parameters*, and PiPedal skips
plugins like that ("skipped. (Has unsupported patch parameters)"), so it never appears in the
plugin list. This folder is just the shifter engine, ported from JUCE to plain C++ and wrapped
with ordinary control ports.

| Port | Range | Notes |
|---|---|---|
| Pitch | -24 to +24 semitones | |
| Step | on/off | on: snap to whole semitones; off: smooth whammy-style sweep |
| Tonality | 1 kHz to 20 kHz (log) | frequency above which the dry signal bypasses the shifter; 20 kHz = off |
| Buffer | 20 / 30 / 40 / 60 ms | 20 ms suits guitar; 30 ms (default) covers bass |
| Power | on/off | when off the signal passes through untouched and latency is 0 |
| Latency | output | reported to the host: (2 ms + buffer) / 2 while powered |

Put it **first** in the chain (after the noise gate, before the amp): it works best on a clean
instrument signal.

## Files

- `pitch_shift.h/.cpp`: the engine. `diff` it against `plugin/src/PitchShift.cpp` upstream; only the
  JUCE types were swapped out.
- `dsp_helpers.h`: plain-C++ versions of the JUCE pieces it used (linear ramp, Linkwitz-Riley crossover, `jlimit` etc.).
- `lv2_pitch_shift.cpp`, `PitchShiftTone3000.lv2/*.ttl`: the LV2 wrapper and metadata.

## Build and install (on the Pi)

```bash
make                                  # needs g++ and the lv2 headers (/usr/include/lv2)
sudo make install                     # copies the bundle to /usr/lib/lv2
sudo systemctl restart pipedald       # PiPedal rescans plugins at startup
```

## Tests

- `test/compare.sh`: renders test audio through TONE3000's original JUCE shifter and this port
  under six parameter schedules (mono/stereo, two block sizes) and compares sample by sample.
  Needs a JUCE 9.0.3 checkout and a tone3000-plugin checkout (see the script header). Result at
  the time of writing: max difference 0 in all 24 runs (bit-identical).
- `test/host_smoke.cpp`: loads the built `.so` like a host and checks output pitch and latency.

## License

MIT, same as TONE3000's plugin. The shifter engine is Copyright (c) 2026 TONE3000 (originating from
a contribution by Vivek Radhakrishna, tone3000-plugin PR #133); see `LICENSE`.
