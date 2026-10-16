Handling: Unclassified — working

# Methodology

Version 1.0 pilot draft. Parameters marked **(calibrate)** are provisional and are set from pilot evidence before the v1.0 freeze.

## 1. Design basis

The survey is a census of verified evidence, not an opinion poll. It combines four established practices:

| Practice | Source | How it is used here |
| :-- | :-- | :-- |
| Industrial-base assessment surveys | US Commerce Department (BIS), Rocket Propulsion Industrial Base Assessment, 2018 | Firm- and facility-level mapping, business-line taxonomy, supplier and customer dependencies, aggregate-only publication |
| National space-sector survey | Canadian Space Agency, State of the Canadian Space Sector (annual) | OECD value-chain categories, so results compare with official statistics |
| Composite indicators | OECD/JRC, Handbook on Constructing Composite Indicators (2008) | Ten-step index construction, including uncertainty and sensitivity analysis |
| Survey quality | AAPOR Code and Standard Definitions; Dillman, Tailored Design Method; Willis, Cognitive Interviewing | Disclosure of wording and method, response-rate reporting, multi-contact protocol, cognitive pretesting |

Maturity scales follow staged capability-maturity logic (five anchored levels) and are written in observable, sector-specific language so two raters reading the same evidence reach the same level.

**Evidence over perception.** Every maturity (M5) item is followed by an evidence tier (ET0 to ET3). Self-ratings without evidence are reported but carry limited weight in any score.

## 2. Structure

| Module | Status | Time |
| :-- | :-- | :-- |
| A. Screener and consent | Core, frozen | 2-3 min |
| B. Core panel | Core, frozen | 8-10 min |
| C. Rotating thematic module (wave 1: turbopumps) | Rotating | 12-18 min |
| D. Segment add-ons | Core, frozen | 3-5 min |
| E. Evidence upload (optional) | Private channel | Variable |

Target median completion: **25 minutes or less** per segment path, hard cap 35 **(calibrate)**. `survey.py paths` reports item counts per segment; pilot paradata (time per item, break-offs) decides any cuts.

## 3. Population and frame

Five segments: suppliers, consortium members, primes and integrators, government buyers, allied partners. The frame is the program's registry of Canadian launch-chain organizations, refreshed before each wave, plus snowball referrals from respondents. Non-respondents in the frame are flagged, not dropped, so the published picture is not limited to organizations that chose to answer.

The unit of response is the **organization**. One designated respondent per organization, who may consult colleagues.

## 4. Contact protocol

Four to five personalized contacts over four to six weeks: advance notice from a credible sponsor, invitation with link, two reminders, final notice. Prior-wave answers are pre-filled for confirmation in later waves to reduce burden.

## 5. Composite index

Constructed following the OECD/JRC ten steps: framework, variable selection, imputation, multivariate analysis, normalization, weighting and aggregation, uncertainty and sensitivity analysis, back to the data, links to other indicators, presentation.

**Published:** pillar structure, which items feed each pillar (the `X` feed in the item bank), normalization method, imputation rules, aggregate scores and trend, and sensitivity ranges under alternative weighting and normalization.

**Not published:** the weights and rubric thresholds. To keep the index auditable without disclosing them, an **independent methodologist** holds the versioned weights and attests in each release that they were applied as recorded. Government users may review the weights under a confidentiality agreement.

Index computation uses frozen core items only, so the series stays comparable across waves.

## 6. Disclosure control

| Rule | Setting |
| :-- | :-- |
| Minimum published cell | 5 organizations **(calibrate)**; rises to 10 once the frame exceeds about 50 organizations per dimension |
| Dominance | A cell is suppressed when its largest one or two contributors dominate the total, following Statistics Canada concentration rules |
| Complementary suppression | Applied so suppressed cells cannot be recovered from totals |
| Small domains | No province × segment × capability cross-tabulations for the wave-1 module |
| Open text | Never published verbatim; themed and coded only |
| Single-point-of-failure detail | Published only at category level; the full register is restricted |

## 7. Data handling

All respondent-level data is stored and processed in Canada. Identifiers are split from answers into a separate key store; analysis runs on a pseudonymized copy. Only disclosure-controlled aggregates reach this repository. See `CONSENT.md`.

## 8. Quality reporting

Each release reports response rates using AAPOR Standard Definitions, item non-response, panel attrition, imputation share, and any change to the instrument since the previous wave.

## 9. Pilot and pretest

| Step | Method | Exit criterion |
| :-- | :-- | :-- |
| Expert review | Survey methodologist, turbomachinery engineer, export-control counsel, item by item | Every item accepted or revised |
| Cognitive interviews, two rounds | 8-10 respondents per round across all segments; think-aloud with neutral probes | No critical comprehension problems on core items |
| Rater calibration | Two raters score the same evidence packets against M5 anchors | Agreement target set from pilot **(calibrate)** |
| Soft launch | 15-25 organizations on the production platform | Median time at or under target; acceptable break-off and technical-data screen rates **(calibrate)** |
| Freeze | Maintainer sign-off and tagged release | `v1.0.0` |

## References

- US Department of Commerce, BIS Office of Technology Evaluation, *U.S. Rocket Propulsion Industrial Base Assessment* (2018).
- Canadian Space Agency, *State of the Canadian Space Sector Report 2025*.
- OECD/JRC, *Handbook on Constructing Composite Indicators: Methodology and User Guide* (2008).
- AAPOR, *Code of Professional Ethics and Practices* and *Standard Definitions*.
- Dillman, Smyth and Christian, *Internet, Phone, Mail, and Mixed-Mode Surveys: The Tailored Design Method*.
- Willis, *Cognitive Interviewing: A Tool for Improving Questionnaire Design* (2005).
- Statistics Canada, *Quality Guidelines* (12-539-X).
- Treasury Board of Canada Secretariat, Privacy Implementation Notice 2020-03.
- Missile Technology Control Regime, *Equipment, Software and Technology Annex*, Item 3.A.5.
- NIST, *Cybersecurity Framework 2.0* and SP 800-161 (confirm current revision before mapping).
