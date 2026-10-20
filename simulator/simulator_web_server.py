"""Runs the simulator on the laptop's network and serves the settings page."""

import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from src.protocols import PageLike
from src.settings_page import SAVED_PATH


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


class SimulatorWebServer:
    """Serves one page at "/" with http.server, for phones on the same LAN."""

    def __init__(self):
        self._server: HTTPServer | None = None

    def start(self, host: str, port: int, page: PageLike) -> str:
        """Start serving on all interfaces.

        :param host: IP address in the returned URL
        :param port: TCP port to listen on
        :param page: Page to serve at "/"; see WebServerLike.start
        :return: URL of the page
        """

        class Handler(BaseHTTPRequestHandler):
            # Seconds to wait on a connection that sends nothing
            timeout = 0.2

            def do_GET(self):
                query = parse_qs(urlsplit(self.path).query)
                self._send(page.render(query.get("saved") == ["1"]))

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode()
                page.save({key: values[0] for key, values in parse_qs(body).items()})
                self.send_response(303)
                self.send_header("Location", SAVED_PATH)
                self.send_header("Content-Length", "0")
                self.end_headers()

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
