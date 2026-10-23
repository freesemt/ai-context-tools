# PDF Extraction Tests

Manual test scripts for PDF text extraction functionality using real academic papers.

## Test Scripts

| Script | Purpose | Test Data |
|--------|---------|-----------|
| `test_aic_pdf_english.py` | Test `_extract_with_pypdf` on English PDF | `2025, Furukawa.pdf` in the English papers folder (see below) |
| `test_aic_pdf_pypdf.py` | Test `_extract_with_pypdf` on Japanese PDF | `humanomics/docs/references/2019, Yasuo, Honjo.pdf` |
| `test_english_pdfs.py` | Compare pypdf vs pymupdf on multiple English papers | the English papers folder (4 papers) |
| `test_pdf_comparison.py` | Compare pypdf vs pymupdf on Japanese paper | `humanomics/docs/references/2019, Yasuo, Honjo.pdf` |
| `test_pypdf_warning.py` | Detect encoding warnings from pypdf on Japanese PDF | `humanomics/docs/references/2019, Yasuo, Honjo.pdf` |

## Requirements

The papers are copyrighted and not in git. The English ones are looked up in the folder given by the environment variable `AIC_TEST_PAPERS_DIR`; if it is not set, the former location `../molass-review/reference_papers/` (sibling repo, now retired) is tried. The Japanese test paper is read from a sibling repository:
```
GitHub/
├── ai-context-tools/    ← this repo
└── humanomics/          ← for Japanese test papers
```

If a paper is not found, the English scripts skip with a message; the Japanese ones fail with "file not found".

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
