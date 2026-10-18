"""Tests for network patches."""

from types import SimpleNamespace

from src.network_patches import NETWORK_TIMEOUT_SECONDS, apply_network_patches


def _make_matrixportal():
    calls = []
    requests = SimpleNamespace(get=lambda *a, **kw: calls.append(("get", kw)))
    network = SimpleNamespace(
        fetch=lambda *a, **kw: calls.append(("fetch", kw)),
        connect=lambda *a, **kw: calls.append(("connect", kw)),
        _wifi=SimpleNamespace(requests=requests),
    )
    return SimpleNamespace(network=network), calls


def test_patches_force_short_timeouts_and_no_retries():
    matrixportal, calls = _make_matrixportal()
    apply_network_patches(matrixportal)

    matrixportal.network.fetch("url", timeout=10)
    matrixportal.network.connect(max_attempts=5)
    matrixportal.network._wifi.requests.get("url", timeout=10)

    assert calls == [
        ("fetch", {"timeout": NETWORK_TIMEOUT_SECONDS}),
        ("connect", {"max_attempts": 1}),
        ("get", {"timeout": NETWORK_TIMEOUT_SECONDS}),
    ]


def test_applying_twice_wraps_once():
    matrixportal, _ = _make_matrixportal()
    apply_network_patches(matrixportal)
    fetch = matrixportal.network.fetch
    connect = matrixportal.network.connect
    get = matrixportal.network._wifi.requests.get

    apply_network_patches(matrixportal)
    matrixportal.network.connect()

    assert matrixportal.network.fetch is fetch
    assert matrixportal.network.connect is connect
    assert matrixportal.network._wifi.requests.get is get


def test_connect_patches_new_requests_object():
    matrixportal, calls = _make_matrixportal()
    apply_network_patches(matrixportal)
    matrixportal.network._wifi.requests = SimpleNamespace(
        get=lambda *a, **kw: calls.append(("new_get", kw))
    )

    matrixportal.network.connect()
    matrixportal.network._wifi.requests.get("url")

    assert calls[-1] == ("new_get", {"timeout": NETWORK_TIMEOUT_SECONDS})
