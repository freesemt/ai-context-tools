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
| [vscode-version-recorder](https://github.com/freesemt/vscode-version-recorder) | TypeScript / VS Code extension | Records VS Code version to `.github/vscode-version.txt` |
| **ai-context-tools** (this package) | Python | AI workflow utilities (notebook output reading, etc.) |

Both tools support the [AI Context Standard](https://github.com/freesemt/ai-context-standard).

---

## License

MIT
