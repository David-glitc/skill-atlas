# Gathering evidence

## Sources, in order of trust

1. **Running things.** Live URLs (checked today), published packages, deployed contracts with explorer links, running services.
2. **Project status notes.** Handoff notes, DEVELOPMENT.md logs, changelogs. They say what is live, paused or abandoned better than READMEs.
3. **Code and history.** Commit counts, last commit date, tests, CI config, deploy config (`scan_local.py` records these as `flags`).
4. **READMEs and CVs.** Useful for wording, weakest for facts. Confirm any claim of users, money or performance elsewhere.

## Scanning

- `scan_local.py` stops at the first project folder it finds and does not descend into it, so a monorepo counts once. Raise `--depth` for workspaces nested deeper than two levels.
- It skips dependency folders and any folder whose name suggests credentials or backups. Do not widen that list without asking.
- `scan_github.py` leaves out private repos unless `--include-private` is passed. Ask first: private repo names can reveal clients or unreleased products.
- Large scan files: summarise them with a short script (counts by language, the 30 most recent projects) instead of reading them whole.

## Turning a project into evidence

For each project worth listing:

- **clusters:** the 2-4 skills it actually proves. A landing page proves full-stack, not smart contracts, even if the repo has a contracts folder.
- **status and label:** `live` only with a 2xx check today; `preview` for testnet, beta, paper trading or preview deploys; otherwise research, local, contributor, hackathon.
- **summary:** what it is, in one line, with one concrete number when there is one.
- **bullet:** a CV sentence starting with a verb. Only claim what the person did (contributor work says "contributed").

Group many small repos into one evidence item ("Bitcoin, Polkadot and zk work") rather than listing twenty thin entries.

## Privacy rules

- Never copy keys, tokens, wallet addresses, emails or phone numbers into the profile. `build_atlas.py` warns on common patterns, but read the profile yourself too.
- Leave out client names, salaries, revenue, P&L and incident details unless the person asks for them.
- Personal notes (journals, Obsidian vaults) can inform the `patterns` section, but quote nothing from them without consent.

## When the person corrects you

Remove or change the evidence, then search the profile for everything that relied on it: role `proof`, combos, services, stats and research cards. Re-run `build_atlas.py --check`, which errors if a cluster is left with no evidence.
