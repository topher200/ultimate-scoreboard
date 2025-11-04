# LED Scoreboard

## Running Tests

This project includes tests that use fake hardware implementations to test the
code logic without requiring actual CircuitPython hardware.

### How to Run Tests

To run all tests:

```bash
python3 -m unittest discover tests
```

Or run tests directly:

```bash
python3 -m unittest tests/test_text_manager.py
python3 -m unittest tests/test_score_manager.py
```

### Fakes Directory

The `fakes/` directory contains mock implementations of CircuitPython hardware
components that allow testing without physical hardware:

- **`fakes/fake_matrixportal.py`** - Fake `MatrixPortal` and `Display` classes that mimic the hardware display interface, including `get_io_feed()` for Adafruit IO feed access
- **`fakes/fake_displayio.py`** - Fake `displayio.Group` class for managing display elements
- **`fakes/fake_label.py`** - Fake `Label` class that mimics `adafruit_display_text.label.Label`
- **`fakes/__init__.py`** - Package exports for easy importing

## Commands

### Set watchman to send updates to CircuitPython board

```bash
watchman watch-project .
watchman -- trigger . copy-to-CIRCUITPY '*.py' -- sh -c 'cp *.py /media/CIRCUITPY'
```

Delete with:

```bash
watchman trigger-del . copy-to-CIRCUITPY
```

## Resources

The base of this project is
[Matrix Portal Scoreboard](https://learn.adafruit.com/matrix-portal-scoreboard/overview).
That code snippet is MIT licensed so this project is MIT licensed.

The [matrixportal
lib](https://github.com/adafruit/Adafruit_CircuitPython_MatrixPortal) is
copied into this repo, mostly for development help.

```bash
$ git clone https://github.com/adafruit/Adafruit_CircuitPython_MatrixPortal lib/
# <delete everything but the adafruit_matrixportal directory>
```
