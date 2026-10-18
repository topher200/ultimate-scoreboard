"""Tests for the simulator's DisplayRenderer.

conftest replaces displayio with fakes, so these tests render in a subprocess
that imports the real Blinka displayio and adafruit_display_text.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(script: str):
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYGAME_HIDE_SUPPORT_PROMPT": "1"},
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_render_pixels_draws_terminalio_glyph():
    """Test that a label renders the ter-u12n bitmap for "1"."""
    lit = _run(
        """
import json
import displayio, terminalio
from adafruit_display_text import label
from simulator.display_renderer import render_pixels

group = displayio.Group()
group.append(label.Label(terminalio.FONT, text="1", color=0xFFFFFF,
                         anchor_point=(0, 0), anchored_position=(0, 0)))
pixels = render_pixels(group)
print(json.dumps([[i % 64, i // 64] for i, color in enumerate(pixels) if color]))
"""
    )
    assert sorted(map(tuple, lit)) == sorted(
        [(2, 2), (1, 3), (2, 3)]
        + [(2, y) for y in range(4, 9)]
        + [(1, 9), (2, 9), (3, 9)]
    )


def test_render_draws_quantized_leds():
    """Test that render draws round LEDs in the colors the matrix can show."""
    result = _run(
        """
import json
import displayio
from simulator.display_renderer import DisplayRenderer

bitmap = displayio.Bitmap(1, 1, 2)
bitmap[0, 0] = 1
palette = displayio.Palette(2)
palette[1] = 0xFF80C0
palette.make_transparent(0)
group = displayio.Group()
group.append(displayio.TileGrid(bitmap, pixel_shader=palette))
image = DisplayRenderer().render(group, target_scale=10)
print(json.dumps({
    "size": image.size,
    "lit_center": image.getpixel((5, 5)),
    "lit_corner": image.getpixel((0, 0)),
    "unlit_center": image.getpixel((15, 5)),
}))
"""
    )
    assert result == {
        "size": [640, 320],
        "lit_center": [255, 212, 255],
        "lit_corner": [0, 0, 0],
        "unlit_center": [24, 24, 24],
    }
