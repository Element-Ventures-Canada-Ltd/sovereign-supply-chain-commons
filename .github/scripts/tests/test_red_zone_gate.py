# Handling: Unclassified — working
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
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


class Zones(unittest.TestCase):
    def assertZone(self, path, red):
        self.assertEqual(is_red(path, RULES), red, path)

    def test_green_areas(self):
        for p in ["Dashboard/build.py", "Dashboard/tests/test_build.py", "Engagement/x.md",
                  "Survey/README.md", "examples/synthetic-turbopump-chain/a.yaml"]:
            self.assertZone(p, False)

    def test_red_default_and_root(self):
        for p in ["CLA.md", "README.md", "adapters/gotham/SPEC.md", "newdir/file.py", "LICENSE"]:
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


if __name__ == "__main__":
    unittest.main()
