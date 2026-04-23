"""
aic_tools.widget_snapshot — Surface ipywidget-rendered figures via sidecar PNGs.

Problem: Notebook cells that render figures into ipywidgets.Output contexts
(e.g. molass MplMonitor) save only widget-view metadata in cell.outputs, not
the rendered pixels. AI assistants reading the .ipynb JSON see "Figure
1400x500" placeholders but no images.

Solution: Many such tools, when given an opt-in env var, write a sidecar PNG
to disk (e.g. molass-legacy MplMonitor writes <work_folder>/figs/mplmonitor_latest.png
when MOLASS_MONITOR_SNAPSHOT=1, see molass-legacy issue #19). This module
parses the cell's stdout for paths to those sidecar PNGs and reports which
ones exist on disk.

Usage (CLI):
    python -m aic_tools.widget_snapshot <notebook.ipynb> <cell_number>

Usage (API):
    from aic_tools.widget_snapshot import find_widget_snapshots
    paths = find_widget_snapshots("path/to/nb.ipynb", 7)
    # -> [PosixPath('.../figs/mplmonitor_latest.png'), ...]

Routing rule for AI assistants:
    When a cell's outputs contain only "Figure NxM" display_data placeholders
    (no image/png mime type) but you need to see what the user saw, call this
    tool. It surfaces snapshots written by upstream cooperating tools.
"""

import json
import re
import sys
from pathlib import Path

# Match plausible PNG paths in stdout. Accepts both Windows and POSIX
# separators. Anchored on a non-path char (or start) to avoid clipping.
_PNG_PATH_RE = re.compile(
    r"""(?<![A-Za-z0-9._/\\-])     # left boundary
        (                           # capture path
            (?:[A-Za-z]:[\\/])?     # optional drive letter
            [^\s'"<>|()\[\]]+?      # path body (no whitespace or shell delims)
            \.png                   # extension
        )
        (?![A-Za-z0-9._-])          # right boundary
    """,
    re.VERBOSE,
)

# Match "work folder" announcements such as molass legacy's
#   "updating information from <path>\callback.txt"
# We then probe sibling locations for sidecar snapshots.
_WORK_FOLDER_HINTS = (
    re.compile(r"updating information from\s+(?P<path>\S+?)[\\/]callback\.txt"),
    re.compile(r"work[_ ]folder\s*[=:]\s*(?P<path>\S+)"),
    re.compile(r"analysis_folder\s*[=:]\s*(?P<path>\S+)"),
)

# Known sidecar-snapshot relative paths produced by cooperating tools.
_SIDECAR_RELATIVE_PATHS = (
    Path("figs") / "mplmonitor_latest.png",
    Path("optimized") / "figs" / "mplmonitor_latest.png",
)


def _iter_cell_stdout(nb_path, cell_number: int):
    """Yield each stdout text chunk from the given 1-based cell."""
    path = Path(nb_path)
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)
    cells = nb.get("cells", [])
    if not (1 <= cell_number <= len(cells)):
        raise IndexError(
            f"cell_number {cell_number} out of range 1..{len(cells)}"
        )
    cell = cells[cell_number - 1]
    if cell.get("cell_type") != "code":
        return
    for out in cell.get("outputs", []):
        if out.get("output_type") == "stream" and out.get("name") == "stdout":
            text = out.get("text", "")
            if isinstance(text, list):
                text = "".join(text)
            yield text


def _explicit_png_paths(text: str):
    """Return PNG paths literally mentioned in `text`."""
    return [Path(m.group(1)) for m in _PNG_PATH_RE.finditer(text)]


def _probe_work_folders(text: str):
    """Return existing sidecar snapshots derived from work-folder mentions."""
    found: list[Path] = []
    for pattern in _WORK_FOLDER_HINTS:
        for m in pattern.finditer(text):
            base = Path(m.group("path"))
            for rel in _SIDECAR_RELATIVE_PATHS:
                candidate = base / rel
                if candidate.is_file():
                    found.append(candidate)
    return found


def find_widget_snapshots(nb_path, cell_number: int):
    """Return a deduplicated list of existing PNG snapshot paths for a cell.

    Combines:
      1. PNG paths literally printed in the cell's stdout.
      2. Sidecar snapshots under any work-folder mentioned in the stdout.

    Only paths that exist on disk are returned.
    """
    seen: set[str] = set()
    found: list[Path] = []
    for text in _iter_cell_stdout(nb_path, cell_number):
        for p in _explicit_png_paths(text):
            if p.is_file():
                key = str(p.resolve())
                if key not in seen:
                    seen.add(key)
                    found.append(p)
        for p in _probe_work_folders(text):
            key = str(p.resolve())
            if key not in seen:
                seen.add(key)
                found.append(p)
    return found


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print(
            "Usage: python -m aic_tools.widget_snapshot <notebook.ipynb> <cell_number>",
            file=sys.stderr,
        )
        return 2
    nb_path = argv[0]
    try:
        cell_number = int(argv[1])
    except ValueError:
        print(f"cell_number must be an integer, got: {argv[1]!r}", file=sys.stderr)
        return 2
    paths = find_widget_snapshots(nb_path, cell_number)
    if not paths:
        print(f"No widget snapshots found for cell {cell_number}.")
        return 1
    for p in paths:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
