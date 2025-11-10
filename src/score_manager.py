import asyncio

from src.network_manager import NetworkManager
from src.sync_manager import SyncManager


class ScoreManager(SyncManager):
    """Manages score state with async network sync."""

    def __init__(self, network_manager: NetworkManager):
        """Initialize ScoreManager with NetworkManager.

        :param network_manager: NetworkManager instance for fetching data
        """
        super().__init__()
        self._network_manager = network_manager
        self.left_score: int = 0
        self.right_score: int = 0
        self._last_synced_left = 0
        self._last_synced_right = 0

    async def _perform_sync(self) -> None:
        """Perform sync of scores to network.

        Syncs left and right scores if they have changed.
        """
        if self.left_score != self._last_synced_left:
            await self._network_manager.set_left_team_score(self.left_score)
            self._last_synced_left = self.left_score

        await asyncio.sleep(0)

        if self.right_score != self._last_synced_right:
            await self._network_manager.set_right_team_score(self.right_score)
            self._last_synced_right = self.right_score

    async def try_sync_scores(self) -> bool:
        """Attempt to sync local scores to network.

        :return: True if sync was successful, False otherwise
        """
        return await self._try_sync_with_backoff()

    async def update_scores_from_network(self):
        """Fetch latest scores from Adafruit IO and update internal state.

        Will skip network fetch if there are pending local changes to sync.

        :return: True if either score has changed, False otherwise
        """
        if self._has_pending_sync:
            if not await self.try_sync_scores():
                print("Skipping network update - local changes pending")
                return False

        score_left = await self._network_manager.get_left_team_score()
        if score_left is None:
            print("No left score from network")
            return False
        await asyncio.sleep(0)
        score_right = await self._network_manager.get_right_team_score()
        if score_right is None:
            print("No right score from network")
            return False
        await asyncio.sleep(0)

        if self._has_pending_sync:
            print(
                "Received a local update while pulling the network update, skipping network update"
            )
            return False

        previous_left_score = self.left_score
        previous_right_score = self.right_score
        self.left_score = score_left
        self.right_score = score_right
        self._last_synced_left = score_left
        self._last_synced_right = score_right

        left_changed = self.left_score != previous_left_score
        if left_changed:
            print(
                f"Left score from network: {previous_left_score} -> {self.left_score}"
            )
        right_changed = self.right_score != previous_right_score
        if right_changed:
            print(
                f"Right score from network: {previous_right_score} -> {self.right_score}"
            )
        return left_changed or right_changed

    def increment_left_score(self) -> None:
        """Increment left team score by 1 and mark for network sync."""
        self.left_score += 1
        self._mark_pending()

    def increment_right_score(self) -> None:
        """Increment right team score by 1 and mark for network sync."""
        self.right_score += 1
        self._mark_pending()
