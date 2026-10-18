"""Legibility lab: shows test screens and records votes from a phone page.

Hold both buttons for LONG_HOLD_THRESHOLD seconds to restart into the lab, and
again to restart into the scoreboard.
"""

import asyncio
import json
import time

import terminalio
from adafruit_display_text import label

from src.compat import Callable
from src.display_manager import DisplayManager
from src.hardware_manager import BUTTON_LEFT, BUTTON_RIGHT, HardwareManager
from src.lab_screens import (
    BACKGROUND_NAMES,
    COLOR_NAMES,
    FONTS,
    GENDERS,
    MOTIONS,
    DrawnScreen,
    Pair,
    Screen,
    round_two_screens,
)
from src.network_manager import NetworkManager
from src.settings_page import _escape

# Votes live after the settings in non-volatile memory
VOTE_STORE_OFFSET = 4096
# Byte just before the votes that asks the next boot to start the lab
LAB_REQUEST_OFFSET = VOTE_STORE_OFFSET - 1
LAB_REQUEST_VALUE = 0x1A
_LENGTH_BYTES = 2

# (vote, button label) for each kind of item
RATING_VOTES = (("good", "Good"), ("ok", "OK"), ("bad", "Bad"))
COMPARE_VOTES = (("left", "Left better"), ("same", "Same"), ("right", "Right better"))
PAIR_VOTES = (("a", "A better"), ("same", "Same"), ("b", "B better"))
VOTES = ("good", "ok", "bad", "left", "same", "right", "a", "b")
MAX_NOTE_LENGTH = 40
ID_OVERLAY_SECONDS = 3.0
AUTO_ADVANCE_SECONDS = 8.0
LAB_POLL_INTERVAL = 0.1
ID_OVERLAY_COLOR = 0x555555
CUSTOM_SCREEN_ID = "Z1"

_PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scoreboard lab</title>
<style>
body{{font-family:sans-serif;max-width:28em;margin:0 auto;padding:1em;background:#111;color:#eee}}
button,select,input{{font-size:1.3em;padding:.4em;margin:.2em 0}}
.row{{display:flex;gap:.4em}}.row>*{{flex:1}}
.good{{background:#2a2}}.ok{{background:#aa2}}.bad{{background:#a22}}
.showing{{outline:3px solid #fff}}
h1{{font-size:1.4em}}pre{{white-space:pre-wrap;background:#222;padding:.5em}}
label{{display:block}}.note{{width:100%;box-sizing:border-box}}
</style></head><body>
<h1>{screen_id} ({position}/{count}): {title}</h1>
<form method="post" action="/">
<div class="row"><button name="action" value="prev">&larr; Prev</button>
<button name="action" value="next">Next &rarr;</button></div>
<input name="note" placeholder="Note (optional)" maxlength="{max_note}" class="note">
{pair_buttons}
<div class="row">{vote_buttons}</div>
<p>{vote}</p>
<div class="row"><select name="screen">{screen_options}</select>
<button name="action" value="goto">Go</button></div>
<button name="action" value="auto">Auto-advance: {auto}</button>
</form>
<h2>Custom screen ({custom_id})</h2>
<form method="post" action="/">{custom_fields}
<button name="action" value="custom">Show custom screen</button>
</form>
<h2>Votes</h2>
<pre>{results}</pre>
<form method="post" action="/"><button name="action" value="clear">Clear votes</button></form>
</body></html>"""


def _option(value: str, text: str, selected: bool) -> str:
    attribute = " selected" if selected else ""
    return f'<option value="{value}"{attribute}>{_escape(text)}</option>'


def _options(choices, selected: str) -> str:
    return "".join(_option(choice, choice, choice == selected) for choice in choices)


def request_lab(nvm) -> None:
    """Ask the next boot to start the lab."""
    nvm[LAB_REQUEST_OFFSET] = LAB_REQUEST_VALUE


def take_lab_request(nvm) -> bool:
    """Clear the lab request, and return whether there was one."""
    requested = nvm[LAB_REQUEST_OFFSET] == LAB_REQUEST_VALUE
    if requested:
        nvm[LAB_REQUEST_OFFSET] = 0
    return requested


class VoteStore:
    """Saves votes as JSON in non-volatile memory, after the settings."""

    def __init__(self, nvm, offset: int = VOTE_STORE_OFFSET):
        """Initialize VoteStore.

        :param nvm: Writable byte buffer that keeps its contents across reboots
        :param offset: Index of the first byte that the votes use
        """
        self._nvm = nvm
        self._offset = offset

    def load(self) -> dict:
        """Return the saved votes as {screen ID: [vote, note]}."""
        start = self._offset + _LENGTH_BYTES
        length = int.from_bytes(self._nvm[self._offset : start], "big")
        if length == 0 or length > len(self._nvm) - start:
            return {}
        try:
            votes = json.loads(bytes(self._nvm[start : start + length]).decode())
        except (ValueError, UnicodeError) as e:
            print(f"Failed to load votes: {e}")
            return {}
        return votes if isinstance(votes, dict) else {}

    def save(self, votes: dict) -> None:
        """Save votes, replacing what was saved before."""
        data = json.dumps(votes).encode()
        if len(data) > len(self._nvm) - self._offset - _LENGTH_BYTES:
            raise ValueError("Votes are too large to save")
        self._nvm[self._offset : self._offset + _LENGTH_BYTES + len(data)] = (
            len(data).to_bytes(_LENGTH_BYTES, "big") + data
        )


class Lab:
    """Shows one test screen at a time and records a vote for each."""

    def __init__(
        self,
        display,
        items: list,
        vote_store: VoteStore,
        get_time: Callable = time.monotonic,
    ):
        """Initialize Lab.

        :param display: Display whose root group the lab sets
        :param items: Screens and Pairs, in the order the lab shows them
        :param vote_store: VoteStore that keeps the votes
        :param get_time: Callable returning current time in seconds
        """
        self._display = display
        self._custom = Screen(CUSTOM_SCREEN_ID, "custom", left="yellow", right="cyan")
        self._items = list(items) + [self._custom]
        self._vote_store = vote_store
        self._votes = vote_store.load()
        self._get_time = get_time
        self._index = 0
        self._showing_b = False
        self._drawn: DrawnScreen | None = None
        self._overlay: label.Label | None = None
        self._shown_at = 0.0
        self.auto_advance = False

    @property
    def item(self):
        """The Screen or Pair at the current position."""
        return self._items[self._index]

    @property
    def screen(self) -> Screen:
        """The screen on the display, which is one side of a Pair."""
        item = self.item
        if isinstance(item, Pair):
            return item.b if self._showing_b else item.a
        return item

    @property
    def votes(self) -> dict:
        return self._votes

    @property
    def shown(self) -> bool:
        """Whether the display shows a test screen."""
        drawn = self._drawn
        return drawn is not None and self._display.root_group is drawn.group

    def show(self, index: int, showing_b: bool = False) -> None:
        """Show the item at `index`, with its ID in the corner for a few seconds.

        :param index: Position of the item, which wraps around
        :param showing_b: Whether a Pair shows its B screen
        """
        self._index = index % len(self._items)
        self._showing_b = showing_b
        item = self.item
        drawn = DrawnScreen(self.screen)
        group = drawn.group
        side = (" B" if showing_b else " A") if isinstance(item, Pair) else ""
        overlay = label.Label(
            terminalio.FONT,
            text=item.screen_id + side,
            color=ID_OVERLAY_COLOR,
            background_color=0x000000,
            anchor_point=(0.0, 0.0),
            anchored_position=(0, 0),
        )
        group.append(overlay)
        self._overlay = overlay
        self._drawn = drawn
        self._display.root_group = group
        self._shown_at = self._get_time()
        print(f"Lab screen {item.screen_id}{side}: {self.screen.title}")

    async def previous(self) -> None:
        self.show(self._index - 1 if self.shown else self._index)

    async def next(self) -> None:
        self.show(self._index + 1 if self.shown else self._index)

    async def toggle_auto_advance(self) -> None:
        self.auto_advance = not self.auto_advance
        self.show(self._index)

    def tick(self) -> None:
        """Animate the screen, hide the ID overlay, and advance when auto-advance is on."""
        drawn = self._drawn
        if drawn is None or not self.shown:
            return
        elapsed = self._get_time() - self._shown_at
        if self.auto_advance and elapsed >= AUTO_ADVANCE_SECONDS:
            self.show(self._index + 1)
            return
        drawn.animate(elapsed)
        if self._overlay is not None and elapsed >= ID_OVERLAY_SECONDS:
            self._overlay.hidden = True

    async def run(self) -> None:
        """Run tick forever."""
        while True:
            self.tick()
            await asyncio.sleep(LAB_POLL_INTERVAL)

    def _apply(self, form: dict) -> None:
        action = form.get("action")
        if action == "prev":
            self.show(self._index - 1)
        elif action == "next":
            self.show(self._index + 1)
        elif action == "goto":
            for i, item in enumerate(self._items):
                if item.screen_id == form.get("screen"):
                    self.show(i)
        elif action in {"show_a", "show_b"}:
            self.show(self._index, showing_b=action == "show_b")
        elif action == "auto":
            self.auto_advance = not self.auto_advance
        elif action in VOTES:
            item = self.item
            note = form.get("note", "").strip()[:MAX_NOTE_LENGTH]
            self._votes[item.screen_id] = [action, note]
            self._vote_store.save(self._votes)
            print(f"Lab vote {item.screen_id} ({item.title}): {action} {note}")
            self.show(self._index + 1)
        elif action == "custom":
            self._apply_custom(form)
            self.show(len(self._items) - 1)
        elif action == "clear":
            self._votes = {}
            self._vote_store.save(self._votes)

    def _apply_custom(self, form: dict) -> None:
        custom = self._custom
        choices = (
            ("font", FONTS),
            ("left", COLOR_NAMES),
            ("right", COLOR_NAMES),
            ("gender", GENDERS),
            ("motion", MOTIONS),
            ("left_bg", BACKGROUND_NAMES),
            ("right_bg", BACKGROUND_NAMES),
        )
        for field, allowed in choices:
            if form.get(field) in allowed:
                setattr(custom, field, form[field])
        custom.names = form.get("names") == "on"
        names = ", names" if custom.names else ""
        custom.title = (
            f"custom: {custom.font}, {custom.left}/{custom.right} on"
            + f" {custom.left_bg}/{custom.right_bg},"
            + f" gender {custom.gender} {custom.motion}{names}"
        )

    def results(self) -> str:
        """Return one line per vote, in screen order."""
        lines = []
        for item in self._items:
            vote = self._votes.get(item.screen_id)
            if vote is not None:
                note = f" ({vote[1]})" if vote[1] else ""
                lines.append(f"{item.screen_id} {item.title}: {vote[0]}{note}")
        return "\n".join(lines) or "No votes yet."

    def respond(self, form: dict | None) -> str:
        """Apply the submitted form, if any, and return the lab page HTML.

        :param form: Submitted values by field name, or None to only show the page
        :return: HTML for the lab page
        """
        if form is None:
            if not self.shown:
                self.show(self._index)
        else:
            self._apply(form)
        item = self.item
        vote = self._votes.get(item.screen_id)
        custom = self._custom
        checked = " checked" if custom.names else ""
        custom_fields = (
            "".join(
                f'<label>{name}<select name="{field}">'
                + _options(choices, getattr(custom, field))
                + "</select></label>"
                for field, name, choices in (
                    ("font", "Font", FONTS),
                    ("left", "Left color", COLOR_NAMES),
                    ("right", "Right color", COLOR_NAMES),
                    ("left_bg", "Left background", BACKGROUND_NAMES),
                    ("right_bg", "Right background", BACKGROUND_NAMES),
                    ("gender", "Gender", GENDERS),
                    ("motion", "Gender motion", MOTIONS),
                )
            )
            + f'<label><input type="checkbox" name="names"{checked}> Team names</label>'
        )

        if isinstance(item, Pair):
            votes = PAIR_VOTES
            pair_buttons = (
                '<div class="row">'
                + "".join(
                    f'<button name="action" value="show_{side}"{shown}>'
                    + f"Show {side.upper()}: {_escape(screen.title)}</button>"
                    for side, screen, shown in (
                        ("a", item.a, "" if self._showing_b else ' class="showing"'),
                        ("b", item.b, ' class="showing"' if self._showing_b else ""),
                    )
                )
                + "</div>"
            )
        else:
            votes = COMPARE_VOTES if item.compare else RATING_VOTES
            pair_buttons = ""
        return _PAGE.format(
            screen_id=item.screen_id,
            position=self._index + 1,
            count=len(self._items),
            title=_escape(item.title),
            max_note=MAX_NOTE_LENGTH,
            pair_buttons=pair_buttons,
            vote_buttons="".join(
                f'<button class="{v}" name="action" value="{v}">{text}</button>'
                for v, text in votes
            ),
            vote=_escape(f"Your vote: {vote[0]} {vote[1]}")
            if vote
            else "Not voted yet.",
            screen_options="".join(
                _option(i.screen_id, f"{i.screen_id} {i.title}", i is item)
                for i in self._items
            ),
            auto="on" if self.auto_advance else "off",
            custom_id=CUSTOM_SCREEN_ID,
            custom_fields=custom_fields,
            results=_escape(self.results()),
        )


async def run_lab(
    matrixportal, keys, nvm, network, web_server, *extra_tasks, restart=None
) -> None:
    """Join Wi-Fi, show the lab page's QR code, then run the lab forever.

    :param matrixportal: MatrixPortal instance (real or simulator)
    :param keys: Keys instance (real or fake) for button input
    :param nvm: Byte buffer that keeps votes across reboots
    :param network: Network that joins Wi-Fi (real or simulator)
    :param web_server: Server for the lab page (real or simulator)
    :param extra_tasks: Additional coroutines to run alongside
    :param restart: Optional async callback for holding both buttons longer,
        which restarts into the scoreboard
    """
    display_manager = DisplayManager(matrixportal)
    lab = Lab(matrixportal.display, round_two_screens(), VoteStore(nvm))
    network_manager = NetworkManager(network, display_manager, web_server, lab.respond)
    network_manager.connect()
    if not display_manager.qr_code_shown:
        lab.show(0)
    await asyncio.gather(
        HardwareManager(keys).monitor_buttons(
            {BUTTON_LEFT: lab.previous, BUTTON_RIGHT: lab.next},
            hold_both_callback=lab.toggle_auto_advance,
            long_hold_both_callback=restart,
        ),
        network_manager.serve(),
        lab.run(),
        *extra_tasks,
    )
