"""Tests for SettingsPage."""

from unittest.mock import MagicMock

import pytest

from src.settings_page import (
    MAX_NAME_LENGTH,
    SettingsPage,
    decode_form,
    decode_form_value,
)
from src.settings_store import DEFAULT_SETTINGS, LEFT_TEAM_NAME, RIGHT_TEAM_NAME


@pytest.fixture
def on_save():
    return MagicMock()


@pytest.fixture
def settings_page(settings_store, on_save):
    return SettingsPage(settings_store, on_save)


class TestSettingsPage:
    def test_page_shows_saved_names(self, settings_page, settings_store):
        settings_store.save({LEFT_TEAM_NAME: "Phoenix", RIGHT_TEAM_NAME: "Tigers"})

        html = settings_page.respond(None)

        assert 'value="Phoenix"' in html
        assert 'value="Tigers"' in html

    def test_viewing_the_page_saves_nothing(self, settings_page, on_save):
        settings_page.respond(None)

        on_save.assert_not_called()

    def test_submit_saves_and_reports_settings(
        self, settings_page, settings_store, on_save
    ):
        html = settings_page.respond(
            {LEFT_TEAM_NAME: " Phoenix ", RIGHT_TEAM_NAME: "Tigers"}
        )

        expected = {LEFT_TEAM_NAME: "Phoenix", RIGHT_TEAM_NAME: "Tigers"}
        assert settings_store.load() == expected
        on_save.assert_called_once_with(expected)
        assert "Saved." in html

    def test_blank_names_fall_back_to_defaults(self, settings_page, settings_store):
        settings_page.respond({LEFT_TEAM_NAME: "  "})

        assert settings_store.load() == DEFAULT_SETTINGS

    def test_names_are_escaped(self, settings_page):
        html = settings_page.respond(
            {LEFT_TEAM_NAME: '<b>"A&B"</b>', RIGHT_TEAM_NAME: "Tigers"}
        )

        assert 'value="&lt;b&gt;&quot;A&amp;B&quot;&lt;/b&gt;"' in html

    def test_fields_missing_from_the_form_keep_their_saved_values(
        self, settings_page, settings_store
    ):
        settings_store.save({LEFT_TEAM_NAME: "Phoenix", RIGHT_TEAM_NAME: "Tigers"})

        settings_page.respond({})

        assert settings_store.load() == {
            LEFT_TEAM_NAME: "Phoenix",
            RIGHT_TEAM_NAME: "Tigers",
        }

    def test_long_names_are_cut_to_max_length(self, settings_page, settings_store):
        settings_page.respond({LEFT_TEAM_NAME: "x" * 100})

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

    def get(self, field_name, default=None, *, safe=True):
        value = self._raw.get(field_name, default)
        return value.replace("&", "&amp;") if safe and value else value


def test_decode_form_decodes_raw_values():
    form = decode_form(
        _FakeFormData({LEFT_TEAM_NAME: "Red+Team", RIGHT_TEAM_NAME: "A%26B"})
    )

    assert form == {LEFT_TEAM_NAME: "Red Team", RIGHT_TEAM_NAME: "A&B"}
