# Job matching and application drafts

## What the skill does and does not do

- **Does:** rank listings against the profile, name the closest role, list the clusters a post asks for, pick projects to cite, and draft a CV variant, an opening paragraph and a profile headline.
- **Does not:** submit applications, send messages, or log into job boards or LinkedIn. Automated submission breaks most job boards' and LinkedIn's terms, can get accounts restricted, and sends unreviewed claims under the person's name. The person reviews and sends every application.

## Input shape

`match_jobs.py` accepts a list of jobs or an object with a `jobs` list:

```json
{ "jobs": [{ "id": "abc", "title": "Senior Quant Developer", "org": "acme", "url": "https://...",
             "location": "Remote", "tags": ["remote"], "description": "Full text when available", "kind": "job" }] }
```

Listings with `kind` other than `job` (grants, hackathons) are skipped unless `--kind ''` is passed.

## Scoring

Per cluster, demand = keyword hits / 3, capped at 1. For each role: 0.35 × (share of the role's skills the post asks for) + 0.30 × (share of the post's demand the role covers) + 0.35 × (title word overlap) + 0.05 per role keyword hit, ±0.03 for tier. Listings without a description are multiplied by 0.8 and marked `title only`.

Treat scores as a sort order, not a probability. Read the top 20 before trusting the ranking, and tune cluster keywords when obvious mismatches rank high.

## Fetching descriptions

Public ATS boards expose job descriptions without keys:

| ATS | Endpoint |
|---|---|
| Greenhouse | `https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{id}` (`content` is HTML) |
| Lever | `https://api.lever.co/v0/postings/{company}/{id}` |
| Ashby | `https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true` |

Fetch descriptions only for the top title-only matches, respect rate limits, strip HTML, then re-run the matcher.

`scripts/draft_applications.py` does this for the top `--fetch` title matches (one request every 0.6 s, generic user agent, descriptions cached in `drafts/.descriptions.json`), re-scores them and writes the queue described below.

## Drafting an application

`draft_applications.py` writes `job.md`, `cv.md` and `opening.md` per listing plus `INDEX.md` (new listings since the last run are marked). By hand, for one chosen listing:

1. Re-score with the full description.
2. CV variant: the role's headline, then the cited evidence `bullet`s, reordered so the post's top-asked clusters come first. Never add a claim that is not in the profile.
3. Opening paragraph: name the role, the two or three things the post asks for, and one project for each. Keep it under 120 words.
4. Thin spots (asked-for clusters with depth 2 or less): say how the person would close them, or leave the listing.
5. Save drafts to a review folder. The person edits and submits.

## Scheduling

A daily run is fine: refresh the job index, run `match_jobs.py` with `--min 0.5`, and write `matches.md` with new listings only (compare ids with the previous run). Notify the person with the file, not with sent applications.

## LinkedIn and profile copy

`scripts/linkedin_kit.py` generates this from `person.bio` (first person; falls back to `summary`). Copy for the person to paste: a headline from the lead lane plus the top three clusters, an About section from `person.summary` plus three evidence bullets, and featured items from live evidence with URLs. Do not automate LinkedIn actions.
