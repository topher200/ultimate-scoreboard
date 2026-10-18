# Set shell for command execution
set shell := ['bash', '-uc']
set dotenv-load
set dotenv-override

# Command that prints the mount point of the board's CIRCUITPY drive; set the
# CIRCUITPY env var to override it
circuitpy := "'" + just_executable() + "' --justfile '" + justfile() + "' _circuitpy"

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

_circuitpy:
    @echo "${CIRCUITPY:-$(for d in /Volumes /run/media/$(id -un) /media/$(id -un); do [ -f "$d/CIRCUITPY/boot_out.txt" ] && { echo "$d/CIRCUITPY"; exit; }; done; echo /media/CIRCUITPY)}"

# Mount the board's CIRCUITPY drive (Linux)
mount:
    @d=$({{circuitpy}}); test -f "$d/boot_out.txt" && echo "Already mounted at $d" || udisksctl mount -b /dev/disk/by-label/CIRCUITPY

# Deploy project files to CircuitPython board; give a release version to let it update over Wi-Fi
deploy version="dev": usb-mode
    #!/usr/bin/env bash
    set -euo pipefail
    d=$({{circuitpy}})
    rsync -r --delete --delete-excluded --checksum --exclude __pycache__ --exclude .DS_Store --exclude version.py src/ "$d/src/"
    cp boot.py main.py ota_loader.py safe_mode.py "$d/"
    rm -f "$d/ota_state.json" "$d/ota_state.tmp"
    if [ "{{version}}" != dev ]; then echo 'VERSION = "{{version}}"' > "$d/src/version.py"; fi
    sync
    uv run python scripts/board_serial.py reset
    echo "Deployed to $d"

# Restart the board with CIRCUITPY writable over USB, and wait until it is
usb-mode:
    #!/usr/bin/env bash
    set -euo pipefail
    writable() { local d; d=$({{circuitpy}}); touch "$d/.write_test" 2>/dev/null && rm -f "$d/.write_test"; }
    writable && exit 0
    echo "Restarting the board in USB mode"
    uv run python scripts/board_serial.py usb-mode
    for _ in $(seq 60); do
        sleep 1
        writable && exit 0
        if command -v udisksctl >/dev/null && [ -e /dev/disk/by-label/CIRCUITPY ]; then
            udisksctl mount -b /dev/disk/by-label/CIRCUITPY >/dev/null 2>&1 || true
        fi
    done
    echo "CIRCUITPY is not writable; start safe mode (press reset, then again while the LED blinks yellow), or set CIRCUITPY to its path" >&2
    exit 1

# Stop the running code and soft reload the board over serial
reboot:
    uv run python scripts/board_serial.py reload

# Watch for changes and auto-deploy to CircuitPython board
watch-deploy:
    watchexec -w main.py -w src/ -- just deploy

# Build the OTA bundle for a software version
bundle version:
    uv run python scripts/build_bundle.py {{version}} build/scoreboard-{{version}}.bundle

# Build the OTA bundle and upload it to Memfault as a release
release version: (bundle version)
    uvx --from memfault-cli memfault --org-token "$MEMFAULT_ORG_TOKEN" --org "$MEMFAULT_ORG" --project "$MEMFAULT_PROJECT" upload-ota-payload --hardware-version matrixportal-s3 --software-type scoreboard --software-version {{version}} build/scoreboard-{{version}}.bundle

# Activate a Memfault release for the default cohort, so boards install it
activate version:
    uvx --from memfault-cli memfault --org-token "$MEMFAULT_ORG_TOKEN" --org "$MEMFAULT_ORG" --project "$MEMFAULT_PROJECT" deploy-release --release-version {{version}} --cohort default

# Install packages on CircuitPython board
install-packages-on-circuitpy:
    uv run circup install -r requirements.txt

# Run the local simulator with visual display
simulator:
    uv sync --group simulator
    uv run python local_main.py

alias sim := simulator

# Run the legibility lab in the local simulator
simulator-lab:
    uv sync --group simulator
    uv run python local_main.py --lab

alias sim-lab := simulator-lab
