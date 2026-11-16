# dopamine-content

[![validate](https://github.com/Kmassidik/dopamine-content/actions/workflows/validate.yml/badge.svg)](https://github.com/Kmassidik/dopamine-content/actions/workflows/validate.yml)

The lessons behind [Dopamine](https://github.com/Kmassidik/dopamine), a private, offline Android learning app with no ads, no accounts and no tracking. **266 lessons in 14 courses**, all plain JSON that anyone can read, fix or extend.

**Data only. No code from this repository ever runs in the app.**

<p align="center">
  <img src="https://raw.githubusercontent.com/Kmassidik/dopamine/main/docs/screenshots/subjects.png" width="200" alt="Subjects in the app">
  <img src="https://raw.githubusercontent.com/Kmassidik/dopamine/main/docs/screenshots/diagram.png" width="200" alt="A lesson with a diagram">
  <img src="https://raw.githubusercontent.com/Kmassidik/dopamine/main/docs/screenshots/code.png" width="200" alt="A lesson with a code block">
</p>

## What is inside

| Subject | Courses | Lessons |
|---|---|---|
| **Math** | Pre-Algebra (23), Algebra 1 (28), Geometry (28), Algebra 2 (22), Precalculus (22) | 123 |
| **Programming** | C Fundamentals (23), Arrays, Strings and Debugging (21), Algorithms in C (21), Memory and Pointers (22), Data Structures in C (21), Programming Basics in Python (4), AI Engineering (25) | 137 |
| **Science** | Science Basics | 2 |
| **Electronics** | Electronics Basics | 4 |

Every unit has a cheat sheet (`notes.json`) and an app-generated unit quiz. Every lesson is a few short reading pages followed by practice. See [docs/ROADMAP.md](docs/ROADMAP.md) for what is planned next.

## Repository map

```
README.md          you are here
manifest.json      GENERATED. The app fetches this file first. Never edit by hand
contract.json      GENERATED. What the app must understand (question types, LaTeX, SVG limits)

content/           ALL the learning material (the only folder the app downloads lessons from)
  catalog.json       categories, courses and units (hand edited)
  math/  swe/  science/  electronics/
    <course>/<unit>/lesson-NN.json    the lessons (NN sets the order)
    <course>/<unit>/notes.json        the unit's cheat sheet
  images/            SVG diagrams used by lessons

docs/              guides for people and AI agents
  AUTHORING.md       make a new course on any topic, step by step
  SVG.md             how diagrams work end to end (with the flow diagram)
  STANDARD.md        the enforced rules and why
  ROADMAP.md         GENERATED coverage and plan

tools/             build_manifest, validate, standard, svgcheck, build_contract, tests
schema/            JSON Schemas (manifest, lesson)
.github/           CI that runs the same checks on every push
```

## If you are an AI agent

Read in this order, then work only inside `content/` (plus the generated files below):

1. [docs/AUTHORING.md](docs/AUTHORING.md): the workflow for adding or changing a course, and a prompt template.
2. [docs/STANDARD.md](docs/STANDARD.md): the rules the validators enforce. `tools/standard.py` holds the numbers.
3. [docs/SVG.md](docs/SVG.md): only if you draw a diagram.
4. Look at one finished course (`content/math/geometry`) for tone and shape.

Rules that are easy to forget:

- **Never edit `manifest.json` or `contract.json` by hand.** Run `python3 tools/build_manifest.py` after any change under `content/`.
- **Bump a lesson's `version`** whenever you change it, or the app will not download it again.
- **Never rename or reuse an id.** Learners' progress is stored against it.
- **Moving or renaming a lesson file changes its path.** Apps up to 0.3.0 only notice a change by `version` or hash, so also bump `version` when you move a file.
- **Run before you finish:** `python3 tools/build_manifest.py && python3 tools/build_contract.py --check && python3 tools/standard.py && python3 tools/validate.py && python3 tools/test_standard.py` (`validate.py` needs `pip install jsonschema`).
- Verify facts by running something (a script, the code you show). Write in your own words. Commit with a plain message and no AI attribution lines.

## Add your own course

Want to learn something that is not here yet (a language, a tool, an idea like software architecture)? **[docs/AUTHORING.md](docs/AUTHORING.md)** is a step-by-step recipe for making a whole course on any topic, by hand or with an AI agent, including a copy-paste prompt. The result appears in the app after **Settings, Update content**. No app release is needed.

The layout is enforced by tools and CI, so a new course always looks and behaves like the rest. The rules are in **[docs/STANDARD.md](docs/STANDARD.md)**.

## How it reaches the phone

```
 you edit JSON  ->  build_manifest.py  ->  git push main  ->  Settings, Update content
                     (manifest.json:        (raw GitHub)        downloads only what changed,
                      hashes + sizes)                           verifies every file, then swaps
```

The app fetches `manifest.json` from this repo's raw URL on `main`, downloads only the lessons whose version or hash changed, checks size, hash and schema, and swaps them in atomically. If anything fails, nothing changes. Every path in the manifest starts with `content/`. A small bundled sample of this content also ships inside the app as the first-launch seed.

Pictures take the same road. **[docs/SVG.md](docs/SVG.md)** shows the whole journey of a diagram, from drawing it to the learner's screen:

[![How a diagram reaches the screen](docs/content-flow.svg)](docs/SVG.md)

Removing a course from the manifest hides it in the app after the next update.

## Publish an update

1. Add or edit lesson files. **Bump `version` in a lesson whenever you change it.**
2. `python3 tools/build_manifest.py`
3. `pip install jsonschema && python3 tools/validate.py`
4. Commit and push to `main`. In the app: Settings, Update content.

CI (`.github/workflows/validate.yml`) fails when `manifest.json` is stale or any file is invalid. The app repo keeps a small bundled sample (the first-launch seed) that is refreshed separately, only when the sample should change.

## Add a course, unit or category

Follow [docs/AUTHORING.md](docs/AUTHORING.md). In short: edit `content/catalog.json` to add the category (`id`, `name`, `icon`, `color` hex, `order`), course (`id`, `categoryId`, `title`, `description`, `order`, `dir`, `overview`) or unit (`id`, `title`, `order`, `dir`), create the folder under `content/`, add lessons and notes, regenerate the manifest. Icon names the app knows: `ic_math`, `ic_science`, `ic_english`, `ic_swe`, `ic_electronics`; unknown names fall back to a default icon.

## Lesson file

```json
{
  "id": "linear-eq-01",
  "version": 1,
  "title": "One-step equations",
  "xp": 10,
  "tags": ["algebra"],
  "learn": [
    { "id": "what-is-an-equation", "kind": "text", "title": "What is an equation?",
      "body": "An equation says two things are equal, like $x+3=7$." },
    { "id": "example-add", "kind": "example", "title": "Solve $x+3=7$", "body": "Undo the +3.",
      "steps": ["Subtract 3 from both sides: $x=4$", "Check: $4+3=7$."] },
    { "id": "opposite", "kind": "tip", "body": "Do the opposite operation, then check." }
  ],
  "questions": [ { "id": "q1", "type": "multiple_choice", "prompt": "Solve $x+3=7$",
                   "choices": ["$x=4$", "$x=10$", "$x=-4$"], "answerIndex": 0,
                   "explanation": "Subtract 3 from both sides: $x=7-3=4$." } ]
}
```

Rules: ids are lowercase and hyphenated (`^[a-z0-9]+(-[a-z0-9]+)*$`), stable, and never reused for different content. Every question has a unique `id` within the lesson, a `type`, and an `explanation`. Max 40 questions per lesson, lesson file under 256 KB, image under 1 MB. An optional `image` is a relative `.svg` path (no `..`, no leading `/`).

| `type` | Required fields |
|---|---|
| `multiple_choice` | `prompt`, `choices` (2 to 5), `answerIndex` (0-based, into the original order; the app shuffles) |
| `fill_blank` | `prompt` (write the blank as `\\_\\_`), `choices` (2 to 5), `answerIndex` |
| `type_answer` | `prompt`, `accepted` (list of strings), optional `keypad`: `numeric` / `algebra` / `full` |
| `match_pairs` | `pairs`: 2 to 6 `[left, right]` pairs (the app shuffles the right column), optional `prompt` |
| `order_steps` | `steps` in the correct order (the app shuffles), optional `prompt` |

Unknown `type` values are skipped by older apps (forward compatible), so new types can be added carefully.

## Writing math

Text fields support `$inline$` LaTeX (a literal dollar sign is not supported; write the word). The standard only allows commands the app can draw (`LATEX_OK` in `tools/standard.py`). In JSON, backslashes are doubled: `"$\\frac{a}{b}$"`. Keep formulas short; very wide ones can overflow a narrow screen. The renderer has no matrices, `cases` or `align`, and `\left(` `\right)` do not stretch to the height of what they wrap.

Copy style: short, calm, specific. One idea per question. The explanation says why, not just what.
