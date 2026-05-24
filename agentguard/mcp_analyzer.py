"""
MCP Analyzer.
Scores MCP server configurations for over-permission and security risks.
"""

from agentguard.mcp_tools_db import (
    MCP_SERVER_DB,
    DANGEROUS_PATH_PATTERNS,
    PRODUCTION_INDICATORS,
)


def analyze_mcp(parsed: dict) -> dict:
    """
    Analyze an MCP server configuration.

    Returns:
        {
            score: int (0-100),
            level: str (LOW / MEDIUM / HIGH / CRITICAL),
            findings: list of per-server finding dicts,
            unknown_servers: list of server names not in the database,
            servers_analyzed: list of server names that were analyzed,
        }
    """
    servers = parsed["servers"]
    findings = []
    unknown_servers = []
    server_risk_levels = []

    for server in servers:
        db_entry = _lookup(server["package"])
        if not db_entry:
            unknown_servers.append(server["name"])
            continue

        risks = []

        # 1. Path-based risk (filesystem servers)
        if db_entry.get("path_sensitive") and server["paths"]:
            path_risk = _assess_paths(server["paths"])
            if path_risk:
                risks.append(path_risk)

        # 2. Credential exposure in plaintext
        for cred in server["exposed_credentials"]:
            if cred["has_real_value"]:
                risks.append({
                    "type": "credential_exposure",
                    "blast_weight": 3,
                    "detail": f"{cred['var']} is exposed in plaintext in your config file ({cred['preview']})",
                })

        # 3. Production database detection
        if db_entry.get("connection_string_sensitive"):
            for path in server["paths"]:
                if any(ind in path.lower() for ind in PRODUCTION_INDICATORS):
                    risks.append({
                        "type": "production_db",
                        "blast_weight": 4,
                        "detail": "Connection string points to a production database",
                    })

        # 4. Inherent capability risk (exec/admin/delete scopes)
        max_scope_blast = max(db_entry["blast_radius"].values())
        if max_scope_blast >= 3:
            worst_scope = max(db_entry["blast_radius"], key=db_entry["blast_radius"].get)
            risks.append({
                "type": "scope_risk",
                "blast_weight": max_scope_blast,
                "detail": f"Grants {worst_scope} access — {_blast_description(max_scope_blast)}",
            })

        if not risks:
            # Safe server — still record it but with no issues
            server_risk_levels.append(1)
            continue

        max_blast = max(r["blast_weight"] for r in risks)
        server_risk_levels.append(max_blast)

        findings.append({
            "server": server["name"],
            "package": server["package"],
            "description": db_entry["description"],
            "risks": risks,
            "safe_alternative": db_entry["safe_alternative"],
            "max_blast": max_blast,
        })

    # Sort findings: most dangerous first
    findings.sort(key=lambda f: f["max_blast"], reverse=True)

    score = _calculate_score(server_risk_levels)
    level = _score_to_level(score)

    return {
        "score": score,
        "level": level,
        "findings": findings,
        "unknown_servers": unknown_servers,
        "servers_analyzed": [
            s["name"] for s in servers if _lookup(s["package"]) is not None
        ],
    }


# ── helpers ───────────────────────────────────────────────────────────────────

def _lookup(package: str) -> dict | None:
    if package in MCP_SERVER_DB:
        return MCP_SERVER_DB[package]
    for key in MCP_SERVER_DB:
        if key in package or package in key:
            return MCP_SERVER_DB[key]
    return None


def _assess_paths(paths: list[str]) -> dict | None:
    for path in paths:
        for pattern, kind in DANGEROUS_PATH_PATTERNS:
            p = path.replace("\\", "/")
            if p == pattern.rstrip("/") or p.startswith(pattern):
                if kind == "home_dir":
                    return {
                        "type": "path_risk",
                        "blast_weight": 4,
                        "detail": (
                            f"Path '{path}' exposes your entire home directory — "
                            "includes .ssh keys, .aws credentials, .env files, and all your code"
                        ),
                    }
                if kind == "root":
                    return {
                        "type": "path_risk",
                        "blast_weight": 4,
                        "detail": (
                            f"Path '{path}' gives access to your entire drive — "
                            "the AI can read and write anything on your system"
                        ),
                    }
    return None


def _calculate_score(server_risk_levels: list[int]) -> int:
    if not server_risk_levels:
        return 0
    max_risk = max(server_risk_levels)
    high_risk_count = sum(1 for r in server_risk_levels if r >= 3)
    # base: max_risk * 20 → maps 4 to 80, 3 to 60, 2 to 40, 1 to 20
    # bonus: each additional high-risk server adds up to 20 more
    base = max_risk * 20
    bonus = min(20, high_risk_count * 5)
    return min(100, base + bonus)


def _score_to_level(score: int) -> str:
    if score <= 25:
        return "LOW"
    elif score <= 50:
        return "MEDIUM"
    elif score <= 75:
        return "HIGH"
    else:
        return "CRITICAL"


def _blast_description(weight: int) -> str:
    return {
        1: "read-only, low impact",
        2: "can write data, reversible",
        3: "can delete or send messages, hard to reverse",
        4: "can execute code or modify critical systems",
    }.get(weight, "unknown impact")
