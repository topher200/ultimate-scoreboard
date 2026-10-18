"""Tests for the Memfault chunk encoder."""

import pytest

from src.memfault_chunks import EVENT_REBOOT, MESSAGE_EVENT, cbor, chunk, crc16, event
from src.ota_manager import DeviceInfo


class TestCbor:
    @pytest.mark.parametrize(
        ("value", "encoded"),
        [
            (0, "00"),
            (23, "17"),
            (24, "1818"),
            (1000, "1903e8"),
            (1000000, "1a000f4240"),
            (-1, "20"),
            (-1000, "3903e7"),
            (b"\x01\x02\x03\x04", "4401020304"),
            ("IETF", "6449455446"),
            ("ü", "62c3bc"),
            ([1, [2, 3]], "8201820203"),
            ({1: 2, 3: 4}, "a201020304"),
            ({"a": [1]}, "a161618101"),
        ],
    )
    def test_matches_rfc_8949_examples(self, value, encoded):
        assert cbor(value).hex() == encoded

    def test_rejects_a_float(self):
        with pytest.raises(TypeError):
            cbor(1.5)


class TestChunk:
    def test_crc16_matches_the_xmodem_check_value(self):
        assert crc16(b"123456789") == 0x31C3

    def test_reboot_event_matches_a_known_chunk(self):
        device = DeviceInfo("abc", "evt_24", "main", "1.2.3")

        data = chunk(MESSAGE_EVENT, event(EVENT_REBOOT, {1: 8}, device))

        assert data.hex() == (
            "0802a6020203010a646d61696e0965312e322e3306666576745f323404a10108cb59"
        )
