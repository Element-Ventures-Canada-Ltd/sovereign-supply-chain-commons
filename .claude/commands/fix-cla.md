---
description: Diagnose a failing CLA check on a pull request and give the exact fix
argument-hint: <PR number>
---
<!-- Handling: Unclassified — working -->

Diagnose the CLA check on PR #$ARGUMENTS. Read only until the owner approves a fix.

1. Read the PR (opener), its comments (has the opener posted "I have read the
   CLA Document and I hereby sign the CLA"?), its commits (author name, email
   and linked GitHub login for each), and the CLA job log (`Committers of Pull
   Request … have to sign`).
2. Classify the cause:
   - **A. Opener has not signed.** Fix: the owner posts the sign-off sentence once.
   - **B. A commit is authored as `Claude <noreply@anthropic.com>`.** GitHub
     links that address to an unrelated public account, so the bot sees an
     outside committer and the AI-author exemption cannot apply. Signing again
     does not help. Fix: recreate the change on a fresh branch committed as the
     owner (step 3).
   - **C. A commit by another person** who has not signed. Fix: that person signs,
     or their employer signs the Corporate CLA. Never rewrite their commit.
3. For B, propose (do not start until the owner says yes):
   1. `git fetch origin <pr-branch>`; `git switch -c <same-name>-owner origin/main`
   2. `git checkout origin/<pr-branch> -- .` to take the final file state
      (for a stacked PR, base the new branch on the replacement of its parent).
   3. `/check`, then one commit authored as the owner, with the original
      message and a `Co-Authored-By: Claude <noreply@anthropic.com>` trailer.
   4. Push and open a new PR titled as before, whose first line says
      "Replaces #<old> (commit identity fix)". Copy the original PR text.
   5. The owner closes the old PR. Never force-push or rewrite the old branch.
4. Report the cause in one sentence, then the owner's steps, numbered, each with
   one line on why it matters.
