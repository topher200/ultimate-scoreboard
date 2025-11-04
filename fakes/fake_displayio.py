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
