"""
aic_tools.notebook — Read stdout output of a specific notebook cell.

Bypasses the built-in read_notebook_cell_output tool size limit by reading
the .ipynb JSON directly from disk.

Usage (CLI):
    python -m aic_tools.notebook <notebook.ipynb> <cell_number> [max_lines]

Usage (API):
    from aic_tools.notebook import read_cell_output
    read_cell_output("path/to/notebook.ipynb", 14)

Arguments:
    notebook     Path to the .ipynb file
    cell_number  1-based cell number (matches VS Code display)
    max_lines    Max lines to print (default: 100, 0 = all)

Routing rule for AI assistants:
    After copilot_getNotebookSummary, check each cell's mime types.
    If a cell has application/vnd.code.notebook.stdout, call this tool
    instead of read_notebook_cell_output — the built-in tool will fail
    with "output too large" for stdout-heavy cells.
"""

import json
import sys
from pathlib import Path


def read_cell_output(nb_path, cell_number: int, max_lines: int = 100) -> str:
    """Return the stdout output of a notebook cell as a string.

    Args:
        nb_path:     Path to the .ipynb file (str or Path).
        cell_number: 1-based cell index (all cells, matching VS Code display).
        max_lines:   Maximum lines to return. 0 = unlimited.

    Raises:
        FileNotFoundError: if the notebook file does not exist.
        ValueError:        if cell_number is out of range.
    """
    path = Path(nb_path)
    if not path.exists():
        raise FileNotFoundError(f"Notebook not found: {nb_path}")

    with open(path, encoding="utf-8") as f:
        nb = json.load(f)

    cells = nb["cells"]
    if cell_number < 1 or cell_number > len(cells):
        raise ValueError(
            f"cell_number {cell_number} out of range (1–{len(cells)})"
        )

    cell = cells[cell_number - 1]
    if cell["cell_type"] != "code":
        return f"Cell {cell_number} is a markdown cell — no output."

    outputs = cell.get("outputs", [])
    if not outputs:
        return f"(no stdout output)"

    lines_out: list[str] = []
    lines_out.append(
        f"Cell {cell_number} (execution_count={cell.get('execution_count')}):"
    )
    lines_out.append("")

    for out in outputs:
        out_type = out.get("output_type", "")
        if out_type == "stream":
            text = "".join(out.get("text", []))
            lines = text.splitlines()
            if max_lines and len(lines) > max_lines:
                lines_out.extend(lines[:max_lines])
                lines_out.append(
                    f"... ({len(lines) - max_lines} more lines,"
                    f" use max_lines=0 to see all)"
                )
            else:
                lines_out.extend(lines)
        elif out_type in ("execute_result", "display_data"):
            data = out.get("data", {})
            if "text/plain" in data:
                lines_out.append(f"[{out_type}] {''.join(data['text/plain'])}")
            else:
                lines_out.append(f"[{out_type}] (mime types: {list(data.keys())})")
        elif out_type == "error":
            lines_out.append(f"[error] {out.get('ename')}: {out.get('evalue')}")
        else:
            lines_out.append(f"[{out_type}]")

    return "\n".join(lines_out)


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    nb_path = sys.argv[1]
    cell_number = int(sys.argv[2])
    max_lines = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    try:
        result = read_cell_output(nb_path, cell_number, max_lines)
        print(result)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
