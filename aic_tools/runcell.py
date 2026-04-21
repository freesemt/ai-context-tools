"""
aic_tools.runcell — Execute a notebook cell (or cells 1..N) and print outputs.

The companion to ``aic_tools.notebook`` (which reads stale outputs from disk).
``runcell`` actually runs cells via nbclient and prints fresh outputs to the
terminal with no size limit — closing the verification loop for AI agents.

Usage (CLI):
    python -m aic_tools.runcell <notebook.ipynb> <cell_number>
                                [--kernel NAME] [--timeout SEC]
                                [--write] [--max-lines N]

Usage (API):
    from aic_tools.runcell import run_up_to_cell
    output = run_up_to_cell("path/to/notebook.ipynb", 5)

Arguments:
    notebook      Path to the .ipynb file.
    cell_number   1-based cell number (target cell). Cells 1..cell_number are
                  all executed in order to bring the kernel state up to date.
    --kernel      Override the notebook's recorded kernelspec name
                  (e.g. "python3").
    --timeout     Per-cell execution timeout in seconds (default: 120).
    --write       Save executed outputs back to the .ipynb (papermill-like).
                  Default: read-only execution, the .ipynb is not modified.
    --max-lines   Truncate the printed output of the target cell to N lines
                  (default: 100, 0 = unlimited).

Exit codes:
    0  Target cell executed successfully.
    1  A cell raised an error, file not found, or arguments invalid.

Routing rule for AI assistants:
    Use this tool when you need *fresh* output (e.g. after editing code that
    the cell depends on). Use ``aic_tools.notebook`` when reading the cell's
    last-saved output is sufficient.
"""

from __future__ import annotations

import sys
from pathlib import Path


def run_up_to_cell(
    nb_path,
    cell_number: int,
    kernel_name: str | None = None,
    timeout: int = 120,
    write: bool = False,
):
    """Execute cells 1..cell_number of a notebook and return the target cell.

    Args:
        nb_path:     Path to the .ipynb file (str or Path).
        cell_number: 1-based cell number of the target cell. All preceding
                     cells are also executed (to build kernel state).
        kernel_name: Kernel spec name; if None, use the notebook's recorded
                     kernelspec.
        timeout:     Per-cell execution timeout in seconds.
        write:       If True, save executed outputs back to the .ipynb.

    Returns:
        The executed target cell (a nbformat NotebookNode dict).

    Raises:
        FileNotFoundError:  notebook file missing.
        ValueError:         cell_number out of range or target is not a code cell.
        nbclient.exceptions.CellExecutionError: a cell raised an exception.
    """
    import nbformat
    from nbclient import NotebookClient

    path = Path(nb_path)
    if not path.exists():
        raise FileNotFoundError(f"Notebook not found: {nb_path}")

    nb = nbformat.read(path, as_version=4)
    cells = nb.cells

    if cell_number < 1 or cell_number > len(cells):
        raise ValueError(
            f"cell_number {cell_number} out of range (1..{len(cells)})"
        )

    # Truncate to cells 1..cell_number so nbclient doesn't run the rest.
    nb_truncated = nbformat.from_dict({**nb, "cells": cells[:cell_number]})

    client_kwargs = {"timeout": timeout, "allow_errors": False}
    if kernel_name:
        client_kwargs["kernel_name"] = kernel_name

    client = NotebookClient(nb_truncated, **client_kwargs)
    client.execute(cwd=str(path.parent))

    if write:
        # Merge executed cells back into the original notebook (preserving
        # any cells beyond cell_number) and save.
        nb.cells[:cell_number] = nb_truncated.cells
        nbformat.write(nb, path)

    return nb_truncated.cells[cell_number - 1]


def _format_executed_cell(cell, cell_number: int, max_lines: int) -> str:
    """Format the freshly executed cell's outputs (mirrors notebook.py style)."""
    lines: list[str] = []
    lines.append(
        f"Cell {cell_number} (execution_count={cell.get('execution_count')}):"
    )
    lines.append("")

    for out in cell.get("outputs", []):
        out_type = out.get("output_type", "")
        if out_type == "stream":
            stream_name = out.get("name", "stdout")
            text = "".join(out.get("text", []))
            text_lines = text.splitlines()
            if stream_name != "stdout":
                lines.append(f"[{stream_name}]")
            if max_lines and len(text_lines) > max_lines:
                lines.extend(text_lines[:max_lines])
                lines.append(
                    f"... ({len(text_lines) - max_lines} more lines,"
                    f" use --max-lines 0 for all)"
                )
            else:
                lines.extend(text_lines)
        elif out_type in ("execute_result", "display_data"):
            data = out.get("data", {})
            if "text/plain" in data:
                lines.append(f"[{out_type}] {''.join(data['text/plain'])}")
            else:
                lines.append(
                    f"[{out_type}] (mime types: {list(data.keys())})"
                )
        elif out_type == "error":
            ename = out.get("ename", "")
            evalue = out.get("evalue", "")
            lines.append(f"[error] {ename}: {evalue}")
        else:
            lines.append(f"[{out_type}]")

    return "\n".join(lines)


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2 or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if args and args[0] in ("-h", "--help") else 1)

    nb_path = args[0]
    try:
        cell_number = int(args[1])
    except ValueError:
        print(f"Error: cell_number must be an integer, got {args[1]!r}",
              file=sys.stderr)
        sys.exit(1)

    kernel_name: str | None = None
    timeout = 120
    write = False
    max_lines = 100

    i = 2
    while i < len(args):
        a = args[i]
        if a == "--kernel" and i + 1 < len(args):
            kernel_name = args[i + 1]
            i += 2
        elif a == "--timeout" and i + 1 < len(args):
            timeout = int(args[i + 1])
            i += 2
        elif a == "--max-lines" and i + 1 < len(args):
            max_lines = int(args[i + 1])
            i += 2
        elif a == "--write":
            write = True
            i += 1
        else:
            print(f"Error: unknown argument {a!r}", file=sys.stderr)
            sys.exit(1)

    try:
        cell = run_up_to_cell(
            nb_path,
            cell_number,
            kernel_name=kernel_name,
            timeout=timeout,
            write=write,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except ImportError as exc:
        print(
            f"Error: {exc}. Install execution deps: pip install nbclient nbformat ipykernel",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:  # nbclient.CellExecutionError and friends
        print(f"Error during cell execution: {exc}", file=sys.stderr)
        sys.exit(1)

    print(_format_executed_cell(cell, cell_number, max_lines))


if __name__ == "__main__":
    main()
