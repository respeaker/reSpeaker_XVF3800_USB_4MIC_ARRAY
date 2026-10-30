#!/usr/bin/env python3
"""Use the reSpeaker XVF3800 Mute button as an LED mode switch (USB firmware >= v2.1.1).

Short press -> next LED mode (see MODES below)
Long press  -> toggle mute (muted: 3 red blinks, then LEDs off;
               unmuted: short multi-color blink, then back to the LED mode)

While this script is not running, the button keeps its default mute behaviour.

Usage: python mute_button_led_modes.py
"""
import json
import struct
import sys
import time
from pathlib import Path

import usb.core

VID, PID = 0x2886, 0x001A
LONG_PRESS_S = 0.8
POLL_S = 0.02
STATE_FILE = Path(__file__).with_name("mute_button_state.json")

COLORS = [
    ("Red", 0xFF0000),
    ("Orange", 0xFF6000),
    ("Yellow", 0xFFD000),
    ("Lime", 0x80FF00),
    ("Green", 0x00FF00),
    ("Spring green", 0x00FF80),
    ("Cyan", 0x00FFFF),
    ("Azure", 0x0080FF),
    ("Blue", 0x0000FF),
    ("Violet", 0x8000FF),
    ("Magenta", 0xFF00FF),
    ("Pink", 0xFF0080),
    ("White", 0xFFFFFF),
]
# (name, LED_EFFECT, LED_COLOR) - effects: 0 off, 1 breath, 2 rainbow, 3 single color, 4 doa
MODES = (
    [("DOA (default)", 4, None), ("Rainbow", 2, None)]
    + [(name, 3, color) for name, color in COLORS]
    + [("Off", 0, None)]
)

# name: (resid, cmdid, struct format)
CMDS = {
    "LED_EFFECT": (20, 12, "B"),
    "LED_COLOR": (20, 16, "I"),
    "AUDIO_MGR_MIC_GAIN": (35, 0, "f"),
    "GPI_READ_VALUES": (36, 0, "BBB"),
    "MUTE_FUNCTION_ENABLE": (36, 8, "B"),
    "SAVE_CONFIGURATION": (48, 9, "B"),
}

CONTROL_SUCCESS = 0
SERVICER_COMMAND_RETRY = 64


class ReSpeaker:
    def __init__(self, dev):
        self.dev = dev

    def write(self, name, value):
        resid, cmdid, fmt = CMDS[name]
        self.dev.ctrl_transfer(0x40, 0, cmdid, resid, struct.pack("<" + fmt, value), 1000)

    def read(self, name):
        resid, cmdid, fmt = CMDS[name]
        length = struct.calcsize(fmt) + 1
        for _ in range(100):
            resp = self.dev.ctrl_transfer(0xC0, 0, 0x80 | cmdid, resid, length, 1000)
            if resp[0] == CONTROL_SUCCESS:
                return struct.unpack("<" + fmt, bytes(resp[1:]))[0]
            if resp[0] != SERVICER_COMMAND_RETRY:
                raise IOError(f"{name}: status {resp[0]}")
            time.sleep(0.01)
        raise IOError(f"{name}: no response")

    def pressed(self):
        # Raw level of the Mute button: 1 = released, 0 = pressed.
        # GPI_VALUE_ALL is not used because its polarity was observed to change.
        return self.read("GPI_READ_VALUES") == 0

    def save(self):
        # Save with the mute function enabled, so the button mutes normally without this script
        self.write("MUTE_FUNCTION_ENABLE", 1)
        self.write("SAVE_CONFIGURATION", 1)
        self.write("MUTE_FUNCTION_ENABLE", 0)


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def apply_mode(mic, idx):
    name, effect, color = MODES[idx]
    if color is not None:
        mic.write("LED_COLOR", color)
    mic.write("LED_EFFECT", effect)
    log(f"LED mode: {name}")


def blink(mic, colors, on_s=0.12, off_s=0.08):
    mic.write("LED_EFFECT", 3)
    for color in colors:
        mic.write("LED_COLOR", color)
        time.sleep(on_s)
        if off_s:
            mic.write("LED_COLOR", 0)
            time.sleep(off_s)


def current_mode(mic):
    effect, color = mic.read("LED_EFFECT"), mic.read("LED_COLOR")
    return next(
        (i for i, m in enumerate(MODES) if m[1] == effect and m[2] in (None, color)), 0
    )


def load_gain():
    try:
        return json.loads(STATE_FILE.read_text())["gain"]
    except (OSError, ValueError, KeyError):
        return None


def run(mic):
    mic.write("MUTE_FUNCTION_ENABLE", 0)
    mode = current_mode(mic)
    gain = mic.read("AUDIO_MGR_MIC_GAIN")
    # Gain 0 means the script exited while muted: restore the saved gain on unmute
    muted = gain == 0.0 and load_gain() is not None
    if muted:
        gain = load_gain()
    log(f"Connected. Mode: {MODES[mode][0]}, mic gain {gain}, muted: {muted}")

    while True:
        if not mic.pressed():
            time.sleep(POLL_S)
            continue

        start, long_done = time.monotonic(), False
        while mic.pressed():
            if not long_done and time.monotonic() - start >= LONG_PRESS_S:
                long_done = True
                muted = not muted
                if muted:
                    gain = mic.read("AUDIO_MGR_MIC_GAIN")
                    STATE_FILE.write_text(json.dumps({"gain": gain}))
                    mic.write("AUDIO_MGR_MIC_GAIN", 0.0)
                    blink(mic, [0xFF0000] * 3)
                    mic.write("LED_EFFECT", 0)
                    log("Muted")
                else:
                    mic.write("AUDIO_MGR_MIC_GAIN", gain)
                    blink(mic, [c for _, c in COLORS[:-1]], on_s=0.07, off_s=0)
                    apply_mode(mic, mode)
                    log("Unmuted")
            time.sleep(POLL_S)

        if not long_done and not muted:
            mode = (mode + 1) % len(MODES)
            apply_mode(mic, mode)
            mic.save()


def main():
    while True:
        dev = usb.core.find(idVendor=VID, idProduct=PID)
        if dev is None:
            time.sleep(2)
            continue
        try:
            run(ReSpeaker(dev))
        except (usb.core.USBError, IOError) as e:
            log(f"Connection lost ({e}), waiting for device ...")
            time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
