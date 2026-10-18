"""Type stubs for the adafruit_httpserver library.

Installed only on the board.
"""

from collections.abc import Callable, Iterable
from typing import Any

GET: str
POST: str

class FormData:
    fields: list[str]
    def get(
        self, field_name: str, default: str | None = None, *, safe: bool = True
    ) -> str | None: ...

class Request:
    method: str
    form_data: FormData | None

class Response:
    def __init__(
        self, request: Request, body: str = "", *, content_type: str | None = None
    ) -> None: ...

class Server:
    socket_timeout: float
    def __init__(self, socket_source: Any, root_path: str | None = None) -> None: ...
    def route(
        self, path: str, methods: str | Iterable[str] = ...
    ) -> Callable[[Callable[..., Response]], Callable[..., Response]]: ...
    def start(self, host: str = "0.0.0.0", port: int = 5000) -> None: ...
    def poll(self) -> str: ...
