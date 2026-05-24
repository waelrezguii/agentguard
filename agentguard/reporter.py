"""
Reporter module.
Formats the analysis result into clean, readable CLI output.
"""

LEVEL_COLORS = {
    "LOW": "\033[92m",      # green
    "MEDIUM": "\033[93m",   # yellow
    "HIGH": "\033[91m",     # red
    "CRITICAL": "\033[95m", # magenta
}
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def format_report(result: dict, filepath: str, no_color: bool = False) -> str:
    """Format analysis result into a human-readable CLI report."""

    def color(text, code):
        if no_color:
            return text
        return f"{code}{text}{RESET}"

    def bold(text):
        if no_color:
            return text
        return f"{BOLD}{text}{RESET}"

    def dim(text):
        if no_color:
            return text
        return f"{DIM}{text}{RESET}"

    lines = []
    lines.append("")
    lines.append(bold("AgentGuard") + " — AI Agent Permission Scanner")
    lines.append(dim(f"File: {filepath}"))
    lines.append("")

    # Score line
    score = result["score"]
    level = result["level"]
    level_color = LEVEL_COLORS.get(level, "")
    score_display = color(f"{score}/100 — {level}", level_color)
    lines.append(bold(f"Risk Score: {score_display}") if not no_color else f"Risk Score: {score}/100 — {level}")
    lines.append("")

    # Task context
    if result["task_description"]:
        lines.append(dim(f"Task: \"{result['task_description'][:120]}\""))
        lines.append(dim(f"Required actions inferred: {', '.join(result['required_actions'])}"))
        lines.append("")

    # Findings
    findings = result["findings"]
    if not findings:
        lines.append(color("✓ No over-permissioned tools found.", "\033[92m"))
    else:
        count = len(findings)
        lines.append(bold(f"{count} over-permissioned tool{'s' if count > 1 else ''} found:"))
        lines.append("")

        for finding in findings:
            tool_name = finding["tool"]
            excess = finding["excess_scopes"]

            # Tool header
            lines.append(f"  {bold(tool_name)}")
            lines.append(dim(f"  {finding['description']}"))

            for scope_info in excess:
                scope = scope_info["scope"]
                weight = scope_info["blast_weight"]
                blast_label = _blast_label(weight)
                blast_colored = color(blast_label, _blast_color(weight))
                lines.append(f"    → {scope} scope   {blast_colored if not no_color else blast_label}")

            lines.append(dim(f"  Fix: {finding['safe_alternative']}"))
            lines.append("")

    # Unknown tools
    if result["unknown_tools"]:
        lines.append(dim(f"Unknown tools (not in database): {', '.join(result['unknown_tools'])}"))
        lines.append(dim("  Submit a PR to add them: github.com/agentguard/agentguard"))
        lines.append("")

    # Remediation summary
    if findings:
        lines.append(bold("Remediation:"))
        for i, finding in enumerate(findings, 1):
            lines.append(f"  {i}. {finding['safe_alternative']}")
        lines.append("")

    # Footer
    if result["score"] == 0:
        lines.append(color("✓ This agent follows least privilege. Good work.", "\033[92m"))
    elif result["score"] <= 25:
        lines.append(color("Minor issues. Low priority — review before next deploy.", "\033[92m"))
    elif result["score"] <= 50:
        lines.append(color("Notable excess permissions. Review before deploying to production.", "\033[93m"))
    elif result["score"] <= 75:
        lines.append(color("Significant over-permission. Fix before shipping.", "\033[91m"))
    else:
        lines.append(color("CRITICAL: This agent could cause irreversible damage if compromised or manipulated.", "\033[95m"))

    lines.append("")
    return "\n".join(lines)


def format_mcp_report(result: dict, filepath: str, app: str = None, no_color: bool = False) -> str:
    """Format MCP scan result into a human-readable CLI report."""

    def color(text, code):
        if no_color:
            return text
        return f"{code}{text}{RESET}"

    def bold(text):
        if no_color:
            return text
        return f"{BOLD}{text}{RESET}"

    def dim(text):
        if no_color:
            return text
        return f"{DIM}{text}{RESET}"

    lines = []
    lines.append("")
    label = app or "MCP Config"
    lines.append(bold("AgentGuard") + f" — MCP Security Scanner  [{label}]")
    lines.append(dim(f"Config: {filepath}"))
    lines.append("")

    # Score line
    score = result["score"]
    level = result["level"]
    level_color = LEVEL_COLORS.get(level, "")
    if no_color:
        lines.append(f"Risk Score: {score}/100 — {level}")
    else:
        lines.append(f"{BOLD}Risk Score: {color(f'{score}/100 — {level}', level_color)}{RESET}")
    lines.append("")

    # Servers analyzed summary
    analyzed = result["servers_analyzed"]
    unknown = result["unknown_servers"]
    summary_parts = []
    if analyzed:
        summary_parts.append(f"{len(analyzed)} server{'s' if len(analyzed) != 1 else ''} analyzed")
    if unknown:
        summary_parts.append(f"{len(unknown)} unknown")
    if summary_parts:
        lines.append(dim("Servers: " + " · ".join(summary_parts)))
        lines.append("")

    # Findings
    findings = result["findings"]
    if not findings:
        lines.append(color("✓ No high-risk MCP server configurations found.", "\033[92m"))
    else:
        count = len(findings)
        lines.append(bold(f"{count} risky server{'s' if count > 1 else ''} found:"))
        lines.append("")

        for finding in findings:
            max_blast = finding["max_blast"]
            blast_color_code = _blast_color(max_blast)

            # Server header
            sname = finding["server"]
            server_label = color(f"● {sname}", blast_color_code)
            lines.append(f"  {server_label if not no_color else ('● ' + sname)}")
            lines.append(dim(f"  {finding['description']}"))
            lines.append(dim(f"  Package: {finding['package']}"))
            lines.append("")

            for risk in finding["risks"]:
                rtype = risk["type"]
                weight = risk["blast_weight"]
                blast_label = _blast_label(weight)
                blast_colored = color(blast_label, _blast_color(weight))
                flag = color("⚠", _blast_color(weight))

                detail = risk["detail"]
                lines.append(
                    f"    {flag if not no_color else '⚠'}  {detail}"
                )
                lines.append(
                    dim(f"       Blast radius: {blast_colored if not no_color else blast_label}")
                )
                lines.append("")

            lines.append(dim(f"  Fix: {finding['safe_alternative']}"))
            lines.append("")

    # Unknown servers
    if unknown:
        lines.append(dim(f"Unknown servers (not in database): {', '.join(unknown)}"))
        lines.append(dim("  These may be custom or private servers — review their permissions manually."))
        lines.append(dim("  Submit a PR to add them: github.com/waelrezguii/agentguard"))
        lines.append("")

    # Footer
    if score == 0:
        lines.append(color("✓ Your MCP setup looks safe. Good configuration.", "\033[92m"))
    elif score <= 25:
        lines.append(color("Minor issues. Review before sharing this config.", "\033[92m"))
    elif score <= 50:
        lines.append(color("Moderate risk. Consider restricting permissions.", "\033[93m"))
    elif score <= 75:
        lines.append(color("High risk. Fix before using in production or with untrusted prompts.", "\033[91m"))
    else:
        lines.append(color(
            "CRITICAL: A prompt injection attack could cause irreversible damage with this configuration.",
            "\033[95m"
        ))

    lines.append("")
    return "\n".join(lines)


def _blast_label(weight: int) -> str:
    labels = {1: "low blast radius", 2: "medium blast radius", 3: "high blast radius", 4: "critical blast radius"}
    return labels.get(weight, "unknown")


def _blast_color(weight: int) -> str:
    colors = {1: "\033[92m", 2: "\033[93m", 3: "\033[91m", 4: "\033[95m"}
    return colors.get(weight, "")
