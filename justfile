# Set shell for command execution
set shell := ['bash', '-uc']

# List available commands
default:
    @just --list

# Run linter and formatter to fix issues automatically
lint:
    uv run ruff check --fix .
    uv run ty check --error-on-warning .

alias fmt := lint

# Run all tests
test:
    uv run pytest

# shortcut: run linter and tests
ci:
    @just lint
    @just test

# Monitor the board over serial
monitor:
    python3 -m serial.tools.miniterm /dev/ttyACM0 115200 || python3 -m serial.tools.miniterm /dev/ttyACM1 115200

# Set up watchman to copy Python files to CircuitPython board
watchman-setup-circuitpy:
    watchman watch-project .
    watchman -- trigger . copy-to-CIRCUITPY '*.py' 'lib/*.py' -- sh -c 'cp *.py /media/CIRCUITPY/ 2>/dev/null || true; mkdir -p /media/CIRCUITPY/lib && cp lib/*.py /media/CIRCUITPY/lib/ 2>/dev/null || true'
    @echo "Watchman trigger 'copy-to-CIRCUITPY' has been set up"

# Remove the watchman trigger for CircuitPython
watchman-remove:
    watchman trigger-del . copy-to-CIRCUITPY
    @echo "Watchman trigger 'copy-to-CIRCUITPY' has been removed"
