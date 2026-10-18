# Handling: Unclassified — working
"""Unit tests for which review threads may be resolved automatically."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from resolve_review_threads import reviewer_of, select  # noqa: E402


def thread(tid, path, body, login="github-actions", resolved=False):
    return {"id": tid, "path": path, "isResolved": resolved,
            "comments": {"nodes": [{"author": {"login": login}, "body": body}]}}


CODE = "**Important (REVIEW.md rule 4):** something"
SEC = "Security, MEDIUM: an exploit path. The fix."


class ReviewerOf(unittest.TestCase):
    def test_code_tags(self):
        for body in ("Important: x", "**Nit** x", "Pre-existing: x", "> **Important** x"):
            self.assertEqual(reviewer_of(body), "code", body)

    def test_security_tag(self):
        self.assertEqual(reviewer_of(SEC), "security")
        self.assertEqual(reviewer_of("**Security, HIGH:** x"), "security")

    def test_unknown(self):
        for body in ("", None, "Looks good", "Importantly, x", "Nitpick"):
            self.assertIsNone(reviewer_of(body), body)


class Select(unittest.TestCase):
    def test_resolves_own_thread_when_file_is_clean(self):
        self.assertEqual(select([thread("t1", "a.py", CODE)], "code", []), ["t1"])

    def test_keeps_thread_while_any_finding_remains_in_file(self):
        findings = [{"path": "./a.py", "line": 9, "tag": "Nit"}]
        self.assertEqual(select([thread("t1", "a.py", CODE)], "code", findings), [])

    def test_open_medium_security_thread_keeps_blocking(self):
        findings = [{"path": "a.py", "line": 3, "severity": "MEDIUM"}]
        self.assertEqual(select([thread("t1", "a.py", SEC)], "security", findings), [])

    def test_never_resolves_other_reviewers_thread(self):
        threads = [thread("t1", "a.py", SEC), thread("t2", "b.py", CODE)]
        self.assertEqual(select(threads, "code", []), ["t2"])
        self.assertEqual(select(threads, "security", []), ["t1"])

    def test_never_resolves_human_thread(self):
        threads = [thread("t1", "a.py", CODE, login="TLS-sys"),
                   thread("t2", "a.py", CODE, login="someone[bot]")]
        self.assertEqual(select(threads, "code", []), [])

    def test_skips_already_resolved_and_empty(self):
        threads = [thread("t1", "a.py", CODE, resolved=True),
                   {"id": "t2", "path": "a.py", "isResolved": False, "comments": {"nodes": []}}]
        self.assertEqual(select(threads, "code", []), [])

    def test_other_files_unaffected_by_open_finding(self):
        threads = [thread("t1", "a.py", CODE), thread("t2", "b.py", CODE)]
        findings = [{"path": "a.py", "line": 1, "tag": "Important"}]
        self.assertEqual(select(threads, "code", findings), ["t2"])


if __name__ == "__main__":
    unittest.main()
