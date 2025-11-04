class ScoreManager:
    """Manages score state."""

    def __init__(self, network_manager):
        """Initialize ScoreManager with NetworkManager.

        :param network_manager: NetworkManager instance for fetching data
        """
        self._network_manager = network_manager
        self.left_score = None
        self.right_score = None

    def update_scores(self):
        """Fetch latest scores from Adafruit IO and update internal state.

        :return: True if either score has changed, False otherwise
        """
        score_left = self._network_manager.get_left_team_score()
        if score_left is None:
            score_left = 0

        score_right = self._network_manager.get_right_team_score()
        if score_right is None:
            score_right = 0

        previous_left_score = self.left_score
        previous_right_score = self.right_score
        self.left_score = score_left
        self.right_score = score_right

        if previous_left_score is None and previous_right_score is None:
            return False

        left_changed = (
            previous_left_score is not None and self.left_score != previous_left_score
        )
        right_changed = (
            previous_right_score is not None
            and self.right_score != previous_right_score
        )

        return left_changed or right_changed
