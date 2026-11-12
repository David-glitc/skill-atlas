#!/usr/bin/env python3
"""Validate a skill-atlas profile.json and render it into a single HTML page.

Usage:
  python3 build_atlas.py PROFILE.json [--out atlas.html] [--check]

--check validates only and writes nothing. Exit code 1 means errors were found;
warnings never fail the build. Python 3.8+, standard library only.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "atlas-template.html"

REQUIRED = ["person", "families", "clusters", "fields", "roles", "evidence"]
# Strings that suggest a secret or private identifier slipped into the profile.
SECRET_PATTERNS = [
    (re.compile(r"\b0x[0-9a-fA-F]{64}\b"), "a 32-byte hex value (private key?)"),
    (re.compile(r"\b(sk|rk)_(live|test)_[0-9A-Za-z]{8,}"), "a Stripe-style secret key"),
    (re.compile(r"\bgh[pousr]_[0-9A-Za-z]{20,}"), "a GitHub token"),
    (re.compile(r"\bxox[abpr]-[0-9A-Za-z-]{10,}"), "a Slack token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a PEM private key"),
    (re.compile(r"\b(api[_-]?key|secret|password|seed phrase)\s*[:=]", re.I), "a credential assignment"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "an email address"),
]


def validate(p):
    errors, warnings = [], []
    for k in REQUIRED:
        if k not in p:
            errors.append(f"missing top-level key '{k}'")
    if errors:
        return errors, warnings

    fam_ids = {f.get("id") for f in p["families"]}
    if len(p["families"]) > 3:
        warnings.append("more than 3 families: the 4th and later render in neutral grey")

    cids = [c.get("id") for c in p["clusters"]]
    if len(set(cids)) != len(cids):
        errors.append("cluster ids are not unique")
    cset = set(cids)
    for c in p["clusters"]:
        if c.get("family") not in fam_ids:
            errors.append(f"cluster {c.get('id')} has unknown family '{c.get('family')}'")
        d = c.get("depth")
        if not isinstance(d, (int, float)) or not 1 <= d <= 5:
            errors.append(f"cluster {c.get('id')} depth must be 1-5")
        if not c.get("keywords"):
            warnings.append(f"cluster {c.get('id')} has no keywords, so job matching ignores it")

    fids = {f.get("id") for f in p["fields"]}
    for f in p["fields"]:
        for k, v in (f.get("weights") or {}).items():
            if k not in cset:
                errors.append(f"field {f.get('id')} weights unknown cluster '{k}'")
            if not isinstance(v, (int, float)) or not 0 <= v <= 3:
                errors.append(f"field {f.get('id')} weight for {k} must be 0-3")

    for r in p["roles"]:
        t = r.get("title", "?")
        if r.get("tier") not in (1, 2, 3):
            errors.append(f"role '{t}' tier must be 1, 2 or 3")
        for x in r.get("fields", []):
            if x not in fids:
                errors.append(f"role '{t}' has unknown field '{x}'")
        for x in r.get("clusters", []):
            if x not in cset:
                errors.append(f"role '{t}' has unknown cluster '{x}'")
        if not r.get("proof"):
            warnings.append(f"role '{t}' has no proof text")

    eids = [e.get("id") for e in p["evidence"]]
    if len(set(eids)) != len(eids):
        errors.append("evidence ids are not unique")
    proven = set()
    for e in p["evidence"]:
        for x in e.get("clusters", []):
            if x not in cset:
                errors.append(f"evidence '{e.get('name')}' has unknown cluster '{x}'")
            proven.add(x)
        if not e.get("clusters"):
            warnings.append(f"evidence '{e.get('name')}' is tagged with no cluster")
    for c in cset - proven:
        errors.append(f"cluster {c} has no evidence: every skill claim needs at least one project")

    for kind in ("combos", "services"):
        for item in p.get(kind, []):
            for x in item.get("clusters", []):
                if x not in cset:
                    errors.append(f"{kind[:-1]} '{item.get('name')}' has unknown cluster '{x}'")
    layer_names = {l.get("name") for l in p.get("layers", [])}
    if layer_names:
        for s in p.get("services", []):
            if s.get("layer") not in layer_names:
                errors.append(f"service '{s.get('name')}' has unknown layer '{s.get('layer')}'")

    blob = json.dumps(p, ensure_ascii=False)
    for rx, what in SECRET_PATTERNS:
        m = rx.search(blob)
        if m:
            warnings.append(f"possible {what} in the profile near '{m.group(0)[:24]}'. Remove it before publishing")
    if "—" in blob:
        warnings.append("profile text contains em dashes; the house style avoids them")
    return errors, warnings


def render(p, title):
    tpl = TEMPLATE.read_text(encoding="utf-8")
    data = json.dumps(p, ensure_ascii=False, indent=None)
    data = data.replace("</", "<\\/")  # keep </script> inside strings from closing the block
    name = (p.get("person") or {}).get("name") or "Skill"
    page_title = title or f"{name} Skill Atlas"
    return tpl.replace("__ATLAS_TITLE__", html.escape(page_title)).replace("__ATLAS_DATA__", data)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("profile")
    ap.add_argument("--out", default="atlas.html")
    ap.add_argument("--title")
    ap.add_argument("--check", action="store_true", help="validate only")
    a = ap.parse_args()
    try:
        p = json.loads(Path(a.profile).read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"error: {a.profile} not found")
    except json.JSONDecodeError as e:
        sys.exit(f"error: {a.profile} is not valid JSON ({e})")
    errors, warnings = validate(p)
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("error:", e)
    if errors:
        sys.exit(1)
    counts = {k: len(p.get(k, [])) for k in ("clusters", "fields", "roles", "combos", "services", "evidence", "research")}
    print("ok:", ", ".join(f"{v} {k}" for k, v in counts.items()))
    if a.check:
        return
    out = Path(a.out)
    out.write_text(render(p, a.title), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
