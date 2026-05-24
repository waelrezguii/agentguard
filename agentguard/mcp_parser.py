"""
MCP Config Parser.
Reads MCP server configurations from standard app locations or a given path.

Supported apps:
  - Claude Desktop  (Windows + Mac)
  - Cursor
  - VSCode
  - Windsurf
"""

import json
import os
import re
from pathlib import Path


_APPDATA = os.environ.get("APPDATA", "")
_HOME = Path.home()

# Standard MCP config file locations keyed by app name
MCP_CONFIG_LOCATIONS: dict[str, Path] = {
    "Claude Desktop": Path(_APPDATA) / "Claude" / "claude_desktop_config.json",
    "Claude Desktop (Mac)": _HOME / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
    "Cursor": _HOME / ".cursor" / "mcp.json",
    "VSCode": _HOME / ".vscode" / "mcp.json",
    "Windsurf": _HOME / ".codeium" / "windsurf" / "mcp_config.json",
}


def find_mcp_configs() -> list[dict]:
    """Return all MCP config files found on this machine."""
    found = []
    for app, path in MCP_CONFIG_LOCATIONS.items():
        if path.exists():
            found.append({"app": app, "path": str(path)})
    return found


def parse_mcp_config(filepath: str) -> dict:
    """
    Parse an MCP config file and extract server definitions.

    Returns:
        {
            servers: list of server dicts,
            filepath: str,
            raw: original parsed JSON,
        }

    Raises:
        FileNotFoundError: if file does not exist
        ValueError: if file is not valid JSON or has no mcpServers key
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {filepath}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}")

    if not isinstance(raw, dict):
        raise ValueError(f"Expected a JSON object, got {type(raw).__name__}")

    servers = _extract_servers(raw)

    return {
        "servers": servers,
        "filepath": str(path.resolve()),
        "raw": raw,
    }


def _extract_servers(raw: dict) -> list[dict]:
    mcp_servers = raw.get("mcpServers", {})
    servers = []
    for name, config in mcp_servers.items():
        if not isinstance(config, dict):
            continue
        server = {
            "name": name,
            "command": config.get("command", ""),
            "args": config.get("args", []),
            "env": config.get("env", {}),
            "package": _infer_package(name, config),
            "paths": _extract_paths(config),
            "exposed_credentials": _find_credentials(config),
        }
        servers.append(server)
    return servers


def _infer_package(name: str, config: dict) -> str:
    """Infer the npm/pip package name from command and args."""
    args = config.get("args", [])
    command = config.get("command", "")

    # npx / npx -y  →  look for @scope/package or *mcp* in args
    if command in ("npx", "bunx", "pnpm", "yarn"):
        for arg in args:
            if arg.startswith("-"):
                continue
            # Strip version tag from package names like @scope/pkg@1.2.3
            return re.sub(r"@[\d.]+$", "", arg)

    # uvx / pipx  →  first non-flag arg is the package
    if command in ("uvx", "pipx"):
        for arg in args:
            if not arg.startswith("-"):
                return arg

    # python -m mcp_server_x  →  convert module to package name
    if command in ("python", "python3") and "-m" in args:
        idx = args.index("-m")
        if idx + 1 < len(args):
            return args[idx + 1].replace("_", "-")

    # node path/to/build/index.js  →  unknown, fall back to server name
    return name


def _extract_paths(config: dict) -> list[str]:
    """Extract filesystem path arguments from the server config."""
    paths = []
    for arg in config.get("args", []):
        if _looks_like_path(arg):
            paths.append(arg)
    return paths


def _looks_like_path(s: str) -> bool:
    if not s or s.startswith("-") or s.startswith("@"):
        return False
    # Unix absolute or home-relative
    if s.startswith("/") or s.startswith("~"):
        return True
    # Windows absolute  C:\ or C:/
    if len(s) >= 3 and s[1] == ":" and s[2] in "/\\":
        return True
    return False


def _find_credentials(config: dict) -> list[dict]:
    """Find API tokens / passwords exposed in plaintext in env or args."""
    credential_patterns = re.compile(
        r"(token|key|secret|password|passwd|pwd|api_key|access_token|auth|credential)",
        re.IGNORECASE,
    )
    found = []

    # Check env vars
    for var_name, value in config.get("env", {}).items():
        if credential_patterns.search(var_name):
            is_real = bool(value) and not value.startswith(("$", "<")) and value not in (
                "", "YOUR_TOKEN_HERE", "xxx", "REPLACE_ME",
            )
            found.append({
                "var": var_name,
                "has_real_value": is_real,
                "preview": (value[:6] + "...") if is_real and len(value) > 6 else value,
            })

    # Check args for embedded credentials in connection strings
    for arg in config.get("args", []):
        if re.search(r"://[^/@]+:[^@]+@", arg):   # proto://user:pass@host
            found.append({
                "var": "connection_string",
                "has_real_value": True,
                "preview": re.sub(r"(://[^:@]+:)[^@]+(@)", r"\1***\2", arg),
            })

    return found
