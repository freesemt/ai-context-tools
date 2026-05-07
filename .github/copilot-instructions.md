<!-- AI Context Standard v0.9.2 - Adopted: 2026-05-07 -->
# AI Assistant Initialization Guide — ai-context-tools

**Purpose**: Initialize AI context for working in this repository

---

## What this repository is about

`ai-context-tools` is a Python package providing CLI utilities for the [AI Context Standard](https://github.com/freesemt/ai-context-standard) ecosystem.

**Published at**: https://pypi.org/project/ai-context-tools/

**Key tool**: `python -m aic_tools.notebook <notebook_path> <cell_number> [max_lines]`  
Reads notebook cell stdout from the saved `.ipynb` file on disk, bypassing the VS Code tool size limit.

---

## Repository structure

```
ai-context-tools/
├── .github/
│   ├── copilot-instructions.md  ← this file
│   ├── prompts/
│   │   └── init.prompt.md
│   ├── vscode-version.txt
│   └── workflows/
│       └── upload_to_pypi.yml
├── pyproject.toml
├── README.md
├── aic_tools/
│   ├── __init__.py
│   ├── nb_status.py
│   ├── notebook.py       ← main CLI tool
│   ├── runcell.py
│   └── widget_snapshot.py
└── tests/
```

---

## Publishing to PyPI

Uses GitHub Actions with [PyPI Trusted Publisher](https://docs.pypi.org/trusted-publishers/) (OIDC — no API token needed).

**To publish**: Go to Actions → "Manual Upload Python Package to PyPI" → Run workflow.

The workflow builds the package, uploads to PyPI via OIDC, and creates a version tag (e.g. `v0.9.2`).

---

## Response language

**Response language**: English
