#!/usr/bin/env python3
"""List a GitHub account's repositories for a skill-atlas profile, using the gh CLI.

Usage:
  python3 scan_github.py OWNER [--readmes 40] [--include-private] [--out github-scan.json]

Records name, description, primary language, visibility, fork flag, stars, topics and
last update for every repo. With --readmes N it also fetches the first 800 characters
of the README for the N most recently updated non-fork repos. Private repos are left out
unless --include-private is given, because their names can be confidential.

Requires an authenticated gh CLI (gh auth status). Python 3.8+, standard library only.
"""
import argparse
import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path

FIELDS = "name,description,primaryLanguage,isPrivate,isFork,stargazerCount,updatedAt,repositoryTopics,url,homepageUrl"


def gh(*args, timeout=60):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "gh failed")
    return r.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("owner")
    ap.add_argument("--readmes", type=int, default=0)
    ap.add_argument("--include-private", action="store_true")
    ap.add_argument("--limit", type=int, default=1000)
    ap.add_argument("--out", default="github-scan.json")
    a = ap.parse_args()
    if not shutil.which("gh"):
        sys.exit("error: the gh CLI is not installed. Install it, run `gh auth login`, then retry.")
    try:
        repos = json.loads(gh("repo", "list", a.owner, "--limit", str(a.limit), "--json", FIELDS))
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        sys.exit(f"error: could not list repos for {a.owner}: {e}. Check `gh auth status`.")
    out = []
    for r in repos:
        if r.get("isPrivate") and not a.include_private:
            continue
        out.append({
            "name": r["name"], "description": r.get("description") or "",
            "language": (r.get("primaryLanguage") or {}).get("name") or "",
            "private": r.get("isPrivate"), "fork": r.get("isFork"), "stars": r.get("stargazerCount", 0),
            "updated": (r.get("updatedAt") or "")[:10], "url": r.get("url"), "homepage": r.get("homepageUrl") or "",
            "topics": [t.get("name") for t in (r.get("repositoryTopics") or []) if isinstance(t, dict)],
        })
    out.sort(key=lambda x: x["updated"], reverse=True)
    fetched = 0
    for r in out:
        if fetched >= a.readmes:
            break
        if r["fork"]:
            continue
        try:
            raw = gh("api", f"repos/{a.owner}/{r['name']}/readme", "--jq", ".content", timeout=20)
            r["readme"] = base64.b64decode(raw).decode("utf-8", "replace")[:800]
        except (RuntimeError, subprocess.TimeoutExpired, ValueError):
            r["readme"] = ""
        fetched += 1
    own = [r for r in out if not r["fork"]]
    langs = {}
    for r in own:
        langs[r["language"] or "none"] = langs.get(r["language"] or "none", 0) + 1
    summary = {"owner": a.owner, "repos": len(out), "own": len(own), "public": sum(not r["private"] for r in out),
               "languages": dict(sorted(langs.items(), key=lambda kv: -kv[1]))}
    Path(a.out).write_text(json.dumps({"summary": summary, "repos": out}, indent=1), encoding="utf-8")
    print(json.dumps(summary))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
