"""Tests for the DisplayManager QR code and the address beside it."""

import pytest

from fakes import FakeMatrixPortal
from src.display_manager import (
    ADDRESS_GAP,
    ADDRESS_GLYPH_HEIGHT,
    ADDRESS_TEXT_INDEX,
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    QR_CODE_LEFT,
    QR_CODE_LIGHT_INDEX,
    QR_CODE_QUIET_ZONE_WIDTH,
    DisplayManager,
    address_fits_below,
    address_line,
    address_lines,
    address_text_width,
    make_qr_matrix,
)
from tests.qr_code import shows_qr_code

URL = "HTTP://192.168.100.200:81"
LONGEST_URL = "HTTP://255.255.255.255:81"
# The simulator's URL when the laptop does not allow port 81
SIMULATOR_URL = "HTTP://255.255.255.255:8081"


def _address_pixels(display_manager) -> set:
    bitmap = display_manager._qr_code.bitmap
    return {
        (x, y)
        for y in range(DISPLAY_HEIGHT)
        for x in range(DISPLAY_WIDTH)
        if bitmap[x, y] == ADDRESS_TEXT_INDEX
    }


def _code_right_edge(url: str) -> int:
    """Return the column just past the quiet zone of `url`'s QR code beside its
    address."""
    return QR_CODE_LEFT + make_qr_matrix(url).width + QR_CODE_QUIET_ZONE_WIDTH


def _code_bottom_edge(url: str) -> int:
    """Return the row just past the quiet zone of `url`'s QR code above its
    address."""
    return make_qr_matrix(url).height + 2 * QR_CODE_QUIET_ZONE_WIDTH


class TestDisplayQrCode:
    def test_qr_code_starts_hidden(self, display_manager):
        assert not display_manager.qr_code_shown

    def test_qr_code_is_drawn_under_only_the_update_notice(self, display_manager):
        assert display_manager._main_group[-2] is display_manager._qr_code

    def test_show_and_hide(self, display_manager):
        display_manager.show_qr_code(URL)
        assert shows_qr_code(display_manager, URL)

        display_manager.hide_qr_code()
        assert not display_manager.qr_code_shown

    @pytest.mark.parametrize("url", [LONGEST_URL, SIMULATOR_URL])
    def test_longest_url_fits_with_its_quiet_zone(self, url):
        matrix = make_qr_matrix(url)

        assert matrix.height + 2 * QR_CODE_QUIET_ZONE_WIDTH <= DISPLAY_HEIGHT

    def test_board_url_is_the_smallest_qr_code(self):
        assert make_qr_matrix(LONGEST_URL).width == 21

    def test_board_quiet_zone_is_centered_at_the_top(self, display_manager):
        display_manager.show_qr_code(LONGEST_URL)

        bitmap = display_manager._qr_code.bitmap
        lit_columns = [
            x for x in range(DISPLAY_WIDTH) if bitmap[x, 0] == QR_CODE_LIGHT_INDEX
        ]
        assert abs(lit_columns[0] - (DISPLAY_WIDTH - 1 - lit_columns[-1])) <= 1
        middle = DISPLAY_WIDTH // 2
        bottom = _code_bottom_edge(LONGEST_URL)
        assert bitmap[middle, bottom - 1] == QR_CODE_LIGHT_INDEX
        assert bitmap[middle, bottom] != QR_CODE_LIGHT_INDEX

    def test_simulator_quiet_zone_starts_at_the_left_edge(self, display_manager):
        display_manager.show_qr_code(SIMULATOR_URL)

        bitmap = display_manager._qr_code.bitmap
        middle = DISPLAY_HEIGHT // 2
        right = _code_right_edge(SIMULATOR_URL)
        assert bitmap[0, middle] == QR_CODE_LIGHT_INDEX
        assert bitmap[right - 1, middle] == QR_CODE_LIGHT_INDEX
        assert bitmap[right, middle] != QR_CODE_LIGHT_INDEX

    def test_a_new_url_replaces_the_old_address(self, display_manager):
        fresh = DisplayManager(FakeMatrixPortal())
        fresh.show_qr_code("HTTP://1.1.1.1:81")

        display_manager.show_qr_code(SIMULATOR_URL)
        display_manager.show_qr_code("HTTP://1.1.1.1:81")

        assert shows_qr_code(display_manager, "HTTP://1.1.1.1:81")
        assert _address_pixels(display_manager) == _address_pixels(fresh)


class TestAddressBelow:
    @pytest.mark.parametrize("url", [URL, LONGEST_URL])
    def test_board_address_fits_below(self, url):
        assert address_fits_below(make_qr_matrix(url), url)

    @pytest.mark.parametrize("url", [URL, LONGEST_URL])
    def test_address_is_one_line_below_the_quiet_zone(self, display_manager, url):
        display_manager.show_qr_code(url)

        pixels = _address_pixels(display_manager)
        rows = {y for _, y in pixels}
        assert min(rows) >= _code_bottom_edge(url) + ADDRESS_GAP
        assert len(rows) == ADDRESS_GLYPH_HEIGHT
        assert max(rows) < DISPLAY_HEIGHT

    @pytest.mark.parametrize("url", [URL, LONGEST_URL])
    def test_address_is_centered_horizontally(self, display_manager, url):
        display_manager.show_qr_code(url)

        columns = {x for x, _ in _address_pixels(display_manager)}
        left, right = min(columns), max(columns)
        assert abs(left - (DISPLAY_WIDTH - 1 - right)) <= 1

    def test_longest_address_spans_the_width(self, display_manager):
        display_manager.show_qr_code(LONGEST_URL)

        columns = {x for x, _ in _address_pixels(display_manager)}
        assert min(columns) == 0
        assert max(columns) >= DISPLAY_WIDTH - 2


class TestAddressBeside:
    def test_simulator_address_does_not_fit_below(self):
        assert not address_fits_below(make_qr_matrix(SIMULATOR_URL), SIMULATOR_URL)

    def test_address_is_drawn_right_of_the_quiet_zone(self, display_manager):
        display_manager.show_qr_code(SIMULATOR_URL)

        pixels = _address_pixels(display_manager)
        assert pixels
        assert (
            min(x for x, _ in pixels) >= _code_right_edge(SIMULATOR_URL) + ADDRESS_GAP
        )
        assert max(x for x, _ in pixels) < DISPLAY_WIDTH

    def test_every_line_fits_beside_the_code(self):
        room = DISPLAY_WIDTH - _code_right_edge(SIMULATOR_URL) - ADDRESS_GAP

        assert all(
            address_text_width(line) <= room for line in address_lines(SIMULATOR_URL)
        )

    def test_address_is_centered_vertically(self, display_manager):
        display_manager.show_qr_code(SIMULATOR_URL)

        rows = {y for _, y in _address_pixels(display_manager)}
        top, bottom = min(rows), max(rows)
        assert abs(top - (DISPLAY_HEIGHT - 1 - bottom)) <= 1

    def test_lines_do_not_touch(self, display_manager):
        display_manager.show_qr_code(SIMULATOR_URL)

        rows = sorted({y for _, y in _address_pixels(display_manager)})
        assert len(rows) == 3 * ADDRESS_GLYPH_HEIGHT


class TestAddressLine:
    def test_drops_the_scheme(self):
        assert address_line("HTTP://255.255.255.255:81") == "255.255.255.255:81"

    def test_drops_a_trailing_slash(self):
        assert address_line("http://192.168.1.50:8080/") == "192.168.1.50:8080"


class TestAddressLines:
    def test_ipv4_shows_two_parts_per_line_and_the_port(self):
        assert address_lines("HTTP://10.115.170.193:81") == [
            "10.115.",
            "170.193",
            ":81",
        ]

    def test_lowercase_url_with_trailing_slash(self):
        assert address_lines("http://192.168.1.50:8080/") == [
            "192.168.",
            "1.50",
            ":8080",
        ]

    def test_host_without_port(self):
        assert address_lines("HTTP://1.2.3.4") == ["1.2.", "3.4"]

    def test_other_host_stays_on_one_line(self):
        assert address_lines("HTTP://LOCALHOST:81") == ["LOCALHOST", ":81"]


class TestAddressTextWidth:
    def test_digits_are_three_wide_with_one_between(self):
        assert address_text_width("1") == 3
        assert address_text_width("12") == 7

    def test_dot_and_colon_are_one_wide(self):
        assert address_text_width("1.2") == 9
        assert address_text_width(":81") == 9

    def test_unknown_characters_take_no_room(self):
        assert address_text_width("LOCAL") == 0
