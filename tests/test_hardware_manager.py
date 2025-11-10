"""Tests for HardwareManager using fake button implementations."""

import pytest


class TestHardwareManager:
    """Test HardwareManager with fake hardware."""

    def test_initialization(self, hardware_manager):
        """Test that HardwareManager initializes without errors."""
        assert hardware_manager is not None

    def test_button_not_pressed_initially(self, hardware_manager):
        """Test that buttons are not detected as pressed initially."""
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed("up")
        assert not hardware_manager.is_button_pressed("down")

    def test_button_press_detected(self, hardware_manager, fake_buttons):
        """Test that a button press is detected."""
        # Buttons start released (value=True)
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed("up")

        # Press the button (active-low, so value=False)
        fake_buttons["up"].press()
        hardware_manager.update()

        # Should detect the press
        assert hardware_manager.is_button_pressed("up")

    def test_button_press_only_detected_once(self, hardware_manager, fake_buttons):
        """Test that a button press is only detected once until released."""
        # Press the button
        fake_buttons["up"].press()
        hardware_manager.update()

        # First check should detect the press
        assert hardware_manager.is_button_pressed("up")

        # Second check without releasing should not detect press
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed("up")

        # Third check still held down
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed("up")

    def test_button_press_release_press_cycle(self, hardware_manager, fake_buttons):
        """Test a full press, release, press cycle."""
        # First press
        fake_buttons["up"].press()
        hardware_manager.update()
        assert hardware_manager.is_button_pressed("up")

        # Still pressed, no new press detected
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed("up")

        # Release the button
        fake_buttons["up"].release()
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed("up")

        # Press again
        fake_buttons["up"].press()
        hardware_manager.update()
        assert hardware_manager.is_button_pressed("up")

    def test_multiple_buttons_independently(self, hardware_manager, fake_buttons):
        """Test that multiple buttons work independently."""
        # Press up button
        fake_buttons["up"].press()
        hardware_manager.update()
        assert hardware_manager.is_button_pressed("up")
        assert not hardware_manager.is_button_pressed("down")

        # Press down button while up is still pressed
        fake_buttons["down"].press()
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed("up")  # Already detected
        assert hardware_manager.is_button_pressed("down")  # New press

        # Release both
        fake_buttons["up"].release()
        fake_buttons["down"].release()
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed("up")
        assert not hardware_manager.is_button_pressed("down")

    def test_unknown_button_raises_error(self, hardware_manager):
        """Test that checking an unknown button raises KeyError."""
        hardware_manager.update()
        with pytest.raises(KeyError, match="Unknown button name: nonexistent"):
            hardware_manager.is_button_pressed("nonexistent")

    def test_button_active_low_logic(self, hardware_manager, fake_buttons):
        """Test that button active-low logic works correctly."""
        # Released state (value=True) should not be detected as pressed
        assert fake_buttons["up"].value is True
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed("up")

        # Pressed state (value=False) should be detected
        fake_buttons["up"].value = False
        hardware_manager.update()
        assert hardware_manager.is_button_pressed("up")

    def test_debouncing_prevents_multiple_detections(self, hardware_manager, fake_buttons):
        """Test that debouncing prevents detecting the same press multiple times."""
        # Simulate button press
        fake_buttons["up"].press()

        # First update detects the press
        hardware_manager.update()
        assert hardware_manager.is_button_pressed("up")

        # Subsequent updates while button is held should not detect press
        for _ in range(10):
            hardware_manager.update()
            assert not hardware_manager.is_button_pressed("up")

        # Only after release and press again should it be detected
        fake_buttons["up"].release()
        hardware_manager.update()
        fake_buttons["up"].press()
        hardware_manager.update()
        assert hardware_manager.is_button_pressed("up")

    def test_simultaneous_button_presses(self, hardware_manager, fake_buttons):
        """Test handling of simultaneous button presses."""
        # Press both buttons at the same time
        fake_buttons["up"].press()
        fake_buttons["down"].press()

        hardware_manager.update()

        # Both presses should be detected
        assert hardware_manager.is_button_pressed("up")
        assert hardware_manager.is_button_pressed("down")

        # Next update should not detect either
        hardware_manager.update()
        assert not hardware_manager.is_button_pressed("up")
        assert not hardware_manager.is_button_pressed("down")
