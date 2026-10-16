Handling: Unclassified — working

# Data dictionary: Workforce Training and Simulation database

Dates use `YYYY`, `YYYY-MM` or `YYYY-MM-DD`. `as_of` is the date the row was last checked. Multi-value fields use `;` as the separator. Allowed values are enforced by `schema/schema.sql` and `tools/build.py`.

## Shared fields

| Field | Meaning |
|---|---|
| `cell_id` | Primary Sovereign Seam cell, `LAYER-Mn`. Must exist in `seam_cells.csv`. |
| `secondary_cell_ids` | Other cells the record also bears on, `;`-separated. Optional. |
| `source_id` | The source in `sources.csv` that supports the row. Required on public rows; must be empty on synthetic rows. |
| `is_synthetic` | `1` = invented test row (id `SYN-…`, name "Synthetic …"); `0` = public record. |

## seam_cells

| Field | Meaning |
|---|---|
| `cell_id` | `APP`, `SOV`, `MOD`, `INF`, `CHI` or `ENE`, then `-M1` to `-M10` |
| `layer`, `layer_index` | Stack layer, 1 (Applications) to 6 (Energy) |
| `capability_code`, `capability`, `capability_index` | Defence Industrial Strategy sovereign capability, M1 to M10 |

## sources

| Field | Meaning |
|---|---|
| `title`, `publisher`, `authors`, `published` | Bibliographic detail; `published` may be blank when the page is undated |
| `url` | Working `https` link |
| `citability` | `P` primary · `A` authoritative secondary · `AS` attributable secondary · `AN` attribute-only · `PR` self-reported or vendor · `S` single-sourced |
| `accessed` | Date the link was checked |

## programs

`sector`: `defence`, `civilian`, `dual-use`. `modality`: `lecture`, `vr`, `manikin`, `live`, `blended`, `online`, `mixed`. `status`: `active`, `inactive`, `unknown`, `synthetic`. `jurisdiction`: ISO country code or `INTL`.

## facilities

`facility_type`: `schoolhouse`, `embedded-civilian-hospital`, `simulation-centre`, `mobile`, `field-site`, `test-site`. Location fields may be blank where the source does not state them.

## equipment

`equipment_class`: `high-fidelity-manikin`, `task-trainer`, `vr-system`, `av-capture`, `standardized-patient-suite`, `test-stand`, `cold-flow-rig`, `console-simulator`. `fidelity`: `low`, `medium`, `high`, `n/a`. An item's synthetic flag must match its facility's.

## skills

| Field | Meaning |
|---|---|
| `skill_type` | `psychomotor`, `cognitive`, `team`, `psychomotor-team`, `procedural` |
| `decay_form` | Functional form of skill fade: `exponential` |
| `parameter_status` | `held` = a calibrated value exists but is not published here; `open` = no value yet |

## skill_evidence

| Field | Meaning |
|---|---|
| `finding` | Short factual statement of the result, in plain words |
| `direction` | `retained`, `decayed` or `mixed` over the interval studied |
| `interval_months_low` / `_high` | Follow-up interval(s) the finding covers |
| `population` | Who was studied, and where |

Evidence rows inherit their skill's Seam binding.

## roles

`noc_2021`: five-digit National Occupational Classification 2021 code.

## indicators

| Field | Meaning |
|---|---|
| `value` | Numeric value where one exists |
| `value_text` | The value as the source states it ("about 4,700", "1 in 13", "4,000+") |
| `unit`, `period`, `geography` | What is counted, over what period, where |
| `role_id` | Optional link to `roles.csv` |

## enabling_environment

`instrument_type`: `strategy`, `policy`, `legislation`, `regulation`, `directive`, `standard`, `accreditation`, `credential`, `classification`, `institution`. `status`: `in-force`, `published`, `announced`, `sunsetting`, `repealed`, `benchmark` (a foreign comparator). Announced and in force are kept distinct.

## missions

A Design Reference Mission: the real-world job that every role and skill requirement traces to. Public, cited.

| Field | Meaning |
|---|---|
| `mission_id` | `DRM-nn` |
| `description` | The mission in plain words. No technical performance data. |

## role_skills

Link table: mission `DRM-nn` needs role `RL-nn` to hold skill `SK-nn`.

| Field | Meaning |
|---|---|
| `basis` | `source` = the requirement is stated in a cited source; `inference` = Element Ventures judgement, uncited and shown as such |
| `source_id` | Required when `basis` is `source`; must be empty when `basis` is `inference` |

## Generated (release/)

Run `python tools/build.py` to build these. Only `SEAM_COVERAGE.md` is committed; the SQLite file and the workbook are binary, so they are built locally and kept out of the repository.

| File | Built from |
|---|---|
| `wts.sqlite` | All tables, plus `record_cells` (every primary and secondary binding) and the view `v_seam_coverage` |
| `WTS_Database.xlsx` | All tables; synthetic rows shaded grey |
| `SEAM_COVERAGE.md` | `v_seam_coverage` as a 6 × 10 grid |

---

Element Ventures (Canada) Ltd. · Sovereign Operating Intelligence (SOI™)
