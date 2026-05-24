import pytest
from agentguard.analyzer import analyze


def _parsed(tools, task=""):
    return {"tools": tools, "task_description": task}


def test_three_overpermissioned_tools_critical():
    """GitHubTool + SlackTool + SQLDatabaseTool on a read-only summarizer → CRITICAL."""
    result = analyze(_parsed(
        ["GitHubTool", "SlackTool", "SQLDatabaseTool"],
        "You are an assistant that summarizes pull requests.",
    ))
    assert result["level"] == "CRITICAL"
    assert result["score"] > 75
    assert len(result["findings"]) == 3


def test_read_only_task_low_score():
    """NotionTool on a task that needs both read+write → all scopes used → score 0."""
    result = analyze(_parsed(
        ["NotionTool"],
        "read and write notes to keep knowledge organized",
    ))
    assert result["level"] == "LOW"
    assert result["score"] <= 25


def test_unknown_tools_reported():
    result = analyze(_parsed(["MyCustomTool", "AnotherRandomTool"], "do something"))
    assert "MyCustomTool" in result["unknown_tools"]
    assert "AnotherRandomTool" in result["unknown_tools"]
    assert result["findings"] == []


def test_no_tools_scores_zero():
    result = analyze(_parsed([], "read emails and summarize them"))
    assert result["score"] == 0
    assert result["level"] == "LOW"


def test_shell_tool_exec_on_read_task_scores_critical():
    """ShellTool carrying exec scope on a pure-read task should be flagged as CRITICAL."""
    result = analyze(_parsed(["ShellTool"], "summarize the latest news"))
    assert result["level"] == "CRITICAL"
    assert any(f["tool"] == "ShellTool" for f in result["findings"])


def test_findings_sorted_by_blast_radius():
    """Most dangerous findings appear first."""
    result = analyze(_parsed(
        ["NotionTool", "ShellTool"],
        "read documents",
    ))
    if len(result["findings"]) >= 2:
        first_max = result["findings"][0]["max_blast"]
        second_max = result["findings"][1]["max_blast"]
        assert first_max >= second_max


def test_result_keys_present():
    result = analyze(_parsed(["GitHubTool"], "read repos"))
    for key in ("score", "level", "findings", "unknown_tools", "tools_analyzed", "required_actions"):
        assert key in result


def test_mixed_known_unknown_tools():
    result = analyze(_parsed(["GitHubTool", "WeirdCustomTool"], "read repos"))
    assert "WeirdCustomTool" in result["unknown_tools"]
    assert "GitHubTool" in result["tools_analyzed"]
