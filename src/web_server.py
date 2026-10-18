"""Serves the settings page over the board's Wi-Fi connection."""

import wifi
from adafruit_connection_manager import get_radio_socketpool
from adafruit_httpserver import GET, POST, Request, Response, Server

from src.compat import Callable
from src.settings_page import decode_form_value

# Seconds the server waits on a connection that sends nothing
SOCKET_TIMEOUT = 0.2


class WebServer:
    """Serves one page at "/" with adafruit_httpserver."""

    def __init__(self):
        self._server: Server | None = None

    def start(self, host: str, port: int, respond: Callable) -> str:
        """Start serving.

        :param host: IP address of the board, which the URL uses
        :param port: TCP port to listen on
        :param respond: Called with the submitted form dict, or None for a
            plain page view; returns the page HTML
        :return: URL of the page
        """
        server = Server(get_radio_socketpool(wifi.radio))
        server.socket_timeout = SOCKET_TIMEOUT

        @server.route("/", [GET, POST])
        def page(request: Request) -> Response:
            form = None
            if request.method == POST and request.form_data is not None:
                form = {
                    key: decode_form_value(request.form_data.get(key, safe=False) or "")
                    for key in request.form_data.fields
                }
            return Response(request, respond(form), content_type="text/html")

        server.start(host, port)
        self._server = server
        return f"http://{host}:{port}/"

    def poll(self) -> None:
        """Handle a waiting request, if there is one."""
        if self._server is not None:
            self._server.poll()
