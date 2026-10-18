"""Tests for OTA bundles."""

import pytest

from scripts.build_bundle import collect_files
from src.bundle import BundleError, pack, unpack, verify


@pytest.fixture
def bundle_path(tmp_path):
    return f"{tmp_path}/update.bundle"


def write(path: str, data: bytes) -> None:
    with open(path, "wb") as f:
        f.write(data)


class TestBundle:
    def test_pack_then_unpack(self, tmp_path, bundle_path):
        files = {
            "src/a.py": b"A = 1\n",
            "src/protocols/b.py": b"",
            "src/c.py": b"x" * 3000,
        }
        write(bundle_path, pack(files))

        verify(bundle_path)
        unpack(bundle_path, f"{tmp_path}/slot")

        for path, data in files.items():
            assert (tmp_path / "slot" / path).read_bytes() == data

    def test_damaged_bundle_fails_verify(self, bundle_path):
        data = bytearray(pack({"src/a.py": b"A = 1\n"}))
        data[-6] ^= 0xFF
        write(bundle_path, bytes(data))

        with pytest.raises(BundleError):
            verify(bundle_path)

    def test_truncated_bundle_fails_verify(self, bundle_path):
        write(bundle_path, pack({"src/a.py": b"A = 1\n"})[:-10])

        with pytest.raises(BundleError):
            verify(bundle_path)

    def test_path_outside_slot_fails_unpack(self, tmp_path, bundle_path):
        write(bundle_path, pack({"../escape.py": b""}))

        with pytest.raises(BundleError):
            unpack(bundle_path, f"{tmp_path}/slot")


class TestCollectFiles:
    def test_bundle_has_the_app_and_its_version(self):
        files = collect_files("1.2.0")

        assert "src/board_main.py" in files
        assert "src/protocols/__init__.py" in files
        assert files["src/version.py"] == b'VERSION = "1.2.0"\n'
        assert not any("__pycache__" in path for path in files)
