---
name: skill-atlas
description: Builds a person's skill atlas from their real work. Scans local project folders and GitHub, writes an evidence-backed profile.json that maps skill clusters to fields, job titles, signature skill combinations and sellable services, then renders an interactive HTML map with a job-post matcher, CV angles and a profile loader. Use when asked to "map my skills", "build a profile from my projects", "what jobs or fields can I fit", "what services can I offer", "make a career map", "skill atlas", "match me to job listings", or to tailor a CV, cover letter or LinkedIn headline from project evidence.
license: MIT
metadata:
  version: "1.0.0"
---

# Skill Atlas

- **IS:** turning a person's projects, repos, notes and CV into a validated `profile.json` and an interactive atlas page; ranking job listings against that profile; drafting CV bullets and openings from it.
- **IS NOT:** submitting job applications, posting to LinkedIn or emailing anyone. Every output is a draft the person sends themselves.

## Outputs

| File | What it is |
|---|---|
| `profile.json` | The graph: person, families, clusters, fields, roles, combos, services, research, patterns, evidence. Schema in `references/schema.md` |
| `atlas.html` | One self-contained page rendered from the profile by `scripts/build_atlas.py` |
| `matches.json` / `.md` | Optional ranked job listings from `scripts/match_jobs.py` |

## Reference files

| File | Read when |
|---|---|
| `references/schema.md` | Writing or editing `profile.json` (always, before step 4) |
| `references/evidence-gathering.md` | Scanning folders, GitHub, notes and CVs (step 2) |
| `references/taxonomy.md` | Choosing clusters, fields and roles, and scoring depth, weights and tiers (steps 3 to 5) |
| `references/job-matching.md` | The person wants job matches, application drafts or a scheduled match run |

## Scripts

All are Python 3.8+ standard library. Run them, do not read them, unless one fails.

| Script | Run |
|---|---|
| `scripts/scan_local.py` | `python3 scripts/scan_local.py ~ --depth 2 --out local-scan.json` |
| `scripts/scan_github.py` | `python3 scripts/scan_github.py OWNER --readmes 40 --out github-scan.json` (needs `gh auth status` to pass; add `--include-private` only with consent) |
| `scripts/build_atlas.py` | `python3 scripts/build_atlas.py profile.json --check`, then `--out atlas.html` |
| `scripts/match_jobs.py` | `python3 scripts/match_jobs.py profile.json jobs.json --top 30 --md matches.md` |
| `scripts/draft_applications.py` | `python3 scripts/draft_applications.py profile.json jobs.json --out-dir drafts --fetch 40 --top 15` (fetches public Greenhouse, Lever and Ashby descriptions, writes a review queue) |
| `scripts/linkedin_kit.py` | `python3 scripts/linkedin_kit.py profile.json --out linkedin.md` (headlines, About, Featured, bullets, skills to paste by hand) |

`assets/atlas-template.html` is the renderer. `examples/sample-profile.json` is a small fictional profile to copy the shape from.

## Workflow

Copy this checklist and keep it updated:

```text
Skill atlas progress:
- [ ] 1. Agree scope: folders, GitHub owner, private repos yes/no, where the page goes
- [ ] 2. Gather evidence: scans, project notes, CV, live-URL checks
- [ ] 3. Draft 10-16 skill clusters in 2-3 families, each with depth and keywords
- [ ] 4. Draft fields with 0-3 weights, then roles with tiers
- [ ] 5. Add combos, services, research, patterns, lane, gaps, strengths
- [ ] 6. Validate with build_atlas.py --check until it prints ok
- [ ] 7. Review the summary with the person and apply their corrections
- [ ] 8. Render atlas.html, open it, check one desktop and one phone width
- [ ] 9. Optional: match jobs (references/job-matching.md)
```

1. **Scope.** Ask which folders and which GitHub account to scan, whether private repo names may appear, and whether the page will be shared. Default to excluding private repo names, client names, money figures and anything under credential-looking paths.
2. **Evidence.** Run both scanners. Also read any project status notes, the CV, and the portfolio site source. Every evidence item needs a status, and `live` requires a URL that returned 2xx today (`curl -s -o /dev/null -w "%{http_code}" -A "Mozilla/5.0" URL`). Details in `references/evidence-gathering.md`.
3. **Clusters.** Group skills by what a buyer would pay for, not by language. Use the depth rubric in `references/taxonomy.md`. Give each cluster 10-20 matching keywords, mostly multiword phrases.
4. **Fields and roles.** Weight each field 0-3 per cluster. Tier each role 3 (strong), 2 (good) or 1 (stretch) with the rubric; write `proof` naming projects and `gap` for anything below strong.
5. **The rest.** Combos are overlaps of 2-5 clusters with proof in every one. Services carry a band and a time, labelled as estimates in `priceNote`. Research cards state question, method, result and next step. Patterns describe how the person works, each tied to evidence.
6. **Validate.** `build_atlas.py --check` fails on unknown ids, out-of-range values and any cluster with no evidence. Fix errors; read warnings (secrets, emails, em dashes) and remove what should not be public.
7. **Review.** Show the person a table of clusters with depth, roles with tiers, and anything marked live. They know their work; apply every correction, and when they ask to remove a project, also drop roles, combos and services that only it proved.
8. **Render and check.** Build `atlas.html`, open it in a browser (or screenshot it with Playwright), and check one desktop and one phone width in both themes. Fix layout problems once, then hand it over.

## Rubrics in brief

- **Depth 5:** shipped and operated in production, more than once. **4:** shipped, with tests or users. **3:** built working projects. **2:** coursework, prototypes or training. **1:** exposure only.
- **Field weight 3:** the field cannot be done without this skill. **2:** used weekly. **1:** occasionally useful.
- **Tier 3:** projects match most lines of a typical job post. **2:** real proof with a gap in scale or depth. **1:** one project or credential away.

## Gotchas

- READMEs overclaim. "Live at X" often points at a dead deploy (Vercel returns 402 when an account is disabled, 404 when a project is gone). Check the URL before writing `"status": "live"`.
- Generic keywords such as `ai`, `data` or `api` match almost every job post and flatten the job matcher. Prefer phrases like `market making`, `react native`, `smart contract`.
- Job indexes often carry titles without descriptions. `match_jobs.py` discounts those to at most 80% and marks them `title only`; fetch the description before treating a match as strong.
- Forked repos are not the person's work. Count them only when the person confirms commits of their own.
- One giant project inflates every cluster it touches. Tag evidence with the 2-4 clusters it actually proves.
- Removing a project from the profile can leave a cluster with no evidence. Re-run `--check`; it reports this as an error.
- The renderer colours only three families. A fourth family renders in neutral grey, so keep families to three.
- Never submit applications, connection requests or posts from this skill. Match output and drafts go to the person for review.
