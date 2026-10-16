---
description: Run the repository checks that match the files changed on this branch
---
<!-- Handling: Unclassified — working -->

Run the checks CI will run, before any pull request. Change no files except to
fix a genuine failure you then report.

1. `git fetch origin main` then `git diff --name-only origin/main...HEAD > /tmp/changed_files.txt`
   (add uncommitted files with `git status --porcelain`). Show the list.
2. Always run:
   - `python3 .github/scripts/scope_guard.py /tmp/changed_files.txt`
   - `python3 .github/scripts/data_handling_guard.py /tmp/changed_files.txt`
   - `python3 -m unittest discover -s .claude/hooks -p 'test_guard.py'`
3. Run the folder checks listed under **Commands** in `CLAUDE.md` for every
   folder that appears in the list (Agents, Survey, Engagement, Dashboard,
   `.github/scripts`, `modules/turbopump-marketplace` via its own README).
4. Check every new or changed substantive file starts with a
   `Handling: Unclassified — working` marking.
5. Zone check: for each changed path, find the last matching line in
   `.github/CODEOWNERS`. Owned by `@TLS-sys` = red. Report "this PR is RED
   (files: …)" or "this PR is green".
6. Report pass/fail per check in a short table. If anything failed, fix the
   cause (never weaken a check or add a `# scope-ok` marker) or explain why it
   cannot be fixed here.
