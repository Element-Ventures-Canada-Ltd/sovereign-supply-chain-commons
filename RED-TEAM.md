Handling: Unclassified — working

> **STATUS: FINAL — approved by counsel, October 2026.** The safe-harbour
> statement in section 5 is in effect from its merge to `main`.

# Red-Team Programme

An open invitation to test this project and publish what you find. The programme
has two purposes that shift over time: first to show buyers and partners how
the platform stands up to expert scrutiny, then to harden it before wider
deployment.

## 1. Phases

| Phase | Purpose | Focus |
| :-- | :-- | :-- |
| 1. Public review | Credibility | Named reviewers critique architecture, method, and evidence claims. Findings and responses are published |
| 2. Hardening | Resilience | Adversarial testing of code, data, and agents. Prize value moves here |

**Transition.** Maintainers announce the move to Phase 2 once there are no open
High or Critical Phase 1 findings, or 60 days after the first public release,
whichever comes first. Phase 1 work continues in Phase 2; the register stays
open throughout.

## 2. In scope

- Code, schemas, validators, and CI configuration in this repository.
- The dependency chain (build and supply-chain integrity, including SBOM review).
- Prompt injection and tool misuse against any agent tooling in this repository.
- Poisoning or manipulation of the synthetic and public-source datasets, and of
  the validators that check them.
- Analytical claims: methodology errors, unsupported inferences, and
  citation or provenance problems.

## 3. Out of scope

- EV's private systems, the private core tier, and any non-public data.
- Anyone else's infrastructure, including hosting providers and package
  registries.
- Social engineering of EV staff, contributors, or partners.
- Denial-of-service testing, physical testing, and any testing that degrades
  service for others.
- Submitting technical data outside CONTRIBUTION-SCOPE.md as part of a test.

## 4. Rules of engagement

- Test only against your own fork or copy, or against material this repository
  designates as a test target.
- Do not access, copy, or retain data that is not yours or not public.
- Stop and report if you reach anything that looks non-public or sensitive.
- Do not publish exploit details for a vulnerability before the response
  period in section 6 has run.

## 5. Safe harbour

EV will not start legal action over good-faith research that follows this
charter and the rules above. This is a statement of EV's intent. It does not
bind third parties, waive rights of others, or authorize anything unlawful.

## 6. Reporting and response

| Finding type | Where to report |
| :-- | :-- |
| Vulnerability (code, dependency, access, data exposure) | Privately, per SECURITY.md |
| Analytical, methodological, or evidence finding | Public issue with the `red-team` label |

- Acknowledgement within 5 business days (consistent with SECURITY.md).
- Triage and severity rating within 10 business days.
- Every finding is entered in RED-TEAM-REGISTER.md with its status and EV's
  response, including findings EV declines to act on, with the reason.
- Vulnerabilities are listed in the register only after remediation, or after
  90 days from report, whichever comes first.

## 7. Severity

| Severity | Meaning |
| :-- | :-- |
| Critical | Compromises integrity of the platform or its data, or invalidates a core analytical claim |
| High | Materially weakens a security property or a stated result |
| Medium | Limited-impact weakness or an error with a clear workaround |
| Low | Minor issue, hardening suggestion, or clarity problem |

## 8. Recognition

Reviewers are credited by name or handle in the register. Accepted High and
Critical findings qualify for the `bounty:expert` tier (BOUNTIES.md), subject to
its limits. Any sponsor-funded prize pool will be published here before it opens.
