"""Strip execution outputs from Jupyter notebooks (nbstripout equivalent).

Uses only the standard library so it can run anywhere Python does:

    python scripts/strip_notebook_outputs.py <path> [<path> ...]
    python scripts/strip_notebook_outputs.py --all <repo-root>

For every notebook it clears cell outputs and resets execution counts, which
keeps the diff reviewable and the repository free of multi-megabyte output
blobs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def strip_notebook(path: Path) -> bool:
    """Clear outputs in ``path``; return True when the file changed."""
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return False

    changed = False
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        if cell.get("outputs"):
            cell["outputs"] = []
            changed = True
        if cell.get("execution_count") is not None:
            cell["execution_count"] = None
            changed = True

    if not changed:
        return False

    path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


def iter_notebooks(root: Path) -> list[Path]:
    skip = {".git", "node_modules", ".venv", "venv", "site-packages", "__pycache__", ".ipynb_checkpoints"}
    return [
        path
        for path in root.rglob("*.ipynb")
        if not any(part in skip for part in path.parts)
    ]


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2

    if args[0] == "--all":
        roots = [Path(item) for item in args[1:]] or [Path.cwd()]
    else:
        roots = [Path(item).parent if Path(item).suffix == ".ipynb" else Path(item) for item in args]

    changed: list[Path] = []
    for root in roots:
        candidates = [root] if root.suffix == ".ipynb" else iter_notebooks(root)
        for notebook in candidates:
            if notebook.is_file() and strip_notebook(notebook):
                changed.append(notebook)

    for notebook in changed:
        print(f"stripped {notebook}")
    print(f"{len(changed)} notebook(s) changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
