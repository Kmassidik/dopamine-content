#!/usr/bin/env python3
"""Proves the standard really rejects bad content. Run: python3 tools/test_standard.py"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import standard  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def good_tree(tmp: Path):
    """Copy the real catalog and lessons into tmp so each test can break one thing."""
    import shutil
    shutil.copy(ROOT / "catalog.json", tmp / "catalog.json")
    for d in ("math", "science"):
        shutil.copytree(ROOT / d, tmp / d)


class StandardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        good_tree(self.tmp)
        self.lesson = self.tmp / "math/algebra-1/linear-eq/lesson-01.json"

    def edit_lesson(self, fn):
        d = json.loads(self.lesson.read_text(encoding="utf-8"))
        fn(d)
        self.lesson.write_text(json.dumps(d), encoding="utf-8")

    def rules(self):
        return {line.split("]")[0].split("[")[1] for line in standard.run(self.tmp)}

    def test_real_content_passes(self):
        self.assertEqual(standard.run(ROOT), [])

    def test_lesson_without_learn_pages_fails(self):
        self.edit_lesson(lambda d: d.pop("learn"))
        self.assertIn("LESSON-LEARN", self.rules())

    def test_missing_example_fails(self):
        def f(d): d["learn"] = [p for p in d["learn"] if p["kind"] != "example"]
        self.edit_lesson(f)
        self.assertIn("LESSON-EXAMPLE", self.rules())

    def test_first_page_must_be_text(self):
        def f(d): d["learn"].insert(0, {"id": "tip-first", "kind": "tip", "body": "Hello there friend."})
        self.edit_lesson(f)
        self.assertIn("LESSON-INTRO", self.rules())

    def test_long_page_fails(self):
        def f(d): d["learn"][0]["body"] = "word " * 120
        self.edit_lesson(f)
        self.assertIn("LESSON-PAGE-LENGTH", self.rules())

    def test_too_few_questions_fails(self):
        def f(d): d["questions"] = d["questions"][:1]
        self.edit_lesson(f)
        self.assertIn("LESSON-QUESTIONS", self.rules())

    def test_unsupported_latex_fails(self):
        def f(d): d["questions"][0]["prompt"] = "Solve $\\begin{matrix}1\\end{matrix}$"
        self.edit_lesson(f)
        self.assertIn("TEXT-LATEX", self.rules())

    def test_unbalanced_dollar_fails(self):
        def f(d): d["questions"][0]["prompt"] = "Solve $x+3=7"
        self.edit_lesson(f)
        self.assertIn("TEXT-MATH-BALANCE", self.rules())

    def test_messy_text_fails(self):
        def f(d): d["questions"][0]["explanation"] = "Two  spaces and TODO"
        self.edit_lesson(f)
        self.assertIn("TEXT-CLEAN", self.rules())

    def test_course_without_overview_fails(self):
        cat = json.loads((self.tmp / "catalog.json").read_text(encoding="utf-8"))
        del cat["courses"][0]["overview"]
        (self.tmp / "catalog.json").write_text(json.dumps(cat), encoding="utf-8")
        self.assertIn("COURSE-OVERVIEW", self.rules())

    def test_wrong_minutes_fails(self):
        cat = json.loads((self.tmp / "catalog.json").read_text(encoding="utf-8"))
        cat["courses"][0]["overview"]["minutes"] = 500
        (self.tmp / "catalog.json").write_text(json.dumps(cat), encoding="utf-8")
        self.assertIn("COURSE-MINUTES", self.rules())

    def test_too_few_outcomes_fails(self):
        cat = json.loads((self.tmp / "catalog.json").read_text(encoding="utf-8"))
        cat["courses"][0]["overview"]["outcomes"] = ["Solve things"]
        (self.tmp / "catalog.json").write_text(json.dumps(cat), encoding="utf-8")
        self.assertIn("COURSE-OUTCOMES", self.rules())


if __name__ == "__main__":
    unittest.main()
