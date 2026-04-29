#!/usr/bin/env python3
"""Regenerate root __init__.py from subpackage __all__ lists."""

from __future__ import annotations

import ast
from pathlib import Path


def parse_all(init_file: Path) -> list[str] | None:
    """Parse __all__ from a module's AST."""
    try:
        tree = ast.parse(init_file.read_text())
    except SyntaxError:
        return None
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "__all__"
                    and isinstance(node.value, ast.List)
                ):
                    return [elt.value for elt in node.value.elts if isinstance(elt, ast.Constant)]
    return None


def collect_exports(pkg_dir: Path) -> dict[str, list[str]]:
    """Scan subpackages for __all__ definitions."""
    exports: dict[str, list[str]] = {}
    for subdir in sorted(pkg_dir.iterdir()):
        if not subdir.is_dir() or subdir.name.startswith("__"):
            continue
        init_file = subdir / "__init__.py"
        if not init_file.exists():
            continue
        symbols = parse_all(init_file)
        if symbols:
            exports[subdir.name] = symbols
    return exports


def build_imports(exports: dict[str, list[str]]) -> list[str]:
    """Generate import lines from collected exports."""
    lines: list[str] = []
    for module, symbols in sorted(exports.items()):
        pkg = f"another_intelligence.{module}"
        if len(symbols) == 1:
            lines.append(f"from {pkg} import {symbols[0]}")
        else:
            lines.append(f"from {pkg} import (")
            for sym in symbols:
                lines.append(f"    {sym},")
            lines.append(")")
    return lines


def build_all(exports: dict[str, list[str]]) -> list[str]:
    """Generate root __all__ list from collected exports."""
    symbols: list[str] = ["__version__", "DigitalBrain"]
    for mod_symbols in exports.values():
        symbols.extend(mod_symbols)
    return symbols


def generate_init(pkg_dir: Path) -> str:
    """Generate the full root __init__.py contents."""
    exports = collect_exports(pkg_dir)
    imports = build_imports(exports)
    all_symbols = build_all(exports)

    lines = [
        '"""Another-Intelligence — A persistent neuroscience-grounded digital brain."""',
        "",
        "from another_intelligence.brain import DigitalBrain",
    ]
    lines.extend(imports)
    lines.append("")
    lines.append('__version__ = "0.1.0"')
    lines.append("__all__ = [")
    for sym in all_symbols:
        lines.append(f'    "{sym}",')
    lines.append("]")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    pkg_dir = Path(__file__).resolve().parent.parent / "src" / "another_intelligence"
    if not pkg_dir.exists():
        raise RuntimeError(f"Package directory not found: {pkg_dir}")

    content = generate_init(pkg_dir)
    init_file = pkg_dir / "__init__.py"
    init_file.write_text(content)
    print(f"Regenerated {init_file}")


if __name__ == "__main__":
    main()
