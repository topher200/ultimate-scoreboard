"""Joins Wi-Fi with the board's radio."""

import wifi

from src.compat import Any


class BoardNetwork:
    """Wraps the MatrixPortal network and the board's Wi-Fi radio."""

    def __init__(self, portal_network: Any):
        """Initialize BoardNetwork.

        :param portal_network: MatrixPortal network that reads settings.toml
        """
        self._portal_network = portal_network

    def connect(self) -> str:
        self._portal_network.connect()
        return str(wifi.radio.ipv4_address)
