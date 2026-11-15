#!/usr/bin/env python3
"""Validate manifest.json and every lesson file. Needs: pip install jsonschema"""
import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))
import standard  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
errors = []


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def schema_check(doc, schema_file: str, label: str):
    v = Draft7Validator(load(ROOT / "schema" / schema_file))
    for e in sorted(v.iter_errors(doc), key=lambda e: list(e.path)):
        where = "/".join(str(x) for x in e.path) or "(root)"
        errors.append(f"{label}: {where}: {e.message}")


def semantic_check(lesson: dict, label: str):
    seen = set()
    for q in lesson["questions"]:
        qid, t = q["id"], q["type"]
        if qid in seen:
            errors.append(f"{label}: duplicate question id {qid}")
        seen.add(qid)
        if t in ("multiple_choice", "fill_blank"):
            if q["answerIndex"] >= len(q["choices"]):
                errors.append(f"{label}: {qid}: answerIndex out of range")
            if len(set(q["choices"])) != len(q["choices"]):
                errors.append(f"{label}: {qid}: duplicate choices")
        if t == "match_pairs":
            lefts = [p[0] for p in q["pairs"]]
            rights = [p[1] for p in q["pairs"]]
            if len(set(lefts)) != len(lefts) or len(set(rights)) != len(rights):
                errors.append(f"{label}: {qid}: duplicate items in pairs")
        if t == "order_steps" and len(set(q["steps"])) != len(q["steps"]):
            errors.append(f"{label}: {qid}: duplicate steps")
        if "image" in q and not (ROOT / q["image"]).is_file():
            errors.append(f"{label}: {qid}: image not found: {q['image']}")


def learn_check(lesson: dict, label: str):
    seen = set()
    for pg in lesson.get("learn", []):
        if pg["id"] in seen:
            errors.append(f"{label}: duplicate learn page id {pg['id']}")
        seen.add(pg["id"])
        if "image" in pg and not (ROOT / pg["image"]).is_file():
            errors.append(f"{label}: learn page {pg['id']}: image not found: {pg['image']}")


def main() -> int:
    manifest = load(ROOT / "manifest.json")
    schema_check(manifest, "manifest.schema.json", "manifest.json")
    lesson_ids = set()
    for course in manifest["courses"]:
        for unit in course["units"]:
            for l in unit["lessons"]:
                if l["id"] in lesson_ids:
                    errors.append(f"duplicate lesson id {l['id']}")
                lesson_ids.add(l["id"])
                p = ROOT / l["path"]
                if not p.is_file():
                    errors.append(f"{l['path']}: file missing")
                    continue
                doc = load(p)
                schema_check(doc, "lesson.schema.json", l["path"])
                if not errors:
                    semantic_check(doc, l["path"])
                    learn_check(doc, l["path"])
                if doc.get("id") != l["id"] or doc.get("version") != l["version"]:
                    errors.append(f"{l['path']}: id/version differ from manifest")
    for course in manifest["courses"]:
        for unit in course["units"]:
            n = unit.get("notes")
            if not n:
                continue
            p = ROOT / n["path"]
            if not p.is_file():
                errors.append(f"{n['path']}: file missing")
                continue
            doc = load(p)
            schema_check(doc, "notes.schema.json", n["path"])
            if doc.get("id") != n["id"] or doc.get("version") != n["version"]:
                errors.append(f"{n['path']}: id/version differ from manifest")
            ids = [b["id"] for b in doc.get("blocks", [])]
            if len(set(ids)) != len(ids):
                errors.append(f"{n['path']}: duplicate block ids")
    for img in manifest["images"]:
        if not (ROOT / img["path"]).is_file():
            errors.append(f"{img['path']}: image missing")
    errors.extend(standard.run(ROOT))
    if errors:
        print("\n".join(errors))
        return 1
    print(f"ok: {len(lesson_ids)} lessons, {len(manifest['images'])} images")
    return 0


if __name__ == "__main__":
    sys.exit(main())
