"""tests for aic_tools.notebook"""

import json
import pathlib
import tempfile
import pytest

from aic_tools.notebook import read_cell_output, read_cell_output_by_id, list_cells


def _make_notebook(cells: list[dict]) -> pathlib.Path:
    """Create a minimal .ipynb file in a temp dir and return its path."""
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}},
        "cells": cells,
    }
    p = pathlib.Path(tempfile.mktemp(suffix=".ipynb"))
    p.write_text(json.dumps(nb), encoding="utf-8")
    return p


def _code_cell(source: str, outputs: list[dict], cell_id: str = "test-id") -> dict:
    return {
        "cell_type": "code",
        "source": source,
        "metadata": {},
        "outputs": outputs,
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


def _stdout_output(text: str) -> dict:
    return {"output_type": "stream", "name": "stdout", "text": text}


def _stderr_output(text: str) -> dict:
    return {"output_type": "stream", "name": "stderr", "text": text}


def _error_output(ename: str, evalue: str, traceback: list[str]) -> dict:
    return {
        "output_type": "error",
        "ename": ename,
        "evalue": evalue,
        "traceback": traceback,
    }


def _display_data(data: dict) -> dict:
    return {"output_type": "display_data", "data": data, "metadata": {}}


# ---------------------------------------------------------------------------
# Basic happy-path tests
# ---------------------------------------------------------------------------

def test_read_single_line():
    nb = _make_notebook([_code_cell("print('hello')", [_stdout_output("hello\n")])])
    result = read_cell_output(nb, 1)
    assert "hello" in result


def test_read_multiline():
    text = "line1\nline2\nline3\n"
    nb = _make_notebook([_code_cell("...", [_stdout_output(text)])])
    result = read_cell_output(nb, 1)
    assert "line1" in result
    assert "line2" in result
    assert "line3" in result


def test_max_lines_truncates():
    text = "\n".join(f"line{i}" for i in range(20)) + "\n"
    nb = _make_notebook([_code_cell("...", [_stdout_output(text)])])
    result = read_cell_output(nb, 1, max_lines=5)
    lines = [l for l in result.splitlines() if l.startswith("line")]
    assert len(lines) == 5


def test_max_lines_zero_means_all():
    text = "\n".join(f"line{i}" for i in range(100)) + "\n"
    nb = _make_notebook([_code_cell("...", [_stdout_output(text)])])
    result = read_cell_output(nb, 1, max_lines=0)
    lines = [l for l in result.splitlines() if l.startswith("line")]
    assert len(lines) == 100


def test_second_cell():
    cells = [
        _code_cell("first", [_stdout_output("first output\n")]),
        _code_cell("second", [_stdout_output("second output\n")]),
    ]
    nb = _make_notebook(cells)
    assert "second output" in read_cell_output(nb, 2)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_no_stdout_returns_message():
    # Cell with no outputs at all
    nb = _make_notebook([_code_cell("x = 1", [])])
    result = read_cell_output(nb, 1)
    assert "(no output)" in result or result.strip() == ""


def test_cell_out_of_range():
    nb = _make_notebook([_code_cell("x=1", [])])
    with pytest.raises((IndexError, ValueError)):
        read_cell_output(nb, 99)


def test_accepts_string_path():
    nb = _make_notebook([_code_cell("...", [_stdout_output("ok\n")])])
    result = read_cell_output(str(nb), 1)
    assert "ok" in result


# ---------------------------------------------------------------------------
# Issue D: stderr and error traceback support
# ---------------------------------------------------------------------------

def test_stderr_shown_with_label():
    nb = _make_notebook([_code_cell("...", [_stderr_output("warning msg\n")])])
    result = read_cell_output(nb, 1)
    assert "[stderr]" in result
    assert "warning msg" in result


def test_error_basic():
    nb = _make_notebook([_code_cell("...", [
        _error_output("ValueError", "bad value", ["tb line 1", "tb line 2"])
    ])])
    result = read_cell_output(nb, 1)
    assert "ValueError" in result
    assert "bad value" in result
    # Without full=True, traceback is NOT shown
    assert "tb line 1" not in result


def test_error_full_traceback():
    nb = _make_notebook([_code_cell("...", [
        _error_output("TypeError", "oops", ["frame 1", "frame 2", "frame 3"])
    ])])
    result = read_cell_output(nb, 1, full=True)
    assert "TypeError" in result
    assert "frame 1" in result
    assert "frame 3" in result


def test_mixed_stdout_stderr():
    nb = _make_notebook([_code_cell("...", [
        _stdout_output("out1\n"),
        _stderr_output("err1\n"),
        _stdout_output("out2\n"),
    ])])
    result = read_cell_output(nb, 1)
    assert "out1" in result
    assert "err1" in result
    assert "out2" in result


# ---------------------------------------------------------------------------
# Issue E: cell-ID lookup and list_cells
# ---------------------------------------------------------------------------

def test_list_cells():
    cells = [
        _markdown_cell("# Title", cell_id="md-001"),
        _code_cell("print('hi')", [_stdout_output("hi\n")], cell_id="code-001"),
        _code_cell("x = 1", [], cell_id="code-002"),
    ]
    nb = _make_notebook(cells)
    result = list_cells(nb)
    assert "md-001" in result
    assert "code-001" in result
    assert "code-002" in result
    assert "markdown" in result
    assert "code" in result


def test_read_by_id():
    cells = [
        _code_cell("first", [_stdout_output("aaa\n")], cell_id="cell-aaa"),
        _code_cell("second", [_stdout_output("bbb\n")], cell_id="cell-bbb"),
    ]
    nb = _make_notebook(cells)
    result = read_cell_output_by_id(nb, "cell-bbb")
    assert "bbb" in result
    assert "aaa" not in result


def test_read_by_id_with_hash_prefix():
    cells = [
        _code_cell("x", [_stdout_output("found\n")], cell_id="VSC-abc123"),
    ]
    nb = _make_notebook(cells)
    # Should work with or without '#' prefix
    result = read_cell_output_by_id(nb, "#VSC-abc123")
    assert "found" in result


def test_read_by_id_not_found():
    nb = _make_notebook([_code_cell("x", [], cell_id="real-id")])
    with pytest.raises(KeyError):
        read_cell_output_by_id(nb, "nonexistent-id")


# ---------------------------------------------------------------------------
# Issue F: --full flag for all output types
# ---------------------------------------------------------------------------

def test_full_display_data():
    nb = _make_notebook([_code_cell("...", [
        _display_data({
            "text/plain": ["<Figure>"],
            "image/png": ["iVBOR...base64..."],
        })
    ])])
    # Without full: only text/plain
    result = read_cell_output(nb, 1)
    assert "<Figure>" in result
    assert "iVBOR" not in result

    # With full: all mime types
    result_full = read_cell_output(nb, 1, full=True)
    assert "text/plain" in result_full
    assert "image/png" in result_full
    assert "iVBOR" in result_full


def test_full_execute_result():
    nb = _make_notebook([_code_cell("...", [{
        "output_type": "execute_result",
        "data": {"text/plain": ["42"], "text/html": ["<b>42</b>"]},
        "metadata": {},
        "execution_count": 1,
    }])])
    result_full = read_cell_output(nb, 1, full=True)
    assert "text/html" in result_full
    assert "<b>42</b>" in result_full
