# Set shell for command execution
set shell := ['bash', '-uc']

# Mount point of the board's CIRCUITPY drive; override with the CIRCUITPY env var
circuitpy := env("CIRCUITPY", `for d in /Volumes /run/media/$(id -un) /media/$(id -un); do [ -f "$d/CIRCUITPY/boot_out.txt" ] && { echo "$d/CIRCUITPY"; exit; }; done; echo /media/CIRCUITPY`)

# List available commands
default:
    @just --list

# Run linter and formatter to fix issues automatically
lint:
    uv run ruff check --fix --quiet .
    uv run ruff format --quiet .
    uv run pyrefly check --summary=none
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
    uv run python -m serial.tools.miniterm hwgrep://MatrixPortal 115200

# Deploy project files to CircuitPython board
deploy:
    @test -f "{{circuitpy}}/boot_out.txt" || { echo "No CircuitPython board found; mount it or set CIRCUITPY to its path" >&2; exit 1; }
    cp main.py "{{circuitpy}}/"
    cp -r src "{{circuitpy}}/"
    @echo "Deployed to {{circuitpy}}"

# Watch for changes and auto-deploy to CircuitPython board
watch-deploy:
    watchexec -w main.py -w src/ -- just deploy

# Install packages on CircuitPython board
install-packages-on-circuitpy:
    uv run circup install -r requirements.txt

# Run the local simulator with visual display
simulator:
    uv sync --group simulator
    uv run python local_main.py

alias sim := simulator
