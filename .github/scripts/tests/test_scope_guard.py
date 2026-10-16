"""Unit tests for the scope guard's maintainer-approval marker."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scope_guard.py"
FLAGGED = "  options: 25 mm band"


def run_guard(content: str, assoc: str, name: str = "data.yaml"):
    """Run scope_guard.py on one file; return (exit code, stdout, summary text)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / name).write_text(content, encoding="utf-8")
        (tmp_path / "changed.txt").write_text(name + "\n", encoding="utf-8")
        summary = tmp_path / "summary.md"
        env = {k: v for k, v in os.environ.items() if k != "AUTHOR_ASSOCIATION"}
        env["GITHUB_STEP_SUMMARY"] = str(summary)
        if assoc is not None:
            env["AUTHOR_ASSOCIATION"] = assoc
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "changed.txt"],
            cwd=tmp, env=env, capture_output=True, text=True,
        )
        text = summary.read_text(encoding="utf-8") if summary.exists() else ""
        return proc.returncode, proc.stdout, text


class ScopeGuardMarker(unittest.TestCase):
    def test_no_marker_fails(self):
        code, out, _ = run_guard(FLAGGED + "\n", "OWNER")
        self.assertEqual(code, 1)
        self.assertIn("engineering unit", out)

    def test_clean_file_passes(self):
        code, _, _ = run_guard("name: supplier list\n", "NONE")
        self.assertEqual(code, 0)

    def test_marker_from_maintainer_passes_and_is_listed(self):
        line = FLAGGED + "  # scope-ok: size bands for capacity mapping, no specs\n"
        for assoc in ("OWNER", "MEMBER", "COLLABORATOR"):
            with self.subTest(assoc=assoc):
                code, _, summary = run_guard(line, assoc)
                self.assertEqual(code, 0)
                self.assertIn("data.yaml", summary)
                self.assertIn("| 1 |", summary)
                self.assertIn("size bands for capacity mapping", summary)

    def test_marker_from_non_maintainer_fails(self):
        line = FLAGGED + "  # scope-ok: size bands for capacity mapping, no specs\n"
        for assoc in ("CONTRIBUTOR", "FIRST_TIME_CONTRIBUTOR", "NONE", ""):
            with self.subTest(assoc=assoc):
                code, out, _ = run_guard(line, assoc)
                self.assertEqual(code, 1)
                self.assertIn("approval marker added by non-maintainer", out)

    def test_missing_association_fails_closed(self):
        line = FLAGGED + "  # scope-ok: size bands for capacity mapping, no specs\n"
        code, out, _ = run_guard(line, None)
        self.assertEqual(code, 1)
        self.assertIn("non-maintainer", out)

    def test_short_or_empty_reason_fails(self):
        for reason in ("", "ok", "too short", "         "):
            with self.subTest(reason=reason):
                code, out, _ = run_guard(FLAGGED + "  # scope-ok:" + reason + "\n", "OWNER")
                self.assertEqual(code, 1)
                self.assertIn("at least 10 characters", out)

    def test_marker_is_case_insensitive_and_only_covers_its_own_line(self):
        content = FLAGGED + "  # SCOPE-OK: size bands for capacity mapping\n" + FLAGGED + "\n"
        code, out, _ = run_guard(content, "OWNER")
        self.assertEqual(code, 1)
        self.assertIn("data.yaml:2: number with engineering unit", out)
        self.assertNotIn("data.yaml:1: number with engineering unit", out)


if __name__ == "__main__":
    unittest.main()
