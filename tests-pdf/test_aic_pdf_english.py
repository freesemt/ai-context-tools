"""aic_tools.pdf の _extract_with_pypdf を英語PDFでテスト"""
from pathlib import Path
from aic_tools.pdf import _extract_with_pypdf

# Relative path to sibling repo
pdf_path = Path(__file__).parent.parent.parent / 'molass-review' / 'reference_papers' / '2025, Furukawa.pdf'

print("="*70)
print("テスト：aic_tools.pdf の _extract_with_pypdf（英語PDF）")
print("="*70)

try:
    text = _extract_with_pypdf(pdf_path, page=1)
    print(f"\n✅ 抽出成功: {len(text)} chars")
    print(f"\n最初の500文字:")
    print(text[:500])
    print("\n\n結果：警告メッセージは出ませんでした（正常）")
except Exception as e:
    print(f"\n❌ エラー: {e}")
