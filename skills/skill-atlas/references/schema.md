# profile.json schema (skill-atlas/1)

## Contents

- Top level
- person, stats, families
- clusters
- fields
- roles
- evidence
- combos, layers, services
- research, patterns, lane, money, gaps, strengths
- Minimal valid file

## Top level

```json
{ "schema": "skill-atlas/1", "person": {}, "stats": [], "families": [], "clusters": [], "fields": [],
  "roles": [], "evidence": [], "combos": [], "layers": [], "services": [], "priceNote": "",
  "research": [], "patterns": [], "lane": [], "money": {}, "gaps": [], "strengths": [], "matchSample": "" }
```

Required: `person`, `families`, `clusters`, `fields`, `roles`, `evidence`. Everything else is optional and its plate is hidden when empty. Ids are short strings, unique within their list. Text is plain (no HTML).

## person, stats, families

```json
"person": { "name": "Ada Example", "headline": "Backend engineer for payments", "summary": "One or two sentences, may address the reader.",
            "bio": "First-person version for CVs and LinkedIn: I build ...",
            "location": "Remote", "generated": "1 Jan 2027", "links": [{ "label": "GitHub", "url": "https://github.com/ada" }],
            "sources": "Built from 40 project folders and 60 GitHub repos." },
"stats": [{ "value": "60", "label": "GitHub repos of your own" }],
"families": [{ "id": "mk", "name": "Markets & research" }, { "id": "bd", "name": "Build" }, { "id": "pp", "name": "People" }]
```

Use 2 or 3 families. Families 1-3 get validated colours and shapes (circle, square, diamond); a 4th renders grey.

## clusters

```json
{ "id": "T", "name": "Trading systems & execution", "short": "Trading", "family": "mk", "depth": 5,
  "skills": ["Market-making engines", "risk gates"], "keywords": ["market making", "order book", "rfq"] }
```

- `depth` 1-5 (rubric in `taxonomy.md`).
- `short` labels the map; keep it to one word or two.
- `keywords` drive job matching: 10-20 lowercase phrases. Three hits mark the cluster as fully asked for.

## fields

```json
{ "id": "fintech", "name": "Fintech & stablecoin payments", "short": "Fintech & payments",
  "want": "What buyers in this field need, in one sentence.", "weights": { "P": 3, "F": 3, "C": 2 } }
```

`weights` maps cluster id to 0-3. Omitted clusters count as 0. The page sums weights into a fit score.

## roles

```json
{ "id": "mm-eng", "title": "Market-Making Engineer", "tier": 3, "fields": ["crypto-trading"],
  "clusters": ["T", "Q", "I"], "proof": "Projects that prove it.", "gap": "Only for tier 2 or 1.",
  "keywords": ["market making", "liquidity"] }
```

`tier` 3 strong, 2 good, 1 stretch. `clusters` are the 2-5 skills the role draws on. `keywords` add a small bonus when a job post contains them.

## evidence

```json
{ "id": "zinger", "name": "Zinger market maker", "clusters": ["T", "Q", "I"], "status": "live", "label": "Live, real money",
  "summary": "One line on what it is.", "bullet": "CV-ready sentence starting with a verb.", "url": "https://..." }
```

- `status`: `live` (verified URL or running service), `preview` (testnet, beta, paper, preview deploy), anything else (research, local, contributor) renders neutral.
- `label` is the visible status text.
- `bullet` feeds CV angles, match drafts and citations. Write it for items worth citing.

## combos, layers, services

```json
"combos": [{ "name": "Replay before real money", "clusters": ["Q", "D", "T"], "buyers": "Funds", "proof": "mm-replay", "offer": "Strategy audit" }],
"layers": [{ "name": "Lead offers", "note": "Highest value." }],
"services": [{ "layer": "Lead offers", "name": "Strategy audit", "desc": "...", "clusters": ["Q", "D"], "proof": "mm-replay",
               "band": "$3k–8k", "time": "2–3 weeks" },
             { "layer": "Own products", "product": true, "name": "Kachim", "clusters": ["F", "P"], "proof": "kachim.com", "band": "User revenue", "time": "Live" }]
```

`product: true` marks things already running; they appear in the stack but not in the service count. The first six combos become presets in the Combine plate.

## research, patterns, lane, money, gaps, strengths

```json
"research": [{ "title": "...", "status": "research", "label": "Pre-registered", "clusters": ["Q"],
               "question": "...", "method": "...", "result": "...", "next": "...", "open": "Optional open question",
               "links": [{ "label": "Paper", "url": "https://..." }] }],
"patterns": [{ "name": "You simulate before you risk", "description": "...", "evidence": "...", "risk": "optional" }],
"lane": [{ "label": "Lead", "title": "Trading-systems engineer.", "text": "..." }],
"money": { "title": "One way to $40k", "items": [["One build", 15000]], "note": "Illustration, not a forecast." },
"gaps": ["..."], "strengths": ["..."], "matchSample": "Optional job post text preloaded in the matcher"
```

## Minimal valid file

```json
{
  "schema": "skill-atlas/1",
  "person": { "name": "Ada Example" },
  "families": [{ "id": "b", "name": "Build" }],
  "clusters": [{ "id": "F", "name": "Full-stack", "short": "Full-stack", "family": "b", "depth": 3, "keywords": ["react", "node"] }],
  "fields": [{ "id": "web", "name": "Web apps", "weights": { "F": 3 } }],
  "roles": [{ "id": "fs", "title": "Full-Stack Engineer", "tier": 2, "fields": ["web"], "clusters": ["F"], "proof": "Shop app" }],
  "evidence": [{ "id": "shop", "name": "Shop app", "clusters": ["F"], "status": "live", "label": "Live", "summary": "A small store." }]
}
```
