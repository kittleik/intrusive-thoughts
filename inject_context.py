#!/usr/bin/env python3
"""Extract active project context from MEMORY.md and write active_context.json."""

import json
import re
from datetime import datetime
from pathlib import Path

MEMORY_PATH = Path.home() / ".openclaw" / "workspace" / "MEMORY.md"
OUTPUT_PATH = Path(__file__).parent / "active_context.json"

# Known project keywords to detect
PROJECT_KEYWORDS = [
    "cauldron-tui", "cauldron-beta", "cauldron-wallet", "intrusive-thoughts",
    "newsroom", "libriften", "DSTC-bots", "poly_data", "bch-prediction-market",
    "moltbook", "agent-commons",
]

# Thought types that relate to active project work
PROJECT_THOUGHTS = ["upgrade-project", "build-tool", "learn", "share-discovery"]


def extract_context():
    if not MEMORY_PATH.exists():
        return {"updated": datetime.now().isoformat(), "open_items": [], "hot_projects": [], "suggested_thoughts": []}

    text = MEMORY_PATH.read_text()

    # Extract "Active Projects" section
    active_section = ""
    m = re.search(r"## Active Projects\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if m:
        active_section = m.group(1)

    open_items = []
    hot_projects = []

    for line in active_section.strip().split("\n"):
        line = line.strip()
        if not line or not line.startswith("- **"):
            continue

        # Extract project name
        proj_match = re.match(r"- \*\*(\S+)\*\*", line)
        if not proj_match:
            continue
        proj = proj_match.group(1)

        # Detect activity markers: ❌ blocked, recent activity, working
        is_hot = False
        if any(marker in line.lower() for marker in ["❌", "blocked", "working", "wip", "active"]):
            is_hot = True
        if "no recent activity" in line.lower() or "stable" in line.lower():
            is_hot = False

        # Extract blockers/issues as open items
        issue_patterns = [
            r"(issue #\d+[^.]*)",
            r"(❌[^.]*\.)",
            r"(blocked by[^.]*\.?)",
        ]
        for pat in issue_patterns:
            for hit in re.finditer(pat, line, re.IGNORECASE):
                item = f"{proj}: {hit.group(1).strip()}"
                item = re.sub(r'\*+', '', item)  # strip markdown bold
                if item not in open_items:
                    open_items.append(item)

        if is_hot:
            hot_projects.append(proj)

    # Suggest thoughts based on what's hot
    suggested = []
    if hot_projects:
        suggested.append("upgrade-project")
        suggested.append("build-tool")

    return {
        "updated": datetime.now().isoformat(),
        "open_items": open_items[:10],
        "hot_projects": hot_projects,
        "suggested_thoughts": suggested,
    }


if __name__ == "__main__":
    ctx = extract_context()
    OUTPUT_PATH.write_text(json.dumps(ctx, indent=2) + "\n")
    print(json.dumps(ctx, indent=2))
