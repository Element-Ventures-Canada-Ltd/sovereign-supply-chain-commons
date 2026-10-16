Handling: Unclassified — working

# Sovereign Supply Chain Survey

A recurring, multi-stakeholder survey of the Canadian space-launch supply chain. It replaces ad hoc questionnaires and sprint intake: from wave 1 onward, the survey decides who is invited to sprints and red-team challenges, what the program asks contributors to work on, and what the program publishes.

**Cadence:** twice a year (Wave A spring, Wave B fall). **Pilot topic:** turbopump supply chain and IP. **Status:** v1.0 pilot draft; freeze target 1 February 2027.

## What is here

| Path | Contents |
| :-- | :-- |
| `instrument/item-bank-v1.0.yaml` | Single source of truth for every question, response option, routing rule and segment |
| `instrument/questionnaire-v1.0.md` | Human-readable questionnaire, generated from the item bank. Do not edit by hand |
| `METHODOLOGY.md` | Design basis, sampling frame, contact protocol, index construction, disclosure control, quality reporting |
| `GOVERNANCE.md` | Wave calendar, freeze rules, change control, invitation and contribution-eligibility logic, anti-gaming controls |
| `CONSENT.md` | Respondent-facing consent, confidentiality, IP and export-control text |
| `CHANGELOG.md` | Version history |
| `tools/survey.py` | Validates the item bank, renders the questionnaire, reports burden by segment |

```bash
python3 Survey/tools/survey.py validate Survey/instrument/item-bank-v1.0.yaml
python3 Survey/tools/survey.py render   Survey/instrument/item-bank-v1.0.yaml --out Survey/instrument/questionnaire-v1.0.md
python3 Survey/tools/survey.py paths    Survey/instrument/item-bank-v1.0.yaml
```

## Two-tier boundary

| Open tier (this folder) | Proprietary core (not in this repository) |
| :-- | :-- |
| Questionnaire, routing, method, governance, consent text | Scoring weights, maturity-rubric thresholds, scoring algorithms |
| Aggregate results and the index time series, after disclosure control | Respondent-level data, identifiers, evidence uploads |
| Sensitivity ranges for the index | Invitation lists, contribution decisions, verifier reports |
| Changelog | Mappings to proprietary analytical frameworks and live engagements |

The questionnaire and method are published so any expert can audit them. The scoring is not, and is held under independent attestation (see `METHODOLOGY.md`).

## Contributing

Propose changes to questions as issues labelled `survey`, with the item ID and rationale. Frozen core items change only at a major version (see `GOVERNANCE.md`). All contributions follow `CONTRIBUTING.md`, `HANDLING.md` and the CLA.

The survey collects **no technical data**. Never propose an item that would ask for drawings, specifications, tolerances or performance values.
