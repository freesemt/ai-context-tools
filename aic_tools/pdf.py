"""
aic_tools.pdf — Extract text from PDF files.

Usage (CLI):
    python -m aic_tools.pdf <file.pdf>               # Extract all pages
    python -m aic_tools.pdf <file.pdf> --page 2      # Extract single page
    python -m aic_tools.pdf <file.pdf> --page 2 --max-lines 50

Usage (API):
    from aic_tools.pdf import extract_text
    text = extract_text("paper.pdf")          # All pages
    text = extract_text("paper.pdf", page=2)  # Single page

Arguments:
    file.pdf     Path to the PDF file
    --page N     Page number to extract (1-indexed). If omitted, extracts all pages.
    --max-lines  Limit output to N lines (default: unlimited)

Requirements:
    pip install pypdf

Routing rule for AI assistants:
    Use this tool when you need to read PDF content in AI conversations.
    For JOSS review PDFs with line numbers, extract the full text and parse
    line numbers from text (they appear at the end of each line).
"""

import sys
from pathlib import Path


def extract_text(pdf_path, page=None):
    """
    Extract text from PDF.
    
    Args:
        pdf_path: Path to PDF file (str or Path)
        page: Page number (1-indexed). If None, extracts all pages.
    
    Returns:
        str: Extracted text
    
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ImportError: If pypdf is not installed
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError(
            "pypdf is required for PDF extraction. "
            "Install with: pip install pypdf"
        )
    
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    reader = PdfReader(str(path))
    
    if page is not None:
        if page < 1 or page > len(reader.pages):
            raise ValueError(
                f"Page {page} out of range. "
                f"PDF has {len(reader.pages)} pages."
            )
        return reader.pages[page - 1].extract_text()
    
    # Extract all pages
    return '\n'.join([p.extract_text() for p in reader.pages])


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract text from PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument(
        "--page",
        type=int,
        help="Page number to extract (1-indexed). If omitted, extracts all pages."
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        help="Limit output to N lines"
    )
    
    args = parser.parse_args()
    
    try:
        text = extract_text(args.pdf_path, page=args.page)
        
        if args.max_lines:
            lines = text.split('\n')
            if len(lines) > args.max_lines:
                text = '\n'.join(lines[:args.max_lines])
                text += f"\n\n[... {len(lines) - args.max_lines} more lines omitted ...]"
        
        print(text)
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
