"""Runs the simulator on the laptop's network and serves the settings page."""

import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from src.compat import Callable


def _lan_address() -> str:
    """Return the laptop's LAN address, or localhost if it has none."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            # Picks the outbound interface; UDP connect sends no packets
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except OSError:
            return "127.0.0.1"


class SimulatorNetwork:
    """Uses the laptop's network, which is always up."""

    def connect(self) -> str:
        return _lan_address()

    def start_access_point(self, ssid: str) -> str:
        raise NotImplementedError

    def access_point_has_clients(self) -> bool:
        return False


class SimulatorWebServer:
    """Serves one page at "/" with http.server, for phones on the same LAN."""

    def __init__(self):
        self._server: HTTPServer | None = None

    def start(self, host: str, port: int, respond: Callable) -> str:
        """Start serving on all interfaces.

        :param host: IP address in the returned URL
        :param port: TCP port to listen on
        :param respond: Called with the submitted form dict, or None for a
            plain page view; returns the page HTML
        :return: URL of the page
        """

        class Handler(BaseHTTPRequestHandler):
            # Seconds to wait on a connection that sends nothing
            timeout = 0.2

            def do_GET(self):
                self._send(respond(None))

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode()
                form = {key: values[0] for key, values in parse_qs(body).items()}
                self._send(respond(form))

            def _send(self, html: str) -> None:
                data = html.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self._server = HTTPServer(("0.0.0.0", port), Handler)
        self._server.timeout = 0
        return f"http://{host}:{port}/"

    def poll(self) -> None:
        """Handle a waiting request, if there is one."""
        if self._server is not None:
            self._server.handle_request()
