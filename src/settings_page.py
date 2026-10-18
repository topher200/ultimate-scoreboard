"""Serves the settings web page and saves what the user submits."""

from src.compat import Callable
from src.settings_store import (
    DEFAULT_SETTINGS,
    LEFT_TEAM_NAME,
    RIGHT_TEAM_NAME,
    SettingsStore,
)

# (setting key, form label, label color)
_FIELDS = (
    (LEFT_TEAM_NAME, "Left team", "#cc0"),
    (RIGHT_TEAM_NAME, "Right team", "#ccc"),
)

_PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scoreboard</title>
<style>
body{{font-family:sans-serif;max-width:24em;margin:0 auto;padding:1em;background:#111;color:#eee}}
label{{display:block;margin-top:1em;font-weight:bold}}
input{{width:100%;box-sizing:border-box;font-size:1.5em;padding:.3em;margin-top:.2em}}
button{{width:100%;font-size:1.5em;padding:.5em;margin-top:1.5em}}
p{{color:#8c8}}
</style></head><body>
<h1>Scoreboard</h1>
<form method="post" action="/">{fields}
<button type="submit">Save</button>
</form>{message}
</body></html>"""

_FIELD = """
<label style="color:{color}" for="{key}">{label}</label>
<input id="{key}" name="{key}" value="{value}" maxlength="{max_length}" autocomplete="off">"""

MAX_NAME_LENGTH = 16


def decode_form_value(text: str) -> str:
    """Decode one value from an application/x-www-form-urlencoded body."""
    data = bytearray()
    i = 0
    while i < len(text):
        char = text[i]
        if char == "+":
            data.append(0x20)
        elif char == "%" and _is_hex(text[i + 1 : i + 3]):
            data.append(int(text[i + 1 : i + 3], 16))
            i += 2
        else:
            data.extend(char.encode())
        i += 1
    return data.decode()


def decode_form(form_data) -> dict:
    """Decode the fields of a urlencoded adafruit_httpserver FormData into a dict."""
    return {key: decode_form_value(form_data[key]) for key in form_data.fields}


def _is_hex(text: str) -> bool:
    return len(text) == 2 and all(c in "0123456789abcdefABCDEF" for c in text)


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class SettingsPage:
    """Renders the settings form and saves submitted settings."""

    def __init__(self, store: SettingsStore, on_save: Callable):
        """Initialize SettingsPage.

        :param store: SettingsStore that holds the settings
        :param on_save: Called with the settings dict after each save
        """
        self._store = store
        self._on_save = on_save

    def respond(self, form: dict | None) -> str:
        """Save the submitted form, if any, and return the page HTML.

        :param form: Submitted values by setting key, or None to only show the page
        :return: HTML for the settings page
        """
        settings = self._store.load()
        message = ""
        if form is not None:
            for key, _, _ in _FIELDS:
                if key not in form:
                    continue
                value = form[key].strip()[:MAX_NAME_LENGTH]
                settings[key] = value or DEFAULT_SETTINGS[key]
            self._store.save(settings)
            self._on_save(settings)
            message = "<p>Saved.</p>"
        fields = "".join(
            _FIELD.format(
                key=key,
                label=label,
                color=color,
                value=_escape(settings[key]),
                max_length=MAX_NAME_LENGTH,
            )
            for key, label, color in _FIELDS
        )
        return _PAGE.format(fields=fields, message=message)
