"""
aic_tools.pdf — Extract text from PDF files with automatic library selection.

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

Requirements (auto-selected):
    - Recommended: pip install pymupdf  (best for Japanese/scanned PDFs)
    - Fallback:    pip install pypdf    (sufficient for English PDFs)

Routing rule for AI assistants:
    Just call this tool. It automatically handles:
    - Japanese PDFs (uses pymupdf if available)
    - English PDFs (pypdf fallback is sufficient)
    - Scanned PDFs (pymupdf preferred)
    - Encoding issues (automatic selection)
    
    You don't need to check PDF type or choose which library to use.
"""

import sys
from pathlib import Path


def extract_text(pdf_path, page=None):
    """
    Extract text from PDF using the best available library.
    
    Tries pymupdf first (best quality, Japanese support), 
    falls back to pypdf (lighter, English-friendly).
    
    Args:
        pdf_path: Path to PDF file (str or Path)
        page: Page number (1-indexed). If None, extracts all pages.
    
    Returns:
        str: Extracted text
    
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ImportError: If neither pymupdf nor pypdf is installed
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    # Try pymupdf first (best quality)
    try:
        import fitz  # pymupdf
        return _extract_with_pymupdf(path, page)
    except ImportError:
        pass  # Fall back to pypdf
    
    # Fall back to pypdf
    try:
        from pypdf import PdfReader
        return _extract_with_pypdf(path, page)
    except ImportError:
        raise ImportError(
            "PDF extraction requires either pymupdf or pypdf.\n"
            "Recommended: pip install pymupdf  (best for Japanese/scanned PDFs)\n"
            "Fallback:    pip install pypdf    (sufficient for English PDFs)"
        )


def _extract_with_pymupdf(path, page=None):
    """Extract using pymupdf (fitz)"""
    import fitz
    
    doc = fitz.open(str(path))
    
    try:
        if page is not None:
            if page < 1 or page > len(doc):
                raise ValueError(
                    f"Page {page} out of range. "
                    f"PDF has {len(doc)} pages."
                )
            return doc[page - 1].get_text()
        
        # Extract all pages
        return '\n'.join([p.get_text() for p in doc])
    finally:
        doc.close()


def _extract_with_pypdf(path, page=None):
    """Extract using pypdf (fallback)"""
    from pypdf import PdfReader
    import io
    
    # Capture encoding warnings
    old_stderr = sys.stderr
    stderr_capture = io.StringIO()
    sys.stderr = stderr_capture
    
    try:
        reader = PdfReader(str(path))
        
        if page is not None:
            if page < 1 or page > len(reader.pages):
                raise ValueError(
                    f"Page {page} out of range. "
                    f"PDF has {len(reader.pages)} pages."
                )
            text = reader.pages[page - 1].extract_text()
        else:
            # Extract all pages
            text = '\n'.join([p.extract_text() for p in reader.pages])
        
        # Check for encoding warnings
        warnings = stderr_capture.getvalue()
        if warnings and ('encoding' in warnings.lower() or 'not implemented' in warnings.lower()):
            # Restore stderr and print warning
            sys.stderr = old_stderr
            print(
                "\nWARNING: PDF encoding issue detected.\n"
                "For better quality (especially Japanese/scanned PDFs), install:\n"
                "  pip install pymupdf\n",
                file=sys.stderr
            )
        
        return text
    finally:
        sys.stderr = old_stderr


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
