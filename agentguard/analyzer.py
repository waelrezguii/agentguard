"""
Analyzer module.
Takes parsed agent data (tools + task description) and produces:
  - A risk score (0-100)
  - A list of findings (over-permissioned tools)
  - A remediation list
"""

from agentguard.tools_db import TOOL_PERMISSIONS, TASK_KEYWORDS, SCOPE_TO_ACTION


def analyze(parsed: dict) -> dict:
    """
    Core analysis function.
    Returns a result dict with: score, level, findings, unknown_tools
    """
    tools = parsed["tools"]
    task_description = parsed["task_description"]

    required_actions = _infer_required_actions(task_description)
    findings = []
    unknown_tools = []
    total_excess_weight = 0
    max_possible_weight = 0

    for tool_name in tools:
        if tool_name not in TOOL_PERMISSIONS:
            unknown_tools.append(tool_name)
            continue

        tool_data = TOOL_PERMISSIONS[tool_name]
        excess_scopes = []

        for scope in tool_data["scopes"]:
            canonical_action = SCOPE_TO_ACTION.get(scope, scope)
            blast_weight = tool_data["blast_radius"][scope]
            max_possible_weight += blast_weight

            # Check if this scope is needed by the task
            if canonical_action not in required_actions:
                excess_scopes.append({
                    "scope": scope,
                    "blast_weight": blast_weight,
                    "action": canonical_action,
                })
                total_excess_weight += blast_weight

        if excess_scopes:
            findings.append({
                "tool": tool_name,
                "description": tool_data["description"],
                "excess_scopes": excess_scopes,
                "safe_alternative": tool_data["safe_alternative"],
                "max_blast": max(s["blast_weight"] for s in excess_scopes),
            })

    # Sort findings by max blast radius descending (most dangerous first)
    findings.sort(key=lambda f: f["max_blast"], reverse=True)

    # Score calculation
    # Base: ratio of excess weight to max possible weight
    if max_possible_weight == 0:
        raw_score = 0
    else:
        raw_score = total_excess_weight / max_possible_weight

    # Apply blast radius amplifier: if any exec/admin scope is excess, boost score
    has_critical_excess = any(
        scope["blast_weight"] >= 4
        for finding in findings
        for scope in finding["excess_scopes"]
    )
    if has_critical_excess:
        raw_score = min(1.0, raw_score * 1.4)

    score = round(raw_score * 100)
    level = _score_to_level(score)

    return {
        "score": score,
        "level": level,
        "findings": findings,
        "unknown_tools": unknown_tools,
        "tools_analyzed": [t for t in tools if t in TOOL_PERMISSIONS],
        "task_description": task_description,
        "required_actions": sorted(list(required_actions)),
    }


def _infer_required_actions(task_description: str) -> set:
    """
    Infer which action categories are required from the task description.
    If no task description exists, conservatively assume read only.
    """
    if not task_description:
        return {"read"}

    text = task_description.lower()
    required = set()

    for action, keywords in TASK_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            required.add(action)

    # Read is always required if anything else is required
    # (you can't write without reading)
    if required:
        required.add("read")
    else:
        required.add("read")

    return required


def _score_to_level(score: int) -> str:
    if score <= 25:
        return "LOW"
    elif score <= 50:
        return "MEDIUM"
    elif score <= 75:
        return "HIGH"
    else:
        return "CRITICAL"
