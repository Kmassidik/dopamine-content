# Content standard

Every course in this repo has the same shape. `python3 tools/validate.py` enforces it and CI fails a pull request that breaks it. Each failure prints a rule id, for example `FAIL [LESSON-EXAMPLE] math/.../lesson-01.json: needs at least one worked 'example' page`.

## The shape

```
Course
  overview      summary, what you'll learn, before you start, minutes
  Unit          one objective (a topic you can say in one line)
    notes.json  the unit's cheat sheet (look things up any time)
    Lesson      Learn pages (read) -> Practice questions (do)
```

A learner first **reads** a few short pages, then **practises**. Never questions alone.

## Rules

| Rule id | What must be true |
|---|---|
| COURSE-OVERVIEW | Every course has an `overview` in `catalog.json` |
| COURSE-SUMMARY | `summary`: 20 to 300 characters |
| COURSE-OUTCOMES | `outcomes` ("What you'll learn"): 3 to 6 items, each 5 to 100 characters, starting with a capital |
| COURSE-REQUIREMENTS | `requirements` ("Before you start"): 1 to 4 items. Write "None. ..." if nothing is needed |
| COURSE-MINUTES | `minutes` is at least the estimate and at most 3x it. Estimate = reading words / 200 + 0.5 per question. The error message tells you the range |
| UNIT-SIZE | 1 to 8 lessons per unit |
| UNIT-NOTES | Every unit has a `notes.json` next to its lessons |
| NOTES-BLOCKS | 3 to 10 blocks |
| NOTES-INTRO | The first block is kind `text` (the big idea of the unit) |
| NOTES-CONTENT | At least one `formula` or `list` block (something to look up) |
| NOTES-KIND / BODY / TITLE | Kinds are `text`, `formula`, `list`, `tip`. `text`, `formula` and `tip` need a `body`; `text`, `formula` and `list` need a `title` |
| NOTES-FORMULA | A `formula` body contains a `$...$` formula |
| NOTES-ITEMS | A `list` has 2 to 8 items, each at most 100 characters |
| NOTES-LENGTH | A block body is at most 450 characters and the whole notes file at most 400 words |
| LESSON-LEARN | 2 to 10 learn pages |
| LESSON-INTRO | The first page is `text` (what this lesson is about) |
| LESSON-EXAMPLE | At least one `example` page (a worked example) |
| LESSON-PAGE-LENGTH | A page body is at most 450 characters. One idea per page |
| LESSON-PAGE-TITLE | `text` and `example` pages have a title |
| LESSON-STEPS | An `example` has 2 to 6 steps |
| LESSON-KIND | Page kind is `text`, `example` or `tip` |
| LESSON-READING | All learn pages together are 60 to 500 words (about 2 minutes) |
| LESSON-QUESTIONS | 3 to 12 practice questions |
| LESSON-VARIETY | 5 or more questions must use at least 2 question types |
| LESSON-XP | `xp` is 5 to 30 |
| LESSON-TITLE | At most 40 characters, no trailing period |
| LESSON-TAGS | At least one tag |
| TEXT-CLEAN | No leading, trailing or double spaces, tabs, newlines, HTML tags, TODO or FIXME |
| TEXT-MATH-BALANCE | An even number of `$`, and balanced `{ }` inside each formula |
| LESSON-QTYPE | Question `type` is one the app supports (`QUESTION_TYPES` in `tools/standard.py`) |
| LESSON-MINAPP / NOTES-MINAPP | Content that uses a feature introduced in app version N declares `"minApp": N` (or higher). Older apps then show it as locked instead of half-rendering it. Code pages, code note blocks and `` `inline code` `` need `"minApp": 2` |
| LESSON-CODE / NOTES-CODE | A `code` page or block has a `code` field (and a title) |
| CODE-LINES / CODE-WIDTH / CODE-CLEAN | Code is at most 12 lines of at most 40 characters, with no tabs, trailing spaces or blank first/last lines |
| TEXT-CODE-BALANCE | An even number of backticks |
| IMAGE-ALT | A question or learn page with an `image` also has `alt`: 10 to 200 characters describing what the picture shows, for screen readers. For a question image, describe the picture without giving away the answer |
| TEXT-DOLLAR | No `\$` (the app does not support an escaped dollar) |
| TEXT-LATEX | Only the LaTeX commands the app can draw (list in `tools/standard.py`, `LATEX_OK`) |

Notes file (`<unit>/notes.json`): `{ "id", "version", "title", "blocks": [ { "id", "kind", "title", "body", "items" } ] }`. Bump `version` when you change it. Keep it to what a learner looks up: the big idea, the rules, the formulas, the notation, one tip.

Page kinds: `code` (title, optional `body`, a `code` string and an optional `language`; shown in monospace), `text` (explain one idea), `example` (a title, a one-line `body` and 2 to 6 `steps` shown one at a time), `tip` (a short reminder, `body` only). A page may have an `image` (relative `.svg`).

The numbers live in one place, the `RULES` dictionary in `tools/standard.py`. If you change a number, change it here too. `python3 tools/test_standard.py` proves the checks catch bad content, and CI runs it.

## Images (SVG)

Questions and learn pages may have an `image` (a relative `.svg` under `images/`). The app draws it with a small native renderer, so images must stay inside a strict subset. `tools/svgcheck.py` enforces it (the numbers live in its `SVG` dictionary, exported to `contract.json` under `"svg"`).

- Root `<svg>` with a required `viewBox="0 0 W H"` (W and H from 20 to 2000). `width`, `height` and `xmlns` on the root are ignored. Aim for about 340 wide for a phone.
- Elements: `svg g line rect circle ellipse polyline polygon path text`. Comments are fine. Nothing else (no style, script, image, use, defs, gradients, filter, clipPath, foreignObject, tspan, title, desc).
- Attributes: `id x y x1 y1 x2 y2 cx cy r rx ry width height points d fill stroke stroke-width stroke-linecap stroke-linejoin stroke-dasharray opacity font-size font-weight text-anchor`. No `transform`, `style`, `class`, `href`, event handlers or `url(...)`.
- Path `d` uses only `M m L l H h V v C c Q q Z z` (no arcs).
- Colours (`fill`, `stroke`): `none`, `currentColor`, or one palette hex: #FFFFFF #14201A #4F5D55 #E4EAE6 #35C46F #17803F #E4F8EC #22994F #FFC93C #8A5F00 #FFF3CC #D9A21B #FF7FAE #B8305F #FFE4EE #DB5A8A. Set `fill` explicitly on every shape and text (or on a parent `g`), because SVG defaults to black.
- `text` holds plain characters only, `font-size` 10 to 48, `text-anchor` start, middle or end, `font-weight` normal or bold.
- Limits: 6144 bytes, 80 elements, nesting depth 4, no DOCTYPE, ENTITY or processing instructions (only the XML declaration).

| Rule id | What must be true |
|---|---|
| IMAGE-XML | Well-formed UTF-8 XML, no DOCTYPE/ENTITY/processing instructions |
| IMAGE-ELEMENT | Only the allowed elements |
| IMAGE-ATTR | Only the allowed attributes, plain values, no `url()` |
| IMAGE-PATH | Path commands from the allowed list only |
| IMAGE-COLOR | Colours from the palette, `none` or `currentColor` |
| IMAGE-FILL | Explicit `fill` on every shape and text |
| IMAGE-SIZE | File size, element count and nesting limits |
| IMAGE-VIEWBOX | A valid `viewBox` of 20 to 2000 per side |
| IMAGE-TEXT | Plain text, font size 10 to 48, valid anchor and weight |

Tip: draw lines and labels in `currentColor`. The app paints it in the theme's ink colour, so the diagram stays readable in light and dark mode.

Apps older than the one that added the renderer do not show questions that have an `image`. They skip them and count them, so nothing is hidden silently.

## Why these numbers

Short and specific on purpose: the app is for a few minutes a day, so every lesson is small.

- **Objective first, one idea at a time, practice in every section.** Udemy's [course outline guidance](https://teach.udemy.com/course-creation/curriculum?lang=pt-br) builds each section around a learning objective and asks for at least one practice activity per section; its [community guidance](https://community.udemy.com/t5/First-time-course-creation/Course-Outline/m-p/15149) suggests short lectures of 2 to 6 minutes, one topic each.
- **Reading time.** Udemy counts [one minute per 240 words](https://support.udemy.com/hc/en-us/articles/229604328-Calculating-Course-Length) for article lectures. We cap reading at 500 words per lesson and estimate at 200 words per minute to be generous to slow readers.
- **Teach, then practise, with feedback.** Gagné's [nine events of instruction](https://pressbooks.nebraska.edu/onlineteaching/chapter/gagnes-nine-events-of-instruction/) go from gaining attention and stating the objective, through presenting content and guidance, to practice, feedback and assessment. Our lesson is that sequence in small: intro page, worked example, tip, practice, explanation after each answer.
- **Worked examples before problems.** For beginners, studying a worked example then solving similar problems beats unguided problem solving ([cognitive load research summary](https://recapio.com/blog/cognitive-load-theory-examples)). Hence the required `example` page and the 2 to 6 steps that appear one at a time.
- **Small chunks.** Splitting material into small pieces reduces extra mental load ([adaptive lesson chunking study](https://nhsjs.com/?p=32936)). Hence 450 characters per page.

These are guidelines drawn from public teaching advice, not hard science. If a rule blocks a good lesson, open an issue and we change the rule, not work around it.

## Adding a course (checklist)

1. Add the course and its units to `catalog.json`, including `overview`.
2. For each unit, add `notes.json` and `lesson-NN.json` files with `learn` pages and `questions`.
3. `python3 tools/build_manifest.py`, then `pip install jsonschema` and `python3 tools/validate.py`. Fix every `FAIL` line.
4. Open a pull request. CI runs the same checks.

## The contract with the app
`contract.json` is generated (`python3 tools/build_contract.py`) from the schemas and `tools/standard.py`. It lists the question types, page kinds and note kinds the app must understand (with the app version that introduced each), every allowed LaTeX command and every size limit. The app repo keeps a copy and has a unit test that fails if the app's parser or limits disagree with it, so the two repos cannot drift apart. CI fails if `contract.json` is stale.

Adding a new kind of content: (1) build it in the app and bump its `versionCode`, (2) add it to the maps in `tools/standard.py` with that version, (3) regenerate `contract.json`, (4) update the schemas and this document. Content that uses it must declare `minApp`.
