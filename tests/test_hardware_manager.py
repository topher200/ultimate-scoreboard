"""Tests for HardwareManager using fake keypad implementation."""

import asyncio

import pytest

from src.hardware_manager import (
    BUTTON_DOWN,
    BUTTON_LEFT,
    BUTTON_RIGHT,
    BUTTON_UP,
    KEY_NUMBER_BUTTON_DOWN,
    KEY_NUMBER_BUTTON_LEFT,
    KEY_NUMBER_BUTTON_RIGHT,
    KEY_NUMBER_BUTTON_UP,
)


class TestHardwareManager:
    """Test HardwareManager with fake hardware."""

    def test_initialization(self, hardware_manager):
        """Test that HardwareManager initializes without errors."""
        assert hardware_manager is not None

    def test_button_not_pressed_initially(self, hardware_manager):
        """Test that buttons are not detected as pressed initially."""
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)
        assert not hardware_manager.is_button_pressed(BUTTON_DOWN)

    def test_button_press_detected(self, hardware_manager, fake_keys):
        """Test that a button press is detected."""
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)

        # Simulate button press
        fake_keys.press_key(KEY_NUMBER_BUTTON_UP)
        hardware_manager.update()

        # Should detect the press
        assert hardware_manager.is_button_pressed(BUTTON_UP)

    def test_button_press_only_detected_once(self, hardware_manager, fake_keys):
        """Test that a button press is only detected once until next press."""
        # Press the button
        fake_keys.press_key(KEY_NUMBER_BUTTON_UP)
        hardware_manager.update()

        # First check should detect the press
        assert hardware_manager.is_button_pressed(BUTTON_UP)

        # Second check without new press should not detect press
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)

        # Third check still no new press
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)

    def test_button_press_release_press_cycle(self, hardware_manager, fake_keys):
        """Test a full press, release, press cycle."""
        # First press
        fake_keys.press_key(KEY_NUMBER_BUTTON_UP)
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_UP)

        # Still pressed, no new press detected
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)

        # Release the button (should be ignored, we only care about presses)
        fake_keys.release_key(KEY_NUMBER_BUTTON_UP)
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)

        # Press again
        fake_keys.press_key(KEY_NUMBER_BUTTON_UP)
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_UP)

    def test_multiple_buttons_independently(self, hardware_manager, fake_keys):
        """Test that multiple buttons work independently."""
        # Press up button
        fake_keys.press_key(KEY_NUMBER_BUTTON_UP)
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_UP)
        assert not hardware_manager.is_button_pressed(BUTTON_DOWN)

        # Press down button while up was already detected
        fake_keys.press_key(KEY_NUMBER_BUTTON_DOWN)
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)  # Already detected
        assert hardware_manager.is_button_pressed(BUTTON_DOWN)  # New press

        # Release both (should be ignored)
        fake_keys.release_key(KEY_NUMBER_BUTTON_UP)
        fake_keys.release_key(KEY_NUMBER_BUTTON_DOWN)
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)
        assert not hardware_manager.is_button_pressed(BUTTON_DOWN)

    def test_unknown_button_raises_error(self, hardware_manager):
        """Test that checking an unknown button raises KeyError."""
        hardware_manager.update()
        with pytest.raises(KeyError, match="Unknown button name: nonexistent"):
            hardware_manager.is_button_pressed("nonexistent")

    def test_debouncing_prevents_multiple_detections(self, hardware_manager, fake_keys):
        """Test that debouncing prevents detecting the same press multiple times."""
        # Simulate button press
        fake_keys.press_key(KEY_NUMBER_BUTTON_UP)

        # First update detects the press
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_UP)

        # Subsequent updates while button is held should not detect press
        for _ in range(10):
            hardware_manager.update()
            assert not hardware_manager.is_button_pressed(BUTTON_UP)

        # Only after new press should it be detected again
        fake_keys.release_key(KEY_NUMBER_BUTTON_UP)  # Release (ignored)
        hardware_manager.update()
        fake_keys.press_key(KEY_NUMBER_BUTTON_UP)  # Press again
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_UP)

    def test_simultaneous_button_presses(self, hardware_manager, fake_keys):
        """Test handling of simultaneous button presses."""
        # Press both buttons at the same time
        fake_keys.press_key(KEY_NUMBER_BUTTON_UP)
        fake_keys.press_key(KEY_NUMBER_BUTTON_DOWN)

        hardware_manager.update()

        # Both presses should be detected
        assert hardware_manager.is_button_pressed(BUTTON_UP)
        assert hardware_manager.is_button_pressed(BUTTON_DOWN)

        # Next update should not detect either (already consumed)
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)
        assert not hardware_manager.is_button_pressed(BUTTON_DOWN)

    def test_release_events_are_ignored(self, hardware_manager, fake_keys):
        """Test that release events are ignored, only presses are processed."""
        # Press and release
        fake_keys.press_key(KEY_NUMBER_BUTTON_UP)
        fake_keys.release_key(KEY_NUMBER_BUTTON_UP)
        hardware_manager.update()

        # Should only detect the press, not the release
        assert hardware_manager.is_button_pressed(BUTTON_UP)

        # Next update should not detect anything
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)

    def test_are_buttons_pressed_simultaneously(self, hardware_manager, fake_keys):
        """Test detection of simultaneous button presses."""
        hardware_manager.update()
        # Initially no buttons pressed
        assert not hardware_manager.are_buttons_pressed_simultaneously(
            BUTTON_LEFT, BUTTON_RIGHT
        )

        # Press only LEFT
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        hardware_manager.update()
        assert not hardware_manager.are_buttons_pressed_simultaneously(
            BUTTON_LEFT, BUTTON_RIGHT
        )

        # Press RIGHT as well
        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)
        hardware_manager.update()
        assert hardware_manager.are_buttons_pressed_simultaneously(
            BUTTON_LEFT, BUTTON_RIGHT
        )

        # Consume LEFT event
        hardware_manager.is_button_pressed(BUTTON_LEFT)
        assert not hardware_manager.are_buttons_pressed_simultaneously(
            BUTTON_LEFT, BUTTON_RIGHT
        )

    def test_consume_button_events(self, hardware_manager, fake_keys):
        """Test consuming button events for multiple buttons."""
        # Press both LEFT and RIGHT
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)
        hardware_manager.update()

        # Both should be detected
        assert hardware_manager.is_button_pressed(BUTTON_LEFT)
        assert hardware_manager.is_button_pressed(BUTTON_RIGHT)

        # Press again
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)
        hardware_manager.update()

        # Consume both events
        hardware_manager.consume_button_events(BUTTON_LEFT, BUTTON_RIGHT)

        # Neither should be detected now
        assert not hardware_manager.is_button_pressed(BUTTON_LEFT)
        assert not hardware_manager.is_button_pressed(BUTTON_RIGHT)

    @pytest.mark.asyncio
    async def test_monitor_buttons_simultaneous_press(
        self, hardware_manager, fake_keys
    ):
        """Test that simultaneous button press triggers simultaneous callback."""
        left_callback_called = False
        right_callback_called = False
        simultaneous_callback_called = False

        async def left_callback():
            nonlocal left_callback_called
            left_callback_called = True

        async def right_callback():
            nonlocal right_callback_called
            right_callback_called = True

        async def simultaneous_callback():
            nonlocal simultaneous_callback_called
            simultaneous_callback_called = True

        callbacks = {
            BUTTON_LEFT: left_callback,
            BUTTON_RIGHT: right_callback,
        }
        simultaneous_callbacks = {
            (BUTTON_LEFT, BUTTON_RIGHT): simultaneous_callback,
        }

        # Press both buttons simultaneously
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)
        fake_keys.press_key(KEY_NUMBER_BUTTON_RIGHT)

        # Start monitor_buttons task
        task = asyncio.create_task(
            hardware_manager.monitor_buttons(callbacks, simultaneous_callbacks)
        )

        # Wait a bit for the callback to be called
        await asyncio.sleep(0.15)

        # Cancel the task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Simultaneous callback should be called, individual callbacks should not
        assert simultaneous_callback_called
        assert not left_callback_called
        assert not right_callback_called

    @pytest.mark.asyncio
    async def test_monitor_buttons_individual_press(self, hardware_manager, fake_keys):
        """Test that individual button press triggers individual callback."""
        left_callback_called = False
        right_callback_called = False
        simultaneous_callback_called = False

        async def left_callback():
            nonlocal left_callback_called
            left_callback_called = True

        async def right_callback():
            nonlocal right_callback_called
            right_callback_called = True

        async def simultaneous_callback():
            nonlocal simultaneous_callback_called
            simultaneous_callback_called = True

        callbacks = {
            BUTTON_LEFT: left_callback,
            BUTTON_RIGHT: right_callback,
        }
        simultaneous_callbacks = {
            (BUTTON_LEFT, BUTTON_RIGHT): simultaneous_callback,
        }

        # Press only LEFT button
        fake_keys.press_key(KEY_NUMBER_BUTTON_LEFT)

        # Start monitor_buttons task
        task = asyncio.create_task(
            hardware_manager.monitor_buttons(callbacks, simultaneous_callbacks)
        )

        # Wait a bit for the callback to be called
        await asyncio.sleep(0.15)

        # Cancel the task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Individual callback should be called, simultaneous should not
        assert left_callback_called
        assert not right_callback_called
        assert not simultaneous_callback_called
