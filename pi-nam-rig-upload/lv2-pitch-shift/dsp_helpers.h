#pragma once
// Plain-C++ stand-ins for the handful of JUCE helpers the TONE3000 pitch
// shifter uses (jlimit/jmin/roundToInt, a linear parameter ramp and a
// 4th-order Linkwitz-Riley crossover). Written to behave identically to the
// JUCE versions (test/compare.sh checks the port against the original), so
// the shifter's tuned behaviour carries over unchanged.
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <vector>

namespace ps {

constexpr double kPi = 3.14159265358979323846;

template <typename T>
constexpr T jlimit(T lower, T upper, T value) {
  return value < lower ? lower : (upper < value ? upper : value);
}

template <typename T>
constexpr T jmin(T a, T b) {
  return b < a ? b : a;
}

inline int roundToInt(double x) { return static_cast<int>(std::floor(x + 0.5)); }

// Exact comparison on purpose (callers detect "any change at all").
inline bool exactlyEqual(float a, float b) { return a == b; }

// juce::approximatelyEqual for floats, used by the ramp to skip a no-op target.
inline bool approximatelyEqual(float a, float b) {
  if (!(std::isfinite(a) && std::isfinite(b))) return exactlyEqual(a, b);
  const float diff = std::abs(a - b);
  return diff <= std::numeric_limits<float>::min() ||
         diff <= std::numeric_limits<float>::epsilon() * std::max(std::abs(a), std::abs(b));
}

// Linear ramp to a target over a fixed number of samples
// (juce::LinearSmoothedValue<float>).
class LinearRamp {
public:
  void reset(double sampleRate, double rampSeconds) {
    stepsToTarget = static_cast<int>(std::floor(rampSeconds * sampleRate));
    setCurrentAndTargetValue(target);
  }

  void setCurrentAndTargetValue(float v) {
    target = current = v;
    countdown = 0;
  }

  void setTargetValue(float v) {
    if (approximatelyEqual(v, target)) return;
    if (stepsToTarget <= 0) {
      setCurrentAndTargetValue(v);
      return;
    }
    target = v;
    countdown = stepsToTarget;
    step = (target - current) / static_cast<float>(countdown);
  }

  float getNextValue() {
    if (!isSmoothing()) return target;
    --countdown;
    if (isSmoothing())
      current += step;
    else
      current = target;
    return current;
  }

  bool isSmoothing() const { return countdown > 0; }

private:
  float current = 0.0f, target = 0.0f, step = 0.0f;
  int countdown = 0, stepsToTarget = 0;
};

// 4th-order Linkwitz-Riley low/high-pass: two cascaded 2nd-order
// state-variable stages (juce::dsp::LinkwitzRileyFilter<float>, lowpass and
// highpass types only).
class LinkwitzRiley4 {
public:
  enum class Type { lowpass, highpass };

  LinkwitzRiley4() { update(); }

  void setType(Type t) { type = t; }

  void setCutoffFrequency(float hz) {
    cutoff = hz;
    update();
  }

  void prepare(double newSampleRate, int numChannels) {
    sampleRate = newSampleRate;
    update();
    const auto n = static_cast<size_t>(numChannels);
    s1.assign(n, 0.0f);
    s2.assign(n, 0.0f);
    s3.assign(n, 0.0f);
    s4.assign(n, 0.0f);
  }

  float processSample(int channel, float x) {
    const auto c = static_cast<size_t>(channel);
    auto yH = (x - (R2 + g) * s1[c] - s2[c]) * h;
    auto yB = g * yH + s1[c];
    s1[c] = g * yH + yB;
    auto yL = g * yB + s2[c];
    s2[c] = g * yB + yL;

    auto yH2 = ((type == Type::lowpass ? yL : yH) - (R2 + g) * s3[c] - s4[c]) * h;
    auto yB2 = g * yH2 + s3[c];
    s3[c] = g * yH2 + yB2;
    auto yL2 = g * yB2 + s4[c];
    s4[c] = g * yB2 + yL2;

    return type == Type::lowpass ? yL2 : yH2;
  }

private:
  void update() {
    g = static_cast<float>(std::tan(kPi * cutoff / sampleRate));
    R2 = static_cast<float>(std::sqrt(2.0));
    h = static_cast<float>(1.0 / (1.0 + R2 * g + g * g));
  }

  float g = 0.0f, R2 = 0.0f, h = 0.0f;
  double sampleRate = 44100.0;
  float cutoff = 2000.0f;
  Type type = Type::lowpass;
  std::vector<float> s1, s2, s3, s4;
};

}  // namespace ps
