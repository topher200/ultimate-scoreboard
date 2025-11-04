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

    def increment_left_score(self) -> bool:
        """Increment left team score by 1 and push to network.

        :return: True if score was successfully updated
        """
        self.left_score += 1

        try:
            self._network_manager.set_left_team_score(self.left_score)
            return True
        except Exception as e:
            print(f"Error updating left score: {e}")
            return False

    def increment_right_score(self) -> bool:
        """Increment right team score by 1 and push to network.

        :return: True if score was successfully updated
        """
        self.right_score += 1

        try:
            self._network_manager.set_right_team_score(self.right_score)
            return True
        except Exception as e:
            print(f"Error updating right score: {e}")
            return False
