"""
Tool permission database.
Each entry defines what scopes a tool carries and the blast radius weight of each scope.
Blast radius weight: how destructive is this permission if the agent is compromised?
  1 = low (read-only, reversible)
  2 = medium (write, reversible)
  3 = high (delete, send, irreversible)
  4 = critical (exec, admin, schema-altering)
"""

TOOL_PERMISSIONS = {
    "GitHubTool": {
        "scopes": ["read", "write", "admin"],
        "blast_radius": {"read": 1, "write": 2, "admin": 4},
        "description": "GitHub repository access",
        "safe_alternative": "Use read_only=True or a scoped token with only repo:read",
    },
    "SlackTool": {
        "scopes": ["read", "write", "delete"],
        "blast_radius": {"read": 1, "write": 2, "delete": 3},
        "description": "Slack workspace access",
        "safe_alternative": "Use channels:read,channels:history scopes only if agent only reads",
    },
    "SQLDatabaseTool": {
        "scopes": ["select", "insert", "update", "delete", "schema"],
        "blast_radius": {"select": 1, "insert": 2, "update": 2, "delete": 3, "schema": 4},
        "description": "SQL database access",
        "safe_alternative": "Add read_only=True and restrict to specific tables",
    },
    "GmailTool": {
        "scopes": ["read", "send", "delete"],
        "blast_radius": {"read": 1, "send": 3, "delete": 3},
        "description": "Gmail access",
        "safe_alternative": "Use gmail.readonly scope if agent only reads emails",
    },
    "FileSystemTool": {
        "scopes": ["read", "write", "delete"],
        "blast_radius": {"read": 1, "write": 2, "delete": 3},
        "description": "Local file system access",
        "safe_alternative": "Restrict to a specific directory with read_only=True",
    },
    "PythonREPLTool": {
        "scopes": ["exec"],
        "blast_radius": {"exec": 4},
        "description": "Python code execution",
        "safe_alternative": "Use a sandboxed environment or remove if not strictly needed",
    },
    "ShellTool": {
        "scopes": ["exec"],
        "blast_radius": {"exec": 4},
        "description": "Shell command execution",
        "safe_alternative": "Remove if possible. If needed, whitelist specific commands only",
    },
    "RequestsTool": {
        "scopes": ["get", "post", "put", "delete"],
        "blast_radius": {"get": 1, "post": 2, "put": 2, "delete": 3},
        "description": "HTTP requests to external URLs",
        "safe_alternative": "Restrict to GET only if agent only fetches data",
    },
    "NotionTool": {
        "scopes": ["read", "write"],
        "blast_radius": {"read": 1, "write": 2},
        "description": "Notion workspace access",
        "safe_alternative": "Use read-only integration token if agent only reads pages",
    },
    "JiraTool": {
        "scopes": ["read", "write", "admin"],
        "blast_radius": {"read": 1, "write": 2, "admin": 4},
        "description": "Jira project access",
        "safe_alternative": "Use browse_projects scope only if agent only reads issues",
    },
}

# Keywords in agent task descriptions that map to required permission scopes
# Used to infer what the agent actually needs vs what it has
TASK_KEYWORDS = {
    "read": [
        "read", "summarize", "summary", "fetch", "get", "retrieve",
        "list", "search", "find", "check", "review", "analyze", "report",
        "monitor", "watch", "look", "scan", "query", "select",
    ],
    "write": [
        "write", "create", "update", "edit", "modify", "post", "add",
        "insert", "set", "push", "save", "store", "generate", "draft",
    ],
    "send": [
        "send", "notify", "alert", "email", "message", "reply", "respond",
        "communicate", "share",
    ],
    "delete": [
        "delete", "remove", "clean", "purge", "archive", "clear",
    ],
    "exec": [
        "execute", "run", "compute", "calculate", "process", "install",
        "deploy", "build", "compile",
    ],
    "admin": [
        "admin", "manage", "configure", "setup", "provision", "control",
        "govern", "administer",
    ],
}

# Map tool-specific scopes to canonical action categories
SCOPE_TO_ACTION = {
    # read-like
    "read": "read", "select": "read", "get": "read",
    # write-like
    "write": "write", "insert": "write", "update": "write",
    "post": "write", "put": "write",
    # send-like
    "send": "send",
    # delete-like
    "delete": "delete",
    # exec-like
    "exec": "exec",
    # admin-like
    "admin": "admin", "schema": "admin",
}
