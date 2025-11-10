"""Base class for managers that sync state with network.

We use this to prioritize local state changes until we can sync to the network.
We keep track of pending changes and refuse to allow updates from the network
until we can sync the pending changes. We use exponential backoff to retry sync
attempts.
"""

import time

from .compat import ABC, abstractmethod


class SyncManager(ABC):
    """Abstract base class for managing state sync with exponential backoff.

    Provides common infrastructure for tracking pending changes, retry delays,
    and exponential backoff logic. Subclasses implement domain-specific sync logic.
    """

    MIN_RETRY_DELAY = 1.0
    MAX_RETRY_DELAY = 60.0

    def __init__(self):
        """Initialize SyncManager with common sync state."""
        self._has_pending_sync = False
        self._sync_retry_delay = self.MIN_RETRY_DELAY
        self._last_sync_attempt = 0.0

    def has_pending_changes(self) -> bool:
        """Check if there are pending local changes to sync.

        :return: True if changes need to be synced
        """
        return self._has_pending_sync

    def get_next_retry_delay(self) -> float:
        """Get the delay before next sync retry attempt.

        :return: Delay in seconds
        """
        return self._sync_retry_delay

    def reset_sync_timing(self) -> None:
        """Reset sync timing to allow immediate sync attempts.

        Primarily intended for testing purposes to bypass timing restrictions.
        """
        self._last_sync_attempt = 0.0

    def _mark_pending(self) -> None:
        """Mark that there are pending changes to sync."""
        self._has_pending_sync = True

    async def _try_sync_with_backoff(self) -> bool:
        """Attempt to sync with exponential backoff infrastructure.

        Handles time-based retry delay checks and exponential backoff.
        Calls abstract _perform_sync() method for actual sync logic.

        :return: True if sync was successful, False otherwise
        """
        current_time = time.monotonic()
        if current_time - self._last_sync_attempt < self._sync_retry_delay:
            return False

        self._last_sync_attempt = current_time

        try:
            await self._perform_sync()
            self._has_pending_sync = False
            self._sync_retry_delay = self.MIN_RETRY_DELAY
            return True
        except Exception as e:
            print(f"Sync failed: {e}")
            self._sync_retry_delay = min(
                self._sync_retry_delay * 2, self.MAX_RETRY_DELAY
            )
            return False

    @abstractmethod
    async def _perform_sync(self) -> None:
        """Perform the actual sync operation.

        Subclasses implement this method with their specific sync logic.
        This method should sync local state to network.
        """
        pass
