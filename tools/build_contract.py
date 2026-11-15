#!/usr/bin/env python3
"""Generate contract.json: everything the app must understand to read this repo's content.

The app repo keeps a copy (app/src/test/resources/contract.json) and a unit test that fails if the
app's parser, validators or math renderer disagree with it. That is how the two repos stay aligned.

Usage:
  python3 tools/build_contract.py           write contract.json
  python3 tools/build_contract.py --check   exit 1 if contract.json is out of date
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import standard  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "contract.json"


def load(name):
    return json.loads((ROOT / "schema" / name).read_text(encoding="utf-8"))


def build() -> dict:
    lesson = load("lesson.schema.json")
    notes = load("notes.schema.json")
    manifest = load("manifest.schema.json")
    lp = lesson["properties"]
    q = lesson["definitions"]
    page = lesson["definitions"]["learnPage"]["properties"]
    # Limits are read from the schemas, so there is a single source of truth.
    mc = next(a["then"]["properties"] for a in q["question"]["allOf"] if a["if"]["properties"]["type"]["const"] == "multiple_choice")
    ta = next(a["then"]["properties"] for a in q["question"]["allOf"] if a["if"]["properties"]["type"]["const"] == "type_answer")
    mp = next(a["then"]["properties"] for a in q["question"]["allOf"] if a["if"]["properties"]["type"]["const"] == "match_pairs")
    os_ = next(a["then"]["properties"] for a in q["question"]["allOf"] if a["if"]["properties"]["type"]["const"] == "order_steps")
    ov = manifest["properties"]["courses"]["items"]["properties"]["overview"]["properties"]
    nb = notes["properties"]["blocks"]
    nblock = notes["definitions"]["block"]["properties"]
    limits = {
        "idPattern": lp["id"]["pattern"],
        "titleMax": lp["title"]["maxLength"],
        "xpMin": lp["xp"]["minimum"], "xpMax": lp["xp"]["maximum"],
        "questionsMin": lp["questions"]["minItems"], "questionsMax": lp["questions"]["maxItems"],
        "textMax": q["text"]["maxLength"],
        "choicesMin": mc["choices"]["minItems"], "choicesMax": mc["choices"]["maxItems"],
        "answerIndexMax": mc["answerIndex"]["maximum"],
        "acceptedMin": ta["accepted"]["minItems"], "acceptedMax": ta["accepted"]["maxItems"],
        "acceptedItemMax": ta["accepted"]["items"]["maxLength"],
        "pairsMin": mp["pairs"]["minItems"], "pairsMax": mp["pairs"]["maxItems"],
        "stepsMin": os_["steps"]["minItems"], "stepsMax": os_["steps"]["maxItems"],
        "learnMax": lp["learn"]["maxItems"],
        "pageTitleMax": page["title"]["maxLength"],
        "exampleStepsMin": page["steps"]["minItems"], "exampleStepsMax": page["steps"]["maxItems"],
        "notesBlocksMax": nb["maxItems"],
        "noteItemsMax": nblock["items"]["maxItems"],
        "summaryMax": ov["summary"]["maxLength"],
        "outcomesMax": ov["outcomes"]["maxItems"],
        "requirementsMax": ov["requirements"]["maxItems"],
        "minutesMax": ov["minutes"]["maximum"],
        "codeMax": page["code"]["maxLength"],
        "codeLines": standard.RULES["code_lines"],
        "codeWidth": standard.RULES["code_width"],
    }
    return {
        "contractVersion": standard.CONTRACT_VERSION,
        "questionTypes": standard.QUESTION_TYPES,
        "pageKinds": standard.PAGE_KINDS,
        "noteKinds": standard.NOTE_KINDS,
        "latexCommands": sorted(standard.LATEX_OK),
        "limits": limits,
    }


def dump(d: dict) -> str:
    return json.dumps(d, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main() -> int:
    text = dump(build())
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("contract.json is out of date. Run: python3 tools/build_contract.py")
            return 1
        return 0
    OUT.write_text(text, encoding="utf-8")
    print("wrote contract.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
