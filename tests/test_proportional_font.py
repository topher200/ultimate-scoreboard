"""Tests for ProportionalFont, run with the real Blinka displayio and fontio."""

from tests.test_display_renderer import _run


def test_trims_a_glyph_from_a_shared_tile_bitmap():
    """Test that a glyph in the second tile of a shared bitmap is cut to its lit columns."""
    glyph = _run(
        """
import json
import displayio, fontio
from src.proportional_font import ProportionalFont

# Two 4x2 tiles in one row; tile 1 lights columns 1-2
bitmap = displayio.Bitmap(8, 2, 2)
bitmap[0, 0] = 1
bitmap[5, 0] = 1
bitmap[6, 1] = 1

class SharedFont:
    def get_bounding_box(self):
        return (4, 2)

    def get_glyph(self, codepoint):
        return fontio.Glyph(bitmap, codepoint - 65, 4, 2, 0, 0, 4, 0)

trimmed = ProportionalFont(SharedFont()).get_glyph(ord("B"))
pixels = [[trimmed.bitmap[x, y] for x in range(trimmed.width)] for y in range(2)]
print(json.dumps({"width": trimmed.width, "shift_x": trimmed.shift_x, "pixels": pixels}))
"""
    )
    assert glyph == {"width": 2, "shift_x": 3, "pixels": [[1, 0], [0, 1]]}
