#!/usr/bin/env bash
# Checks the plain-C++ port against TONE3000's original JUCE-based pitch
# shifter: renders the same test signal through both under several parameter
# schedules and reports the largest sample difference.
#
#   JUCE_DIR=~/build/JUCE TONE3000_DIR=~/build/tone3000-plugin ./compare.sh
#
# JUCE_DIR      a JUCE checkout (9.0.3, what TONE3000 pins)
# TONE3000_DIR  a checkout of https://github.com/tone-3000/tone3000-plugin
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
: "${JUCE_DIR:?set JUCE_DIR}" "${TONE3000_DIR:?set TONE3000_DIR}"
out="${OUT_DIR:-/tmp/pitch-shift-compare}"
mkdir -p "$out"

echo "== building port"
g++ -O2 -std=c++17 -I"$here/.." "$here/render.cpp" "$here/../pitch_shift.cpp" -o "$out/render_port"

echo "== building original (JUCE)"
juce_flags="-DJUCE_GLOBAL_MODULE_SETTINGS_INCLUDED=1 -DJUCE_STANDALONE_APPLICATION=1 -DJUCE_USE_CURL=0 \
  -DJUCE_WEB_BROWSER=0 -DJUCE_MODAL_LOOPS_PERMITTED=0 -DNDEBUG \
  -DJUCE_USE_FLAC=0 -DJUCE_USE_OGGVORBIS=0 -DJUCE_USE_OPUS=0 -DJUCE_USE_MP3AUDIOFORMAT=0 -DJUCE_USE_LAME_AUDIO_FORMAT=0 \
  -DJUCE_USE_WINDOWS_MEDIA_FORMAT=0"
juce_inc="-I$JUCE_DIR/modules -I$TONE3000_DIR/plugin/include"
for m in juce_core juce_audio_basics juce_audio_formats juce_dsp; do
  if [ ! -f "$out/$m.o" ]; then
    g++ -O2 -std=c++20 $juce_flags $juce_inc -c "$JUCE_DIR/modules/$m/$m.cpp" -o "$out/$m.o"
  fi
done
# JUCE's build-date symbols (normally compiled in by its CMake helpers)
if [ ! -f "$out/juce_compilation_time.o" ]; then
  g++ -O2 -std=c++20 $juce_flags $juce_inc -c "$JUCE_DIR/modules/juce_core/juce_core_CompilationTime.cpp" -o "$out/juce_compilation_time.o"
fi
g++ -O2 -std=c++20 -DUSE_JUCE $juce_flags $juce_inc "$here/render.cpp" \
  "$TONE3000_DIR/plugin/src/PitchShift.cpp" "$out"/juce_core.o "$out"/juce_audio_basics.o "$out"/juce_audio_formats.o "$out"/juce_dsp.o "$out"/juce_compilation_time.o \
  -lpthread -ldl -l:libz.so.1 -o "$out/render_juce"

status=0
for scenario in 0 1 2 3 4 5; do
  for channels in 1 2; do
    for block in 64 480; do
      tag="s${scenario}_c${channels}_b${block}"
      "$out/render_juce" $scenario $channels $block "$out/$tag.juce.raw"
      "$out/render_port" $scenario $channels $block "$out/$tag.port.raw"
      printf "%-14s " "$tag"
      python3 "$here/compare.py" "$out/$tag.juce.raw" "$out/$tag.port.raw" || status=1
    done
  done
done
exit $status
