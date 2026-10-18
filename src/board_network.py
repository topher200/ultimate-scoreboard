"""Joins Wi-Fi or hosts an access point with the board's radio."""

import time

import wifi

from src.compat import Any

ACCESS_POINT_ADDRESS_TIMEOUT = 5.0


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

    def start_access_point(self, ssid: str) -> str:
        wifi.radio.start_ap(ssid)
        deadline = time.monotonic() + ACCESS_POINT_ADDRESS_TIMEOUT
        while wifi.radio.ipv4_address_ap is None:
            if time.monotonic() > deadline:
                raise OSError("Access point has no IP address")
            time.sleep(0.1)
        return str(wifi.radio.ipv4_address_ap)

    def access_point_has_clients(self) -> bool:
        return bool(wifi.radio.stations_ap)
