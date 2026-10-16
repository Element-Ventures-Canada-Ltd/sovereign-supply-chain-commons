Handling: Unclassified — working

# Sovereign Supply-Chain Intelligence Platform

The open tier of a jurisdiction-controlled supply-chain intelligence platform — dashboard, tooling, and documentation — maintained by **Element Ventures (Canada) Ltd.** ("EV"), exclusive licensee of the project's background IP.

> **Scope.** Contributions to this repository are supply-chain *mapping* only: suppliers, dependencies, and chokepoints. Do not submit technical data on how components are designed, made, or tested, or on how they perform. See [CONTRIBUTION-SCOPE.md](CONTRIBUTION-SCOPE.md).

## Why this repo exists

Open, rule-of-law economies increasingly plan and defend their industrial base using digital infrastructure they do not fully control. This project builds the alternative: a supply-chain intelligence platform whose data handling, hosting, and access model are controlled by jurisdiction, not by wherever a server happens to sit.

## Ways to contribute

- **Map.** Propose suppliers, dependencies, or chokepoints from public sources, using the *Supply-chain mapping contribution* issue form.
- **Build.** Improve the dashboard and tooling in the open tier.
- **Challenge.** Test the methodology and the code under RED-TEAM.md. Security issues go through SECURITY.md, not a public issue.

New here? Read HANDLING.md, CONTRIBUTION-SCOPE.md, and the CLA, then look for issues labelled `good first issue`.

## Repository structure

| Folder | Workstream |
| :-- | :-- |
| Dashboard/ | The query and visualization layer for capability-gap and dependency analysis |
| Engagement/ | Client-agnostic engagement workflow: solicitation, delivery gates, acceptance, reporting |
| Survey/ | The recurring sovereign supply chain survey: questionnaire, method, governance and tooling |
| WorkforceTrainingSimulation/ | Public, cited reference data on training programs, simulation facilities, skills retention, workforce roles and the enabling policy environment, organised on the Sovereign Seam |

The core components — ontology, registry, and decision engine — are © 2026 T. Leroy Smith, exclusively licensed to Element Ventures (Canada) Ltd., and maintained in a separate private repository. See CONTRIBUTING.md for the two-tier model.

## Handling and confidentiality

Every file in this repository is marked with a handling classification. Default is **Unclassified — working**. See HANDLING.md before contributing or referencing any sensitive input — sensitive material is represented here only as a pointer, never as raw content.

## Contributing

See CONTRIBUTING.md. This repository is the open tier: contributions require a one-time signature of the CLA (CLA.md, or CCLA.md for organizations). Core components do not accept public contributions. See GOVERNANCE.md for how the project is run, CONTRIBUTION-SCOPE.md for what it accepts, BOUNTIES.md for the deferred bounty ledger, and RED-TEAM.md to test the project.

## License

Code and content in this repository are licensed under Apache License 2.0 unless a file states otherwise. Released model weights are governed by MODEL-LICENSE.md. See NOTICE and TRADEMARKS.md.

## Maintainers

See MAINTAINERS.md.

## Security

See SECURITY.md to report a vulnerability.

## Code of Conduct

See CODE_OF_CONDUCT.md.

---

*This repository describes Element Ventures' own technology initiative.*
