Handling: Unclassified — working

> **STATUS: DRAFT specification — not announced.** The scoring harness and
> reference dataset described here do not exist yet. Do not publish this page
> until they do.

# Turbo-Pump Chokepoint Challenge

A public challenge for contributors, built around the hardest mapping problem in
the launch supply chain: where does a turbo-pump supply network depend on a
single source, process, material, or skill?

## Task

Given a synthetic reference dataset of a turbo-pump supply network (suppliers,
part and material categories, process categories, workforce categories, and the
relationships between them), submit an analysis that identifies the chokepoints
and ranks them by dependency concentration, with your reasoning.

The dataset is synthetic. It contains no technical data about how any component
is designed, made, tested, or performs (see CONTRIBUTION-SCOPE.md).

## Scoring

A published, open harness scores submissions against a reference answer key on:
accuracy of chokepoints found, quality of the ranking, quality of the stated
reasoning, and robustness to a hidden perturbed variant of the dataset. Scores
appear on a public leaderboard by contributor name or handle.

## Founding contributor cohort

A capped group, proposed at up to 12 seats, for contributors with accepted work
in the first 90 days after public release. Seats carry a named role:

- Schema steward
- Turbo-pump domain reviewer
- Data pipeline contributor
- Security reviewer
- Workforce and simulation contributor

Cohort members are credited in the repository and become eligible for TSC
nomination (GOVERNANCE.md). A seat carries no payment; bounties are earned
separately under BOUNTIES.md.

## To build before launch

| Item | Needed for |
| :-- | :-- |
| Synthetic reference dataset and `provenance.yaml` | The task |
| Answer key and hidden perturbed variant | Scoring |
| Open scoring harness with CI | Leaderboard |
| 12 to 15 curated issues with acceptance tests | First contributions |
