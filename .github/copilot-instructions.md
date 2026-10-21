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

## Git and shell quirks on Windows PowerShell

Shared rules from [ai-context-standard](https://github.com/freesemt/ai-context-standard) v0.10.2 ("PowerShell Terminal — Native-command Output and Commit Messages"):

- A red `NativeCommandError` after `git push` / `fetch` or `gh` is stderr progress, not failure. Judge by the result line (`a1b2c3d..e4f5a6b  main -> main`, `✓ Closed issue`) or `git status -sb`; do not retry.
- Commit messages (and `gh ... --body-file` text): write to a fresh file with the editor's create tool, then `git commit -F <file>`. `git commit -F -` from a here-string fails. Keep trailers such as `Co-authored-by:`.
- `| Select-Object -Last N` buffers output until the command ends; silence is expected.
- Tool calls in one batch run in parallel: read an artifact in a later batch than the call that creates it.

## Response language

**Response language**: English
