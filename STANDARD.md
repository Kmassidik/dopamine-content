# Content standard

Every course in this repo has the same shape. `python3 tools/validate.py` enforces it and CI fails a pull request that breaks it. Each failure prints a rule id, for example `FAIL [LESSON-EXAMPLE] math/.../lesson-01.json: needs at least one worked 'example' page`.

## The shape

```
Course
  overview      summary, what you'll learn, before you start, minutes
  Unit          one objective (a topic you can say in one line)
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
| TEXT-DOLLAR | No `\$` (the app does not support an escaped dollar) |
| TEXT-LATEX | Only the LaTeX commands the app can draw (list in `tools/standard.py`, `LATEX_OK`) |

Page kinds: `text` (explain one idea), `example` (a title, a one-line `body` and 2 to 6 `steps` shown one at a time), `tip` (a short reminder, `body` only). A page may have an `image` (relative `.svg`).

The numbers live in one place, the `RULES` dictionary in `tools/standard.py`. If you change a number, change it here too. `python3 tools/test_standard.py` proves the checks catch bad content, and CI runs it.

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
2. For each unit, add `lesson-NN.json` files with `learn` pages and `questions`.
3. `python3 tools/build_manifest.py`, then `pip install jsonschema` and `python3 tools/validate.py`. Fix every `FAIL` line.
4. Open a pull request. CI runs the same checks.
