"""Reports reboots, crashes, logs and heartbeat metrics to Memfault."""

from __future__ import annotations

import asyncio
import os
import time
import traceback

import ota_loader
from src.compat import TYPE_CHECKING, Callable
from src.log import WARNING, discard_lines, kept_lines, log
from src.memfault_chunks import (
    EVENT_CUSTOM_DATA_RECORDING,
    EVENT_HEARTBEAT,
    EVENT_LOGS,
    EVENT_REBOOT,
    HEARTBEAT_METRICS,
    MESSAGE_CUSTOM_DATA_RECORDING,
    MESSAGE_EVENT,
    MESSAGE_LOGS,
    REBOOT_ASSERT,
    REBOOT_REASON,
    REBOOT_REASON_LOG,
    RECORDING_DATA,
    RECORDING_DURATION_MS,
    RECORDING_MIMETYPES,
    RECORDING_REASON,
    chunk,
    event,
)
from src.protocols import HttpLike

if TYPE_CHECKING:
    from src.ota_manager import DeviceInfo

CHUNKS_URL = "https://chunks.memfault.com/api/v0/chunks/"
# Memfault keeps at most 100 heartbeats per device per day
HEARTBEAT_INTERVAL_S = 900
UPLOAD_TIMEOUT_S = 10
REBOOT_REASON_FILE = "reboot_reason"
CRASH_FILE = "crash.txt"
CRASH_UPLOAD_FILE = "crash_upload.txt"
MAX_PENDING_EVENTS = 8
MAX_RECORDING_REASON_LENGTH = 100


class Telemetry:
    """Uploads to Memfault as chunks, and keeps what fails to upload for the next flush."""

    def __init__(
        self,
        http: HttpLike,
        project_key: str,
        device: DeviceInfo,
        root: str,
        reboot_reason: int | None,
        read_metrics: Callable,
        monotonic: Callable = time.monotonic,
    ):
        """Initialize Telemetry, and queue the reboot and the crash from before this run.

        A crash stays on disk until it uploads.

        :param http: HTTP session that reaches Memfault
        :param project_key: Memfault project key
        :param device: Board and app identity
        :param root: Board filesystem root, ending in "/"
        :param reboot_reason: Memfault reboot reason from the hardware, or None
            when the app restarted without a reboot
        :param read_metrics: Returns a dict of int metrics for a heartbeat
        :param monotonic: Returns the time in seconds
        """
        self._http = http
        self._project_key = project_key
        self._device = device
        self._root = root
        self._read_metrics = read_metrics
        self._monotonic = monotonic
        self._last_heartbeat = monotonic()
        self._events: list = []

        saved_reason = _read_saved_reason(root + REBOOT_REASON_FILE)
        crashed = _move_file(root + CRASH_FILE, root + CRASH_UPLOAD_FILE)
        self._crash = _read_file(root + CRASH_UPLOAD_FILE)
        if reboot_reason is not None:
            info: dict = {REBOOT_REASON: reboot_reason}
            if crashed and self._crash:
                info[REBOOT_REASON] = REBOOT_ASSERT
                info[REBOOT_REASON_LOG] = _last_line(self._crash).encode()
            elif saved_reason is not None:
                info[REBOOT_REASON] = saved_reason
            self._queue(EVENT_REBOOT, info)

    def flush(self) -> None:
        """Upload the queued events, the crash, and the kept log lines."""
        if self._events and self._post(MESSAGE_EVENT, self._events):
            self._events = []
        if self._crash and self._post(MESSAGE_CUSTOM_DATA_RECORDING, self._recording()):
            self._crash = None
            ota_loader.remove_tree(self._root + CRASH_UPLOAD_FILE)
        lines = kept_lines()
        if lines:
            info = []
            for level, text in lines:
                info.append(level)
                info.append(text)
            if self._post(MESSAGE_LOGS, event(EVENT_LOGS, info, self._device)):
                discard_lines(len(lines))

    def send_heartbeat(self) -> None:
        """Queue a heartbeat with the metrics since the last one, then flush."""
        now = self._monotonic()
        metrics = self._read_metrics()
        metrics["MemfaultSdkMetric_IntervalMs"] = int(
            (now - self._last_heartbeat) * 1000
        )
        self._last_heartbeat = now
        self._queue(EVENT_HEARTBEAT, {HEARTBEAT_METRICS: metrics})
        self.flush()

    async def run(self, online: Callable) -> None:
        """Send a heartbeat each HEARTBEAT_INTERVAL_S while online() is true."""
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_S)
            if online():
                self.send_heartbeat()

    def prepare_reset(self, reason: int) -> None:
        """Save the reason for the reboot that follows, and upload the log lines."""
        try:
            with open(self._root + REBOOT_REASON_FILE, "w") as f:
                f.write(str(reason))
        except OSError as e:
            log(f"Failed to save the reboot reason: {e}", WARNING)
        self.flush()

    def _queue(self, event_type: int, event_info) -> None:
        self._events.append(event(event_type, event_info, self._device))
        del self._events[:-MAX_PENDING_EVENTS]

    def _recording(self) -> dict:
        crash = self._crash or b""
        info = {
            RECORDING_DURATION_MS: 0,
            RECORDING_MIMETYPES: ["text/plain"],
            RECORDING_REASON: _last_line(crash)[:MAX_RECORDING_REASON_LENGTH],
            RECORDING_DATA: crash,
        }
        return event(EVENT_CUSTOM_DATA_RECORDING, info, self._device)

    def _post(self, message_type: int, payload) -> bool:
        """Upload one chunk, and return True if Memfault accepted it."""
        try:
            response = self._http.post(
                CHUNKS_URL + self._device.serial,
                data=chunk(message_type, payload),
                headers={
                    "Memfault-Project-Key": self._project_key,
                    "Content-Type": "application/octet-stream",
                },
                timeout=UPLOAD_TIMEOUT_S,
            )
            try:
                status = response.status_code
            finally:
                response.close()
        except Exception as e:
            log(f"Telemetry upload failed: {e}", WARNING)
            return False
        if status != 202:
            log(f"Telemetry upload returned {status}", WARNING)
            return False
        return True


def save_crash(root: str, e: Exception) -> None:
    """Write the traceback of e to the crash file, which Telemetry reports on the next run."""
    try:
        with open(root + CRASH_FILE, "w") as f:
            traceback.print_exception(e, file=f)
    except Exception:
        pass


def _read_file(path: str) -> bytes | None:
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return None


def _move_file(source: str, destination: str) -> bool:
    """Replace destination with source, and return True if source existed."""
    try:
        os.stat(source)
    except OSError:
        return False
    try:
        ota_loader.remove_tree(destination)
        os.rename(source, destination)
    except OSError:
        return False
    return True


def _read_saved_reason(path: str) -> int | None:
    """Return the reason in the file and delete it, or None."""
    data = _read_file(path)
    if data is None:
        return None
    try:
        os.remove(path)
        return int(data.decode())
    except (OSError, ValueError, UnicodeError):
        return None


def _last_line(data: bytes) -> str:
    """Return the last line of text in data that is not blank."""
    try:
        text = data.decode()
    except UnicodeError:
        return ""
    for line in reversed(text.split("\n")):
        if line.strip():
            return line.strip()
    return ""
