"""Shared application setup functions for src/board_main.py and local_main.py."""

import asyncio

from src.compat import Callable, NamedTuple
from src.display_manager import DisplayManager
from src.game_controller import GameController
from src.gender_manager import GenderManager
from src.hardware_manager import (
    BUTTON_LEFT,
    BUTTON_RIGHT,
    HardwareManager,
)
from src.network_manager import NetworkManager
from src.score_manager import ScoreManager
from src.settings_page import SettingsPage
from src.settings_store import SettingsStore
from src.timing_indicator import (
    TIMING_INDICATOR_PIXEL_COUNT,
    TIMING_INDICATOR_REMOVAL_INTERVAL,
    TimingIndicatorManager,
)


class Managers(NamedTuple):
    """Container for all application managers."""

    display_manager: DisplayManager
    network_manager: NetworkManager
    score_manager: ScoreManager
    gender_manager: GenderManager
    timing_indicator_manager: TimingIndicatorManager
    hardware_manager: HardwareManager
    game_controller: GameController
    settings_store: SettingsStore


def create_managers(matrixportal, keys, nvm, network, web_server) -> Managers:
    """Initialize all application managers.

    :param matrixportal: MatrixPortal instance (real or simulator)
    :param keys: Keys instance (real or fake) for button input
    :param nvm: Byte buffer that keeps settings across reboots
    :param network: Network that joins Wi-Fi (real or simulator)
    :param web_server: Server for the settings page (real or simulator)
    :return: Managers named tuple containing all initialized managers
    """
    display_manager = DisplayManager(matrixportal)
    settings_store = SettingsStore(nvm)

    def on_settings_saved(settings: dict) -> None:
        game_controller.apply_settings(settings)
        display_manager.hide_qr_code()

    network_manager = NetworkManager(
        network,
        display_manager,
        web_server,
        SettingsPage(settings_store, on_settings_saved).respond,
    )
    score_manager = ScoreManager()
    gender_manager = GenderManager()
    timing_indicator_manager = TimingIndicatorManager(
        max_dots=TIMING_INDICATOR_PIXEL_COUNT,
        removal_interval=TIMING_INDICATOR_REMOVAL_INTERVAL,
    )
    hardware_manager = HardwareManager(keys=keys)
    game_controller = GameController(
        score_manager,
        display_manager,
        network_manager,
        gender_manager,
        timing_indicator_manager,
    )

    return Managers(
        display_manager=display_manager,
        network_manager=network_manager,
        score_manager=score_manager,
        gender_manager=gender_manager,
        timing_indicator_manager=timing_indicator_manager,
        hardware_manager=hardware_manager,
        game_controller=game_controller,
        settings_store=settings_store,
    )


def initialize_application(
    managers: Managers, ota_manager=None, telemetry=None
) -> None:
    """Show the saved team names and the scores, join Wi-Fi, then report and install any update.

    :param managers: Managers from create_managers
    :param ota_manager: OtaManager that checks for an update once Wi-Fi joins,
        or None to skip the check
    :param telemetry: Telemetry that uploads once Wi-Fi joins, or None to skip the upload
    """
    managers.game_controller.apply_settings(managers.settings_store.load())
    managers.game_controller.initialize_scores()
    managers.network_manager.connect()
    if managers.network_manager.url is None:
        return
    if telemetry is not None:
        telemetry.flush()
    if ota_manager is not None:
        ota_manager.check_and_install()


def create_button_callbacks(game_controller: GameController) -> dict[str, Callable]:
    """Create button callback mapping for hardware manager.

    Individual button callbacks fire on release if no chord was detected.

    :param game_controller: GameController instance
    :return: Dictionary mapping button names to callback functions
    """
    return {
        BUTTON_LEFT: game_controller.handle_left_score_button,
        BUTTON_RIGHT: game_controller.handle_right_score_button,
    }


def create_chord_callbacks(
    game_controller: GameController,
) -> dict[tuple[str, str], Callable]:
    """Create chord callback mapping for hardware manager.

    Chords fire when one button is held and the other is tapped:
    - Hold LEFT, tap RIGHT → toggle gender matchup and retry joining Wi-Fi
    - Hold RIGHT, tap LEFT → undo last point

    :param game_controller: GameController instance
    :return: Dictionary mapping (held_button, tapped_button) to callback functions
    """
    return {
        (BUTTON_LEFT, BUTTON_RIGHT): game_controller.handle_toggle_gender_button,
        (BUTTON_RIGHT, BUTTON_LEFT): game_controller.handle_undo_button,
    }


def dismiss_qr_code_first(display_manager: DisplayManager, callback: Callable):
    """Wrap a button callback so that, while the QR code shows, it only hides the QR code.

    :param display_manager: DisplayManager that shows the QR code
    :param callback: Async button callback to wrap
    :return: The wrapped callback
    """

    async def wrapped() -> None:
        if display_manager.qr_code_shown:
            display_manager.hide_qr_code()
            return
        await callback()

    return wrapped


async def run_tasks(managers: Managers, *extra_tasks, enter_lab=None) -> None:
    """Run the button monitor, the timing indicator, the settings page, and any extra tasks.

    :param managers: Managers from create_managers
    :param extra_tasks: Additional coroutines to run alongside
    :param enter_lab: Optional async callback for holding both buttons longer
    """
    display_manager = managers.display_manager
    game_controller = managers.game_controller
    await asyncio.gather(
        managers.hardware_manager.monitor_buttons(
            {
                button: dismiss_qr_code_first(display_manager, callback)
                for button, callback in create_button_callbacks(game_controller).items()
            },
            hold_both_callback=dismiss_qr_code_first(
                display_manager, game_controller.handle_reset_button
            ),
            chord_callbacks={
                chord: dismiss_qr_code_first(display_manager, callback)
                for chord, callback in create_chord_callbacks(game_controller).items()
            },
            long_hold_both_callback=enter_lab,
        ),
        managers.network_manager.serve(),
        create_timing_indicator_task(
            managers.timing_indicator_manager, managers.display_manager
        ),
        animate_wmp_frame(managers.display_manager),
        *extra_tasks,
    )


async def create_timing_indicator_task(
    timing_indicator_manager: TimingIndicatorManager, display_manager: DisplayManager
) -> None:
    """Create and run the timing indicator task.

    Periodically removes dots from timing indicator.

    :param timing_indicator_manager: TimingIndicatorManager instance
    :param display_manager: DisplayManager instance
    """
    POLLING_INTERVAL = 0.1
    while True:
        if timing_indicator_manager.remove_due_dots():
            display_manager.update_timing_indicator(
                timing_indicator_manager.get_dot_count()
            )
        await asyncio.sleep(POLLING_INTERVAL)


async def animate_wmp_frame(display_manager: DisplayManager) -> None:
    """Animate the WMP frame."""
    while True:
        display_manager.animate_wmp_frame()
        await asyncio.sleep(0.05)
