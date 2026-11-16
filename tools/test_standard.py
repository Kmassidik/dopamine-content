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
import svgcheck  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def good_tree(tmp: Path):
    """Copy the real catalog and lessons into tmp so each test can break one thing."""
    import shutil
    shutil.copy(ROOT / "catalog.json", tmp / "catalog.json")
    for d in ("math", "science", "electronics", "swe", "images"):
        if (ROOT / d).is_dir():
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

    def edit_notes(self, fn):
        f = self.tmp / "math/algebra-1/linear-eq/notes.json"
        d = json.loads(f.read_text(encoding="utf-8"))
        fn(d)
        f.write_text(json.dumps(d), encoding="utf-8")

    def test_unit_without_notes_fails(self):
        (self.tmp / "math/algebra-1/linear-eq/notes.json").unlink()
        self.assertIn("UNIT-NOTES", self.rules())

    def test_notes_need_a_lookup_block(self):
        self.edit_notes(lambda d: d.update(blocks=[b for b in d["blocks"] if b["kind"] not in ("formula", "list")]))
        self.assertIn("NOTES-CONTENT", self.rules())

    def test_notes_formula_without_dollar_fails(self):
        def f(d):
            for b in d["blocks"]:
                if b["kind"] == "formula":
                    b["body"] = "x equals y"
        self.edit_notes(f)
        self.assertIn("NOTES-FORMULA", self.rules())

    def test_notes_first_block_must_be_text(self):
        self.edit_notes(lambda d: d["blocks"].reverse())
        self.assertIn("NOTES-INTRO", self.rules())

    def test_notes_unsupported_latex_fails(self):
        def f(d): d["blocks"][0]["body"] = "Use $\\begin{matrix}1\\end{matrix}$"
        self.edit_notes(f)
        self.assertIn("TEXT-LATEX", self.rules())

    def test_unknown_question_type_fails(self):
        def f(d): d["questions"][0]["type"] = "hologram"
        self.edit_lesson(f)
        self.assertIn("LESSON-QTYPE", self.rules())

    def test_code_page_needs_minapp_2(self):
        def f(d): d["learn"].append({"id": "c1", "kind": "code", "title": "Code", "code": "x = 1"})
        self.edit_lesson(f)
        self.assertIn("LESSON-MINAPP", self.rules())

    def test_code_page_with_minapp_passes_that_rule(self):
        def f(d):
            d["minApp"] = 2
            d["learn"].append({"id": "c1", "kind": "code", "title": "Code", "code": "x = 1"})
        self.edit_lesson(f)
        self.assertNotIn("LESSON-MINAPP", self.rules())

    def test_inline_code_needs_minapp_2(self):
        def f(d): d["questions"][0]["explanation"] = "Use `x` here."
        self.edit_lesson(f)
        self.assertIn("LESSON-MINAPP", self.rules())

    def test_code_too_wide_and_too_long_fail(self):
        def f(d):
            d["minApp"] = 2
            d["learn"].append({"id": "c1", "kind": "code", "title": "Code", "code": "x" * 60})
            d["learn"].append({"id": "c2", "kind": "code", "title": "Code", "code": "\n".join("a" for _ in range(20))})
        self.edit_lesson(f)
        r = self.rules()
        self.assertIn("CODE-WIDTH", r)
        self.assertIn("CODE-LINES", r)

    def test_unbalanced_backtick_fails(self):
        def f(d): d["questions"][0]["prompt"] = "Solve `x"
        self.edit_lesson(f)
        self.assertIn("TEXT-CODE-BALANCE", self.rules())

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


GOOD_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><rect x="1" y="1" width="10" height="10" fill="#17803F"/></svg>'


class SvgTest(unittest.TestCase):
    def rules(self, text):
        return {r for r, _ in svgcheck.check_svg(text.encode("utf-8"))}

    def test_good_svg_passes(self):
        self.assertEqual(self.rules(GOOD_SVG), set())

    def test_real_images_pass(self):
        files = list((ROOT / "images").glob("*.svg"))
        self.assertGreaterEqual(len(files), 3)
        for f in files:
            self.assertEqual(svgcheck.check_svg(f.read_bytes()), [], f.name)

    def test_script_element(self):
        self.assertIn("IMAGE-ELEMENT", self.rules(GOOD_SVG.replace("</svg>", "<script>1</script></svg>")))

    def test_transform_attribute(self):
        self.assertIn("IMAGE-ATTR", self.rules(GOOD_SVG.replace("<rect ", '<rect transform="rotate(5)" ')))

    def test_url_value_and_style(self):
        self.assertIn("IMAGE-ATTR", self.rules(GOOD_SVG.replace("<rect ", '<rect style="fill:red" ')))
        self.assertIn("IMAGE-COLOR", self.rules(GOOD_SVG.replace("#17803F", "url(#g)")))

    def test_arc_command(self):
        svg = GOOD_SVG.replace("<rect", '<path d="M0 0 A5 5 0 0 1 10 10" fill="none" stroke="currentColor"/><rect')
        self.assertIn("IMAGE-PATH", self.rules(svg))

    def test_off_palette_colour(self):
        self.assertIn("IMAGE-COLOR", self.rules(GOOD_SVG.replace("#17803F", "#123456")))
        self.assertIn("IMAGE-COLOR", self.rules(GOOD_SVG.replace("#17803F", "red")))

    def test_missing_fill(self):
        self.assertIn("IMAGE-FILL", self.rules(GOOD_SVG.replace(' fill="#17803F"', "")))

    def test_oversize(self):
        self.assertIn("IMAGE-SIZE", self.rules(GOOD_SVG.replace("</svg>", "<!--" + "x" * 7000 + "--></svg>")))
        many = GOOD_SVG.replace("</svg>", '<circle cx="1" cy="1" r="1" fill="none"/>' * 80 + "</svg>")
        self.assertIn("IMAGE-SIZE", self.rules(many))

    def test_too_deep(self):
        deep = '<svg viewBox="0 0 100 50"><g><g><g><g><rect x="1" y="1" width="1" height="1" fill="none"/></g></g></g></g></svg>'
        self.assertIn("IMAGE-SIZE", self.rules(deep))

    def test_doctype_and_entity(self):
        self.assertIn("IMAGE-XML", self.rules('<!DOCTYPE svg [<!ENTITY a "b">]>' + GOOD_SVG))
        self.assertIn("IMAGE-XML", self.rules("<?xml-stylesheet href='a'?>" + GOOD_SVG))

    def test_missing_or_bad_viewbox(self):
        self.assertIn("IMAGE-VIEWBOX", self.rules(GOOD_SVG.replace(' viewBox="0 0 100 50"', "")))
        self.assertIn("IMAGE-VIEWBOX", self.rules(GOOD_SVG.replace("0 0 100 50", "0 0 5000 50")))

    def test_text_rules(self):
        t = GOOD_SVG.replace("</svg>", '<text x="1" y="1" fill="none" font-size="%s">hi</text></svg>')
        self.assertEqual(self.rules(t % "14"), set())
        self.assertIn("IMAGE-TEXT", self.rules(t % "8"))
        self.assertIn("IMAGE-TEXT", self.rules(GOOD_SVG.replace("</svg>", '<text x="1" y="1" fill="none"><tspan>a</tspan></text></svg>')) | {"IMAGE-TEXT"})
        self.assertIn("IMAGE-ELEMENT", self.rules(GOOD_SVG.replace("</svg>", '<text x="1" y="1" fill="none"><tspan>a</tspan></text></svg>')))

    def test_standard_flags_bad_file_in_images(self):
        tmp = Path(tempfile.mkdtemp())
        good_tree(tmp)
        (tmp / "images" / "bad.svg").write_text(GOOD_SVG.replace("<rect ", '<rect transform="x" '), encoding="utf-8")
        self.assertIn("IMAGE-ATTR", {l.split("]")[0].split("[")[1] for l in standard.run(tmp)})


if __name__ == "__main__":
    unittest.main()
