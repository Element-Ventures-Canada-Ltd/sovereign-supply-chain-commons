# Handling: Unclassified — working
"""Unit tests for which review threads may be resolved automatically."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from resolve_review_threads import auto_resolvable, rules_cited, select  # noqa: E402

NIT = "**Nit (REVIEW.md rule 6):** a typo in a log line."
IMPORTANT = "**Important (REVIEW.md rule 6):** off-by-one."
GUARD = "Nit (REVIEW.md rule 4): something about a guard."
SEC = "Security, LOW: an exploit path. The fix."
FILES = ["a.py", "b.py"]


def thread(tid, path, body, login="github-actions", resolved=False, outdated=True):
    return {"id": tid, "path": path, "isResolved": resolved, "isOutdated": outdated,
            "comments": {"nodes": [{"author": {"login": login}, "body": body}]}}


class AutoResolvable(unittest.TestCase):
    def test_nit_outside_rules_1_to_5(self):
        for body in (NIT, "Nit (rule 7): x", "> **Nit** rules 6 and 7: x"):
            self.assertTrue(auto_resolvable(body), body)

    def test_never_important_preexisting_or_security(self):
        for body in (IMPORTANT, "Pre-existing (rule 6): x", SEC, "**Security, HIGH:** x"):
            self.assertFalse(auto_resolvable(body), body)

    def test_never_nit_under_rules_1_to_5(self):
        for body in (GUARD, "Nit (rules 6, 3): x", "Nit (rules 1-7): x", "Nit (rule 5): x"):
            self.assertFalse(auto_resolvable(body), body)

    def test_never_without_a_rule_or_unparseable(self):
        for body in ("Nit: no rule", "", None, "Nitpick (rule 6)", "Nit (rules 6-900): x"):
            self.assertFalse(auto_resolvable(body), body)

    def test_rule_ranges_expand(self):
        self.assertEqual(rules_cited("rules 2–4"), {2, 3, 4})


class Select(unittest.TestCase):
    def test_resolves_outdated_nit_in_clean_file(self):
        self.assertEqual(select([thread("t1", "a.py", NIT)], [], FILES), ["t1"])

    def test_keeps_thread_when_line_unchanged(self):
        self.assertEqual(select([thread("t1", "a.py", NIT, outdated=False)], [], FILES), [])
        self.assertEqual(select([thread("t2", "a.py", NIT, outdated=None)], [], FILES), [])

    def test_keeps_thread_while_any_finding_remains_in_file(self):
        findings = [{"path": "./a.py", "line": 9, "tag": "Nit"}]
        self.assertEqual(select([thread("t1", "a.py", NIT)], findings, FILES), [])

    def test_never_resolves_important_even_if_silent_and_outdated(self):
        self.assertEqual(select([thread("t1", "a.py", IMPORTANT)], [], FILES), [])

    def test_never_resolves_security_or_guard_threads(self):
        threads = [thread("t1", "a.py", SEC), thread("t2", "b.py", GUARD)]
        self.assertEqual(select(threads, [], FILES), [])

    def test_never_resolves_human_or_other_bot_thread(self):
        threads = [thread("t1", "a.py", NIT, login="TLS-sys"),
                   thread("t2", "a.py", NIT, login="someone[bot]")]
        self.assertEqual(select(threads, [], FILES), [])

    def test_skips_already_resolved_and_empty(self):
        threads = [thread("t1", "a.py", NIT, resolved=True),
                   {"id": "t2", "path": "a.py", "isResolved": False, "isOutdated": True,
                    "comments": {"nodes": []}}]
        self.assertEqual(select(threads, [], FILES), [])

    def test_other_files_unaffected_by_open_finding(self):
        threads = [thread("t1", "a.py", NIT), thread("t2", "b.py", NIT)]
        findings = [{"path": "a.py", "line": 1, "tag": "Important"}]
        self.assertEqual(select(threads, findings, FILES), ["t2"])

    def test_any_unrecognised_finding_path_resolves_nothing(self):
        threads = [thread("t1", "a.py", NIT), thread("t2", "b.py", NIT)]
        for bad in ("/a.py", "A.py", "a.py ", "b/a.py", "/home/runner/work/x/a.py", None, "c.py"):
            findings = [{"path": bad, "line": 1, "tag": "Nit"}]
            self.assertEqual(select(threads, findings, FILES), [], repr(bad))


if __name__ == "__main__":
    unittest.main()
