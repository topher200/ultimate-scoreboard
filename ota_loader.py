"""Chooses the app slot to run at boot and rolls back a trial slot that crashes.

The board keeps two app slots, slots/a and slots/b. An update installs into
the slot that is not running and starts a trial of it. The trial ends when
the app checks in with Memfault. A crash during the trial switches back to the
previous slot. With no state file, the board runs the app in the root
directory, which is where a USB deploy puts it.

Every path is relative to a root directory that ends in "/". This module
imports nothing from src/, so that src/ resolves to the active slot.
"""

import json
import os
import sys
import traceback

STATE_FILE = "ota_state.json"
STATE_TEMP_FILE = "ota_state.tmp"
SLOTS_DIR = "slots"

ACTIVE = "active"
PREVIOUS = "previous"
TRIAL = "trial"
VERSION = "version"
ROLLED_BACK = "rolled_back"


def read_state(root: str) -> dict:
    """Return the saved slot state, or an empty dict when there is none."""
    for name in (STATE_FILE, STATE_TEMP_FILE):
        try:
            with open(root + name) as f:
                return json.load(f)
        except (OSError, ValueError):
            pass
    return {}


def write_state(root: str, state: dict) -> None:
    """Replace the saved state, keeping a whole copy on disk at every moment."""
    with open(root + STATE_TEMP_FILE, "w") as f:
        json.dump(state, f)
    remove_tree(root + STATE_FILE)
    os.rename(root + STATE_TEMP_FILE, root + STATE_FILE)


def slot_path(root: str, slot: str) -> str:
    return root + SLOTS_DIR + "/" + slot


def inactive_slot(root: str) -> str:
    """Return the slot that an update installs into."""
    return "b" if read_state(root).get(ACTIVE) == "a" else "a"


def app_path(root: str) -> str | None:
    """Return the directory of the slot to run, or None to run the root app."""
    slot = read_state(root).get(ACTIVE)
    if slot is None:
        return None
    return slot_path(root, slot)


def start_trial(root: str, slot: str, version: str) -> None:
    """Run version from slot on the next boot, until a crash or a Memfault check-in."""
    write_state(
        root,
        {
            ACTIVE: slot,
            PREVIOUS: read_state(root).get(ACTIVE),
            TRIAL: True,
            VERSION: version,
        },
    )


def in_trial(root: str) -> bool:
    return bool(read_state(root).get(TRIAL))


def mark_healthy(root: str) -> None:
    """End the trial and keep the active slot."""
    state = read_state(root)
    if state.get(TRIAL):
        state[TRIAL] = False
        write_state(root, state)


def rolled_back_version(root: str) -> str | None:
    """Return the version that crashed during its trial, if one did."""
    return read_state(root).get(ROLLED_BACK)


def roll_back_trial(root: str) -> bool:
    """Switch back to the previous slot if the active slot is in trial.

    :return: True if the board rolled back
    """
    state = read_state(root)
    if not state.get(TRIAL):
        return False
    write_state(root, {ACTIVE: state.get(PREVIOUS), ROLLED_BACK: state.get(VERSION)})
    return True


def run_app(root: str, start, reset) -> None:
    """Run the app from the active slot, and roll back and reset if a trial crashes.

    :param root: Board filesystem root, ending in "/"
    :param start: Imports and runs the app
    :param reset: Restarts the board
    """
    path = app_path(root)
    if path is not None:
        sys.path.insert(0, path)
    print(f"Running the app from {path or root}")
    try:
        start()
    except Exception as e:
        try:
            rolled_back = roll_back_trial(root)
        except OSError:
            rolled_back = False
        if not rolled_back:
            raise
        traceback.print_exception(e)
        print("Rolled back to the previous slot")
        reset()


def remove_tree(path: str) -> None:
    """Delete a file or a directory and everything in it, if it exists."""
    try:
        mode = os.stat(path)[0]
    except OSError:
        return
    if mode & 0x4000:
        for name in os.listdir(path):
            remove_tree(path + "/" + name)
        os.rmdir(path)
    else:
        os.remove(path)


def make_dirs(path: str) -> None:
    """Create a directory and its missing parents."""
    current: str | None = None
    for part in path.split("/"):
        current = part if current is None else current + "/" + part
        if not part:
            continue
        try:
            os.mkdir(current)
        except OSError:
            pass
