# oled_display.py — SSD1309 2.42" 128x64 SPI OLED, wiring per
# pipedal-hardware-v2.md §4.1 (GP14 SCK, GP15 MOSI, GP16 RES, GP17 DC,
# GP18 CS).
#
# There is no Adafruit (or other) CircuitPython driver specifically for the
# SSD1309 controller, so this uses adafruit_displayio_ssd1306's driver
# against the SSD1309 panel -- CONFIRMED WORKING on the real hardware
# (2026-09-23), provided the SPI clock is slowed to 1 MHz (see init()).
#
# Five screens:
#   - grid: 3x2 grid of preset OR snapshot names (mirrors the footswitch
#     rows), with a border around whichever one is currently active. Used
#     for both PRESET and SNAPSHOT mode -- code.py picks which data to pass.
#   - bigtext: two big lines, reused for two different purposes that never
#     show at the same time -- live tuner note+cents, and the rotary
#     encoder's preset-browse preview (position + candidate name).
#   - menu list / slider: the RESET-switch settings menu (midi_logic.EditMenu).
#     The list shows a title plus up to 7 items with a ">" cursor; the slider
#     shows a title, the value as text, and a bar that grows left or right of
#     centre (so +/- values read at a glance).
# code.py picks between them based on FootswitchState.tuner_mute_on,
# EditMenu.active and BrowseState.active.
#
# Needs in CIRCUITPY/lib/: adafruit_displayio_ssd1306, adafruit_display_text,
# adafruit_display_shapes

import board
import busio
import displayio
import vectorio

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
_menu_group = None
_menu_title = None
_menu_lines = None    # 7 item labels
_slider_group = None
_slider_title = None
_slider_value = None
_slider_bar = None    # vectorio.Rectangle, grows from the centre line

MENU_MAX_ITEMS = 7
BAR_X = 2
BAR_W = 124
BAR_Y = 46
BAR_H = 14
BAR_CENTRE = BAR_X + BAR_W // 2


def init():
    global _display, _grid_group, _grid_labels, _grid_borders
    global _bigtext_group, _bigtext_line1, _bigtext_line2
    global _menu_group, _menu_title, _menu_lines
    global _slider_group, _slider_title, _slider_value, _slider_bar

    displayio.release_displays()
    spi = busio.SPI(clock=board.GP14, MOSI=board.GP15)
    # 1 MHz, well under FourWire's 24 MHz default -- hand-wired jumper leads
    # can corrupt fast SPI silently (no ACK, so no error), leaving a blank panel.
    display_bus = FourWire(spi, command=board.GP17, chip_select=board.GP18, reset=board.GP16,
                           baudrate=1000000)
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

    _menu_group = displayio.Group()
    _menu_title = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=2, y=4)
    _menu_group.append(_menu_title)
    _menu_lines = []
    for _ in range(MENU_MAX_ITEMS):
        line = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=2, y=0)
        _menu_lines.append(line)
        _menu_group.append(line)

    _slider_group = displayio.Group()
    _slider_title = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=2, y=5)
    _slider_value = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=2, y=28, scale=2)
    _slider_group.append(_slider_title)
    _slider_group.append(_slider_value)
    _slider_group.append(Rect(BAR_X, BAR_Y, BAR_W, BAR_H, fill=None, outline=0xFFFFFF, stroke=1))
    palette = displayio.Palette(1)
    palette[0] = 0xFFFFFF
    _slider_bar = vectorio.Rectangle(pixel_shader=palette, width=1, height=BAR_H - 4,
                                     x=BAR_CENTRE, y=BAR_Y + 2)
    _slider_bar.hidden = True
    _slider_group.append(_slider_bar)
    # centre tick, drawn after the fill so it stays visible on top of it
    _slider_group.append(Rect(BAR_CENTRE, BAR_Y - 3, 1, BAR_H + 6, fill=0xFFFFFF))

    _display.root_group = _grid_group


def show_splash():
    """Boot self-test: a full-screen border plus text, drawn before any MIDI
    data exists. The normal empty grid is all-black pixels, so without this
    a blank screen can't distinguish "panel dead" from "no data yet"."""
    splash = displayio.Group()
    splash.append(Rect(0, 0, WIDTH, HEIGHT, fill=None, outline=0xFFFFFF, stroke=1))
    splash.append(label.Label(terminalio.FONT, text="OLED OK", color=0xFFFFFF, x=22, y=24, scale=2))
    splash.append(label.Label(terminalio.FONT, text="waiting for Pi", color=0xFFFFFF, x=22, y=50))
    _display.root_group = splash


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


def show_menu_list(title, items, cursor):
    """Settings-menu list page. A short list (the 3-item root) is spaced out;
    a long one (the 7 EQ bands) is packed at one text line each. Roomy lists
    top out at 4 items (the root menu)."""
    _display.root_group = _menu_group
    _menu_title.text = title
    roomy = len(items) <= 4
    first_y = 19 if roomy else 14
    step = 13 if roomy else 7
    for i, line in enumerate(_menu_lines):
        if i < len(items):
            line.text = ("> " if i == cursor else "  ") + items[i]
            line.y = first_y + step * i
        else:
            line.text = ""


def show_slider(title, value_text, fraction):
    """Settings-menu slider page. fraction: 0-100 position in the control's
    range (50 == centre), or None while the value hasn't arrived yet."""
    _display.root_group = _slider_group
    _slider_title.text = title
    _slider_value.text = value_text
    if fraction is None:
        _slider_bar.hidden = True
        return
    half = BAR_W // 2 - 2
    length = int(abs(fraction - 50) / 50 * half + 0.5)
    if length < 1:
        _slider_bar.hidden = True
        return
    _slider_bar.width = length
    _slider_bar.x = BAR_CENTRE if fraction >= 50 else BAR_CENTRE - length
    _slider_bar.hidden = False
