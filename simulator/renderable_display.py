"""Display wrapper that adds rendering capability to FakeDisplay."""

from fakes.fake_matrixportal import FakeDisplay
from simulator.display_renderer import DisplayRenderer


class RenderableDisplay(FakeDisplay):
    """Display wrapper that can render the current state to pixels.

    Wraps FakeDisplay and adds rendering capability for visual simulation.
    """

    def __init__(self):
        """Initialize a renderable display."""
        super().__init__()
        self._renderer = DisplayRenderer()

    def render_to_image(self, target_scale: int = 1):
        """Render the current display state to a PIL Image.

        :param target_scale: Scale factor for rendering (1 = native size)
        :return: PIL Image of the current display state
        """
        return self._renderer.render(self._root_group, target_scale=target_scale)
