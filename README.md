# dopamine-content

Lesson content for the [Dopamine](https://github.com/Kmassidik/dopamine) Android app. **Data only. No code from here ever runs in the app.**

The app fetches `manifest.json` from this repo (raw URL on `main`) when the user taps *Update content* in Settings, downloads only the lessons whose version or hash changed, verifies them, and swaps them in atomically. A bundled copy of this repo's content ships inside the app as the first-launch seed.

## Layout

```
catalog.json                      categories, courses, units (hand edited)
<category>/<course>/<unit>/lesson-NN.json   lessons (NN sets the order)
images/*.svg                      diagrams referenced by lessons
manifest.json                     GENERATED. Never edit by hand.
schema/                           JSON Schemas (manifest, lesson)
tools/build_manifest.py           generates manifest.json (stdlib only)
tools/validate.py                 schema + semantic checks (needs `pip install jsonschema`)
```

Current content: Math / Algebra 1 / Linear Equations (2 lessons), Science / Science Basics / Matter (2 lessons).

## Publish an update

1. Add or edit lesson files. **Bump `version` in a lesson whenever you change it.**
2. `python3 tools/build_manifest.py`
3. `pip install jsonschema && python3 tools/validate.py`
4. Commit and push to `main`. In the app: Settings, Update content.

CI (`.github/workflows/validate.yml`) fails when `manifest.json` is stale or any file is invalid. If the bundled seed in the app should include new lessons, also copy `manifest.json`, the lesson folders and `images/` into the app repo's `app/src/main/assets/content/`.

## Add a course, unit or category

Edit `catalog.json`: add the category (`id`, `name`, `icon`, `color` hex, `order`), course (`id`, `categoryId`, `title`, `description`, `order`, `dir`) or unit (`id`, `title`, `order`, `dir`), create the folder, add lessons, regenerate the manifest. Icon names the app knows: `ic_math`, `ic_science`, `ic_english`, `ic_swe`, `ic_electronics`; unknown names fall back to a default icon.

## Lesson file

```json
{
  "id": "linear-eq-01",
  "version": 1,
  "title": "One-step equations",
  "xp": 10,
  "tags": ["algebra"],
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

Every text field supports `$inline$` and `$$block$$` LaTeX; write a literal dollar as `\$`. In JSON, backslashes are doubled: `"$\\frac{a}{b}$"`. Keep formulas short; wide ones scroll horizontally. The native renderer's supported subset is documented in the app repo once the renderer is built (`HANDOVER.md`, item 1); stick to common commands (`\frac`, `\sqrt`, `^`, `_`, Greek letters, `\sum`, `\int`, `\begin{cases}`) until then.

Copy style: short, calm, specific. One idea per question. The explanation says why, not just what.
