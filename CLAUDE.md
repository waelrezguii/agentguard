# AgentGuard — Project Notes for Claude

## What this project is

AgentGuard is an open-source CLI tool that scans LangChain agent Python files and detects over-permissioned tools before deployment. It operates at **definition time** — before the agent ships — not at runtime.

Built by Wael Rezgui (rezguiwael@hotmail.com).

GitHub: https://github.com/waelrezguii/agentguard

---

## What was built in this session

### 1. pyproject.toml (replaces setup.py)
- Created `pyproject.toml` with `setuptools.build_meta` as build backend
- Includes all metadata: name, version, description, author, license, python_requires
- Entry point: `agentguard = "agentguard.cli:main"`
- Optional dev dependencies: `pytest>=7.0` (install with `pip install -e ".[dev]"`)
- `setup.py` still exists locally but is superseded — can be deleted

### 2. Unit tests (25 tests, all passing)
- `tests/test_parser.py` — 7 tests: tool extraction, task description, FileNotFoundError, ValueError, dedup
- `tests/test_analyzer.py` — 8 tests: CRITICAL score with 3 over-permissioned tools, LOW score on fully-used scopes, unknown tools, empty tools, blast radius sort order
- `tests/test_reporter.py` — 10 tests: string output, ANSI color/no-color, JSON validity, remediation section, filepath in report

**Bug fixed during testing:** `parser.py` `_extract_task_description()` only handled `system_message = "..."` (assignment syntax). Added support for `"system_message": "..."` (dict key syntax used in `agent_kwargs={}`).

Run tests:
```bash
D:\python\python.exe -m pytest tests/ -v
```

### 3. GitHub Actions CI (.github/workflows/ci.yml)
- Triggers on push and PR to main
- Matrix: Python 3.10, 3.11, 3.12
- Steps: checkout → setup-python → `pip install -e ".[dev]"` → `pytest tests/ -v`
- **Fixed:** original pyproject.toml used `setuptools.backends.legacy:build` (experimental, not available on GitHub runners) → changed to `setuptools.build_meta`

### 4. GitHub repo
- Remote: https://github.com/waelrezguii/agentguard.git
- Branch: main
- Python at: `D:\python\python.exe` (Python 3.14.5)
- All 3 CI runs now green

### 5. CONTRIBUTING.md
- Explains how to add a new tool to `tools_db.py` (the main contribution path)
- Includes blast radius scale table, scope-to-action mapping explanation, real example (LinearTool)
- Steps: fork → add entry → run tests → open PR

### 6. README.md (rewritten)
- CI badge, Python badge, MIT badge
- Real scan output shown verbatim
- Positioning table vs Aembit / Astrix / LangSmith
- CLI reference: `--json`, `--fail-on`, `--no-color`
- GitHub Actions snippet for CI/CD integration
- Roadmap with checkboxes
- PyPI badge removed until package is published (step 6)

---

## What still needs to be done

### Step 6 — Publish to PyPI
```bash
D:\python\python.exe -m pip install build twine
cd D:\agentguard
D:\python\python.exe -m build
D:\python\Scripts\twine.exe upload dist/*
```
Requires a PyPI account at pypi.org. After publishing, add back the PyPI badge to README:
```markdown
[![PyPI](https://img.shields.io/pypi/v/agentguard)](https://pypi.org/project/agentguard/)
```

### Step 7 — Post on Reddit r/LangChain
Title: `I built a tool that scans your LangChain agent for over-permissioned tools before you ship it — AgentGuard`
- Show the scan output from sample_agent.py
- Link to GitHub repo
- Ask for feedback and missing tools

### Step 8 — Open issue on LangChain repo
Title: `Security: no built-in way to audit tool permission scopes before deployment`
- Link AgentGuard as partial solution
- Ask if they'd consider integrating something like this

---

## Architecture

```
agentguard/
├── cli.py        — argparse entry point, scan command, --json / --fail-on / --no-color
├── parser.py     — AST + regex extraction of tools list and task description
├── analyzer.py   — scoring engine: excess scopes × blast radius weights
├── reporter.py   — ANSI-colored CLI output formatter
└── tools_db.py   — permission database: 10 tools, blast radius weights, SCOPE_TO_ACTION map
```

### Scoring logic (analyzer.py)
1. Infer required actions from task description keywords (`TASK_KEYWORDS` in tools_db.py)
2. For each tool scope: if its canonical action is not in required actions → excess
3. `raw_score = total_excess_weight / max_possible_weight`
4. If any excess scope has blast_weight >= 4 (exec/admin): multiply by 1.4, cap at 1.0
5. `score = round(raw_score * 100)` → level: LOW / MEDIUM / HIGH / CRITICAL

### Adding a tool
Edit `agentguard/tools_db.py`, add entry to `TOOL_PERMISSIONS`. If the tool uses a scope name not in `SCOPE_TO_ACTION`, add it there too. No other files need changing.

---

## Environment
- Python: `D:\python\python.exe` (3.14.5)
- pytest: `D:\python\Scripts\pytest.exe`
- No external runtime dependencies (stdlib only: ast, re, argparse, pathlib, json, sys)
