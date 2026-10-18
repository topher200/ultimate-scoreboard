"""Type stubs for CircuitPython microcontroller module.

Only available on CircuitPython hardware.
"""

class ResetReason:
    POWER_ON: ResetReason
    BROWNOUT: ResetReason
    SOFTWARE: ResetReason
    DEEP_SLEEP_ALARM: ResetReason
    RESET_PIN: ResetReason
    WATCHDOG: ResetReason
    UNKNOWN: ResetReason
    RESCUE_DEBUG: ResetReason

class Processor:
    uid: bytearray
    reset_reason: ResetReason
    temperature: float | None

cpu: Processor
nvm: bytearray

def reset() -> None: ...
