#!/usr/bin/env python3
"""Linter to detect typing module imports in CircuitPython code.

This script builds a dependency graph from entry points (main.py, src/app_setup.py)
and checks all files in that chain for imports unavailable to CircuitPython,
such as the 'typing' module. If these are left in the code the board will fail
to run.
"""

import ast
import sys
from pathlib import Path


class TypingImportVisitor(ast.NodeVisitor):
    """AST visitor to detect typing imports."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.violations: list[tuple[int, str]] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Check for 'import typing' statements."""
        for alias in node.names:
            if alias.name == "typing":
                self.violations.append((node.lineno, f"import typing"))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check for 'from typing import ...' statements."""
        if node.module == "typing":
            imported_names = ", ".join(alias.name for alias in node.names)
            self.violations.append(
                (node.lineno, f"from typing import {imported_names}")
            )
        self.generic_visit(node)


class DependencyGraphBuilder:
    """Builds a dependency graph from entry points."""

    def __init__(
        self, root_dir: Path, excluded_dirs: set[str], excluded_files: set[str]
    ):
        self.root_dir = root_dir
        self.excluded_dirs = excluded_dirs
        self.excluded_files = excluded_files
        self.visited_files: set[Path] = set()
        self.files_to_check: set[Path] = set()

    def should_exclude(self, filepath: Path) -> bool:
        """Check if a file should be excluded from checking."""
        # Check if any parent directory is excluded
        for parent in filepath.parents:
            if parent.name in self.excluded_dirs:
                return True

        # Check if the file itself is excluded
        if filepath.name in self.excluded_files:
            return True

        # Check if file is in an excluded directory
        parts = filepath.parts
        for excluded_dir in self.excluded_dirs:
            if excluded_dir in parts:
                return True

        return False

    def resolve_import(self, module_name: str, from_file: Path) -> Path | None:
        """Resolve an import to a file path."""
        # Handle relative imports
        if module_name.startswith("."):
            # Count leading dots for relative import level
            level = len(module_name) - len(module_name.lstrip("."))
            module_name = module_name.lstrip(".")

            # Get the directory of the file doing the import
            base_dir = from_file.parent
            for _ in range(level - 1):
                base_dir = base_dir.parent

            # Build path from base directory
            if module_name:
                parts = module_name.split(".")
                target_path = base_dir / Path(*parts)
            else:
                target_path = base_dir
        else:
            # Absolute import - only check if it's in src/
            if module_name.startswith("src."):
                # Remove 'src.' prefix
                module_name = module_name[4:]
            elif not module_name.startswith("src/"):
                # External package, skip
                return None

            parts = module_name.split(".")
            target_path = self.root_dir / "src" / Path(*parts)

        # Try .py extension
        py_file = target_path.with_suffix(".py")
        if py_file.exists() and not self.should_exclude(py_file):
            return py_file

        # Try as a directory with __init__.py
        init_file = target_path / "__init__.py"
        if init_file.exists() and not self.should_exclude(init_file):
            return init_file

        return None

    def extract_imports(self, filepath: Path) -> list[str]:
        """Extract import statements from a Python file."""
        try:
            with open(filepath, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(filepath))
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not parse {filepath}: {e}", file=sys.stderr)
            return []

        imports: list[str] = []

        class ImportExtractor(ast.NodeVisitor):
            def visit_Import(self, node: ast.Import) -> None:
                for alias in node.names:
                    imports.append(alias.name)
                self.generic_visit(node)

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                if node.module:
                    imports.append(node.module)
                self.generic_visit(node)

        extractor = ImportExtractor()
        extractor.visit(tree)
        return imports

    def build_graph(self, entry_points: list[Path]) -> None:
        """Build dependency graph starting from entry points."""
        to_process = list(entry_points)

        while to_process:
            current_file = to_process.pop(0)

            if current_file in self.visited_files:
                continue

            if not current_file.exists():
                continue

            if self.should_exclude(current_file):
                continue

            self.visited_files.add(current_file)
            self.files_to_check.add(current_file)

            # Extract imports from this file
            imports = self.extract_imports(current_file)

            # Resolve imports and add to processing queue
            for import_name in imports:
                # Skip standard library and external packages
                if import_name in {
                    "asyncio",
                    "board",
                    "displayio",
                    "terminalio",
                    "keypad",
                    "adafruit_matrixportal",
                    "adafruit_display_text",
                }:
                    continue

                # Skip if it's clearly an external package (has dots and doesn't start with src)
                if "." in import_name and not import_name.startswith("src"):
                    # Check if it's a known external package
                    first_part = import_name.split(".")[0]
                    if first_part not in {"src", "fakes", "simulator"}:
                        continue

                resolved = self.resolve_import(import_name, current_file)
                if resolved and resolved not in self.visited_files:
                    to_process.append(resolved)


def check_file_for_typing(filepath: Path) -> list[tuple[int, str]]:
    """Check a single file for typing imports."""
    try:
        with open(filepath, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {filepath}: {e}", file=sys.stderr)
        return []

    visitor = TypingImportVisitor(filepath)
    visitor.visit(tree)
    return visitor.violations


def main() -> int:
    """Main entry point for the linter."""
    root_dir = Path(__file__).parent.parent

    # Entry points to check
    entry_points = [
        root_dir / "main.py",
        root_dir / "src" / "app_setup.py",
    ]

    # Directories to exclude
    excluded_dirs = {
        "tests",
        "stubs",
        "fakes",
        "simulator",
        "__pycache__",
        ".git",
        ".venv",
        "scripts",
    }

    # Files to exclude (files that intentionally use typing with TYPE_CHECKING)
    excluded_files = {
        "compat.py",  # Uses typing with try/except and TYPE_CHECKING
    }

    # Build dependency graph
    builder = DependencyGraphBuilder(root_dir, excluded_dirs, excluded_files)
    builder.build_graph(entry_points)

    # Check all files in the dependency graph
    all_violations: dict[Path, list[tuple[int, str]]] = {}
    for filepath in sorted(builder.files_to_check):
        violations = check_file_for_typing(filepath)
        if violations:
            all_violations[filepath] = violations

    # Report violations
    if all_violations:
        print(
            "Error: typing module imports detected in CircuitPython code:",
            file=sys.stderr,
        )
        print("", file=sys.stderr)
        for filepath in sorted(all_violations.keys()):
            rel_path = filepath.relative_to(root_dir)
            for lineno, import_stmt in all_violations[filepath]:
                print(f"  {rel_path}:{lineno}: {import_stmt}", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "CircuitPython does not include the typing module. "
            "Use src.compat for typing compatibility.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
