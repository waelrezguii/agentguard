"""
AgentGuard CLI entry point.

Commands:
  agentguard scan-mcp               Scan MCP config files (auto-detected)
  agentguard scan-mcp --config PATH Scan a specific MCP config file
  agentguard scan ./my_agent.py     Scan a LangChain agent file
"""

import sys
import json
import argparse

# Ensure Unicode output works on Windows (PowerShell / cmd default to cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agentguard.mcp_parser import parse_mcp_config, find_mcp_configs
from agentguard.mcp_analyzer import analyze_mcp
from agentguard.reporter import format_mcp_report

from agentguard.parser import parse_agent_file
from agentguard.analyzer import analyze
from agentguard.reporter import format_report


def main():
    parser = argparse.ArgumentParser(
        prog="agentguard",
        description="Audit the permission surface of your AI agents and MCP servers.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # ── scan-mcp ──────────────────────────────────────────────────────────────
    mcp_parser = subparsers.add_parser("scan-mcp", help="Scan MCP server configurations")
    mcp_parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to a specific MCP config file (default: auto-detect all)",
    )
    mcp_parser.add_argument(
        "--app",
        metavar="NAME",
        help="App name label for the report (e.g. 'Claude Desktop')",
    )
    mcp_parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    mcp_parser.add_argument("--json", action="store_true", help="Output results as JSON")
    mcp_parser.add_argument(
        "--fail-on",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        default=None,
        help="Exit with code 1 if risk level is at or above this threshold",
    )

    # ── scan (LangChain) ──────────────────────────────────────────────────────
    scan_parser = subparsers.add_parser("scan", help="Scan a LangChain agent file")
    scan_parser.add_argument("filepath", help="Path to the Python file containing the agent")
    scan_parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    scan_parser.add_argument("--json", action="store_true", help="Output results as JSON")
    scan_parser.add_argument(
        "--fail-on",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        default=None,
        help="Exit with code 1 if risk level is at or above this threshold",
    )

    args = parser.parse_args()

    if args.command == "scan-mcp":
        _run_scan_mcp(args)
    elif args.command == "scan":
        _run_scan(args)
    else:
        parser.print_help()
        sys.exit(0)


def _run_scan_mcp(args):
    configs_to_scan = []

    if args.config:
        configs_to_scan.append({
            "app": getattr(args, "app", None) or "Custom",
            "path": args.config,
        })
    else:
        configs_to_scan = find_mcp_configs()
        if not configs_to_scan:
            print("No MCP config files found on this machine.")
            print("Checked: Claude Desktop, Cursor, VSCode, Windsurf")
            print("Use --config PATH to specify a file manually.")
            sys.exit(0)

    worst_level = "LOW"
    levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    for config in configs_to_scan:
        try:
            parsed = parse_mcp_config(config["path"])
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

        result = analyze_mcp(parsed)

        if args.json:
            output = {k: v for k, v in result.items()}
            output["config"] = config["path"]
            output["app"] = config["app"]
            print(json.dumps(output, indent=2))
        else:
            report = format_mcp_report(
                result,
                config["path"],
                app=config["app"],
                no_color=args.no_color,
            )
            print(report)

        if levels.index(result["level"]) > levels.index(worst_level):
            worst_level = result["level"]

    if args.fail_on:
        threshold_idx = levels.index(args.fail_on)
        if levels.index(worst_level) >= threshold_idx:
            sys.exit(1)


def _run_scan(args):
    try:
        parsed = parse_agent_file(args.filepath)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    result = analyze(parsed)

    if args.json:
        output = {k: v for k, v in result.items() if k != "raw_source"}
        print(json.dumps(output, indent=2))
    else:
        report = format_report(result, args.filepath, no_color=args.no_color)
        print(report)

    if args.fail_on:
        levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        threshold_idx = levels.index(args.fail_on)
        result_idx = levels.index(result["level"])
        if result_idx >= threshold_idx:
            sys.exit(1)


if __name__ == "__main__":
    main()
