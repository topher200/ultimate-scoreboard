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
    SCORES_LEFT_TEAM_FEED = "scores-group.left-team-score-feed"
    SCORES_RIGHT_TEAM_FEED = "scores-group.right-team-score-feed"
    TEAM_LEFT_TEAM_FEED = "scores-group.left-team-name"
    TEAM_RIGHT_TEAM_FEED = "scores-group.right-team-name"
    FIRST_POINT_GENDER_FEED = "scores-group.first-point-gender"

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

    async def get_left_team_score(self) -> int:
        if value := await self._get_feed_value(self.SCORES_LEFT_TEAM_FEED):
            return int(value)
        return 0

    async def get_right_team_score(self) -> int:
        if value := await self._get_feed_value(self.SCORES_RIGHT_TEAM_FEED):
            return int(value)
        return 0

    async def get_left_team_name(self) -> str:
        if value := await self._get_feed_value(self.TEAM_LEFT_TEAM_FEED):
            return value
        return self.DEFAULT_LEFT_TEAM_NAME

    async def get_right_team_name(self) -> str:
        if value := await self._get_feed_value(self.TEAM_RIGHT_TEAM_FEED):
            return value
        return self.DEFAULT_RIGHT_TEAM_NAME

    async def set_left_team_score(self, score: int) -> None:
        """Set the left team score on Adafruit IO.

        :param score: The score value to set
        """
        await self._set_feed_value(self.SCORES_LEFT_TEAM_FEED, score)

    async def set_right_team_score(self, score: int) -> None:
        """Set the right team score on Adafruit IO.

        :param score: The score value to set
        """
        await self._set_feed_value(self.SCORES_RIGHT_TEAM_FEED, score)

    async def get_first_point_gender(self) -> str:
        """Get the first point gender from Adafruit IO feed.

        Returns uppercase gender constant (WMP or MMP).
        Accepts case-insensitive input from network (mmp/wmp/MMP/WMP).

        :return: Gender constant (GenderManager.GENDER_WMP or GenderManager.GENDER_MMP)
        """
        from src.gender_manager import GenderManager

        if value := await self._get_feed_value(self.FIRST_POINT_GENDER_FEED):
            normalized = value.upper()
            if normalized in {GenderManager.GENDER_MMP, GenderManager.GENDER_WMP}:
                return normalized
        return GenderManager.DEFAULT_GENDER

    async def set_first_point_gender(self, value: str) -> None:
        """Set the first point gender on Adafruit IO.

        Accepts gender constant (WMP or MMP) and stores as uppercase string.

        :param value: The gender value to set (GenderManager.GENDER_WMP or GenderManager.GENDER_MMP)
        """
        from src.gender_manager import GenderManager

        if value not in {GenderManager.GENDER_MMP, GenderManager.GENDER_WMP}:
            raise ValueError(
                f"Invalid gender value: {value}. "
                f"Must be '{GenderManager.GENDER_WMP}' or '{GenderManager.GENDER_MMP}'"
            )
        await self._set_feed_value(self.FIRST_POINT_GENDER_FEED, value)
