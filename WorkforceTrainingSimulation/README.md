Handling: Unclassified — working

# Workforce Training and Simulation database

Public, cited reference data on how Canada trains and sustains the people behind its medical and defence readiness: training programs, simulation facilities and equipment, skills and the evidence on how fast they fade, workforce roles and supply indicators, and the policy environment that governs all of it.

**Organised on the Sovereign Seam.** Every record binds to one of 60 cells: the six layers of the geoeconomic AI stack (Applications, Sovereign Decision Layer, Models, Infrastructure, Chips, Energy) crossed with the ten sovereign capabilities of Canada's Defence Industrial Strategy (M1 Aerospace to M10 Uncrewed & Autonomous). A cell id reads `LAYER-Mn`; for example `SOV-M9` is the Sovereign Decision Layer for Training & Simulation. The binding records where a record sits. It is not an assessment or a recommendation.

## Open it

| You want to | Open |
|---|---|
| Browse in Excel | Run the build (below), then open `release/WTS_Database.xlsx`: one sheet per table, plus "Read me" and "Seam coverage" |
| See which cells have data | `release/SEAM_COVERAGE.md` |
| Query it | Run the build (below), then open `release/wts.sqlite` in any SQLite browser |
| Edit or add data | the CSV files in `data/` |

## The tables

| File | Holds |
|---|---|
| `seam_cells.csv` | The 60 Seam cells |
| `sources.csv` | Every source cited, with URL and citability grade |
| `programs.csv` | Training programs and courses |
| `facilities.csv` | Simulation centres and training establishments |
| `equipment.csv` | Simulation equipment by facility (synthetic only for now: no public asset inventories exist) |
| `skills.csv` | Skill definitions |
| `skill_evidence.csv` | Published findings on how well each skill is retained over time |
| `roles.csv` | Workforce roles with NOC 2021 codes |
| `indicators.csv` | Counts and supply indicators (recruitment, accredited centres, network size) |
| `enabling_environment.csv` | Strategies, policies, directives, standards, accreditation and credentials |
| `missions.csv` | Design Reference Missions: the real-world job each requirement traces to |
| `role_skills.csv` | Which role needs which skill for a mission, and whether that is cited or an inference |

Field-by-field definitions are in [DATA_DICTIONARY.md](DATA_DICTIONARY.md).

## Space launch: propulsion test slice

The first space-launch slice covers the people who run a liquid-rocket static fire: roles, skills, certification ladders, training providers, test-site facilities and the regulatory touchpoints, in Canada with US rules as comparators. It traces to one Design Reference Mission, `DRM-01` (a pump-fed liquid static fire by a student and volunteer team). Records bind to the Training & Simulation cells, with Space (`-M7`) as the secondary binding.

What the slice deliberately leaves out:

- **Technical test data.** No pressures, safety factors, engine size, standoff distances or performance figures, even where a source publishes them. This repository maps workforce and supply chain only.
- **Calibrated parameters.** Skill-decay values, proficiency thresholds and simulator-transfer ratios are held privately (rule 4 below). The public `skill_evidence` rows show what the literature found, and say when the study was not on propulsion crews.
- **People.** No names, rosters, scores or certificate numbers.

Known gaps, open for contribution: time to competency for test conductors, instructor-to-trainee ratios, simulator transfer for test consoles, and a count of Canadian propulsion and turbomachinery workers. None is published anywhere we could find.

How to challenge a row: [RED_TEAM_CHECKLIST.md](RED_TEAM_CHECKLIST.md). How a calibrated value is recorded in the private registry: [schema/parameter_record.schema.json](schema/parameter_record.schema.json) (the format is public; the values are not).

## Rules every row follows

1. **Public rows are cited.** Each carries a `source_id` that resolves to `sources.csv`, which records the URL, the publisher and a citability grade: P primary, A authoritative secondary, AS attributable secondary, AN attribute-only, PR self-reported, S single-sourced.
2. **Synthetic rows are unmistakable.** Ids start `SYN-`, names start "Synthetic", they cite no source, and they are never added to public counts. They exist to stress-test the structure.
3. **An empty cell is a coverage gap, not a finding.** The coverage page shows where data is missing so contributors know where to look.
4. **Parameters are not published.** Skills record the evidence and the decay form only. Calibrated parameter values are not part of this open dataset.

The build script enforces rules 1 and 2. It stops if a row breaks them.

## Change or add data

1. Edit the CSV in `data/`. Keep ids unique and use an existing `cell_id` from `seam_cells.csv`.
2. Add any new source to `sources.csv` first, then cite its `source_id`.
3. Run the build from this folder:

   ```
   python tools/build.py
   ```

   It checks every row, then regenerates everything in `release/`. Fix any problem it lists and run it again.
4. Commit the CSV changes and `release/SEAM_COVERAGE.md` together on a branch, and open a pull request. The workbook and the SQLite file are built locally and are not committed: binary files cannot be checked line by line for technical data, so the open tier does not accept them.

`python tools/build.py --check` validates without rebuilding. Needs Python 3.9+ and `openpyxl` (`pip install openpyxl`).

## Licence

Data and documents: Open Government Licence – Canada 2.0 (`OGL-Canada-2.0`). Code: Apache-2.0. Third-party sources remain under their own terms; this dataset records citations and short factual findings, not their content.

---

Element Ventures (Canada) Ltd. · Sovereign Operating Intelligence (SOI™)
