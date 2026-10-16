#!/usr/bin/env python3
# Handling: Unclassified — working
"""Session-start hook: author every commit in this repository as the owner.

The environment's default git identity is `Claude <noreply@anthropic.com>`.
GitHub links that address to an unrelated public account, so a commit made
under it fails the required CLA check. This hook writes the owner's name and
email from `.claude/owner.local.json` (a collaborator's own, gitignored) or
else `.claude/owner.json` (the repository owner) into this repository's own git config (not the
global config), then prints one status line that Claude reads at session start.
It changes nothing else and is safe to run any number of times.
"""
import json
import os
import subprocess
import sys


def repo_root():
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return env
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    return out.stdout.strip() or os.getcwd()


def load_owner(root):
    """A collaborator's own `.claude/owner.local.json` (gitignored) wins over
    the repository owner's `.claude/owner.json`, so nobody commits as someone else."""
    for name in ("owner.local.json", "owner.json"):
        path = os.path.join(root, ".claude", name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
    raise OSError("no .claude/owner.json")


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)


def main():
    root = repo_root()
    try:
        owner = load_owner(root)
    except (OSError, ValueError) as exc:
        print(f"owner identity: NOT SET ({exc}). Do not commit until this is fixed.")
        return 0
    git(root, "config", "--local", "user.name", owner["name"])
    git(root, "config", "--local", "user.email", owner["email"])
    name = git(root, "config", "user.name").stdout.strip()
    email = git(root, "config", "user.email").stdout.strip()
    ok = name == owner["name"] and email.lower() == owner["email"].lower()
    status = "OK" if ok else "MISMATCH"
    print(f"owner identity: {status}: commits in this repo are authored as {name} <{email}>. "
          "Credit Claude only with a Co-Authored-By trailer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
