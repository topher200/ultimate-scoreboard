"""Tests for the simulator's settings page server."""

from unittest.mock import MagicMock

from simulator import simulator_web_server
from simulator.simulator_web_server import FALLBACK_PORT, SimulatorWebServer


class _FakeHTTPServer:
    """Records the address it serves, and refuses ports below 1024."""

    def __init__(self, address, handler):
        if address[1] < 1024:
            raise PermissionError("needs root")
        self.address = address
        self.timeout = None


class TestSimulatorWebServer:
    def test_uses_the_requested_port_when_allowed(self, monkeypatch):
        monkeypatch.setattr(simulator_web_server, "HTTPServer", _FakeHTTPServer)

        url = SimulatorWebServer().start("10.0.0.5", 8090, page=MagicMock())

        assert url == "HTTP://10.0.0.5:8090"

    def test_falls_back_when_the_port_needs_privileges(self, monkeypatch):
        monkeypatch.setattr(simulator_web_server, "HTTPServer", _FakeHTTPServer)
        server = SimulatorWebServer()

        url = server.start("10.0.0.5", 81, page=MagicMock())

        assert url == f"HTTP://10.0.0.5:{FALLBACK_PORT}"
        assert getattr(server._server, "address") == ("0.0.0.0", FALLBACK_PORT)
