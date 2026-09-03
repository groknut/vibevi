# AGENTS.md

## Project

Open-source file viewer built with Python/PyQt. Created with AI agents (vibe coding).

Two-panel UI: right panel — file tree, left panel — content viewer. Sorting by date, name, type. Supports txt, doc/docx, jpeg, png, avi, and more. All rendering done programmatically — no external applications.

Requirements spec: `docs/TASK.md`

## Stack

- **Python 3.13** (pinned in `.python-version`)
- **uv** — package/dependency manager
- **PyQt** — GUI framework (deps not yet declared in `pyproject.toml`)
- **PEP8** — code style

## Architecture

```
main.py          # Entry point
ui/              # PyQt GUI components
parser/          # File parsing logic
```

## Notes

- No test suite, linter, or CI configured yet
- No lockfile — run `uv sync` after dependencies are added
- Doxygen documentation planned per `docs/TASK.md`
