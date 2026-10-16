---
description: Start-of-session status for the owner — what is waiting on them, what is failing, what is next
---
<!-- Handling: Unclassified — working -->

Give the owner a one-screen status of this repository. The owner is not a
software engineer: plain words, no jargon, numbered steps with one line on why
each matters. Read only; change nothing.

1. **Identity.** Run `git config user.name` and `git config user.email`. If the
   email is not the one in `.claude/owner.json`, run
   `python3 .claude/hooks/owner_identity.py` and say so.
2. **Open pull requests.** List every open PR on this repository with the
   GitHub tools (read only): number, title, days open, `[RED]` or green, and
   the state of each check on the head commit. Flag any PR open more than
   4 days.
3. **For each failing check, find the cause before advising.**
   - CLA signature: read the PR comments *and* the commit authors. If the owner
     has already signed and a commit is authored as `Claude
     <noreply@anthropic.com>` (or any account other than the owner), the cause
     is the commit identity, not the signature. Point to `/fix-cla`.
   - Any other check: name the failing step from the job log in one line.
4. **Plan position.** Read the repository's open milestones (the delivery plan
   itself is held privately). If one is open, say its title, due date, days left
   and how many of its issues are closed; if none is open, say so.
5. **Report** in this shape:

```
REPO STATUS — <weekday, date>
Identity: <OK / fixed / problem>
WAITING ON YOU
1. PR #<n> <title> — <days> days — <the one click or decision> — Why: <one line>
FAILING
- PR #<n>: <check> — cause: <cause> — fix: <command or step>
NEXT MILESTONE: <title>, due <date> (<n> days), <closed>/<total> issues closed
NEXT 3: <three actions that most move the milestone>
```

If GitHub is unreachable, write "no signal" for that line. Never guess a
number.
