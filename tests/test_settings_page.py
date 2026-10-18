"""Tests for SettingsPage."""

from unittest.mock import MagicMock

import pytest

from src.settings_page import (
    MAX_NAME_LENGTH,
    SettingsPage,
    decode_form,
    decode_form_value,
)
from src.settings_store import (
    DEFAULT_SETTINGS,
    LEFT_TEAM_NAME,
    MARCH_WMP_FRAME,
    RIGHT_TEAM_NAME,
    SHOW_WMP_FRAME,
)


@pytest.fixture
def on_save():
    return MagicMock()


@pytest.fixture
def settings_page(settings_store, on_save):
    return SettingsPage(settings_store, on_save)


class TestSettingsPage:
    def test_page_shows_saved_names(self, settings_page, settings_store):
        settings_store.save({LEFT_TEAM_NAME: "Phoenix", RIGHT_TEAM_NAME: "Tigers"})

        html = settings_page.render()

        assert 'value="Phoenix"' in html
        assert 'value="Tigers"' in html
        assert "Saved." not in html

    def test_viewing_the_page_saves_nothing(self, settings_page, on_save):
        settings_page.render()

        on_save.assert_not_called()

    def test_submit_saves_and_reports_settings(
        self, settings_page, settings_store, on_save
    ):
        settings_page.save({LEFT_TEAM_NAME: " Phoenix ", RIGHT_TEAM_NAME: "Tigers"})

        expected = {
            **DEFAULT_SETTINGS,
            LEFT_TEAM_NAME: "Phoenix",
            RIGHT_TEAM_NAME: "Tigers",
        }
        assert settings_store.load() == expected
        on_save.assert_called_once_with(expected)

    def test_page_after_a_save_says_saved(self, settings_page):
        assert "Saved." in settings_page.render(saved=True)

    def test_blank_names_fall_back_to_defaults(self, settings_page, settings_store):
        settings_page.save({LEFT_TEAM_NAME: "  "})

        assert settings_store.load() == DEFAULT_SETTINGS

    def test_names_are_escaped(self, settings_page):
        settings_page.save({LEFT_TEAM_NAME: '<b>"A&B"</b>', RIGHT_TEAM_NAME: "Tigers"})
        html = settings_page.render()

        assert 'value="&lt;b&gt;&quot;A&amp;B&quot;&lt;/b&gt;"' in html

    def test_fields_missing_from_the_form_keep_their_saved_values(
        self, settings_page, settings_store
    ):
        saved = {
            LEFT_TEAM_NAME: "Phoenix",
            RIGHT_TEAM_NAME: "Tigers",
            SHOW_WMP_FRAME: False,
            MARCH_WMP_FRAME: False,
        }
        settings_store.save(saved)

        settings_page.save({})

        assert settings_store.load() == saved

    def test_checkboxes_default_to_checked(self, settings_page):
        html = settings_page.render()

        for key in (SHOW_WMP_FRAME, MARCH_WMP_FRAME):
            assert f'name="{key}" value="1" checked>' in html

    def test_unchecked_boxes_save_false(self, settings_page, settings_store):
        settings_page.save({SHOW_WMP_FRAME: "0", MARCH_WMP_FRAME: "0"})
        html = settings_page.render()

        settings = settings_store.load()
        assert settings[SHOW_WMP_FRAME] is False
        assert settings[MARCH_WMP_FRAME] is False
        assert 'value="1" checked' not in html

    def test_checked_boxes_save_true(self, settings_page, settings_store):
        settings_store.save({SHOW_WMP_FRAME: False, MARCH_WMP_FRAME: False})

        settings_page.save({SHOW_WMP_FRAME: "1", MARCH_WMP_FRAME: "1"})

        settings = settings_store.load()
        assert settings[SHOW_WMP_FRAME] is True
        assert settings[MARCH_WMP_FRAME] is True

    def test_long_names_are_cut_to_max_length(self, settings_page, settings_store):
        settings_page.save({LEFT_TEAM_NAME: "x" * 100})

        assert settings_store.load()[LEFT_TEAM_NAME] == "x" * MAX_NAME_LENGTH


@pytest.mark.parametrize(
    ("encoded", "decoded"),
    [
        ("Red+Team", "Red Team"),
        ("A%26B", "A&B"),
        ("Se%C3%B1or", "Señor"),
        ("100%", "100%"),
        ("%zz", "%zz"),
    ],
)
def test_decode_form_value(encoded, decoded):
    assert decode_form_value(encoded) == decoded


class _FakeFormData:
    """Stands in for adafruit_httpserver FormData, which keeps values urlencoded."""

    def __init__(self, raw):
        self._raw = raw
        self.fields = list(raw)

    def __getitem__(self, field_name):
        return self._raw[field_name]

    def get(self, field_name, default=None, *, safe=True):
        if not safe:
            print("WARNING: Setting safe to False makes XSS vulnerabilities possible")
        value = self._raw.get(field_name, default)
        return value.replace("&", "&amp;") if safe and value else value


def test_decode_form_decodes_raw_values():
    form = decode_form(
        _FakeFormData({LEFT_TEAM_NAME: "Red+Team", RIGHT_TEAM_NAME: "A%26B"})
    )

    assert form == {LEFT_TEAM_NAME: "Red Team", RIGHT_TEAM_NAME: "A&B"}


def test_decode_form_prints_no_xss_warning(capsys):
    decode_form(_FakeFormData({LEFT_TEAM_NAME: "Red+Team"}))

    assert not capsys.readouterr().out
