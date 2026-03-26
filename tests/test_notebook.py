"""tests for aic_tools.notebook"""

import json
import pathlib
import tempfile
import pytest

from aic_tools.notebook import read_cell_output


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


def _code_cell(source: str, outputs: list[dict]) -> dict:
    return {
        "cell_type": "code",
        "source": source,
        "metadata": {},
        "outputs": outputs,
        "execution_count": None,
        "id": "test-id",
    }


def _stdout_output(text: str) -> dict:
    return {"output_type": "stream", "name": "stdout", "text": text}


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
    assert "(no stdout output)" in result or result.strip() == ""


def test_cell_out_of_range():
    nb = _make_notebook([_code_cell("x=1", [])])
    with pytest.raises((IndexError, ValueError)):
        read_cell_output(nb, 99)


def test_accepts_string_path():
    nb = _make_notebook([_code_cell("...", [_stdout_output("ok\n")])])
    result = read_cell_output(str(nb), 1)
    assert "ok" in result
