# Make a course on any topic

This is the recipe for adding a new course to Dopamine, written so that a person or an AI agent can follow it from start to finish. Pick a topic ("Linux basics", "Music theory", "Software architecture"), follow the steps, and the course shows up in the app after **Settings, Update content**. No app release is needed.

Read [STANDARD.md](STANDARD.md) for the rules. This page is the workflow around them.

## What you will make

```
Course                      one topic (aim for 4 to 5 units and 20 to 26 lessons)
  Unit                      one objective you can say in a line (1 to 8 lessons, aim for 4 to 7)
    notes.json              the unit's cheat sheet (3 to 10 blocks)
    lesson-01.json ...      read 5 to 7 short pages, then answer 6 to 9 questions
```

A lesson is 5 to 10 minutes on a phone. Learners **read first, then practise**. Questions never come alone.

## The steps

### 1. Set up

```bash
git clone https://github.com/Kmassidik/dopamine-content && cd dopamine-content
pip install jsonschema          # the only dependency
python3 tools/validate.py       # should print: ok: 241 lessons, 7 images
```

### 2. Plan the course on paper first

Write down, before any JSON:

- **Who is it for, and what do they know already?** This becomes `requirements` (1 to 4 lines; write "None. ..." if nothing is needed).
- **3 to 6 outcomes**, each a sentence starting with a verb ("Read a stack trace", "Pick between two designs"). This becomes `outcomes`.
- **4 to 5 units in teaching order**, each with one objective. Do not use a term before you have taught it. Later lessons should reuse earlier ideas.
- **A list of lesson titles per unit** (at most 40 characters, no trailing period).

Use a well-known topic order if one exists, but write everything in your **own words**. Do not copy text from books, courses or websites.

### 3. Choose ids

Everything is lowercase with hyphens (`^[a-z0-9]+(-[a-z0-9]+)*$`) and globally unique. Never reuse an id for different content, and never rename an id once learners may have progress on it.

| Thing | Pattern | Example |
|---|---|---|
| Course | `<topic>` | `software-architecture` |
| Unit | `<prefix>-<unit>` | `arch-layers` |
| Lesson | `<unit id>-NN` | `arch-layers-01` |
| Notes | `<unit id>-notes` | `arch-layers-notes` |
| Page / block / question | unique inside its file | `intro`, `q1` |

### 4. Register the course in `content/catalog.json`

Add one object to `courses` (copy a neighbour such as Geometry and edit it). `categoryId` is `math`, `science`, `swe` or `electronics`; a new category needs its own entry (see [README](../README.md#add-a-course-unit-or-category)). `dir` is the folder under `content/`, and each unit's `dir` is a folder inside it.

```json
{
  "id": "software-architecture",
  "categoryId": "swe",
  "title": "Software Architecture",
  "description": "How to split a program into parts that stay easy to change",
  "order": 7,
  "dir": "swe/software-architecture",
  "overview": {
    "summary": "Learn how real programs are organised, from layers and modules to trade-offs. Short readings, each followed by practice.",
    "outcomes": [
      "Split a program into layers with clear jobs",
      "Explain what coupling and cohesion mean",
      "Choose between two designs and say why"
    ],
    "requirements": ["Basic programming in any language"],
    "minutes": 120
  },
  "units": [
    { "id": "arch-layers", "title": "Layers", "order": 1, "dir": "layers" }
  ]
}
```

`minutes` must fall inside the range the validator prints if it is wrong (rule `COURSE-MINUTES`), so write your best guess, run step 7, and adjust.

### 5. Write the lessons and notes

Create `content/swe/software-architecture/layers/lesson-01.json`, `lesson-02.json`, ... and `notes.json`. The number in the file name sets the order. Start from this skeleton:

```json
{
  "id": "arch-layers-01",
  "version": 1,
  "title": "Why use layers",
  "xp": 10,
  "tags": ["architecture"],
  "learn": [
    { "id": "intro", "kind": "text", "title": "One job per part",
      "body": "A layer is a group of code with one job. Keeping jobs apart makes each part easier to change." },
    { "id": "example", "kind": "example", "title": "Where does it go?",
      "body": "Sort three pieces of code.",
      "steps": ["Drawing a button: the screen layer.", "Saving a score: the data layer."] },
    { "id": "tip", "kind": "tip", "body": "If a change touches every file, the parts are tangled." }
  ],
  "questions": [
    { "id": "q1", "type": "multiple_choice", "prompt": "Which job belongs in the data layer?",
      "choices": ["Saving a score", "Drawing a button", "Choosing a colour"], "answerIndex": 0,
      "explanation": "The data layer stores and loads information. Drawing belongs to the screen layer." }
  ]
}
```

This skeleton is short on purpose. Until you add more pages (60 words of reading or more) and 3 or more questions, the validator will tell you so. That is the checker working, not a mistake in the template.

The notes skeleton:

```json
{
  "id": "arch-layers-notes",
  "version": 1,
  "title": "Layers: cheat sheet",
  "blocks": [
    { "id": "big-idea", "kind": "text", "title": "The big idea", "body": "Give every part of the program one job." },
    { "id": "layers", "kind": "list", "title": "Common layers",
      "items": ["Screen: shows things", "Logic: decides things", "Data: stores things"] },
    { "id": "tip", "kind": "tip", "body": "Dependencies point one way: screen to logic to data." }
  ]
}
```

Writing rules that the validator cannot judge for you:

- **Calm, short, specific.** One idea per page, one idea per question. No emoji, no exclamation marks, no trick questions.
- **Every explanation teaches.** Say why the answer is right, not just what it is. Wrong choices must be plausible and unique.
- **Easy questions first**, harder later. Use at least three question types per lesson (`multiple_choice`, `fill_blank`, `type_answer`, `match_pairs`, `order_steps`). The field table is in the [README](../README.md#lesson-file).
- **Accept every reasonable spelling** in `type_answer.accepted`, including the decimal form of numbers.
- **Math** uses `$...$` with only the LaTeX commands the app can draw (`LATEX_OK` in `tools/standard.py`). Backslashes are doubled in JSON: `"$\\frac{a}{b}$"`.
- **Code** uses a `code` page (at most 12 lines of 40 characters, 4-space indent) and the lesson must declare `"minApp": 2`. Python is highlighted; other languages show plain.
- **Pictures** are optional hand-written SVG in the strict subset, at most 6 KB, with `alt` text. [SVG.md](SVG.md) has the template, the flow and the common errors.

### 6. Check the facts

The validator checks shape, not truth. Before you trust a lesson:

- **Numbers and math:** compute every answer with a short script and check that each wrong choice really is wrong.
- **Code and commands:** put the full program in a file, run it, and confirm the output your lesson claims. For C, compile with `cc -std=c11 -Wall -Wextra`.
- **Claims:** if a statement depends on a platform or a version, say so in the lesson.
- If you cannot verify something, leave it out or say it is unverified. Never write an unchecked fact as certain.

### 7. Build and validate

```bash
python3 tools/build_manifest.py        # regenerates manifest.json (never edit it by hand)
python3 tools/build_contract.py --check
python3 tools/standard.py
python3 tools/validate.py
python3 tools/test_standard.py
```

Every failure prints a rule id and a file, for example `FAIL [LESSON-EXAMPLE] ...: needs at least one worked 'example' page`. Fix each one and run again. CI runs the same commands.

### 8. Publish

```bash
git add content manifest.json
git commit -m "Add Software Architecture course"
git push origin main
```

On the phone: **Settings, Update content**. Only changed files download, and every file is checked before it replaces the old copy. If a file is bad, nothing changes.

When you later edit a published lesson, **bump its `version`**, or the app will not download it again.

## A prompt you can give an AI agent

Copy this, fill in the two blanks, and run it inside a clone of this repo.

```text
Write one complete course for the Dopamine app in this repository.

Topic: <TOPIC>
Audience: <WHO IT IS FOR AND WHAT THEY ALREADY KNOW>

First read README.md, docs/STANDARD.md, docs/AUTHORING.md and tools/standard.py, then look at one
finished course (content/math/geometry) to see the tone and shape. Follow docs/AUTHORING.md step by step.

Rules:
- Plan first: outcomes, requirements, 4 to 5 units, lesson titles. Show me the plan before writing lessons.
- Write everything in your own words. Do not copy from any website, book or course.
- Verify every number, answer and code output by running a script. Say what you could not verify.
- Only edit the new course folder under content/ and content/catalog.json. Do not touch tools/, schema/ or docs/STANDARD.md.
- Run the five commands in step 7 until they all pass.
- Commit with a plain message. Do not add AI attribution trailers (no Co-Authored-By, no "Generated with" lines).
- Report: files created, the output of each command, and anything uncertain.
```

Ask the agent to stop after the plan and wait for your approval; changing a plan is much cheaper than changing 25 lessons.

## Done checklist

- [ ] Every command in step 7 passes
- [ ] You tapped Update content on a phone and opened at least one lesson from each unit
- [ ] Math, code and claims were verified by running something
- [ ] Ids are stable and nothing was renamed
- [ ] No text is copied from another source
