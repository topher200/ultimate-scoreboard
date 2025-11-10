"""Network patches for faster failure behavior.

This module provides monkey-patches to reduce network retries and timeouts
for faster failure when network is unavailable.
"""

from src.compat import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.protocols import MatrixPortalLike

# Track which requests objects have been patched to avoid double-patching
_patched_requests = set()


def _patch_requests_get(requests_obj: Any) -> None:
    """Patch requests.get with shorter timeout if not already patched."""
    if requests_obj is None:
        return
    
    # Use id() to track unique requests objects
    requests_id = id(requests_obj)
    if requests_id in _patched_requests:
        return
    
    if hasattr(requests_obj, "get"):
        original_requests_get = requests_obj.get

        def requests_get_with_short_timeout(*args, **kwargs):
            """Wrapper that forces timeout=2 for faster failure."""
            kwargs["timeout"] = 2
            return original_requests_get(*args, **kwargs)

        requests_obj.get = requests_get_with_short_timeout
        _patched_requests.add(requests_id)


def apply_network_patches(matrixportal: Any) -> None:
    """Apply all network patches to reduce retries and timeouts.

    Patches:
    - network.connect: Forces max_attempts=1 (no retries)
    - network.fetch: Forces timeout=2 seconds (instead of 10)
    - requests.get: Forces timeout=2 seconds for direct HTTP calls

    :param matrixportal: MatrixPortal instance to patch
    """
    # Monkey-patch network.fetch to use shorter timeout (2 seconds instead of 10)
    original_fetch = matrixportal.network.fetch

    def fetch_with_short_timeout(*args, **kwargs):
        """Wrapper that forces timeout=2 for faster failure."""
        kwargs["timeout"] = 2
        return original_fetch(*args, **kwargs)

    matrixportal.network.fetch = fetch_with_short_timeout

    # Monkey-patch network.connect to fail immediately (no retries)
    # Also patch requests.get lazily when connect is called
    original_connect = matrixportal.network.connect

    def connect_with_no_retries(*args, **kwargs):
        """Wrapper that forces max_attempts=1 for immediate failure."""
        kwargs["max_attempts"] = 1
        result = original_connect(*args, **kwargs)
        
        # Patch requests.get after connection is established (requests is now set)
        _patch_requests_get(matrixportal.network._wifi.requests)
        
        return result

    matrixportal.network.connect = connect_with_no_retries

    # Patch requests.get immediately if it already exists (e.g., from previous connection)
    _patch_requests_get(matrixportal.network._wifi.requests)

