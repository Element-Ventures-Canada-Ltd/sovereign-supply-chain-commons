Handling: Unclassified — working

# Governance

## 1. Wave calendar

Months are provisional and may shift to fit program milestones.

| Phase | Wave A (spring) | Wave B (fall) |
| :-- | :-- | :-- |
| Change requests close | 15 January | 15 July |
| Change-control review; retest changed items | Late January | Late July |
| Freeze and version tag | 1 February | 1 August |
| Fieldwork (4-6 weeks) | March to mid-April | September to mid-October |
| Cleaning, disclosure control, scoring | May | November |
| Aggregate release and method note | June | December |
| Eligibility decisions and invitations | June | December |

The pilot runs before the first freeze. Wave 1 is `2027A`.

## 2. Versioning

`SSCP-SURVEY vMAJOR.MINOR.PATCH`, tagged per wave (for example `v1.0.0-2027A`). Every item has a permanent ID. Retired IDs are listed in the item bank and never reused.

## 3. Freeze rules

1. Modules A, B and D are frozen. Wording, options, order and anchors change only at a **major** version.
2. A major version is allowed at most once a year, needs maintainer and steering-committee approval, and uses a split-ballot bridge (half the sample sees the old item, half the new) in the transition wave.
3. The rotating module changes topic between waves. When a topic returns, its items follow the same freeze rules so its own trend line holds.
4. Minor changes that do not alter meaning (typos, help text) need a short cognitive retest and a changelog entry.
5. Index weights are fixed within a major version. Any re-weighting is back-cast over prior waves and published as a revised series.

## 4. Change control

1. Open an issue labelled `survey` with the item ID, proposed text and rationale.
2. Maintainers triage; accepted changes go to a feature branch and pull request.
3. `tools/survey.py validate` must pass. The rendered questionnaire is regenerated, never hand-edited.
4. Frozen releases are tagged. Private scoring changes carry the same version numbers, so every published result traces to one instrument version and one scoring version.

## 5. From response to invitation to contribution

**Principle: a response earns eligibility to be considered. It never earns credit.** Credit goes only to independently verified outcomes.

| Gate | Input | Decision | Decided by |
| :-- | :-- | :-- | :-- |
| G1 Eligibility | Core and module complete; consent tier 3; export-control attestation | Enters the invitation pool | Automated |
| G2 Invitation | Private scoring of gap criticality, capability, contribution intent and evidence tier | Sprint or red-team invitation; balance rules apply (for example, at least one small or medium enterprise per sprint) | Steering-committee panel; scoring is advisory, not binding |
| G3 Credit | Delivered, verified outcome | Contribution credit by outcome class | Steering-committee panel plus an independent verifier; open challenge window |

**Outcome classes** (relative order only; values are private):

1. Closes a single point of failure the survey identified.
2. Produces milestone evidence accepted by the program's client.
3. Adds verified records to the control-tower data layer (new qualified source, test capacity, lead-time series).
4. Raises an index pillar through a verified evidence upgrade (ET2 or ET3), not a self-rating change.
5. Supporting work: reviews, mentoring, training.

## 6. Anti-gaming controls

| Risk | Control |
| :-- | :-- |
| Inflated self-ratings | Ratings at ET0 or ET1 earn no credit and only capped weight in invitation scoring |
| False evidence claims | Credit-bearing ET2 or ET3 claims are sampled for confidential review; a false claim voids that wave's eligibility and suspends credit for one wave |
| Splitting work to multiply credit | Credit is per outcome, not per artifact or pull request |
| Popularity contests | Decisions by domain panels with conflict-of-interest recusal, not open votes |
| Unpredictable rewards | Fixed settlement point each wave; outcome classes published in advance |
| Incentive bias in answers | Eligibility items are placed after the benchmark items; the eligibility flag is never shown in the questionnaire; the index uses frozen core items only |
| Operator conflict of interest | Recusal rules, independent verifier, and a public log of the operator's own entries |

## 7. Steering

The program's technical steering committee is advisory and owns change control and gate decisions under the published rules. The repository maintainers (see `MAINTAINERS.md`) own releases.
