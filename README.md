# skill-atlas

An agent skill that turns your real work into a skill atlas: a `profile.json` graph of your skills, the fields and job titles they fit, the skill combinations few people can offer, and the services you can sell, rendered as one interactive HTML page.

The page includes:

- a radial map you can switch between fields, job titles and projects, with search and zoom
- a picker that shows which roles and services a set of skills unlocks
- a job-post matcher that names your closest role, the projects to cite, and drafts an opening and a headline
- CV angles for every job title, field-fit matrix, research cards, a service stack and an evidence ledger
- a loader, so anyone can drop in their own `profile.json`

Everything is backed by evidence: the build fails if a skill has no project behind it.

## Install

```bash
npx skills add David-glitc/skill-atlas --skill skill-atlas
```

Then ask your agent: *"Build my skill atlas from my projects and GitHub."*

## Use the scripts directly

```bash
cd skills/skill-atlas
python3 scripts/scan_local.py ~ --out local-scan.json
python3 scripts/scan_github.py YOUR_GITHUB --readmes 40 --out github-scan.json
# write profile.json (see references/schema.md and examples/sample-profile.json)
python3 scripts/build_atlas.py profile.json --out atlas.html
python3 scripts/match_jobs.py profile.json jobs.json --md matches.md
python3 scripts/draft_applications.py profile.json jobs.json --out-dir drafts   # review queue, never sends
python3 scripts/linkedin_kit.py profile.json --out linkedin.md                  # copy to paste by hand
```

Python 3.8+ with the standard library. `scan_github.py` needs the GitHub CLI signed in.

## What it will not do

It does not submit applications, message recruiters or automate LinkedIn. Matches and drafts are for you to review and send.

## Layout

```
skills/skill-atlas/
  SKILL.md                 workflow and rubrics for the agent
  references/              schema, evidence gathering, taxonomy, job matching
  scripts/                 scanners, validator and renderer, job matcher
  assets/atlas-template.html
  examples/sample-profile.json
```

## License

MIT
