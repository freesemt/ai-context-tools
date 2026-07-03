"""英語学術論文PDFの比較テスト — pypdf vs pymupdf"""
import sys
import io
from pathlib import Path

# Relative path to sibling repo
papers_dir = Path(__file__).parent.parent.parent / 'molass-review' / 'reference_papers'

# テスト対象のPDF（新旧）
test_pdfs = [
    "2025, Furukawa.pdf",
    "2024, Jesse B. Hopkins.pdf",
    "2018, Alejandro Panjkovich.pdf",
    "1988, Marcel Maeder.pdf",
]

def test_pypdf(pdf_path, sample_lines=20):
    """pypdf でテスト"""
    try:
        from pypdf import PdfReader
        
        # Suppress warnings
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        
        reader = PdfReader(str(pdf_path))
        text = reader.pages[0].extract_text()  # First page
        
        warnings = sys.stderr.getvalue()
        sys.stderr = old_stderr
        
        lines = text.split('\n')[:sample_lines]
        return {
            'success': True,
            'text': '\n'.join(lines),
            'length': len(text),
            'warnings': warnings.strip() if warnings.strip() else None
        }
    except Exception as e:
        sys.stderr = old_stderr
        return {'success': False, 'error': str(e)}

def test_pymupdf(pdf_path, sample_lines=20):
    """pymupdf でテスト"""
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        text = doc[0].get_text()  # First page
        doc.close()
        
        lines = text.split('\n')[:sample_lines]
        return {
            'success': True,
            'text': '\n'.join(lines),
            'length': len(text)
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

print("=" * 80)
print("英語学術論文PDF比較テスト — pypdf vs pymupdf")
print("=" * 80)

for pdf_name in test_pdfs:
    pdf_path = papers_dir / pdf_name
    
    if not pdf_path.exists():
        print(f"\n⚠️  SKIP: {pdf_name} (not found)")
        continue
    
    print(f"\n{'='*80}")
    print(f"📄 {pdf_name}")
    print('='*80)
    
    # pypdf test
    print("\n[pypdf]")
    result_pypdf = test_pypdf(pdf_path)
    if result_pypdf['success']:
        print(f"✅ Success ({result_pypdf['length']} chars)")
        if result_pypdf['warnings']:
            print(f"⚠️  Warnings: {result_pypdf['warnings'][:200]}")
        print("\nSample (first 20 lines):")
        print(result_pypdf['text'][:500])
    else:
        print(f"❌ Error: {result_pypdf['error']}")
    
    # pymupdf test
    print("\n[pymupdf]")
    result_pymupdf = test_pymupdf(pdf_path)
    if result_pymupdf['success']:
        print(f"✅ Success ({result_pymupdf['length']} chars)")
        print("\nSample (first 20 lines):")
        print(result_pymupdf['text'][:500])
    else:
        print(f"❌ Error: {result_pymupdf['error']}")
    
    # Comparison
    if result_pypdf['success'] and result_pymupdf['success']:
        diff = result_pymupdf['length'] - result_pypdf['length']
        print(f"\n📊 Length difference: {diff:+d} chars ({result_pypdf['length']} vs {result_pymupdf['length']})")

print("\n" + "=" * 80)
print("結論")
print("=" * 80)
