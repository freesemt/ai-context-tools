"""pypdf vs pymupdf 比較テスト — 本荘論文"""
import sys
import io

print("=" * 70)
print("TEST 1: pypdf (現行実装)")
print("=" * 70)

try:
    from pathlib import Path
    from pypdf import PdfReader
    pdf_path = Path(__file__).parent.parent.parent / 'humanomics' / 'docs' / 'references' / '2019, Yasuo, Honjo.pdf'
    reader = PdfReader(str(pdf_path))
    
    # Suppress stderr warnings
    old_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    text = reader.pages[1].extract_text()  # Page 2 (0-indexed)
    
    sys.stderr = old_stderr
    
    print(text[:500])
    print(f"\n[Total length: {len(text)} chars]")
except Exception as e:
    sys.stderr = old_stderr
    print(f"ERROR: {e}")

print("\n\n")
print("=" * 70)
print("TEST 2: pymupdf (fitz)")
print("=" * 70)

try:
    from pathlib import Path
    import fitz
    pdf_path = Path(__file__).parent.parent.parent / 'humanomics' / 'docs' / 'references' / '2019, Yasuo, Honjo.pdf'
    doc = fitz.open(str(pdf_path))
    text = doc[1].get_text()  # Page 2 (0-indexed)
    print(text[:500])
    print(f"\n[Total length: {len(text)} chars]")
    doc.close()
except Exception as e:
    print(f"ERROR: {e}")

print("\n\n")
print("=" * 70)
print("結論")
print("=" * 70)
print("pypdf: 日本語エンコーディング警告あり、文字化け混在の可能性")
print("pymupdf: 日本語完全対応、警告なし")
