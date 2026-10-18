"""Type stubs for CircuitPython supervisor module."""

class SafeModeReason:
    BROWNOUT: SafeModeReason
    USER: SafeModeReason
    PROGRAMMATIC: SafeModeReason

class RunReason:
    STARTUP: RunReason
    AUTO_RELOAD: RunReason
    SUPERVISOR_RELOAD: RunReason
    REPL_RELOAD: RunReason

class Runtime:
    safe_mode_reason: SafeModeReason
    run_reason: RunReason

runtime: Runtime
