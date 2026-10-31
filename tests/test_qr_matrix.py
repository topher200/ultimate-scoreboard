"""Tests for building QR code matrices."""

import pytest
import zxingcpp
from PIL import Image

from src.qr_matrix import (
    ALPHANUMERIC_CHARACTERS,
    alphanumeric_version,
    is_alphanumeric,
    make_qr_matrix,
)

# The longest settings page URL the board makes
LONGEST_URL = "HTTP://255.255.255.255:81"


def decode(matrix) -> list[str]:
    """Return what a QR reader finds in a clean image of `matrix`."""
    quiet_zone = 4
    size = matrix.width + 2 * quiet_zone
    pixels = [
        (0, 0, 0)
        if 0 <= x - quiet_zone < matrix.width
        and 0 <= y - quiet_zone < matrix.height
        and matrix[x - quiet_zone, y - quiet_zone]
        else (255, 255, 255)
        for y in range(size)
        for x in range(size)
    ]
    image = Image.new("RGB", (size, size))
    image.putdata(pixels)
    image = image.resize((size * 8, size * 8), Image.Resampling.NEAREST)
    return [result.text for result in zxingcpp.read_barcodes(image)]


class TestMakeQrMatrix:
    @pytest.mark.parametrize(
        "text",
        [
            LONGEST_URL,
            "HTTP://10.115.170.193:81",
            "HTTP://1.2.3.4:81",
            "HTTP://192.168.1.50:8081",
            ALPHANUMERIC_CHARACTERS,
            "A",
        ],
    )
    def test_alphanumeric_text_decodes(self, text):
        assert decode(make_qr_matrix(text)) == [text]

    @pytest.mark.parametrize("text", ["http://192.168.1.50:8080/", "lowercase"])
    def test_other_text_decodes_in_byte_mode(self, text):
        assert decode(make_qr_matrix(text)) == [text]

    def test_longest_url_is_the_smallest_qr_code(self):
        assert make_qr_matrix(LONGEST_URL).width == 21

    def test_alphanumeric_mode_is_smaller_than_byte_mode(self):
        assert make_qr_matrix(LONGEST_URL).width < (
            make_qr_matrix(LONGEST_URL.lower()).width
        )


class TestAlphanumeric:
    def test_uppercase_url_is_alphanumeric(self):
        assert is_alphanumeric(LONGEST_URL)

    @pytest.mark.parametrize("text", ["http://", "a/b", "1_2", "é"])
    def test_other_characters_are_not(self, text):
        assert not is_alphanumeric(text)

    @pytest.mark.parametrize(
        ("length", "version"), [(1, 1), (25, 1), (26, 2), (47, 2), (48, 3)]
    )
    def test_version_grows_at_each_capacity(self, length, version):
        assert alphanumeric_version("A" * length) == version

    def test_text_too_long_for_version_9_raises(self):
        with pytest.raises(ValueError):
            alphanumeric_version("A" * 1000)
