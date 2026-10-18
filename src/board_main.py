import asyncio
import binascii
import os

import adafruit_requests
import board
import microcontroller
import wifi
from adafruit_connection_manager import get_radio_socketpool, get_radio_ssl_context
from adafruit_matrixportal.matrixportal import MatrixPortal

from src.app_setup import create_managers, initialize_application, run_tasks
from src.board_network import BoardNetwork
from src.hardware_manager import create_keys_from_board
from src.lab import request_lab, run_lab, take_lab_request
from src.network_patches import apply_network_patches
from src.ota_manager import DeviceInfo, OtaManager
from src.web_server import WebServer

try:
    from src.version import VERSION  # pyrefly: ignore[missing-import]
except ImportError:
    VERSION = "dev"

HARDWARE_VERSION = "matrixportal-s3"
SOFTWARE_TYPE = "scoreboard"
ROOT = "/"


def create_ota_manager(display_manager) -> OtaManager | None:
    """Return an OtaManager, or None for a dev build or without a Memfault project key."""
    project_key = os.getenv("MEMFAULT_PROJECT_KEY")
    if not project_key or VERSION == "dev":
        return None
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
    return OtaManager(
        http, project_key, device, display_manager, ROOT, microcontroller.reset
    )


async def enter_lab() -> None:
    request_lab(microcontroller.nvm)
    microcontroller.reset()


async def leave_lab() -> None:
    microcontroller.reset()


async def main():
    """Main application entry point with asyncio tasks."""
    print(f"Scoreboard {VERSION}")
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

    # Initialize application state
    initialize_application(managers, create_ota_manager(managers.display_manager))

    await run_tasks(managers, enter_lab=enter_lab)


def run():
    asyncio.run(main())
