# Candlery Agent Boot File

Use this file at the start of every AI session for this repo.

Read first:
1. `docs/ai-state/SYSTEM_KEY.md` (single-file control + playbook order)

Optional deep context, if needed:
2. `docs/CONSTITUTION.md` (architecture boundaries only)
3. `docs/ai-state/REAL_WORLD_GAP.md` (full scoreboard + R1-R10)
4. `docs/ai-state/HANDOFF.md` (cross-session context)

Required first reply from any AI:
- `Action type:` `act` or `doc`
- `Gap row:` which row in `REAL_WORLD_GAP.md` this closes
- `Non-doc alternative considered:` one line (or `none`)

If action type is `doc`, pause and ask whether a non-doc act exists first.

Operator prompt prefix (copy into any AI platform):
`Before any work: read docs/ai-state/SYSTEM_KEY.md and then state Action type (act/doc), Gap row, and one non-doc alternative considered. If your next step is doc-shaped, stop and ask before writing.`

This file is a boot router, not the rule source. Do not expand it with long policy text.
