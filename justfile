# Set shell for command execution
set shell := ['bash', '-uc']

# List available commands
default:
@just --list

# Run linter and formatter to fix issues automatically
lint:
uv run ruff check --fix .
uv run ruff format .

# Run all tests
test:
uv run pytest

# Set up watchman to copy Python files to CircuitPython board
watchman-setup-circuitpy:
watchman watch-project .
watchman -- trigger . copy-to-CIRCUITPY '*.py' -- sh -c 'cp *.py /media/CIRCUITPY'
@echo "Watchman trigger 'copy-to-CIRCUITPY' has been set up"

# Remove the watchman trigger for CircuitPython
watchman-remove:
watchman trigger-del . copy-to-CIRCUITPY
@echo "Watchman trigger 'copy-to-CIRCUITPY' has been removed"
