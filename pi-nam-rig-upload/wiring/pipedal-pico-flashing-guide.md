# Pico — flash CircuitPython before mounting

Do this **before** taping the Pico anywhere. BOOTSEL is only needed for this initial flash, and
it's much easier to press on a bare board on your desk than one already stuck in the box — see
`pipedal-footswitch-wiring-procedure.md` step 1 for why the Pico's mounted where it is.

## What you need

- The Pico H itself, unmounted.
- A **micro-USB data cable** — not a charge-only cable, it needs the data lines.
- A computer with a USB port. Drag-and-drop in a file manager is all that's strictly required;
  a code editor with CircuitPython support (Mu, Thonny, VS Code) is optional, useful for step 9.
- Internet access, to download:
  - **CircuitPython firmware (UF2)** for Raspberry Pi Pico — current stable is **10.3.1**, from
    <https://circuitpython.org/board/raspberry_pi_pico/>. Pico H uses the identical firmware to a
    plain Pico (same RP2040 chip — the only difference is the pre-soldered headers), so there's no
    separate "Pico H" download to hunt for.
  - **Adafruit CircuitPython Library Bundle**, matching CircuitPython's major version (10.x), from
    <https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/latest>.
- The project's own firmware files, already sitting in `pico-footswitch-v2/`: `code.py`,
  `midi_logic.py`, `pitch.py`, `oled_display.py`.

## Steps

1. **Download the CircuitPython UF2** for Raspberry Pi Pico from the link above.
2. **Put the Pico into bootloader mode**: hold down the **BOOTSEL** button, plug the micro-USB
   cable into your computer while still holding it, release after a second or two. It should show
   up as a mass-storage drive named `RPI-RP2`.
3. **Copy the UF2 file onto `RPI-RP2`.** The Pico reboots on its own and reappears as a new drive
   named `CIRCUITPY` — that's your confirmation CircuitPython installed correctly.
4. **Download the Adafruit CircuitPython Bundle**, matching the major version you just installed
   (10.x). If you want to double-check the exact version, it's written to `boot_out.txt` on the
   `CIRCUITPY` drive after step 3.
5. **Create a `lib` folder** on the `CIRCUITPY` drive, if one isn't already there.
6. **Copy these 4 items** from the bundle's own `lib` folder into `CIRCUITPY/lib/`:
   - `adafruit_displayio_ssd1306`
   - `adafruit_display_text`
   - `adafruit_display_shapes`
   - `adafruit_midi`

   Each may be a single file or a folder depending on the bundle — copy whatever it provides under
   that name, folder and all, don't try to pick out individual files from inside.
7. **Copy the project's 4 firmware files** onto the `CIRCUITPY` drive's root (not inside `lib`):
   `code.py`, `midi_logic.py`, `pitch.py`, `oled_display.py`, from `pico-footswitch-v2/`. Overwrite
   the placeholder `code.py` that's already there by default.
8. **The Pico auto-runs `code.py`** the moment `CIRCUITPY` finishes saving. With nothing wired up
   yet (no switches, no OLED, no encoder), expect it to do very little, or throw errors about
   missing hardware — that's expected at this stage and just confirms the files loaded. Real
   functional testing happens later, per the build guide's §9 first-power-up checklist, once
   everything's actually wired.
9. **(Optional) Watch for errors over serial.** CircuitPython exposes a REPL over the same USB
   connection — a terminal program (Mu, Thonny, or any serial terminal) connected to the Pico's
   port will show a traceback if something's wrong with what you copied. Useful for confirming the
   4 libraries imported cleanly before any hardware is attached to blame instead.

Once `code.py` runs without library-import errors, you're clear to move on to mounting
(`pipedal-footswitch-wiring-procedure.md` step 1) and then wiring.
