"""Gives the app write access to the filesystem, except in USB mode.

In USB mode, the CIRCUITPY drive stays writable over USB for this boot. The
board enters USB mode when the /usb_mode flag file exists.
"""

import os

import storage

USB_MODE_FILE = "/usb_mode"


def take_usb_mode_flag() -> bool:
    """Delete the USB mode flag file, and return whether it existed."""
    try:
        os.stat(USB_MODE_FILE)
    except OSError:
        return False
    storage.remount("/", readonly=False)
    os.remove(USB_MODE_FILE)
    storage.remount("/", readonly=True)
    return True


if take_usb_mode_flag():
    print("USB mode: CIRCUITPY stays writable over USB")
else:
    storage.remount("/", readonly=False)
