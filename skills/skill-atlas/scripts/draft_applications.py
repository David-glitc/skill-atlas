#!/usr/bin/env python3
"""Build a review queue of application drafts from a skill-atlas profile and a job index.

Usage:
  python3 draft_applications.py PROFILE.json JOBS.json --out-dir drafts [--fetch 40] [--top 15] [--min 0.5]

Steps: rank every listing by title (match_jobs.py scoring), fetch the full description for
the best --fetch listings from public Greenhouse, Lever and Ashby job APIs, re-score with the
description, then write one folder per kept job:

  job.md       listing, score, closest role, what it asks for, thin spots, description excerpt
  cv.md        CV variant: headline, summary, evidence bullets ordered for this job, skills
  opening.md   short opening paragraph naming the asks and the projects that prove them

INDEX.md lists the queue and marks listings that are new since the previous run.
Nothing is submitted or sent. Python 3.8+, standard library only.
"""
import argparse
import html
import http.client
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from match_jobs import load_jobs, score_job  # noqa: E402

UA = "skill-atlas-job-matcher/1.0"  # generic client name; no personal details in requests
REQUEST_GAP_S = 0.6  # pause between API calls to stay polite to public job boards
DESC_EXCERPT = 1800  # characters of description kept in job.md

GH = re.compile(r"https?://(?:job-boards|boards)(\.eu)?\.greenhouse\.io/([^/]+)/jobs/(\d+)")
LEVER = re.compile(r"https?://jobs\.lever\.co/([^/]+)/([0-9a-f-]{36})")
ASHBY = re.compile(r"https?://jobs\.ashbyhq\.com/([^/]+)/([0-9a-f-]{36})")


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def strip_html(s):
    s = html.unescape(s or "")
    s = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", s, flags=re.I)
    s = re.sub(r"<li[^>]*>", "- ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


class Fetcher:
    def __init__(self, cache_path):
        self.cache_path = cache_path
        self.cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
        self.ashby_boards = {}
        self.errors = 0

    def save(self):
        self.cache_path.write_text(json.dumps(self.cache))

    def description(self, url):
        if not url:
            return ""
        if url in self.cache:
            return self.cache[url]
        text = ""
        try:
            m = GH.match(url)
            if m:
                eu, board, jid = m.groups()
                d = get_json(f"https://boards-api{eu or ''}.greenhouse.io/v1/boards/{board}/jobs/{jid}")
                text = strip_html(d.get("content", ""))
            if not text and LEVER.match(url):
                c, i = LEVER.match(url).groups()
                d = get_json(f"https://api.lever.co/v0/postings/{c}/{i}")
                parts = [d.get("descriptionPlain", "")]
                for lst in d.get("lists", []):
                    parts.append(lst.get("text", "") + "\n" + strip_html(lst.get("content", "")))
                parts.append(d.get("additionalPlain", ""))
                text = "\n\n".join(p for p in parts if p)
            if not text and ASHBY.match(url):
                board, i = ASHBY.match(url).groups()
                if board not in self.ashby_boards:
                    self.ashby_boards[board] = []  # remember failures too, so a bad board is not retried per job
                    self.ashby_boards[board] = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}").get("jobs", [])
                    time.sleep(REQUEST_GAP_S)
                for j in self.ashby_boards[board]:
                    if j.get("id") == i:
                        text = j.get("descriptionPlain") or strip_html(j.get("descriptionHtml", ""))
                        break
        except (urllib.error.URLError, http.client.HTTPException, OSError, json.JSONDecodeError, ValueError):
            self.errors += 1
            text = ""
        self.cache[url] = text
        if len(self.cache) % 10 == 0:
            self.save()  # keep progress if the run is interrupted
        time.sleep(REQUEST_GAP_S)
        return text


def slug(s, n=40):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:n] or "job"


def write_drafts(p, job, m, folder):
    C = {c["id"]: c for c in p["clusters"]}
    E = {e["id"]: e for e in p["evidence"]}
    role = next((r for r in p["roles"] if r.get("id") == m["role_id"]), None) or {}
    person = p.get("person", {})
    def soft_lower(s):  # "Trading systems" -> "trading systems", but keep "AI agents" and "LLM"
        return s[0].lower() + s[1:] if re.match(r"^[A-Z][a-z]", s) else s
    asked_names = [soft_lower(C[c]["name"]) for c in m["asked"][:3]]
    cited = [E[i] for i in m["cite"] if i in E]
    rc = set(role.get("clusters", []))
    more = [e for e in p["evidence"] if e not in cited and e.get("bullet") and rc & set(e.get("clusters", []))][:4]
    folder.mkdir(parents=True, exist_ok=True)

    desc = (job.get("description") or "").strip()
    (folder / "job.md").write_text("\n".join([
        f"# {job.get('title')} · {job.get('org') or ''}",
        "",
        f"- Link: {job.get('url') or 'n/a'}",
        f"- Location: {job.get('location') or 'n/a'}",
        f"- Score: {round(m['score'] * 100)}% ({m['confidence']})",
        f"- Closest role in your profile: {m['role']}",
        f"- Asks for: {', '.join(C[c]['name'] for c in m['asked']) or 'unclear from the text'}",
        f"- Thin spots: {', '.join(C[c]['name'] for c in m['thin']) or 'none found'}",
        "- Status: draft. Review before sending.",
        "",
        "## Description excerpt",
        "",
        desc[:DESC_EXCERPT] + ("…" if len(desc) > DESC_EXCERPT else "") if desc else "_No description fetched. Open the link before deciding._",
        "",
    ]))

    skills = []
    for c in role.get("clusters", []):
        skills += C[c].get("skills", [])[:5]
    cv = [f"# {person.get('name', '')}", "", f"**{role.get('title', m['role'])}.** {person.get('headline', '')}", ""]
    if person.get("bio") or person.get("summary"):
        cv += [person.get("bio") or person["summary"], ""]
    cv += ["## Selected work", ""] + [f"- {e.get('bullet') or e.get('summary')}" for e in cited + more] + [""]
    cv += ["## Skills", "", ", ".join(dict.fromkeys(skills)), ""]
    links = person.get("links") or []
    if links:
        cv += ["## Links", "", " · ".join(f"[{l['label']}]({l['url']})" for l in links), ""]
    (folder / "cv.md").write_text("\n".join(cv))

    hl = (person.get("headline") or "").rstrip(".")
    if re.match(r"^[A-Z][a-z]", hl):
        hl = hl[0].lower() + hl[1:]
    asks = ", ".join(asked_names[:-1]) + (" and " if len(asked_names) > 1 else "") + (asked_names[-1] if asked_names else "")
    lines = [f"Hi{' ' + job['org'] + ' team' if job.get('org') else ''},", "",
             f"I'm {person.get('name', '')}{', ' + hl if hl else ''}. The {job.get('title')} role asks for {asks or 'work I already do'}. "
             "That is the work I already do:", ""]
    lines += [f"- {e.get('bullet') or e.get('summary')}" for e in cited[:3]]
    lines += ["", "I'd be glad to walk through any of these and how they map to your roadmap.", ""]
    if m["thin"]:
        lines += [f"<!-- Thin spots to address or leave out: {', '.join(C[c]['name'] for c in m['thin'])} -->", ""]
    (folder / "opening.md").write_text("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("profile")
    ap.add_argument("jobs")
    ap.add_argument("--out-dir", default="drafts")
    ap.add_argument("--fetch", type=int, default=40, help="fetch descriptions for this many top title matches")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--min", type=float, default=0.5)
    ap.add_argument("--exclude-org", action="append", default=[], help="skip an org (repeatable)")
    ap.add_argument("--focus", default="", help="comma-separated role ids or title fragments, e.g. the lead lane")
    a = ap.parse_args()
    try:
        p = json.loads(Path(a.profile).read_text(encoding="utf-8"))
        raw = json.loads(Path(a.jobs).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"error: {e}")
    jobs = [j for j in load_jobs(raw) if j.get("kind", "job") == "job"]
    skip = {o.lower() for o in a.exclude_org}
    jobs = [j for j in jobs if (j.get("org") or "").lower() not in skip]
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    focus = {f.strip().lower() for f in a.focus.split(",") if f.strip()} or None
    first = sorted(((score_job(p, j, focus) or {"score": 0}, j) for j in jobs), key=lambda x: -x[0]["score"])
    fetcher = Fetcher(out / ".descriptions.json")
    rescored = []
    for m, j in first[: a.fetch]:
        if not j.get("description"):
            j = {**j, "description": fetcher.description(j.get("url"))}
        m2 = score_job(p, j, focus)
        if m2 and m2["score"] >= a.min:
            rescored.append((m2, j))
    fetcher.save()
    rescored.sort(key=lambda x: -x[0]["score"])
    rescored = rescored[: a.top]

    prev_path = out / "index.json"
    prev = {r["id"] for r in json.loads(prev_path.read_text())} if prev_path.exists() else set()
    rows, index = [], []
    for m, j in rescored:
        folder = out / f"{round(m['score'] * 100):03d}-{slug(j.get('org'), 20)}-{slug(j.get('title'))}-{str(j.get('id') or '')[:6]}"
        write_drafts(p, j, m, folder)
        new = j.get("id") not in prev
        index.append({"id": j.get("id"), "title": j.get("title"), "org": j.get("org"), "url": j.get("url"),
                      "score": m["score"], "role": m["role"], "confidence": m["confidence"], "folder": folder.name})
        rows.append(f"| {'new' if new else ''} | {round(m['score'] * 100)}% | [{j.get('title')}]({j.get('url')}) | {j.get('org') or ''} | {m['role']} | {m['confidence']} | `{folder.name}` |")
    prev_path.write_text(json.dumps(index, indent=1))
    (out / "INDEX.md").write_text("\n".join([
        "# Application drafts", "",
        f"{len(rows)} listings at or above {round(a.min * 100)}%, from {len(jobs)} scored and {min(a.fetch, len(first))} checked with full descriptions"
        f" ({fetcher.errors} fetch errors). Drafts only: review, edit and send them yourself.", "",
        "| | Score | Title | Org | Closest role | Based on | Folder |", "|---|---|---|---|---|---|---|", *rows, ""]))
    print(f"scored {len(jobs)}; fetched {min(a.fetch, len(first))} descriptions ({fetcher.errors} errors); wrote {len(rows)} drafts to {out}")


if __name__ == "__main__":
    main()
