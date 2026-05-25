"""
Agent Differ.
Compares two agent analysis results and surfaces permission changes.
"""

from agentguard.parser import parse_agent_file
from agentguard.analyzer import analyze


def diff_agents(base_result: dict, head_result: dict) -> dict:
    """
    Compare two agent analysis results.

    Returns:
        {
            tools_added:    list of finding dicts (new tools with risks)
            tools_removed:  list of tool name strings
            score_before:   int
            score_after:    int
            level_before:   str
            level_after:    str
            changed:        bool
            elevated:       bool  (risk went up)
        }
    """
    base_tools = {f["tool"]: f for f in base_result["findings"]}
    head_tools = {f["tool"]: f for f in head_result["findings"]}

    added_names   = set(head_tools) - set(base_tools)
    removed_names = set(base_tools) - set(head_tools)

    tools_added   = [head_tools[t] for t in added_names]
    tools_removed = list(removed_names)

    # Sort added tools by max_blast descending
    tools_added.sort(key=lambda f: f["max_blast"], reverse=True)

    score_before = base_result["score"]
    score_after  = head_result["score"]
    level_before = base_result["level"]
    level_after  = head_result["level"]

    levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    elevated = levels.index(level_after) > levels.index(level_before)
    changed  = bool(added_names or removed_names or score_before != score_after)

    return {
        "tools_added":    tools_added,
        "tools_removed":  tools_removed,
        "score_before":   score_before,
        "score_after":    score_after,
        "level_before":   level_before,
        "level_after":    level_after,
        "changed":        changed,
        "elevated":       elevated,
    }


def diff_files(base_path: str, head_path: str) -> dict:
    """Parse and analyze two agent files, then diff them."""
    base_result = analyze(parse_agent_file(base_path))
    head_result = analyze(parse_agent_file(head_path))
    return diff_agents(base_result, head_result)
