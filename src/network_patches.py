"""Network patches for faster failure behavior.

This module monkey-patches the MatrixPortal network so that joining Wi-Fi
fails fast when the network is unavailable.
"""

from src.compat import Any

_PATCHED_MARKER = "_scoreboard_no_retries"


def apply_network_patches(matrixportal: Any) -> None:
    """Make network.connect try once, with no retries.

    Applying the patches more than once has no further effect.

    :param matrixportal: MatrixPortal instance to patch
    """
    network = matrixportal.network
    if getattr(network, _PATCHED_MARKER, False):
        return
    setattr(network, _PATCHED_MARKER, True)

    original_connect = network.connect

    def connect_with_no_retries(*args, **kwargs):
        kwargs["max_attempts"] = 1
        return original_connect(*args, **kwargs)

    network.connect = connect_with_no_retries
