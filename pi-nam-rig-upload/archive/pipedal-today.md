# Today — Pi 4 + SD card + UMC204HD

Nothing to nothing-but-a-working-test. No Pico, no heatsink, no HAT, **no screen or keyboard**.
Full detail: [`pipedal-nam-rig-plan.md`](./pipedal-nam-rig-plan.md)
Data model (banks / presets / snapshots): [`pipedal-data-model.md`](./pipedal-data-model.md)

---

## 0. On the bench

- Raspberry Pi 4 + its 3A USB-C power supply
- 32 GB microSD card
- A way to plug that card into your laptop — built-in SD slot (with the full-size adapter the card
  came in) or a USB card reader
- Behringer UMC204HD + its USB cable
- 2 × 1/4" guitar cables
- Laptop and phone on the same wifi

**You do NOT need:** monitor, keyboard, mouse, micro-HDMI cable, WSL, or a VM.

Every step below opens with a **Using:** line listing exactly what it needs.

**Get these two files onto the Windows laptop first** — USB stick, email them to yourself, or
OneDrive. Put them in your **Downloads** folder:

- `pipedal-setup.sh`
- `pipedal-nam-rig-plan.md` (reference, optional)

> ⚠️ **Don't open `pipedal-setup.sh` in Notepad and save it.** Windows will rewrite the line
> endings and the Pi will refuse to run it (`bad interpreter: /bin/bash^M`). Just move the file.
> If it does happen, fix it on the Pi with: `sed -i 's/\r$//' pipedal-setup.sh`

---

## 1. Flash the SD card

**Using:** Windows laptop · microSD card · card reader or SD adapter
**Pi stays unplugged.**

1. Put the microSD card into your laptop.
2. Go to **raspberrypi.com/software**, download **Raspberry Pi Imager for Windows**, run the
   installer, open it.
3. Click **CHOOSE DEVICE** → **Raspberry Pi 4**.
4. Click **CHOOSE OS** → scroll down to **Raspberry Pi OS (other)** → **Raspberry Pi OS Lite (64-bit)**.
   - Lite = no desktop. Correct here, and it's what makes the latency good.
5. Click **CHOOSE STORAGE** → pick your card. **Check the size matches your card** — this erases
   whatever you select.
6. Click **NEXT**.
7. Dialog appears: *"Would you like to apply OS customisation settings?"* → click **EDIT SETTINGS**.
8. On the **GENERAL** tab, tick each box and fill in:

   | Field | Value |
   |---|---|
   | Set hostname | `pipedal` |
   | Set username and password | pick both — write them down |
   | Configure wireless LAN — SSID | your wifi name |
   | Configure wireless LAN — Password | your wifi password |
   | **Wireless LAN country** | **AU** ← wifi may not start without this |
   | Set locale settings — Time zone | `Australia/Perth` |

9. Click the **SERVICES** tab → tick **Enable SSH** → select **Use password authentication**.
   - This is the step that means you never need a screen.
10. Click **SAVE**.
11. Back at the dialog, click **YES** (apply settings).
12. *"All existing data will be erased"* → **YES**.
13. Wait ~5 minutes. It writes, then verifies.
14. **"Write Successful"** → click **CONTINUE**. Imager ejects the card for you.
15. Pull the card out of the laptop.

---

## 2. Boot the Pi

**Using:** Pi 4 · microSD (just flashed) · USB-C power supply · UMC204HD · its USB-B cable
**Not used:** monitor, keyboard, HDMI cable — none of it goes near the Pi.

1. Slot the microSD into the Pi 4 — the slot is on the **underside** of the board, opposite the
   USB ports. Contacts face up toward the board. It pushes in flush.
2. Plug the UMC204HD into any USB port on the Pi with its USB cable.
3. Plug in the USB-C power last.
4. Red LED = power. Green LED flickering = it's reading the card and booting.
5. **Wait 90 seconds.** First boot is slower than later ones.

---

## 3. Find the Pi on your network

**Using:** Windows laptop (PowerShell) · your router's admin page · Pi powered on and booted

Open **PowerShell** on Windows (Start → type `powershell`) and try:

```powershell
ping pipedal.local
```

**If that replies**, note the IP address it shows and skip ahead.

**If it doesn't** (common on Windows), get the IP from your router:

1. Browse to your router's admin page — usually `192.168.0.1` or `192.168.1.1`
2. Find the connected-devices / DHCP-clients list
3. Look for a device named **pipedal** and note its IP, e.g. `192.168.0.42`

Everything below uses `<PI-IP>` — substitute that number.

---

## 4. Connect and copy the script over

**Using:** Windows laptop (PowerShell) · `pipedal-setup.sh` in your Downloads folder

Windows 10 (1809+) and Windows 11 have `ssh` and `scp` built in. **No PuTTY, no WSL, no VM.**

In the same **PowerShell** window:

```powershell
cd $HOME\Downloads
scp pipedal-setup.sh <user>@<PI-IP>:~/
```

First connection asks *"Are you sure you want to continue connecting?"* → type `yes` and Enter.
Then enter the password you set in step 8. (The password won't show as you type — that's normal.)

Now log in:

```powershell
ssh <user>@<PI-IP>
```

The prompt changes to `<user>@pipedal:~ $`. You're on the Pi.

> **If `ssh` isn't recognised:** Settings → Apps → Optional Features → Add a feature →
> **OpenSSH Client** → Install. Then reopen PowerShell.

---

## 5. Set up (on the Pi)

**Using:** Windows laptop (SSH session) · Pi · UMC204HD plugged into it
**Everything from here is typed on the laptop, running on the Pi.**

```bash
chmod +x pipedal-setup.sh
./pipedal-setup.sh check
```

Read the output. `aarch64` should be a green tick.

```bash
sudo ./pipedal-setup.sh update
```

Takes 5–15 minutes. Then:

```bash
sudo reboot
```

Your SSH session drops. Wait 60s, reconnect with the same `ssh` command, then:

```bash
./pipedal-setup.sh audio
```

**The UMC204HD must appear under capture devices.** If it doesn't, unplug and replug its USB
cable and run it again.

```bash
sudo ./pipedal-setup.sh install
```

---

## 6. Wire up the audio

**Using:** guitar · guitar cable #1 (guitar → interface INPUT 1) · UMC204HD ·
guitar cable #2 (interface MAIN OUT L → amp FX RETURN) · Blackstar HT Stage 60

**On the interface:**

| Control | Set to |
|---|---|
| Guitar plugged into | INPUT 1 |
| LINE/INSTR switch | **INSTR** |
| 48V | OFF |
| GAIN | start low, adjust so peaks hit ~ −6 dB |
| **MIX knob** | **fully round to PLAYBACK** ← or dry guitar leaks through and it sounds thin |
| Output level knob | **ZERO** for now |

**To the amp (HT Stage 60):**

- Interface **MAIN OUT L** → amp **FX RETURN**, using a normal 1/4" guitar cable
- Rear panel loop level switch: start at **+4 dB**
- ⚠️ Do not plug anything into the speaker output jack
- ⚠️ Master volume may not control level from the FX return — that's why the output knob starts at zero

---

## 7. PiPedal

**Using:** phone (browser) · guitar · amp · everything from step 6 still connected

On your **phone**, browse to `http://<PI-IP>/`

1. Work through the onboarding page if it appears.
2. Hamburger menu → **Settings** → **Audio Device Settings**:
   - Device: **UMC204HD**
   - Sample rate: **48 kHz**
   - Buffers: **64 × 3**
   - **Input channel** — guitar is often on the right channel only. If you get silence, this is why.
3. Log into **TONE3000** inside the UI and download 3 **preamp-only** captures.
   - Preamp-only, because your EL34s are already the power amp.
   - Prefer **A2 Full** for one instance; A2 Lite if CPU is tight.

Play, and bring the interface output knob up slowly. You should hear guitar.

---

## 8. The test

**Using:** phone (PiPedal UI) · guitar · amp · laptop (SSH) for the hands-free version

Build one preset: `[Gate] → [TooB NAM] → [Delay]`

**Set your levels.** Interface input gain so peaks approach 0 dBFS, then the plugin's Input Gain
and Output Gain per capture. *Not* NAM Calibration — that's a different feature than it sounds
(one voltmeter measurement of your guitar, and it only works on captures whose author embedded
calibration metadata, which most TONE3000 captures don't). PiPedal's own doc: "there is no
requirement to perform this calibration step."

Make 2 snapshots (camera icon in the preset editor) pointing at **two captures that sound wildly
different** — clean vs high gain.

**Check the swap actually happens before judging anything:** tap snapshot 1 → the NAM plugin shows
capture A. Tap snapshot 2 → capture B. If both show the same model, the test tells you nothing.

Now switch between them in **Performance View** and listen for a click or dropout:

1. On a ringing open chord
2. While actively picking

Hands-free version, so both hands stay on the guitar:

```bash
sudo ./pipedal-setup.sh midi
# bind CC 20 -> next snapshot in Settings -> System MIDI Bindings, then:
sleep 5; amidi -p hw:2,0 -S "B0 14 7F"
```

Not sure what you heard? Record the amp on your phone and look for a dip in the waveform.

---

## 9. Write these down

**Using:** phone (CPU meter in PiPedal UI) · laptop (second SSH window for temperature)

## ✅ DONE 2026-09-04

| | Result |
|---|---|
| Snapshot model swap — clean or glitch? | **Clean / seamless** → **Design A selected** |
| Built as | preset `New`: one NAM instance, 3 snapshots swapping `modelFile` (Fender Clean → Fender Crunch → Mesa MKVII) |
| Chain | `[tuner] → [gate] → [NAM] → [cab-sim] → [delay]` |
| Buffer size that ran clean | **64 × 3 @ 48 kHz**, first try |
| DSP load @ **1 NAM** + tuner + gate + cab sim + delay | **~27–28%** of one core, peak 36% |
| Temp under load | **50.1 °C** (H0608 fitted, open air) |
| `get_throttled` | **`0x0`**, including sticky since-boot bits |
| Underruns while playing | **1** in ~1h45m, probably caused by SSH sampling |

Measured on the `ppdl_alsaDriver` thread (RT priority 90) — the real audio thread. Its CPU against
one core *is* the DSP load, so the UI meter wasn't needed.

**Design A is what this doc hoped for**, and the cheap option: one NAM instance, capture swapped per
snapshot, ~1× NAM CPU. Design B (three instances toggling bypass) was never built and isn't needed.

> ⚠️ **The 27% figure is ONE NAM instance.** An earlier revision of this table said three — wrong.

### Next, in order

**Stale — Phase 2 is built. See `pipedal-session-handoff.md` §4 for the live list.**
Of the three items that were here: no-cab/DI captures are still **deferred** (only needed for the
Blackstar FX return); Phase 2 shipped as **six** presets × **four** snapshots, not three × three;
and 32×3 remains an unexercised want-to — 64×3 measures ~29.5% worst case with no underruns.

### Environment notes worth keeping

- Pi: `192.168.0.73`, hostname `pipedal`, SSH by key, no passphrase
- Services are **`pipedald`** and **`pipedaladmind`** — both active
- The UMC204HD's **card number drifts** — it was 3, it was 1 on 2026-09-05. PiPedal stores it by
  name as `hw:U192k`, which is what makes that a non-event. **Never pin the number.** The `hw:2,0`
  in step 8's MIDI command is a guess — run `amidi -l` and use what you actually see
- **If it goes silent after a reboot or USB replug: reapply Audio Device Settings in the UI before
  debugging anything else.** A stale `AudioConfig.json` was the cause once, and it cost an hour

---

## If something breaks

**Using:** laptop (SSH session)

```bash
./pipedal-setup.sh check          # first stop for anything
journalctl -u pipedald -f         # live logs, Ctrl-C to quit
```

| Symptom | Fix |
|---|---|
| Can't find the Pi on the network | Wifi country wasn't set to AU — reflash |
| SSH refused | Enable SSH wasn't ticked in Services — reflash |
| `ssh` not recognised in PowerShell | Add OpenSSH Client in Optional Features (§4) |
| `bad interpreter: /bin/bash^M` | Windows line endings: `sed -i 's/\r$//' pipedal-setup.sh` |
| No sound at all | MIX knob to PLAYBACK; check input channel in PiPedal |
| Interface missing after reboot | Unplug/replug its USB cable |
| Silence or glitching, buffers don't help | `sudo ./pipedal-setup.sh implicitfb` |
| Thin, phasey, hollow | MIX knob again |
| Crackling / dropouts | Raise buffers to 64×4, then 128×3 |
