"""Tests for MCP analyzer."""

import pytest

from agentguard.mcp_analyzer import analyze_mcp


# ── helpers ───────────────────────────────────────────────────────────────────

def _parsed(servers: list) -> dict:
    return {"servers": servers, "filepath": "test.json", "raw": {}}


def _server(name, package, paths=None, creds=None):
    return {
        "name": name,
        "command": "npx",
        "args": [],
        "env": {},
        "package": package,
        "paths": paths or [],
        "exposed_credentials": creds or [],
    }


# ── basic scoring ─────────────────────────────────────────────────────────────

def test_empty_config():
    result = analyze_mcp(_parsed([]))
    assert result["score"] == 0
    assert result["level"] == "LOW"
    assert result["findings"] == []


def test_unknown_server_not_analyzed():
    parsed = _parsed([_server("my-custom-server", "my-custom-package")])
    result = analyze_mcp(parsed)
    assert "my-custom-server" in result["unknown_servers"]
    assert result["findings"] == []


def test_safe_server_no_findings():
    parsed = _parsed([
        _server("brave", "@modelcontextprotocol/server-brave-search")
    ])
    result = analyze_mcp(parsed)
    assert result["findings"] == []
    assert result["level"] == "LOW"


def test_high_risk_server_detected():
    parsed = _parsed([
        _server("filesystem", "@modelcontextprotocol/server-filesystem",
                paths=["/home/user"])
    ])
    result = analyze_mcp(parsed)
    assert result["score"] > 50
    assert result["level"] in ("HIGH", "CRITICAL")
    assert len(result["findings"]) == 1
    assert result["findings"][0]["server"] == "filesystem"


def test_credential_exposure_flagged():
    creds = [{"var": "GITHUB_TOKEN", "has_real_value": True, "preview": "ghp_ab..."}]
    parsed = _parsed([
        _server("github", "@modelcontextprotocol/server-github", creds=creds)
    ])
    result = analyze_mcp(parsed)
    assert any(r["type"] == "credential_exposure" for r in result["findings"][0]["risks"])


def test_production_db_flagged():
    parsed = _parsed([
        _server("postgres", "@modelcontextprotocol/server-postgres",
                paths=["postgresql://user:pass@prod.rds.amazonaws.com/mydb"])
    ])
    result = analyze_mcp(parsed)
    assert any(r["type"] == "production_db" for r in result["findings"][0]["risks"])


def test_scope_risk_exec_server():
    parsed = _parsed([
        _server("everything", "@modelcontextprotocol/server-everything")
    ])
    result = analyze_mcp(parsed)
    assert result["level"] == "CRITICAL"
    assert any(r["type"] == "scope_risk" for r in result["findings"][0]["risks"])


def test_findings_sorted_by_blast():
    creds = [{"var": "SLACK_TOKEN", "has_real_value": True, "preview": "xoxb-..."}]
    parsed = _parsed([
        _server("brave", "@modelcontextprotocol/server-brave-search"),
        _server("exec-server", "@modelcontextprotocol/server-everything"),
        _server("slack", "@modelcontextprotocol/server-slack", creds=creds),
    ])
    result = analyze_mcp(parsed)
    # Most dangerous finding first
    blasts = [f["max_blast"] for f in result["findings"]]
    assert blasts == sorted(blasts, reverse=True)


def test_servers_analyzed_list():
    parsed = _parsed([
        _server("brave", "@modelcontextprotocol/server-brave-search"),
        _server("unknown-one", "com.custom/unknown"),
    ])
    result = analyze_mcp(parsed)
    assert "brave" in result["servers_analyzed"]
    assert "unknown-one" not in result["servers_analyzed"]


def test_home_dir_path_risk():
    parsed = _parsed([
        _server("fs", "@modelcontextprotocol/server-filesystem",
                paths=["/home/alice"])
    ])
    result = analyze_mcp(parsed)
    path_risks = [r for r in result["findings"][0]["risks"] if r["type"] == "path_risk"]
    assert path_risks
    assert path_risks[0]["blast_weight"] == 4
