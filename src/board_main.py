import asyncio
import binascii
import gc
import os
import time

import adafruit_requests
import board
import microcontroller
import supervisor
import wifi
from adafruit_connection_manager import get_radio_socketpool, get_radio_ssl_context
from adafruit_matrixportal.matrixportal import MatrixPortal

from src.app_setup import create_managers, initialize_application, run_tasks
from src.app_version import VERSION
from src.board_network import BoardNetwork
from src.game_controller import GameController
from src.hardware_manager import create_keys_from_board
from src.lab import request_lab, run_lab, take_lab_request
from src.log import log
from src.memfault_chunks import (
    REBOOT_BROWN_OUT,
    REBOOT_DEEP_SLEEP,
    REBOOT_FW_UPDATE,
    REBOOT_HARDWARE_WATCHDOG,
    REBOOT_PIN,
    REBOOT_POWER_ON,
    REBOOT_SOFTWARE,
    REBOOT_UNKNOWN,
)
from src.network_patches import apply_network_patches
from src.ota_manager import DeviceInfo, OtaManager
from src.telemetry import Telemetry, save_crash
from src.web_server import WebServer

HARDWARE_VERSION = "matrixportal-s3"
SOFTWARE_TYPE = "scoreboard"
ROOT = "/"


def hardware_reboot_reason() -> int | None:
    """Return the Memfault reason for the last reboot, or None after a reload without one."""
    if supervisor.runtime.run_reason != supervisor.RunReason.STARTUP:
        return None
    reason = microcontroller.cpu.reset_reason
    for board_reason, code in (
        (microcontroller.ResetReason.POWER_ON, REBOOT_POWER_ON),
        (microcontroller.ResetReason.BROWNOUT, REBOOT_BROWN_OUT),
        (microcontroller.ResetReason.SOFTWARE, REBOOT_SOFTWARE),
        (microcontroller.ResetReason.DEEP_SLEEP_ALARM, REBOOT_DEEP_SLEEP),
        (microcontroller.ResetReason.RESET_PIN, REBOOT_PIN),
        (microcontroller.ResetReason.WATCHDOG, REBOOT_HARDWARE_WATCHDOG),
    ):
        if reason == board_reason:
            return code
    return REBOOT_UNKNOWN


def read_metrics(game_controller: GameController) -> dict:
    """Return the heartbeat metrics."""
    metrics = {
        "free_memory": gc.mem_free(),  # pyrefly: ignore[missing-attribute]
        "uptime_s": int(time.monotonic()),
        "points_scored": game_controller.take_points_scored(),
    }
    ap_info = wifi.radio.ap_info
    if ap_info is not None:
        metrics["wifi_rssi"] = ap_info.rssi
    temperature = microcontroller.cpu.temperature
    if temperature is not None:
        metrics["cpu_temp_c"] = int(temperature)
    return metrics


def create_memfault(managers) -> tuple[Telemetry | None, OtaManager | None]:
    """Return Telemetry and an OtaManager.

    Both are None without a Memfault project key. The OtaManager is None for a dev build.
    """
    project_key = os.getenv("MEMFAULT_PROJECT_KEY")
    if not project_key:
        return None, None
    http = adafruit_requests.Session(
        get_radio_socketpool(wifi.radio),  # pyrefly: ignore[bad-argument-type]
        get_radio_ssl_context(wifi.radio),
    )
    device = DeviceInfo(
        serial=binascii.hexlify(microcontroller.cpu.uid).decode(),
        hardware_version=HARDWARE_VERSION,
        software_type=SOFTWARE_TYPE,
        software_version=VERSION,
    )
    telemetry = Telemetry(
        http,
        project_key,
        device,
        ROOT,
        hardware_reboot_reason(),
        lambda: read_metrics(managers.game_controller),
    )
    if VERSION == "dev":
        return telemetry, None

    def reset_for_update() -> None:
        telemetry.prepare_reset(REBOOT_FW_UPDATE)
        microcontroller.reset()

    ota_manager = OtaManager(
        http, project_key, device, managers.display_manager, ROOT, reset_for_update
    )
    return telemetry, ota_manager


async def enter_lab() -> None:
    request_lab(microcontroller.nvm)
    microcontroller.reset()


async def leave_lab() -> None:
    microcontroller.reset()


async def main():
    """Main application entry point with asyncio tasks."""
    log(f"Scoreboard {VERSION}")
    lab_mode = take_lab_request(microcontroller.nvm)

    # Initialize hardware
    matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)

    # Apply network patches for faster failure behavior
    apply_network_patches(matrixportal)

    # Create keys from board
    keys = create_keys_from_board(board)

    if lab_mode:
        await run_lab(
            matrixportal,
            keys,
            microcontroller.nvm,
            BoardNetwork(matrixportal.network),
            WebServer(),
            restart=leave_lab,
        )
        return

    # Initialize managers
    managers = create_managers(
        matrixportal,
        keys,
        microcontroller.nvm,
        BoardNetwork(matrixportal.network),
        WebServer(),
    )

    telemetry, ota_manager = create_memfault(managers)

    # Initialize application state
    initialize_application(managers, ota_manager, telemetry)

    if telemetry is None:
        await run_tasks(managers, enter_lab=enter_lab)
    else:
        await run_tasks(
            managers,
            telemetry.run(lambda: managers.network_manager.url is not None),
            enter_lab=enter_lab,
        )


def run():
    """Run the app, and save the traceback of a crash before it re-raises."""
    try:
        asyncio.run(main())
    except Exception as e:
        save_crash(ROOT, e)
        raise
