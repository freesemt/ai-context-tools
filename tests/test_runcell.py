"""Tests for aic_tools.runcell."""

import json
import pathlib
import tempfile
import pytest

# Skip the entire module if execution deps aren't installed.
nbclient = pytest.importorskip("nbclient")
nbformat = pytest.importorskip("nbformat")
pytest.importorskip("ipykernel")

from aic_tools.runcell import run_up_to_cell


def _make_notebook(cells: list[dict]) -> pathlib.Path:
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
            "language_info": {"name": "python"},
        },
        "cells": cells,
    }
    p = pathlib.Path(tempfile.mktemp(suffix=".ipynb"))
    p.write_text(json.dumps(nb), encoding="utf-8")
    return p


def _code_cell(source: str, cell_id: str = "test-id") -> dict:
    return {
        "cell_type": "code",
        "source": source,
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "id": cell_id,
    }


def _markdown_cell(source: str, cell_id: str = "md-id") -> dict:
    return {
        "cell_type": "markdown",
        "source": source,
        "metadata": {},
        "id": cell_id,
    }


def _outputs_text(cell) -> str:
    chunks = []
    for out in cell.get("outputs", []):
        if out.get("output_type") == "stream":
            chunks.append("".join(out.get("text", [])))
        elif out.get("output_type") in ("execute_result", "display_data"):
            data = out.get("data", {})
            if "text/plain" in data:
                chunks.append("".join(data["text/plain"]))
    return "".join(chunks)


def test_runs_single_cell_and_captures_stdout():
    nb = _make_notebook([_code_cell("print('hello world')")])
    cell = run_up_to_cell(nb, 1)
    assert "hello world" in _outputs_text(cell)


def test_state_persists_across_preceding_cells():
    cells = [
        _code_cell("x = 41", cell_id="c1"),
        _code_cell("print(x + 1)", cell_id="c2"),
    ]
    nb = _make_notebook(cells)
    cell = run_up_to_cell(nb, 2)
    assert "42" in _outputs_text(cell)


def test_does_not_write_outputs_by_default():
    nb = _make_notebook([_code_cell("print('side effect')")])
    before = nb.read_text(encoding="utf-8")
    run_up_to_cell(nb, 1)
    after = nb.read_text(encoding="utf-8")
    assert before == after


def test_write_persists_outputs():
    nb = _make_notebook([_code_cell("print('persisted')")])
    run_up_to_cell(nb, 1, write=True)
    saved = nbformat.read(nb, as_version=4)
    cell = saved.cells[0]
    assert "persisted" in _outputs_text(cell)


def test_skips_markdown_cells_in_path():
    cells = [
        _markdown_cell("# heading", cell_id="md1"),
        _code_cell("x = 7", cell_id="c1"),
        _code_cell("print(x * 6)", cell_id="c2"),
    ]
    nb = _make_notebook(cells)
    cell = run_up_to_cell(nb, 3)
    assert "42" in _outputs_text(cell)


def test_cell_number_out_of_range():
    nb = _make_notebook([_code_cell("x=1")])
    with pytest.raises(ValueError):
        run_up_to_cell(nb, 99)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        run_up_to_cell("/no/such/notebook.ipynb", 1)


def test_cell_error_propagates():
    nb = _make_notebook([_code_cell("raise RuntimeError('boom')")])
    with pytest.raises(Exception) as exc_info:
        run_up_to_cell(nb, 1)
    # nbclient raises CellExecutionError; check the message carries through.
    assert "boom" in str(exc_info.value) or "RuntimeError" in str(exc_info.value)
