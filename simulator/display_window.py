"""Pygame window for displaying the LED matrix simulator."""

import pygame

from src.display_manager import DISPLAY_HEIGHT, DISPLAY_WIDTH


class DisplayWindow:
    """Pygame window that displays the rendered LED matrix display."""

    def __init__(self, display, scale: int = 20, keys=None):
        """Initialize the display window.

        :param display: RenderableDisplay instance to render
        :param scale: Pixel scaling factor (default 20x for 1280x640 window)
        :param keys: Optional FakeKeys instance for keyboard button simulation
        """
        self._display = display
        self._scale = scale
        self._window_width = DISPLAY_WIDTH * scale
        self._window_height = DISPLAY_HEIGHT * scale
        self._running = False
        self._screen: pygame.Surface | None = None
        self._clock: pygame.time.Clock | None = None
        self._keys = keys
        # Keyboard mapping: pygame key -> button key_number
        # UP=0, DOWN=1, LEFT=2, RIGHT=3
        self._keyboard_map = {
            pygame.K_UP: 0,  # UP button
            pygame.K_DOWN: 1,  # DOWN button
            pygame.K_LEFT: 2,  # LEFT button
            pygame.K_RIGHT: 3,  # RIGHT button
            pygame.K_w: 0,  # W key for UP
            pygame.K_s: 1,  # S key for DOWN
            pygame.K_a: 2,  # A key for LEFT
            pygame.K_d: 3,  # D key for RIGHT
        }

    def _init_pygame(self):
        """Initialize Pygame."""
        pygame.init()
        self._screen = pygame.display.set_mode(
            (self._window_width, self._window_height)
        )
        pygame.display.set_caption("LED Matrix Simulator")
        self._clock = pygame.time.Clock()
        self._running = True

    def _render_display(self):
        """Render the current display state to the Pygame window."""
        if not self._running:
            return

        screen = self._screen
        if screen is None:
            return

        try:
            image = self._display.render_to_image(target_scale=self._scale)
            if image:
                image_rgb = image.convert("RGB")
                image_bytes = image_rgb.tobytes()
                pygame_surface = pygame.image.frombuffer(
                    image_bytes, image_rgb.size, "RGB"
                )
                screen.blit(pygame_surface, (0, 0))
                pygame.display.flip()
        except Exception as e:
            print(f"Error rendering display: {e}")

    def start(self):
        """Start the display window.

        Must be called from the main thread since Pygame requires it.
        """
        self._init_pygame()
        if self._keys:
            print("Keyboard controls enabled:")
            print("  Arrow Keys or WASD: Simulate button presses")
            print("  UP/W: Toggle gender matchup and refresh team names")
            print("  LEFT/A: Increment left team score")
            print("  RIGHT/D: Increment right team score")
            print("  LEFT+RIGHT (hold ~1s): Toggle gender matchup")
            print("  LEFT+RIGHT (short press): Undo last point")
            print("  Q or ESC: Quit")

    def update(self):
        """Update the display and handle Pygame events.

        Call this periodically from the main thread to handle window events and update the display.
        """
        if not self._running:
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                # Handle quit keys
                if event.key in {pygame.K_q, pygame.K_ESCAPE}:
                    self._running = False
                    pygame.quit()
                    return
                # Handle keyboard button simulation
                elif self._keys and event.key in self._keyboard_map:
                    key_number = self._keyboard_map[event.key]
                    self._keys.press_key(key_number)
            elif event.type == pygame.KEYUP:
                if self._keys and event.key in self._keyboard_map:
                    key_number = self._keyboard_map[event.key]
                    self._keys.release_key(key_number)

        self._render_display()
        clock = self._clock
        if clock is not None:
            clock.tick(30)

    def is_running(self) -> bool:
        """Check if the window is still running.

        :return: True if the window is running, False otherwise
        """
        return self._running

    def stop(self):
        """Stop the display window."""
        self._running = False
        if self._screen:
            pygame.quit()
