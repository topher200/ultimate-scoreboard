"""Installs app updates that Memfault releases."""

from __future__ import annotations

import ota_loader
from src.bundle import unpack, verify
from src.compat import TYPE_CHECKING, Callable
from src.protocols import HttpLike

if TYPE_CHECKING:
    from src.display_manager import DisplayManager

LATEST_URL = "https://device.memfault.com/api/v0/releases/latest"
DOWNLOAD_CHUNK_SIZE = 1024


class DeviceInfo:
    """Identifies the board and the app it runs to Memfault."""

    def __init__(
        self,
        serial: str,
        hardware_version: str,
        software_type: str,
        software_version: str,
    ):
        self.serial = serial
        self.hardware_version = hardware_version
        self.software_type = software_type
        self.software_version = software_version


class OtaManager:
    """Asks Memfault for a newer release and installs it into the inactive slot."""

    def __init__(
        self,
        http: HttpLike,
        project_key: str,
        device: DeviceInfo,
        display_manager: DisplayManager,
        root: str,
        reset: Callable,
    ):
        """Initialize OtaManager.

        :param http: HTTP session that reaches Memfault and the download URL
        :param project_key: Memfault project key
        :param device: Board and app identity
        :param display_manager: DisplayManager for the update screen
        :param root: Board filesystem root, ending in "/"
        :param reset: Restarts the board
        """
        self._http = http
        self._project_key = project_key
        self._device = device
        self._display_manager = display_manager
        self._root = root
        self._reset = reset

    def check_and_install(self) -> None:
        """Install the newer release, if there is one, and restart the board.

        A successful check-in ends the trial of a newly installed release. The
        board skips a release that crashed during its trial.
        """
        try:
            release = self._latest_release()
            ota_loader.mark_healthy(self._root)
        except Exception as e:
            print(f"Update check failed: {e}")
            return
        if release is None:
            print(f"Software {self._device.software_version} is up to date")
            return
        version, url = release
        if version == ota_loader.rolled_back_version(self._root):
            print(f"Skipping {version}, which crashed during its trial")
            return
        self._display_manager.show_update_notice()
        try:
            self._install(version, url)
        except Exception as e:
            print(f"Update failed: {e}")
            self._display_manager.hide_update_notice()
            return
        self._reset()

    def _latest_release(self) -> tuple[str, str] | None:
        """Return the version and download URL of a newer release, or None."""
        device = self._device
        query = "&".join(
            f"{name}={value}"
            for name, value in (
                ("device_serial", device.serial),
                ("hardware_version", device.hardware_version),
                ("software_type", device.software_type),
                ("current_version", device.software_version),
            )
        )
        response = self._http.get(
            f"{LATEST_URL}?{query}",
            headers={"Memfault-Project-Key": self._project_key},
        )
        try:
            if response.status_code == 204:
                return None
            if response.status_code != 200:
                raise OSError(f"Memfault returned {response.status_code}")
            release = response.json()
            return release["version"], release["artifacts"][0]["url"]
        finally:
            response.close()

    def _install(self, version: str, url: str) -> None:
        slot = ota_loader.inactive_slot(self._root)
        slot_dir = ota_loader.slot_path(self._root, slot)
        bundle_path = slot_dir + ".bundle"
        ota_loader.make_dirs(ota_loader.slot_path(self._root, ""))
        print(f"Downloading the update into slot {slot}")
        response = self._http.get(url)
        try:
            if response.status_code != 200:
                raise OSError(f"Download returned {response.status_code}")
            with open(bundle_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    f.write(chunk)
        finally:
            response.close()
        try:
            verify(bundle_path)
            ota_loader.remove_tree(slot_dir)
            unpack(bundle_path, slot_dir)
        finally:
            ota_loader.remove_tree(bundle_path)
        ota_loader.start_trial(self._root, slot, version)
