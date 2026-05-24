"""
AgentGuard CLI entry point.
Usage: agentguard scan ./my_agent.py
"""

import sys
import argparse
from agentguard.parser import parse_agent_file
from agentguard.analyzer import analyze
from agentguard.reporter import format_report


def main():
    parser = argparse.ArgumentParser(
        prog="agentguard",
        description="Audit the permission surface of your LangChain agents.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan a LangChain agent file")
    scan_parser.add_argument("filepath", help="Path to the Python file containing the agent")
    scan_parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    scan_parser.add_argument("--json", action="store_true", help="Output results as JSON")
    scan_parser.add_argument(
        "--fail-on",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        default=None,
        help="Exit with code 1 if risk level is at or above this threshold (for CI/CD)",
    )

    args = parser.parse_args()

    if args.command == "scan":
        _run_scan(args)
    else:
        parser.print_help()
        sys.exit(0)


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
        import json
        # Remove raw source from JSON output
        output = {k: v for k, v in result.items() if k != "raw_source"}
        print(json.dumps(output, indent=2))
    else:
        report = format_report(result, args.filepath, no_color=args.no_color)
        print(report)

    # Exit code for CI/CD integration
    if args.fail_on:
        levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        threshold_idx = levels.index(args.fail_on)
        result_idx = levels.index(result["level"])
        if result_idx >= threshold_idx:
            sys.exit(1)


if __name__ == "__main__":
    main()
