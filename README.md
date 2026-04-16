# ai-context-tools

AI workflow utilities for the [AI Context Standard](https://github.com/freesemt/ai-context-standard).

**Version**: tracks AI Context Standard version (currently `0.8.2`)

---

## Installation

```bash
pip install ai-context-tools
```

Or for development (from the workspace):

```bash
pip install -e C:/Users/takahashi/GitHub/ai-context-tools
```

---

## Publishing to PyPI

Uses GitHub Actions with [PyPI Trusted Publisher](https://docs.pypi.org/trusted-publishers/) (OIDC — no API token needed).

**One-time setup on PyPI**: Configure a Trusted Publisher at  
`https://pypi.org/manage/account/publishing/`  
(or for a new package not yet on PyPI, use the "pending publisher" form)

Settings to enter:
- PyPI project name: `ai-context-tools`
- Owner: `freesemt`
- Repository: `ai-context-tools`
- Workflow: `upload_to_pypi.yml`
- Environment: *(leave blank)*

**To publish**: Go to Actions → "Manual Upload Python Package to PyPI" → Run workflow.

The workflow builds the package, uploads to PyPI via OIDC, and creates a version tag (e.g. `v0.8.2`).

---

## Tools

### `aic_tools.notebook` — Read notebook cell outputs

Bypasses the built-in `read_notebook_cell_output` tool size limit by reading
the `.ipynb` JSON directly from disk.

**When to use** (routing rule for AI assistants):
After `copilot_getNotebookSummary`, check each cell's mime types.
If a cell has `application/vnd.code.notebook.stdout`, use this tool —
the built-in tool will fail silently with "output too large".

**CLI**:
```bash
python -m aic_tools.notebook <notebook.ipynb> <cell_number> [max_lines]

# Examples:
python -m aic_tools.notebook experiments/08d.ipynb 14
python -m aic_tools.notebook experiments/08d.ipynb 14 0   # all lines
```

**Entry point** (after install):
```bash
aic-notebook experiments/08d.ipynb 14
```

**Python API**:
```python
from aic_tools.notebook import read_cell_output
read_cell_output("experiments/08d.ipynb", 14)
read_cell_output("experiments/08d.ipynb", 14, max_lines=0)  # all lines
```

---

## Versioning

Package version tracks the AI Context Standard version that introduced each tool.
`0.8.2` = notebook reader introduced in Standard v0.8.2.

---

## Relationship to other tools

| Tool | Language | Role |
|------|----------|------|
| [ai-context-vscode](https://github.com/freesemt/ai-context-vscode) | TypeScript / VS Code extension | Live notebook cell output reading + VS Code version recording (supersedes `vscode-version-recorder`) |
| **ai-context-tools** (this package) | Python | AI workflow utilities (notebook output reading, etc.) |

All tools support the [AI Context Standard](https://github.com/freesemt/ai-context-standard).

> **VS Code users**: The [ai-context-vscode](https://github.com/freesemt/ai-context-vscode) extension reads live cell outputs from the VS Code document model — no save required. This Python package serves as the fallback for terminal-only sessions or non-VS Code editors.

---

## License

MIT
