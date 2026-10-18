"""Decodes Memfault chunks, to check what the board uploads."""

from src.memfault_chunks import crc16


def decode_chunk(data: bytes) -> tuple[int, object]:
    """Return the message type and the payload of one chunk, after checking its framing."""
    assert data[0] == 0x08
    message, crc = data[1:-2], int.from_bytes(data[-2:], "little")
    assert crc16(message) == crc
    value, end = decode_cbor(message, 1)
    assert end == len(message)
    return message[0], value


def decode_cbor(data: bytes, offset: int = 0):
    """Return the CBOR value at offset, and the offset after it."""
    initial = data[offset]
    major, info = initial >> 5, initial & 0x1F
    offset += 1
    if info < 24:
        argument = info
    else:
        size = 1 << (info - 24)
        argument = int.from_bytes(data[offset : offset + size], "big")
        offset += size
    if major == 0:
        return argument, offset
    if major == 1:
        return -1 - argument, offset
    if major in {2, 3}:
        raw = bytes(data[offset : offset + argument])
        return (raw if major == 2 else raw.decode()), offset + argument
    if major == 4:
        items = []
        for _ in range(argument):
            item, offset = decode_cbor(data, offset)
            items.append(item)
        return items, offset
    if major == 5:
        result = {}
        for _ in range(argument):
            key, offset = decode_cbor(data, offset)
            result[key], offset = decode_cbor(data, offset)
        return result, offset
    raise ValueError(f"unsupported CBOR major type {major}")
