Handling: Unclassified — working

# REVIEW.md

What a reviewer, automated or human, looks for in this repository. Read it
with `CLAUDE.md`; where the two differ, `CLAUDE.md` wins. Review comments are
public, so the content rules apply to them too.

## What failure looks like here

Ranked. The first five are release blockers, not style issues.

1. **It identifies.** A name, term or detail that lets a reader infer a client,
   programme, contract, funder or internal codename; a competitor product
   name; or a third-party vendor or platform name outside a neutral adapter
   slot. Applies to files, commit messages and pull request text. Cite the
   file and line; never repeat the term in the comment.
2. **It exports.** Technical data on how a component is designed, made, tested
   or performs (`CONTRIBUTION-SCOPE.md`), even when it looks public.
3. **It leaks.** Credentials, tokens, keys, private repository names,
   respondent data, scoring weights or rubrics.
4. **It weakens a guard.** A check loosened, skipped or narrowed; an allowlist
   widened; a `# scope-ok` marker added; a `pull_request_target` workflow that
   checks out or runs pull request code; an action not pinned to a full SHA.
5. **It guesses.** Real-entity data without a public-record citation, or a gap
   filled by inference. Gaps stay gaps.
6. **It breaks.** Logic errors; untrusted input rendered without escaping;
   non-https links; CSV export open to formula injection; a schema, API or
   data-contract change without a version bump.
7. **It is unmarked.** A new or changed substantive file without a
   `Handling:` marking.

## Rules for findings

- Give the file and line as evidence. Do not infer a problem from a name alone.
- Flag a class of problem once and list every instance in that finding.
- Tag each finding **Important**, **Nit** or **Pre-existing**. Pre-existing
  issues are reported but do not block this pull request.
- At most three nits per review. Do not raise nits that tests or guards
  already enforce. Rules 1–7 are always reviewed: the guards are a floor, not
  a substitute for review.
- Do not repeat a finding already posted on this pull request. After the
  second round, review only what changed since the last review.
- Start the summary with a count, for example "2 Important, 1 Nit". If there
  is nothing to fix, say "No findings."

## Zone check

Use the merge gate's definition. A change is red if any changed path is owned
by the owner in `CODEOWNERS`, is matched by no `CODEOWNERS` line, is under
`.github/`, or is a `CODEOWNERS` file. It is green only if every changed path
matches a line with no owner. Red waits for the owner. If a red change's title
lacks the red prefix or its description does not list the red files, report
it as Important.

## Skip

- `examples/`: synthetic data only. Still apply rules 1, 2, 3, 5 and 7, and
  flag any real entity.
- Lockfiles: review only added or changed dependencies.
