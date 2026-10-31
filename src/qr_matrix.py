"""Builds QR code matrices, in alphanumeric mode when the text allows it.

adafruit_miniqr only encodes bytes. A QR code's alphanumeric mode packs two
characters into 11 bits instead of 16, so an uppercase URL such as
"HTTP://255.255.255.255:81" fits the smallest QR code, 21 by 21 modules.
"""

import adafruit_miniqr

# The characters of QR alphanumeric mode, in the order of their values
ALPHANUMERIC_CHARACTERS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"

_MODE_ALPHANUMERIC = 0b0010
# Bits of the character count in alphanumeric mode, for versions 1 to 9
_ALPHANUMERIC_COUNT_BITS = 9
_MODE_BITS = 4
_MAX_VERSION = 9
_PAD_BYTES = (0xEC, 0x11)


def is_alphanumeric(text: str) -> bool:
    """True when every character of `text` has a QR alphanumeric value."""
    return all(char in ALPHANUMERIC_CHARACTERS for char in text)


def _alphanumeric_bits(text: str) -> int:
    """Return the bits that encode `text` in alphanumeric mode, with its header."""
    pairs, odd = divmod(len(text), 2)
    return _MODE_BITS + _ALPHANUMERIC_COUNT_BITS + 11 * pairs + 6 * odd


def _data_capacity_bits(version: int) -> int:
    """Return the data bits a QR code of `version` holds at error correction L."""
    blocks = adafruit_miniqr._get_rs_blocks(version, adafruit_miniqr.L)
    return 8 * sum(block["data"] for block in blocks)


def alphanumeric_version(text: str) -> int:
    """Return the smallest QR version that holds `text` in alphanumeric mode."""
    needed = _alphanumeric_bits(text)
    for version in range(1, _MAX_VERSION + 1):
        if needed <= _data_capacity_bits(version):
            return version
    raise ValueError(f"Too long for a QR code: {len(text)} characters")


def _alphanumeric_codewords(text: str, version: int) -> bytes:
    """Return the data and error correction codewords for `text`."""
    capacity = _data_capacity_bits(version)
    buffer = adafruit_miniqr.QRBitBuffer()
    buffer.put(_MODE_ALPHANUMERIC, _MODE_BITS)
    buffer.put(len(text), _ALPHANUMERIC_COUNT_BITS)
    values = [ALPHANUMERIC_CHARACTERS.index(char) for char in text]
    for i in range(0, len(values) - 1, 2):
        buffer.put(45 * values[i] + values[i + 1], 11)
    if len(values) % 2:
        buffer.put(values[-1], 6)
    # Terminator, then zero bits to the next byte, then the pad bytes
    buffer.put(0, min(4, capacity - buffer.get_length_bits()))
    while buffer.get_length_bits() % 8:
        buffer.put_bit(False)
    pad = 0
    while buffer.get_length_bits() < capacity:
        buffer.put(_PAD_BYTES[pad % 2], 8)
        pad += 1
    blocks = adafruit_miniqr._get_rs_blocks(version, adafruit_miniqr.L)
    # miniqr annotates the buffer as bytes, but passes its QRBitBuffer
    return adafruit_miniqr.QRCode._create_bytes(
        buffer,  # pyrefly: ignore[bad-argument-type]
        blocks,
    )


def make_qr_matrix(text: str) -> adafruit_miniqr.QRBitMatrix:
    """Return the QR code modules for `text`, truthy where a module is dark.

    Uses alphanumeric mode when `text` allows it, and byte mode otherwise.
    """
    if is_alphanumeric(text):
        version = alphanumeric_version(text)
        qr = adafruit_miniqr.QRCode(qr_type=version)
        # make() maps these codewords instead of encoding data_list as bytes
        qr.data_cache = _alphanumeric_codewords(  # pyrefly: ignore[bad-assignment]
            text, version
        )
    else:
        qr = adafruit_miniqr.QRCode()
        qr.add_data(text.encode())
    qr.make()
    matrix = qr.matrix
    assert matrix is not None
    return matrix
