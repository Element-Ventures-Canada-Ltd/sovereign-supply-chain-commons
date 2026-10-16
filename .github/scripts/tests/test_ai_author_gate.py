# Handling: Unclassified — working
"""Unit tests for the AI author gate's decision rule."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai_author_gate import decide  # noqa: E402

BASE = "TLS-sys,dependabot[bot]"
TRAILER = "feat: x\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"


def ai(sha="a" * 40, message=TRAILER, **kw):
    c = {"sha": sha, "login": None, "name": "Claude", "email": "noreply@anthropic.com",
         "message": message}
    c.update(kw)
    return c


def human(login="someone", sha="b" * 40):
    return {"sha": sha, "login": login, "name": login, "email": f"{login}@example.com",
            "message": "fix: y"}


class AiAuthorGate(unittest.TestCase):
    def test_signed_opener_with_trailer_exempts_ai_identity(self):
        al, exempted, _ = decide("TLS-sys", {"TLS-sys"}, BASE, [ai()])
        self.assertEqual(al, BASE + ",Claude")
        self.assertEqual(len(exempted), 1)

    def test_unsigned_opener_gets_no_exemption(self):
        al, exempted, reason = decide("stranger", {"TLS-sys"}, BASE, [ai()])
        self.assertEqual(al, BASE)
        self.assertEqual(exempted, [])
        self.assertIn("has not signed", reason)

    def test_missing_trailer_gets_no_exemption(self):
        al, _, reason = decide("TLS-sys", {"TLS-sys"}, BASE, [ai(message="feat: x")])
        self.assertEqual(al, BASE)
        self.assertIn("Co-Authored-By", reason)

    def test_one_commit_missing_trailer_blocks_all(self):
        commits = [ai(sha="1" * 40), ai(sha="2" * 40, message="no trailer")]
        al, _, _ = decide("TLS-sys", {"TLS-sys"}, BASE, commits)
        self.assertEqual(al, BASE)

    def test_wrong_email_is_not_the_ai_identity(self):
        al, _, reason = decide("TLS-sys", {"TLS-sys"}, BASE, [ai(email="x@evil.example")])
        self.assertEqual(al, BASE)
        self.assertEqual(reason, "no AI-authored commits")

    def test_commit_with_a_github_account_is_not_exempted(self):
        al, _, _ = decide("TLS-sys", {"TLS-sys"}, BASE, [ai(login="impostor")])
        self.assertEqual(al, BASE)

    def test_human_only_pr_unchanged(self):
        al, exempted, _ = decide("TLS-sys", {"TLS-sys"}, BASE, [human()])
        self.assertEqual((al, exempted), (BASE, []))

    def test_other_unsigned_human_commits_are_not_exempted(self):
        # Only the single AI identity is added; the bot still flags the other author.
        al, _, _ = decide("TLS-sys", {"TLS-sys"}, BASE, [ai(), human("stranger")])
        self.assertEqual(al, BASE + ",Claude")
        self.assertNotIn("stranger", al)

    def test_empty_base_allowlist(self):
        al, _, _ = decide("a", {"a"}, "", [ai()])
        self.assertEqual(al, "Claude")


if __name__ == "__main__":
    unittest.main()
