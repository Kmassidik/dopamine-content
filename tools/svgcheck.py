#!/usr/bin/env python3
"""Strict SVG subset checker. The app draws images with a small native renderer that understands
only this subset, so every .svg under content/images/ must stay inside it. STANDARD.md explains it.

Used by tools/standard.py. Run alone with: python3 tools/svgcheck.py [file.svg ...]
The SVG dict below is the single source of truth; tools/build_contract.py exports it.
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PALETTE = """#FFFFFF #14201A #4F5D55 #E4EAE6 #35C46F #17803F #E4F8EC #22994F
#FFC93C #8A5F00 #FFF3CC #D9A21B #FF7FAE #B8305F #FFE4EE #DB5A8A""".split()

SVG = {
    "elements": {"svg", "g", "line", "rect", "circle", "ellipse", "polyline", "polygon", "path", "text"},
    "attributes": {"id", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "width", "height",
                   "points", "d", "fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin",
                   "stroke-dasharray", "opacity", "font-size", "font-weight", "text-anchor"},
    "pathCommands": "MmLlHhVvCcQqZz",
    "colors": {"none", "currentColor"} | {c.lower() for c in PALETTE},
    "maxBytes": 6144,
    "maxElements": 80,
    "maxDepth": 4,
    "viewBoxMin": 20,
    "viewBoxMax": 2000,
    "fontSizeMin": 10,
    "fontSizeMax": 48,
}

NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
NUM_RE = re.compile(rf"^{NUM}$")
NUMS_RE = re.compile(rf"^\s*{NUM}(?:[\s,]+{NUM})*\s*$")
PATH_TOKEN = re.compile(rf"\s*,?\s*(?:([A-Za-z])|({NUM}))")
NS = "{http://www.w3.org/2000/svg}"
NUMERIC = {"x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "width", "height", "stroke-width"}
FILLED = {"rect", "circle", "ellipse", "polyline", "polygon", "path", "text"}
ENUMS = {"stroke-linecap": {"butt", "round", "square"}, "stroke-linejoin": {"miter", "round", "bevel"},
         "font-weight": {"normal", "bold"}, "text-anchor": {"start", "middle", "end"}}


def check_path(d, out):
    allowed = SVG["pathCommands"]
    pos, n = 0, len(d)
    while pos < n:
        if not d[pos:].strip():
            break
        m = PATH_TOKEN.match(d, pos)
        if not m:
            out.append(("IMAGE-PATH", f"cannot read path data near '{d[pos:pos + 12]}'"))
            return
        if m.group(1) and m.group(1) not in allowed:
            out.append(("IMAGE-PATH", f"path command '{m.group(1)}' is not allowed (use only {allowed}; no arcs)"))
            return
        pos = m.end()


def check_color(name, v, out):
    if v not in SVG["colors"] and v.lower() not in SVG["colors"]:
        out.append(("IMAGE-COLOR", f"{name}=\"{v}\" is not none, currentColor or a palette colour"))
    elif v.lower() == "currentcolor" and v != "currentColor":
        out.append(("IMAGE-COLOR", f"write currentColor exactly, not \"{v}\""))


def check_svg(data: bytes):
    """Return a list of (rule_id, message). Empty means the file is inside the subset."""
    out = []
    if len(data) > SVG["maxBytes"]:
        out.append(("IMAGE-SIZE", f"{len(data)} bytes; at most {SVG['maxBytes']}"))
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return out + [("IMAGE-XML", "file is not UTF-8")]
    low = text.lower()
    if "<!doctype" in low or "<!entity" in low:
        return out + [("IMAGE-XML", "DOCTYPE and ENTITY are not allowed")]
    body = text.lstrip("﻿")
    if re.search(r"<\?(?!xml\s)", body) or body.find("<?xml", 1) > 0:
        return out + [("IMAGE-XML", "processing instructions are not allowed (only the XML declaration)")]
    try:
        root = ET.fromstring(body.encode("utf-8"))
    except ET.ParseError as e:
        return out + [("IMAGE-XML", f"not well-formed XML: {e}")]
    if root.tag != NS + "svg" and root.tag != "svg":
        return out + [("IMAGE-ELEMENT", "the root element must be <svg>")]

    vb = root.get("viewBox")
    if vb is None:
        out.append(("IMAGE-VIEWBOX", "the root <svg> needs viewBox=\"0 0 W H\""))
    else:
        parts = vb.replace(",", " ").split()
        ok = len(parts) == 4 and all(NUM_RE.match(p) for p in parts)
        if ok and (float(parts[0]) != 0 or float(parts[1]) != 0):
            ok = False
        if ok:
            w, h = float(parts[2]), float(parts[3])
            lo, hi = SVG["viewBoxMin"], SVG["viewBoxMax"]
            if not (lo <= w <= hi and lo <= h <= hi):
                out.append(("IMAGE-VIEWBOX", f"viewBox width and height must be {lo} to {hi}"))
        else:
            out.append(("IMAGE-VIEWBOX", f"viewBox \"{vb}\" must be four numbers \"0 0 W H\""))

    count = 0

    def walk(el, depth, filled):
        nonlocal count
        count += 1
        tag = el.tag
        if tag.startswith(NS):
            tag = tag[len(NS):]
        if tag not in SVG["elements"]:
            out.append(("IMAGE-ELEMENT", f"<{tag.split('}')[-1]}> is not allowed"))
            return
        if depth > SVG["maxDepth"]:
            out.append(("IMAGE-SIZE", f"nesting deeper than {SVG['maxDepth']} at <{tag}>"))
        for name, v in el.attrib.items():
            root_ok = el is root and name in ("viewBox", "width", "height")
            if name not in SVG["attributes"] and not root_ok:
                out.append(("IMAGE-ATTR", f"attribute '{name}' on <{tag}> is not allowed"))
                continue
            if "url(" in v.lower() or "javascript:" in v.lower():
                out.append(("IMAGE-ATTR", f"'{name}' must not contain url() or scripts"))
            if root_ok and name != "viewBox":
                continue
            if name in ("fill", "stroke"):
                check_color(name, v, out)
            elif name in NUMERIC and not NUM_RE.match(v):
                out.append(("IMAGE-ATTR", f"{name}=\"{v}\" must be a plain number"))
            elif name == "points" and not NUMS_RE.match(v):
                out.append(("IMAGE-ATTR", "points must be numbers only"))
            elif name == "stroke-dasharray" and v != "none" and not NUMS_RE.match(v):
                out.append(("IMAGE-ATTR", "stroke-dasharray must be numbers only"))
            elif name == "opacity" and not (NUM_RE.match(v) and 0 <= float(v) <= 1):
                out.append(("IMAGE-ATTR", "opacity must be a number from 0 to 1"))
            elif name in ENUMS and v not in ENUMS[name]:
                out.append(("IMAGE-ATTR" if name != "font-weight" and name != "text-anchor" else "IMAGE-TEXT",
                            f"{name}=\"{v}\" must be one of {'|'.join(sorted(ENUMS[name]))}"))
            elif name == "font-size":
                if not NUM_RE.match(v) or not SVG["fontSizeMin"] <= float(v) <= SVG["fontSizeMax"]:
                    out.append(("IMAGE-TEXT", f"font-size must be {SVG['fontSizeMin']} to {SVG['fontSizeMax']}"))
            elif name == "d":
                check_path(v, out)
        if tag == "path" and "d" not in el.attrib:
            out.append(("IMAGE-PATH", "<path> needs a d attribute"))
        has_fill = filled or "fill" in el.attrib
        if tag in FILLED and not has_fill:
            out.append(("IMAGE-FILL", f"<{tag}> needs an explicit fill (here or on a parent <g>); SVG defaults to black"))
        if tag == "text":
            if len(el) or not (el.text or "").strip():
                out.append(("IMAGE-TEXT", "<text> must hold plain character data only"))
        else:
            if (el.text or "").strip():
                out.append(("IMAGE-XML", f"<{tag}> must not contain text"))
        for child in el:
            if not isinstance(child.tag, str):
                continue
            walk(child, depth + 1, has_fill)
            if (child.tail or "").strip():
                out.append(("IMAGE-XML", f"stray text inside <{tag}>"))

    walk(root, 1, False)
    if count > SVG["maxElements"]:
        out.append(("IMAGE-SIZE", f"{count} elements; at most {SVG['maxElements']}"))
    return out


if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:] or sorted(str(f) for f in (Path(__file__).resolve().parent.parent / "content" / "images").glob("*.svg")):
        for rule, msg in check_svg(Path(p).read_bytes()):
            print(f"FAIL [{rule}] {p}: {msg}")
            bad += 1
    print("svgcheck: ok" if not bad else "")
    sys.exit(1 if bad else 0)
