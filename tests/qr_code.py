"""Helpers for checking the QR code on the display."""

from src.display_manager import make_qr_matrix, qr_code_origin


def shows_qr_code(display_manager, text):
    """True when the display shows the QR code for `text`."""
    matrix = make_qr_matrix(text)
    bitmap = display_manager._qr_code.bitmap
    left, top = qr_code_origin(matrix, text)
    return display_manager.qr_code_shown and all(
        (bitmap[left + x, top + y] == 1) == (not matrix[x, y])
        for y in range(matrix.height)
        for x in range(matrix.width)
    )
