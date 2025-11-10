from src.network_manager import NetworkManager
from src.sync_manager import SyncManager


class GenderManager(SyncManager):
    """Manages first point gender state with async network sync and exponential backoff."""

    # Gender constants
    GENDER_WMP = "WMP"
    GENDER_MMP = "MMP"
    DEFAULT_GENDER = GENDER_WMP

    def __init__(self, network_manager: NetworkManager):
        """Initialize GenderManager with NetworkManager.

        :param network_manager: NetworkManager instance for fetching data
        """
        super().__init__()
        self._network_manager = network_manager
        self._local_first_point_gender: str = self.DEFAULT_GENDER
        self._network_first_point_gender: str = self.DEFAULT_GENDER

    def get_first_point_gender(self) -> str:
        """Get the current first point gender (local value, trusted until sync).

        :return: Gender constant (GENDER_WMP or GENDER_MMP)
        """
        return self._local_first_point_gender

    def toggle_first_point_gender(self) -> None:
        """Toggle the first point gender between MMP and WMP and mark for sync."""
        if self._local_first_point_gender == self.GENDER_WMP:
            self._local_first_point_gender = self.GENDER_MMP
        else:
            self._local_first_point_gender = self.GENDER_WMP
        self._mark_pending()

    async def _perform_sync(self) -> None:
        """Perform sync of gender to network.

        Syncs gender if it has changed.
        """
        if self._local_first_point_gender != self._network_first_point_gender:
            await self._network_manager.set_first_point_gender(
                self._local_first_point_gender
            )
            self._network_first_point_gender = self._local_first_point_gender

    async def try_sync_gender(self) -> bool:
        """Attempt to sync local gender to network with exponential backoff.

        :return: True if sync was successful, False otherwise
        """
        return await self._try_sync_with_backoff()

    async def update_gender_from_network(self) -> bool:
        """Fetch latest gender from Adafruit IO and update internal state.

        Will skip network fetch if there are pending local changes to sync.

        :return: True if gender has changed, False otherwise
        """
        if self._has_pending_sync:
            if not await self.try_sync_gender():
                print("Skipping network gender update - local changes pending")
                return False

        network_gender = await self._network_manager.get_first_point_gender()

        previous_gender = self._local_first_point_gender
        self._local_first_point_gender = network_gender
        self._network_first_point_gender = network_gender

        return self._local_first_point_gender != previous_gender
