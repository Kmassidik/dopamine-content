# AGENTS.md (content repo)

You are editing **data that ships to a phone app**. Read `README.md` here, then the app repo's `AGENTS.md`.

- Never edit `manifest.json` by hand. Run `python3 tools/build_manifest.py` after any content change, then `pip install jsonschema && python3 tools/validate.py`. Both must pass before you commit; CI enforces it.
- **Bump `version`** in any lesson you change, or the app will not refetch it (the manifest diff uses version and sha256).
- Never reuse an `id` for different content; never change an id that learners may have progress on.
- Paths: plain relative `a/b/c.json` or `.svg`. No `..`, no leading `/`, no other extensions. The app rejects the whole update if one path is unsafe.
- Keep files small (lesson under 256 KB, image under 1 MB, at most 40 questions) and diagrams as SVG.
- Do not add executable content, scripts, or links the app would open. Content is data only.
- Do not commit AI attribution trailers (no `Co-Authored-By`, no "Generated with"). The owner asked for none on their GitHub.
- Schema changes are breaking changes: bump `schemaVersion` in `catalog.json` only with a matching app release, and record it in the app repo's `DECISIONS.md`.

## The standard is enforced
Read STANDARD.md. Every lesson needs reading pages (`learn`) with a worked example before its practice, and every course needs an `overview`. `python3 tools/validate.py` fails with a rule id for anything that does not fit, and CI runs it. When you add a LaTeX command, it must exist in the app's `ui/math/MathParser.kt` and in `LATEX_OK` in `tools/standard.py`.
