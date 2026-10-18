"""Encodes events as Memfault chunks, which the board uploads to Memfault."""

from __future__ import annotations

from src.compat import TYPE_CHECKING

if TYPE_CHECKING:
    from src.ota_manager import DeviceInfo

MESSAGE_EVENT = 0x02
MESSAGE_LOGS = 0x03
MESSAGE_CUSTOM_DATA_RECORDING = 0x04

EVENT_HEARTBEAT = 1
EVENT_REBOOT = 2
EVENT_LOGS = 4
EVENT_CUSTOM_DATA_RECORDING = 5

REBOOT_UNKNOWN = 0x0000
REBOOT_FW_UPDATE = 0x0003
REBOOT_POWER_ON = 0x0007
REBOOT_SOFTWARE = 0x0008
REBOOT_DEEP_SLEEP = 0x0009
REBOOT_PIN = 0x000A
REBOOT_ASSERT = 0x8001
REBOOT_BROWN_OUT = 0x8003
REBOOT_HARDWARE_WATCHDOG = 0x8005

REBOOT_REASON = 1
REBOOT_REASON_LOG = 8

HEARTBEAT_METRICS = 1

RECORDING_DURATION_MS = 1
RECORDING_MIMETYPES = 2
RECORDING_REASON = 3
RECORDING_DATA = 4

_EVENT_CAPTURE_TYPE = 2
_EVENT_SCHEMA_VERSION = 3
_EVENT_INFO = 4
_EVENT_HARDWARE_VERSION = 6
_EVENT_SOFTWARE_VERSION = 9
_EVENT_SOFTWARE_TYPE = 10

_CHUNK_HEADER = 0x08


def event(event_type: int, event_info, device: DeviceInfo) -> dict:
    """Return the event map for one event from the device."""
    return {
        _EVENT_CAPTURE_TYPE: event_type,
        _EVENT_SCHEMA_VERSION: 1,
        _EVENT_SOFTWARE_TYPE: device.software_type,
        _EVENT_SOFTWARE_VERSION: device.software_version,
        _EVENT_HARDWARE_VERSION: device.hardware_version,
        _EVENT_INFO: event_info,
    }


def chunk(message_type: int, payload) -> bytes:
    """Return one chunk that holds a message.

    :param message_type: MESSAGE_EVENT with an event map or a list of them, or
        MESSAGE_LOGS or MESSAGE_CUSTOM_DATA_RECORDING with one event map
    :param payload: The event map or list
    """
    message = bytes((message_type,)) + cbor(payload)
    return bytes((_CHUNK_HEADER,)) + message + crc16(message).to_bytes(2, "little")


def cbor(value) -> bytes:
    """Encode ints, strings, bytes, lists and dicts as CBOR."""
    out = bytearray()
    _encode(value, out)
    return bytes(out)


def crc16(data: bytes) -> int:
    """Return the CRC-16/XMODEM of data."""
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else crc << 1
            crc &= 0xFFFF
    return crc


def _encode(value, out: bytearray) -> None:
    if isinstance(value, int):
        if value >= 0:
            _head(0, value, out)
        else:
            _head(1, -1 - value, out)
    elif isinstance(value, (bytes, bytearray)):
        _head(2, len(value), out)
        out.extend(value)
    elif isinstance(value, str):
        data = value.encode()
        _head(3, len(data), out)
        out.extend(data)
    elif isinstance(value, (list, tuple)):
        _head(4, len(value), out)
        for item in value:
            _encode(item, out)
    elif isinstance(value, dict):
        _head(5, len(value), out)
        for key, item in value.items():
            _encode(key, out)
            _encode(item, out)
    else:
        raise TypeError(f"cannot encode {type(value)} as CBOR")


def _head(major: int, argument: int, out: bytearray) -> None:
    major <<= 5
    if argument < 24:
        out.append(major | argument)
    elif argument < 0x100:
        out.append(major | 24)
        out.append(argument)
    elif argument < 0x10000:
        out.append(major | 25)
        out.extend(argument.to_bytes(2, "big"))
    else:
        out.append(major | 26)
        out.extend(argument.to_bytes(4, "big"))
