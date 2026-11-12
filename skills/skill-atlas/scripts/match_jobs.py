#!/usr/bin/env python3
"""Rank job listings against a skill-atlas profile.

Usage:
  python3 match_jobs.py PROFILE.json JOBS.json [--top 30] [--min 0.35] [--out matches.json] [--md matches.md]

JOBS.json may be a list of objects or an object with a "jobs" list (the Yggdrasil
opportunities.json shape). Each job needs a "title"; "description", "org", "location",
"tags", "url" and "id" are used when present. Title-only listings are scored on the title,
so a full description raises confidence.

Scoring mirrors the atlas page: each skill cluster gets a 0-1 demand score from keyword hits
(3 hits = full demand); a role scores on how much of its skills the job asks for and how much
of the job's demand the role covers, plus title overlap. Output lists the best role, the score,
the clusters asked for and the evidence ids to cite. It never applies to anything.
Python 3.8+, standard library only.
"""
import argparse
import json
import re
import sys
from pathlib import Path

STOP = {"senior", "junior", "lead", "staff", "principal", "sr", "jr", "remote", "the", "and", "of", "for", "with",
        "engineer", "developer", "i", "ii", "iii", "a", "an", "in", "to", "on", "at", "or", "/", "-", "&"}
HITS_FOR_FULL = 3  # keyword hits after which a cluster counts as fully asked for (matches the page)
TITLE_ONLY_DISCOUNT = 0.8  # a listing with no description can at best reach 80%: fetch the description to confirm


def hit(text, kw):
    k = re.escape(kw.lower().strip())
    return bool(k) and re.search(r"(^|[^a-z0-9])" + k + r"([^a-z0-9]|$)", text) is not None


def words(s):
    return {w for w in re.findall(r"[a-z0-9+#.]+", s.lower()) if w not in STOP and len(w) > 1}


def load_jobs(raw):
    """Accept a list, {"jobs": [...]}, or {"jobs": {id: job}} (Yggdrasil's cache); drop inactive listings."""
    jobs = raw.get("jobs", []) if isinstance(raw, dict) else raw
    if isinstance(jobs, dict):
        jobs = [{"id": k, **v} if isinstance(v, dict) else v for k, v in jobs.items()]
    return [j for j in jobs if isinstance(j, dict) and j.get("active", True) is not False]


def score_job(p, job, focus=None):
    """focus: optional set of role ids or lowercase title fragments; only those roles can be the best match."""
    title = job.get("title") or ""
    text = " ".join(str(job.get(k) or "") for k in ("title", "description", "org")).lower()
    text += " " + " ".join(job.get("tags") or []).lower()
    clusters = {c["id"]: c for c in p["clusters"]}
    sc, raw = {}, {}
    for cid, c in clusters.items():
        n = sum(1 for k in c.get("keywords", []) if hit(text, k))
        raw[cid] = n
        sc[cid] = min(1.0, n / HITS_FOR_FULL)
    total = sum(sc.values())
    tw = words(title)
    best = None
    for r in p["roles"]:
        if focus and r.get("id") not in focus and not any(f in r["title"].lower() for f in focus):
            continue
        rc = [c for c in r.get("clusters", []) if c in clusters]
        if not rc:
            continue
        cover = sum(sc[c] for c in rc)
        role_side = cover / len(rc)
        job_side = cover / total if total else 0
        rw = words(r["title"]) | {w for k in r.get("keywords", []) for w in words(k)}
        title_overlap = len(tw & rw) / max(1, len(tw)) if tw else 0
        kw_bonus = 0.05 * sum(1 for k in r.get("keywords", []) if hit(text, k))
        s = 0.35 * role_side + 0.30 * job_side + 0.35 * title_overlap + kw_bonus + 0.03 * (r.get("tier", 2) - 2)
        s = max(0.0, min(1.0, s))
        if best is None or s > best[0]:
            best = (s, r)
    if best is None:
        return None
    role_ids = set(best[1].get("clusters", []))
    # Rank asks by raw keyword hits (boilerplate trips one keyword; real asks trip several), role skills first on ties.
    asked = sorted([c for c in sc if raw[c] > 0], key=lambda c: (-raw[c], c not in role_ids))
    strong_asks = [c for c in asked if raw[c] >= 2] or asked[:3]
    order = list(best[1].get("clusters", []))  # the role's first skill weighs most
    role_cl = set(order)
    status_rank = {"live": 0, "preview": 1}

    def ev_key(e):
        ec = set(e.get("clusters", []))
        weight = sum(len(order) - i for i, c in enumerate(order) if c in ec)
        return (-weight, status_rank.get(e.get("status"), 2), 0 if e.get("bullet") else 1)

    cite = [e["id"] for e in sorted(p["evidence"], key=ev_key) if role_cl & set(e.get("clusters", []))][:4]
    thin = [c for c in strong_asks if clusters[c].get("depth", 3) <= 2]
    has_desc = bool(job.get("description"))
    # A title alone is weak evidence of fit, so title-only listings are discounted.
    final = best[0] if has_desc else best[0] * TITLE_ONLY_DISCOUNT
    return {"score": round(final, 3), "role": best[1]["title"], "role_id": best[1].get("id"),
            "asked": strong_asks[:6], "asked_all": asked, "thin": thin, "cite": cite,
            "confidence": "description" if has_desc else "title only"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("profile")
    ap.add_argument("jobs")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--min", type=float, default=0.35, help="drop matches below this score")
    ap.add_argument("--kind", default="job", help="keep only listings with this kind when present ('' keeps all)")
    ap.add_argument("--out", default="matches.json")
    ap.add_argument("--md")
    ap.add_argument("--focus", default="", help="comma-separated role ids or title fragments to match against")
    a = ap.parse_args()
    try:
        p = json.loads(Path(a.profile).read_text(encoding="utf-8"))
        raw = json.loads(Path(a.jobs).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"error: {e}")
    jobs = load_jobs(raw)
    if a.kind:
        jobs = [j for j in jobs if j.get("kind", a.kind) == a.kind]
    res = []
    for j in jobs:
        m = score_job(p, j, {f.strip().lower() for f in a.focus.split(",") if f.strip()} or None)
        if m and m["score"] >= a.min:
            res.append({**{k: j.get(k) for k in ("id", "title", "org", "location", "url", "posted")}, **m})
    res.sort(key=lambda x: -x["score"])
    res = res[: a.top]
    Path(a.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"scored {len(jobs)} listings; kept {len(res)} at or above {a.min}; wrote {a.out}")
    if a.md:
        names = {e["id"]: e["name"] for e in p["evidence"]}
        lines = ["| Score | Title | Org | Best role | Cite | Based on |", "|---|---|---|---|---|---|"]
        for r in res:
            t = f"[{r['title']}]({r['url']})" if r.get("url") else r["title"]
            lines.append(f"| {round(r['score'] * 100)}% | {t} | {r.get('org') or ''} | {r['role']} | {', '.join(names.get(i, i) for i in r['cite'])} | {r['confidence']} |")
        Path(a.md).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote {a.md}")


if __name__ == "__main__":
    main()
