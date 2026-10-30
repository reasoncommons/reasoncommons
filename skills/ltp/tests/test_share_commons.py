"""Checks for preparing a commons to share on the Reason Commons site, on the private view's fixture."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/share_commons.py"
SPEC = importlib.util.spec_from_file_location("share_commons", SCRIPT)
share = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(share)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_open_commons import STATE  # noqa: E402

BUILD = SKILL.parents[1] / "apps/reasoning-demo/build.py"
CONSENTS = [
    {"participant": "alice", "name": "Alice Example", "given_at": "2026-10-30T10:00:00Z", "source": "conversation",
     "source_text": "Yes, share it, and name me as Alice Example.", "recorded_by": "alice"},
    {"participant": "bob", "name": "Bob", "given_at": "2026-10-29T18:00:00+01:00", "source": "attested",
     "note": "Bob agreed by email to Alice, first name only.", "recorded_by": "alice"},
]
OPTIONS = {"slug": "quote-turnaround", "title": "Quote turnaround", "summary": "Getting customers a quote within a day.", "github": "alice-example", "today": "2026-10-30"}


def consented(consents=CONSENTS):
    state = deepcopy(STATE)
    state["share_consents"] = deepcopy(consents)
    return state


def ids(publication):
    return {i["id"] for tree in publication["trees"].values() for i in tree["nodes"] + tree["links"]}


class PrepareTests(unittest.TestCase):
    def test_nobody_is_named_without_agreeing(self):
        with self.assertRaisesRegex(ValueError, r"Not yet agreed to be named: Bob \(bob\)"):
            share.prepare(consented(CONSENTS[:1]), **OPTIONS)
        with self.assertRaisesRegex(ValueError, r"Alice \(alice\), Bob \(bob\)"):
            share.prepare(deepcopy(STATE), **OPTIONS)

    def test_people_appear_as_they_chose(self):
        publication = share.prepare(consented(), **OPTIONS)
        self.assertEqual([p["name"] for p in publication["people"]], ["Alice Example", "Bob"])
        self.assertEqual(publication["people"][1]["consent"], {"given_on": "2026-10-29", "how": "attested"})
        self.assertEqual(publication["submitted_by"], {"name": "Alice Example", "github": "alice-example"})
        text = json.dumps(publication)
        self.assertNotIn('"Alice"', text)  # The configured name gives way to the one she chose.
        for absent in ("contributions", "attribution", "mode", "share_consents", "driver", "source_text"):
            self.assertNotIn(f'"{absent}"', text, "Capture details and receipts stay in the working file")

    def test_the_group_chooses_standings_and_trees(self):
        everything = share.prepare(consented(), **OPTIONS)
        self.assertEqual(ids(everything), {"g1", "g2", "gl1", "n1", "n2", "n3", "l1"})
        accepted = share.prepare(consented(), **OPTIONS, standings=("accepted",))
        self.assertEqual(ids(accepted), {"g1", "n1"})  # A connection goes only with both of its ends.
        self.assertEqual([p["name"] for p in accepted["people"]], ["Alice Example", "Bob"])
        goal_only = share.prepare(consented(), **OPTIONS, trees=["goal"])
        self.assertEqual(set(goal_only["trees"]), {"goal"})
        with self.assertRaisesRegex(ValueError, "Choose trees"):
            share.prepare(consented(), **OPTIONS, trees=["conflict"])

    def test_notes_and_open_work_go_only_when_chosen(self):
        plain = share.prepare(consented(), **OPTIONS)
        cr = plain["trees"]["current_reality"]
        self.assertFalse(any("assumptions" in n or "challenges" in n for n in cr["nodes"]))
        self.assertEqual(cr["backlog"], [])
        fuller = share.prepare(consented(), **OPTIONS, notes=True, open_work=True)
        cr = fuller["trees"]["current_reality"]
        self.assertEqual(next(n for n in cr["nodes"] if n["id"] == "n3")["challenges"], [{"text": "Most quotes reuse a template already.", "by": "Alice Example"}])
        self.assertEqual(next(n for n in cr["nodes"] if n["id"] == "n2")["assumptions"], [{"text": "Approval is the only queue.", "by": "Bob"}])
        self.assertEqual({t["ref"] for t in cr["backlog"]}, {"l1", "n3"})

    def test_the_site_checks_run_before_anything_is_written(self):
        with self.assertRaisesRegex(ValueError, "Invalid slug"):
            share.prepare(consented(), **{**OPTIONS, "slug": "Quote Turnaround"})
        with self.assertRaisesRegex(ValueError, "GitHub username"):
            share.prepare(consented(), **{**OPTIONS, "github": "not a handle"})


class ConsentRecordTests(unittest.TestCase):
    def test_the_validator_checks_each_consent(self):
        share.views.validate(consented())
        for change, message in ((lambda c: c[0].pop("source_text"), "own words"), (lambda c: c[1].pop("note"), "where and how"),
                                (lambda c: c[0].update(participant="carol"), "configured human participants"),
                                (lambda c: c[0].update(source="assumed"), "conversation or attested"),
                                (lambda c: c[0].update(given_at="yesterday"), "ISO 8601"),
                                (lambda c: c[0].update(name="AI assistant"), "how the person wants to appear")):
            consents = deepcopy(CONSENTS)
            change(consents)
            with self.assertRaisesRegex(ValueError, message):
                share.views.validate(consented(consents))


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "reason-commons.yaml"
        self.path.write_text(yaml.safe_dump(consented(), sort_keys=False, allow_unicode=True))

    def tearDown(self):
        self.tmp.cleanup()

    def run_share(self, *extra):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.path), "--slug", "quote-turnaround", "--title", "Quote turnaround",
                               "--summary", "Getting customers a quote within a day.", "--github", "alice-example", *extra], capture_output=True, text=True)

    def test_it_writes_the_file_and_a_preview_and_shares_nothing(self):
        result = self.run_share("--notes")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        out = (self.path.parent / ".reason-commons" / "share").resolve()
        self.assertEqual(report["publication"], str(out / "quote-turnaround" / "publication.json"))
        self.assertEqual(report["named"], ["Alice Example", "Bob"])
        self.assertEqual(report["open"], (out / "preview/quote-turnaround/index.html").as_uri())
        preview = (out / "preview/quote-turnaround/about.html").read_text()
        self.assertIn("Preview on this computer.", preview)
        self.assertIn("Nothing has been shared yet.", preview)
        self.assertIn("<b>Bob</b> agreed to be named on 29 October 2026", preview)
        self.assertEqual(sorted(p.name for p in (out / "quote-turnaround").iterdir()), ["publication.json"])

    def test_a_missing_consent_stops_it_with_nothing_written(self):
        self.path.write_text(yaml.safe_dump(consented(CONSENTS[:1]), sort_keys=False, allow_unicode=True))
        result = self.run_share()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Not yet agreed to be named: Bob (bob)", result.stderr)
        self.assertFalse((self.path.parent / ".reason-commons" / "share").exists())

    @unittest.skipUnless(BUILD.is_file(), "The site build lives in the Reason Commons repository")
    def test_the_site_build_accepts_what_it_writes(self):
        result = self.run_share("--notes", "--open-work")
        self.assertEqual(result.returncode, 0, result.stderr)
        spec = importlib.util.spec_from_file_location("demo_build_for_share", BUILD)
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        build.SUBMISSIONS = Path(self.tmp.name) / "submissions"  # What a pull request adds: the folder and its one file.
        (build.SUBMISSIONS / "quote-turnaround").mkdir(parents=True)
        (build.SUBMISSIONS / "quote-turnaround" / "publication.json").write_text(Path(json.loads(result.stdout)["publication"]).read_text())
        site, commons = build.load_site()
        outputs = build.build_files(site, commons)
        self.assertIn("quote-turnaround/index.html", outputs)
        self.assertIn('id="shared"', outputs["index.html"])


if __name__ == "__main__":
    unittest.main()
