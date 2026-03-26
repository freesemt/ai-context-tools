"""
aic_tools.notebook — Read notebook cell outputs from .ipynb JSON.

Bypasses the built-in read_notebook_cell_output tool size limit by reading
the .ipynb JSON directly from disk.

Usage (CLI):
    python -m aic_tools.notebook <notebook.ipynb> <cell_number> [max_lines]
    python -m aic_tools.notebook <notebook.ipynb> --list
    python -m aic_tools.notebook <notebook.ipynb> --by-id <cell_id> [max_lines]
    python -m aic_tools.notebook <notebook.ipynb> <cell_number> --full

Usage (API):
    from aic_tools.notebook import read_cell_output, list_cells
    read_cell_output("path/to/notebook.ipynb", 14)
    read_cell_output("path/to/notebook.ipynb", 14, full=True)
    read_cell_output_by_id("path/to/notebook.ipynb", "VSC-abc123")
    list_cells("path/to/notebook.ipynb")

Arguments:
    notebook     Path to the .ipynb file
    cell_number  1-based cell number (matches VS Code display)
    max_lines    Max lines to print (default: 100, 0 = all)
    --list       List all cells with number, ID, type, and first line
    --by-id      Look up a cell by its VS Code cell ID
    --full       Show all output types including stderr, tracebacks,
                 and all mime types (not just text/plain)

Routing rule for AI assistants:
    After copilot_getNotebookSummary, check each cell's mime types.
    If a cell has application/vnd.code.notebook.stdout, call this tool
    instead of read_notebook_cell_output — the built-in tool will fail
    with "output too large" for stdout-heavy cells.
"""

import json
import sys
from pathlib import Path


def _load_notebook(nb_path):
    """Load and return (path, notebook_dict)."""
    path = Path(nb_path)
    if not path.exists():
        raise FileNotFoundError(f"Notebook not found: {nb_path}")
    with open(path, encoding="utf-8") as f:
        return path, json.load(f)


def _format_cell_outputs(cell, cell_number: int, max_lines: int, full: bool) -> str:
    """Format the outputs of a single code cell."""
    if cell["cell_type"] != "code":
        return f"Cell {cell_number} is a markdown cell — no output."

    outputs = cell.get("outputs", [])
    if not outputs:
        return "(no output)"

    lines_out: list[str] = []
    lines_out.append(
        f"Cell {cell_number} (execution_count={cell.get('execution_count')}):"
    )
    lines_out.append("")

    for out in outputs:
        out_type = out.get("output_type", "")
        if out_type == "stream":
            stream_name = out.get("name", "stdout")
            text = "".join(out.get("text", []))
            lines = text.splitlines()
            if stream_name != "stdout":
                lines_out.append(f"[{stream_name}]")
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
            if full:
                for mime, content in data.items():
                    text = "".join(content) if isinstance(content, list) else str(content)
                    lines_out.append(f"[{out_type} {mime}]")
                    lines_out.append(text)
            elif "text/plain" in data:
                lines_out.append(f"[{out_type}] {''.join(data['text/plain'])}")
            else:
                lines_out.append(f"[{out_type}] (mime types: {list(data.keys())})")
        elif out_type == "error":
            ename = out.get("ename", "")
            evalue = out.get("evalue", "")
            lines_out.append(f"[error] {ename}: {evalue}")
            if full:
                traceback = out.get("traceback", [])
                for tb_line in traceback:
                    # Traceback lines may contain ANSI escape codes
                    lines_out.append(tb_line)
        else:
            lines_out.append(f"[{out_type}]")

    return "\n".join(lines_out)


def read_cell_output(nb_path, cell_number: int, max_lines: int = 100,
                     full: bool = False) -> str:
    """Return the output of a notebook cell as a string.

    Args:
        nb_path:     Path to the .ipynb file (str or Path).
        cell_number: 1-based cell index (all cells, matching VS Code display).
        max_lines:   Maximum lines to return. 0 = unlimited.
        full:        If True, include stderr, full tracebacks, and all mime types.

    Raises:
        FileNotFoundError: if the notebook file does not exist.
        ValueError:        if cell_number is out of range.
    """
    _, nb = _load_notebook(nb_path)
    cells = nb["cells"]
    if cell_number < 1 or cell_number > len(cells):
        raise ValueError(
            f"cell_number {cell_number} out of range (1–{len(cells)})"
        )
    return _format_cell_outputs(cells[cell_number - 1], cell_number, max_lines, full)


def read_cell_output_by_id(nb_path, cell_id: str, max_lines: int = 100,
                           full: bool = False) -> str:
    """Return the output of a notebook cell looked up by its cell ID.

    Args:
        nb_path:  Path to the .ipynb file (str or Path).
        cell_id:  The cell ID (e.g. "VSC-abc123"). Prefix '#' is stripped.
        max_lines: Maximum lines to return. 0 = unlimited.
        full:     If True, include stderr, full tracebacks, and all mime types.

    Raises:
        FileNotFoundError: if the notebook file does not exist.
        KeyError:          if no cell with the given ID is found.
    """
    _, nb = _load_notebook(nb_path)
    cell_id = cell_id.lstrip("#")
    for i, cell in enumerate(nb["cells"]):
        cid = cell.get("id", "")
        if cid == cell_id or cid.lstrip("#") == cell_id:
            return _format_cell_outputs(cell, i + 1, max_lines, full)
    raise KeyError(f"No cell with id '{cell_id}' found")


def list_cells(nb_path) -> str:
    """List all cells in a notebook with number, ID, type, and first source line.

    Args:
        nb_path: Path to the .ipynb file (str or Path).

    Returns:
        A formatted table string.
    """
    _, nb = _load_notebook(nb_path)
    lines: list[str] = []
    lines.append(f"{'#':>3}  {'ID':<20}  {'Type':<8}  First line")
    lines.append("-" * 70)
    for i, cell in enumerate(nb["cells"]):
        cid = cell.get("id", "")
        ctype = cell["cell_type"]
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        first_line = source.split("\n", 1)[0][:50]
        lines.append(f"{i+1:>3}  {cid:<20}  {ctype:<8}  {first_line}")
    return "\n".join(lines)


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    nb_path = args[0]

    # --list mode
    if "--list" in args:
        try:
            print(list_cells(nb_path))
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        return

    # --by-id mode
    if "--by-id" in args:
        idx = args.index("--by-id")
        if idx + 1 >= len(args):
            print("Error: --by-id requires a cell ID argument", file=sys.stderr)
            sys.exit(1)
        cell_id = args[idx + 1]
        remaining = [a for i, a in enumerate(args) if i not in (0, idx, idx + 1) and a != "--full"]
        max_lines = int(remaining[0]) if remaining else 100
        full = "--full" in args
        try:
            print(read_cell_output_by_id(nb_path, cell_id, max_lines, full))
        except (FileNotFoundError, KeyError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        return

    # Default: cell_number mode
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)

    cell_number = int(args[1])
    remaining = [a for i, a in enumerate(args) if i > 1 and a != "--full"]
    max_lines = int(remaining[0]) if remaining else 100
    full = "--full" in args
    try:
        result = read_cell_output(nb_path, cell_number, max_lines, full)
        print(result)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
