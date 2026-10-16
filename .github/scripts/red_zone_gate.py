# Handling: Unclassified — working
"""Red zone gate.

Fails a pull request that changes any red-zone path, so that it can merge only
through the repository owner's logged ruleset bypass. Green-only pull requests
pass and can auto-merge.

Zones come from .github/CODEOWNERS on the BASE branch: a path whose last
matching CODEOWNERS line names an owner is red; a path whose last matching
line has no owner is green; a path no line matches is red (fail closed).

Why this exists: GitHub does not require code-owner review when the pull
request author is the code owner, and every pull request here is authored by
the owner's account. Code-owner review alone therefore never blocks.

Uses only the GitHub REST API and the base-branch checkout. Never checks out or
runs pull request code.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

CODEOWNERS = Path(".github/CODEOWNERS")


def pattern_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a CODEOWNERS (gitignore-style) pattern into a regex."""
    anchored = pattern.startswith("/") or "/" in pattern.strip("/")
    dir_only = pattern.endswith("/")
    body = pattern.strip("/")
    out, i = [], 0
    while i < len(body):
        if body.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif body.startswith("/**", i) and i + 3 == len(body):
            out.append("/.*")
            i += 3
        elif body.startswith("**", i):
            out.append(".*")
            i += 2
        elif body[i] == "*":
            out.append("[^/]*")
            i += 1
        elif body[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(body[i]))
            i += 1
    prefix = "^" if anchored else "^(?:.*/)?"
    suffix = "/.*$" if dir_only else "(?:/.*)?$"
    return re.compile(prefix + "".join(out) + suffix)


def parse_codeowners(text: str) -> list[tuple[re.Pattern[str], bool]]:
    """Return (regex, has_owner) per rule, in file order."""
    rules = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        rules.append((pattern_to_regex(parts[0]), len(parts) > 1))
    return rules


def is_red(path: str, rules: list[tuple[re.Pattern[str], bool]]) -> bool:
    verdict = True  # unmatched paths are red
    for regex, has_owner in rules:
        if regex.match(path):
            verdict = has_owner  # last match wins
    return verdict


def changed_paths(repo: str, pr: str, token: str) -> list[str]:
    paths, page = [], 1
    while True:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/pulls/{pr}/files?per_page=100&page={page}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            batch = json.load(resp)
        for f in batch:
            paths.append(f["filename"])
            if f.get("previous_filename"):
                paths.append(f["previous_filename"])  # moving a file out of red is red
        if len(batch) < 100:
            return paths
        page += 1


def main() -> int:
    repo, pr, token = os.environ["REPO"], os.environ["PR_NUMBER"], os.environ["GITHUB_TOKEN"]
    if not CODEOWNERS.is_file():
        print("::error::.github/CODEOWNERS missing on base branch; failing closed")
        return 1
    rules = parse_codeowners(CODEOWNERS.read_text(encoding="utf-8"))
    red = sorted({p for p in changed_paths(repo, pr, token) if is_red(p, rules)})
    lines = ["## Red zone gate", ""]
    if red:
        lines += ["**RED**: owner approval required (ruleset bypass). Red paths:", ""]
        lines += [f"- `{p}`" for p in red]
        for p in red:
            print(f"::error file={p}::red-zone path; merge requires owner bypass")
    else:
        lines.append("**GREEN**: no red-zone paths changed.")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
