"""Tests for Telemetry."""

import asyncio

import pytest

import ota_loader
from fakes import FakeHttp, FakeResponse
from src.log import ERROR, INFO, discard_lines, kept_lines, log
from src.memfault_chunks import (
    EVENT_CUSTOM_DATA_RECORDING,
    EVENT_HEARTBEAT,
    EVENT_LOGS,
    EVENT_REBOOT,
    MESSAGE_CUSTOM_DATA_RECORDING,
    MESSAGE_EVENT,
    MESSAGE_LOGS,
    REBOOT_ASSERT,
    REBOOT_FW_UPDATE,
    REBOOT_PIN,
    REBOOT_POWER_ON,
)
from src.ota_manager import DeviceInfo
from src.telemetry import (
    CHUNKS_URL,
    CRASH_FILE,
    FIRST_HEARTBEAT_S,
    HEARTBEAT_INTERVAL_S,
    MAX_PENDING_EVENTS,
    Telemetry,
    save_crash,
)
from tests.cbor_decode import decode_chunk

CRASH = b'Traceback (most recent call last):\n  File "main.py", line 1\nRuntimeError: boom\n'


@pytest.fixture
def root(tmp_path):
    return f"{tmp_path}/"


@pytest.fixture(autouse=True)
def empty_log():
    discard_lines(len(kept_lines()))
    yield
    discard_lines(len(kept_lines()))


@pytest.fixture
def fake_http():
    http = FakeHttp()
    accept(http)
    return http


def accept(http, status=202):
    http.responses[CHUNKS_URL] = FakeResponse(status)


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return Clock()


def make_telemetry(fake_http, root, clock, reboot_reason=REBOOT_POWER_ON, metrics=None):
    device = DeviceInfo("abc123", "matrixportal-s3", "scoreboard", "1.0.0")
    return Telemetry(
        fake_http,
        "project-key",
        device,
        root,
        reboot_reason,
        lambda: dict(metrics or {}),
        clock,
    )


def write_crash(root):
    with open(root + CRASH_FILE, "wb") as f:
        f.write(CRASH)


def uploads(fake_http) -> list:
    """Return the (message type, payload) of each post."""
    return [decode_chunk(data) for _, _, data in fake_http.posts]


def event_infos(fake_http, event_type) -> list:
    """Return the event_info of each uploaded event of a type."""
    infos = []
    for _, payload in uploads(fake_http):
        for e in payload if isinstance(payload, list) else [payload]:
            if e[2] == event_type:
                infos.append(e[4])
    return infos


class TestFlush:
    def test_posts_with_the_project_key(self, fake_http, root, clock):
        make_telemetry(fake_http, root, clock).flush()

        url, headers, _ = fake_http.posts[0]
        assert url == CHUNKS_URL + "abc123"
        assert headers["Memfault-Project-Key"] == "project-key"
        assert headers["Content-Type"] == "application/octet-stream"
        _, events = uploads(fake_http)[0]
        assert isinstance(events, list)
        assert events[0][6] == "matrixportal-s3"
        assert events[0][9] == "1.0.0"
        assert events[0][10] == "scoreboard"

    def test_sends_each_kind_as_its_own_message_type(self, fake_http, root, clock):
        write_crash(root)
        telemetry = make_telemetry(fake_http, root, clock)
        log("hello")

        telemetry.flush()

        types = [message_type for message_type, _ in uploads(fake_http)]
        assert types == [MESSAGE_EVENT, MESSAGE_CUSTOM_DATA_RECORDING, MESSAGE_LOGS]

    def test_sends_the_kept_log_lines_once(self, fake_http, root, clock):
        telemetry = make_telemetry(fake_http, root, clock, reboot_reason=None)
        log("hello")
        log("bad thing", ERROR)

        telemetry.flush()
        telemetry.flush()

        assert event_infos(fake_http, EVENT_LOGS) == [
            [INFO, "hello", ERROR, "bad thing"]
        ]

    def test_failed_upload_keeps_the_events_for_the_next_flush(
        self, fake_http, root, clock
    ):
        telemetry = make_telemetry(fake_http, root, clock)
        accept(fake_http, 500)
        telemetry.flush()
        fake_http.posts.clear()

        accept(fake_http)
        telemetry.flush()

        assert event_infos(fake_http, EVENT_REBOOT) == [{1: REBOOT_POWER_ON}]
        assert "Telemetry upload returned 500" in event_infos(fake_http, EVENT_LOGS)[0]

    def test_network_error_keeps_the_events(self, root, clock):
        fake_http = FakeHttp()
        telemetry = make_telemetry(fake_http, root, clock)
        telemetry.flush()
        fake_http.posts.clear()

        accept(fake_http)
        telemetry.flush()

        assert event_infos(fake_http, EVENT_REBOOT) == [{1: REBOOT_POWER_ON}]

    def test_nothing_to_send_posts_nothing(self, fake_http, root, clock):
        make_telemetry(fake_http, root, clock, reboot_reason=None).flush()

        assert fake_http.posts == []


class TestReboot:
    def test_saved_reason_wins_over_the_hardware_reason(self, fake_http, root, clock):
        make_telemetry(fake_http, root, clock).prepare_reset(REBOOT_FW_UPDATE)
        fake_http.posts.clear()

        make_telemetry(fake_http, root, clock, reboot_reason=REBOOT_PIN).flush()

        assert event_infos(fake_http, EVENT_REBOOT) == [{1: REBOOT_FW_UPDATE}]

    def test_saved_reason_applies_to_one_reboot(self, fake_http, root, clock):
        make_telemetry(fake_http, root, clock).prepare_reset(REBOOT_FW_UPDATE)
        make_telemetry(fake_http, root, clock)
        fake_http.posts.clear()

        make_telemetry(fake_http, root, clock, reboot_reason=REBOOT_PIN).flush()

        assert event_infos(fake_http, EVENT_REBOOT) == [{1: REBOOT_PIN}]

    def test_damaged_saved_reason_uses_the_hardware_reason(
        self, fake_http, root, clock
    ):
        with open(root + "reboot_reason", "wb") as f:
            f.write(b"\xff\xfe")

        make_telemetry(fake_http, root, clock, reboot_reason=REBOOT_PIN).flush()

        assert event_infos(fake_http, EVENT_REBOOT) == [{1: REBOOT_PIN}]

    def test_prepare_reset_uploads_the_log_lines(self, fake_http, root, clock):
        telemetry = make_telemetry(fake_http, root, clock, reboot_reason=None)
        log("Downloading the update into slot a")

        telemetry.prepare_reset(REBOOT_FW_UPDATE)

        assert (
            "Downloading the update into slot a"
            in event_infos(fake_http, EVENT_LOGS)[0]
        )


class TestCrash:
    def test_crash_uploads_a_recording_and_an_assert_reboot(
        self, fake_http, root, clock
    ):
        write_crash(root)

        make_telemetry(fake_http, root, clock, reboot_reason=REBOOT_PIN).flush()

        assert event_infos(fake_http, EVENT_REBOOT) == [
            {1: REBOOT_ASSERT, 8: b"RuntimeError: boom"}
        ]
        assert event_infos(fake_http, EVENT_CUSTOM_DATA_RECORDING) == [
            {1: 0, 2: ["text/plain"], 3: "RuntimeError: boom", 4: CRASH}
        ]

    def test_crash_wins_over_the_saved_reason(self, fake_http, root, clock):
        make_telemetry(fake_http, root, clock).prepare_reset(REBOOT_FW_UPDATE)
        write_crash(root)
        fake_http.posts.clear()

        make_telemetry(fake_http, root, clock).flush()

        assert event_infos(fake_http, EVENT_REBOOT)[0][1] == REBOOT_ASSERT

    def test_crash_uploads_once(self, fake_http, root, clock):
        write_crash(root)
        make_telemetry(fake_http, root, clock).flush()
        fake_http.posts.clear()

        make_telemetry(fake_http, root, clock).flush()

        assert event_infos(fake_http, EVENT_CUSTOM_DATA_RECORDING) == []
        assert event_infos(fake_http, EVENT_REBOOT) == [{1: REBOOT_POWER_ON}]

    def test_crash_that_fails_to_upload_uploads_after_the_next_reboot(
        self, root, clock
    ):
        write_crash(root)
        fake_http = FakeHttp()
        make_telemetry(fake_http, root, clock).flush()
        fake_http.posts.clear()

        accept(fake_http)
        make_telemetry(fake_http, root, clock).flush()

        assert event_infos(fake_http, EVENT_CUSTOM_DATA_RECORDING)[0][4] == CRASH
        assert event_infos(fake_http, EVENT_REBOOT) == [{1: REBOOT_POWER_ON}]

    def test_saved_crash_uploads(self, fake_http, root, clock):
        try:
            crash()
        except RuntimeError as e:
            save_crash(root, e)

        make_telemetry(fake_http, root, clock).flush()

        recording = event_infos(fake_http, EVENT_CUSTOM_DATA_RECORDING)
        assert recording[0][3] == "RuntimeError: boom"
        assert b"Traceback" in recording[0][4]


def crash():
    raise RuntimeError("boom")


class TestHeartbeat:
    def test_heartbeat_sends_the_metrics_and_the_interval(self, fake_http, root, clock):
        telemetry = make_telemetry(
            fake_http, root, clock, reboot_reason=None, metrics={"points_scored": 3}
        )
        clock.now += 900.5

        telemetry.send_heartbeat()

        assert event_infos(fake_http, EVENT_HEARTBEAT) == [
            {1: {"points_scored": 3, "MemfaultSdkMetric_IntervalMs": 900500}}
        ]

    def test_failed_heartbeats_queue_up_to_a_limit(self, root, clock):
        fake_http = FakeHttp()
        telemetry = make_telemetry(fake_http, root, clock, reboot_reason=None)

        for _ in range(MAX_PENDING_EVENTS + 3):
            telemetry.send_heartbeat()
        fake_http.posts.clear()
        accept(fake_http)
        telemetry.flush()

        assert len(event_infos(fake_http, EVENT_HEARTBEAT)) == MAX_PENDING_EVENTS

    async def test_run_sends_a_heartbeat_only_while_online(
        self, fake_http, root, clock, monkeypatch
    ):
        telemetry = make_telemetry(fake_http, root, clock, reboot_reason=None)
        sleeps = []
        online = [False, True]

        async def fake_sleep(seconds):
            sleeps.append(seconds)
            if len(sleeps) > len(online):
                raise asyncio.CancelledError

        monkeypatch.setattr("src.telemetry.asyncio.sleep", fake_sleep)

        with pytest.raises(asyncio.CancelledError):
            await telemetry.run(lambda: online[len(sleeps) - 1])

        assert sleeps == [FIRST_HEARTBEAT_S] + [HEARTBEAT_INTERVAL_S] * 2
        assert len(event_infos(fake_http, EVENT_HEARTBEAT)) == 1
