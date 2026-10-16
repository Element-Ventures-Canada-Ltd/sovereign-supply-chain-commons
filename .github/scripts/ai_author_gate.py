#!/usr/bin/env python3
# Handling: Unclassified — working
"""
AI-authored commit gate for the CLA workflow.

CLA.md section 1 says a Contribution made by or through an AI agent is made by
the Responsible Person who authorized it, and section 11 says an AI system
cannot sign. The CLA bot checks commit authors, and an AI agent's commit author
has no GitHub account, so the bot would flag it as an unsigned committer.

This script decides whether the allowlist passed to the CLA bot may also name
the AI commit identity for THIS pull request. It does, only when ALL hold:

  1. the pull request opener has signed the CLA (recorded on the
     `cla-signatures` branch) or is on the static allowlist; and
  2. every commit authored by the AI identity (name and email below) carries a
     `Co-Authored-By: <AI name>` trailer, so the AI contribution is disclosed
     in the history.

Commits by any other unsigned author are still flagged by the bot. The
exemption names one identity and never uses a wildcard. It is computed per
pull request from the GitHub API only; no pull request code is checked out or
run. The decision and the exempted commits are written to the job summary.

Env: GH_TOKEN, REPO, PR_NUMBER, BASE_ALLOWLIST. Optional: AI_NAME, AI_EMAIL.
Writes `allowlist=` to $GITHUB_OUTPUT.
"""
import base64
import json
import os
import re
import subprocess
import sys

AI_NAME_DEFAULT = "Claude"
AI_EMAIL_DEFAULT = "noreply@anthropic.com"


def decide(opener, signed, base_allowlist, commits, ai_name=AI_NAME_DEFAULT,
           ai_email=AI_EMAIL_DEFAULT):
    """Return (allowlist, exempted_commits, reason). `signed` is a set of logins."""
    trailer = re.compile(r"^Co-Authored-By:\s*" + re.escape(ai_name) + r"\b",
                         re.IGNORECASE | re.MULTILINE)
    ai_commits = [
        c for c in commits
        if (c.get("name") or "") == ai_name
        and (c.get("email") or "").lower() == ai_email.lower()
        and not c.get("login")
    ]
    if not ai_commits:
        return base_allowlist, [], "no AI-authored commits"
    if opener not in signed:
        return base_allowlist, [], f"PR opener {opener!r} has not signed the CLA"
    missing = [c["sha"][:7] for c in ai_commits if not trailer.search(c.get("message") or "")]
    if missing:
        return base_allowlist, [], (
            "AI-authored commits without a 'Co-Authored-By: " + ai_name + "' trailer: "
            + ", ".join(missing)
        )
    allowlist = base_allowlist + ("," if base_allowlist else "") + ai_name
    return allowlist, ai_commits, f"AI identity {ai_name!r} exempted; Responsible Person {opener!r} has signed"


def gh(path, *extra):
    out = subprocess.run(["gh", "api", *extra, path], check=True, capture_output=True, text=True)
    return out.stdout


def load_signed(repo, base_allowlist):
    signed = {p.strip() for p in base_allowlist.split(",") if p.strip() and "*" not in p}
    try:
        raw = json.loads(gh(f"repos/{repo}/contents/signatures/cla.json?ref=cla-signatures"))
        data = json.loads(base64.b64decode(raw["content"]).decode("utf-8"))
        signed |= {s["name"] for s in data.get("signedContributors", []) if s.get("name")}
    except (subprocess.CalledProcessError, KeyError, ValueError):
        pass  # no signatures yet; only the static allowlist counts
    return signed


def main():
    repo, pr = os.environ["REPO"], os.environ.get("PR_NUMBER", "")
    base = os.environ.get("BASE_ALLOWLIST", "")
    ai_name = os.environ.get("AI_NAME", AI_NAME_DEFAULT)
    ai_email = os.environ.get("AI_EMAIL", AI_EMAIL_DEFAULT)

    allowlist, exempted, reason = base, [], "not a pull request"
    if pr:
        opener = json.loads(gh(f"repos/{repo}/pulls/{pr}"))["user"]["login"]
        raw = json.loads(gh(f"repos/{repo}/pulls/{pr}/commits", "--paginate", "--slurp"))
        commits = [
            {"sha": c["sha"], "login": (c.get("author") or {}).get("login"),
             "name": c["commit"]["author"]["name"], "email": c["commit"]["author"]["email"],
             "message": c["commit"]["message"]}
            for page in raw for c in page
        ]
        allowlist, exempted, reason = decide(opener, load_signed(repo, base), base, commits,
                                             ai_name, ai_email)

    print(f"AI author gate: {reason}")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
        fh.write(f"allowlist={allowlist}\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        lines = ["## AI author gate", "", reason, ""]
        lines += [f"- `{c['sha'][:7]}` {c['message'].splitlines()[0]}" for c in exempted]
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
