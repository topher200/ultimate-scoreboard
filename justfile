# Set shell for command execution
set shell := ['bash', '-uc']

# List available commands
default:
    @just --list

# Run linter and formatter to fix issues automatically
lint:
    uv run ruff check --fix --quiet .
    uv run pyrefly check --summary=none .
    uv run python scripts/check_circuitpython_imports.py

alias fmt := lint

# Run all tests
test:
    uv run pytest -qq

# shortcut: run linter and tests
ci:
    @just lint
    @just test

# Monitor the board over serial
monitor:
    @echo "Monitoring serial output. Press Ctrl+] to exit."
    python3 -m serial.tools.miniterm /dev/ttyACM0 115200 || python3 -m serial.tools.miniterm /dev/ttyACM1 115200

# Set up watchman to copy Python files to CircuitPython board
watchman-setup-circuitpy:
    watchman watch-project .
    watchman -- trigger . copy-to-CIRCUITPY '*.py' 'src/*.py' -- sh -c 'cp *.py /media/CIRCUITPY/ 2>/dev/null || true; cp -r src /media/CIRCUITPY 2>/dev/null || true'
    @echo "Watchman trigger 'copy-to-CIRCUITPY' has been set up"

# Remove the watchman trigger for CircuitPython
watchman-remove:
    watchman trigger-del . copy-to-CIRCUITPY
    @echo "Watchman trigger 'copy-to-CIRCUITPY' has been removed"

# Install packages on CircuitPython board
install-packages-on-circuitpy:
    uv run circup install -r requirements.txt

# Run the local simulator with visual display
simulator:
    uv sync --group simulator
    uv run python local_main.py

alias sim := simulator
