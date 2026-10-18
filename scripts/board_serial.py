#!/usr/bin/env python3
"""Control the board over its serial REPL."""

import argparse
import time

import serial

PORT_URL = "hwgrep://MatrixPortal"
BAUD_RATE = 115200
PROMPT = b">>> "
PROMPT_TIMEOUT = 10.0

COMMANDS = {
    "reload": None,
    "reset": "import microcontroller; microcontroller.reset()",
    "usb-mode": (
        "open('/usb_mode', 'w').close(); import microcontroller; microcontroller.reset()"
    ),
}


def enter_repl(port: serial.Serial) -> None:
    """Stop the running code and wait for the REPL prompt."""
    deadline = time.monotonic() + PROMPT_TIMEOUT
    received = b""
    while time.monotonic() < deadline:
        port.write(b"\x03")
        time.sleep(0.2)
        port.write(b"\r")
        time.sleep(0.3)
        received += port.read(port.in_waiting or 1)
        if PROMPT in received:
            return
    raise SystemExit("The board's REPL did not answer")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=COMMANDS,
        help=(
            "reload: soft reload the app; reset: hard reset the board; "
            "usb-mode: hard reset with CIRCUITPY writable over USB for one boot"
        ),
    )
    args = parser.parse_args()
    port = serial.serial_for_url(PORT_URL, BAUD_RATE, timeout=0.2)
    code = COMMANDS[args.command]
    if code is None:
        port.write(b"\x03")
        time.sleep(0.5)
        port.write(b"\x04")
    else:
        enter_repl(port)
        port.write(code.encode() + b"\r")
        time.sleep(0.5)
    port.close()


if __name__ == "__main__":
    main()
