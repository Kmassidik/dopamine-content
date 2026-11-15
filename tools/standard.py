#!/usr/bin/env python3
"""The Dopamine content standard, enforced. Every rule has an id; a violation fails CI.

Used by tools/validate.py. Run alone with: python3 tools/standard.py
The numbers below are the standard. STANDARD.md explains why each exists.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---- The numbers (keep STANDARD.md in sync) ---------------------------------
RULES = {
    "summary_chars": (20, 300),
    "outcomes": (3, 6),
    "requirements": (1, 4),
    "list_item_chars": (5, 100),
    "lessons_per_unit": (1, 8),
    "learn_pages": (2, 10),
    "page_body_chars": 450,
    "example_steps": (2, 6),
    "reading_words": (60, 500),      # per lesson, all learn pages together
    "questions": (3, 12),
    "variety_from": 5,               # lessons with this many questions must use 2+ question types
    "xp": (5, 30),
    "title_chars": 40,
    "words_per_minute": 200,         # reading speed used for the time estimate
    "minutes_per_question": 0.5,
    "minutes_slack": 3,              # overview.minutes may be up to 3x the estimate
    "notes_blocks": (3, 10),
    "notes_words": 400,
    "notes_list_items": (2, 8),
    "notes_item_chars": 100,
}

# LaTeX commands the app's renderer understands (ui/math/MathParser.kt). Keep in sync.
LATEX_OK = set("""
frac dfrac tfrac sqrt text mathrm textbf mathbf operatorname left right
cdot times div pm mp le leq ge geq ne neq approx equiv to rightarrow Rightarrow leftarrow in
infty degree circ ldots dots cdots sum int prod partial nabla angle triangle perp parallel
Delta Omega Sigma Pi Theta alpha beta gamma delta epsilon eta theta lambda mu pi rho sigma tau phi omega
sin cos tan log ln lim min max exp det
""".split())

MATH_RE = re.compile(r"\$(.*?)\$", re.S)


def lo_hi(name):
    return RULES[name]


class Report:
    def __init__(self):
        self.items = []

    def fail(self, rule, where, msg):
        self.items.append(f"FAIL [{rule}] {where}: {msg}")


def words(s: str) -> int:
    """Count words; each $math$ chunk counts as one word."""
    return len(MATH_RE.sub(" m ", s).split())


def texts_of(lesson: dict):
    """Every learner-visible string in a lesson, with a label."""
    for pg in lesson.get("learn", []):
        for k in ("title", "body"):
            if k in pg:
                yield f"learn/{pg['id']}.{k}", pg[k]
        for i, s in enumerate(pg.get("steps", [])):
            yield f"learn/{pg['id']}.steps[{i}]", s
    for q in lesson.get("questions", []):
        for k in ("prompt", "explanation"):
            if k in q:
                yield f"{q['id']}.{k}", q[k]
        for i, s in enumerate(q.get("choices", [])):
            yield f"{q['id']}.choices[{i}]", s
        for i, s in enumerate(q.get("steps", [])):
            yield f"{q['id']}.steps[{i}]", s
        for i, pair in enumerate(q.get("pairs", [])):
            for j, s in enumerate(pair):
                yield f"{q['id']}.pairs[{i}][{j}]", s


def check_text(rep, where, s):
    if "\\$" in s:
        rep.fail("TEXT-DOLLAR", where, "escaped \\$ is not supported; write the word 'dollars' or avoid it")
    if s.count("$") % 2:
        rep.fail("TEXT-MATH-BALANCE", where, "odd number of $ signs")
    if s != s.strip() or "  " in s or "\t" in s or "\n" in s:
        rep.fail("TEXT-CLEAN", where, "no leading/trailing/double spaces, tabs or newlines")
    if re.search(r"<[a-zA-Z/]", s) or "TODO" in s or "FIXME" in s:
        rep.fail("TEXT-CLEAN", where, "no HTML tags and no TODO/FIXME")
    for m in MATH_RE.finditer(s):
        body = m.group(1)
        if body.count("{") != body.count("}"):
            rep.fail("TEXT-MATH-BALANCE", where, f"unbalanced braces in ${body}$")
        for cmd in re.findall(r"\\([A-Za-z]+)", body):
            if cmd not in LATEX_OK:
                rep.fail("TEXT-LATEX", where, f"\\{cmd} is not supported by the app's math renderer")


def notes_texts(notes: dict):
    for b in notes.get("blocks", []):
        for k in ("title", "body"):
            if k in b:
                yield f"notes/{b['id']}.{k}", b[k]
        for i, s in enumerate(b.get("items", [])):
            yield f"notes/{b['id']}.items[{i}]", s


def check_notes(rep, label, notes):
    blocks = notes.get("blocks", [])
    lo, hi = RULES["notes_blocks"]
    if not lo <= len(blocks) <= hi:
        rep.fail("NOTES-BLOCKS", label, f"needs {lo} to {hi} blocks, has {len(blocks)}")
    if blocks and blocks[0]["kind"] != "text":
        rep.fail("NOTES-INTRO", label, "the first block must be kind 'text' (the big idea of the unit)")
    if not any(b["kind"] in ("formula", "list") for b in blocks):
        rep.fail("NOTES-CONTENT", label, "needs at least one 'formula' or 'list' block (something to look up)")
    if len(notes["title"]) > RULES["title_chars"] + 20 or notes["title"].endswith("."):
        rep.fail("NOTES-TITLE", label, "title up to 60 characters, no trailing period")
    for b in blocks:
        w = f"{label} block {b['id']}"
        kind = b["kind"]
        if kind not in ("text", "formula", "list", "tip"):
            rep.fail("NOTES-KIND", w, f"unknown kind '{kind}' (use text, formula, list or tip)")
        if kind in ("text", "formula", "tip") and "body" not in b:
            rep.fail("NOTES-BODY", w, f"a {kind} block needs a body")
        if kind in ("text", "list", "formula") and "title" not in b:
            rep.fail("NOTES-TITLE", w, f"a {kind} block needs a title")
        if kind == "formula" and "$" not in b.get("body", ""):
            rep.fail("NOTES-FORMULA", w, "a formula block's body must contain a $formula$")
        if kind == "list":
            a, z = RULES["notes_list_items"]
            items = b.get("items", [])
            if not a <= len(items) <= z:
                rep.fail("NOTES-ITEMS", w, f"a list needs {a} to {z} items")
            if any(len(i) > RULES["notes_item_chars"] for i in items):
                rep.fail("NOTES-ITEMS", w, f"list items are at most {RULES['notes_item_chars']} characters")
        if len(b.get("body", "")) > RULES["page_body_chars"]:
            rep.fail("NOTES-LENGTH", w, f"body over {RULES['page_body_chars']} characters")
    nw = sum(words(t) for _, t in notes_texts(notes))
    if nw > RULES["notes_words"]:
        rep.fail("NOTES-LENGTH", label, f"notes are {nw} words; keep them under {RULES['notes_words']}")
    for where, t in notes_texts(notes):
        check_text(rep, f"{label} {where}", t)


def estimate_minutes(lessons):
    reading = 0
    questions = 0
    for l in lessons:
        for _, t in texts_of({"learn": l.get("learn", []), "questions": []}):
            reading += words(t)
        questions += len(l.get("questions", []))
    return reading / RULES["words_per_minute"] + questions * RULES["minutes_per_question"]


def check_lesson(rep, label, l):
    lo, hi = RULES["learn_pages"]
    pages = l.get("learn", [])
    if not lo <= len(pages) <= hi:
        rep.fail("LESSON-LEARN", label, f"needs {lo} to {hi} learn pages before the practice, has {len(pages)}")
    if pages and pages[0]["kind"] != "text":
        rep.fail("LESSON-INTRO", label, "the first learn page must be kind 'text' (what this lesson is about)")
    if pages and not any(p["kind"] == "example" for p in pages):
        rep.fail("LESSON-EXAMPLE", label, "needs at least one worked 'example' page before the practice")
    for p in pages:
        w = f"{label} page {p['id']}"
        if len(p.get("body", "")) > RULES["page_body_chars"]:
            rep.fail("LESSON-PAGE-LENGTH", w, f"body over {RULES['page_body_chars']} characters; one idea per page")
        if p["kind"] in ("text", "example") and "title" not in p:
            rep.fail("LESSON-PAGE-TITLE", w, "text and example pages need a title")
        if p["kind"] == "example":
            lo2, hi2 = RULES["example_steps"]
            if not lo2 <= len(p.get("steps", [])) <= hi2:
                rep.fail("LESSON-STEPS", w, f"an example needs {lo2} to {hi2} steps")
        if p["kind"] not in ("text", "example", "tip"):
            rep.fail("LESSON-KIND", w, f"unknown page kind '{p['kind']}' (use text, example or tip)")
    reading = sum(words(t) for _, t in texts_of({"learn": pages, "questions": []}))
    lo3, hi3 = RULES["reading_words"]
    if pages and not lo3 <= reading <= hi3:
        rep.fail("LESSON-READING", label, f"reading is {reading} words; keep it between {lo3} and {hi3}")
    qs = l.get("questions", [])
    lo4, hi4 = RULES["questions"]
    if not lo4 <= len(qs) <= hi4:
        rep.fail("LESSON-QUESTIONS", label, f"needs {lo4} to {hi4} practice questions, has {len(qs)}")
    if len(qs) >= RULES["variety_from"] and len({q["type"] for q in qs}) < 2:
        rep.fail("LESSON-VARIETY", label, "use at least 2 different question types")
    lo5, hi5 = RULES["xp"]
    if not lo5 <= l["xp"] <= hi5:
        rep.fail("LESSON-XP", label, f"xp must be {lo5} to {hi5}")
    if len(l["title"]) > RULES["title_chars"] or l["title"].endswith("."):
        rep.fail("LESSON-TITLE", label, f"title up to {RULES['title_chars']} characters, no trailing period")
    if not l.get("tags"):
        rep.fail("LESSON-TAGS", label, "needs at least one tag")
    for where, s in texts_of(l):
        check_text(rep, f"{label} {where}", s)


def check_course(rep, course, lessons_by_unit):
    where = f"course {course['id']}"
    ov = course.get("overview")
    if not ov:
        rep.fail("COURSE-OVERVIEW", where, "every course needs an overview (summary, outcomes, requirements, minutes)")
        return
    lo, hi = RULES["summary_chars"]
    if not lo <= len(ov.get("summary", "")) <= hi:
        rep.fail("COURSE-SUMMARY", where, f"summary must be {lo} to {hi} characters")
    for key in ("outcomes", "requirements"):
        a, b = RULES[key]
        items = ov.get(key, [])
        if not a <= len(items) <= b:
            rep.fail(f"COURSE-{key.upper()}", where, f"{key} needs {a} to {b} items, has {len(items)}")
        c1, c2 = RULES["list_item_chars"]
        for it in items:
            if not c1 <= len(it) <= c2 or it != it.strip() or not it[0].isupper():
                rep.fail(f"COURSE-{key.upper()}", where, f"'{it}': {c1} to {c2} characters, start with a capital letter")
    all_lessons = [l for ls in lessons_by_unit.values() for l in ls]
    est = estimate_minutes(all_lessons)
    mins = ov.get("minutes", 0)
    if not (math.ceil(est) <= mins <= est * RULES["minutes_slack"]):
        rep.fail("COURSE-MINUTES", where,
                 f"minutes is {mins} but the content takes about {est:.1f}; use {math.ceil(est)} to {int(est * RULES['minutes_slack'])}")
    for unit in course["units"]:
        n = len(lessons_by_unit.get(unit["id"], []))
        a, b = RULES["lessons_per_unit"]
        if not a <= n <= b:
            rep.fail("UNIT-SIZE", f"{where} unit {unit['id']}", f"needs {a} to {b} lessons, has {n}")


def run(root: Path = ROOT) -> list:
    rep = Report()
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    for course in catalog["courses"]:
        by_unit = {}
        for unit in course["units"]:
            d = root / course["dir"] / unit["dir"]
            by_unit[unit["id"]] = []
            for f in sorted(d.glob("lesson-*.json")):
                l = json.loads(f.read_text(encoding="utf-8"))
                by_unit[unit["id"]].append(l)
                check_lesson(rep, f.relative_to(root).as_posix(), l)
        for unit in course["units"]:
            nf = root / course["dir"] / unit["dir"] / "notes.json"
            if not nf.is_file():
                rep.fail("UNIT-NOTES", f"course {course['id']} unit {unit['id']}", "every unit needs a notes.json (the cheat sheet)")
            else:
                check_notes(rep, nf.relative_to(root).as_posix(), json.loads(nf.read_text(encoding="utf-8")))
        check_course(rep, course, by_unit)
    return rep.items


if __name__ == "__main__":
    problems = run()
    print("\n".join(problems) if problems else "standard: ok")
    sys.exit(1 if problems else 0)
