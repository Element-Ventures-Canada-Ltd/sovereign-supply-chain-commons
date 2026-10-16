# Handling: Unclassified — working
"""Tests for the pre-tool guard. Run: python3 -m unittest discover -s .claude/hooks -p 'test_guard.py'"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import guard  # noqa: E402

OWNER = "tleroy@elementventureslp.com"


def ctx(branch="feature/x", email=OWNER):
    return {"branch": branch, "email": email, "name": "T. Leroy Smith",
            "owner_email": OWNER, "owner_name": "T. Leroy Smith",
            "blocked": ["noreply@anthropic.com"]}


def bash(cmd, **kw):
    return guard.decide({"tool_name": "Bash", "tool_input": {"command": cmd}}, ctx(**kw))[0]


def mcp(name, **inp):
    return guard.decide({"tool_name": "mcp__github__" + name, "tool_input": inp}, ctx())[0]


class Identity(unittest.TestCase):
    def test_commit_as_owner_allowed(self):
        self.assertEqual(bash("git commit -m 'feat: x'"), "allow")

    def test_commit_as_claude_denied(self):
        self.assertEqual(bash("git commit -m x", email="noreply@anthropic.com"), "deny")

    def test_commit_with_no_identity_denied(self):
        self.assertEqual(bash("git commit -m x", email=""), "deny")

    def test_author_override_denied(self):
        self.assertEqual(bash('git commit --author="Claude <noreply@anthropic.com>" -m x'), "deny")

    def test_inline_config_override_denied(self):
        self.assertEqual(bash("git -c user.email=noreply@anthropic.com commit -m x"), "deny")

    def test_set_other_email_denied(self):
        self.assertEqual(bash("git config user.email noreply@anthropic.com"), "deny")

    def test_set_owner_email_allowed(self):
        self.assertEqual(bash(f"git config --local user.email {OWNER}"), "allow")

    def test_global_identity_change_denied(self):
        self.assertEqual(bash(f"git config --global user.email {OWNER}"), "deny")

    def test_reading_identity_allowed(self):
        self.assertEqual(bash("git config user.email"), "allow")


class MainBranch(unittest.TestCase):
    def test_commit_on_main_denied(self):
        self.assertEqual(bash("git commit -m x", branch="main"), "deny")

    def test_push_to_main_denied(self):
        self.assertEqual(bash("git push origin main"), "deny")
        self.assertEqual(bash("git push origin HEAD:main"), "deny")
        self.assertEqual(bash("git push origin feature/x:refs/heads/main"), "deny")

    def test_bare_push_on_main_denied(self):
        self.assertEqual(bash("git push", branch="main"), "deny")

    def test_force_push_denied(self):
        self.assertEqual(bash("git push --force origin feature/x"), "deny")
        self.assertEqual(bash("git push -f origin feature/x"), "deny")
        self.assertEqual(bash("git push origin +feature/x"), "deny")

    def test_delete_remote_branch_denied(self):
        self.assertEqual(bash("git push origin :feature/x"), "deny")
        self.assertEqual(bash("git push origin --delete feature/x"), "deny")

    def test_feature_push_asks(self):
        self.assertEqual(bash("git push -u origin feature/x"), "ask")

    def test_push_with_wrong_identity_denied(self):
        self.assertEqual(bash("git push -u origin feature/x", email="noreply@anthropic.com"), "deny")

    def test_no_verify_denied(self):
        self.assertEqual(bash("git commit --no-verify -m x"), "deny")

    def test_history_rewrite_denied(self):
        self.assertEqual(bash("git filter-repo --path x"), "deny")

    def test_chained_command_caught(self):
        self.assertEqual(bash("git add . && git commit -m x && git push origin main"), "deny")


class GitHub(unittest.TestCase):
    def test_merge_denied(self):
        self.assertEqual(bash("gh pr merge 12 --squash"), "deny")

    def test_auto_merge_allowed(self):
        self.assertEqual(bash("gh pr merge 12 --auto --squash"), "allow")

    def test_approve_denied(self):
        self.assertEqual(bash("gh pr review 12 --approve"), "deny")

    def test_secrets_denied(self):
        self.assertEqual(bash("gh secret set GUARD_TERMS"), "deny")
        self.assertEqual(bash("gh variable set X --body y"), "deny")

    def test_pr_create_asks(self):
        self.assertEqual(bash("gh pr create --title t --body b"), "ask")

    def test_api_read_allowed_write_denied(self):
        self.assertEqual(bash("gh api repos/o/r/pulls/35"), "allow")
        self.assertEqual(bash("gh api -X PUT repos/o/r/pulls/35/merge"), "deny")
        self.assertEqual(bash("gh api repos/o/r/issues/1/comments -f body=x"), "deny")

    def test_token_denied(self):
        self.assertEqual(bash("GH_TOKEN=abc gh pr list"), "deny")
        self.assertEqual(bash("export GITHUB_TOKEN=abc"), "deny")
        self.assertEqual(bash("curl -H 'Authorization: token abc' https://api.github.com"), "deny")

    def test_mcp_merge_and_approve_denied(self):
        self.assertEqual(mcp("merge_pull_request", pullNumber=1), "deny")
        self.assertEqual(mcp("pull_request_review_write", method="create", event="APPROVE"), "deny")

    def test_mcp_write_main_denied_branch_asks(self):
        self.assertEqual(mcp("create_or_update_file", branch="main", path="a"), "deny")
        self.assertEqual(mcp("push_files", branch="feature/x"), "ask")

    def test_mcp_auto_merge_allowed(self):
        self.assertEqual(mcp("enable_pr_auto_merge", pullNumber=1), "allow")

    def test_reads_allowed(self):
        self.assertEqual(mcp("pull_request_read", method="get", pullNumber=1), "allow")
        self.assertEqual(bash("python3 -m unittest discover -s Agents/tests"), "allow")


class Collaborator(unittest.TestCase):
    def test_local_file_wins_and_owner_identity_then_denied(self):
        import json, subprocess, tempfile
        d = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q", d], check=True)
        os.makedirs(os.path.join(d, ".claude"))
        json.dump({"name": "T. Leroy Smith", "email": OWNER},
                  open(os.path.join(d, ".claude", "owner.json"), "w"))
        json.dump({"name": "A Collaborator", "email": "collab@example.org"},
                  open(os.path.join(d, ".claude", "owner.local.json"), "w"))
        env = dict(os.environ, CLAUDE_PROJECT_DIR=d)
        hook = os.path.join(os.path.dirname(__file__), "owner_identity.py")
        subprocess.run([sys.executable, hook], env=env, check=True, capture_output=True)
        email = subprocess.run(["git", "-C", d, "config", "user.email"],
                               capture_output=True, text=True).stdout.strip()
        self.assertEqual(email, "collab@example.org")
        old = os.environ.get("CLAUDE_PROJECT_DIR")
        os.environ["CLAUDE_PROJECT_DIR"] = d
        try:
            c = guard.load_context()
            c["branch"] = "feature/x"
            self.assertEqual(guard.decide({"tool_name": "Bash", "tool_input": {
                "command": "git commit -m x"}}, c)[0], "allow")
            c["email"] = OWNER  # collaborator trying to commit as the owner
            self.assertEqual(guard.decide({"tool_name": "Bash", "tool_input": {
                "command": "git commit -m x"}}, c)[0], "deny")
        finally:
            if old is None:
                del os.environ["CLAUDE_PROJECT_DIR"]
            else:
                os.environ["CLAUDE_PROJECT_DIR"] = old


if __name__ == "__main__":
    unittest.main()
