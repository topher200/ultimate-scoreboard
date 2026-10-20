"""Serves the settings web page and saves what the user submits."""

from src.compat import Callable
from src.settings_store import (
    DEFAULT_SETTINGS,
    LEFT_TEAM_NAME,
    MARCH_WMP_FRAME,
    RIGHT_TEAM_NAME,
    SHOW_WMP_FRAME,
    SettingsStore,
)

# (setting key, form label, label color)
_FIELDS = (
    (LEFT_TEAM_NAME, "Left team", "#cc0"),
    (RIGHT_TEAM_NAME, "Right team", "#ccc"),
)

# (setting key, checkbox label)
_CHECKBOXES = (
    (SHOW_WMP_FRAME, "Include the WMP border"),
    (MARCH_WMP_FRAME, "Rotate the WMP border"),
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
.check{{display:flex;align-items:center;gap:.5em;font-weight:normal}}
.check input{{width:1.5em;height:1.5em;margin:0}}
p{{color:#8c8}}
</style></head><body>
<h1>Scoreboard</h1>
<form method="post" action="/">{fields}{checkboxes}
<button type="submit">Save</button>
</form>{message}
</body></html>"""

_FIELD = """
<label style="color:{color}" for="{key}">{label}</label>
<input id="{key}" name="{key}" value="{value}" maxlength="{max_length}" autocomplete="off">"""

# The hidden input submits "0" when the box is unchecked; a checked box submits
# "1" first, and the form decoders keep the first value of each field.
_CHECKBOX = """
<label class="check"><input type="checkbox" name="{key}" value="1"{checked}>{label}</label>
<input type="hidden" name="{key}" value="0">"""

MAX_NAME_LENGTH = 16

# Where the server sends the browser after a submit
SAVED_PATH = "/?saved=1"


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

    def save(self, form: dict) -> None:
        """Save the submitted form.

        :param form: Submitted values by setting key
        """
        settings = self._store.load()
        for key, _, _ in _FIELDS:
            if key not in form:
                continue
            value = form[key].strip()[:MAX_NAME_LENGTH]
            settings[key] = value or DEFAULT_SETTINGS[key]
        for key, _ in _CHECKBOXES:
            if key in form:
                settings[key] = form[key] == "1"
        self._store.save(settings)
        self._on_save(settings)

    def render(self, saved: bool = False) -> str:
        """Return the page HTML.

        :param saved: Whether to tell the user that the last submit saved
        :return: HTML for the settings page
        """
        settings = self._store.load()
        message = "<p>Saved.</p>" if saved else ""
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
        checkboxes = "".join(
            _CHECKBOX.format(
                key=key, label=label, checked=" checked" if settings[key] else ""
            )
            for key, label in _CHECKBOXES
        )
        return _PAGE.format(fields=fields, checkboxes=checkboxes, message=message)
