from lib.network_manager import NetworkManager


class ScoreManager:
    """Manages score state."""

    def __init__(self, network_manager: NetworkManager):
        """Initialize ScoreManager with NetworkManager.

        :param network_manager: NetworkManager instance for fetching data
        """
        self._network_manager = network_manager
        self.left_score: int = 0
        self.right_score: int = 0

    def update_scores(self):
        """Fetch latest scores from Adafruit IO and update internal state.

        :return: True if either score has changed, False otherwise
        """
        score_left = self._network_manager.get_left_team_score()
        score_right = self._network_manager.get_right_team_score()

        previous_left_score = self.left_score
        previous_right_score = self.right_score
        self.left_score = score_left
        self.right_score = score_right

        left_changed = self.left_score != previous_left_score
        right_changed = self.right_score != previous_right_score
        return left_changed or right_changed

    def increment_left_score(self) -> None:
        """Increment left team score by 1 and push to network."""
        self.left_score += 1

        try:
            self._network_manager.set_left_team_score(self.left_score)
        except Exception as e:
            print(f"Error updating left score: {e}")

    def increment_right_score(self) -> None:
        """Increment right team score by 1 and push to network."""
        self.right_score += 1

        try:
            self._network_manager.set_right_team_score(self.right_score)
        except Exception as e:
            print(f"Error updating right score: {e}")
