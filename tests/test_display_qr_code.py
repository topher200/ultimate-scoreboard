"""Tests for the DisplayManager QR code."""

from src.display_manager import (
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    QR_CODE_QUIET_ZONE_WIDTH,
    make_qr_matrix,
)
from tests.qr_code import shows_qr_code

URL = "http://192.168.100.200:8080/"


class TestDisplayQrCode:
    def test_qr_code_starts_hidden(self, display_manager):
        assert not display_manager.qr_code_shown

    def test_qr_code_is_drawn_on_top(self, display_manager):
        assert display_manager._main_group[-1] is display_manager._qr_code

    def test_show_and_hide(self, display_manager):
        display_manager.show_qr_code(URL)
        assert shows_qr_code(display_manager, URL)

        display_manager.hide_qr_code()
        assert not display_manager.qr_code_shown

    def test_longest_url_fits_with_its_quiet_zone(self):
        matrix = make_qr_matrix(URL)

        assert matrix.height + 2 * QR_CODE_QUIET_ZONE_WIDTH <= DISPLAY_HEIGHT

    def test_only_the_quiet_zone_and_code_are_lit(self, display_manager):
        display_manager.show_qr_code(URL)

        matrix = make_qr_matrix(URL)
        left = (DISPLAY_WIDTH - matrix.width) // 2
        bitmap = display_manager._qr_code.bitmap
        middle = DISPLAY_HEIGHT // 2
        assert bitmap[left - QR_CODE_QUIET_ZONE_WIDTH, middle] == 1
        assert bitmap[left - QR_CODE_QUIET_ZONE_WIDTH - 1, middle] == 0
