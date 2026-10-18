"""Fake displayio classes for testing without hardware."""


class FakeGroup:
    """Fake implementation of displayio.Group for testing."""

    def __init__(self):
        """Initialize a fake group."""
        self._items = []

    def append(self, item):
        """Append an item to the group.

        :param item: Item to append (typically a Label or other display element)
        """
        self._items.append(item)

    def __len__(self):
        """Return the number of items in the group."""
        return len(self._items)

    def __getitem__(self, index):
        """Get an item by index."""
        return self._items[index]

    def __iter__(self):
        """Iterate over items in the group."""
        return iter(self._items)


class FakeBitmap:
    """Fake implementation of displayio.Bitmap for testing."""

    def __init__(self, width, height, value_count):
        """Initialize a fake bitmap with all pixels set to 0."""
        self.width = width
        self.height = height
        self._pixels = [0] * (width * height)

    def __getitem__(self, index):
        """Get a pixel value by (x, y)."""
        x, y = index
        return self._pixels[y * self.width + x]

    def __setitem__(self, index, value):
        """Set a pixel value by (x, y)."""
        x, y = index
        self._pixels[y * self.width + x] = value


class FakePalette:
    """Fake implementation of displayio.Palette for testing."""

    def __init__(self, color_count):
        """Initialize a fake palette with all colors set to black."""
        self._colors = [0] * color_count
        self._transparent = set()

    def __len__(self):
        """Return the number of colors in the palette."""
        return len(self._colors)

    def __getitem__(self, index):
        """Get a color by index."""
        return self._colors[index]

    def __setitem__(self, index, color):
        """Set a color by index."""
        self._colors[index] = color

    def make_transparent(self, palette_index):
        """Mark a palette index as transparent."""
        self._transparent.add(palette_index)

    def is_transparent(self, palette_index):
        """Check if a palette index is transparent."""
        return palette_index in self._transparent


class FakeTileGrid:
    """Fake implementation of displayio.TileGrid for testing."""

    def __init__(self, bitmap, *, pixel_shader, x=0, y=0):
        """Initialize a fake tile grid."""
        self.bitmap = bitmap
        self.pixel_shader = pixel_shader
        self.x = x
        self.y = y
        self.hidden = False
