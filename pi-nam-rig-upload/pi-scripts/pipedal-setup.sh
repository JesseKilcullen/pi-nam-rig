#!/usr/bin/env bash
#
# pipedal-setup.sh — stepped setup + diagnostics for the PiPedal NAM rig
# Companion to pipedal-nam-rig-plan.md
#
# Run ONE command at a time and read the output before moving on.
# Nothing here runs unattended — there are reboot points and steps where
# you have to listen and judge.
#
#   ./pipedal-setup.sh check        <- start here, read-only, always safe
#
set -uo pipefail

RED=$'\e[31m'; GRN=$'\e[32m'; YLW=$'\e[33m'; BLD=$'\e[1m'; RST=$'\e[0m'

say()  { printf '%s==>%s %s\n' "$BLD" "$RST" "$*"; }
ok()   { printf '  %s✓%s %s\n' "$GRN" "$RST" "$*"; }
warn() { printf '  %s!%s %s\n' "$YLW" "$RST" "$*"; }
bad()  { printf '  %s✗%s %s\n' "$RED" "$RST" "$*"; }
need_root() { [ "$(id -u)" -eq 0 ] || { bad "run this one with sudo"; exit 1; }; }

# ─────────────────────────────────────────────────────────────────────
# check — read-only system report. Safe to run at any point.
# ─────────────────────────────────────────────────────────────────────
cmd_check() {
    say "Architecture and OS"
    if [ "$(uname -m)" = "aarch64" ]; then
        ok "aarch64 (64-bit) — audio code runs ~40% faster than 32-bit"
    else
        bad "$(uname -m) — not aarch64. Reflash with the 64-bit Raspberry Pi OS image."
    fi
    printf '    %s\n' "$(. /etc/os-release && echo "$PRETTY_NAME")"
    printf '    kernel %s' "$(uname -r)"
    case "$(uname -r)" in
        [0-4].*|5.1[0-5].*) printf ' %s(want >5.15 for USB audio fixes)%s' "$YLW" "$RST" ;;
    esac
    echo

    say "Boot target"
    local tgt; tgt=$(systemctl get-default 2>/dev/null)
    if [ "$tgt" = "multi-user.target" ]; then
        ok "console — good, no GPU contention"
    else
        warn "$tgt — desktop is running. Run './pipedal-setup.sh headless' before measuring latency."
    fi

    say "Thermals and power"
    if command -v vcgencmd >/dev/null 2>&1; then
        printf '    %s\n' "$(vcgencmd measure_temp)"
        local t; t=$(vcgencmd get_throttled); t=${t#*=}
        decode_throttled "$t"
    else
        warn "vcgencmd not available"
    fi

    say "Audio devices"
    if ! command -v arecord >/dev/null 2>&1; then
        warn "alsa-utils not installed:  sudo apt install alsa-utils"
    else
        local caps; caps=$(arecord -l 2>/dev/null | grep -c '^card' || true)
        if [ "$caps" -gt 0 ]; then
            ok "$caps capture device(s):"
            arecord -l | grep '^card' | sed 's/^/      /'
        else
            bad "NO capture devices. Guitar cannot get in. Check the USB cable."
        fi
    fi
    lsusb 2>/dev/null | grep -i behringer | sed 's/^/      /'
    lsmod 2>/dev/null | grep -q snd_usb_audio && ok "snd_usb_audio loaded (no vendor driver needed)"

    say "PiPedal"
    if systemctl list-unit-files 2>/dev/null | grep -q '^pipedald'; then
        for svc in pipedald pipedaladmind; do
            if systemctl is-active --quiet "$svc"; then ok "$svc active"; else bad "$svc NOT active"; fi
        done
        printf '    reach it at: http://%s/\n' "$(hostname -I | awk '{print $1}')"
    else
        warn "not installed — run './pipedal-setup.sh install'"
    fi

    say "MIDI inputs"
    command -v amidi >/dev/null 2>&1 && amidi -l 2>/dev/null | sed 's/^/      /'
}

decode_throttled() {
    local n=$(( $1 ))
    if [ "$n" -eq 0 ]; then ok "no throttling, no under-voltage"; return; fi
    [ $(( n & 0x1     )) -ne 0 ] && bad  "NOW: under-voltage — check the 3A PSU"
    [ $(( n & 0x2     )) -ne 0 ] && bad  "NOW: ARM frequency capped"
    [ $(( n & 0x4     )) -ne 0 ] && bad  "NOW: throttled — CPU numbers are meaningless"
    [ $(( n & 0x8     )) -ne 0 ] && bad  "NOW: soft temperature limit"
    [ $(( n & 0x10000 )) -ne 0 ] && warn "since boot: under-voltage occurred"
    [ $(( n & 0x20000 )) -ne 0 ] && warn "since boot: frequency capping occurred"
    [ $(( n & 0x40000 )) -ne 0 ] && warn "since boot: throttling occurred"
    [ $(( n & 0x80000 )) -ne 0 ] && warn "since boot: soft temp limit hit"
    return 0
}

# ─────────────────────────────────────────────────────────────────────
cmd_update() {
    need_root
    say "Updating the OS (this takes a while on a Pi 4)"
    apt update && apt full-upgrade -y
    ok "done — REBOOT before continuing:  sudo reboot"
}

# ─────────────────────────────────────────────────────────────────────
cmd_audio() {
    say "USB devices"
    lsusb
    say "Capture devices (guitar in) — the UMC204HD MUST be here"
    arecord -l
    say "Playback devices (to amp)"
    aplay -l
    say "Kernel driver"
    lsmod | grep snd_usb_audio || warn "snd_usb_audio not loaded — is anything plugged in?"
    cat /proc/asound/cards
    echo
    say "Reminders you cannot fix in software"
    echo "    • LINE/INSTR switch  -> INSTR"
    echo "    • MIX knob           -> FULLY to PLAYBACK (else dry guitar leaks through)"
    echo "    • 48V                -> OFF"
    echo "    • output goes to the amp's FX RETURN, not the front input"
}

# ─────────────────────────────────────────────────────────────────────
cmd_install() {
    need_root
    command -v curl >/dev/null || { apt install -y curl; }

    say "Finding the latest PiPedal arm64 .deb"
    local url
    url=$(curl -fsSL https://api.github.com/repos/rerdavies/pipedal/releases/latest \
          | grep -o 'https://[^"]*arm64\.deb' | head -n1)
    [ -n "$url" ] || { bad "couldn't find the asset — grab it manually from"; \
                       echo "    https://github.com/rerdavies/pipedal/releases"; exit 1; }

    local deb="/tmp/$(basename "$url")"
    ok "found $(basename "$url")"
    curl -fL --progress-bar -o "$deb" "$url"

    say "Installing (apt-get, NOT apt — apt won't install local .debs)"
    apt-get install -y "$deb"

    systemctl is-active --quiet pipedald && ok "pipedald running" || warn "pipedald not running yet"
    printf '\n  Open:  http://%s/\n\n' "$(hostname -I | awk '{print $1}')"
    echo "  Then in the web UI:"
    echo "    Settings -> Audio Device Settings -> UMC204HD, 48kHz, buffers 64x3"
    echo "    check the INPUT CHANNEL — many 2-in interfaces put guitar on the right only"
}

# ─────────────────────────────────────────────────────────────────────
cmd_headless() {
    need_root
    say "Setting boot target to console"
    echo "  The docs cite this as the difference between ~15ms and sub-5ms latency."
    systemctl set-default multi-user.target
    ok "done — reboot, then unplug the monitor and use your phone"
    echo "  revert with: ./pipedal-setup.sh desktop"
}

cmd_desktop() {
    need_root
    systemctl set-default graphical.target
    ok "will boot to desktop after reboot"
}

# ─────────────────────────────────────────────────────────────────────
cmd_implicitfb() {
    need_root
    say "Applying the Behringer implicit-feedback workaround"
    echo "  ONLY do this if you get silence or glitching that buffer changes don't fix."
    echo "  A UMC202HD user needed it to get the device working at all."
    read -rp "  Proceed? [y/N] " a; [ "${a,,}" = "y" ] || { echo "  skipped"; return 0; }
    echo "options snd_usb_audio implicit_fb=1" > /etc/modprobe.d/behringer.conf
    ok "wrote /etc/modprobe.d/behringer.conf — reboot to apply"
    echo "  undo with: sudo rm /etc/modprobe.d/behringer.conf"
}

# ─────────────────────────────────────────────────────────────────────
# midi — virtual MIDI ports so you can test bindings with no hardware
# ─────────────────────────────────────────────────────────────────────
cmd_midi() {
    need_root
    say "Loading snd-virmidi"
    modprobe snd-virmidi
    grep -qx snd-virmidi /etc/modules 2>/dev/null || echo snd-virmidi >> /etc/modules
    ok "will load at boot"

    local card
    card=$(amidi -l 2>/dev/null | awk '/Virtual Raw MIDI/ {sub(/hw:/,"",$2); split($2,a,","); print a[1]; exit}')
    [ -n "$card" ] || { bad "no virmidi ports appeared"; exit 1; }
    ok "virmidi is card $card"

    say "Wiring port 0 -> port 1 through the sequencer"
    # writing to a virmidi device sends OUT its sequencer port; it does not
    # loop back to its own read side. Hence two ports.
    if aconnect "Virtual Raw MIDI ${card}-0:0" "Virtual Raw MIDI ${card}-1:0" 2>/dev/null; then
        ok "connected"
    else
        warn "aconnect by name failed — connect manually using numbers from 'aconnect -l'"
    fi

    cat <<EOF

  ${BLD}Prove the transport BEFORE involving PiPedal.${RST} Two terminals:

    Terminal A:   amidi -p hw:${card},1 -d
    Terminal B:   amidi -p hw:${card},0 -S "C0 00"

  Terminal A must print  C0 00 . If it doesn't, fix this before blaming PiPedal.
  (If virmidi won't cooperate, plug in any USB MIDI keyboard instead.)

  Then: PiPedal -> Settings -> MIDI -> input = "Virtual Raw MIDI ${card}-1"
        PiPedal -> Settings -> System MIDI Bindings
  Then: ./pipedal-setup.sh miditest

EOF
}

# ─────────────────────────────────────────────────────────────────────
cmd_miditest() {
    local card
    card=$(amidi -l 2>/dev/null | awk '/Virtual Raw MIDI/ {sub(/hw:/,"",$2); split($2,a,","); print a[1]; exit}')
    [ -n "$card" ] || { bad "no virmidi ports — run './pipedal-setup.sh midi' first"; exit 1; }
    local port="hw:${card},0"

    say "Firing the five footswitch messages on $port — watch PiPedal on your phone"
    echo
    fire() { printf '  %-18s %s\n' "$1" "$2"; amidi -p "$port" -S "$2"; sleep 2; }
    fire "SW1 snapshot 1" "B0 14 7F"   # CC 20
    fire "SW2 snapshot 2" "B0 15 7F"   # CC 21
    fire "SW3 snapshot 3" "B0 16 7F"   # CC 22
    fire "SW4 bank up"    "B0 17 7F"   # CC 23
    fire "SW5 bank down"  "B0 18 7F"   # CC 24
    fire "SW6 tuner ON"   "B0 19 7F"   # CC 25
    fire "SW6 mute ON"    "B0 1A 7F"   # CC 26
    fire "SW6 tuner OFF"  "B0 19 00"
    fire "SW6 mute OFF"   "B0 1A 00"
    echo
    ok "these are the exact bytes code.py sends from the Pico"
}

# ─────────────────────────────────────────────────────────────────────
cmd_monitor() {
    say "Live monitor — Ctrl-C to quit. Use this during the Phase 1 test."
    watch -n 2 '
        vcgencmd measure_temp
        vcgencmd get_throttled
        echo
        top -bn1 | head -n 12
    '
}

cmd_logs() { journalctl -u pipedald -f; }

# ─────────────────────────────────────────────────────────────────────
# report — timed CPU/temp/xrun capture, writes a summary instead of you
# reading a live terminal. Run this while playing through your busiest
# snapshots.
#
# Note: PiPedal's own log wording is "Recovering from ALSA <direction>
# underrun." (src/AlsaDriver.cpp), NOT "xrun" — confirmed from source
# rather than guessed, since grepping for "xrun" would silently match
# nothing and report a false "0 xruns" every time.
# ─────────────────────────────────────────────────────────────────────
cmd_report() {
    local duration="${1:-600}"   # seconds, default 10 min
    local interval=2

    if ! [[ "$duration" =~ ^[0-9]+$ ]]; then
        bad "duration must be a number of seconds, e.g. './pipedal-setup.sh report 300'"
        exit 1
    fi

    local outdir="$HOME/pipedal-reports"
    mkdir -p "$outdir"
    local start_epoch; start_epoch=$(date +%s)
    local end_epoch=$(( start_epoch + duration ))
    local since_iso; since_iso=$(date -d "@$start_epoch" '+%Y-%m-%d %H:%M:%S')
    local outfile="$outdir/report-$(date -d "@$start_epoch" '+%Y%m%d-%H%M%S').txt"

    local have_vcgencmd=0
    command -v vcgencmd >/dev/null 2>&1 && have_vcgencmd=1
    [ "$have_vcgencmd" -eq 1 ] || warn "vcgencmd not available — CPU will still be tracked, temp/throttle won't"

    say "Recording for ${duration}s (samples every ${interval}s). Play through your busiest snapshots now."
    echo "  Ctrl-C to stop early — it'll still write a report for however long it ran."

    local cpu_samples=() temp_samples=()
    local throttled_ever=0
    local samples=0

    # baseline for CPU delta calc (see /proc/stat format: user nice system idle iowait irq softirq ...)
    read -r _ u1 n1 s1 i1 w1 irq1 sirq1 _ < /proc/stat

    trap 'echo; warn "stopped early"; ' INT

    while [ "$(date +%s)" -lt "$end_epoch" ]; do
        sleep "$interval"
        read -r _ u2 n2 s2 i2 w2 irq2 sirq2 _ < /proc/stat
        local totald=$(( (u2+n2+s2+i2+w2+irq2+sirq2) - (u1+n1+s1+i1+w1+irq1+sirq1) ))
        local idled=$(( i2 - i1 ))
        local cpu_pct=0
        [ "$totald" -gt 0 ] && cpu_pct=$(( (100*(totald-idled)) / totald ))
        cpu_samples+=("$cpu_pct")
        u1=$u2; n1=$n2; s1=$s2; i1=$i2; w1=$w2; irq1=$irq2; sirq1=$sirq2

        local temp_display="n/a"
        if [ "$have_vcgencmd" -eq 1 ]; then
            local traw; traw=$(vcgencmd measure_temp 2>/dev/null)
            local tval=${traw#temp=}; tval=${tval%\'C*}
            [ -n "$tval" ] && temp_samples+=("$tval")
            temp_display="${tval:-n/a}°C"

            local thr; thr=$(vcgencmd get_throttled 2>/dev/null); thr=${thr#*=}
            [ -n "$thr" ] && [ "$(( thr ))" -ne 0 ] && throttled_ever="$thr"
        fi

        samples=$((samples+1))
        printf '\r  sample %-4d  cpu %3d%%   temp %-8s  elapsed %ds/%ds  ' \
            "$samples" "$cpu_pct" "$temp_display" "$(( $(date +%s) - start_epoch ))" "$duration"
    done
    trap - INT
    echo

    say "Counting underruns from the journal over that window"
    local underrun_count
    underrun_count=$(journalctl -u pipedald --since "$since_iso" 2>/dev/null | grep -ic "underrun" || true)
    underrun_count=${underrun_count:-0}

    local max_cpu=0
    for v in "${cpu_samples[@]:-}"; do [ -n "$v" ] && [ "$v" -gt "$max_cpu" ] && max_cpu=$v; done

    local max_temp="n/a"
    if [ "${#temp_samples[@]}" -gt 0 ]; then
        max_temp=$(printf '%s\n' "${temp_samples[@]}" | sort -g | tail -1)
    fi

    {
        echo "PiPedal CPU/temp/xrun report"
        echo "  started:   $since_iso"
        echo "  duration:  ${duration}s requested, $(( $(date +%s) - start_epoch ))s actual"
        echo "  samples:   $samples (every ${interval}s)"
        echo
        echo "  peak CPU:      ${max_cpu}%"
        echo "  peak temp:     ${max_temp}°C"
        echo "  underruns:     $underrun_count  (journalctl -u pipedald, matched \"underrun\")"
        if [ "$have_vcgencmd" -eq 1 ]; then
            echo "  throttled:     $([ "$throttled_ever" = "0" ] && echo "no" || echo "yes (0x$throttled_ever at some point — see decode below)")"
        fi
        echo
        echo "  verdict:"
        if [ "$max_cpu" -gt 70 ]; then
            echo "    CPU peaked above the ~70% guideline (pipedal-nam-rig-plan.md §7/Phase 2) —"
            echo "    back off before adding more load: try TooB NAM's Threaded button, drop"
            echo "    reverb/delay tail, or raise the buffer size."
        else
            echo "    CPU stayed under the ~70% guideline — headroom looks fine."
        fi
        if [ "$underrun_count" -gt 0 ]; then
            echo "    $underrun_count underrun(s) logged — audible glitches almost certainly happened"
            echo "    during this run, whether or not you heard them over the amp."
        else
            echo "    no underruns logged — clean run."
        fi
    } | tee "$outfile"

    echo
    ok "report saved to $outfile"
}

cmd_debug() {
    need_root
    say "Stopping pipedald and running it in the foreground with debug logging"
    echo "  Browse to http://$(hostname -I | awk '{print $1}'):8080/"
    echo "  Ctrl-C, then: sudo systemctl start pipedald"
    echo
    systemctl stop pipedald
    pipedald /etc/pipedal/config /etc/pipedal/react -port 0.0.0.0:8080 -log-level debug
}

# ─────────────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
${BLD}pipedal-setup.sh${RST} — stepped setup for the PiPedal NAM rig

  ${BLD}Phase 0 — setup, in this order${RST}
    check         read-only system report (start here, safe any time)
    update        apt update + full-upgrade        [sudo, then reboot]
    audio         verify the UMC204HD is detected
    install       fetch + install latest PiPedal   [sudo]
    headless      boot to console, big latency win [sudo, then reboot]

  ${BLD}Phase 1 — the decisive test${RST}
    monitor       live temp / throttle / CPU while you play
    logs          tail pipedald
    report [secs] timed CPU/temp/underrun capture -> summary report (default 600s)

  ${BLD}Phase 3 — footswitch${RST}
    midi          create virtual MIDI ports + wire them   [sudo]
    miditest      fire the 5 footswitch messages

  ${BLD}Troubleshooting${RST}
    implicitfb    Behringer implicit_fb workaround  [sudo]
    debug         run pipedald in foreground, verbose
    desktop       revert to graphical boot          [sudo]

  See pipedal-nam-rig-plan.md for what each phase means.
EOF
}

case "${1:-}" in
    check)      cmd_check ;;
    update)     cmd_update ;;
    audio)      cmd_audio ;;
    install)    cmd_install ;;
    headless)   cmd_headless ;;
    desktop)    cmd_desktop ;;
    implicitfb) cmd_implicitfb ;;
    midi)       cmd_midi ;;
    miditest)   cmd_miditest ;;
    monitor)    cmd_monitor ;;
    logs)       cmd_logs ;;
    report)     shift; cmd_report "$@" ;;
    debug)      cmd_debug ;;
    *)          usage ;;
esac
