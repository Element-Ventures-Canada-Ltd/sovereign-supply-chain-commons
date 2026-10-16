# Handling: Unclassified — working
import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import red_zone_gate as g  # noqa: E402
from red_zone_gate import is_red, parse_codeowners  # noqa: E402

CODEOWNERS = """
# comment
*                                   @TLS-sys
/Dashboard/
/Engagement/
/Survey/
/examples/
/Dashboard/openchokepoint.pin       @TLS-sys
**/requirements*.txt                @TLS-sys
**/pyproject.toml                   @TLS-sys
**/package.json                     @TLS-sys
**/package-lock.json                @TLS-sys
/Survey/data-feeds/                 @TLS-sys
/Survey/CONSENT.md                  @TLS-sys
/Survey/GOVERNANCE.md               @TLS-sys
**/manifest*.yaml                   @TLS-sys
**/manifest*.yml                    @TLS-sys
/.github/                           @TLS-sys
/Agents/                            @TLS-sys
/CLAUDE.md                          @TLS-sys
**/CLAUDE.md                        @TLS-sys
"""
RULES = parse_codeowners(CODEOWNERS)
REPO = "example-org/example-repo"
SHA = "a" * 40
NEW_SHA = "b" * 40
RUN = "https://github.com/example-org/example-repo/actions/runs/1"


class Zones(unittest.TestCase):
    def assertZone(self, path, red):
        self.assertEqual(is_red(path, RULES), red, path)

    def test_green_areas(self):
        for p in ["Dashboard/build.py", "Dashboard/tests/test_build.py", "Engagement/x.md",
                  "Survey/README.md", "examples/synthetic-turbopump-chain/a.yaml"]:
            self.assertZone(p, False)

    def test_red_default_and_root(self):
        for p in ["CLA.md", "README.md", "adapters/vendor-x/SPEC.md", "newdir/file.py", "LICENSE"]:
            self.assertZone(p, True)

    def test_red_inside_green(self):
        for p in ["Dashboard/openchokepoint.pin", "Dashboard/requirements.txt",
                  "Survey/tools/requirements-dev.txt", "Survey/data-feeds/BLUEPRINT.md",
                  "Survey/CONSENT.md", "Survey/GOVERNANCE.md", "Dashboard/pyproject.toml",
                  "Survey/connectors/manifest.yaml", "Dashboard/CLAUDE.md"]:
            self.assertZone(p, True)

    def test_guardrails_red(self):
        for p in [".github/CODEOWNERS", ".github/workflows/cla.yml", "Agents/checks.py", "CLAUDE.md"]:
            self.assertZone(p, True)

    def test_unmatched_is_red(self):
        self.assertTrue(is_red("anything", parse_codeowners("/Dashboard/\n")))

    def test_dir_pattern_not_prefix_match(self):
        self.assertZone("DashboardX/file.py", True)
        self.assertZone("SurveyOld/file.md", True)

    def test_always_red_even_if_codeowners_says_green(self):
        loose = parse_codeowners("*\n")  # a CODEOWNERS that owns nothing
        self.assertEqual(g.red_paths([".github/workflows/x.yml", "Dashboard/CODEOWNERS",
                                      "Dashboard/a.py"], loose),
                         [".github/workflows/x.yml", "Dashboard/CODEOWNERS"])

    def test_marked_red(self):
        self.assertTrue(g.marked_red("[RED] Fix", ""))
        self.assertTrue(g.marked_red("Fix", "Replaces [RED] work"))
        self.assertFalse(g.marked_red("Fix red text", None))


class Comment(unittest.TestCase):
    def test_paths_are_escaped(self):
        body = g.render_comment("pending", ["Dashboard/<img src=x onerror=alert(1)>`.md"],
                                False, SHA, RUN)
        self.assertNotIn("<img", body)
        self.assertNotIn("`.md", body)
        self.assertIn("&lt;img", body)
        self.assertEqual(body.count(g.MARKER), 1)

    def test_non_https_run_link_dropped(self):
        self.assertNotIn("javascript:", g.render_comment("green", [], False, SHA, "javascript:x"))

    def test_long_list_is_capped(self):
        body = g.render_comment("pending", [f"r/{i}" for i in range(80)], False, SHA)
        self.assertIn("and 30 more", body)


class Approver(unittest.TestCase):
    PERM = {"permission": "admin", "user": {"id": g.OWNER_ID}}

    def test_owner_with_admin(self):
        self.assertIsNone(g.approver_problem("TLS-sys", g.OWNER_ID, self.PERM))

    def test_other_login(self):
        self.assertIn("not TLS-sys", g.approver_problem("someone", 1, self.PERM))

    def test_right_login_wrong_id(self):
        self.assertIsNotNone(g.approver_problem("TLS-sys", 42, self.PERM))

    def test_write_is_not_enough(self):
        self.assertIsNotNone(g.approver_problem("TLS-sys", g.OWNER_ID,
                                                {"permission": "write", "user": {"id": g.OWNER_ID}}))

    def test_no_permission_record(self):
        self.assertIsNotNone(g.approver_problem("TLS-sys", g.OWNER_ID, None))


class FakeGitHub:
    """In-memory stand-in for the GitHub API, recording every write."""

    def __init__(self, files, title="Change", labels=(), auto_merge=None, fork=False,
                 draft=False, state="open", sha=SHA):
        self.repo = REPO
        self.files = list(files)
        self.pr = {
            "number": 7, "state": state, "title": title, "body": "", "draft": draft,
            "node_id": "PR_node", "auto_merge": auto_merge,
            "head": {"sha": sha, "repo": {"full_name": "someone/fork" if fork else REPO}},
            "labels": [{"name": n} for n in labels],
        }
        self.status_log = {}  # sha -> list newest first
        self.comment_list = []
        self.calls = []
        self.perms = {"TLS-sys": {"permission": "admin", "user": {"id": g.OWNER_ID}}}
        self.fail_on = set()

    def _maybe_fail(self, name):
        self.calls.append(name)
        if name in self.fail_on:
            raise g.ApiError(f"{name} failed")

    def get_pr(self, n):
        self._maybe_fail("get_pr")
        return self.pr

    def pr_files(self, n):
        self._maybe_fail("pr_files")
        return self.files

    def labels(self):
        return {l["name"] for l in self.pr["labels"]}

    def add_label(self, n, name):
        self._maybe_fail("add_label")
        self.pr["labels"].append({"name": name})

    def remove_label(self, n, name):
        self._maybe_fail("remove_label")
        self.pr["labels"] = [l for l in self.pr["labels"] if l["name"] != name]

    def ensure_label(self, *a):
        self._maybe_fail("ensure_label")

    def statuses(self, sha):
        return self.status_log.get(sha, [])

    def set_status(self, sha, state, description, target_url=""):
        self._maybe_fail(f"status:{state}")
        self.status_log.setdefault(sha, []).insert(0, {
            "context": g.CONTEXT, "state": state, "description": description,
            "creator": {"login": g.BOT}, "created_at": "2026-10-16T12:00:00Z"})

    def latest(self, sha=SHA):
        return self.status_log.get(sha, [{}])[0]

    def comments(self, n):
        return self.comment_list

    def create_comment(self, n, body):
        self.calls.append("create_comment")
        self.comment_list.append({"id": len(self.comment_list) + 1, "body": body,
                                  "user": {"login": g.BOT}})

    def update_comment(self, cid, body):
        self.calls.append("update_comment")
        next(c for c in self.comment_list if c["id"] == cid)["body"] = body

    def permission(self, login):
        return self.perms.get(login)

    def set_auto_merge(self, node_id, enable):
        self._maybe_fail(f"auto_merge:{enable}")
        self.pr["auto_merge"] = {"merge_method": "squash"} if enable else None

    def bot_comments(self):
        return [c for c in self.comment_list if g.MARKER in c["body"]]


def gate(gh, action="opened"):
    return g.cmd_gate(gh, 7, RULES, action, RUN)


def approve(gh, login="TLS-sys", uid=g.OWNER_ID, event_sha=SHA):
    return g.cmd_approve(gh, 7, RULES, RUN, login, uid, event_sha,
                         now=dt.datetime(2026, 10, 16, 12, 0, tzinfo=dt.timezone.utc))


class Gate(unittest.TestCase):
    def test_red_pr_is_pending_not_failed(self):
        gh = FakeGitHub(["Dashboard/a.py", "Agents/x.py"])
        self.assertEqual(gate(gh), 0)
        self.assertEqual(gh.latest()["state"], "pending")
        self.assertIn("zone:red", gh.labels())
        self.assertNotIn("zone:green", gh.labels())
        self.assertEqual(len(gh.bot_comments()), 1)
        self.assertIn("Agents/x.py", gh.bot_comments()[0]["body"])

    def test_title_marked_red_is_red(self):
        gh = FakeGitHub(["Dashboard/a.py"], title="[RED] tweak")
        gate(gh)
        self.assertEqual(gh.latest()["state"], "pending")

    def test_green_pr_is_success(self):
        gh = FakeGitHub(["Dashboard/a.py"], labels=["zone:red"])
        self.assertEqual(gate(gh), 0)
        self.assertEqual(gh.latest()["state"], "success")
        self.assertNotIn("zone:red", gh.labels())
        self.assertIn("zone:green", gh.labels())

    def test_comment_updated_in_place_never_repeated(self):
        gh = FakeGitHub([".github/workflows/x.yml"])
        gate(gh)
        gh.pr["head"]["sha"] = NEW_SHA
        gate(gh, "synchronize")
        gate(gh, "edited")
        self.assertEqual(len(gh.comment_list), 1)
        self.assertEqual(gh.calls.count("create_comment"), 1)
        self.assertIn("update_comment", gh.calls)

    def test_unchanged_comment_is_not_rewritten(self):
        gh = FakeGitHub(["Agents/x.py"])
        gate(gh)
        gate(gh, "edited")
        self.assertNotIn("update_comment", gh.calls)

    def test_marker_in_someone_elses_comment_is_ignored(self):
        gh = FakeGitHub(["Agents/x.py"])
        gh.comment_list.append({"id": 99, "body": g.MARKER + " fake", "user": {"login": "mallory"}})
        gate(gh)
        self.assertEqual(gh.comment_list[0]["body"], g.MARKER + " fake")
        self.assertEqual(gh.calls.count("create_comment"), 1)

    def test_unapproved_red_pr_loses_auto_merge(self):
        gh = FakeGitHub(["Agents/x.py"], auto_merge={"merge_method": "squash"})
        gate(gh)
        self.assertIsNone(gh.pr["auto_merge"])

    def test_push_clears_approval(self):
        gh = FakeGitHub(["Agents/x.py"])
        gate(gh)
        gh.pr["labels"].append({"name": g.APPROVED_LABEL})
        approve(gh)
        self.assertEqual(gh.latest()["state"], "success")
        gh.pr["head"]["sha"] = NEW_SHA  # new commit pushed
        gate(gh, "synchronize")
        self.assertNotIn(g.APPROVED_LABEL, gh.labels())
        self.assertEqual(gh.latest(NEW_SHA)["state"], "pending")
        self.assertIn("earlier approval was cleared", gh.bot_comments()[0]["body"])

    def test_edit_keeps_valid_approval(self):
        gh = FakeGitHub(["Agents/x.py"], labels=[g.APPROVED_LABEL])
        approve(gh)
        gate(gh, "edited")
        self.assertEqual(gh.latest()["state"], "success")
        self.assertIn("Status: approved", gh.bot_comments()[0]["body"])

    def test_label_without_recorded_approval_stays_pending(self):
        gh = FakeGitHub(["Agents/x.py"], labels=[g.APPROVED_LABEL])
        gate(gh, "reopened")
        self.assertEqual(gh.latest()["state"], "pending")
        self.assertIn("Remove the label and add it again", gh.bot_comments()[0]["body"])

    def test_spoofed_status_not_from_bot_is_not_an_approval(self):
        gh = FakeGitHub(["Agents/x.py"], labels=[g.APPROVED_LABEL])
        gh.status_log[SHA] = [{"context": g.CONTEXT, "state": "success",
                               "description": g.APPROVED_PREFIX + "aaaaaaa",
                               "creator": {"login": "mallory"}}]
        gate(gh, "edited")
        self.assertEqual(gh.latest()["state"], "pending")

    def test_api_error_is_a_real_failure(self):
        gh = FakeGitHub(["Agents/x.py"])
        gh.fail_on.add("pr_files")
        with self.assertRaises(g.ApiError):
            gate(gh)

    def test_main_returns_1_on_api_error(self):
        gh = FakeGitHub(["Agents/x.py"])
        gh.fail_on.add("get_pr")
        env = {"PR_NUMBER": "7", "EVENT_ACTION": "opened"}
        old = dict(g.os.environ)
        g.os.environ.update(env)
        try:
            cwd = Path.cwd()
            g.os.chdir(Path(__file__).resolve().parents[3])  # repo root, for CODEOWNERS
            self.assertEqual(g.main(["gate"], gh=gh), 1)
        finally:
            g.os.chdir(cwd)
            g.os.environ.clear()
            g.os.environ.update(old)

    def test_missing_codeowners_fails_closed(self):
        cwd = Path.cwd()
        g.os.chdir(Path(__file__).resolve().parent)  # no .github/CODEOWNERS here
        try:
            self.assertEqual(g.main(["gate"], gh=FakeGitHub(["a"])), 1)
        finally:
            g.os.chdir(cwd)


class Approve(unittest.TestCase):
    def test_owner_approval_records_commit_and_enables_auto_merge(self):
        gh = FakeGitHub(["Agents/x.py"], labels=[g.APPROVED_LABEL])
        self.assertEqual(approve(gh), 0)
        self.assertEqual(gh.latest()["state"], "success")
        self.assertEqual(gh.latest()["description"], g.APPROVED_PREFIX + SHA[:7])
        self.assertEqual(gh.pr["auto_merge"], {"merge_method": "squash"})
        self.assertLess(gh.calls.index("auto_merge:True"), gh.calls.index("status:success"))
        self.assertIn(SHA, gh.bot_comments()[0]["body"])

    def test_other_person_is_refused(self):
        gh = FakeGitHub(["Agents/x.py"], labels=[g.APPROVED_LABEL])
        gh.perms["helper"] = {"permission": "admin", "user": {"id": 5}}
        approve(gh, login="helper", uid=5)
        self.assertNotIn(g.APPROVED_LABEL, gh.labels())
        self.assertEqual(gh.latest()["state"], "pending")
        self.assertIsNone(gh.pr["auto_merge"])
        self.assertIn("refused", gh.bot_comments()[0]["body"])

    def test_owner_without_admin_is_refused(self):
        gh = FakeGitHub(["Agents/x.py"], labels=[g.APPROVED_LABEL])
        gh.perms["TLS-sys"] = {"permission": "write", "user": {"id": g.OWNER_ID}}
        approve(gh)
        self.assertEqual(gh.latest()["state"], "pending")

    def test_lookalike_account_is_refused(self):
        gh = FakeGitHub(["Agents/x.py"], labels=[g.APPROVED_LABEL])
        approve(gh, uid=123)
        self.assertEqual(gh.latest()["state"], "pending")

    def test_label_on_old_commit_is_refused(self):
        gh = FakeGitHub(["Agents/x.py"], labels=[g.APPROVED_LABEL], sha=NEW_SHA)
        approve(gh, event_sha=SHA)
        self.assertNotIn(g.APPROVED_LABEL, gh.labels())
        self.assertEqual(gh.latest(NEW_SHA)["state"], "pending")
        self.assertNotIn("status:success", gh.calls)

    def test_fork_is_approved_but_not_auto_merged(self):
        gh = FakeGitHub(["Agents/x.py"], labels=[g.APPROVED_LABEL], fork=True)
        approve(gh)
        self.assertEqual(gh.latest()["state"], "success")
        self.assertNotIn("auto_merge:True", gh.calls)
        self.assertIn("forks never auto-merge", gh.bot_comments()[0]["body"])

    def test_auto_merge_failure_still_records_approval(self):
        gh = FakeGitHub(["Agents/x.py"], labels=[g.APPROVED_LABEL])
        gh.fail_on.add("auto_merge:True")
        self.assertEqual(approve(gh), 0)
        self.assertEqual(gh.latest()["state"], "success")

    def test_closed_pr_is_ignored(self):
        gh = FakeGitHub(["Agents/x.py"], labels=[g.APPROVED_LABEL], state="closed")
        approve(gh)
        self.assertEqual(gh.status_log, {})

    def test_revoke_returns_to_pending(self):
        gh = FakeGitHub(["Agents/x.py"], labels=[g.APPROVED_LABEL])
        approve(gh)
        gh.remove_label(7, g.APPROVED_LABEL)
        g.cmd_revoke(gh, 7, RULES, RUN)
        self.assertEqual(gh.latest()["state"], "pending")
        self.assertIsNone(gh.pr["auto_merge"])
        self.assertIn("withdrawn", gh.bot_comments()[0]["body"])

    def test_classify_writes_output(self):
        import tempfile
        with tempfile.NamedTemporaryFile("r+", suffix=".txt") as fh:
            old = g.os.environ.get("GITHUB_OUTPUT")
            g.os.environ["GITHUB_OUTPUT"] = fh.name
            try:
                g.cmd_classify(FakeGitHub(["Agents/x.py"]), 7, RULES)
                g.cmd_classify(FakeGitHub(["Dashboard/a.py"]), 7, RULES)
            finally:
                if old is None:
                    del g.os.environ["GITHUB_OUTPUT"]
                else:
                    g.os.environ["GITHUB_OUTPUT"] = old
            self.assertEqual(fh.read(), "red=true\nred=false\n")


if __name__ == "__main__":
    unittest.main()
