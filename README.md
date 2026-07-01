# ai-context-tools

AI workflow utilities for the [AI Context Standard](https://github.com/freesemt/ai-context-standard).

**Version**: tracks AI Context Standard version (currently `0.8.8`)

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

### `aic_tools.nb_status` — Read notebook execution status

Reports which cells have been executed (and in what order) by reading the
`execution_count` field stored in the `.ipynb` file.

**When to use** (routing rule for AI assistants):

> ⚠️ **disk vs. live kernel**: execution counts are read from the saved
> `.ipynb` file. If the file was externally rewritten while open in VS Code
> (e.g. via `json.dump`), VS Code reloads from disk and loses unsaved counts.
> In that case, the kernel variables section of `copilot_getNotebookSummary`
> is the authoritative live source — a variable being present there proves the
> cell ran, regardless of what the execution count says.
>
> Use `aic-nb-status` for quick offline checks or to cross-check after a
> suspected external file write.

**CLI**:
```bash
python -m aic_tools.nb_status <notebook.ipynb>
python -m aic_tools.nb_status <notebook.ipynb> --executed-only
python -m aic_tools.nb_status <notebook.ipynb> --json
```

**Entry point** (after install):
```bash
aic-nb-status experiments/13h.ipynb
aic-nb-status experiments/13h.ipynb --executed-only
```

**Python API**:
```python
from aic_tools.nb_status import get_execution_status
rows = get_execution_status("experiments/13h.ipynb")
# Returns list of dicts: cell_number, cell_id, cell_type, execution_count, first_line
```

---

### `aic_tools.runcell` — Execute a notebook cell with fresh outputs

Executes cells `1..N` of a notebook via `nbclient` and prints the target
cell's outputs to the terminal with no size limit. The companion to
`aic_tools.notebook` (which reads stale outputs from disk).

**When to use** (routing rule for AI assistants):
- Use `aic_tools.notebook` when the cell's last-saved output is enough.
- Use `aic_tools.runcell` when you need *fresh* output — e.g. after editing
  code that the cell depends on, or when verifying a one-line fix without
  re-running the entire notebook in the GUI.

**Install execution dependencies** (`nbclient`, `nbformat`, `ipykernel`):
```bash
pip install ai-context-tools[run]
```

**CLI**:
```bash
python -m aic_tools.runcell <notebook.ipynb> <cell_number> \
    [--kernel NAME] [--timeout SEC] [--write] [--max-lines N]

# Examples:
python -m aic_tools.runcell experiments/08d.ipynb 14
python -m aic_tools.runcell experiments/08d.ipynb 14 --write    # save outputs
python -m aic_tools.runcell experiments/08d.ipynb 14 --kernel python3
```

**Entry point** (after install):
```bash
aic-runcell experiments/08d.ipynb 14
```

**Python API**:
```python
from aic_tools.runcell import run_up_to_cell
cell = run_up_to_cell("experiments/08d.ipynb", 14)
```

**Behaviour**:
- Executes cells 1 through `cell_number` in order (markdown cells are skipped
  by nbclient automatically) so the kernel state is correctly built up.
- Read-only by default — the `.ipynb` is not modified unless `--write` is
  passed.
- Exit code `1` on cell error, file-not-found, or invalid arguments.

---

### `aic_tools.marimo_session` — Read marimo notebook cell outputs

Reads the marimo session cache written to `__marimo__/session/<notebook_name>.py.json`
after each execution. Works without a running server — reads from disk.

**When to use** (routing rule for AI assistants):

| Output type | Tool |
|---|---|
| `console` (stdout/stderr from `print()`) | `aic_tools.marimo_session` — always readable as text |
| `text/plain`, `text/markdown` | `aic_tools.marimo_session` |
| `text/html` with embedded image | size summary only; use `screenshot_page()` to view |
| Live UI (sliders, buttons) | browser tools — `screenshot_page()`, `run_playwright_code()` |

**CLI**:
```bash
python -m aic_tools.marimo_session <notebook.py>              # list all cells
python -m aic_tools.marimo_session <notebook.py> <cell_N>     # read cell N (1-based)
python -m aic_tools.marimo_session <notebook.py> <cell_N> 50  # limit to 50 lines
```

**Entry point** (after install):
```bash
aic-marimo-session experiments/23a_basic_workflow.py
aic-marimo-session experiments/23a_basic_workflow.py 8
```

**Python API**:
```python
from aic_tools.marimo_session import list_cells, read_cell_output
list_cells("experiments/23a_basic_workflow.py")
read_cell_output("experiments/23a_basic_workflow.py", 8)
read_cell_output("experiments/23a_basic_workflow.py", 8, max_lines=50)
```

**Note**: `marimo mcp` does not exist in marimo 0.23.8. This tool is the
primary offline alternative for AI-readable marimo cell output.

---

### `aic_tools.edit_lines` — Line-range based file editing

Solves the "duplicate content" problem where `replace_string_in_file` fails
with "Multiple matches found" errors. Uses line numbers instead of string
matching, making edits precise and unambiguous.

**When to use** (routing rule for AI assistants):
- HTML/XML files with duplicate sections (common in generated/templated files)
- Any file where `replace_string_in_file` returns "Multiple matches found"
- Large structural changes where line-based editing is clearer
- When you need to replace exact line ranges (e.g., "replace lines 124-358")

**What problem does this solve?**

VS Code's built-in `replace_string_in_file` requires exact string matching.
If your file has duplicate sections (common in HTML templates, config files,
generated documentation), the tool fails with "Multiple matches found".

This tool uses line numbers instead, so you can target the exact section:

```bash
# Replace lines 124-358 in index.html with content from replacement.html
python -m aic_tools.edit_lines index.html 124 358 replacement.html
```

**CLI**:
```bash
python -m aic_tools.edit_lines <file> <start_line> <end_line> <content_file>
python -m aic_tools.edit_lines <file> <start_line> <end_line> --delete
python -m aic_tools.edit_lines <file> <start_line> <end_line> --stdin

# Examples:
python -m aic_tools.edit_lines index.html 124 358 replacement.html
python -m aic_tools.edit_lines config.json 10 20 --delete
echo "new content" | python -m aic_tools.edit_lines file.txt 5 5 --stdin
python -m aic_tools.edit_lines file.txt 1 10 new.txt --no-backup
```

**Entry point** (after install):
```bash
aic-edit-lines index.html 124 358 replacement.html
```

**Python API**:
```python
from aic_tools.edit_lines import edit_lines, delete_lines

# Replace lines 10-20 with new content
edit_lines("index.html", 10, 20, "new content here")

# Replace from file
edit_lines("index.html", 10, 20, content_file="replacement.html")

# Delete lines 10-20
delete_lines("index.html", 10, 20)

# Edit without backup
edit_lines("index.html", 10, 20, "new content", backup=False)
```

**Safety features**:
- Creates `.bak` backup by default (use `--no-backup` to skip)
- Validates line numbers before editing
- Atomic write (writes to temp file, then renames — no partial writes)

---

### `aic_tools.pdf` — Extract text from PDF files

Automatically selects the best PDF library for your document:
- **pymupdf** (recommended): best quality, handles Japanese & scanned PDFs
- **pypdf** (fallback): lighter, sufficient for English text PDFs

**When to use** (routing rule for AI assistants):
Just call this tool — it automatically handles:
- Japanese PDFs (uses pymupdf if available)
- English PDFs (pypdf fallback is sufficient)
- Scanned PDFs (pymupdf preferred)
- Encoding issues (automatic selection)

You don't need to check PDF type or choose which library to use.

**Install PDF dependencies**:
```bash
# Recommended (both libraries for full compatibility):
pip install ai-context-tools[pdf]

# Or install individually:
pip install pymupdf  # recommended
pip install pypdf    # fallback
```

**CLI**:
```bash
python -m aic_tools.pdf <file.pdf>               # Extract all pages
python -m aic_tools.pdf <file.pdf> --page 2      # Extract single page
python -m aic_tools.pdf <file.pdf> --page 2 --max-lines 50

# Examples:
python -m aic_tools.pdf paper.pdf
python -m aic_tools.pdf paper.pdf --page 1
python -m aic_tools.pdf paper.pdf --page 2 --max-lines 20
```

**Entry point** (after install):
```bash
aic-pdf paper.pdf --page 2
```

**Python API**:
```python
from aic_tools.pdf import extract_text

# Extract all pages
text = extract_text("paper.pdf")

# Extract specific page (1-indexed)
text = extract_text("paper.pdf", page=2)
```

**Requirements**:
```bash
pip install ai-context-tools[pdf]
# or
pip install pypdf
```

**JOSS review note**: For JOSS PDFs with line numbering, extract the full page
text — line numbers appear at the end of each line in the extracted text
(e.g., "Software Design34"), making them easily parsable.

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
