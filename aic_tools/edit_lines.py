"""
aic_tools.edit_lines — Line-range based file editing.

Solves the "duplicate content" problem where replace_string_in_file fails
with "Multiple matches found" errors. This tool uses line numbers instead
of string matching, making edits precise and unambiguous.

Usage (CLI):
    python -m aic_tools.edit_lines <file> <start_line> <end_line> <new_content_file>
    python -m aic_tools.edit_lines <file> <start_line> <end_line> --stdin
    python -m aic_tools.edit_lines <file> <start_line> <end_line> --delete

Usage (API):
    from aic_tools.edit_lines import edit_lines, delete_lines
    
    # Replace lines 10-20 with new content
    edit_lines("index.html", 10, 20, "new content here")
    
    # Delete lines 10-20
    delete_lines("index.html", 10, 20)
    
    # Replace from file
    edit_lines("index.html", 10, 20, content_file="new_content.txt")

Arguments:
    file              Path to file to edit
    start_line        1-based line number (first line to replace)
    end_line          1-based line number (last line to replace, inclusive)
    new_content_file  File containing replacement content
    --stdin           Read replacement content from stdin
    --delete          Delete the specified line range (no replacement)
    --backup          Create .bak backup before editing (default: True)
    --no-backup       Skip backup creation

Safety:
    - Creates .bak backup by default (use --no-backup to skip)
    - Validates line numbers before editing
    - Atomic write (writes to temp file, then renames)

Example use case:
    HTML file with duplicate sections prevents replace_string_in_file from
    working. Use edit_lines to target the exact line range:
    
    python -m aic_tools.edit_lines index.html 124 358 replacement.html

Design rationale:
    This fills a gap in VS Code's editing tools. The built-in tools are:
    - replace_string_in_file: exact string matching (fails on duplicates)
    - edit_notebook_file: notebook cells only
    - No line-based editing tool exists (this is it)
"""

import sys
import shutil
import argparse
from pathlib import Path
from tempfile import NamedTemporaryFile


def edit_lines(
    file_path: str,
    start_line: int,
    end_line: int,
    new_content: str = None,
    content_file: str = None,
    backup: bool = True,
    encoding: str = "utf-8"
) -> dict:
    """
    Replace lines [start_line, end_line] with new_content.
    
    Args:
        file_path: Path to file to edit
        start_line: 1-based line number (first line to replace)
        end_line: 1-based line number (last line to replace, inclusive)
        new_content: Replacement text (if not using content_file)
        content_file: Path to file containing replacement text
        backup: Create .bak backup before editing (default True)
        encoding: File encoding (default utf-8)
    
    Returns:
        dict with keys: backup_path, lines_before, lines_after, replaced_count
    
    Raises:
        FileNotFoundError: If file_path or content_file doesn't exist
        ValueError: If line numbers are invalid
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Load replacement content
    if content_file:
        content_path = Path(content_file)
        if not content_path.exists():
            raise FileNotFoundError(f"Content file not found: {content_file}")
        new_content = content_path.read_text(encoding=encoding)
    
    if new_content is None:
        raise ValueError("Must provide either new_content or content_file")
    
    # Read original file
    lines = path.read_text(encoding=encoding).splitlines(keepends=True)
    
    # Validate line numbers (1-based)
    if start_line < 1 or end_line < start_line or end_line > len(lines):
        raise ValueError(
            f"Invalid line range [{start_line}, {end_line}] for file with {len(lines)} lines"
        )
    
    # Create backup
    backup_path = None
    if backup:
        backup_path = path.with_suffix(path.suffix + '.bak')
        shutil.copy2(path, backup_path)
    
    # Convert 1-based to 0-based indices
    start_idx = start_line - 1
    end_idx = end_line  # end_line is inclusive, so no -1 needed for slice
    
    # Build replacement (ensure it ends with newline if original did)
    replacement_lines = new_content.splitlines(keepends=True)
    if not replacement_lines:
        replacement_lines = []
    elif replacement_lines and not replacement_lines[-1].endswith('\n'):
        # Add newline if missing and there's more content after
        if end_idx < len(lines):
            replacement_lines[-1] += '\n'
    
    # Replace lines
    new_lines = lines[:start_idx] + replacement_lines + lines[end_idx:]
    
    # Atomic write (write to temp, then rename)
    with NamedTemporaryFile(
        mode='w',
        encoding=encoding,
        delete=False,
        dir=path.parent,
        prefix=f'.{path.name}.',
        suffix='.tmp'
    ) as tmp:
        tmp.writelines(new_lines)
        tmp_path = Path(tmp.name)
    
    # Replace original with temp
    tmp_path.replace(path)
    
    return {
        'backup_path': str(backup_path) if backup_path else None,
        'lines_before': len(lines),
        'lines_after': len(new_lines),
        'replaced_count': end_idx - start_idx
    }


def delete_lines(
    file_path: str,
    start_line: int,
    end_line: int,
    backup: bool = True,
    encoding: str = "utf-8"
) -> dict:
    """
    Delete lines [start_line, end_line] from file.
    
    Args:
        file_path: Path to file to edit
        start_line: 1-based line number (first line to delete)
        end_line: 1-based line number (last line to delete, inclusive)
        backup: Create .bak backup before editing (default True)
        encoding: File encoding (default utf-8)
    
    Returns:
        dict with keys: backup_path, lines_before, lines_after, deleted_count
    """
    return edit_lines(file_path, start_line, end_line, new_content="", backup=backup, encoding=encoding)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Line-range based file editing (replaces duplicate-content-safe)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Replace lines 10-20 with content from file
    python -m aic_tools.edit_lines index.html 10 20 replacement.txt
    
    # Replace lines 10-20 with content from stdin
    echo "new content" | python -m aic_tools.edit_lines index.html 10 20 --stdin
    
    # Delete lines 10-20
    python -m aic_tools.edit_lines index.html 10 20 --delete
    
    # Edit without backup
    python -m aic_tools.edit_lines index.html 10 20 replacement.txt --no-backup
"""
    )
    
    parser.add_argument('file', help='File to edit')
    parser.add_argument('start_line', type=int, help='First line to replace (1-based)')
    parser.add_argument('end_line', type=int, help='Last line to replace (1-based, inclusive)')
    parser.add_argument('content_file', nargs='?', help='File containing replacement content')
    parser.add_argument('--stdin', action='store_true', help='Read replacement content from stdin')
    parser.add_argument('--delete', action='store_true', help='Delete lines (no replacement)')
    parser.add_argument('--no-backup', action='store_true', help='Skip .bak backup creation')
    
    args = parser.parse_args()
    
    # Validate input mode
    if args.delete and (args.content_file or args.stdin):
        parser.error("--delete cannot be used with content_file or --stdin")
    if not args.delete and not args.content_file and not args.stdin:
        parser.error("Must provide content_file, --stdin, or --delete")
    if args.content_file and args.stdin:
        parser.error("Cannot use both content_file and --stdin")
    
    try:
        # Get replacement content
        if args.delete:
            new_content = ""
        elif args.stdin:
            new_content = sys.stdin.read()
        else:
            new_content = Path(args.content_file).read_text(encoding='utf-8')
        
        # Perform edit
        result = edit_lines(
            args.file,
            args.start_line,
            args.end_line,
            new_content=new_content,
            backup=not args.no_backup
        )
        
        # Report result
        print(f"Edited {args.file}")
        if result['backup_path']:
            print(f"Backup: {result['backup_path']}")
        print(f"Lines: {result['lines_before']} → {result['lines_after']}")
        print(f"Replaced: lines {args.start_line}-{args.end_line} ({result['replaced_count']} lines)")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
