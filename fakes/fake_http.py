"""Fake HTTP session for testing without a network."""

import json


class FakeResponse:
    """Fake HTTP response with a fixed status and body."""

    def __init__(self, status_code: int, body: bytes = b""):
        self.status_code = status_code
        self.body = body

    def json(self):
        return json.loads(self.body)

    def iter_content(self, chunk_size: int = 1):
        for start in range(0, len(self.body), chunk_size):
            yield self.body[start : start + chunk_size]

    def close(self) -> None:
        pass


class FakeHttp:
    """Fake HTTP session that answers each URL prefix with a set response."""

    def __init__(self):
        """Initialize a session with no responses set."""
        self.responses: dict[str, FakeResponse] = {}
        self.requests: list[tuple[str, dict | None]] = []

    def get(self, url, headers=None):
        """Record the request and return the response for the URL."""
        self.requests.append((url, headers))
        for prefix, response in self.responses.items():
            if url.startswith(prefix):
                return response
        raise OSError(f"no fake response for {url}")
