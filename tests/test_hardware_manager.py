"""Tests for HardwareManager's keypad wiring and callback dispatch."""

import asyncio

from src.button_state_machine import SIMULTANEOUS_HOLD_THRESHOLD
from src.hardware_manager import (
    KEY_NUMBER_BUTTON_LEFT,
    KEY_NUMBER_BUTTON_RIGHT,
    HardwareManager,
)

UNKNOWN_KEY_NUMBER = 7


async def _run(fake_keys, steps):
    """Drive monitor_buttons through steps and return the fired callbacks.

    :param steps: list of ("press"|"release", key_number) or ("time", seconds)
    """
    fired = []

    def recorder(name):
        async def cb():
            fired.append(name)

        return cb

    mock_time = [0.0]
    hw = HardwareManager(fake_keys, get_time=lambda: mock_time[0])
    task = asyncio.create_task(
        hw.monitor_buttons(
            {"left": recorder("left"), "right": recorder("right")},
            hold_both_callback=recorder("reset"),
            chord_callbacks={
                ("left", "right"): recorder("toggle"),
                ("right", "left"): recorder("undo"),
            },
        )
    )
    for action, arg in steps:
        if action == "press":
            fake_keys.press_key(arg)
        elif action == "release":
            fake_keys.release_key(arg)
        else:
            mock_time[0] += arg
        await asyncio.sleep(0.15)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    return fired


async def test_single_press_runs_button_callback(fake_keys):
    fired = await _run(
        fake_keys,
        [("press", KEY_NUMBER_BUTTON_RIGHT), ("release", KEY_NUMBER_BUTTON_RIGHT)],
    )
    assert fired == ["right"]


async def test_chord_runs_chord_callback(fake_keys):
    fired = await _run(
        fake_keys,
        [
            ("press", KEY_NUMBER_BUTTON_LEFT),
            ("press", KEY_NUMBER_BUTTON_RIGHT),
            ("release", KEY_NUMBER_BUTTON_RIGHT),
            ("release", KEY_NUMBER_BUTTON_LEFT),
        ],
    )
    assert fired == ["toggle"]


async def test_hold_both_runs_hold_both_callback(fake_keys):
    fired = await _run(
        fake_keys,
        [
            ("press", KEY_NUMBER_BUTTON_RIGHT),
            ("press", KEY_NUMBER_BUTTON_LEFT),
            ("time", SIMULTANEOUS_HOLD_THRESHOLD),
            ("release", KEY_NUMBER_BUTTON_RIGHT),
            ("release", KEY_NUMBER_BUTTON_LEFT),
        ],
    )
    assert fired == ["reset"]


async def test_unknown_key_is_ignored(fake_keys):
    fired = await _run(
        fake_keys,
        [
            ("press", UNKNOWN_KEY_NUMBER),
            ("release", UNKNOWN_KEY_NUMBER),
            ("press", KEY_NUMBER_BUTTON_LEFT),
            ("release", KEY_NUMBER_BUTTON_LEFT),
        ],
    )
    assert fired == ["left"]


async def test_gesture_without_callback_does_nothing(fake_keys):
    hw = HardwareManager(fake_keys)
    task = asyncio.create_task(hw.monitor_buttons({}))
    for key in (KEY_NUMBER_BUTTON_LEFT, KEY_NUMBER_BUTTON_RIGHT):
        fake_keys.press_key(key)
        await asyncio.sleep(0.15)
    fake_keys.release_key(KEY_NUMBER_BUTTON_RIGHT)
    fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
    await asyncio.sleep(0.15)
    fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
    fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
    await asyncio.sleep(0.15)
    assert not task.done()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
