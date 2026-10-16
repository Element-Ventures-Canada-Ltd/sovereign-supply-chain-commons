# Handling: Unclassified — working
"""
Plain, deterministic checks shared by the SOI Graph Agents agents.

Every function here is pure: text in, findings out. No network, no file writes.
The classification and credential patterns are imported from the repository's
data-handling guard so there is one source of truth for them.
"""
from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_GUARD_PATH = REPO_ROOT / ".github" / "scripts" / "data_handling_guard.py"


def _load_guard():
    spec = importlib.util.spec_from_file_location("data_handling_guard", _GUARD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_guard = _load_guard()
CLASSIFIED_PATTERNS = _guard.CLASSIFIED_PATTERNS
CREDENTIAL_PATTERNS = _guard.CREDENTIAL_PATTERNS
requires_handling_marker = _guard.requires_handling_marker
HANDLING_RE = _guard.HANDLING_RE

# --- Scope (mapping only; see CONTRIBUTION-SCOPE.md and DATA-CONTRIBUTIONS.md) ---
DATA_SUFFIXES = {".csv", ".tsv", ".json", ".yaml", ".yml", ".xml", ".parquet"}
UNIT_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:rpm|psi|mpa|kpa|kn|kg/s|mm|µm|um|nm)\b", re.IGNORECASE)
SCOPE_TERMS = [
    "tolerance", "thrust", "specific impulse", "chamber pressure", "mass flow",
    "flow rate", "torque", "drawing number", "cad file", "test result",
]
SCOPE_TERM_RES = [(t, re.compile(r"\b" + re.escape(t) + r"s?\b", re.IGNORECASE)) for t in SCOPE_TERMS]

# --- Licence contamination: data under these licences cannot enter the open tier ---
NONREDISTRIBUTABLE_LICENCE_RES = [
    ("CC BY-NC", re.compile(r"\bCC[-\s]?BY[-\s]?NC\b|NonCommercial", re.IGNORECASE)),
    ("ODbL share-alike", re.compile(r"\bODbL\b", re.IGNORECASE)),
]

# --- Personal information indicators in structured data headers/keys ---
PERSON_FIELD_RE = re.compile(
    r"\b(date_of_birth|dob|birth_date|home_address|residential_address|personal_email|"
    r"phone_number|passport|sin_number|ssn|inventor_name|director_name|nationality)\b",
    re.IGNORECASE,
)

# --- Contribution governance ---
CLA_RE = re.compile(r"^\s*-\s*\[x\]\s*I agree to the Contributor License Agreement", re.IGNORECASE | re.MULTILINE)
DCO_RE = re.compile(r"^Signed-off-by: .+ <.+@.+>", re.IGNORECASE | re.MULTILINE)
AI_DISCLOSURE_RE = re.compile(
    r"\b(ai[- ]assisted|ai[- ]generated|generated (?:by|with) (?:an? )?(?:ai|llm|claude|gpt|chatgpt|copilot|gemini)|"
    r"co-authored-by: (?:claude|copilot|chatgpt)|autonomous agent|agent account)\b",
    re.IGNORECASE,
)
CLAIM_ONLY_RE = re.compile(
    r"^\s*(/take|/claim|/attempt|/assign|\.take|i(?:'d| would)? like to (?:take|work on) this|"
    r"(?:please )?assign (?:this |it )?(?:to )?me|can i (?:take|work on) this)\b",
    re.IGNORECASE,
)
PAYMENT_RE = re.compile(
    r"\b(paypal|venmo|wise transfer|usdt|usdc|crypto|wallet address|bank details|invoice|"
    r"how much (?:is|does) (?:the )?bounty|payment on merge|pay(?:ment)? (?:me|now|upfront))\b",
    re.IGNORECASE,
)
PROTECTED_PATHS = (".github/workflows/", ".github/scripts/", "CLA.md", "CCLA.md", "LICENSE", "NOTICE", "HANDLING.md")
MAINTAINER_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}


@dataclass
class Finding:
    code: str          # stable machine code, e.g. "scope-unit"
    severity: str      # "review" (maintainer should look) or "info"
    where: str         # file path or "pr-body", "comment", ...
    detail: str
    label: str | None = None  # label the agent applies for this finding


@dataclass
class Result:
    findings: list[Finding] = field(default_factory=list)

    def add(self, *args, **kw) -> None:
        self.findings.append(Finding(*args, **kw))

    @property
    def labels(self) -> set[str]:
        return {f.label for f in self.findings if f.label}

    @property
    def needs_review(self) -> bool:
        return any(f.severity == "review" for f in self.findings)


def is_data_file(path: str) -> bool:
    return Path(path).suffix.lower() in DATA_SUFFIXES and not path.startswith(".github/")


def check_file(path: str, text: str, result: Result) -> None:
    """Content checks for one changed file."""
    if requires_handling_marker(path) and not HANDLING_RE.search(text):
        result.add("handling-marker", "review", path, "missing `Handling:` marker (HANDLING.md)", "handling-review")
    for pat in CLASSIFIED_PATTERNS:
        if re.search(pat, text):
            result.add("classification-marking", "review", path, "classification-style marking found", "handling-review")
            break
    for pat in CREDENTIAL_PATTERNS:
        if re.search(pat, text):
            result.add("credential", "review", path, "possible credential or secret", "handling-review")
            break
    if not is_data_file(path):
        return
    for n, line in enumerate(text.splitlines(), start=1):
        m = UNIT_RE.search(line)
        if m:
            result.add("scope-unit", "review", f"{path}:{n}", f"number with engineering unit ({m.group(0)!r})", "scope-review")
        for term, rx in SCOPE_TERM_RES:
            if rx.search(line):
                result.add("scope-term", "review", f"{path}:{n}", f"engineering term ({term!r})", "scope-review")
        if PERSON_FIELD_RE.search(line):
            result.add("personal-info", "review", f"{path}:{n}", "field name suggests personal information", "handling-review")
    for name, rx in NONREDISTRIBUTABLE_LICENCE_RES:
        if rx.search(text):
            result.add("licence-contamination", "review", path, f"mentions {name} licence; data under it cannot enter the open tier", "agent:review")


def check_data_provenance(changed_paths: list[str], result: Result) -> None:
    """DATA-CONTRIBUTIONS.md rule 5: every data folder needs a provenance.yaml."""
    data_dirs = {str(Path(p).parent) for p in changed_paths
                 if is_data_file(p) and Path(p).name != "provenance.yaml"}
    present = {str(Path(p).parent) for p in changed_paths if Path(p).name == "provenance.yaml"}
    for d in sorted(data_dirs - present):
        if (REPO_ROOT / d / "provenance.yaml").exists():
            continue
        result.add("provenance-missing", "review", d, "data added without provenance.yaml (DATA-CONTRIBUTIONS.md)", "agent:review")


def check_pr(body: str, author_association: str, commit_messages: list[str],
             changed_paths: list[str], result: Result) -> None:
    external = author_association not in MAINTAINER_ASSOCIATIONS
    body = body or ""
    if external and not CLA_RE.search(body):
        result.add("cla-box", "review", "pr-body", "CLA box not checked", "agent:review")
    if external:
        missing = sum(1 for m in commit_messages if not DCO_RE.search(m or ""))
        if missing:
            result.add("dco", "review", "commits", f"{missing} commit(s) without DCO sign-off", "agent:review")
        touched = [p for p in changed_paths if p.startswith(PROTECTED_PATHS)]
        if touched:
            result.add("protected-path", "review", ", ".join(touched), "external change to workflows, guards or legal files", "agent:review")
    text = body + "\n" + "\n".join(commit_messages)
    if AI_DISCLOSURE_RE.search(text):
        result.add("ai-disclosure", "info", "pr-body", "AI assistance disclosed; confirm a named Responsible Person accepted the CLA", "ai-assisted")
    check_text_signals(body, "pr-body", result)
    check_data_provenance(changed_paths, result)


def check_text_signals(text: str, where: str, result: Result) -> None:
    """Issue / comment signals: claim-only posts and payment requests."""
    text = text or ""
    stripped = text.strip()
    if CLAIM_ONLY_RE.search(stripped) and len(stripped) < 280:
        result.add("claim-only", "info", where, "short claim with no proposal; claims are not assignments", "agent:claim-only")
    if PAYMENT_RE.search(text):
        result.add("payment-ask", "review", where, "payment or bounty-amount request", "agent:payment-ask")
    if AI_DISCLOSURE_RE.search(text):
        result.add("ai-disclosure", "info", where, "AI assistance or agent account disclosed", "ai-assisted")


def render_summary(title: str, result: Result) -> str:
    lines = [f"### SOI Graph Agents — {title}", ""]
    if not result.findings:
        lines.append("No findings. Plain checks passed.")
        return "\n".join(lines) + "\n"
    lines += ["| Severity | Check | Where | Detail |", "| :-- | :-- | :-- | :-- |"]
    for f in result.findings:
        lines.append(f"| {f.severity} | `{f.code}` | {f.where} | {f.detail} |")
    lines += ["", "_Findings mean a maintainer should look, not that the contribution is wrong. The agent never comments, merges or closes._"]
    return "\n".join(lines) + "\n"
