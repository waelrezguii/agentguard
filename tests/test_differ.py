"""Tests for the agent differ."""

import pytest
from agentguard.differ import diff_agents


# ── helpers ───────────────────────────────────────────────────────────────────

def _result(score, level, tools):
    """Build a minimal analyze() result."""
    findings = []
    for tool in tools:
        findings.append({
            "tool": tool,
            "description": f"{tool} description",
            "excess_scopes": [{"scope": "delete", "blast_weight": 3, "action": "delete"}],
            "safe_alternative": f"Restrict {tool}",
            "max_blast": 3,
        })
    return {
        "score": score,
        "level": level,
        "findings": findings,
        "unknown_tools": [],
        "task_description": "",
        "required_actions": [],
    }


# ── no change ─────────────────────────────────────────────────────────────────

def test_no_change():
    base = _result(60, "HIGH", ["GitHubTool"])
    head = _result(60, "HIGH", ["GitHubTool"])
    diff = diff_agents(base, head)
    assert diff["changed"] is False
    assert diff["elevated"] is False
    assert diff["tools_added"] == []
    assert diff["tools_removed"] == []


# ── tool added ────────────────────────────────────────────────────────────────

def test_tool_added():
    base = _result(40, "MEDIUM", ["GitHubTool"])
    head = _result(80, "CRITICAL", ["GitHubTool", "ShellTool"])
    diff = diff_agents(base, head)
    assert diff["changed"] is True
    assert diff["elevated"] is True
    added_names = [f["tool"] for f in diff["tools_added"]]
    assert "ShellTool" in added_names
    assert "GitHubTool" not in added_names


# ── tool removed ──────────────────────────────────────────────────────────────

def test_tool_removed():
    base = _result(80, "CRITICAL", ["GitHubTool", "ShellTool"])
    head = _result(40, "MEDIUM", ["GitHubTool"])
    diff = diff_agents(base, head)
    assert diff["changed"] is True
    assert diff["elevated"] is False
    assert "ShellTool" in diff["tools_removed"]


# ── score change without level change ────────────────────────────────────────

def test_score_change_marks_changed():
    base = _result(50, "MEDIUM", ["GitHubTool"])
    head = _result(60, "MEDIUM", ["GitHubTool", "SlackTool"])
    diff = diff_agents(base, head)
    assert diff["changed"] is True


# ── clean to risky ────────────────────────────────────────────────────────────

def test_new_file_from_zero():
    base = _result(0, "LOW", [])
    head = _result(80, "CRITICAL", ["ShellTool"])
    diff = diff_agents(base, head)
    assert diff["elevated"] is True
    assert len(diff["tools_added"]) == 1
    assert diff["tools_added"][0]["tool"] == "ShellTool"


# ── all tools removed ─────────────────────────────────────────────────────────

def test_all_tools_removed():
    base = _result(80, "CRITICAL", ["ShellTool", "GitHubTool"])
    head = _result(0, "LOW", [])
    diff = diff_agents(base, head)
    assert diff["changed"] is True
    assert diff["elevated"] is False
    assert set(diff["tools_removed"]) == {"ShellTool", "GitHubTool"}
    assert diff["tools_added"] == []


# ── field presence ────────────────────────────────────────────────────────────

def test_diff_result_keys():
    base = _result(40, "MEDIUM", ["GitHubTool"])
    head = _result(80, "CRITICAL", ["GitHubTool", "ShellTool"])
    diff = diff_agents(base, head)
    for key in ("tools_added", "tools_removed", "score_before", "score_after",
                "level_before", "level_after", "changed", "elevated"):
        assert key in diff
