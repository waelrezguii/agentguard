#!/usr/bin/env python3
"""
AgentGuard GitHub Action entrypoint.

For each Python file changed in the PR that AgentGuard can parse as an agent:
  1. Get the base version (from the target branch)
  2. Get the head version (from the PR branch)
  3. Diff them
  4. Post a PR comment if permissions changed
"""

import os
import sys
import json
import subprocess
import tempfile
import urllib.request
import urllib.error


GITHUB_TOKEN    = os.environ["GITHUB_TOKEN"]
GITHUB_REPO     = os.environ["GITHUB_REPOSITORY"]
PR_NUMBER       = os.environ.get("PR_NUMBER", "")
BASE_REF        = os.environ.get("BASE_REF", "main")
FAIL_ON_ESCALATION = os.environ.get("FAIL_ON_ESCALATION", "false").lower() == "true"


def gh_api(method: str, path: str, body: dict = None):
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"GitHub API error {e.code}: {e.read().decode()}")
        return None


def get_changed_python_files() -> list[str]:
    """Get list of .py files changed in this PR."""
    result = subprocess.run(
        ["git", "diff", "--name-only", f"origin/{BASE_REF}...HEAD"],
        capture_output=True, text=True
    )
    files = [f for f in result.stdout.strip().splitlines() if f.endswith(".py")]
    return files


def get_base_content(filepath: str) -> str | None:
    """Get file content from the base branch."""
    result = subprocess.run(
        ["git", "show", f"origin/{BASE_REF}:{filepath}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None  # File is new in this PR
    return result.stdout


def try_diff_file(filepath: str) -> dict | None:
    """
    Attempt to diff a file between base and head.
    Returns diff dict or None if file isn't an agent file.
    """
    from agentguard.differ import diff_files
    from agentguard.parser import parse_agent_file
    from agentguard.analyzer import analyze

    # Try to parse the head version first — if it's not an agent file, skip
    try:
        head_parsed = parse_agent_file(filepath)
    except (ValueError, FileNotFoundError):
        return None

    head_result = analyze(head_parsed)

    # Check if there's a base version
    base_content = get_base_content(filepath)
    if base_content is None:
        # New file — diff against empty agent (score 0, no findings)
        base_result = {"score": 0, "level": "LOW", "findings": [],
                       "unknown_tools": [], "task_description": "", "required_actions": []}
    else:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(base_content)
            base_path = f.name
        try:
            base_parsed = parse_agent_file(base_path)
            base_result = analyze(base_parsed)
        except (ValueError, FileNotFoundError):
            base_result = {"score": 0, "level": "LOW", "findings": [],
                           "unknown_tools": [], "task_description": "", "required_actions": []}
        finally:
            os.unlink(base_path)

    from agentguard.differ import diff_agents
    return diff_agents(base_result, head_result)


def post_pr_comment(body: str):
    if not PR_NUMBER:
        print("No PR number found, skipping comment.")
        return
    gh_api("POST", f"/repos/{GITHUB_REPO}/issues/{PR_NUMBER}/comments", {"body": body})


def delete_existing_agentguard_comments():
    """Delete previous AgentGuard comments to avoid spam."""
    if not PR_NUMBER:
        return
    comments = gh_api("GET", f"/repos/{GITHUB_REPO}/issues/{PR_NUMBER}/comments")
    if not comments:
        return
    for comment in comments:
        if "AgentGuard" in comment.get("body", ""):
            gh_api("DELETE", f"/repos/{GITHUB_REPO}/issues/comments/{comment['id']}")


def main():
    from agentguard.reporter import format_diff_comment

    changed_files = get_changed_python_files()
    if not changed_files:
        print("No Python files changed.")
        return

    print(f"Scanning {len(changed_files)} changed Python file(s)...")

    results = []
    any_escalated = False

    for filepath in changed_files:
        if not os.path.exists(filepath):
            continue  # Deleted file

        print(f"  Checking {filepath}...")
        diff = try_diff_file(filepath)

        if diff is None:
            print(f"    → Not an agent file, skipping.")
            continue

        if diff["changed"] or diff["elevated"]:
            results.append((filepath, diff))
            if diff["elevated"]:
                any_escalated = True
            print(f"    → Changes detected: {diff['level_before']} → {diff['level_after']}")
        else:
            print(f"    → No permission changes.")

    if results:
        delete_existing_agentguard_comments()
        for filepath, diff in results:
            comment = format_diff_comment(diff, filepath)
            post_pr_comment(comment)
            print(f"  Posted comment for {filepath}")

    if FAIL_ON_ESCALATION and any_escalated:
        print("Risk escalation detected. Failing build.")
        sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
