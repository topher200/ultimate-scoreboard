"""Fake network and web server for testing without hardware."""


class FakeNetwork:
    """Fake Wi-Fi network for testing."""

    IP_ADDRESS = "192.168.1.50"

    def __init__(self):
        """Initialize a fake network that joins Wi-Fi on the first try."""
        self.connect_error: Exception | None = None
        self.connect_count = 0

    def connect(self):
        """Return IP_ADDRESS, or raise connect_error if it is set."""
        self.connect_count += 1
        if self.connect_error is not None:
            raise self.connect_error
        return self.IP_ADDRESS


class FakeWebServer:
    """Fake settings page server that records its handler for tests to call."""

    def __init__(self):
        """Initialize a fake server that has not started."""
        self.respond = None
        self.host = None
        self.port = None
        self.poll_count = 0

    def start(self, host, port, respond):
        """Record the host, port, and handler and return the URL."""
        self.host = host
        self.port = port
        self.respond = respond
        return f"http://{host}:{port}/"

    def poll(self):
        """Count the poll."""
        self.poll_count += 1
