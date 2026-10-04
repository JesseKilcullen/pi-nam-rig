// Loads the built LV2 binary the way a host does (dlopen + lv2_descriptor),
// runs a sine through it and checks the output pitch and reported latency.
//
//   g++ -O2 -std=c++17 -I/usr/include test/host_smoke.cpp -ldl -o host_smoke
//   ./host_smoke PitchShiftTone3000.lv2/pitch_shift.so
#include <dlfcn.h>
#include <lv2/core/lv2.h>

#include <cmath>
#include <cstdio>
#include <vector>

namespace {
int failures = 0;

void check(bool ok, const char* what, double value) {
  std::printf("%s  %s (%.2f)\n", ok ? "ok  " : "FAIL", what, value);
  if (!ok) ++failures;
}

double risingCrossingsPerSecond(const std::vector<float>& x, double rate, double t0, double t1) {
  int c = 0;
  for (size_t i = static_cast<size_t>(t0 * rate) + 1; i < static_cast<size_t>(t1 * rate); ++i)
    if (x[i - 1] <= 0.0f && x[i] > 0.0f) ++c;
  return c / (t1 - t0);
}
}  // namespace

int main(int argc, char** argv) {
  if (argc < 2) return 2;
  void* lib = dlopen(argv[1], RTLD_NOW);
  if (!lib) {
    std::printf("FAIL dlopen: %s\n", dlerror());
    return 1;
  }
  auto getDescriptor = reinterpret_cast<const LV2_Descriptor* (*)(uint32_t)>(dlsym(lib, "lv2_descriptor"));
  if (!getDescriptor || !getDescriptor(0) || getDescriptor(1)) {
    std::printf("FAIL lv2_descriptor\n");
    return 1;
  }
  const LV2_Descriptor* d = getDescriptor(0);
  std::printf("plugin %s\n", d->URI);

  const double rate = 48000.0;
  const int n = 128;
  const int seconds = 3;
  const double hz = 110.0;

  struct Case {
    const char* name;
    float semitones;
    float power;
    double expectHz;
    double expectLatency;
  } cases[] = {
      {"+12 semitones", 12.0f, 1.0f, hz * 2.0, 16.0 * 48.0},  // 30 ms window: (2+30)/2 = 16 ms
      {"-5 semitones", -5.0f, 1.0f, hz * std::pow(2.0, -5.0 / 12.0), 16.0 * 48.0},
      {"power off (passthrough)", 7.0f, 0.0f, hz, 0.0},
  };

  for (const Case& c : cases) {
    LV2_Handle h = d->instantiate(d, rate, "", nullptr);
    if (!h) {
      std::printf("FAIL instantiate\n");
      return 1;
    }
    std::vector<float> in(static_cast<size_t>(rate * seconds)), out(in.size());
    for (size_t i = 0; i < in.size(); ++i)
      in[i] = 0.5f * static_cast<float>(std::sin(2.0 * M_PI * hz * static_cast<double>(i) / rate));

    float semitones = c.semitones, step = 1.0f, tonality = 20000.0f, window = 1.0f, power = c.power, latency = -1.0f;
    float* ctl[] = {nullptr, nullptr, &semitones, &step, &tonality, &window, &power, &latency};
    for (uint32_t p = 2; p < 8; ++p) d->connect_port(h, p, ctl[p]);
    if (d->activate) d->activate(h);
    for (size_t pos = 0; pos + n <= in.size(); pos += n) {
      d->connect_port(h, 0, in.data() + pos);
      d->connect_port(h, 1, out.data() + pos);
      d->run(h, n);
    }
    if (d->deactivate) d->deactivate(h);
    d->cleanup(h);

    std::printf("-- %s\n", c.name);
    const double measured = risingCrossingsPerSecond(out, rate, 1.5, 2.9);
    check(std::fabs(measured - c.expectHz) < c.expectHz * 0.04, "output pitch (Hz)", measured);
    check(std::fabs(latency - c.expectLatency) < 1.0, "reported latency (samples)", latency);
  }
  std::printf(failures ? "\n%d FAILED\n" : "\nall ok\n", failures);
  return failures ? 1 : 0;
}
