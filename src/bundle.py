"""Packs app files into one OTA bundle and unpacks them on the board.

A bundle is a header line, then for each file a "<path> <size>" line and the
file's bytes, then the CRC-32 of everything before it as 4 big-endian bytes.
"""

import binascii
import os

from ota_loader import make_dirs

HEADER = b"SCOREBOARD-BUNDLE 1\n"
CRC_SIZE = 4
READ_SIZE = 1024


class BundleError(Exception):
    """The bundle is damaged or is not a bundle."""


def pack(files: dict[str, bytes]) -> bytes:
    """Return a bundle of the files, keyed by their path in the slot."""
    body = bytearray(HEADER)
    for path, data in files.items():
        body += f"{path} {len(data)}\n".encode()
        body += data
    return bytes(body) + binascii.crc32(body).to_bytes(CRC_SIZE, "big")


def verify(bundle_path: str) -> None:
    """Raise BundleError unless the bundle file ends with the CRC of its contents."""
    size = os.stat(bundle_path)[6]
    if size < len(HEADER) + CRC_SIZE:
        raise BundleError("bundle is too short")
    crc = 0
    with open(bundle_path, "rb") as f:
        remaining = size - CRC_SIZE
        while remaining:
            chunk = f.read(min(READ_SIZE, remaining))
            crc = binascii.crc32(chunk, crc)
            remaining -= len(chunk)
        if int.from_bytes(f.read(CRC_SIZE), "big") != crc:
            raise BundleError("bundle CRC does not match")


def unpack(bundle_path: str, target_dir: str) -> None:
    """Write the files of a verified bundle under target_dir."""
    end = os.stat(bundle_path)[6] - CRC_SIZE
    with open(bundle_path, "rb") as f:
        if f.read(len(HEADER)) != HEADER:
            raise BundleError("not a scoreboard bundle")
        while f.tell() < end:
            path, size = f.readline().decode().rstrip("\n").rsplit(" ", 1)
            if path.startswith("/") or ".." in path.split("/"):
                raise BundleError(f"bad path in bundle: {path}")
            target = target_dir + "/" + path
            make_dirs(target.rsplit("/", 1)[0])
            remaining = int(size)
            with open(target, "wb") as out:
                while remaining:
                    chunk = f.read(min(READ_SIZE, remaining))
                    if not chunk:
                        raise BundleError("bundle ends early")
                    out.write(chunk)
                    remaining -= len(chunk)
