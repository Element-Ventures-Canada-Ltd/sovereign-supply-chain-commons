# Handling: Unclassified — working
"""Unit tests for the SOI Graph Agents. Run: python3 -m unittest discover -s Agents/tests"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import checks  # noqa: E402
import soi_graph_agents as scout  # noqa: E402

H = "Handling: Unclassified — working\n"


class FileChecks(unittest.TestCase):
    def run_file(self, path, text):
        r = checks.Result()
        checks.check_file(path, text, r)
        return {f.code for f in r.findings}, r

    def test_clean_markdown_passes(self):
        codes, _ = self.run_file("docs/a.md", H + "Supplier mapping notes.")
        self.assertEqual(codes, set())

    def test_missing_marker(self):
        codes, r = self.run_file("docs/a.md", "No marker here.")
        self.assertIn("handling-marker", codes)
        self.assertIn("handling-review", r.labels)

    def test_scope_unit_and_term_in_data(self):
        codes, r = self.run_file("data/x.csv", "part,value\nimpeller,12000 rpm\npump,mass flow 3\n")
        self.assertTrue({"scope-unit", "scope-term"} <= codes)
        self.assertIn("scope-review", r.labels)

    def test_scope_terms_ignored_in_prose(self):
        codes, _ = self.run_file("docs/policy.md", H + "Do not submit tolerance or torque data.")
        self.assertNotIn("scope-term", codes)

    def test_licence_contamination(self):
        codes, _ = self.run_file("data/y.yaml", "licence: CC-BY-NC-4.0\n")
        self.assertIn("licence-contamination", codes)

    def test_personal_info_field(self):
        codes, _ = self.run_file("data/p.csv", "name,date_of_birth\n")
        self.assertIn("personal-info", codes)


class PrChecks(unittest.TestCase):
    def test_external_without_cla_or_dco(self):
        r = checks.Result()
        checks.check_pr("no boxes", "CONTRIBUTOR", ["fix thing"], ["docs/a.md"], r)
        codes = {f.code for f in r.findings}
        self.assertTrue({"cla-box", "dco"} <= codes)
        self.assertTrue(r.needs_review)

    def test_external_compliant(self):
        r = checks.Result()
        body = "- [x] I agree to the Contributor License Agreement (CLA.md)"
        checks.check_pr(body, "CONTRIBUTOR", ["x\n\nSigned-off-by: A B <a@b.c>"], ["docs/a.md"], r)
        self.assertFalse(r.needs_review)

    def test_maintainer_exempt_from_cla(self):
        r = checks.Result()
        checks.check_pr("", "OWNER", ["no sign-off"], [".github/workflows/x.yml"], r)
        self.assertFalse(r.needs_review)

    def test_external_workflow_change(self):
        r = checks.Result()
        body = "- [x] I agree to the Contributor License Agreement"
        checks.check_pr(body, "NONE", ["Signed-off-by: A <a@b.c>"], [".github/workflows/ci.yml"], r)
        self.assertIn("protected-path", {f.code for f in r.findings})

    def test_provenance_required(self):
        r = checks.Result()
        checks.check_data_provenance(["Connectors/zz-new/sample.csv"], r)
        self.assertIn("provenance-missing", {f.code for f in r.findings})
        r2 = checks.Result()
        checks.check_data_provenance(["Connectors/zz-new/sample.csv", "Connectors/zz-new/provenance.yaml"], r2)
        self.assertEqual(r2.findings, [])


class TextSignals(unittest.TestCase):
    def codes(self, text):
        r = checks.Result()
        checks.check_text_signals(text, "comment", r)
        return {f.code for f in r.findings}

    def test_claim_only(self):
        self.assertIn("claim-only", self.codes("/take"))
        self.assertIn("claim-only", self.codes("Please assign it to me"))

    def test_long_proposal_not_claim_only(self):
        self.assertNotIn("claim-only", self.codes("I'd like to work on this. " + "Plan detail. " * 40))

    def test_payment(self):
        self.assertIn("payment-ask", self.codes("What is your PayPal? payment on merge?"))

    def test_ai_disclosure(self):
        self.assertIn("ai-disclosure", self.codes("This PR was AI-assisted."))


class FeedAgent(unittest.TestCase):
    WL = {"feeds": [
        {"id": "f1", "checks": [{"label": "page", "kind": "page", "url": "https://a.example/p", "must_contain": ["Open Government Licence"]}]},
        {"id": "f2", "checks": [{"label": "cat", "kind": "ckan", "url": "https://b.example/c", "expect_licence": "ca-ogl-lgo"}]},
        {"id": "f3", "checks": [{"label": "fr", "kind": "fedreg", "url": "https://c.example/fr"}]},
        {"id": "f4", "checks": [{"label": "dataset", "kind": "data", "url": "https://d.example/d.json"}]},
    ]}

    def fake(self, pages):
        def fetch(url, method="GET", max_bytes=0, headers=None):
            spec = pages[url]
            if spec is None:
                return {"status": 0, "final_url": url, "headers": {}, "body": b"", "error": "URLError"}
            return {"status": spec.get("status", 200), "final_url": spec.get("final", url),
                    "headers": spec.get("headers", {}), "body": spec.get("body", b"")}
        return fetch

    def pages(self, licence="ca-ogl-lgo", newest="2026-1", phrase=True, d_up=True, etag="a"):
        return {
            "https://a.example/p": {"body": b"<p>Open Government Licence v3</p>" if phrase else b"<p>Other</p>"},
            "https://b.example/c": {"body": json.dumps({"result": {"license_id": licence, "metadata_modified": "m1", "resources": []}}).encode()},
            "https://c.example/fr": {"body": json.dumps({"count": 1, "results": [{"document_number": newest, "title": "T", "publication_date": "2026-10-01"}]}).encode()},
            "https://d.example/d.json": {"headers": {"etag": etag}} if d_up else None,
        }

    def test_baseline_then_changes(self):
        state, ev = scout.run_feeds(self.WL, {}, self.fake(self.pages()))
        self.assertEqual([e for e in ev if e["severity"] != "info"], [])
        state2, ev2 = scout.run_feeds(self.WL, state, self.fake(self.pages(licence="other", newest="2026-2", etag="b")))
        msgs = {(e["feed"], e["severity"]) for e in ev2}
        self.assertIn(("f2", "alert"), msgs)   # licence changed
        self.assertIn(("f3", "alert"), msgs)   # new Federal Register document
        self.assertIn(("f4", "info"), msgs)    # new publication (etag)

    def test_phrase_missing_alerts(self):
        _, ev = scout.run_feeds(self.WL, {}, self.fake(self.pages(phrase=False)))
        self.assertTrue(any(e["feed"] == "f1" and e["severity"] == "alert" for e in ev))

    def test_down_warns_then_alerts(self):
        s1, ev1 = scout.run_feeds(self.WL, {}, self.fake(self.pages(d_up=False)))
        self.assertTrue(any(e["feed"] == "f4" and e["severity"] == "warn" for e in ev1))
        _, ev2 = scout.run_feeds(self.WL, s1, self.fake(self.pages(d_up=False)))
        self.assertTrue(any(e["feed"] == "f4" and e["severity"] == "alert" for e in ev2))

    def test_throttled_and_bot_protected_are_not_down(self):
        self.assertTrue(scout.is_ok({"status": 429}))
        self.assertTrue(scout.is_ok({"status": 403, "bot_protected": True}))
        self.assertFalse(scout.is_ok({"status": 403}))
        self.assertFalse(scout.is_ok({"status": 0}))

    def test_state_roundtrip_and_report(self):
        state, ev = scout.run_feeds(self.WL, {}, self.fake(self.pages()))
        body = scout.render_feeds_report(self.WL, state, ev, True) + scout.pack_state(state)
        self.assertEqual(scout.unpack_state(body), json.loads(json.dumps(state)))
        self.assertIn("Handling:", body)

    def test_watchlist_ids_match_registry_when_present(self):
        root = Path(__file__).resolve().parents[2]
        wl = scout.load_watchlist(str(root / "Agents" / "feed-watchlist.yaml"))
        reg_path = root / "Survey" / "data-feeds" / "feed-registry.yaml"
        if not reg_path.exists():
            self.skipTest("feed registry not merged yet")
        import yaml
        reg_ids = {f["id"] for f in yaml.safe_load(reg_path.read_text())["feeds"]}
        unknown = {f["id"] for f in wl["feeds"]} - reg_ids - {"bis-affiliates-rule"}
        self.assertEqual(unknown, set())


class FakeGH:
    repo = "o/r"

    def __init__(self, files, commits, texts, labels):
        self.files, self.commits, self.texts, self.labels, self.posted = files, commits, texts, labels, []

    def paged(self, path):
        return self.files if path.endswith("/files") else self.commits

    def file_text(self, path, ref):
        return self.texts.get(path)

    def label_names(self):
        return self.labels

    def req(self, method, path, data=None):
        self.posted.append((method, path, data))


class ContributionAgent(unittest.TestCase):
    def test_pr_flow_labels_only_existing(self):
        gh = FakeGH(
            files=[{"filename": "data/x.csv", "status": "added"}],
            commits=[{"commit": {"message": "add"}}],
            texts={"data/x.csv": "part\nshaft 40 mm\n"},
            labels={"agent:review", "scope-review"},
        )
        event = {"pull_request": {"number": 7, "body": "", "author_association": "NONE", "head": {"sha": "abc"}}}
        r = scout.run_contributions("pull_request_target", event, gh)
        self.assertTrue(r.needs_review)
        self.assertEqual(len(gh.posted), 1)
        method, path, data = gh.posted[0]
        self.assertEqual((method, path), ("POST", "/repos/o/r/issues/7/labels"))
        self.assertEqual(set(data["labels"]), {"agent:review", "scope-review"})

    def test_maintainer_comment_ignored(self):
        gh = FakeGH([], [], {}, {"agent:claim-only"})
        event = {"issue": {"number": 3}, "comment": {"body": "/take", "author_association": "OWNER", "user": {"type": "User"}}}
        r = scout.run_contributions("issue_comment", event, gh)
        self.assertEqual(r.findings, [])
        self.assertEqual(gh.posted, [])


if __name__ == "__main__":
    unittest.main()
