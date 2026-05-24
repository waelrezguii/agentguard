"""
Parser module.
Reads a Python file containing a LangChain agent definition and extracts:
  - The list of tools passed to the agent
  - The agent's task description (system_message or description)
"""

import ast
import re
from pathlib import Path


def parse_agent_file(filepath: str) -> dict:
    """
    Parse a LangChain agent file and extract tools and task description.
    Returns a dict with keys: tools (list[str]), task_description (str), raw_source (str)
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    if not path.suffix == ".py":
        raise ValueError(f"Expected a Python file, got: {filepath}")

    source = path.read_text()

    tools = _extract_tools(source)
    task_description = _extract_task_description(source)

    return {
        "tools": tools,
        "task_description": task_description,
        "raw_source": source,
        "filepath": str(path.resolve()),
    }


def _extract_tools(source: str) -> list[str]:
    """
    Extract tool class names from the source.
    Handles both:
      tools=[GitHubTool, SlackTool]
      tools=[GitHubTool(), SlackTool()]
    """
    tools = []

    # Strategy 1: AST parse to find tools= keyword argument
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "tools":
                        if isinstance(keyword.value, ast.List):
                            for elt in keyword.value.elts:
                                name = _extract_name_from_node(elt)
                                if name:
                                    tools.append(name)
    except SyntaxError:
        pass

    # Strategy 2: Regex fallback for tools= patterns
    if not tools:
        pattern = r"tools\s*=\s*\[([^\]]+)\]"
        match = re.search(pattern, source, re.DOTALL)
        if match:
            items = match.group(1)
            # Extract class names (words before optional parentheses)
            names = re.findall(r"\b([A-Z][A-Za-z0-9]+?)(?:Tool)?\s*[\(\),\]]", items)
            tools = [n + "Tool" if not n.endswith("Tool") else n for n in names]

    # Deduplicate while preserving order
    seen = set()
    unique_tools = []
    for t in tools:
        if t not in seen:
            seen.add(t)
            unique_tools.append(t)

    return unique_tools


def _extract_name_from_node(node) -> str | None:
    """Extract a tool class name from an AST node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _extract_task_description(source: str) -> str:
    """
    Extract the agent's task description from common patterns:
      - system_message="..."
      - description="..."
      - prefix="..."
      - A top-level docstring or comment block
    """
    patterns = [
        # Dict key syntax: "system_message": "..." (agent_kwargs dicts)
        r'"system_message"\s*:\s*["\']([^"\']+)["\']',
        r"'system_message'\s*:\s*['\"]([^'\"]+)['\"]",
        # Assignment syntax: system_message = "..."
        r'system_message\s*=\s*["\']([^"\']+)["\']',
        r'system_message\s*=\s*"""([^"]+)"""',
        r"system_message\s*=\s*'''([^']+)'''",
        r'description\s*=\s*["\']([^"\']+)["\']',
        r'prefix\s*=\s*["\']([^"\']+)["\']',
        r'task\s*=\s*["\']([^"\']+)["\']',
        r'goal\s*=\s*["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, source, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Fallback: use the filename or return empty
    return ""
