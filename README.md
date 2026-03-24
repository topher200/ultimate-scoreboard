# LED Scoreboard

A wireless scoreboard for Ultimate, built on an Adafruit MatrixPortal S3 driving a 64x32 LED matrix.

## Usage

| Button | Action |
|--------|--------|
| Left | +1 left team score |
| Right | +1 right team score |
| Left + Right (short press) | Undo last point |
| Left + Right (hold ~1s) | Toggle gender matchup (WMP/MMP) and refresh team names |
| Up (on-board button) | Toggle gender matchup (WMP/MMP) and refresh team names |
| Down (on-board button) | Undo last point |

- **Team names** are set via [Adafruit IO](https://io.adafruit.com) feeds (`scores-group.left-team-name` and `scores-group.right-team-name`). Update the feed values there and press Up to refresh, or they load automatically on boot.
- **Gender matchup** cycles automatically as scores change (WMP2 → MMP1 → MMP2 → WMP1). Hold both Left + Right for ~1 second (or press the on-board Up button) to toggle whether the first point starts as WMP or MMP.
- **Timing dots** appear after each score and fade out over a few seconds — a visual indicator that the score was registered.

## Board Setup

- connect the board to USB
- install firmware from https://circuitpython.org/board/adafruit_matrixportal_s3/
- add `settings.toml` to the root of the board (see below)
- `just install-packages-on-circuitpy`
- `just deploy` to copy project files to the board
- `just monitor` to see the serial output

### settings.toml

```toml
CIRCUITPY_WIFI_SSID =  ""
CIRCUITPY_WIFI_PASSWORD = ""

ADAFRUIT_AIO_USERNAME = ""
ADAFRUIT_AIO_KEY      = "aio_..."
```

## Development Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync
```

For auto-deploy on file changes, install [watchexec](https://watchexec.github.io/):

```bash
brew install watchexec
```

## Just Command Runner

This project uses [just](https://github.com/casey/just) for running common development tasks.

To install just, visit the [installation
instructions](https://github.com/casey/just#installation). Example: `$ brew
install just`

Common commands:

- `just` - List all available commands
- `just lint` - Run linter and formatter to automatically fix issues
- `just test` - Run all tests
- `just ci` - Run linter and tests (CI check)
- `just simulator` (or `just sim`) - Run the local visual display simulator
- `just deploy` - Copy project files to CircuitPython board
- `just watch-deploy` - Watch for changes and auto-deploy to board

## Running Tests

This project includes tests that use fake hardware implementations to test the
code logic without requiring actual CircuitPython hardware.

### How to Run Tests

To run all tests:

```bash
just test
```

Or run specific test files directly:

```bash
uv run pytest tests/test_display_manager.py
uv run pytest tests/test_score_manager.py
```

### Fakes Directory

The `fakes/` directory contains mock implementations of CircuitPython hardware
components that allow testing without physical hardware:

- **`fakes/fake_matrixportal.py`** - Fake `MatrixPortal` and `Display` classes that mimic the hardware display interface, including `get_io_feed()` for Adafruit IO feed access
- **`fakes/fake_displayio.py`** - Fake `displayio.Group` class for managing display elements
- **`fakes/fake_label.py`** - Fake `Label` class that mimics `adafruit_display_text.label.Label`
- **`fakes/__init__.py`** - Package exports for easy importing

## Local Development with Visual Simulator

You can run the application locally on your laptop with a visual display simulator that shows what the LED matrix would display. This is useful for testing new features and behaviors without physical hardware.

### Running the Simulator

To run the application with the visual display simulator:

```bash
just simulator
```

Or using the shorter alias:

```bash
just sim
```

This command will automatically install simulator dependencies if needed and then start the simulator. It will:

1. Open a Pygame window showing the 64x32 LED matrix display scaled up (1280x640 pixels)
2. Run the full application with fake hardware
3. Update the display in real-time as the application runs
4. Allow you to test all features without physical hardware

## Development Commands

### Linting and Formatting

Run linter and formatter to automatically fix issues:

```bash
just lint
```

### Deploy to CircuitPython board

```bash
just deploy
```

Or watch for changes and auto-deploy:

```bash
just watch-deploy
```

## Resources

The base of this project is
[Matrix Portal Scoreboard](https://learn.adafruit.com/matrix-portal-scoreboard/overview).
That code snippet is MIT licensed so this project is MIT licensed. We've heavily
modified it since then.
