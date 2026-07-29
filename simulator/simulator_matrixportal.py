"""Simulator-specific MatrixPortal with visual display capability."""

from fakes.fake_matrixportal import FakeMatrixPortal
from simulator.renderable_display import RenderableDisplay


class SimulatorMatrixPortal(FakeMatrixPortal):
    """MatrixPortal implementation for local development with visual display.

    Extends FakeMatrixPortal to use RenderableDisplay instead of FakeDisplay,
    enabling visual rendering of the display output.
    """

    def __init__(self, **kwargs):
        """Initialize a simulator matrix portal.

        Accepts any keyword arguments for compatibility with real MatrixPortal,
        but doesn't use them since this is a simulator.
        """
        self._display = RenderableDisplay()
        self._feed_data = {}

