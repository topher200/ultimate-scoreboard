"""Tests for HardwareManager using fake button implementations."""

import pytest

from src.hardware_manager import BUTTON_DOWN, BUTTON_UP


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

    def test_button_press_detected(self, hardware_manager, fake_buttons):
        """Test that a button press is detected."""
        # Buttons start released (value=True)
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)

        # Press the button (active-low, so value=False)
        fake_buttons[BUTTON_UP].press()
        hardware_manager.update()

        # Should detect the press
        assert hardware_manager.is_button_pressed(BUTTON_UP)

    def test_button_press_only_detected_once(self, hardware_manager, fake_buttons):
        """Test that a button press is only detected once until released."""
        # Press the button
        fake_buttons[BUTTON_UP].press()
        hardware_manager.update()

        # First check should detect the press
        assert hardware_manager.is_button_pressed(BUTTON_UP)

        # Second check without releasing should not detect press
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)

        # Third check still held down
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)

    def test_button_press_release_press_cycle(self, hardware_manager, fake_buttons):
        """Test a full press, release, press cycle."""
        # First press
        fake_buttons[BUTTON_UP].press()
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_UP)

        # Still pressed, no new press detected
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)

        # Release the button
        fake_buttons[BUTTON_UP].release()
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)

        # Press again
        fake_buttons[BUTTON_UP].press()
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_UP)

    def test_multiple_buttons_independently(self, hardware_manager, fake_buttons):
        """Test that multiple buttons work independently."""
        # Press up button
        fake_buttons[BUTTON_UP].press()
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_UP)
        assert not hardware_manager.is_button_pressed(BUTTON_DOWN)

        # Press down button while up is still pressed
        fake_buttons[BUTTON_DOWN].press()
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)  # Already detected
        assert hardware_manager.is_button_pressed(BUTTON_DOWN)  # New press

        # Release both
        fake_buttons[BUTTON_UP].release()
        fake_buttons[BUTTON_DOWN].release()
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)
        assert not hardware_manager.is_button_pressed(BUTTON_DOWN)

    def test_unknown_button_raises_error(self, hardware_manager):
        """Test that checking an unknown button raises KeyError."""
        hardware_manager.update()
        with pytest.raises(KeyError, match="Unknown button name: nonexistent"):
            hardware_manager.is_button_pressed("nonexistent")

    def test_button_active_low_logic(self, hardware_manager, fake_buttons):
        """Test that button active-low logic works correctly."""
        # Released state (value=True) should not be detected as pressed
        assert fake_buttons[BUTTON_UP].value is True
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)

        # Pressed state (value=False) should be detected
        fake_buttons[BUTTON_UP].value = False
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_UP)

    def test_debouncing_prevents_multiple_detections(
        self, hardware_manager, fake_buttons
    ):
        """Test that debouncing prevents detecting the same press multiple times."""
        # Simulate button press
        fake_buttons[BUTTON_UP].press()

        # First update detects the press
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_UP)

        # Subsequent updates while button is held should not detect press
        for _ in range(10):
            hardware_manager.update()
            assert not hardware_manager.is_button_pressed(BUTTON_UP)

        # Only after release and press again should it be detected
        fake_buttons[BUTTON_UP].release()
        hardware_manager.update()
        fake_buttons[BUTTON_UP].press()
        hardware_manager.update()
        assert hardware_manager.is_button_pressed(BUTTON_UP)

    def test_simultaneous_button_presses(self, hardware_manager, fake_buttons):
        """Test handling of simultaneous button presses."""
        # Press both buttons at the same time
        fake_buttons[BUTTON_UP].press()
        fake_buttons[BUTTON_DOWN].press()

        hardware_manager.update()

        # Both presses should be detected
        assert hardware_manager.is_button_pressed(BUTTON_UP)
        assert hardware_manager.is_button_pressed(BUTTON_DOWN)

        # Next update should not detect either
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed(BUTTON_UP)
        assert not hardware_manager.is_button_pressed(BUTTON_DOWN)
