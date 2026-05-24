import pytest
from agentguard.parser import parse_agent_file


def _write_agent(tmp_path, code, filename="agent.py"):
    f = tmp_path / filename
    f.write_text(code)
    return str(f)


def test_extracts_tools_from_class_references(tmp_path):
    code = """
from langchain.agents import initialize_agent
agent = initialize_agent(
    tools=[GitHubTool, SlackTool, SQLDatabaseTool],
    llm=None,
    agent_kwargs={"system_message": "You summarize pull requests."}
)
"""
    result = parse_agent_file(_write_agent(tmp_path, code))
    assert set(result["tools"]) == {"GitHubTool", "SlackTool", "SQLDatabaseTool"}


def test_extracts_tools_from_instantiated_calls(tmp_path):
    code = """
agent = initialize_agent(
    tools=[GmailTool(), ShellTool()],
    llm=None,
)
"""
    result = parse_agent_file(_write_agent(tmp_path, code))
    assert "GmailTool" in result["tools"]
    assert "ShellTool" in result["tools"]


def test_extracts_task_description(tmp_path):
    code = """
agent = initialize_agent(
    tools=[],
    llm=None,
    agent_kwargs={"system_message": "read only summarizer"}
)
"""
    result = parse_agent_file(_write_agent(tmp_path, code))
    assert "read only summarizer" in result["task_description"]


def test_file_not_found_raises():
    with pytest.raises(FileNotFoundError):
        parse_agent_file("/nonexistent/path/agent.py")


def test_non_python_file_raises(tmp_path):
    f = tmp_path / "agent.txt"
    f.write_text("not python")
    with pytest.raises(ValueError, match="Expected a Python file"):
        parse_agent_file(str(f))


def test_result_has_required_keys(tmp_path):
    code = "agent = None"
    result = parse_agent_file(_write_agent(tmp_path, code))
    assert "tools" in result
    assert "task_description" in result
    assert "raw_source" in result
    assert "filepath" in result


def test_no_duplicate_tools(tmp_path):
    code = "agent = initialize_agent(tools=[GitHubTool, GitHubTool], llm=None)"
    result = parse_agent_file(_write_agent(tmp_path, code))
    assert result["tools"].count("GitHubTool") == 1
