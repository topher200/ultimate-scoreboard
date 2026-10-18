"""Digit glyphs for the legibility lab, drawn into a displayio.Bitmap."""

# 5x7 digits, one string per row, "1" where a pixel is lit
DIGITS_5X7 = {
    "0": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
}

# 3x5 digits, one string per row, "1" where a pixel is lit
DIGITS_3X5 = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("110", "010", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "001", "001", "001"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
}

# Lit segments of each digit: a top, b top right, c bottom right, d bottom,
# e bottom left, f top left, g middle
SEGMENTS = {
    "0": "abcdef",
    "1": "bc",
    "2": "abdeg",
    "3": "abcdg",
    "4": "bcfg",
    "5": "acdfg",
    "6": "acdefg",
    "7": "abc",
    "8": "abcdefg",
    "9": "abcdfg",
}


def fill_rect(bitmap, x: int, y: int, width: int, height: int, index: int) -> None:
    """Set the pixels of a rectangle to palette `index`, clipped to the bitmap."""
    for py in range(max(y, 0), min(y + height, bitmap.height)):
        for px in range(max(x, 0), min(x + width, bitmap.width)):
            bitmap[px, py] = index


def draw_glyph(
    bitmap, rows, x: int, y: int, scale_x: int, scale_y: int, index: int
) -> None:
    """Draw a glyph from `rows` with each pixel scaled to scale_x by scale_y."""
    for row_number, row in enumerate(rows):
        for column, char in enumerate(row):
            if char == "1":
                fill_rect(
                    bitmap,
                    x + column * scale_x,
                    y + row_number * scale_y,
                    scale_x,
                    scale_y,
                    index,
                )


def draw_segments(
    bitmap, digit: str, x: int, y: int, width: int, height: int, stroke: int, index: int
) -> None:
    """Draw a seven-segment digit that fills width by height with strokes `stroke` thick."""
    middle = (height - stroke) // 2
    upper = middle + stroke
    rects = {
        "a": (0, 0, width, stroke),
        "b": (width - stroke, 0, stroke, upper),
        "c": (width - stroke, middle, stroke, height - middle),
        "d": (0, height - stroke, width, stroke),
        "e": (0, middle, stroke, height - middle),
        "f": (0, 0, stroke, upper),
        "g": (0, middle, width, stroke),
    }
    for segment in SEGMENTS[digit]:
        rx, ry, rw, rh = rects[segment]
        fill_rect(bitmap, x + rx, y + ry, rw, rh, index)
