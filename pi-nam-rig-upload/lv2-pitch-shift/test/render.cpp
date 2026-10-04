// Renders a deterministic guitar-like test signal through the pitch shifter
// under a scripted parameter schedule and writes the result as raw float32.
//
// Built twice by compare.sh: against the original JUCE-based PitchShift
// (-DUSE_JUCE) and against the plain-C++ port, so the two outputs can be
// compared sample by sample.
//
//   render <scenario 0-5> <channels 1|2> <block size> <out.raw>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

#ifdef USE_JUCE
#include "PitchShift.h"
static void processBlock(PitchShift& ps, float* const* ch, int nch, int n) {
  juce::AudioBuffer<float> buffer(ch, nch, n);
  ps.process(buffer);
}
#else
#include "pitch_shift.h"
static void processBlock(PitchShift& ps, float* const* ch, int nch, int n) { ps.process(ch, nch, n); }
#endif

namespace {
constexpr double kRate = 48000.0;
constexpr double kSeconds = 12.0;

uint32_t rngState = 12345;
float noise() {
  rngState = rngState * 1664525u + 1013904223u;
  return static_cast<float>((rngState >> 8) & 0xFFFF) / 32768.0f - 1.0f;
}

// A plucked-string-ish note: a few decaying harmonics plus a short pick burst.
void addNote(std::vector<float>& x, double startSec, double hz, float level) {
  const auto start = static_cast<size_t>(startSec * kRate);
  for (size_t i = start; i < x.size(); ++i) {
    const double t = static_cast<double>(i - start) / kRate;
    if (t > 1.6) break;
    double v = 0.0;
    for (int h = 1; h <= 6; ++h) v += std::sin(2.0 * M_PI * hz * h * t) * std::exp(-t * (2.0 + h * 1.5)) / h;
    if (t < 0.006) v += 0.5 * noise() * (1.0 - t / 0.006);
    x[i] += level * static_cast<float>(v);
  }
}

std::vector<float> makeSignal() {
  std::vector<float> x(static_cast<size_t>(kSeconds * kRate), 0.0f);
  addNote(x, 0.2, 82.41, 0.5f);    // E2
  addNote(x, 1.5, 110.0, 0.5f);    // A2
  addNote(x, 2.8, 146.83, 0.5f);   // D3
  addNote(x, 4.2, 82.41, 0.3f);    // E power chord
  addNote(x, 4.2, 123.47, 0.3f);
  addNote(x, 4.2, 164.81, 0.3f);
  addNote(x, 6.0, 41.20, 0.6f);    // low E1 (bass)
  addNote(x, 7.5, 329.63, 0.4f);   // E4
  addNote(x, 9.0, 146.83, 0.3f);   // dissonant-ish chord
  addNote(x, 9.0, 220.0, 0.3f);
  addNote(x, 9.0, 349.23, 0.3f);
  return x;
}

struct Settings {
  bool enabled;
  PitchShift::Params params;
};

PitchShift::Window win(int ms) {
  return ms == 20 ? PitchShift::Window::ms20
         : ms == 30 ? PitchShift::Window::ms30
         : ms == 40 ? PitchShift::Window::ms40
                    : PitchShift::Window::ms60;
}

Settings settingsAt(int scenario, double t) {
  Settings s{true, {}};
  switch (scenario) {
    case 0: s.params = {-2.0f, 0.0f, win(30)}; break;
    case 1: s.params = {7.0f, 4000.0f, win(20)}; break;
    case 2: s.params = {-12.0f, 1500.0f, win(60)}; break;
    case 3: s.params = {static_cast<float>(5.0 * std::sin(2.0 * M_PI * t / 4.0)), 0.0f, win(40)}; break;
    case 4:
      s.enabled = t >= 3.0 && t < 7.0;
      s.params = {3.0f, 0.0f, win(30)};
      break;
    case 5: {
      const int w[4] = {20, 30, 40, 60};
      s.params = {t < 6.0 ? -5.0f : 24.0f, t < 9.0 ? 0.0f : 3000.0f, win(w[static_cast<int>(t / 2.0) % 4])};
      break;
    }
  }
  return s;
}
}  // namespace

int main(int argc, char** argv) {
  if (argc < 5) {
    std::fprintf(stderr, "usage: render <scenario 0-5> <channels 1|2> <block> <out.raw>\n");
    return 2;
  }
  const int scenario = std::atoi(argv[1]);
  const int channels = std::atoi(argv[2]);
  const int block = std::atoi(argv[3]);

  const std::vector<float> mono = makeSignal();
  std::vector<std::vector<float>> data(static_cast<size_t>(channels), mono);
  if (channels == 2)
    for (size_t i = 0; i < mono.size(); ++i) data[1][i] = 0.8f * mono[i] + 0.05f * (i > 7 ? mono[i - 7] : 0.0f);

  PitchShift ps;
  ps.prepare(kRate, block);

  const size_t total = mono.size();
  for (size_t pos = 0; pos < total; pos += static_cast<size_t>(block)) {
    const int n = static_cast<int>(std::min<size_t>(static_cast<size_t>(block), total - pos));
    const Settings s = settingsAt(scenario, static_cast<double>(pos) / kRate);
    ps.setEnabled(s.enabled);
    if (ps.isRunning()) {
      ps.setParams(s.params);
      float* ptrs[2] = {data[0].data() + pos, channels == 2 ? data[1].data() + pos : nullptr};
      processBlock(ps, ptrs, channels, n);
    }
  }

  FILE* f = std::fopen(argv[4], "wb");
  if (!f) return 1;
  for (size_t i = 0; i < total; ++i)
    for (int c = 0; c < channels; ++c) std::fwrite(&data[static_cast<size_t>(c)][i], sizeof(float), 1, f);
  std::fclose(f);
  return 0;
}
