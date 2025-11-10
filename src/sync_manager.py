"""Base class for managers that sync state with network.

We use this to prioritize local state changes until we can sync to the network.
We keep track of pending changes and refuse to allow updates from the network
until we can sync the pending changes.
"""

from .compat import ABC, abstractmethod


class SyncManager(ABC):
    """Abstract base class for managing state sync.

    Provides common infrastructure for tracking pending changes.
    Subclasses implement domain-specific sync logic.
    """

    def __init__(self):
        """Initialize SyncManager with common sync state."""
        self._has_pending_sync = False

    def has_pending_changes(self) -> bool:
        """Check if there are pending local changes to sync.

        :return: True if changes need to be synced
        """
        return self._has_pending_sync

    def _mark_pending(self) -> None:
        """Mark that there are pending changes to sync."""
        self._has_pending_sync = True

    async def _try_sync_with_backoff(self) -> bool:
        """Attempt to sync pending changes.

        Calls abstract _perform_sync() method for actual sync logic.

        :return: True if sync was successful, False otherwise
        """
        try:
            await self._perform_sync()
            self._has_pending_sync = False
            return True
        except Exception as e:
            print(f"Sync failed: {e}")
            return False

    @abstractmethod
    async def _perform_sync(self) -> None:
        """Perform the actual sync operation.

        Subclasses implement this method with their specific sync logic.
        This method should sync local state to network.
        """
        pass
