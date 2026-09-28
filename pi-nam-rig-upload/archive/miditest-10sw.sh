#!/usr/bin/env bash
# miditest-10sw.sh - exercise the 10-switch / 2-page footswitch layout
#                    with NO Pico and NO switches.
#
# This sends exactly the bytes the Pico will send, so if this works the
# hardware will too. Run it on the Pi, watch the PiPedal UI on your phone.
#
# Prerequisites:
#   sudo ./pipedal-setup.sh midi        # loads snd-virmidi, wires port 0 -> 1
#   PiPedal -> Settings -> MIDI -> input = "Virtual Raw MIDI <card>-1"
#                                  channel = omni (-1)
#   PiPedal -> Settings -> System MIDI Bindings:
#         Snapshot 1..6 = CC 20..25
#   PiPedal -> Settings -> MIDI Bindings (per-plugin, current preset):
#         TooB Tuner MUTE = CC 26, "Toggle on any value"
#
# Usage:
#   ./miditest-10sw.sh              # walk the whole layout
#   ./miditest-10sw.sh presets      # just the preset row, both pages
#   ./miditest-10sw.sh snapshots    # just the snapshot row, both pages
#   ./miditest-10sw.sh reset        # the RESET switch
#   ./miditest-10sw.sh mute         # the MUTE switch, 3 presses
#   ./miditest-10sw.sh defer        # the deferred-message trap, on purpose
#   ./miditest-10sw.sh dead         # snapshots 5-6 on a 4-snapshot preset
#
# Program Change needs no binding - PiPedal handles 0xC0 directly and
# indexes presets 0-based within the selected bank.
#
# NOTE: nothing here ever sends CC 0. B0 00 vv is MIDI Bank Select and
# would switch you into Factory Presets. Don't add it.

set -uo pipefail

GAP="${GAP:-2}"          # seconds between messages; GAP=4 ./miditest-10sw.sh
RESET_GAP="${RESET_GAP:-0.6}"

card=$(amidi -l 2>/dev/null | awk '/Virtual Raw MIDI/ {sub(/hw:/,"",$2); split($2,a,","); print a[1]; exit}')
if [ -z "$card" ]; then
    echo "!! no virmidi ports - run 'sudo ./pipedal-setup.sh midi' first" >&2
    echo "   (or plug in any USB MIDI keyboard and set PORT= by hand)" >&2
    exit 1
fi
PORT="${PORT:-hw:${card},0}"
echo "sending on $PORT   (PiPedal must be listening on hw:${card},1)"
echo

# send <label> <hex bytes>
send() {
    printf '  %-34s %s\n' "$1" "$2"
    amidi -p "$PORT" -S "$2" || echo "     !! amidi failed" >&2
    sleep "$GAP"
}

hex2() { printf 'B0 %02X 7F' "$1"; }   # CC <n> value 127

# ---- preset row -----------------------------------------------------------
# page 0 -> PC 0,1,2   page 1 -> PC 3,4,5
do_presets() {
    echo "PRESET ROW - page 0 (presets 1,2,3)"
    send "P1  -> 1 Clean"        "C0 00"
    send "P2  -> 2 Ambient"      "C0 01"
    send "P3  -> 3 Crunch"       "C0 02"
    echo "PRESET ROW - page 1 (presets 4,5,6)   [PAGE UP sends no MIDI]"
    send "P1  -> 4 HG Rhythm"    "C0 03"
    send "P2  -> 5 HG Lead"      "C0 04"
    send "P3  -> 6 Massive"      "C0 05"
    echo "  expect: audible gap on every one of these (graph rebuild)"
    echo "  expect: presets 4 and 6 crackle - that is the unfixed output-level"
    echo "          issue from handoff 6.10, NOT a MIDI fault"
    echo
}

# ---- snapshot row ---------------------------------------------------------
# page 0 -> CC 20,21,22   page 1 -> CC 23,24,25
do_snapshots() {
    echo "SNAPSHOT ROW - page 0 (snapshots 1,2,3)"
    send "S1  -> snapshot 1"     "$(hex2 20)"
    send "S2  -> snapshot 2"     "$(hex2 21)"
    send "S3  -> snapshot 3"     "$(hex2 22)"
    echo "SNAPSHOT ROW - page 1 (snapshots 4,5,6)"
    send "S1  -> snapshot 4"     "$(hex2 23)"
    send "S2  -> snapshot 5"     "$(hex2 24)"
    send "S3  -> snapshot 6"     "$(hex2 25)"
    echo "  expect: seamless, no gap, reverb/delay tails survive"
    echo
}

# ---- RESET ----------------------------------------------------------------
# PC 0 then CC 20, with a gap. The gap is deliberate - see 'defer' below.
do_reset() {
    echo "RESET - preset 1 + snapshot 1, page 0"
    printf '  %-34s %s\n' "PC 0  -> 1 Clean" "C0 00"
    amidi -p "$PORT" -S "C0 00"
    sleep "$RESET_GAP"
    printf '  %-34s %s\n' "CC 20 -> snapshot 1 (after ${RESET_GAP}s)" "$(hex2 20)"
    amidi -p "$PORT" -S "$(hex2 20)"
    sleep "$GAP"
    echo "  expect: lands on preset 1, snapshot 1"
    echo "  if the snapshot half does not land, raise RESET_GAP and retry:"
    echo "      RESET_GAP=1.2 ./miditest-10sw.sh reset"
    echo "  then set RESET_GAP_S in code.py to whatever worked"
    echo
}

# ---- the deferral trap ----------------------------------------------------
# Sends PC + CC back to back with no gap, which is what NOT to do.
# PiPedal buffers MIDI arriving during a program change; the replay path in
# AudioHost.cpp writes one header byte but reads two, so what comes back out
# looks mangled. This case exists to confirm that on your build before
# trusting any zero-gap sequence.
do_defer() {
    echo "DEFERRAL TRAP - PC 5 + CC 23 back to back, no gap (the bad pattern)"
    amidi -p "$PORT" -S "C0 05"
    amidi -p "$PORT" -S "$(hex2 23)"
    sleep "$GAP"
    echo "  if you land on preset 6 snapshot 4, the deferral path works here."
    echo "  if you land on preset 6 with the WRONG snapshot, or nothing"
    echo "  happens, the buffer is mangling it - keep the gap in RESET and"
    echo "  never stomp two switches across a preset change."
    echo
}

# ---- dead switches --------------------------------------------------------
# Presets 2,3,4,5 have only 4 snapshots. Snapshot 5/6 select should be a
# clean no-op: Pedalboard::ApplySnapshot returns false on an empty slot and
# fires no change. Confirm it is silent, not glitchy.
do_dead() {
    echo "DEAD SWITCHES - snapshots 5 and 6 on a 4-snapshot preset"
    send "go to 3 Crunch (4 snapshots)"  "C0 02"
    send "S2 page 1 -> snapshot 5 (empty)" "$(hex2 24)"
    send "S3 page 1 -> snapshot 6 (empty)" "$(hex2 25)"
    echo "  expect: nothing at all. No click, no gap, no change in the UI."
    echo "  you should still be on whatever snapshot you were on."
    echo
}

# ---- MUTE -----------------------------------------------------------------
# One CC per press. "Toggle on any value" flips MUTE each time, so the pedal
# stays dumb - it never needs to alternate 127/0.
do_mute() {
    echo "MUTE - CC 26, three presses"
    send "press 1 -> muted"      "$(hex2 26)"
    send "press 2 -> unmuted"    "$(hex2 26)"
    send "press 3 -> muted"      "$(hex2 26)"
    echo "  if it mutes once and then sticks, the binding is set to"
    echo "  'Toggle on rising edge' - change it to 'Toggle on any value'."
    echo
    echo "  then, the snapshot clobber - mute is reset by ANY snapshot change:"
    send "mute on"               "$(hex2 26)"
    send "snapshot 2"            "$(hex2 21)"
    echo "  expect: sound is BACK. Every snapshot stores MUTE=0 and"
    echo "  ApplySnapshotValue re-asserts it. Structural, not a settings bug."
    echo
}

case "${1:-all}" in
    presets)   do_presets ;;
    snapshots) do_snapshots ;;
    reset)     do_reset ;;
    mute)      do_mute ;;
    defer)     do_defer ;;
    dead)      do_dead ;;
    all)
        do_presets
        do_snapshots
        do_reset
        do_dead
        do_mute
        do_defer
        echo "done. If all six sections behaved, the layout is settled."
        ;;
    *)
        echo "usage: $0 [all|presets|snapshots|reset|mute|defer|dead]" >&2
        exit 2
        ;;
esac
