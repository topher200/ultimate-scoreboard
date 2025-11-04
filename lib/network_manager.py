"""Manages network interactions with Adafruit IO feeds."""

from __future__ import annotations


class NetworkManager:
    """Manages fetching data from Adafruit IO feeds."""

    # Feed key constants
    SCORES_LEFT_TEAM_FEED = "scores-group.red-team-score-feed"
    SCORES_RIGHT_TEAM_FEED = "scores-group.blue-team-score-feed"
    TEAM_LEFT_TEAM_FEED = "scores-group.red-team-name"
    TEAM_RIGHT_TEAM_FEED = "scores-group.blue-team-name"

    DEFAULT_LEFT_TEAM_NAME = "Red"
    DEFAULT_RIGHT_TEAM_NAME = "Blue"

    def __init__(self, matrixportal):
        """Initialize NetworkManager with MatrixPortal.

        :param matrixportal: MatrixPortal instance for network operations
        """
        self._matrixportal = matrixportal

    def _get_feed_value(self, feed_key: str) -> None | str:
        """Fetch the last value from an Adafruit IO feed.

        :param feed_key: The feed key to fetch from
        :return: The last value from the feed, or None if not available
        """
        try:
            feed = self._matrixportal.get_io_feed(feed_key, detailed=True)
            value = feed["details"]["data"]["last"]
            if value is not None:
                return value["value"]
            return None
        except (KeyError, TypeError):
            return None

    def get_left_team_score(self) -> int:
        if value := self._get_feed_value(self.SCORES_LEFT_TEAM_FEED):
            return int(value)
        return 0

    def get_right_team_score(self) -> int:
        if value := self._get_feed_value(self.SCORES_RIGHT_TEAM_FEED):
            return int(value)
        return 0

    def get_left_team_name(self) -> str:
        if value := self._get_feed_value(self.TEAM_LEFT_TEAM_FEED):
            return value
        return self.DEFAULT_LEFT_TEAM_NAME

    def get_right_team_name(self) -> str:
        if value := self._get_feed_value(self.TEAM_RIGHT_TEAM_FEED):
            return value
        return self.DEFAULT_RIGHT_TEAM_NAME

    def set_left_team_score(self, score: int) -> None:
        """Set the left team score on Adafruit IO.

        :param score: The score value to set
        """
        self._matrixportal.push_to_io(self.SCORES_LEFT_TEAM_FEED, score)

    def set_right_team_score(self, score: int) -> None:
        """Set the right team score on Adafruit IO.

        :param score: The score value to set
        """
        self._matrixportal.push_to_io(self.SCORES_RIGHT_TEAM_FEED, score)
