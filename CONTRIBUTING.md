Handling: Unclassified — working

# Contributing

Thanks for considering a contribution. Please read this in full before opening
a pull request.

## Two-tier model

| Tier | What it covers | How to contribute |
| :-- | :-- | :-- |
| **Open** (this repository) | Dashboard, tooling, SDKs, documentation, and any openly released model weights | Pull requests welcome under the open-tier CLA (below) |
| **Core** (proprietary) | Ontology, registry, decision engine, and related methods and data | Maintained privately by Element Ventures (Canada) Ltd. Not open to public contribution; work is performed only under a written services agreement with EV |

The open tier is where the community builds on the platform. The core tier is
EV's proprietary technology and is licensed separately.

## Before you contribute (open tier)

1. **Read HANDLING.md.** Nothing above "Unclassified — working" is accepted
   here; sensitive material is referenced by pointer only, never committed.
2. **Accept the CLA.** Individuals: CLA.md. If your employer may own your work,
   it must sign the Corporate CLA (CCLA.md) first.
3. **Sign once.** On your first pull request, the project asks you to sign the
   CLA with a one-time click-through. The signature is recorded and covers your
   later contributions. No per-commit sign-off is needed. Organizations sign the
   CCLA and are added to an allowlist.
4. **Data and models:** contributions of datasets, model weights, or fine-tunes
   must meet DATA-CONTRIBUTIONS.md. Released model weights are governed by
   MODEL-LICENSE.md.
5. **Check scope.** Read CONTRIBUTION-SCOPE.md. The platform maps suppliers,
   dependencies, and chokepoints; it does not accept technical data about how
   components are designed, made, tested, or perform.
6. Read CODE_OF_CONDUCT.md and TRADEMARKS.md.

## Governance, bounties, and red-teaming

- **Governance:** the project is steward-led with a Technical Steering
  Committee. See GOVERNANCE.md, including the commitments EV makes to
  contributors about relicensing.
- **Bounties:** scoped issues carry a nominal value recorded in a deferred
  ledger. Payment depends on funding arriving; see BOUNTIES.md and LEDGER.md.
- **Red-team:** you are invited to test the project and publish findings. See
  RED-TEAM.md and SECURITY.md.

## How to contribute

1. Fork the repository (or branch, if you have write access) and make your change.
2. Make sure every new or changed file carries a Handling marking.
3. Open a pull request using the PR template and describe what changed and why.
4. CI runs the data-handling guard and the CLA check (a recorded signature for
   external contributors). Both must pass.
5. A maintainer reviews for technical soundness, handling compliance, and fit.

## Contribution lifecycle

| Step | What happens | Who |
| :-- | :-- | :-- |
| 1. Propose | Comment on an open call or issue describing a bounded piece of work. Reserves nothing; do not start work yet | Contributor |
| 2. Scope | If accepted in principle, a maintainer publishes a bounty issue with tier, acceptance tests, and dependencies (see BOUNTIES.md) | Maintainer |
| 3. Gate | An issue with an unmet dependency is labelled `blocked`. When the dependency merges, the proposer has 14 days of first claim | Maintainer |
| 4. Claim | Comment to claim an open bounty issue | Contributor |
| 5. Build | Open a draft pull request early. Disclose any AI assistance in the PR template. Accept the CLA | Contributor |
| 6. Review | Maintainers review against the acceptance tests. One revision round is included | Maintainer |
| 7. Accept | On merge, a maintainer adds the ledger entry in the same pull request | Maintainer |

Work that touches different files can run in parallel. Schema changes go first;
validators, tests, and documentation that depend on a schema version open only
after that version is merged.

### AI-assisted contributions

AI-assisted work is welcome if disclosed and human-backed. A Responsible Person
must review and approve the work, accept the CLA, and answer for it; an AI system
cannot accept the CLA. Agent accounts must say they are agents and have a named
Responsible Person (CLA.md section 11; CCLA.md for organizations). See
BOUNTIES.md for how this affects the ledger.

#### AI-authored commits

Some AI agents commit under their own identity, which has no GitHub account and
cannot sign the CLA. The CLA already treats such work as the Responsible
Person's (CLA.md section 1), so the CLA check accepts it only under all of
these conditions, which the `ai-author-gate` job in `cla.yml` checks for each
pull request:

1. The **pull request is opened by the Responsible Person**, and that person has
   signed the CLA by comment (or is on the maintainers' allowlist). The agent
   never opens the pull request under its own account and never signs.
2. Every commit by the agent identity (`Claude <noreply@anthropic.com>`) carries
   a **`Co-Authored-By: Claude …` trailer**, so the AI contribution is visible in
   the history as well as in the PR template.
3. The PR template's AI assistance section is completed, and the Responsible
   Person reviews and approves the whole contribution before merge.

The exception names one identity, never a pattern. Commits by any other author
who has not signed are still flagged. It does not create a ledger entry for the
agent: any ledger entry goes to the Responsible Person (BOUNTIES.md). The job
summary lists each commit the exception applied to. Maintainers can withdraw the
exception by removing the `ai-author-gate` job.

### Feedback and ideas

Input that is not a contribution (suggestions, critique, bug reports, ideas) is
welcome and needs no CLA. See FEEDBACK.md for how it is used, how it is
acknowledged, and what it does not earn.

### Examples and documentation

Every example in documentation lives as a file under `examples/` so it can be
validated. Examples are fictional, use invented metadata only, and describe no
real entity and no technical parameters (see CONTRIBUTION-SCOPE.md). Once the
validator is in place, CI validates every file under `examples/`.

## Questions

Open an issue, or contact the maintainers listed in MAINTAINERS.md.
