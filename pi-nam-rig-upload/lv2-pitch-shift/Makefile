# Builds the pitch-shift LV2 bundle. Plain C++, no JUCE.
#   make            build PitchShiftTone3000.lv2/pitch_shift.so
#   sudo make install   copy the bundle to /usr/lib/lv2 (PiPedal scans it)
CXX      ?= g++
CXXFLAGS ?= -O2 -std=c++17 -fPIC -fvisibility=hidden -Wall -Wextra
BUNDLE   := PitchShiftTone3000.lv2
LV2DIR   ?= /usr/lib/lv2

$(BUNDLE)/pitch_shift.so: lv2_pitch_shift.cpp pitch_shift.cpp pitch_shift.h dsp_helpers.h
	$(CXX) $(CXXFLAGS) -shared lv2_pitch_shift.cpp pitch_shift.cpp -o $@

install: $(BUNDLE)/pitch_shift.so
	install -d $(LV2DIR)/$(BUNDLE)
	install -m 644 $(BUNDLE)/manifest.ttl $(BUNDLE)/pitch_shift.ttl $(LV2DIR)/$(BUNDLE)/
	install -m 755 $(BUNDLE)/pitch_shift.so $(LV2DIR)/$(BUNDLE)/

clean:
	rm -f $(BUNDLE)/pitch_shift.so

.PHONY: install clean
