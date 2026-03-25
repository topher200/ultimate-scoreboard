"""Tests for HardwareManager using fake keypad implementation."""

import asyncio

import pytest

from src.hardware_manager import (
    BUTTON_LEFT,
    BUTTON_RIGHT,
    KEY_NUMBER_BUTTON_LEFT,
    KEY_NUMBER_BUTTON_RIGHT,
    SIMULTANEOUS_HOLD_THRESHOLD,
    HardwareManager,
)


class TestHardwareManager:
    """Test HardwareManager with fake hardware."""

    def test_initialization(self, hardware_manager):
        """Test that HardwareManager initializes without errors."""
        assert hardware_manager is not None

    def test_button_not_pressed_initially(self, hardware_manager):
        """Test that buttons are not detected as pressed initially."""
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_LEFT)
        assert not hardware_manager.is_button_pressed(BUTTON_RIGHT)

    def test_button_press_detected(self, hardware_manager, fake_keys):
        """Test that a button press is detected."""
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_LEFT)

        # Simulate button press
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        hardware_manager.update()

        # Should detect the press
        assert hardware_manager.is_button_pressed(BUTTON_LEFT)

    def test_button_press_only_detected_once(self, hardware_manager, fake_keys):
        """Test that a button press is only detected once until next press."""
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        hardware_manager.update()

        assert hardware_manager.is_button_pressed(BUTTON_LEFT)

        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_LEFT)

        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_LEFT)

    def test_button_press_release_press_cycle(self, hardware_manager, fake_keys):
        """Test a full press, release, press cycle."""
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_LEFT)

        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_LEFT)

        fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_LEFT)

        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_LEFT)

    def test_multiple_buttons_independently(self, hardware_manager, fake_keys):
        """Test that multiple buttons work independently."""
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_LEFT)
        assert not hardware_manager.is_button_pressed(BUTTON_RIGHT)

        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_LEFT)  # Already detected
        assert hardware_manager.is_button_pressed(BUTTON_RIGHT)  # New press

        fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
        fake_keys.release_key(KEY_NUMBER_BUTTON_RIGHT)
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_LEFT)
        assert not hardware_manager.is_button_pressed(BUTTON_RIGHT)

    def test_unknown_button_raises_error(self, hardware_manager):
        """Test that checking an unknown button raises KeyError."""
        hardware_manager.update()
        with pytest.raises(KeyError, match="Unknown button name: nonexistent"):
            hardware_manager.is_button_pressed("nonexistent")

    def test_debouncing_prevents_multiple_detections(self, hardware_manager, fake_keys):
        """Test that debouncing prevents detecting the same press multiple times."""
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)

        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_LEFT)

        for _ in range(10):
            hardware_manager.update()
            assert not hardware_manager.is_button_pressed(BUTTON_LEFT)

        fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
        hardware_manager.update()
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_LEFT)

    def test_consume_button_events(self, hardware_manager, fake_keys):
        """Test consuming button events for multiple buttons."""
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)
        hardware_manager.update()

        assert hardware_manager.is_button_pressed(BUTTON_LEFT)
        assert hardware_manager.is_button_pressed(BUTTON_RIGHT)

        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)
        hardware_manager.update()

        hardware_manager.consume_button_events(BUTTON_LEFT, BUTTON_RIGHT)

        assert not hardware_manager.is_button_pressed(BUTTON_LEFT)
        assert not hardware_manager.is_button_pressed(BUTTON_RIGHT)


class TestMonitorButtonsChords:
    """Test the chord-based button monitoring state machine."""

    @pytest.mark.asyncio
    async def test_individual_press_fires_on_release(self, fake_keys):
        """Test that individual button press fires callback on release."""
        left_called = False

        async def left_cb():
            nonlocal left_called
            left_called = True

        async def right_cb():
            pass

        callbacks = {BUTTON_LEFT: left_cb, BUTTON_RIGHT: right_cb}
        hw = HardwareManager(fake_keys)

        # Press LEFT
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)

        task = asyncio.create_task(hw.monitor_buttons(callbacks))
        await asyncio.sleep(0.15)

        # Should NOT have fired yet (still held)
        assert not left_called

        # Release LEFT
        fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
        await asyncio.sleep(0.15)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert left_called

    @pytest.mark.asyncio
    async def test_chord_left_then_right(self, fake_keys):
        """Test hold LEFT then press RIGHT fires chord callback."""
        chord_called = False
        left_called = False
        right_called = False

        async def left_cb():
            nonlocal left_called
            left_called = True

        async def right_cb():
            nonlocal right_called
            right_called = True

        async def chord_cb():
            nonlocal chord_called
            chord_called = True

        callbacks = {BUTTON_LEFT: left_cb, BUTTON_RIGHT: right_cb}
        chord_callbacks = {(BUTTON_LEFT, BUTTON_RIGHT): chord_cb}
        hw = HardwareManager(fake_keys)

        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)

        task = asyncio.create_task(
            hw.monitor_buttons(callbacks, chord_callbacks=chord_callbacks)
        )
        await asyncio.sleep(0.15)

        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)
        await asyncio.sleep(0.15)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert chord_called
        assert not left_called
        assert not right_called

    @pytest.mark.asyncio
    async def test_chord_right_then_left(self, fake_keys):
        """Test hold RIGHT then press LEFT fires chord callback."""
        chord_called = False
        left_called = False
        right_called = False

        async def left_cb():
            nonlocal left_called
            left_called = True

        async def right_cb():
            nonlocal right_called
            right_called = True

        async def chord_cb():
            nonlocal chord_called
            chord_called = True

        callbacks = {BUTTON_LEFT: left_cb, BUTTON_RIGHT: right_cb}
        chord_callbacks = {(BUTTON_RIGHT, BUTTON_LEFT): chord_cb}
        hw = HardwareManager(fake_keys)

        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)

        task = asyncio.create_task(
            hw.monitor_buttons(callbacks, chord_callbacks=chord_callbacks)
        )
        await asyncio.sleep(0.15)

        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        await asyncio.sleep(0.15)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert chord_called
        assert not left_called
        assert not right_called

    @pytest.mark.asyncio
    async def test_hold_both_fires_reset(self, fake_keys):
        """Test holding both buttons for threshold fires hold_both callback."""
        reset_called = False

        async def left_cb():
            pass

        async def right_cb():
            pass

        async def reset_cb():
            nonlocal reset_called
            reset_called = True

        callbacks = {BUTTON_LEFT: left_cb, BUTTON_RIGHT: right_cb}
        mock_time = [0.0]
        hw = HardwareManager(fake_keys, get_time=lambda: mock_time[0])

        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)

        task = asyncio.create_task(
            hw.monitor_buttons(callbacks, hold_both_callback=reset_cb)
        )
        await asyncio.sleep(0.15)

        mock_time[0] = SIMULTANEOUS_HOLD_THRESHOLD + 0.1
        await asyncio.sleep(0.15)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert reset_called

    @pytest.mark.asyncio
    async def test_hold_both_released_early_no_action(self, fake_keys):
        """Test releasing both before threshold fires nothing."""
        reset_called = False
        left_called = False
        right_called = False

        async def left_cb():
            nonlocal left_called
            left_called = True

        async def right_cb():
            nonlocal right_called
            right_called = True

        async def reset_cb():
            nonlocal reset_called
            reset_called = True

        callbacks = {BUTTON_LEFT: left_cb, BUTTON_RIGHT: right_cb}
        mock_time = [0.0]
        hw = HardwareManager(fake_keys, get_time=lambda: mock_time[0])

        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)

        task = asyncio.create_task(
            hw.monitor_buttons(callbacks, hold_both_callback=reset_cb)
        )
        await asyncio.sleep(0.15)

        mock_time[0] = 0.5
        fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
        fake_keys.release_key(KEY_NUMBER_BUTTON_RIGHT)
        await asyncio.sleep(0.15)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert not reset_called
        assert not left_called
        assert not right_called

    @pytest.mark.asyncio
    async def test_chord_suppresses_individual(self, fake_keys):
        """Test that chord suppresses individual callbacks on release."""
        left_called = False
        right_called = False
        chord_called = False

        async def left_cb():
            nonlocal left_called
            left_called = True

        async def right_cb():
            nonlocal right_called
            right_called = True

        async def chord_cb():
            nonlocal chord_called
            chord_called = True

        callbacks = {BUTTON_LEFT: left_cb, BUTTON_RIGHT: right_cb}
        chord_callbacks = {(BUTTON_LEFT, BUTTON_RIGHT): chord_cb}
        hw = HardwareManager(fake_keys)

        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)

        task = asyncio.create_task(
            hw.monitor_buttons(callbacks, chord_callbacks=chord_callbacks)
        )
        await asyncio.sleep(0.15)

        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)
        await asyncio.sleep(0.15)

        fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
        fake_keys.release_key(KEY_NUMBER_BUTTON_RIGHT)
        await asyncio.sleep(0.15)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert chord_called
        assert not left_called
        assert not right_called

    @pytest.mark.asyncio
    async def test_simultaneous_press_enters_both_held(self, fake_keys):
        """Test both pressed in same cycle enters BOTH_HELD, not chord."""
        chord_called = False
        reset_called = False

        async def noop():
            pass

        async def chord_cb():
            nonlocal chord_called
            chord_called = True

        async def reset_cb():
            nonlocal reset_called
            reset_called = True

        callbacks = {BUTTON_LEFT: noop, BUTTON_RIGHT: noop}
        chord_callbacks = {(BUTTON_LEFT, BUTTON_RIGHT): chord_cb}
        mock_time = [0.0]
        hw = HardwareManager(fake_keys, get_time=lambda: mock_time[0])

        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)

        task = asyncio.create_task(
            hw.monitor_buttons(
                callbacks,
                hold_both_callback=reset_cb,
                chord_callbacks=chord_callbacks,
            )
        )
        await asyncio.sleep(0.15)

        mock_time[0] = SIMULTANEOUS_HOLD_THRESHOLD + 0.1
        await asyncio.sleep(0.15)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert reset_called
        assert not chord_called

    @pytest.mark.asyncio
    async def test_individual_press_works_after_chord(self, fake_keys):
        """Test individual presses work after a chord completes."""
        left_call_count = 0
        chord_called = False

        async def left_cb():
            nonlocal left_call_count
            left_call_count += 1

        async def right_cb():
            pass

        async def chord_cb():
            nonlocal chord_called
            chord_called = True

        callbacks = {BUTTON_LEFT: left_cb, BUTTON_RIGHT: right_cb}
        chord_callbacks = {(BUTTON_LEFT, BUTTON_RIGHT): chord_cb}
        hw = HardwareManager(fake_keys)

        task = asyncio.create_task(
            hw.monitor_buttons(callbacks, chord_callbacks=chord_callbacks)
        )

        # Chord: LEFT then RIGHT
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        await asyncio.sleep(0.15)
        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)
        await asyncio.sleep(0.15)

        # Release both
        fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
        fake_keys.release_key(KEY_NUMBER_BUTTON_RIGHT)
        await asyncio.sleep(0.15)

        assert chord_called

        # Individual LEFT press and release
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        await asyncio.sleep(0.15)
        fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
        await asyncio.sleep(0.15)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert left_call_count == 1

    @pytest.mark.asyncio
    async def test_repeated_chord_while_holding(self, fake_keys):
        """Test hold RIGHT, tap LEFT multiple times fires chord each time."""
        chord_call_count = 0
        right_called = False

        async def left_cb():
            pass

        async def right_cb():
            nonlocal right_called
            right_called = True

        async def chord_cb():
            nonlocal chord_call_count
            chord_call_count += 1

        callbacks = {BUTTON_LEFT: left_cb, BUTTON_RIGHT: right_cb}
        chord_callbacks = {(BUTTON_RIGHT, BUTTON_LEFT): chord_cb}
        hw = HardwareManager(fake_keys)

        task = asyncio.create_task(
            hw.monitor_buttons(callbacks, chord_callbacks=chord_callbacks)
        )

        # Hold RIGHT
        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)
        await asyncio.sleep(0.15)

        # First tap LEFT
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        await asyncio.sleep(0.15)
        fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
        await asyncio.sleep(0.15)

        assert chord_call_count == 1

        # Second tap LEFT (still holding RIGHT)
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        await asyncio.sleep(0.15)
        fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
        await asyncio.sleep(0.15)

        assert chord_call_count == 2

        # Third tap LEFT
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        await asyncio.sleep(0.15)
        fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
        await asyncio.sleep(0.15)

        # Release RIGHT
        fake_keys.release_key(KEY_NUMBER_BUTTON_RIGHT)
        await asyncio.sleep(0.15)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert chord_call_count == 3
        assert not right_called

    @pytest.mark.asyncio
    async def test_button_not_broken_after_aborted_both_held(self, fake_keys):
        """Regression: stale release event must not permanently break a button.

        Scenario: both buttons pressed simultaneously (BOTH_HELD), one
        released before threshold → aborted → IDLE. The other button is
        still held and releases while in IDLE. Without the fix, that
        release event is never consumed, causing every subsequent press
        of that button to fire immediately without waiting for a chord.
        """
        right_call_count = 0

        async def left_cb():
            pass

        async def right_cb():
            nonlocal right_call_count
            right_call_count += 1

        callbacks = {BUTTON_LEFT: left_cb, BUTTON_RIGHT: right_cb}
        hw = HardwareManager(fake_keys)

        task = asyncio.create_task(
            hw.monitor_buttons(callbacks)
        )

        # Press both simultaneously → BOTH_HELD
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)
        await asyncio.sleep(0.15)

        # Release LEFT before threshold → aborted hold → IDLE
        # RIGHT is still physically held
        fake_keys.release_key(KEY_NUMBER_BUTTON_LEFT)
        await asyncio.sleep(0.15)

        # Release RIGHT while in IDLE → release event not consumed (the bug)
        fake_keys.release_key(KEY_NUMBER_BUTTON_RIGHT)
        await asyncio.sleep(0.15)

        # Press RIGHT and HOLD — should enter SINGLE_HELD and wait
        # for a chord, NOT fire the individual callback immediately
        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)
        await asyncio.sleep(0.15)

        # Still holding — individual callback must NOT have fired yet
        assert right_call_count == 0, (
            "Individual callback fired while button still held — "
            "stale release event caused immediate firing"
        )

        # Release RIGHT — NOW the individual callback should fire
        fake_keys.release_key(KEY_NUMBER_BUTTON_RIGHT)
        await asyncio.sleep(0.15)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert right_call_count == 1
