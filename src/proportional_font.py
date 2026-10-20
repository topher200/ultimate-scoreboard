"""A proportional copy of a monospace font, for use with adafruit_display_text labels."""

import displayio
import fontio

# Columns that a space advances the text
SPACE_WIDTH = 3
# Dark columns between two glyphs
GLYPH_GAP = 1


class ProportionalFont:
    """Wraps a monospace font, so that each glyph is only as wide as its lit
    columns and the next glyph starts GLYPH_GAP columns after it."""

    def __init__(self, font):
        self._font = font
        self._glyphs: dict = {}

    def get_bounding_box(self):
        return self._font.get_bounding_box()

    def get_glyph(self, codepoint: int):
        if codepoint not in self._glyphs:
            self._glyphs[codepoint] = self._trim(self._font.get_glyph(codepoint))
        return self._glyphs[codepoint]

    def _trim(self, glyph):
        if glyph is None:
            return None
        source = glyph.bitmap
        tiles_per_row = source.width // glyph.width
        tile_x = glyph.tile_index % tiles_per_row * glyph.width
        tile_y = glyph.tile_index // tiles_per_row * glyph.height
        lit_columns = [
            x
            for x in range(glyph.width)
            if any(source[tile_x + x, tile_y + y] for y in range(glyph.height))
        ]
        if not lit_columns:
            return fontio.Glyph(
                source, glyph.tile_index, 0, 0, 0, 0, SPACE_WIDTH, glyph.shift_y
            )
        left = lit_columns[0]
        width = lit_columns[-1] - left + 1
        bitmap = displayio.Bitmap(width, glyph.height, 2)
        for y in range(glyph.height):
            for x in range(width):
                if source[tile_x + left + x, tile_y + y]:
                    bitmap[x, y] = 1
        return fontio.Glyph(
            bitmap,
            0,
            width,
            glyph.height,
            glyph.dx,
            glyph.dy,
            width + GLYPH_GAP,
            glyph.shift_y,
        )
