"""Network patches for faster failure behavior.

This module provides monkey-patches to reduce network retries and timeouts
for faster failure when network is unavailable.
"""

from src.compat import Any

NETWORK_TIMEOUT_SECONDS = 2

_PATCHED_MARKER = "_scoreboard_short_timeout"


def _mark_patched(obj: Any) -> bool:
    """Mark obj as patched.

    :return: False if obj was already patched
    """
    if getattr(obj, _PATCHED_MARKER, False):
        return False
    setattr(obj, _PATCHED_MARKER, True)
    return True


def _patch_requests_get(requests_obj: Any) -> None:
    """Patch requests.get with a shorter timeout if not already patched."""
    if requests_obj is None or not hasattr(requests_obj, "get"):
        return
    if not _mark_patched(requests_obj):
        return

    original_requests_get = requests_obj.get

    def requests_get_with_short_timeout(*args, **kwargs):
        kwargs["timeout"] = NETWORK_TIMEOUT_SECONDS
        return original_requests_get(*args, **kwargs)

    requests_obj.get = requests_get_with_short_timeout


def apply_network_patches(matrixportal: Any) -> None:
    """Apply all network patches to reduce retries and timeouts.

    Patches:
    - network.connect: Forces max_attempts=1 (no retries)
    - network.fetch: Forces timeout=NETWORK_TIMEOUT_SECONDS
    - requests.get: Forces timeout=NETWORK_TIMEOUT_SECONDS for direct HTTP calls

    Applying the patches more than once has no further effect.

    :param matrixportal: MatrixPortal instance to patch
    """
    network = matrixportal.network
    if not _mark_patched(network):
        return

    original_fetch = network.fetch

    def fetch_with_short_timeout(*args, **kwargs):
        kwargs["timeout"] = NETWORK_TIMEOUT_SECONDS
        return original_fetch(*args, **kwargs)

    network.fetch = fetch_with_short_timeout

    original_connect = network.connect

    def connect_with_no_retries(*args, **kwargs):
        kwargs["max_attempts"] = 1
        result = original_connect(*args, **kwargs)
        # requests exists only after the first connect
        _patch_requests_get(network._wifi.requests)
        return result

    network.connect = connect_with_no_retries

    _patch_requests_get(network._wifi.requests)
