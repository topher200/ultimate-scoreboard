class ScoreManager:
    """Manages score state and fetching from Adafruit IO feeds."""

    def __init__(self, matrixportal, left_feed_key, right_feed_key):
        """Initialize ScoreManager with MatrixPortal and feed keys.

        :param matrixportal: MatrixPortal instance for fetching data
        :param left_feed_key: Feed key for left team score
        :param right_feed_key: Feed key for right team score
        """
        self._matrixportal = matrixportal
        self._left_feed_key = left_feed_key
        self._right_feed_key = right_feed_key
        self.left_score = None
        self.right_score = None

    def _get_last_data(self, feed_key):
        """Fetch the last value from an Adafruit IO feed.

        :param feed_key: The feed key to fetch from
        :return: The last value from the feed, or None if not available
        """
        feed = self._matrixportal.get_io_feed(feed_key, detailed=True)
        value = feed["details"]["data"]["last"]
        if value is not None:
            return value["value"]
        return None

    def update_scores(self):
        """Fetch latest scores from Adafruit IO and update internal state.

        :return: True if either score has changed, False otherwise
        """
        score_left = self._get_last_data(self._left_feed_key)
        if score_left is None:
            score_left = 0

        score_right = self._get_last_data(self._right_feed_key)
        if score_right is None:
            score_right = 0

        previous_left_score = self.left_score
        previous_right_score = self.right_score
        self.left_score = score_left
        self.right_score = score_right

        if previous_left_score is None and previous_right_score is None:
            return False

        left_changed = (
            previous_left_score is not None
            and self.left_score != previous_left_score
        )
        right_changed = (
            previous_right_score is not None
            and self.right_score != previous_right_score
        )

        return left_changed or right_changed

