"""AST guard: domain/ may only import stdlib, pydantic, and other domain modules."""

from __future__ import annotations

import ast
from pathlib import Path

DOMAIN_ROOT = Path(__file__).resolve().parents[2] / "src" / "domain"
ALLOWED_TOP_LEVEL = frozenset(
    {"pydantic", "typing", "datetime", "enum", "functools", "collections"}
)


def _collect_imports(path: Path) -> list[tuple[str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name.split(".")[0], str(path)))
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            if node.level > 0:
                continue
            imports.append((node.module.split(".")[0], str(path)))
    return imports


def test_domain_imports_only_stdlib_pydantic_and_domain() -> None:
    violations: list[str] = []
    for py_file in DOMAIN_ROOT.rglob("*.py"):
        for top_level, file_path in _collect_imports(py_file):
            if top_level == "src" and "domain" in file_path.replace("\\", "/"):
                continue
            if top_level in ALLOWED_TOP_LEVEL:
                continue
            if top_level == "domain" or top_level.startswith("domain"):
                continue
            violations.append(f"{file_path}: forbidden import '{top_level}'")
    assert not violations, "Domain dependency rule violations:\n" + "\n".join(violations)
