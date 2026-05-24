# AgentGuard

**Your LangChain agent has a blast radius. AgentGuard measures it.**

When a developer writes `tools=[github_tool, db_tool, slack_tool]` in a LangChain agent, nobody checks whether those tool scopes exceed what the agent's job requires. AgentGuard does.

```bash
pip install agentguard
agentguard scan ./my_agent.py
```

---

## What it does

AgentGuard reads your LangChain agent file, extracts the tools your agent has access to, compares their permission scopes against what the agent's task actually requires, and outputs a risk score with a remediation list.

One command. No account. No API key. No configuration.

---

## Example

Given this agent:

```python
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

Running `agentguard scan ./my_agent.py` outputs:

```
AgentGuard Risk Score: 87/100 — HIGH

3 over-permissioned tools found:

  GitHubTool        has WRITE access — task only requires READ
  SlackTool         has DELETE scope — task never sends or deletes messages
  SQLDatabaseTool   has full schema access — task only needs SELECT

Remediation:
  1. Replace GitHubTool with GitHubReadOnlyTool
  2. Remove SlackTool — not required for PR summarization
  3. Add read_only=True to SQLDatabaseTool
```

---

## Why this matters

Every existing AI agent security tool operates at runtime — after permissions are granted, after the agent is deployed, after the blast radius is already set.

AgentGuard operates at definition time. Before the agent ships.

- **Aembit** manages the secret at runtime
- **Astrix** discovers the secret in your SaaS estate
- **LangSmith** logs what the secret was used for
- **AgentGuard** tells you the secret should never have had that scope

---

## Supported tools (v0.1)

| Tool | Permissions detected |
|------|---------------------|
| GitHubTool | read, write, admin |
| SlackTool | read, write, delete |
| SQLDatabaseTool | select, insert, update, delete, schema |
| GmailTool | read, send, delete |
| FileSystemTool | read, write, delete |
| PythonREPLTool | exec |
| ShellTool | exec |
| RequestsTool | get, post, put, delete |
| NotionTool | read, write |
| JiraTool | read, write, admin |

---

## Scoring

Risk score is calculated from two factors:

1. **Excess permissions** — scopes the tool has that the agent's task doesn't require
2. **Blast radius** — how destructive those excess permissions could be if the agent were compromised or manipulated

A `ShellTool` with exec access on an agent whose job is to read emails scores higher than a `RequestsTool` with GET-only access. Destructive permissions weigh more than read permissions.

| Score | Level | Meaning |
|-------|-------|---------|
| 0–25 | LOW | Minor excess permissions. Low priority. |
| 26–50 | MEDIUM | Notable excess. Review before deploying to production. |
| 51–75 | HIGH | Significant over-permission. Fix before shipping. |
| 76–100 | CRITICAL | Agent has permissions that could cause irreversible damage if compromised. |

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

- v0.1 — LangChain support, 10 tools, CLI
- v0.2 — CrewAI support
- v0.3 — CI/CD integration (GitHub Actions)
- v0.4 — MCP server scanning
- v1.0 — Custom tool definitions, team reports

---

## Contributing

AgentGuard is open source. If you build LangChain agents and have hit this problem, open an issue or a PR.

---

## License

MIT
