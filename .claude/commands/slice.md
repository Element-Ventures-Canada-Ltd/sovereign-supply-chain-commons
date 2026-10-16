---
description: Score the current two-week slice and milestone against the repository plan
---
<!-- Handling: Unclassified — working -->

Score delivery against `project/turbopump/plan.json` and the repository's
issues and milestones. Read only.

1. Get today's date. From the plan's milestones, find the current milestone and
   days to its due date.
2. For each issue in the plan assigned to that milestone, find the matching
   GitHub issue by title (bootstrap creates them) and its state, labels
   (`zone:`, `status:`, `agent:claude`) and any linked PR.
3. Mark each: **done** (closed, or its PR merged) / **in review** (PR open) /
   **not yet** / **no signal** (no matching issue found). Give evidence: issue
   or PR number and date.
4. List items labelled `agent:claude` that are not started: these are work
   Claude can take next, smallest first.
5. Report:

```
SLICE CHECK — <date>  ·  <milestone>, due <date> (<n> days)
DONE <n> · IN REVIEW <n> · NOT YET <n> · NO SIGNAL <n>
<item> — <status> — <evidence>
CLAUDE CAN TAKE NEXT: <up to 3 items>
OWNER DECISIONS NEEDED: <items labelled agent:false or status:blocked>
```

Never invent a status. If the milestone list is empty, say the bootstrap has
not run and give the owner the one step to run it (Actions tab → Turbopump
planning bootstrap → Run workflow), with why it matters.
