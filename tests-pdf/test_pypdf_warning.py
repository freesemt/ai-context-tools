"""pypdf のみで日本語PDF読み取りテスト — エンコーディング警告の検出"""
import sys
import io
from pathlib import Path

# Relative path to sibling repo
pdf_path = Path(__file__).parent.parent.parent / 'humanomics' / 'docs' / 'references' / '2019, Yasuo, Honjo.pdf'

print("="*70)
print("テスト：pypdf で日本語PDFを読む（エンコーディング警告の検出）")
print("="*70)

# pypdf の動作をシミュレート
from pypdf import PdfReader

# Capture stderr
old_stderr = sys.stderr
stderr_capture = io.StringIO()
sys.stderr = stderr_capture

try:
    reader = PdfReader(str(pdf_path))
    text = reader.pages[1].extract_text()  # Page 2
    
    # Restore stderr
    warnings = stderr_capture.getvalue()
    sys.stderr = old_stderr
    
    print(f"\n抽出成功: {len(text)} chars")
    print(f"\n最初の500文字:")
    print(text[:500])
    
    print(f"\n\nstderr 警告:")
    if warnings:
        print(warnings)
        
        # Check for encoding issues
        if 'encoding' in warnings.lower() or 'not implemented' in warnings.lower():
            print("\n" + "="*70)
            print("⚠️  エンコーディング警告を検出")
            print("="*70)
            print("推奨アクション：")
            print("  pip install pymupdf")
            print("\npymupdf は日本語・スキャンPDFに対応しています。")
    else:
        print("(なし)")
        
except Exception as e:
    sys.stderr = old_stderr
    print(f"\nエラー: {e}")
