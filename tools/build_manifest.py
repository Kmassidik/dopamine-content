#!/usr/bin/env python3
"""Generate manifest.json from catalog.json and the lesson files.

Usage:
  python3 tools/build_manifest.py           write manifest.json
  python3 tools/build_manifest.py --check   exit 1 if manifest.json is out of date
"""
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest.json"
ORDER_RE = re.compile(r"lesson-(\d+)\.json$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(content_version: str) -> dict:
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    used_images = set()
    courses = []
    for course in catalog["courses"]:
        units = []
        for unit in course["units"]:
            unit_dir = ROOT / course["dir"] / unit["dir"]
            lessons = []
            for f in sorted(unit_dir.glob("lesson-*.json")):
                m = ORDER_RE.search(f.name)
                if not m:
                    continue
                data = json.loads(f.read_text(encoding="utf-8"))
                for q in data.get("questions", []) + data.get("learn", []):
                    if "image" in q:
                        used_images.add(q["image"])
                lessons.append({
                    "id": data["id"],
                    "title": data["title"],
                    "path": f.relative_to(ROOT).as_posix(),
                    "version": data["version"],
                    "sha256": sha256(f),
                    "sizeBytes": f.stat().st_size,
                    "order": int(m.group(1)),
                })
            lessons.sort(key=lambda l: l["order"])
            units.append({"id": unit["id"], "title": unit["title"],
                          "order": unit["order"], "lessons": lessons})
        courses.append({
            "id": course["id"], "categoryId": course["categoryId"],
            "title": course["title"], "description": course["description"],
            "order": course["order"], "units": units,
            **({"overview": course["overview"]} if "overview" in course else {}),
        })
    images = []
    for rel in sorted(used_images):
        p = ROOT / rel
        if not p.is_file():
            sys.exit(f"error: image referenced by a lesson is missing: {rel}")
        images.append({"path": rel, "sha256": sha256(p), "sizeBytes": p.stat().st_size})
    return {
        "schemaVersion": catalog["schemaVersion"],
        "contentVersion": content_version,
        "minAppVersion": catalog["minAppVersion"],
        "categories": catalog["categories"],
        "courses": courses,
        "images": images,
    }


def dump(manifest: dict) -> str:
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    check = "--check" in sys.argv
    old = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else None
    # Keep the existing contentVersion unless something else changed.
    probe = build(old["contentVersion"] if old else "pending")
    if old is not None and {**old, "contentVersion": ""} == {**probe, "contentVersion": ""}:
        return 0
    if check:
        print("manifest.json is out of date. Run: python3 tools/build_manifest.py")
        return 1
    today = datetime.date.today().strftime("%Y.%m.%d")
    version = today
    if old and old["contentVersion"].split("+")[0] == today:
        n = int(old["contentVersion"].split("+")[1]) + 1 if "+" in old["contentVersion"] else 1
        version = f"{today}+{n}"
    MANIFEST.write_text(dump(build(version)), encoding="utf-8")
    print(f"wrote manifest.json (contentVersion {version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
