"""aic_tools.pdf の _extract_with_pypdf を英語PDFでテスト"""
import os
from pathlib import Path
from aic_tools.pdf import _extract_with_pypdf

# Folder with the English test papers (not in git, copyrighted): set AIC_TEST_PAPERS_DIR,
# otherwise the former location in the sibling repo molass-review is tried
papers_dir = Path(os.environ.get('AIC_TEST_PAPERS_DIR',
                                 Path(__file__).parent.parent.parent / 'molass-review' / 'reference_papers'))
pdf_path = papers_dir / '2025, Furukawa.pdf'

print("="*70)
print("テスト：aic_tools.pdf の _extract_with_pypdf（英語PDF）")
print("="*70)

if not pdf_path.exists():
    raise SystemExit(f"SKIP: {pdf_path} not found (set AIC_TEST_PAPERS_DIR to a folder containing the test papers)")

try:
    text = _extract_with_pypdf(pdf_path, page=1)
    print(f"\n✅ 抽出成功: {len(text)} chars")
    print(f"\n最初の500文字:")
    print(text[:500])
    print("\n\n結果：警告メッセージは出ませんでした（正常）")
except Exception as e:
    print(f"\n❌ エラー: {e}")
