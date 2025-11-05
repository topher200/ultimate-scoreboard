"""Tests for HardwareManager using fake button implementations."""

import pytest

from fakes import FakeButton
from lib.hardware_manager import HardwareManager


class TestHardwareManager:
    """Test HardwareManager with fake hardware."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.button_up = FakeButton()
        self.button_down = FakeButton()
        self.hardware_manager = HardwareManager(
            {
                "up": self.button_up,
                "down": self.button_down,
            }
        )

    def test_initialization(self):
        """Test that HardwareManager initializes without errors."""
        assert self.hardware_manager is not None

    def test_button_not_pressed_initially(self):
        """Test that buttons are not detected as pressed initially."""
        self.hardware_manager.update()
        assert not self.hardware_manager.is_button_pressed("up")
        assert not self.hardware_manager.is_button_pressed("down")

    def test_button_press_detected(self):
        """Test that a button press is detected."""
        # Buttons start released (value=True)
        self.hardware_manager.update()
        assert not self.hardware_manager.is_button_pressed("up")

        # Press the button (active-low, so value=False)
        self.button_up.press()
        self.hardware_manager.update()

        # Should detect the press
        assert self.hardware_manager.is_button_pressed("up")

    def test_button_press_only_detected_once(self):
        """Test that a button press is only detected once until released."""
        # Press the button
        self.button_up.press()
        self.hardware_manager.update()

        # First check should detect the press
        assert self.hardware_manager.is_button_pressed("up")

        # Second check without releasing should not detect press
        self.hardware_manager.update()
        assert not self.hardware_manager.is_button_pressed("up")

        # Third check still held down
        self.hardware_manager.update()
        assert not self.hardware_manager.is_button_pressed("up")

    def test_button_press_release_press_cycle(self):
        """Test a full press, release, press cycle."""
        # First press
        self.button_up.press()
        self.hardware_manager.update()
        assert self.hardware_manager.is_button_pressed("up")

        # Still pressed, no new press detected
        self.hardware_manager.update()
        assert not self.hardware_manager.is_button_pressed("up")

        # Release the button
        self.button_up.release()
        self.hardware_manager.update()
        assert not self.hardware_manager.is_button_pressed("up")

        # Press again
        self.button_up.press()
        self.hardware_manager.update()
        assert self.hardware_manager.is_button_pressed("up")

    def test_multiple_buttons_independently(self):
        """Test that multiple buttons work independently."""
        # Press up button
        self.button_up.press()
        self.hardware_manager.update()
        assert self.hardware_manager.is_button_pressed("up")
        assert not self.hardware_manager.is_button_pressed("down")

        # Press down button while up is still pressed
        self.button_down.press()
        self.hardware_manager.update()
        assert not self.hardware_manager.is_button_pressed("up")  # Already detected
        assert self.hardware_manager.is_button_pressed("down")  # New press

        # Release both
        self.button_up.release()
        self.button_down.release()
        self.hardware_manager.update()
        assert not self.hardware_manager.is_button_pressed("up")
        assert not self.hardware_manager.is_button_pressed("down")

    def test_unknown_button_raises_error(self):
        """Test that checking an unknown button raises KeyError."""
        self.hardware_manager.update()
        with pytest.raises(KeyError, match="Unknown button name: nonexistent"):
            self.hardware_manager.is_button_pressed("nonexistent")

    def test_button_active_low_logic(self):
        """Test that button active-low logic works correctly."""
        # Released state (value=True) should not be detected as pressed
        assert self.button_up.value is True
        self.hardware_manager.update()
        assert not self.hardware_manager.is_button_pressed("up")

        # Pressed state (value=False) should be detected
        self.button_up.value = False
        self.hardware_manager.update()
        assert self.hardware_manager.is_button_pressed("up")

    def test_debouncing_prevents_multiple_detections(self):
        """Test that debouncing prevents detecting the same press multiple times."""
        # Simulate button press
        self.button_up.press()

        # First update detects the press
        self.hardware_manager.update()
        assert self.hardware_manager.is_button_pressed("up")

        # Subsequent updates while button is held should not detect press
        for _ in range(10):
            self.hardware_manager.update()
            assert not self.hardware_manager.is_button_pressed("up")

        # Only after release and press again should it be detected
        self.button_up.release()
        self.hardware_manager.update()
        self.button_up.press()
        self.hardware_manager.update()
        assert self.hardware_manager.is_button_pressed("up")

    def test_simultaneous_button_presses(self):
        """Test handling of simultaneous button presses."""
        # Press both buttons at the same time
        self.button_up.press()
        self.button_down.press()

        self.hardware_manager.update()

        # Both presses should be detected
        assert self.hardware_manager.is_button_pressed("up")
        assert self.hardware_manager.is_button_pressed("down")

        # Next update should not detect either
        self.hardware_manager.update()
        assert not self.hardware_manager.is_button_pressed("up")
        assert not self.hardware_manager.is_button_pressed("down")
