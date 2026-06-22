"""tests for aic_tools.edit_lines"""

import pathlib
import tempfile
import pytest

from aic_tools.edit_lines import edit_lines, delete_lines


def _make_test_file(content: str) -> pathlib.Path:
    """Create a test file in a temp dir and return its path."""
    p = pathlib.Path(tempfile.mktemp(suffix=".txt"))
    p.write_text(content, encoding="utf-8")
    return p


def test_edit_lines_basic():
    """Test basic line replacement."""
    content = "line 1\nline 2\nline 3\nline 4\nline 5\n"
    p = _make_test_file(content)
    
    try:
        result = edit_lines(str(p), 2, 4, "replaced\n", backup=False)
        
        assert result['lines_before'] == 5
        assert result['lines_after'] == 3
        assert result['replaced_count'] == 3
        assert result['backup_path'] is None
        
        new_content = p.read_text()
        assert new_content == "line 1\nreplaced\nline 5\n"
    finally:
        p.unlink(missing_ok=True)


def test_edit_lines_with_backup():
    """Test that backup is created."""
    content = "line 1\nline 2\nline 3\n"
    p = _make_test_file(content)
    
    try:
        result = edit_lines(str(p), 2, 2, "new line 2\n", backup=True)
        
        backup_path = pathlib.Path(result['backup_path'])
        assert backup_path.exists()
        assert backup_path.read_text() == content
        
        new_content = p.read_text()
        assert new_content == "line 1\nnew line 2\nline 3\n"
    finally:
        p.unlink(missing_ok=True)
        if result['backup_path']:
            pathlib.Path(result['backup_path']).unlink(missing_ok=True)


def test_edit_lines_multiline_replacement():
    """Test replacing with multiple lines."""
    content = "line 1\nline 2\nline 3\nline 4\n"
    p = _make_test_file(content)
    
    try:
        new_content = "replacement 1\nreplacement 2\nreplacement 3\n"
        result = edit_lines(str(p), 2, 3, new_content, backup=False)
        
        assert result['replaced_count'] == 2
        
        final = p.read_text()
        assert final == "line 1\nreplacement 1\nreplacement 2\nreplacement 3\nline 4\n"
    finally:
        p.unlink(missing_ok=True)


def test_edit_lines_single_line():
    """Test replacing a single line."""
    content = "line 1\nline 2\nline 3\n"
    p = _make_test_file(content)
    
    try:
        result = edit_lines(str(p), 2, 2, "MODIFIED\n", backup=False)
        
        assert result['replaced_count'] == 1
        
        final = p.read_text()
        assert final == "line 1\nMODIFIED\nline 3\n"
    finally:
        p.unlink(missing_ok=True)


def test_edit_lines_beginning():
    """Test replacing from the beginning."""
    content = "line 1\nline 2\nline 3\n"
    p = _make_test_file(content)
    
    try:
        result = edit_lines(str(p), 1, 1, "NEW START\n", backup=False)
        
        final = p.read_text()
        assert final == "NEW START\nline 2\nline 3\n"
    finally:
        p.unlink(missing_ok=True)


def test_edit_lines_end():
    """Test replacing to the end."""
    content = "line 1\nline 2\nline 3\n"
    p = _make_test_file(content)
    
    try:
        result = edit_lines(str(p), 2, 3, "NEW END\n", backup=False)
        
        final = p.read_text()
        assert final == "line 1\nNEW END\n"
    finally:
        p.unlink(missing_ok=True)


def test_delete_lines():
    """Test deleting a range of lines."""
    content = "line 1\nline 2\nline 3\nline 4\nline 5\n"
    p = _make_test_file(content)
    
    try:
        result = delete_lines(str(p), 2, 4, backup=False)
        
        assert result['replaced_count'] == 3
        
        final = p.read_text()
        assert final == "line 1\nline 5\n"
    finally:
        p.unlink(missing_ok=True)


def test_edit_lines_content_file():
    """Test reading replacement content from a file."""
    original = "line 1\nline 2\nline 3\n"
    replacement = "new content\n"
    
    p_original = _make_test_file(original)
    p_replacement = _make_test_file(replacement)
    
    try:
        result = edit_lines(str(p_original), 2, 2, content_file=str(p_replacement), backup=False)
        
        final = p_original.read_text()
        assert final == "line 1\nnew content\nline 3\n"
    finally:
        p_original.unlink(missing_ok=True)
        p_replacement.unlink(missing_ok=True)


def test_edit_lines_invalid_range():
    """Test that invalid line ranges raise ValueError."""
    content = "line 1\nline 2\nline 3\n"
    p = _make_test_file(content)
    
    try:
        # Start line < 1
        with pytest.raises(ValueError, match="Invalid line range"):
            edit_lines(str(p), 0, 2, "new\n", backup=False)
        
        # End line > file length
        with pytest.raises(ValueError, match="Invalid line range"):
            edit_lines(str(p), 1, 10, "new\n", backup=False)
        
        # Start > end
        with pytest.raises(ValueError, match="Invalid line range"):
            edit_lines(str(p), 3, 2, "new\n", backup=False)
    finally:
        p.unlink(missing_ok=True)


def test_edit_lines_no_content():
    """Test that missing content raises ValueError."""
    content = "line 1\nline 2\n"
    p = _make_test_file(content)
    
    try:
        with pytest.raises(ValueError, match="Must provide either new_content or content_file"):
            edit_lines(str(p), 1, 1, backup=False)
    finally:
        p.unlink(missing_ok=True)


def test_edit_lines_duplicate_content_safe():
    """
    Test the main use case: HTML file with duplicate sections.
    
    This is the problem that motivated this tool — replace_string_in_file
    fails with "Multiple matches found" when there are duplicate sections.
    edit_lines solves this by using line numbers instead of string matching.
    """
    # Simulate HTML with duplicate sections
    content = """<h3 id="section-a">Section A</h3>
<p>Content A</p>

<h3 id="section-b">Section B</h3>
<p>Content B</p>

<h3 id="section-a">Section A (duplicate)</h3>
<p>Content A (duplicate)</p>
"""
    
    p = _make_test_file(content)
    
    try:
        # Replace ONLY the first Section A (lines 1-2) — unambiguous with line numbers
        result = edit_lines(
            str(p),
            1,
            2,
            '<h3 id="section-a">Section A (UPDATED)</h3>\n<p>Updated content</p>\n',
            backup=False
        )
        
        final = p.read_text()
        
        # First section updated
        assert '<h3 id="section-a">Section A (UPDATED)</h3>' in final
        assert '<p>Updated content</p>' in final
        
        # Second section unchanged
        assert '<h3 id="section-a">Section A (duplicate)</h3>' in final
        assert '<p>Content A (duplicate)</p>' in final
        
        # Section B unchanged
        assert '<h3 id="section-b">Section B</h3>' in final
        
    finally:
        p.unlink(missing_ok=True)
