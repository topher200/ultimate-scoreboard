"""Fake network and web server for testing without hardware."""


class FakeNetwork:
    """Fake Wi-Fi network for testing."""

    IP_ADDRESS = "192.168.1.50"
    ACCESS_POINT_IP_ADDRESS = "192.168.4.1"

    def __init__(self):
        """Initialize a fake network that joins Wi-Fi on the first try."""
        self.connect_error: Exception | None = None
        self.connect_count = 0
        self.access_point_ssid: str | None = None
        self.access_point_clients = 0

    def connect(self):
        """Return IP_ADDRESS, or raise connect_error if it is set."""
        self.connect_count += 1
        if self.connect_error is not None:
            raise self.connect_error
        return self.IP_ADDRESS

    def start_access_point(self, ssid):
        """Record the SSID and return ACCESS_POINT_IP_ADDRESS."""
        self.access_point_ssid = ssid
        return self.ACCESS_POINT_IP_ADDRESS

    def access_point_has_clients(self):
        """True when access_point_clients is above zero."""
        return self.access_point_clients > 0


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
