# Contributing to AgentGuard

The most valuable contribution you can make right now is **adding a tool to the database**.

AgentGuard's detection quality depends entirely on how many tools are in `agentguard/tools_db.py`. If you build LangChain agents and use a tool that AgentGuard doesn't know about, adding it takes less than 10 minutes.

---

## How to add a new tool

Open `agentguard/tools_db.py` and add an entry to the `TOOL_PERMISSIONS` dict.

### Template

```python
"YourToolName": {
    "scopes": ["read", "write", "delete"],   # list all permission scopes this tool grants
    "blast_radius": {
        "read":   1,   # 1 = low  (read-only, reversible)
        "write":  2,   # 2 = medium (write, reversible)
        "delete": 3,   # 3 = high  (delete/send, hard to reverse)
    },
    "description": "One-line description of what this tool does",
    "safe_alternative": "How to restrict this tool to least privilege",
},
```

### Blast radius scale

| Weight | Meaning | Examples |
|--------|---------|---------|
| 1 | Low — read-only, fully reversible | list, fetch, get, query |
| 2 | Medium — writes data, reversible | create, update, insert, post |
| 3 | High — deletes or sends irreversibly | delete, send email, message |
| 4 | Critical — executes code or alters schema | exec, shell, schema migration, admin |

### Real example: adding `LinearTool`

```python
"LinearTool": {
    "scopes": ["read", "write", "admin"],
    "blast_radius": {"read": 1, "write": 2, "admin": 4},
    "description": "Linear issue tracker access",
    "safe_alternative": "Use a read-only API token if the agent only reads issues",
},
```

### Scope names and the canonical action map

AgentGuard maps tool-specific scope names to canonical action categories using `SCOPE_TO_ACTION` (also in `tools_db.py`). If your tool uses a scope name that isn't in that map yet, add it:

```python
SCOPE_TO_ACTION = {
    ...
    "your_scope": "canonical_action",   # e.g. "list": "read"
}
```

---

## Steps to submit

1. Fork the repo and create a branch: `git checkout -b add-lineartool`
2. Add the entry to `TOOL_PERMISSIONS` (and `SCOPE_TO_ACTION` if needed)
3. Run the tests: `pytest tests/ -v`
4. Open a PR with the tool name in the title: `Add LinearTool to tools_db`

No new test file needed for adding a tool — the existing test suite covers the analyzer logic. If you want to add a test fixture, add it to `tests/test_analyzer.py`.

---

## Other contributions

- **Bug reports**: open an issue with the agent file that triggered it (redact any secrets)
- **New analysis heuristics**: open an issue first to discuss before implementing
- **New framework support** (CrewAI, AutoGen, etc.): open an issue — this is on the roadmap
