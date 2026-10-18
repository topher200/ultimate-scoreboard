"""Rolls back an OTA slot in trial after a hard crash, then restarts the board."""

import microcontroller
import storage
import supervisor

import ota_loader

ROOT = "/"
IGNORED_REASONS = (
    supervisor.SafeModeReason.BROWNOUT,
    supervisor.SafeModeReason.USER,
    supervisor.SafeModeReason.PROGRAMMATIC,
)

if supervisor.runtime.safe_mode_reason not in IGNORED_REASONS and ota_loader.in_trial(
    ROOT
):
    try:
        storage.remount("/", readonly=False)
        rolled_back = ota_loader.roll_back_trial(ROOT)
    except (OSError, RuntimeError) as e:
        print(f"Could not roll back: {e}")
        rolled_back = False
    if rolled_back:
        microcontroller.reset()
