#!/usr/bin/env python3
"""Inventory project folders on this machine for a skill-atlas profile.

Usage:
  python3 scan_local.py [ROOT ...] [--depth 2] [--out local-scan.json]

Finds folders that look like projects (git repo or a manifest such as package.json,
Cargo.toml, pyproject.toml, foundry.toml, Anchor.toml, go.mod) up to --depth levels
below each root (default: the home folder). For each it records name, path, git remote,
commit count, last commit date, file counts by language, manifest description, notable
tooling flags and the first 600 characters of the README.

It never opens .env files, key files or anything under folders that usually hold
dependencies or secrets. Python 3.8+, standard library only.
"""
import argparse
import json
import re
import os
import subprocess
import sys
from pathlib import Path

MANIFESTS = ["package.json", "Cargo.toml", "pyproject.toml", "requirements.txt", "foundry.toml",
             "Anchor.toml", "go.mod", "pubspec.yaml", "composer.json", "deno.json", "hardhat.config.ts",
             "hardhat.config.js", "wrangler.toml", "wrangler.jsonc", "hyperframes.json"]
SKIP_DIRS = {"node_modules", ".git", "target", "dist", "build", "out", ".next", ".venv", "venv", "__pycache__",
             ".cache", ".npm", ".bun", ".local", "go", "google-cloud-sdk", "Downloads", "lib", "vendor",
             ".pnpm-store", ".turbo", "coverage", ".idea", ".vscode", "snap"}
# Folder names that usually hold credentials or backups. Matched as whole name segments so "token-shop" is still scanned.
SECRETISH = re.compile(r"(^|[-_.])(keys?|creds?|credentials|secrets?|backups?)([-_.]|$)|^\.ssh$|^\.gnupg$|^incident", re.I)
EXT_LANG = {".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript", ".mjs": "JavaScript", ".jsx": "JavaScript",
            ".py": "Python", ".rs": "Rust", ".sol": "Solidity", ".go": "Go", ".c": "C", ".h": "C", ".cu": "CUDA",
            ".cpp": "C++", ".php": "PHP", ".dart": "Dart", ".vue": "Vue", ".svelte": "Svelte", ".astro": "Astro",
            ".clar": "Clarity", ".move": "Move", ".lua": "Lua", ".ipynb": "Jupyter", ".sql": "SQL", ".tex": "LaTeX"}
FLAGS = {"Dockerfile": "docker", "docker-compose.yml": "docker", "wrangler.toml": "cloudflare", "wrangler.jsonc": "cloudflare",
         "cloudflare.config.ts": "cloudflare", "vercel.json": "vercel", "foundry.toml": "foundry", "Anchor.toml": "anchor",
         "hardhat.config.ts": "hardhat", "eas.json": "expo", "hyperframes.json": "hyperframes", ".github": "ci"}
MAX_FILES = 4000  # cap per project so a huge monorepo cannot stall the scan


def git(path, *args):
    try:
        r = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def langs(path):
    counts, seen = {}, 0
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for f in filenames:
            lang = EXT_LANG.get(os.path.splitext(f)[1])
            if lang:
                counts[lang] = counts.get(lang, 0) + 1
            seen += 1
            if seen > MAX_FILES:
                return dict(sorted(counts.items(), key=lambda kv: -kv[1])), True
    return dict(sorted(counts.items(), key=lambda kv: -kv[1])), False


def manifest_info(path):
    info = {}
    pj = path / "package.json"
    if pj.is_file():
        try:
            d = json.loads(pj.read_text(encoding="utf-8", errors="replace"))
            info["package"] = {k: d.get(k) for k in ("name", "description") if d.get(k)}
            deps = list((d.get("dependencies") or {}).keys()) + list((d.get("devDependencies") or {}).keys())
            info["deps"] = sorted(deps)[:60]
        except (json.JSONDecodeError, OSError):
            pass
    ct = path / "Cargo.toml"
    if ct.is_file():
        txt = ct.read_text(encoding="utf-8", errors="replace")
        info["cargo"] = txt[:400]
    return info


def readme(path):
    for n in ("README.md", "readme.md", "README", "README.txt"):
        f = path / n
        if f.is_file():
            return f.read_text(encoding="utf-8", errors="replace")[:600]
    return ""


def is_project(path):
    return (path / ".git").exists() or any((path / m).exists() for m in MANIFESTS)


def scan(roots, depth):
    out = []
    for root in roots:
        root = Path(root).expanduser().resolve()
        if not root.is_dir():
            print(f"warning: {root} is not a folder", file=sys.stderr)
            continue
        stack = [(root, 0)]
        while stack:
            p, d = stack.pop()
            name = p.name.lower()
            if p != root and (p.name in SKIP_DIRS or p.name.startswith(".") or SECRETISH.search(name)):
                continue
            if is_project(p):
                lg, capped = langs(p)
                flags = sorted({v for k, v in FLAGS.items() if (p / k).exists()})
                entry = {
                    "name": p.name, "path": str(p),
                    "remote": git(p, "remote", "get-url", "origin"),
                    "commits": git(p, "rev-list", "--count", "HEAD"),
                    "last_commit": git(p, "log", "-1", "--format=%cs"),
                    "languages": lg, "languages_capped": capped, "flags": flags,
                    "readme": readme(p), **manifest_info(p),
                }
                out.append(entry)
                continue  # do not descend into a project
            if d < depth:
                try:
                    kids = sorted(c for c in p.iterdir() if c.is_dir() and not c.is_symlink())
                except OSError:
                    continue
                stack.extend((c, d + 1) for c in kids)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roots", nargs="*", default=[str(Path.home())])
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--out", default="local-scan.json")
    a = ap.parse_args()
    res = scan(a.roots, a.depth)
    Path(a.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"found {len(res)} projects; wrote {a.out}")


if __name__ == "__main__":
    main()
