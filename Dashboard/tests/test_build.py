#!/usr/bin/env python3
# Handling: Unclassified — working
# SPDX-License-Identifier: Apache-2.0
"""Tests for Dashboard/build.py. Standard library unittest plus PyYAML (required by the SDK).

Needs an OpenChokepoint checkout at the pinned commit: set OPENCHOKEPOINT_ROOT, or place it
at ../openchokepoint next to this repository. CI does this automatically.

Run:  python3 -m unittest discover -s Dashboard/tests -v

Fixtures are invented: fictional names and identifiers on the reserved example.org domain.
"""
import copy
import datetime
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("dashboard_build", HERE.parent / "build.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)

ROOT = B.resolve_root(os.environ.get("OPENCHOKEPOINT_ROOT"))
B.check_pin(ROOT, allow_unpinned=False)  # tests run against the pinned SDK only
SDK = B.load_sdk(ROOT)
THREAD = ROOT / "examples" / "synthetic-turbopump-thread.yaml"
SMALL = ROOT / "examples" / "synthetic-example.yaml"
BASE = {"evidence_grade": "confirmed", "sources": ["https://example.org/synthetic/t"],
        "as_of": datetime.date(2026, 10, 9), "lifecycle": "active", "synthetic": True}


def rec(rtype, rid, **kw):
    r = {"type": rtype, "id": rid, **copy.deepcopy(BASE)}
    r.update(kw)
    return r


class BuildTests(unittest.TestCase):
    def out(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink)
        return tmp.name

    def write(self, data):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8")
        yaml.safe_dump(data, tmp, sort_keys=False)
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink)
        return tmp.name

    def test_pin_file_is_a_full_commit(self):
        self.assertRegex(B.read_pin()["commit"], r"^[0-9a-f]{40}$")

    def test_builds_thread_page(self):
        page = B.build(THREAD, ROOT, self.out()).read_text(encoding="utf-8")
        self.assertIn("Handling: Unclassified — working", page)
        self.assertIn('class="gap">missing', page)
        self.assertIn("Declared critical items", page)
        self.assertIn("Synthetic: every record is fictional.", page)

    def test_builds_capability_page(self):
        page = B.build(SMALL, ROOT, self.out()).read_text(encoding="utf-8")
        self.assertIn('id="cap-table"', page)
        self.assertNotIn('id="threads"', page)  # sections appear only when the file has the data

    def test_fails_closed_on_invalid_file(self):
        bad = self.write({"objects": [{"type": "Entity", "id": "e-1", "synthetic": True}], "links": []})
        out = str(Path(tempfile.mkdtemp()) / "never-written.html")
        with self.assertRaises(B.BuildError):
            B.build(bad, ROOT, out)
        self.assertFalse(Path(out).exists())

    def test_escapes_data_values(self):
        # Red-team case: markup in a record name must render as text, never as page code.
        evil = '<script>alert(1)</script><img src=x onerror=alert(2)>'
        data = {"objects": [
            rec("Entity", "ent-1", name=evil, entity_kind="company",
                incorporation_jurisdiction="CA", controlling_jurisdiction="US"),
            rec("Capability", "cap-1", name='"><b>x</b>'),
        ], "links": [rec("provides_capability", "lnk-1", **{"from": "ent-1", "to": "cap-1"})]}
        page = B.build(self.write(data), ROOT, self.out()).read_text(encoding="utf-8")
        self.assertNotIn("<script>alert", page)
        self.assertNotIn("<img src=x", page)
        self.assertNotIn("<b>x</b>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_page_loads_nothing_external(self):
        page = B.build(THREAD, ROOT, self.out()).read_text(encoding="utf-8")
        self.assertIn("default-src 'none'", page)
        for marker in ("src=\"http", "href=\"http", "@import", "url("):
            self.assertNotIn(marker, page)

    def test_script_allowed_only_by_hash(self):
        page = B.build(THREAD, ROOT, self.out()).read_text(encoding="utf-8")
        self.assertNotIn("script-src 'unsafe-inline'", page)
        self.assertIn(f"script-src '{B.SCRIPT_HASH}'", page)
        self.assertIn(f"<script>{B.SCRIPT}</script>", page)

    def test_control_label_never_shows_host_as_control(self):
        self.assertEqual(B.control_label({"controlling_jurisdiction": "CA", "host_jurisdiction": "US"}), "CA")
        self.assertEqual(B.control_label({"host_jurisdiction": "US"}), "not stated (hosted in US)")
        self.assertEqual(B.control_label({}), "not stated")

    def test_never_shows_real_judgments(self):
        reg = SDK.Registry([rec("CriticalItem", "cri-1", delay_band="d30_90", single_source=True,
                                qualified_alternate=False, synthetic=False)], [])
        self.assertEqual(B.section_critical(reg), "")

    def test_unordered_steps_are_not_numbered(self):
        reg = SDK.Registry(
            [rec("SerialItem", "ser-1", serial="X-1", synthetic=False),
             rec("ProcessStep", "stp-1", step_kind="cleaning", synthetic=False)],
            [rec("underwent", "l-1", synthetic=False, **{"from": "ser-1", "to": "stp-1"})])
        self.assertIn("Order not published", B.section_threads(reg))

    def test_refuses_unpinned_checkout(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(B.BuildError):
                B.check_pin(Path(d), allow_unpinned=False)


if __name__ == "__main__":
    unittest.main()
