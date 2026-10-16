#!/usr/bin/env python3
"""
Scope guard: a heuristic floor, not a substitute for maintainer review.

This repository accepts supply-chain mapping only (suppliers, dependencies,
chokepoints). This check flags data-like files that contain signs of technical
data about how a component is designed, made, tested, or performs: engineering
units attached to numbers, and a short list of engineering terms.

A flag means "a maintainer should look", not "this is wrong". False positives
are expected; a maintainer decides.

Maintainer approval: a flagged line passes if it ends with
`# scope-ok: <reason>` (reason of at least 10 characters). The marker is
honoured only when the PR author's association is OWNER, MEMBER or
COLLABORATOR (env AUTHOR_ASSOCIATION). From anyone else, the marker itself is
a finding. Every approved line is listed in the job summary.
"""
import os
import re
import sys
from pathlib import Path

DATA_SUFFIXES = {".csv", ".tsv", ".json", ".yaml", ".yml"}
EXAMPLES_PREFIX = "examples/"
EXEMPT_PREFIXES = (".github/",)

MAINTAINER_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
MIN_REASON_LEN = 10
MARKER_RE = re.compile(r"#\s*scope-ok:(?P<reason>.*)$", re.IGNORECASE)

UNIT_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s?(?:rpm|psi|mpa|kpa|kn|kg/s|mm|µm|um|nm)\b",
    re.IGNORECASE,
)
TERMS = [
    "tolerance",
    "thrust",
    "specific impulse",
    "chamber pressure",
    "mass flow",
    "flow rate",
    "torque",
    "drawing number",
]
TERM_RES = [(t, re.compile(r"\b" + re.escape(t) + r"s?\b", re.IGNORECASE)) for t in TERMS]


def in_scope(path: str) -> bool:
    if any(path.startswith(p) for p in EXEMPT_PREFIXES):
        return False
    p = Path(path)
    return p.suffix.lower() in DATA_SUFFIXES or path.startswith(EXAMPLES_PREFIX)


def scan(path: str, findings: list, approved: list, maintainer: bool) -> None:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
    except (FileNotFoundError, IsADirectoryError):
        return
    for n, line in enumerate(text.splitlines(), start=1):
        hits = []
        m = UNIT_RE.search(line)
        if m:
            hits.append(f"{path}:{n}: number with engineering unit ({m.group(0)!r})")
        for term, rx in TERM_RES:
            if rx.search(line):
                hits.append(f"{path}:{n}: engineering term ({term!r})")

        marker = MARKER_RE.search(line)
        if marker:
            reason = marker.group("reason").strip()
            if not maintainer:
                findings.append(f"{path}:{n}: approval marker added by non-maintainer")
            elif len(reason) < MIN_REASON_LEN:
                findings.append(
                    f"{path}:{n}: scope-ok marker needs a reason of at least "
                    f"{MIN_REASON_LEN} characters"
                )
            elif hits:
                approved.append((path, n, reason))
                continue  # flagged line approved by a maintainer
        findings.extend(hits)


def write_summary(approved: list, findings: list, maintainer: bool, assoc: str) -> None:
    """Append a report to the GitHub job summary, if running in Actions."""
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    lines = ["## Scope guard", "", f"PR author association: `{assoc or 'unknown'}` "
             f"({'maintainer' if maintainer else 'not a maintainer'})", ""]
    if approved:
        lines += ["### Maintainer-approved lines (`# scope-ok`)", "",
                  "| File | Line | Reason |", "| --- | --- | --- |"]
        for f, n, r in approved:
            safe = r.replace("|", "\\|")
            lines.append(f"| `{f}` | {n} | {safe} |")
        lines.append("")
    if findings:
        lines += ["### Findings", ""] + [f"- {i}" for i in findings] + [""]
    if not approved and not findings:
        lines.append("No findings and no approved lines.")
    with open(target, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: scope_guard.py <changed_files_list.txt>")
        return 2
    listing = Path(sys.argv[1])
    if not listing.exists():
        print("No changed-files list found; nothing to check.")
        return 0

    files = [l.strip() for l in listing.read_text().splitlines() if l.strip()]
    assoc = os.environ.get("AUTHOR_ASSOCIATION", "").strip().upper()
    maintainer = assoc in MAINTAINER_ASSOCIATIONS
    findings: list = []
    approved: list = []
    checked = 0
    for f in files:
        if in_scope(f) and Path(f).is_file():
            checked += 1
            scan(f, findings, approved, maintainer)

    write_summary(approved, findings, maintainer, assoc)
    if approved:
        print("Maintainer-approved lines (# scope-ok):")
        for f, n, r in approved:
            print(f"  - {f}:{n}: {r}")

    if findings:
        print("Scope check flagged possible technical data. This repository accepts mapping only")
        print("(see DATA-CONTRIBUTIONS.md). A maintainer will review:\n")
        for item in findings:
            print(f"  - {item}")
        return 1

    print(f"Scope check passed ({checked} data file(s) checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
