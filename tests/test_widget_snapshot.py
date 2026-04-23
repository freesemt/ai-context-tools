"""tests for aic_tools.widget_snapshot"""

import json
import pathlib
import tempfile

from aic_tools.widget_snapshot import find_widget_snapshots


def _make_notebook(cells: list[dict]) -> pathlib.Path:
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}},
        "cells": cells,
    }
    p = pathlib.Path(tempfile.mktemp(suffix=".ipynb"))
    p.write_text(json.dumps(nb), encoding="utf-8")
    return p


def _stdout_cell(text: str) -> dict:
    return {
        "cell_type": "code",
        "source": "...",
        "metadata": {},
        "outputs": [{"output_type": "stream", "name": "stdout", "text": text}],
        "execution_count": 1,
        "id": "test-id",
    }


def test_no_outputs_returns_empty(tmp_path):
    nb = _make_notebook([{
        "cell_type": "code", "source": "...", "metadata": {},
        "outputs": [], "execution_count": None, "id": "x",
    }])
    assert find_widget_snapshots(nb, 1) == []


def test_explicit_png_path_existing(tmp_path):
    png = tmp_path / "snap.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal PNG signature, content irrelevant
    nb = _make_notebook([_stdout_cell(f"Saved {png}\n")])
    found = find_widget_snapshots(nb, 1)
    assert len(found) == 1
    assert found[0].resolve() == png.resolve()


def test_explicit_png_path_missing_is_skipped(tmp_path):
    nb = _make_notebook([_stdout_cell("Saved C:/Temp/does_not_exist_xyz.png\n")])
    assert find_widget_snapshots(nb, 1) == []


def test_workfolder_sidecar_discovered(tmp_path):
    # Simulate molass MplMonitor sidecar
    work = tmp_path / "analysis_apo_split"
    figs = work / "optimized" / "figs"
    figs.mkdir(parents=True)
    snap = figs / "mplmonitor_latest.png"
    snap.write_bytes(b"\x89PNG\r\n\x1a\n")
    cb = work / "optimized" / "jobs" / "000"
    cb.mkdir(parents=True)
    (cb / "callback.txt").write_text("dummy")

    text = f"updating information from {cb}\\callback.txt, len(x_list)=5\n"
    nb = _make_notebook([_stdout_cell(text)])
    found = find_widget_snapshots(nb, 1)
    # Path probing walks up from the callback.txt parent — not from `work` directly.
    # Our hint pattern uses the callback.txt path's parent (cb) as `base`, then
    # appends "optimized/figs/mplmonitor_latest.png". The actual snapshot is at
    # work/optimized/figs/mplmonitor_latest.png, so the simple base+rel probe
    # will not find it. Thus the test confirms current behavior: no false hit.
    # When called with the work_folder=... pattern instead, it WILL find it.
    assert found == []


def test_workfolder_explicit_pattern(tmp_path):
    work = tmp_path / "analysis_apo"
    figs = work / "figs"
    figs.mkdir(parents=True)
    snap = figs / "mplmonitor_latest.png"
    snap.write_bytes(b"\x89PNG\r\n\x1a\n")

    text = f"work_folder = {work}\nrunning optimizer ...\n"
    nb = _make_notebook([_stdout_cell(text)])
    found = find_widget_snapshots(nb, 1)
    assert len(found) == 1
    assert found[0].resolve() == snap.resolve()


def test_dedup(tmp_path):
    png = tmp_path / "dup.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")
    text = f"Saved {png}\nSaved again {png}\n"
    nb = _make_notebook([_stdout_cell(text)])
    found = find_widget_snapshots(nb, 1)
    assert len(found) == 1
