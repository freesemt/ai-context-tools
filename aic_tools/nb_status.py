"""
aic_tools.nb_status — Read notebook execution status from .ipynb JSON on disk.

Reports which cells have been executed (and in what order) by reading the
``execution_count`` field stored in the .ipynb file.

---

IMPORTANT — disk vs. live kernel:

The .ipynb file is a *snapshot* of the last save, not live kernel state.
Two events can make it stale:

1. **External file rewrite** (``json.dump``, PowerShell, etc.) while the
   notebook is open in VS Code — VS Code reloads the document model from
   disk, losing any unsaved execution counts.

2. **Cells run but not saved** — execution counts live in the VS Code
   document model until the file is saved.

ROUTING RULE FOR AI ASSISTANTS:

    ┌─────────────────────────────────────────────────────────────────┐
    │ "Which cells were run?"  →  copilot_getNotebookSummary           │
    │     → execution counts in the CELL LIST (document model)         │
    │     → kernel variables section (process memory, always live)     │
    │                                                                   │
    │ If execution counts show "not executed" but a variable you expect │
    │ IS in the kernel variables list → the disk/document model is      │
    │ stale. Trust the kernel variables, not the execution counts.      │
    │                                                                   │
    │ aic-nb-status  →  quick offline summary; use when VS Code is not  │
    │     open or to cross-check after an external file write           │
    └─────────────────────────────────────────────────────────────────┘

Usage (CLI):
    python -m aic_tools.nb_status <notebook.ipynb>
    python -m aic_tools.nb_status <notebook.ipynb> --executed-only
    python -m aic_tools.nb_status <notebook.ipynb> --json

Usage (API):
    from aic_tools.nb_status import get_execution_status
    rows = get_execution_status("path/to/notebook.ipynb")
    # Returns list of dicts:
    # [
    #   {
    #     "cell_number": 1,          # 1-based, matches VS Code display
    #     "cell_id": "VSC-abc123",
    #     "cell_type": "code",       # "code" | "markdown"
    #     "execution_count": 3,      # None if never executed / not saved
    #     "first_line": "# [1] Setup",
    #   },
    #   ...
    # ]

Entry point (after install):
    aic-nb-status experiments/13h.ipynb
    aic-nb-status experiments/13h.ipynb --executed-only
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _load(nb_path: str) -> tuple[Path, dict]:
    path = Path(nb_path)
    if not path.exists():
        raise FileNotFoundError(f"Notebook not found: {nb_path}")
    with open(path, encoding="utf-8") as f:
        return path, json.load(f)


def _first_line(cell: dict) -> str:
    src = cell.get("source", [])
    if isinstance(src, list):
        src = "".join(src)
    first = src.strip().splitlines()[0] if src.strip() else "(empty)"
    return first[:80]


def get_execution_status(nb_path: str) -> list[dict]:
    """Return execution status for every cell in the notebook.

    Reads from the .ipynb file on disk — see module docstring for caveats.

    Returns
    -------
    list[dict]
        One entry per cell with keys: cell_number, cell_id, cell_type,
        execution_count, first_line.
        execution_count is None for markdown cells and unexecuted code cells.
    """
    _, nb = _load(nb_path)
    rows = []
    cell_number = 0
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "markdown":
            cell_number += 1
            rows.append({
                "cell_number": cell_number,
                "cell_id": cell.get("id", ""),
                "cell_type": "markdown",
                "execution_count": None,
                "first_line": _first_line(cell),
            })
        else:
            cell_number += 1
            rows.append({
                "cell_number": cell_number,
                "cell_id": cell.get("id", ""),
                "cell_type": "code",
                "execution_count": cell.get("execution_count"),
                "first_line": _first_line(cell),
            })
    return rows


def _print_table(rows: list[dict], executed_only: bool) -> None:
    to_show = [r for r in rows if r["cell_type"] == "code"] if executed_only else rows
    if executed_only:
        to_show = [r for r in to_show if r["execution_count"] is not None]

    # Header
    print(f"{'#':>3}  {'exec':>4}  {'type':<8}  first line")
    print("-" * 72)
    for r in to_show:
        ec = str(r["execution_count"]) if r["execution_count"] is not None else "-"
        print(f"{r['cell_number']:>3}  {ec:>4}  {r['cell_type']:<8}  {r['first_line']}")

    executed = [r for r in rows if r["cell_type"] == "code" and r["execution_count"] is not None]
    code_cells = [r for r in rows if r["cell_type"] == "code"]
    print()
    print(f"Executed: {len(executed)} / {len(code_cells)} code cells  "
          f"({len(rows)} total including markdown)")
    if executed:
        max_ec = max(r["execution_count"] for r in executed)
        in_order = sorted(executed, key=lambda r: r["execution_count"])
        print(f"Execution order: cells {[r['cell_number'] for r in in_order]}  "
              f"(max count={max_ec})")
    print()
    print("NOTE: execution counts read from disk — may be stale if file was")
    print("      externally rewritten while the notebook was open in VS Code.")
    print("      Use copilot_getNotebookSummary kernel-variables for live state.")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="aic-nb-status",
        description="Show notebook execution status from the .ipynb file on disk.",
    )
    parser.add_argument("notebook", help="Path to the .ipynb file")
    parser.add_argument(
        "--executed-only", action="store_true",
        help="Show only code cells that have been executed",
    )
    parser.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Output as JSON instead of a table",
    )
    args = parser.parse_args()

    rows = get_execution_status(args.notebook)

    if args.as_json:
        print(json.dumps(rows, indent=2))
    else:
        _print_table(rows, executed_only=args.executed_only)


if __name__ == "__main__":
    main()
