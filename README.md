# AgentGuard

**Your LangChain agent has a blast radius. AgentGuard measures it.**

[![CI](https://github.com/waelrezguii/agentguard/actions/workflows/ci.yml/badge.svg)](https://github.com/waelrezguii/agentguard/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://github.com/waelrezguii/agentguard)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

When a developer writes `tools=[github_tool, db_tool, slack_tool]` in a LangChain agent, nobody checks whether those tool scopes exceed what the agent's job requires. AgentGuard does — before the agent ships.

```bash
pip install agentguard
agentguard scan ./my_agent.py
```

No account. No API key. No configuration.

---

## Example

```python
# my_agent.py
from langchain.agents import initialize_agent
from langchain_community.tools import GitHubTool, SlackTool, SQLDatabaseTool

agent = initialize_agent(
    tools=[GitHubTool, SlackTool, SQLDatabaseTool],
    llm=llm,
    agent_kwargs={
        "system_message": "You are an assistant that summarizes pull requests."
    }
)
```

```
$ agentguard scan ./my_agent.py

AgentGuard — AI Agent Permission Scanner
File: my_agent.py

Risk Score: 100/100 — CRITICAL

Task: "You are an assistant that summarizes pull requests."
Required actions inferred: read

3 over-permissioned tools found:

  SQLDatabaseTool
  SQL database access
    → insert scope   medium blast radius
    → update scope   medium blast radius
    → delete scope   high blast radius
    → schema scope   critical blast radius
  Fix: Add read_only=True and restrict to specific tables

  GitHubTool
  GitHub repository access
    → write scope   medium blast radius
    → admin scope   critical blast radius
  Fix: Use read_only=True or a scoped token with only repo:read

  SlackTool
  Slack workspace access
    → write scope   medium blast radius
    → delete scope  high blast radius
  Fix: Use channels:read,channels:history scopes only if agent only reads

Remediation:
  1. Add read_only=True and restrict to specific tables
  2. Use read_only=True or a scoped token with only repo:read
  3. Use channels:read,channels:history scopes only if agent only reads

CRITICAL: This agent could cause irreversible damage if compromised or manipulated.
```

---

## Why this matters

Every existing AI agent security tool operates at runtime — after permissions are granted, after the agent is deployed, after the blast radius is already set.

AgentGuard operates at **definition time**. Before the agent ships.

| Tool | When it acts | What it covers |
|------|-------------|----------------|
| **AgentGuard** | Before deployment | Permission scope audit |
| Aembit | Runtime | Secret management |
| Astrix | Discovery | SaaS estate visibility |
| LangSmith | Runtime | Logging and tracing |

---

## Supported tools (v0.1)

| Tool | Permissions detected |
|------|---------------------|
| `GitHubTool` | read, write, admin |
| `SlackTool` | read, write, delete |
| `SQLDatabaseTool` | select, insert, update, delete, schema |
| `GmailTool` | read, send, delete |
| `FileSystemTool` | read, write, delete |
| `PythonREPLTool` | exec |
| `ShellTool` | exec |
| `RequestsTool` | get, post, put, delete |
| `NotionTool` | read, write |
| `JiraTool` | read, write, admin |

Missing a tool you use? [Add it in under 10 minutes →](CONTRIBUTING.md)

---

## How it works

1. **Parses** the agent file (AST + regex fallback) to extract the tool list and task description
2. **Infers** required permission scopes from the task description keywords
3. **Compares** tool scopes against required scopes to find excess permissions
4. **Scores** excess permissions by blast radius — exec/admin scope counts more than read scope

### Scoring

| Score | Level | Meaning |
|-------|-------|---------|
| 0–25 | LOW | Minor excess permissions |
| 26–50 | MEDIUM | Notable excess — review before production |
| 51–75 | HIGH | Significant over-permission — fix before shipping |
| 76–100 | CRITICAL | Could cause irreversible damage if compromised |

---

## CLI reference

```bash
# Basic scan
agentguard scan ./my_agent.py

# JSON output (for programmatic use)
agentguard scan ./my_agent.py --json

# CI/CD integration — exit 1 if risk is HIGH or above
agentguard scan ./my_agent.py --fail-on HIGH

# No color (for log files)
agentguard scan ./my_agent.py --no-color
```

### CI/CD integration

Add to your GitHub Actions workflow:

```yaml
- name: Audit agent permissions
  run: |
    pip install agentguard
    agentguard scan ./my_agent.py --fail-on HIGH
```

---

## What AgentGuard is not

- Not a runtime monitor
- Not a prompt injection detector
- Not a secrets manager
- Not a compliance platform
- Not a dashboard

Those tools exist. AgentGuard does one thing: audits your agent's permission surface before it ships.

---

## Roadmap

- [x] v0.1 — LangChain support, 10 tools, CLI, CI badge
- [ ] v0.2 — CrewAI support
- [ ] v0.3 — GitHub Actions native action
- [ ] v0.4 — MCP server scanning
- [ ] v1.0 — Custom tool definitions, team reports

---

## Contributing

The fastest contribution: add a tool to the database. It takes less than 10 minutes.

[See CONTRIBUTING.md →](CONTRIBUTING.md)

---

## License

MIT
