# AGENTS.md

Guide for AI agents working on this codebase.

## Command Execution

**Always use `uv run` for Python commands:**

```bash
# ✓ Correct
uv run pytest
uv run ruff check --fix .
uv run pyrefly check .

# ✗ Wrong
python -m pytest
pytest
python -m ruff
```

**Use `just` commands for common tasks:**

```bash
just test    # Run all tests
just lint    # Run ruff and pyrefly
just ci      # Run lint and test
```

## Project Structure

- `lib/` - Source code modules
- `tests/` - Test files
- `fakes/` - Mock CircuitPython hardware implementations
- `main.py` - Entry point for CircuitPython board
- `conftest.py` - Pytest configuration for mocking CircuitPython modules

## Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_display_manager.py

# Or use just
just test
```

## Linting and Formatting

```bash
# Run both ruff and pyrefly
just lint

# Or manually
uv run ruff check --fix .
uv run pyrefly check .
```

## Testing Conventions

- Tests mock CircuitPython modules via `conftest.py`
- Fake implementations in `fakes/` directory provide testable versions of hardware components
- Tests can run without actual CircuitPython hardware

## Agent Conventions

- ALWAYS verify all changes with `just ci` before returning to the user
