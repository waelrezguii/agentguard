import json
import pytest
from agentguard.analyzer import analyze
from agentguard.reporter import format_report


def _critical_result():
    return analyze({
        "tools": ["GitHubTool", "SlackTool", "SQLDatabaseTool"],
        "task_description": "You summarize pull requests.",
    })


def _clean_result():
    return analyze({
        "tools": ["NotionTool"],
        "task_description": "read and write notes",
    })


def test_format_report_returns_string():
    report = format_report(_critical_result(), "agent.py")
    assert isinstance(report, str)


def test_report_contains_agentguard_header():
    report = format_report(_critical_result(), "agent.py")
    assert "AgentGuard" in report


def test_report_shows_critical_level():
    report = format_report(_critical_result(), "agent.py", no_color=True)
    assert "CRITICAL" in report


def test_no_color_strips_ansi():
    report = format_report(_critical_result(), "agent.py", no_color=True)
    assert "\033[" not in report


def test_colored_output_contains_ansi():
    report = format_report(_critical_result(), "agent.py", no_color=False)
    assert "\033[" in report


def test_clean_agent_no_findings_message():
    report = format_report(_clean_result(), "agent.py", no_color=True)
    assert "No over-permissioned" in report or "score" in report.lower()


def test_json_output_is_valid_and_parseable():
    result = _critical_result()
    output = {k: v for k, v in result.items() if k != "raw_source"}
    json_str = json.dumps(output, indent=2)
    parsed = json.loads(json_str)
    assert parsed["level"] == "CRITICAL"
    assert isinstance(parsed["findings"], list)
    assert isinstance(parsed["score"], int)


def test_json_findings_contain_expected_fields():
    result = _critical_result()
    output = {k: v for k, v in result.items() if k != "raw_source"}
    parsed = json.loads(json.dumps(output))
    for finding in parsed["findings"]:
        assert "tool" in finding
        assert "excess_scopes" in finding
        assert "safe_alternative" in finding


def test_report_lists_remediation_steps():
    report = format_report(_critical_result(), "agent.py", no_color=True)
    assert "Remediation" in report


def test_report_includes_filepath():
    report = format_report(_critical_result(), "my_agent.py", no_color=True)
    assert "my_agent.py" in report
