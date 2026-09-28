# oled_display.py — SSD1309 2.42" 128x64 SPI OLED, wiring per
# pipedal-hardware-v2.md §4.1 (GP14 SCK, GP15 MOSI, GP16 RES, GP17 DC,
# GP18 CS).
#
# UNVERIFIED ON REAL HARDWARE: there is no Adafruit (or other) CircuitPython
# driver specifically for the SSD1309 controller. SSD1309 is command-set
# compatible with SSD1306 in the overwhelming majority of modules sold
# (same command family, SSD1309 is the lower-power/larger-panel sibling),
# so this uses adafruit_displayio_ssd1306's driver against the SSD1309
# panel — a common practice for this exact part, but not something that
# can be confirmed without the physical display in hand. If the screen
# stays blank or shows garbage, that's the first thing to suspect; try
# init flags before assuming the wiring is wrong.
#
# Three screens:
#   - grid: 3x2 grid of preset OR snapshot names (mirrors the footswitch
#     rows), with a border around whichever one is currently active. Used
#     for both PRESET and SNAPSHOT mode -- code.py picks which data to pass.
#   - bigtext: two big lines, reused for two different purposes that never
#     show at the same time -- live tuner note+cents, and the rotary
#     encoder's preset-browse preview (position + candidate name).
# code.py picks between them based on FootswitchState.tuner_mute_on and
# BrowseState.active.
#
# Needs in CIRCUITPY/lib/: adafruit_displayio_ssd1306, adafruit_display_text,
# adafruit_display_shapes

import board
import busio
import displayio

try:
    from fourwire import FourWire  # CircuitPython 9+
except ImportError:
    from displayio import FourWire  # CircuitPython 8 and earlier

import adafruit_displayio_ssd1306
import terminalio
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect

WIDTH = 128
HEIGHT = 64

# 3x2 grid geometry: column left edges and row top edges. Last column/row
# absorbs the 128/64 remainder so the three columns are 42/43/43 wide.
COL_X = (0, 42, 85)
COL_W = (42, 43, 43)
ROW_Y = (0, 32)
ROW_H = 32

_display = None
_grid_group = None
_grid_labels = None  # 6 Label objects, index 0-5 matching the footswitch rows
_grid_borders = None  # 3 Rects, one per column (Rect width/height are fixed
                       # at construction, only x/y/hidden are mutable, so a
                       # single resizable border isn't an option -- one per
                       # column width, y-repositioned for the row, the other
                       # two hidden)
_bigtext_group = None
_bigtext_line1 = None
_bigtext_line2 = None


def init():
    global _display, _grid_group, _grid_labels, _grid_borders
    global _bigtext_group, _bigtext_line1, _bigtext_line2

    displayio.release_displays()
    spi = busio.SPI(clock=board.GP14, MOSI=board.GP15)
    display_bus = FourWire(spi, command=board.GP17, chip_select=board.GP18, reset=board.GP16)
    _display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)

    _grid_group = displayio.Group()
    _grid_labels = []
    for row in range(2):
        for col in range(3):
            x = COL_X[col] + 3
            y = ROW_Y[row] + ROW_H // 2
            lbl = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=x, y=y)
            _grid_labels.append(lbl)
            _grid_group.append(lbl)
    _grid_borders = []
    for col in range(3):
        border = Rect(COL_X[col], ROW_Y[0], COL_W[col], ROW_H, fill=None, outline=0xFFFFFF, stroke=1)
        border.hidden = True
        _grid_borders.append(border)
        _grid_group.append(border)

    _bigtext_group = displayio.Group()
    _bigtext_line1 = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=2, y=14, scale=2)
    _bigtext_line2 = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=2, y=40, scale=2)
    _bigtext_group.append(_bigtext_line1)
    _bigtext_group.append(_bigtext_line2)

    _display.root_group = _grid_group


def show_grid(names, highlight_index):
    """names: list of up to 6 strings (index 0-5 = footswitch row 1-6, i.e.
    row-major: 0,1,2 top row, 3,4,5 bottom row). Missing entries treated as
    blank. highlight_index: 0-5, or None/out-of-range to show no highlight
    (e.g. the active preset isn't one of the 6 on footswitches)."""
    _display.root_group = _grid_group

    for i in range(6):
        _grid_labels[i].text = names[i][:6] if i < len(names) and names[i] else ""

    if highlight_index is None or not 0 <= highlight_index < 6:
        for border in _grid_borders:
            border.hidden = True
    else:
        row, col = divmod(highlight_index, 3)
        for i, border in enumerate(_grid_borders):
            if i == col:
                border.y = ROW_Y[row]
                border.hidden = False
            else:
                border.hidden = True


def show_tuner(note_name, cents):
    """note_name/cents may be None (no valid pitch yet, or signal dropped)."""
    _display.root_group = _bigtext_group
    if note_name is None:
        _bigtext_line1.text = "-- --"
        _bigtext_line2.text = ""
        return
    _bigtext_line1.text = note_name
    sign = "+" if cents >= 0 else ""
    _bigtext_line2.text = "{}{:.0f}c".format(sign, cents)


def show_browse(position_text, name):
    """Rotary-encoder preset-browse preview. position_text e.g. "7/12";
    name is the candidate preset at the cursor, not yet loaded."""
    _display.root_group = _bigtext_group
    _bigtext_line1.text = position_text
    _bigtext_line2.text = (name or "")[:10]
