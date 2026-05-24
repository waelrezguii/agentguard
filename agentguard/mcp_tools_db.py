"""
MCP server permission database.
Maps known MCP server packages to their capabilities and blast radius.
"""

MCP_SERVER_DB = {
    # ── FILESYSTEM ──────────────────────────────────────────────────────────
    "@modelcontextprotocol/server-filesystem": {
        "scopes": ["read", "write", "delete"],
        "blast_radius": {"read": 1, "write": 2, "delete": 3},
        "description": "Local filesystem read/write/delete access",
        "path_sensitive": True,
        "safe_alternative": "Restrict the path argument to a specific project folder, not your home directory",
    },

    # ── VERSION CONTROL ──────────────────────────────────────────────────────
    "@modelcontextprotocol/server-github": {
        "scopes": ["read", "write", "admin"],
        "blast_radius": {"read": 1, "write": 2, "admin": 4},
        "description": "GitHub repository and organization access",
        "credential_sensitive": True,
        "safe_alternative": "Use a fine-grained PAT scoped to specific repos with read-only permissions",
    },
    "@modelcontextprotocol/server-gitlab": {
        "scopes": ["read", "write", "admin"],
        "blast_radius": {"read": 1, "write": 2, "admin": 4},
        "description": "GitLab repository and group access",
        "credential_sensitive": True,
        "safe_alternative": "Use a project-scoped access token with read_repository scope only",
    },
    "mcp-server-git": {
        "scopes": ["read", "write"],
        "blast_radius": {"read": 1, "write": 2},
        "description": "Git operations on local repositories",
        "safe_alternative": "Restrict to specific repositories if possible",
    },

    # ── DATABASES ────────────────────────────────────────────────────────────
    "@modelcontextprotocol/server-postgres": {
        "scopes": ["select", "insert", "update", "delete", "schema"],
        "blast_radius": {"select": 1, "insert": 2, "update": 2, "delete": 3, "schema": 4},
        "description": "PostgreSQL database — full read/write access",
        "connection_string_sensitive": True,
        "safe_alternative": "Create a read-only DB user. Never point at production.",
    },
    "@modelcontextprotocol/server-sqlite": {
        "scopes": ["select", "insert", "update", "delete"],
        "blast_radius": {"select": 1, "insert": 2, "update": 2, "delete": 3},
        "description": "SQLite database read/write access",
        "safe_alternative": "Use a copy of the database file, not the live file",
    },
    "@modelcontextprotocol/server-mysql": {
        "scopes": ["select", "insert", "update", "delete", "schema"],
        "blast_radius": {"select": 1, "insert": 2, "update": 2, "delete": 3, "schema": 4},
        "description": "MySQL database — full read/write access",
        "connection_string_sensitive": True,
        "safe_alternative": "Create a read-only DB user. Never point at production.",
    },

    # ── COMMUNICATION ────────────────────────────────────────────────────────
    "@modelcontextprotocol/server-slack": {
        "scopes": ["read", "write"],
        "blast_radius": {"read": 1, "write": 3},
        "description": "Slack — can read all channels and send messages as you",
        "credential_sensitive": True,
        "safe_alternative": "Use a bot token restricted to specific channels with read-only scope",
    },
    "@modelcontextprotocol/server-gmail": {
        "scopes": ["read", "send", "delete"],
        "blast_radius": {"read": 1, "send": 3, "delete": 3},
        "description": "Gmail — can read, send, and delete emails",
        "safe_alternative": "Use gmail.readonly OAuth scope if agent only reads emails",
    },

    # ── CLOUD STORAGE ────────────────────────────────────────────────────────
    "@modelcontextprotocol/server-google-drive": {
        "scopes": ["read", "write", "delete"],
        "blast_radius": {"read": 1, "write": 2, "delete": 3},
        "description": "Google Drive — read, write, and delete files",
        "safe_alternative": "Use drive.readonly OAuth scope if agent only reads",
    },
    "@modelcontextprotocol/server-gdrive": {
        "scopes": ["read", "write", "delete"],
        "blast_radius": {"read": 1, "write": 2, "delete": 3},
        "description": "Google Drive — read, write, and delete files",
        "safe_alternative": "Use drive.readonly OAuth scope if agent only reads",
    },

    # ── WEB / NETWORK ────────────────────────────────────────────────────────
    "@modelcontextprotocol/server-fetch": {
        "scopes": ["get", "post"],
        "blast_radius": {"get": 1, "post": 2},
        "description": "HTTP fetch — can make GET and POST requests to any URL",
        "safe_alternative": "Restrict to specific allowed domains if your use case allows it",
    },
    "@modelcontextprotocol/server-brave-search": {
        "scopes": ["read"],
        "blast_radius": {"read": 1},
        "description": "Brave web search — read-only, no external side effects",
        "safe_alternative": "Safe to use as-is",
    },
    "@modelcontextprotocol/server-puppeteer": {
        "scopes": ["exec", "read", "write"],
        "blast_radius": {"exec": 4, "read": 1, "write": 2},
        "description": "Headless browser — can navigate, click, fill forms, and execute JS on any site",
        "safe_alternative": "Only enable if you need browser automation. Scope to specific domains.",
    },

    # ── SHELL / CODE EXECUTION ───────────────────────────────────────────────
    "@modelcontextprotocol/server-everything": {
        "scopes": ["exec", "read", "write", "delete", "admin"],
        "blast_radius": {"exec": 4, "read": 1, "write": 2, "delete": 3, "admin": 4},
        "description": "Demo server with ALL capabilities — never use outside of testing",
        "safe_alternative": "Remove immediately. This is a development/demo server only.",
    },
    "mcp-server-docker": {
        "scopes": ["exec", "admin"],
        "blast_radius": {"exec": 4, "admin": 4},
        "description": "Docker — can create, run, and delete containers",
        "safe_alternative": "Use read-only Docker API if only monitoring. Avoid in production.",
    },
    "mcp-server-kubernetes": {
        "scopes": ["exec", "admin"],
        "blast_radius": {"exec": 4, "admin": 4},
        "description": "Kubernetes — can create/delete pods, deployments, and cluster resources",
        "safe_alternative": "Use a ServiceAccount with read-only ClusterRole if only monitoring",
    },

    # ── CLOUD PROVIDERS ──────────────────────────────────────────────────────
    "mcp-server-aws": {
        "scopes": ["read", "write", "admin"],
        "blast_radius": {"read": 1, "write": 2, "admin": 4},
        "description": "AWS — scope depends on the IAM role/credentials provided",
        "safe_alternative": "Use a least-privilege IAM policy with only the actions you need",
    },

    # ── SAFE / LOW RISK ──────────────────────────────────────────────────────
    "@modelcontextprotocol/server-memory": {
        "scopes": ["read", "write"],
        "blast_radius": {"read": 1, "write": 1},
        "description": "In-memory knowledge graph — stores conversation context locally",
        "safe_alternative": "Safe to use as-is",
    },
    "@modelcontextprotocol/server-sequentialthinking": {
        "scopes": ["read"],
        "blast_radius": {"read": 1},
        "description": "Structured thinking tool — no external access",
        "safe_alternative": "Safe to use as-is",
    },
}

# Paths that indicate dangerously broad filesystem access
DANGEROUS_PATH_PATTERNS = [
    # Unix home directories
    ("~", "home_dir"),
    ("/home/", "home_dir"),
    ("/Users/", "home_dir"),
    ("/root", "root"),
    # Unix root
    ("/", "root"),
    # Windows drives
    ("C:\\", "root"),
    ("C:/", "root"),
    ("D:\\", "root"),
    ("D:/", "root"),
]

# Indicators that a connection string points to a production environment
PRODUCTION_INDICATORS = [
    "prod", "production", "live", "master-db",
    ".rds.amazonaws.com",
    "cloud.google.com",
    ".azure.com",
    "planetscale.com",
    "neon.tech",
    "supabase.co",
]
