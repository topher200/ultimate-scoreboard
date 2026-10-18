"""Tests for network patches."""

from types import SimpleNamespace

from src.network_patches import apply_network_patches


def _make_matrixportal():
    calls = []
    network = SimpleNamespace(connect=lambda *a, **kw: calls.append(kw))
    return SimpleNamespace(network=network), calls


def test_connect_tries_once():
    matrixportal, calls = _make_matrixportal()
    apply_network_patches(matrixportal)

    matrixportal.network.connect(max_attempts=5)

    assert calls == [{"max_attempts": 1}]


def test_applying_twice_wraps_once():
    matrixportal, _ = _make_matrixportal()
    apply_network_patches(matrixportal)
    connect = matrixportal.network.connect

    apply_network_patches(matrixportal)

    assert matrixportal.network.connect is connect
