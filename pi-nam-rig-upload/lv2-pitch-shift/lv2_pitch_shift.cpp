// LV2 wrapper around the TONE3000 pitch shifter (see pitch_shift.h).
//
// Every control is an ordinary LV2 control port, which is what PiPedal needs
// to draw knobs and to bind MIDI CCs. (TONE3000's own LV2 build exposes its
// controls as patch parameters, and PiPedal skips plugins that have those.)
//
// The control handling mirrors TONE3000's Processor: the engine only runs
// while the power control is on, STEP rounds the shift to whole semitones,
// the top of the tonality range means off, and the reported latency is the
// engine's only while it is powered.
#include <lv2/core/lv2.h>

#include <cmath>
#include <cstdint>
#include <cstring>
#include <new>

#include "pitch_shift.h"

#define PITCH_SHIFT_URI "https://github.com/JesseKilcullen/pi-nam-rig/lv2-pitch-shift#mono"

namespace {

enum Port : uint32_t {
  kIn,
  kOut,
  kSemitones,
  kStep,
  kTonality,
  kWindow,
  kPower,
  kLatency,
  kPortCount
};

constexpr int kPrepareBlock = 1024;

struct Plugin {
  float* ports[kPortCount] = {};
  double sampleRate = 48000.0;
  PitchShift engine;
};

LV2_Handle instantiate(const LV2_Descriptor*, double sampleRate, const char*, const LV2_Feature* const*) {
  auto* p = new (std::nothrow) Plugin;
  if (!p) return nullptr;
  p->sampleRate = sampleRate;
  p->engine.prepare(sampleRate, kPrepareBlock);
  return p;
}

void connectPort(LV2_Handle handle, uint32_t port, void* data) {
  if (port < kPortCount) static_cast<Plugin*>(handle)->ports[port] = static_cast<float*>(data);
}

void activate(LV2_Handle handle) {
  auto* p = static_cast<Plugin*>(handle);
  p->engine.prepare(p->sampleRate, kPrepareBlock);  // clears the rings
}

void run(LV2_Handle handle, uint32_t sampleCount) {
  auto* p = static_cast<Plugin*>(handle);
  const float* in = p->ports[kIn];
  float* out = p->ports[kOut];
  if (!in || !out) return;
  const int n = static_cast<int>(sampleCount);
  if (in != out) std::memcpy(out, in, sizeof(float) * sampleCount);

  const bool power = *p->ports[kPower] >= 0.5f;
  const int windowIndex = static_cast<int>(std::lround(*p->ports[kWindow]));
  const PitchShift::Window window = PitchShift::windowFromIndex(windowIndex);

  p->engine.setEnabled(power);
  if (p->engine.isRunning()) {
    const float range = static_cast<float>(PitchShift::kSemitoneRange);
    const float semitones = ps::jlimit(-range, range, *p->ports[kSemitones]);
    const float tonality = *p->ports[kTonality];

    PitchShift::Params params;
    params.semitones = *p->ports[kStep] >= 0.5f ? std::round(semitones) : semitones;
    params.tonalityHz = tonality < PitchShift::kTonalityOffHz ? tonality : 0.0f;
    params.window = window;
    p->engine.setParams(params);

    float* channels[1] = {out};
    p->engine.process(channels, 1, n);
  }

  if (p->ports[kLatency])
    *p->ports[kLatency] = power ? static_cast<float>(PitchShift::latencySamples(window, p->sampleRate)) : 0.0f;
}

void deactivate(LV2_Handle) {}

void cleanup(LV2_Handle handle) { delete static_cast<Plugin*>(handle); }

const void* extensionData(const char*) { return nullptr; }

const LV2_Descriptor kDescriptor = {PITCH_SHIFT_URI, instantiate, connectPort, activate,
                                    run,             deactivate,  cleanup,     extensionData};

}  // namespace

extern "C" LV2_SYMBOL_EXPORT const LV2_Descriptor* lv2_descriptor(uint32_t index) {
  return index == 0 ? &kDescriptor : nullptr;
}
