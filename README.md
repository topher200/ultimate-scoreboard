# LED Scoreboard

A wireless scoreboard for Ultimate, built on an Adafruit MatrixPortal S3 driving a 64x32 LED matrix.

## Usage

| Button | Action |
|--------|--------|
| Left | +1 left score |
| Right | +1 right score |
| Both held ~1s | Reset scores to 0-0 (undoable) |
| Hold Left, tap Right | Toggle gender matchup and retry joining Wi-Fi |
| Hold Right, tap Left | Undo last point |
| Both held ~5s | Restart into the legibility lab, or back to the scoreboard |

- **Team names** are set from a web page that the board serves. When the board joins Wi-Fi, it shows a QR code for the page. Scan it with a phone on the same network, then enter the names and tap Save. Saving or pressing any button hides the QR code; that press does nothing else. The board keeps the names across reboots.
- **Gender matchup** cycles automatically (WMP2 → MMP1 → MMP2 → WMP1). Use the toggle chord to switch whether the first point starts as WMP or MMP.
- **Timing dots** appear after each score and fade out — a visual indicator that the score was registered.

## Legibility Lab

The lab shows test screens with different colors, fonts, and layouts, so you can find the screens that are easiest to read from across the field. To start the lab, hold both buttons for about 5 seconds. The scores reset at 1 second, and then the board restarts into the lab. Hold both buttons for 5 seconds again to restart into the scoreboard. The board joins Wi-Fi and shows a QR code for the lab page. Scan it, then walk away from the board and use the page to step through the screens and vote Good, OK, or Bad on each. A vote moves to the next screen. The page lists all votes, and the board keeps them across reboots.

The board shows each screen's ID in the top-left corner for a few seconds. Without Wi-Fi, use the left and right buttons to step through the screens, and hold both to turn auto-advance on or off.

The custom screen (Z1) shows a font, colors, and layout that you pick on the page. Run the lab in the simulator with `just sim-lab`.

## Board Setup

- connect the board to USB
- install firmware from https://circuitpython.org/board/adafruit_matrixportal_s3/
- add `settings.toml` to the root of the board (see below)
- `just install-packages-on-circuitpy`
- `just deploy` to copy project files to the board
- `just monitor` to see the serial output

After the first deploy, the board can write its own files, and the CIRCUITPY drive is read-only over USB. `just deploy` restarts the board in USB mode over serial, which keeps the drive writable over USB for one boot. If serial does not respond, start CircuitPython safe mode: press reset, then press it again while the status LED blinks yellow.

### settings.toml

```toml
CIRCUITPY_WIFI_SSID =  ""
CIRCUITPY_WIFI_PASSWORD = ""
MEMFAULT_PROJECT_KEY = ""
```

Leave out `MEMFAULT_PROJECT_KEY` to turn off updates over Wi-Fi.

The settings page uses port 8080, so it does not conflict with the CircuitPython web workflow on port 80.

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

- **`fakes/fake_matrixportal.py`** - Fake `MatrixPortal` and `Display` classes that mimic the hardware display interface
- **`fakes/fake_network.py`** - Fake Wi-Fi network and settings page server
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
5. Serve the settings page from your laptop on port 8080, and show its QR code

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

A USB deploy puts the app in the board's root directory. A board with a dev build does not update over Wi-Fi. To set up a board that does, deploy a released version: `just deploy 1.2.0`.

### Updates over Wi-Fi (OTA)

The board gets app updates from Memfault releases. Each time the board joins Wi-Fi at power-on, it asks Memfault for a newer release. If there is one, the board shows "Updating", installs the release, and restarts. Updates change only the files in `src/`. To update CircuitPython or the libraries in `lib/`, use USB.

To publish a release, put `MEMFAULT_ORG_TOKEN`, `MEMFAULT_ORG`, and `MEMFAULT_PROJECT` in a `.env` file at the root of this repo, then run:

```bash
just release 1.2.0
```

Then activate it for the default cohort with `just activate 1.2.0`, or in the Memfault UI. Use a version that is newer than the last release. A new Memfault project rejects the board's update check until its first release exists.

The board keeps two app slots, and installs each update into the slot that is not running. The new release is on trial until it checks in with Memfault. If it crashes during its trial, the board goes back to the previous slot and skips that release from then on. Updates over Wi-Fi never change `boot.py`, `main.py`, `ota_loader.py`, or `safe_mode.py`; deploy those over USB.

## Resources

The base of this project is
[Matrix Portal Scoreboard](https://learn.adafruit.com/matrix-portal-scoreboard/overview).
That code snippet is MIT licensed so this project is MIT licensed. We've heavily
modified it since then.
