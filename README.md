# dopamine-content

Lesson content for the Dopamine Android app. Data only, no code runs from here.

## Layout
- `catalog.json`: categories, courses and units (hand edited).
- `<category>/<course>/<unit>/lesson-NN.json`: lessons.
- `images/*.svg`: diagrams referenced by lessons.
- `manifest.json`: generated. Never edit by hand.
- `schema/`: JSON Schemas for the manifest and lessons.

## Publish an update
1. Edit or add lesson files. Bump `version` in a lesson whenever you change it.
2. `python3 tools/build_manifest.py`
3. `pip install jsonschema && python3 tools/validate.py`
4. Commit and push to `main`. In the app, tap Update.

CI fails if `manifest.json` is out of date or any file is invalid.

## Question types
`multiple_choice`, `fill_blank`, `type_answer`, `match_pairs`, `order_steps`. See `math/algebra-1/linear-eq/lesson-01.json` for one of each. Text supports `$inline$` and `$$block$$` LaTeX; write a literal dollar as `\$`.
