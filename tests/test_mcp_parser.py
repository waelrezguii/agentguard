"""Tests for MCP config parser."""

import json
import pytest
from pathlib import Path

from agentguard.mcp_parser import parse_mcp_config, find_mcp_configs


# ── fixtures ──────────────────────────────────────────────────────────────────

def _write_config(tmp_path: Path, data: dict) -> str:
    p = tmp_path / "mcp.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


MINIMAL_CONFIG = {
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"],
            "env": {},
        }
    }
}


# ── parse_mcp_config ──────────────────────────────────────────────────────────

def test_parse_basic(tmp_path):
    path = _write_config(tmp_path, MINIMAL_CONFIG)
    result = parse_mcp_config(path)
    assert result["filepath"].endswith("mcp.json")
    assert len(result["servers"]) == 1
    server = result["servers"][0]
    assert server["name"] == "filesystem"
    assert server["package"] == "@modelcontextprotocol/server-filesystem"


def test_parse_path_extracted(tmp_path):
    path = _write_config(tmp_path, MINIMAL_CONFIG)
    result = parse_mcp_config(path)
    assert "/home/user/projects" in result["servers"][0]["paths"]


def test_parse_credential_in_env(tmp_path):
    config = {
        "mcpServers": {
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": "ghp_realtoken123456"},
            }
        }
    }
    path = _write_config(tmp_path, config)
    result = parse_mcp_config(path)
    creds = result["servers"][0]["exposed_credentials"]
    assert len(creds) == 1
    assert creds[0]["var"] == "GITHUB_TOKEN"
    assert creds[0]["has_real_value"] is True


def test_parse_placeholder_credential_not_flagged(tmp_path):
    config = {
        "mcpServers": {
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": "$GITHUB_TOKEN"},
            }
        }
    }
    path = _write_config(tmp_path, config)
    result = parse_mcp_config(path)
    creds = result["servers"][0]["exposed_credentials"]
    assert not any(c["has_real_value"] for c in creds)


def test_parse_connection_string_credential(tmp_path):
    config = {
        "mcpServers": {
            "postgres": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://admin:s3cret@localhost/mydb"],
                "env": {},
            }
        }
    }
    path = _write_config(tmp_path, config)
    result = parse_mcp_config(path)
    creds = result["servers"][0]["exposed_credentials"]
    assert any(c["var"] == "connection_string" for c in creds)


def test_parse_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_mcp_config("/nonexistent/path/mcp.json")


def test_parse_invalid_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        parse_mcp_config(str(p))


def test_parse_empty_mcp_servers(tmp_path):
    path = _write_config(tmp_path, {"mcpServers": {}})
    result = parse_mcp_config(path)
    assert result["servers"] == []


def test_infer_package_uvx(tmp_path):
    config = {
        "mcpServers": {
            "memory": {
                "command": "uvx",
                "args": ["mcp-server-memory"],
                "env": {},
            }
        }
    }
    path = _write_config(tmp_path, config)
    result = parse_mcp_config(path)
    assert result["servers"][0]["package"] == "mcp-server-memory"


def test_infer_package_python_m(tmp_path):
    config = {
        "mcpServers": {
            "custom": {
                "command": "python",
                "args": ["-m", "my_mcp_server"],
                "env": {},
            }
        }
    }
    path = _write_config(tmp_path, config)
    result = parse_mcp_config(path)
    assert result["servers"][0]["package"] == "my-mcp-server"


def test_windows_path_extracted(tmp_path):
    config = {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\test\\projects"],
                "env": {},
            }
        }
    }
    path = _write_config(tmp_path, config)
    result = parse_mcp_config(path)
    assert "C:\\Users\\test\\projects" in result["servers"][0]["paths"]
