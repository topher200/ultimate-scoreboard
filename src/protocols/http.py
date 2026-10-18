"""Protocol definitions for HTTP requests, which adafruit_requests.Session meets."""

from src.compat import Any, Protocol


class ResponseLike(Protocol):
    """Protocol defining an HTTP response."""

    status_code: int

    def json(self) -> Any: ...

    def iter_content(self, chunk_size: int = 1) -> Any:
        """Yield the body in byte chunks."""
        ...

    def close(self) -> None: ...


class HttpLike(Protocol):
    """Protocol defining an HTTP session."""

    def get(self, url: str, **kw: Any) -> ResponseLike: ...

    def post(self, url: str, **kw: Any) -> ResponseLike: ...
