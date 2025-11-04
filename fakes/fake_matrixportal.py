"""Fake MatrixPortal and Display classes for testing without hardware."""


class FakeDisplay:
    """Fake implementation of displayio.Display for testing."""

    def __init__(self):
        """Initialize a fake display."""
        self._root_group = None

    @property
    def root_group(self):
        """Get the root display group."""
        return self._root_group

    @root_group.setter
    def root_group(self, value):
        """Set the root display group."""
        self._root_group = value


class FakeMatrixPortal:
    """Fake implementation of MatrixPortal for testing without hardware."""

    def __init__(self, **kwargs):
        """Initialize a fake matrix portal.

        Accepts any keyword arguments for compatibility with real MatrixPortal,
        but doesn't use them since this is a fake.
        """
        self._display = FakeDisplay()
        self._feed_data = {}
        self._pushed_data = {}

    @property
    def display(self):
        """Get the display object."""
        return self._display

    def set_feed_value(self, feed_key, value):
        """Set a value for a feed key for testing.

        :param feed_key: The feed key to set
        :param value: The value to return for this feed
        """
        self._feed_data[feed_key] = value

    def get_io_feed(self, feed_key, detailed=False):
        """Get an IO feed value.

        :param feed_key: The feed key to retrieve
        :param detailed: If True, returns detailed structure
        :return: Feed data structure
        """
        value = self._feed_data.get(feed_key)
        if detailed:
            if value is not None:
                return {
                    "details": {
                        "data": {
                            "last": {
                                "value": value,
                            }
                        }
                    }
                }
            else:
                return {
                    "details": {
                        "data": {
                            "last": None,
                        }
                    }
                }
        return value

    def push_to_io(self, feed_key, value):
        """Push a value to an IO feed.

        :param feed_key: The feed key to push to
        :param value: The value to push
        """
        self._pushed_data[feed_key] = value
        self._feed_data[feed_key] = value

    def get_pushed_value(self, feed_key):
        """Get the last pushed value for a feed key (for testing).

        :param feed_key: The feed key to retrieve
        :return: The last pushed value, or None if not found
        """
        return self._pushed_data.get(feed_key)
