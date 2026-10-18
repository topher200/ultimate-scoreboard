"""Helpers for checking the QR code on the display."""

from src.display_manager import DISPLAY_HEIGHT, DISPLAY_WIDTH, make_qr_matrix


def shows_qr_code(display_manager, text):
    """True when the display shows the QR code for `text`."""
    matrix = make_qr_matrix(text)
    bitmap = display_manager._qr_code.bitmap
    left = (DISPLAY_WIDTH - matrix.width) // 2
    top = (DISPLAY_HEIGHT - matrix.height) // 2
    return display_manager.qr_code_shown and all(
        (bitmap[left + x, top + y] == 1) == (not matrix[x, y])
        for y in range(matrix.height)
        for x in range(matrix.width)
    )
