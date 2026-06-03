"""
aic_tools.marimo_session — Read marimo notebook cell outputs from the session cache.

Marimo saves cell outputs to __marimo__/session/<notebook_name>.json after execution.
This allows the AI to read console output and text outputs without screenshots.

Usage (CLI):
    python -m aic_tools.marimo_session <notebook.py>                 # list all cells
    python -m aic_tools.marimo_session <notebook.py> <cell_number>   # read cell output
    python -m aic_tools.marimo_session <notebook.py> <cell_number> <max_lines>

Usage (API):
    from aic_tools.marimo_session import read_cell_output, list_cells
    list_cells("experiments/23a/23a_basic_workflow.py")
    read_cell_output("experiments/23a/23a_basic_workflow.py", 8)

Cell numbering: 1-based, matches position in the session JSON (same as notebook display order).

Output behaviour:
    - console (stdout/stderr from print() calls) is shown in full
    - text/plain and text/markdown outputs are shown up to max_lines
    - text/html with embedded images is reported as size + mime summary only
      (base64 PNG strings are not dumped — use screenshot_page() to view images)

Session file location:
    Given notebook at <dir>/<name>.py, the session cache is:
    <dir>/__marimo__/session/<name>.py.json
"""

import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_session_path(notebook_path: str) -> Path:
    """Return the path to the marimo session JSON for the given notebook."""
    nb = Path(notebook_path).resolve()
    return nb.parent / "__marimo__" / "session" / (nb.name + ".json")


def _load_session(notebook_path: str) -> list:
    """Load and return the cells list from the session JSON."""
    session_path = _find_session_path(notebook_path)
    if not session_path.exists():
        raise FileNotFoundError(
            f"Session cache not found: {session_path}\n"
            "Run the notebook in marimo first to generate the cache."
        )
    with open(session_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("cells", [])


def _summarise_output(output: dict) -> str:
    """Return a short summary string for one output entry."""
    data = output.get("data", {})
    parts = []
    for mime, value in data.items():
        if not isinstance(value, str):
            parts.append(mime)
            continue
        if mime == "text/html":
            # Check for embedded image
            img_match = re.search(r'data:(image/[^;]+);base64,', value)
            if img_match:
                parts.append(f"HTML ({len(value):,} bytes, {img_match.group(1)} embedded)")
            else:
                parts.append(f"HTML ({len(value):,} bytes)")
        elif mime in ("text/plain", "text/markdown"):
            preview = value.split("\n")[0][:60]
            parts.append(f"{mime}: {preview!r}")
        else:
            parts.append(mime)
    return ", ".join(parts) if parts else "(empty)"


def _format_cell_output(cell: dict, cell_number: int, max_lines: int) -> str:
    """Format all console and output content for one cell."""
    lines: list[str] = [f"=== Cell {cell_number} (id={cell['id']}) ==="]

    # Console (stdout/stderr from print() etc.)
    console = cell.get("console", [])
    if console:
        lines.append("--- console ---")
        for entry in console:
            text = entry.get("text", "")
            name = entry.get("name", "stdout")
            if name == "stderr":
                text = "[stderr] " + text
            lines.append(text.rstrip())
    else:
        lines.append("(no console output)")

    # Outputs
    outputs = cell.get("outputs", [])
    if outputs:
        lines.append("--- output ---")
        for output in outputs:
            data = output.get("data", {})
            for mime, value in data.items():
                if not isinstance(value, str):
                    lines.append(f"[{mime}: non-string value]")
                    continue
                if mime == "text/html":
                    img_match = re.search(r'data:(image/[^;]+);base64,', value)
                    if img_match:
                        lines.append(
                            f"[{mime}: {len(value):,} bytes with embedded "
                            f"{img_match.group(1)} — use screenshot_page() to view]"
                        )
                    else:
                        # Show truncated HTML for non-image HTML
                        html_lines = value.split("\n")
                        shown = html_lines[:max_lines]
                        lines.extend(shown)
                        if len(html_lines) > max_lines:
                            lines.append(f"... ({len(html_lines) - max_lines} more lines)")
                else:
                    text_lines = value.split("\n")
                    shown = text_lines[:max_lines]
                    lines.extend(shown)
                    if len(text_lines) > max_lines:
                        lines.append(f"... ({len(text_lines) - max_lines} more lines)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_cells(notebook_path: str) -> str:
    """Return a summary table of all cells in the session cache."""
    cells = _load_session(notebook_path)
    lines = [f"Marimo session: {_find_session_path(notebook_path)}", ""]
    lines.append(f"{'#':<4} {'id':<8} {'console':<8} {'output'}")
    lines.append("-" * 70)
    for i, cell in enumerate(cells, 1):
        console_count = len(cell.get("console", []))
        outputs = cell.get("outputs", [])
        out_summary = _summarise_output(outputs[0]) if outputs else "(none)"
        lines.append(f"{i:<4} {cell['id']:<8} {console_count:<8} {out_summary}")
    return "\n".join(lines)


def read_cell_output(notebook_path: str, cell_number: int, max_lines: int = 100) -> str:
    """Return formatted output for one cell (1-based)."""
    cells = _load_session(notebook_path)
    if not (1 <= cell_number <= len(cells)):
        raise IndexError(
            f"Cell number {cell_number} out of range (1–{len(cells)})"
        )
    return _format_cell_output(cells[cell_number - 1], cell_number, max_lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    notebook_path = args[0]

    if len(args) == 1:
        # List mode
        try:
            print(list_cells(notebook_path))
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Cell read mode
    try:
        cell_number = int(args[1])
    except ValueError:
        print(f"Error: cell_number must be an integer, got {args[1]!r}", file=sys.stderr)
        sys.exit(1)

    max_lines = 100
    if len(args) >= 3:
        try:
            max_lines = int(args[2])
        except ValueError:
            print(f"Error: max_lines must be an integer, got {args[2]!r}", file=sys.stderr)
            sys.exit(1)

    try:
        print(read_cell_output(notebook_path, cell_number, max_lines))
    except (FileNotFoundError, IndexError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
