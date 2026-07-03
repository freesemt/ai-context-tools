# PDF Extraction Tests

Manual test scripts for PDF text extraction functionality using real academic papers.

## Test Scripts

| Script | Purpose | Test Data |
|--------|---------|-----------|
| `test_aic_pdf_english.py` | Test `_extract_with_pypdf` on English PDF | `molass-review/reference_papers/2025, Furukawa.pdf` |
| `test_aic_pdf_pypdf.py` | Test `_extract_with_pypdf` on Japanese PDF | `humanomics/docs/references/2019, Yasuo, Honjo.pdf` |
| `test_english_pdfs.py` | Compare pypdf vs pymupdf on multiple English papers | `molass-review/reference_papers/` (4 papers) |
| `test_pdf_comparison.py` | Compare pypdf vs pymupdf on Japanese paper | `humanomics/docs/references/2019, Yasuo, Honjo.pdf` |
| `test_pypdf_warning.py` | Detect encoding warnings from pypdf on Japanese PDF | `humanomics/docs/references/2019, Yasuo, Honjo.pdf` |

## Requirements

These tests require **sibling repositories** to be cloned:
```
GitHub/
├── ai-context-tools/    ← this repo
├── molass-review/       ← for English test papers
└── humanomics/          ← for Japanese test papers
```

If repositories are in different locations, tests will fail with "file not found" errors.

## Running Tests

```powershell
cd tests-pdf
py test_aic_pdf_english.py
py test_aic_pdf_pypdf.py
py test_english_pdfs.py
```

## Why These Are Manual Tests

1. **Not for CI** — require private repositories with non-public papers
2. **For development** — validate PDF extraction behavior on real-world documents
3. **Comparison testing** — benchmark pypdf vs pymupdf for performance and accuracy

## Automated Tests

For automated testing (pytest), see `tests/` directory which uses synthetic data or public samples.
