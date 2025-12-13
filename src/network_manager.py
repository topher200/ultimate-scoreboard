"""Manages network interactions with Adafruit IO feeds."""

from __future__ import annotations

import asyncio
import time

from src.compat import TYPE_CHECKING
from src.protocols import MatrixPortalLike

if TYPE_CHECKING:
    from src.display_manager import DisplayManager
    from src.gender_manager import GenderManager


class NetworkManager:
    """Manages fetching data from Adafruit IO feeds."""

    # Feed key constants
    TEAM_LEFT_TEAM_FEED = "scores-group.left-team-name"
    TEAM_RIGHT_TEAM_FEED = "scores-group.right-team-name"

    DEFAULT_LEFT_TEAM_NAME = "AWAY"
    DEFAULT_RIGHT_TEAM_NAME = "HOME"

    def __init__(self, matrixportal: MatrixPortalLike, display_manager: DisplayManager):
        """Initialize NetworkManager with MatrixPortal.

        :param matrixportal: MatrixPortal-like instance for network operations
        :param display_manager: DisplayManager instance for showing connection status
        """
        self._matrixportal = matrixportal
        self.display_manager = display_manager
        self._circuit_breaker_open_until: float | None = None

    def _is_circuit_breaker_open(self) -> bool:
        """Check if the circuit breaker is currently open.

        :return: True if circuit breaker is open, False otherwise
        """
        if self._circuit_breaker_open_until is None:
            return False
        return time.monotonic() < self._circuit_breaker_open_until

    def _trigger_circuit_breaker(self) -> None:
        """Trigger the circuit breaker to open for 60 seconds."""
        self._circuit_breaker_open_until = time.monotonic() + 60

    def reset_circuit_breaker(self) -> None:
        """Reset the circuit breaker to allow immediate network operations."""
        self._circuit_breaker_open_until = None

    async def _get_feed_value(self, feed_key: str) -> None | str:
        """Fetch the last value from an Adafruit IO feed.

        :param feed_key: The feed key to fetch from
        :return: The last value from the feed, or None if not available
        """
        if self._is_circuit_breaker_open():
            return None

        await asyncio.sleep(0)
        self.display_manager.show_connecting(True)
        try:
            feed = self._matrixportal.get_io_feed(feed_key, detailed=True)
            value = feed["details"]["data"]["last"]
            if value is not None:
                return value["value"]
            return None
        except (KeyError, TypeError):
            return None
        except Exception:
            self._trigger_circuit_breaker()
            return None
        finally:
            self.display_manager.show_connecting(False)

    async def _set_feed_value(self, feed_key: str, value: str | int) -> None:
        """Set the value of an Adafruit IO feed.

        :param feed_key: The feed key to set
        :param value: The value to set (string or int)
        """
        if self._is_circuit_breaker_open():
            return

        await asyncio.sleep(0)
        self.display_manager.show_connecting(True)
        try:
            self._matrixportal.push_to_io(feed_key, value)
        except Exception:
            self._trigger_circuit_breaker()
            raise
        finally:
            self.display_manager.show_connecting(False)

    async def get_left_team_name(self) -> str:
        if value := await self._get_feed_value(self.TEAM_LEFT_TEAM_FEED):
            return value
        return self.DEFAULT_LEFT_TEAM_NAME

    async def get_right_team_name(self) -> str:
        if value := await self._get_feed_value(self.TEAM_RIGHT_TEAM_FEED):
            return value
        return self.DEFAULT_RIGHT_TEAM_NAME
