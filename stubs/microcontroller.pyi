"""Type stubs for CircuitPython microcontroller module.

Only available on CircuitPython hardware.
"""

class Processor:
    uid: bytearray

cpu: Processor
nvm: bytearray

def reset() -> None: ...
