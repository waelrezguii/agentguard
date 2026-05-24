# AgentGuard

**Audit the permission surface of your AI agents and MCP servers — before they ship.**

[![CI](https://github.com/waelrezguii/agentguard/actions/workflows/ci.yml/badge.svg)](https://github.com/waelrezguii/agentguard/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://github.com/waelrezguii/agentguard)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

```bash
pip install agentguard

# Scan your MCP config (Claude Desktop, Cursor, VSCode, Windsurf)
agentguard scan-mcp

# Scan a LangChain agent file
agentguard scan ./my_agent.py
```

No account. No API key. No configuration.

---

## MCP Security Scanner

Every MCP config file on your machine is a list of tools your AI can use. Most people configure them without realizing what they've granted:

- The filesystem server pointed at `~` gives the AI **read/write access to every file you own** — including `.ssh/`, `.aws/credentials`, and every `.env` file
- A Slack token in plaintext in `claude_desktop_config.json` can be exfiltrated by a malicious prompt
- A PostgreSQL connection string pointing at your production database means one bad prompt deletes your data

AgentGuard scans those files and tells you exactly what's at risk.

```bash
$ agentguard scan-mcp
```

```
AgentGuard — MCP Security Scanner  [Claude Desktop]
Config: C:\Users\alice\AppData\Roaming\Claude\claude_desktop_config.json

Risk Score: 95/100 — CRITICAL

Servers: 3 servers analyzed · 1 unknown

2 risky servers found:

  ● filesystem
  Local filesystem read/write/delete access
  Package: @modelcontextprotocol/server-filesystem

  ⚠  Path '/Users/alice' exposes your entire home directory —
       includes .ssh keys, .aws credentials, .env files, and all your code
       Blast radius: critical blast radius

  Fix: Restrict the path argument to a specific project folder, not your home directory

  ● postgres
  PostgreSQL database — full read/write access
  Package: @modelcontextprotocol/server-postgres

  ⚠  Connection string points to a production database
       Blast radius: critical blast radius

  Fix: Create a read-only DB user. Never point at production.

CRITICAL: A prompt injection attack could cause irreversible damage with this configuration.
```

### Supported MCP apps

AgentGuard auto-detects config files for:

| App | Config path |
|-----|-------------|
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Claude Desktop (Mac) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Cursor | `~/.cursor/mcp.json` |
| VSCode | `~/.vscode/mcp.json` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` |

Or pass a custom path:

```bash
agentguard scan-mcp --config ./my-mcp-config.json
```

### Supported MCP servers (v0.2)

22 servers in the database — filesystem, GitHub, GitLab, PostgreSQL, MySQL, SQLite, Slack, Gmail, Google Drive, Fetch, Brave Search, Puppeteer, Docker, Kubernetes, AWS, and more.

Missing one? [Add it in under 10 minutes →](CONTRIBUTING.md)

---

## LangChain Agent Scanner

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
    → delete scope   high blast radius
    → schema scope   critical blast radius
  Fix: Add read_only=True and restrict to specific tables

  GitHubTool
  GitHub repository access
    → admin scope   critical blast radius
  Fix: Use read_only=True or a scoped token with only repo:read

  SlackTool
  Slack workspace access
    → write scope   medium blast radius
  Fix: Use channels:read scope only

CRITICAL: This agent could cause irreversible damage if compromised or manipulated.
```

---

## Why this matters

Every existing AI agent security tool operates at runtime — after permissions are granted, after the agent is deployed, after the blast radius is already set.

AgentGuard operates at **definition time**. Before anything can go wrong.

| Tool | When it acts | What it covers |
|------|-------------|----------------|
| **AgentGuard** | Before deployment | Permission scope audit |
| Aembit | Runtime | Secret management |
| Astrix | Discovery | SaaS estate visibility |
| LangSmith | Runtime | Logging and tracing |

---

## CLI reference

```bash
# MCP scanning
agentguard scan-mcp                          # auto-detect all configs
agentguard scan-mcp --config PATH            # specific file
agentguard scan-mcp --app "My App"           # custom label
agentguard scan-mcp --json                   # JSON output
agentguard scan-mcp --fail-on HIGH           # exit 1 if HIGH or above (CI)

# LangChain scanning
agentguard scan ./my_agent.py
agentguard scan ./my_agent.py --json
agentguard scan ./my_agent.py --fail-on HIGH
agentguard scan ./my_agent.py --no-color
```

### CI/CD integration

```yaml
- name: Audit MCP configs
  run: |
    pip install agentguard
    agentguard scan-mcp --fail-on HIGH
```

---

## Scoring

| Score | Level | Meaning |
|-------|-------|---------|
| 0–25 | LOW | Minor issues |
| 26–50 | MEDIUM | Review before sharing config |
| 51–75 | HIGH | Fix before using with untrusted prompts |
| 76–100 | CRITICAL | Prompt injection could cause irreversible damage |

---

## What AgentGuard is not

- Not a runtime monitor
- Not a prompt injection detector
- Not a secrets manager
- Not a compliance platform

Those tools exist. AgentGuard does one thing: audits your AI's permission surface before it can be abused.

---

## Roadmap

- [x] v0.1 — LangChain scanner, 10 tools, CLI, CI
- [x] v0.2 — MCP scanner, 22 servers, auto-detection for Claude Desktop / Cursor / VSCode / Windsurf
- [ ] v0.3 — GitHub Actions native action
- [ ] v0.4 — CrewAI / AutoGen support
- [ ] v1.0 — Custom server definitions, team reports

---

## Contributing

The fastest contribution: add an MCP server or a LangChain tool to the database. It takes less than 10 minutes.

[See CONTRIBUTING.md →](CONTRIBUTING.md)

---

## License

MIT
