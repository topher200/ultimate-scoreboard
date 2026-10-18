"""Type stubs for CircuitPython supervisor module."""

class SafeModeReason:
    BROWNOUT: SafeModeReason
    USER: SafeModeReason
    PROGRAMMATIC: SafeModeReason

class Runtime:
    safe_mode_reason: SafeModeReason

runtime: Runtime
