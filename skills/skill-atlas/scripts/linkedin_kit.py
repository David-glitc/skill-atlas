#!/usr/bin/env python3
"""Write LinkedIn profile copy from a skill-atlas profile, for the person to paste by hand.

Usage:
  python3 linkedin_kit.py PROFILE.json [--out linkedin.md]

Produces headline options (LinkedIn allows 220 characters), an About section (under
2,600 characters), Featured items from live evidence with URLs, Experience-style bullets
grouped by skill family, and a skills list ordered by depth. It does not log in to or
post on LinkedIn. Python 3.8+, standard library only.
"""
import argparse
import json
import sys
from pathlib import Path

HEADLINE_MAX = 220  # LinkedIn headline limit
ABOUT_MAX = 2600  # LinkedIn About limit


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("profile")
    ap.add_argument("--out", default="linkedin.md")
    a = ap.parse_args()
    try:
        p = json.loads(Path(a.profile).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"error: {e}")
    person, C = p.get("person", {}), {c["id"]: c for c in p["clusters"]}
    deep = sorted(p["clusters"], key=lambda c: -c.get("depth", 0))
    lane = p.get("lane", [])
    strong = [r for r in p["roles"] if r.get("tier") == 3]

    heads = []
    if lane:
        heads.append(f"{lane[0]['title'].rstrip('.')} | {' · '.join(c['short'] for c in deep[:3])}")
    if strong:
        heads.append(f"{strong[0]['title']} · {strong[1]['title'] if len(strong) > 1 else ''} | {person.get('headline', '')}".replace(" ·  |", " |"))
    heads.append(f"{person.get('headline', '')} | {' · '.join(c['short'] for c in deep[:4])}")
    heads = [h[:HEADLINE_MAX] for h in dict.fromkeys(h.strip(" |") for h in heads)]

    bullets = [e for e in p["evidence"] if e.get("bullet")]
    # LinkedIn copy is first person: use person.bio, fall back to summary (which may be second person).
    about = [person.get("bio") or person.get("summary", "")]
    if lane:
        about.append("What I do: " + "; ".join(l["title"].rstrip(".") for l in lane[:4]) + ".")
    about.append("Selected work:\n" + "\n".join(f"• {e['bullet']}" for e in bullets[:5]))
    about_text = "\n\n".join(x for x in about if x)[:ABOUT_MAX]

    featured = [e for e in p["evidence"] if e.get("status") == "live" and e.get("url")]
    out = ["# LinkedIn kit", "", "Paste by hand. Nothing here is posted for you.", "", "## Headline options", ""]
    out += [f"{i + 1}. {h} ({len(h)} chars)" for i, h in enumerate(heads)]
    out += ["", f"## About ({len(about_text)} of {ABOUT_MAX} chars)", "", about_text, "", "## Featured", ""]
    out += [f"- **{e['name']}**: {e.get('summary', '')} {e['url']}" for e in featured] or ["- Add live projects with URLs to the profile."]
    out += ["", "## Experience bullets by area", ""]
    for fam in p["families"]:
        items = [e for e in bullets if any(C[c]["family"] == fam["id"] for c in e.get("clusters", [])[:1])]
        if items:
            out += [f"### {fam['name']}", ""] + [f"- {e['bullet']}" for e in items] + [""]
    skills = []
    for c in deep:
        skills += c.get("skills", [])
    out += ["## Skills (LinkedIn allows 100; list the first 50)", "", ", ".join(list(dict.fromkeys(skills))[:50]), ""]
    Path(a.out).write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {a.out}: {len(heads)} headlines, About {len(about_text)} chars, {len(featured)} featured items")


if __name__ == "__main__":
    main()
