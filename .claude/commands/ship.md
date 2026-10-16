---
description: Branch, check, commit as the owner, then (after the owner says yes) push and open the pull request
argument-hint: <short description of the change>
---
<!-- Handling: Unclassified — working -->

Ship the current change as one small pull request: $ARGUMENTS

1. **Branch.** If on `main`, create `feature/<short-name>` (or `fix/<short-name>`
   for a correction). One concern per branch.
2. **Identity.** Confirm `git config user.email` matches `.claude/owner.json`;
   if not, run `python3 .claude/hooks/owner_identity.py`.
3. **Check.** Run `/check`. Stop and report if anything fails.
4. **Commit** with a plain message (what changed and why), ending with:
   ```
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```
   plus any session line the environment asks for. Commit messages are public:
   no client, programme, contract or internal names.
5. **Zone.** Work out red or green from `.github/CODEOWNERS` (last match wins;
   default red). Do not mix red and green edits unless they cannot work apart.
6. **Ask the owner** in one short message: the branch, the files, red or green,
   and "Push and open the PR? (yes/no)". Do nothing further until they say yes.
7. **Push** the feature branch (the guard will ask for confirmation).
8. **Open the PR** into `main` using `.github/PULL_REQUEST_TEMPLATE.md` in full:
   - Title: `[RED] ` prefix if any file is red.
   - Red PRs: first lines list each red file with one line on why.
   - Plain-language summary first; technical detail after.
   - AI assistance section: "AI Assistance was used", describe which parts; leave
     the Responsible Person box for the owner to tick.
   - Call out any `.github/workflows/` change explicitly.
9. **Auto-merge.** Enable squash auto-merge (the `merge-gate` workflow also does
   this). Never merge.
10. **Verify** after CI starts: every commit author is the owner; the CLA check
    is not failing on identity. Report the PR link and what the owner must do,
    as numbered steps with one line on why each matters.
