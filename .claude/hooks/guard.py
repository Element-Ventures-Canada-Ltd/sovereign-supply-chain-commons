#!/usr/bin/env python3
# Handling: Unclassified — working
"""Pre-tool guard for Claude Code in this repository.

Runs before every shell command and every GitHub tool call. It makes the
repository's git rules mechanical rather than a matter of discipline:

  deny  - irreversible or owner-only actions: committing on `main`, pushing to
          `main`, force pushes, history rewrites, merging or approving pull
          requests, secrets, variables, rulesets, releases, repo settings,
          tokens, and any commit made under an identity other than the owner's.
  ask   - actions that change shared state: any push, opening a pull request,
          deleting files or branches, rebase, hard reset, package installs.
  allow - everything else.

Input: the hook JSON on stdin ({"tool_name": ..., "tool_input": {...}}).
Output: a PreToolUse permission decision as JSON for deny or ask; nothing for
allow. Unit tests: `python3 -m unittest .claude/hooks/test_guard.py`.
"""
import json
import os
import re
import shlex
import subprocess
import sys

PROTECTED = {"main", "master"}
FORCE_FLAGS = {"-f", "--force", "--force-with-lease", "--force-if-includes",
               "--mirror", "--delete", "-d", "--tags", "--prune", "--all"}


# ---------------------------------------------------------------- context

def _root():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def load_context():
    root = _root()
    owner = {}
    for name in ("owner.local.json", "owner.json"):  # a collaborator's own file wins
        try:
            with open(os.path.join(root, ".claude", name), encoding="utf-8") as fh:
                owner = json.load(fh)
            break
        except (OSError, ValueError):
            continue

    def git(*args):
        r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
        return r.stdout.strip()

    return {
        "branch": git("branch", "--show-current"),
        "email": git("config", "user.email"),
        "name": git("config", "user.name"),
        "owner_email": owner.get("email", ""),
        "owner_name": owner.get("name", ""),
        "blocked": [e.lower() for e in owner.get("blocked_identities", ["noreply@anthropic.com"])],
    }


# ---------------------------------------------------------------- helpers

def segments(command):
    """Split a shell command line into simple commands (token lists)."""
    parts = re.split(r"&&|\|\||;|\||\n", command)
    out = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        try:
            toks = shlex.split(part)
        except ValueError:
            toks = part.split()
        # drop leading VAR=value assignments, but remember them
        assigns = []
        while toks and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0]):
            assigns.append(toks.pop(0))
        out.append((assigns, toks))
    return out


def _owner_ok(email, ctx):
    return bool(ctx["owner_email"]) and email.lower() == ctx["owner_email"].lower()


def _identity_problem(email, ctx):
    e = (email or "").lower()
    if not e:
        return "git has no author email set"
    if e in ctx["blocked"]:
        return f"git author is the blocked identity <{email}>"
    if not _owner_ok(email, ctx):
        return f"git author <{email}> is not the owner"
    return None


FIX_IDENTITY = ("Run `python3 .claude/hooks/owner_identity.py` to set the owner identity, "
                "then commit again. A commit under the Claude identity fails the CLA check.")


# ---------------------------------------------------------------- git

def check_git(toks, ctx):
    args = toks[1:]
    configs = []
    while args and args[0] in ("-c", "-C", "--git-dir", "--work-tree"):
        flag = args.pop(0)
        val = args.pop(0) if args else ""
        if flag == "-c":
            configs.append(val)
    for cfg in configs:
        key, _, val = cfg.partition("=")
        if key.lower() == "user.email" and not _owner_ok(val, ctx):
            return "deny", f"`git -c user.email={val}` overrides the owner identity. {FIX_IDENTITY}"
        if key.lower().startswith("credential"):
            return "deny", "Sessions use the owner's account only; no credential helpers or tokens."
    if not args:
        return "allow", ""
    sub, rest = args[0], args[1:]

    if sub == "commit":
        if ctx["branch"] in PROTECTED:
            return "deny", f"Never commit on `{ctx['branch']}`. Create a branch first: `git switch -c feature/<name>`."
        if "--no-verify" in rest:
            return "deny", "Skipping hooks (`--no-verify`) is not allowed."
        for i, t in enumerate(rest):
            if t.startswith("--author"):
                val = t.split("=", 1)[1] if "=" in t else (rest[i + 1] if i + 1 < len(rest) else "")
                m = re.search(r"<([^>]+)>", val)
                if not m or not _owner_ok(m.group(1), ctx):
                    return "deny", f"`--author` must be the owner. {FIX_IDENTITY}"
        problem = _identity_problem(ctx["email"], ctx)
        if problem:
            return "deny", f"{problem}. {FIX_IDENTITY}"
        if "--amend" in rest:
            return "ask", "Amending rewrites the last commit. Only on your own unpushed commit."
        return "allow", ""

    if sub == "push":
        if any(t in FORCE_FLAGS or t.startswith("--force") for t in rest) or any(
                re.match(r"^\+", t) for t in rest):
            return "deny", "Force pushes, deletes, tag and mirror pushes are owner-only."
        refspecs = [t for t in rest if not t.startswith("-")][1:]  # skip remote name
        for spec in refspecs:
            dst = spec.split(":")[-1]
            dst = dst.replace("refs/heads/", "")
            if dst in PROTECTED or spec in PROTECTED:
                return "deny", "Never push to `main`. Push your feature branch and open a pull request."
            if spec.startswith(":"):
                return "deny", "Deleting a remote branch is owner-only."
        if not refspecs and ctx["branch"] in PROTECTED:
            return "deny", "You are on `main`. Never push it; switch to a feature branch."
        problem = _identity_problem(ctx["email"], ctx)
        if problem:
            return "deny", f"{problem}; fix the identity before pushing. {FIX_IDENTITY}"
        return "ask", "Pushing changes shared state. The owner confirms each push."

    if sub == "config":
        joined = " ".join(rest)
        if re.search(r"\bcredential", joined):
            return "deny", "No credential helpers or tokens; sessions use the owner's account only."
        if any(t in ("--global", "--system") for t in rest) and re.search(r"user\.(email|name)", joined):
            return "deny", "Do not change the global identity. The repo-local owner identity is set by the hook."
        m = re.search(r"user\.email\s+(\S+)", joined)
        if m and not _owner_ok(m.group(1), ctx):
            return "deny", f"Setting another author email is not allowed. {FIX_IDENTITY}"
        m = re.search(r"user\.name\s+(.+)$", joined)
        if m and ctx["owner_name"] and m.group(1).strip().strip("'\"") != ctx["owner_name"]:
            return "deny", f"Setting another author name is not allowed. {FIX_IDENTITY}"
        return "allow", ""

    if sub in ("filter-branch", "filter-repo", "replace"):
        return "deny", "History rewrites are owner-only."
    if sub == "rebase":
        return "ask", "Rebase rewrites history. Only on your own unpushed branch."
    if sub == "reset" and "--hard" in rest:
        return "ask", "A hard reset discards work."
    if sub == "clean" and any(t.startswith("-") and "f" in t for t in rest):
        return "ask", "`git clean -f` deletes untracked files."
    if sub == "rm":
        return "ask", "Deleting files is red zone; the owner confirms."
    if sub == "branch" and any(t in ("-D", "-d", "--delete") for t in rest):
        return "ask", "Deleting a branch."
    if sub == "tag" and rest:
        return "ask", "Tags mark releases, which are owner-only."
    if sub == "remote" and rest[:1] in (["set-url"], ["add"]) and any("@" in t for t in rest):
        return "deny", "No credentials in remote URLs."
    return "allow", ""


# ---------------------------------------------------------------- gh

def check_gh(toks):
    args = toks[1:]
    if not args:
        return "allow", ""
    grp, rest = args[0], args[1:]
    verb = rest[0] if rest else ""
    if grp == "pr":
        if verb == "merge":
            if "--auto" in rest:
                return "allow", ""
            return "deny", "Never merge a pull request. Auto-merge (`gh pr merge --auto --squash`) is the only form allowed."
        if verb == "review" and any(t in ("--approve", "-a") for t in rest):
            return "deny", "Never approve a pull request; approval is the owner's."
        if verb == "create":
            return "ask", "Opening a pull request. The owner confirms."
        if verb in ("close", "reopen"):
            return "ask", "Closing or reopening a pull request is the owner's call."
    if grp in ("secret", "variable", "ruleset", "auth"):
        return "deny", f"`gh {grp}` is owner-only (secrets, variables, rulesets, credentials)."
    if grp == "release" and verb not in ("list", "view", ""):
        return "deny", "Releases are owner-only."
    if grp == "repo" and verb in ("delete", "edit", "rename", "archive", "create", "fork"):
        return "deny", "Repository settings are owner-only."
    if grp == "api":
        joined = " ".join(rest)
        method = re.search(r"(?:-X|--method)\s*=?\s*(\w+)", joined)
        mutating = (method and method.group(1).upper() != "GET") or re.search(
            r"(^|\s)(-f|-F|--field|--raw-field|--input)(\s|=)", joined)
        if mutating:
            return "deny", "Write calls through `gh api` are blocked; use the reviewed command or ask the owner."
        if "graphql" in joined:
            return "deny", "GraphQL is blocked for these sessions."
    if grp == "workflow" and verb in ("run", "enable", "disable"):
        return "ask", "Running or toggling a workflow changes shared state."
    return "allow", ""


# ---------------------------------------------------------------- bash

def check_bash(command, ctx):
    worst = ("allow", "")
    rank = {"allow": 0, "ask": 1, "deny": 2}
    if re.search(r"Authorization:\s*(token|bearer)", command, re.IGNORECASE):
        return "deny", "No tokens in commands; sessions use the owner's account only."
    for assigns, toks in segments(command):
        for a in assigns:
            if re.match(r"^(GH_TOKEN|GITHUB_TOKEN|GH_ENTERPRISE_TOKEN)=", a):
                return "deny", "Do not set GitHub tokens; sessions act under the owner's account only."
        if not toks:
            continue
        head = os.path.basename(toks[0])
        if head == "export" and any(re.match(r"^(GH_TOKEN|GITHUB_TOKEN)=", t) for t in toks[1:]):
            return "deny", "Do not set GitHub tokens; sessions act under the owner's account only."
        if head == "git":
            res = check_git(toks, ctx)
        elif head == "gh":
            res = check_gh(toks)
        elif head in ("pip", "pip3") and "install" in toks:
            res = ("ask", "Installing packages changes dependencies (red zone if pinned).")
        elif head == "npm" and len(toks) > 1 and toks[1] in ("install", "i", "add", "ci"):
            res = ("ask", "Installing packages changes dependencies (red zone if pinned).")
        else:
            res = ("allow", "")
        if rank[res[0]] > rank[worst[0]]:
            worst = res
        if worst[0] == "deny":
            break
    return worst


# ---------------------------------------------------------------- MCP GitHub tools

def check_mcp(tool, inp):
    name = tool.split("__")[-1]
    blob = json.dumps(inp).upper()
    if name == "merge_pull_request":
        return "deny", "Never merge a pull request; merging is the owner's."
    if name == "pull_request_review_write" and "APPROVE" in blob:
        return "deny", "Never approve a pull request; approval is the owner's."
    if name in ("create_repository", "fork_repository"):
        return "deny", "Repositories are created by the owner."
    if name in ("push_files", "create_or_update_file", "delete_file"):
        if str(inp.get("branch", "")).replace("refs/heads/", "") in PROTECTED:
            return "deny", "Never write to `main`. Use a feature branch and a pull request."
        if name == "delete_file":
            return "ask", "Deleting a file is red zone."
        return "ask", "Writing to a remote branch. The owner confirms."
    if name == "create_pull_request":
        return "ask", "Opening a pull request. The owner confirms."
    if name == "update_pull_request" and ("CLOSED" in blob or "\"BASE\"" in blob):
        return "ask", "Closing or retargeting a pull request is the owner's call."
    if name == "actions_run_trigger":
        return "ask", "Running a workflow changes shared state."
    return "allow", ""


def decide(payload, ctx):
    tool = payload.get("tool_name", "")
    inp = payload.get("tool_input", {}) or {}
    if tool == "Bash":
        return check_bash(inp.get("command", ""), ctx)
    if tool.startswith("mcp__github__"):
        return check_mcp(tool, inp)
    return "allow", ""


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    decision, reason = decide(payload, load_context())
    if decision == "allow":
        return 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": f"Repo guard: {reason}",
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
