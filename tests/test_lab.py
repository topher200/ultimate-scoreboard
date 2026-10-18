"""Tests for the legibility lab."""

import pytest

from fakes import FakeDisplay
from src.lab import (
    AUTO_ADVANCE_SECONDS,
    CUSTOM_SCREEN_ID,
    ID_OVERLAY_SECONDS,
    MAX_NOTE_LENGTH,
    Lab,
    VoteStore,
    request_lab,
    take_lab_request,
)
from src.lab_screens import (
    GENDER_THICK_FRAME,
    MOTION_BLINK,
    MOTION_MARCH,
    MOTION_MARCH_THEN_HOLD,
    DrawnScreen,
    Pair,
    Screen,
    round_five_screens,
)
from src.settings_store import LEFT_TEAM_NAME, SettingsStore
from tests.test_display_renderer import _run


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def nvm():
    return bytearray(8192)


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def display():
    return FakeDisplay()


@pytest.fixture
def lab(display, nvm, clock):
    screens = [
        Screen("A1", "white digits"),
        Screen("A2", "yellow digits", left="yellow"),
    ]
    return Lab(display, screens, VoteStore(nvm), get_time=clock)


class TestVoteStore:
    def test_round_trips_votes(self, nvm):
        VoteStore(nvm).save({"A1": ["good", "sharp"]})

        assert VoteStore(nvm).load() == {"A1": ["good", "sharp"]}

    def test_empty_memory_has_no_votes(self, nvm):
        assert VoteStore(nvm).load() == {}

    def test_votes_leave_the_settings_intact(self, nvm):
        settings_store = SettingsStore(nvm)
        settings_store.save({LEFT_TEAM_NAME: "Phoenix"})

        VoteStore(nvm).save({"A1": ["bad", ""]})

        assert settings_store.load()[LEFT_TEAM_NAME] == "Phoenix"


class TestLabRequest:
    def test_request_is_taken_once(self, nvm):
        request_lab(nvm)

        assert take_lab_request(nvm)
        assert not take_lab_request(nvm)

    def test_no_request_in_empty_memory(self, nvm):
        assert not take_lab_request(nvm)

    def test_request_leaves_settings_and_votes_intact(self, nvm):
        settings_store = SettingsStore(nvm)
        settings_store.save({LEFT_TEAM_NAME: "Phoenix"})
        VoteStore(nvm).save({"A1": ["good", ""]})

        request_lab(nvm)
        take_lab_request(nvm)

        assert settings_store.load()[LEFT_TEAM_NAME] == "Phoenix"
        assert VoteStore(nvm).load() == {"A1": ["good", ""]}


class TestLab:
    def test_page_view_shows_the_first_screen(self, lab, display):
        html = lab.respond(None)

        assert lab.shown
        assert display.root_group is not None
        assert "A1 (1/3): white digits" in html

    def test_next_and_prev_wrap_around(self, lab):
        lab.respond({"action": "prev"})
        assert lab.screen.screen_id == CUSTOM_SCREEN_ID

        lab.respond({"action": "next"})
        assert lab.screen.screen_id == "A1"

    def test_goto_shows_the_chosen_screen(self, lab):
        lab.respond({"action": "goto", "screen": "A2"})

        assert lab.screen.screen_id == "A2"

    def test_vote_saves_and_advances(self, lab, nvm):
        lab.respond(None)

        html = lab.respond({"action": "good", "note": "  clear in sun  "})

        assert VoteStore(nvm).load() == {"A1": ["good", "clear in sun"]}
        assert lab.screen.screen_id == "A2"
        assert "A1 white digits: good (clear in sun)" in html

    def test_vote_truncates_long_notes(self, lab):
        lab.respond({"action": "bad", "note": "x" * 100})

        assert lab.votes["A1"] == ["bad", "x" * MAX_NOTE_LENGTH]

    def test_votes_survive_a_restart(self, lab, display, nvm, clock):
        lab.respond({"action": "ok", "note": ""})

        restarted = Lab(display, [Screen("A1", "white digits")], VoteStore(nvm), clock)

        assert restarted.votes == {"A1": ["ok", ""]}

    def test_clear_removes_votes(self, lab, nvm):
        lab.respond({"action": "good", "note": ""})

        lab.respond({"action": "clear"})

        assert VoteStore(nvm).load() == {}

    def test_custom_applies_valid_choices_only(self, lab):
        lab.respond(
            {
                "action": "custom",
                "font": "3x5",
                "left": "orange",
                "right": "not a color",
                "gender": "bar",
                "names": "on",
            }
        )

        custom = lab.screen
        assert custom.screen_id == CUSTOM_SCREEN_ID
        assert (custom.font, custom.left, custom.right) == ("3x5", "orange", "cyan")
        assert custom.gender == "bar"
        assert custom.names

    def test_page_escapes_notes(self, lab):
        html = lab.respond({"action": "good", "note": "<b>"})

        assert "<b>" not in html
        assert "&lt;b&gt;" in html

    def test_tick_hides_the_id_after_a_few_seconds(self, lab, display, clock):
        lab.respond(None)
        overlay = display.root_group[len(display.root_group) - 1]

        clock.now = ID_OVERLAY_SECONDS
        lab.tick()

        assert overlay.hidden
        assert lab.screen.screen_id == "A1"

    def test_tick_advances_when_auto_advance_is_on(self, lab, clock):
        lab.respond({"action": "auto"})
        lab.respond(None)

        clock.now = AUTO_ADVANCE_SECONDS
        lab.tick()

        assert lab.screen.screen_id == "A2"

    async def test_first_button_press_shows_the_current_screen(self, lab):
        await lab.next()

        assert lab.shown
        assert lab.screen.screen_id == "A1"


class TestPairs:
    @pytest.fixture
    def pair_lab(self, display, nvm, clock):
        pair = Pair(
            "G1",
            "thin vs thick",
            "Which reads?",
            Screen("", "thin"),
            Screen("", "thick"),
        )
        compare = Screen("F1", "terminal vs seg3", compare=True)
        return Lab(display, [pair, compare], VoteStore(nvm), get_time=clock)

    def test_pair_shows_a_then_b(self, pair_lab):
        html = pair_lab.respond(None)
        assert pair_lab.screen.title == "thin"
        assert "A better" in html
        assert "Which reads?" in html

        pair_lab.respond({"action": "show_b"})

        assert pair_lab.screen.title == "thick"
        assert pair_lab.item.screen_id == "G1"

    def test_pair_vote_is_keyed_by_pair(self, pair_lab):
        pair_lab.respond({"action": "show_b"})

        html = pair_lab.respond({"action": "b", "note": ""})

        assert pair_lab.votes == {"G1": ["b", ""]}
        assert pair_lab.item.screen_id == "F1"
        assert "Right better" in html

    def test_next_pair_starts_on_a(self, pair_lab):
        pair_lab.respond({"action": "show_b"})
        pair_lab.respond({"action": "next"})
        pair_lab.respond({"action": "prev"})

        assert pair_lab.screen.title == "thin"


class TestMotion:
    def test_march_moves_the_dashes(self):
        drawn = DrawnScreen(
            Screen("", "", gender=GENDER_THICK_FRAME, motion=MOTION_MARCH)
        )
        bitmap = drawn._bitmap

        drawn.animate(0.0)
        before = [bitmap[x, 0] for x in range(64)]
        drawn.animate(0.1)
        after = [bitmap[x, 0] for x in range(64)]

        assert before != after
        assert after == before[-1:] + before[:-1]

    def test_march_then_hold_stops_after_the_march(self):
        screen = Screen(
            "", "", gender=GENDER_THICK_FRAME, motion=MOTION_MARCH_THEN_HOLD
        )
        drawn = DrawnScreen(screen)
        bitmap = drawn._bitmap
        start = [bitmap[x, 0] for x in range(64)]

        drawn.animate(0.1)
        marching = [bitmap[x, 0] for x in range(64)]
        drawn.animate(30.0)
        held = [bitmap[x, 0] for x in range(64)]

        assert marching != start
        assert held == start

    def test_blink_turns_the_gender_color_off(self):
        drawn = DrawnScreen(
            Screen("", "", gender=GENDER_THICK_FRAME, motion=MOTION_BLINK)
        )
        palette = drawn._palette

        drawn.animate(0.0)
        on = palette[5]
        drawn.animate(0.5)

        assert on != 0
        assert palette[5] == 0


def test_round_five_ids_are_unique():
    ids = [item.screen_id for item in round_five_screens()]

    assert len(ids) == len(set(ids))


def test_round_five_text_overlaps_nothing():
    """Test that no label lights a pixel that the frame or another label lights."""
    result = _run(
        """
import json
from simulator.display_renderer import render_pixels
from src.lab_screens import LAYOUT_CURRENT, DrawnScreen, Pair, round_five_screens

screens = []
for item in round_five_screens():
    screens += [item.a, item.b] if isinstance(item, Pair) else [item]
bad = []
for screen in screens:
    if screen.layout == LAYOUT_CURRENT:
        continue
    group = DrawnScreen(screen).group
    layers = list(group)
    lit = []
    for layer in layers:
        for other in layers:
            other.hidden = other is not layer
        lit.append({i for i, color in enumerate(render_pixels(group)) if color})
    texts = [getattr(layer, "text", None) for layer in layers]
    for i, pixels in enumerate(lit):
        for j in range(i + 1, len(lit)):
            # A bold score is two copies of the same text
            if texts[i] is not None and texts[i] == texts[j]:
                continue
            if pixels & lit[j]:
                bad.append(screen.title)
print(json.dumps(sorted(set(bad))))
"""
    )

    assert result == []
