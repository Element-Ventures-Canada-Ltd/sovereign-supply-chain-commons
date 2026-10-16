-- Handling: Unclassified — working
-- Workforce Training and Simulation database: SQLite schema.
-- Generated tables are rebuilt from data/*.csv by tools/build.py.
-- Every record binds to one Sovereign Seam cell (cell_id = LAYER-Mn).

PRAGMA foreign_keys = ON;

CREATE TABLE seam_cells (
  cell_id          TEXT PRIMARY KEY,
  layer_code       TEXT NOT NULL CHECK (layer_code IN ('APP','SOV','MOD','INF','CHI','ENE')),
  layer            TEXT NOT NULL,
  layer_index      INTEGER NOT NULL CHECK (layer_index BETWEEN 1 AND 6),
  capability_code  TEXT NOT NULL,
  capability       TEXT NOT NULL,
  capability_index INTEGER NOT NULL CHECK (capability_index BETWEEN 1 AND 10)
);

CREATE TABLE sources (
  source_id   TEXT PRIMARY KEY,
  title       TEXT NOT NULL,
  publisher   TEXT NOT NULL,
  authors     TEXT,
  published   TEXT,
  url         TEXT NOT NULL CHECK (url LIKE 'https://%'),
  citability  TEXT NOT NULL CHECK (citability IN ('P','A','AS','AN','PR','S')),
  accessed    TEXT NOT NULL,
  note        TEXT
);

CREATE TABLE programs (
  program_id         TEXT PRIMARY KEY,
  name               TEXT NOT NULL,
  provider           TEXT NOT NULL,
  jurisdiction       TEXT,
  sector             TEXT NOT NULL CHECK (sector IN ('defence','civilian','dual-use')),
  domain             TEXT NOT NULL,
  modality           TEXT NOT NULL CHECK (modality IN ('lecture','vr','manikin','live','blended','online','mixed')),
  status             TEXT NOT NULL CHECK (status IN ('active','inactive','unknown','synthetic')),
  cell_id            TEXT NOT NULL REFERENCES seam_cells(cell_id),
  secondary_cell_ids TEXT,
  source_id          TEXT REFERENCES sources(source_id),
  is_synthetic       INTEGER NOT NULL CHECK (is_synthetic IN (0,1)),
  as_of              TEXT NOT NULL,
  notes              TEXT
);

CREATE TABLE facilities (
  facility_id        TEXT PRIMARY KEY,
  name               TEXT NOT NULL,
  operator           TEXT NOT NULL,
  facility_type      TEXT NOT NULL CHECK (facility_type IN ('schoolhouse','embedded-civilian-hospital','simulation-centre','mobile','field-site','test-site')),
  city               TEXT,
  province_state     TEXT,
  country            TEXT NOT NULL,
  sector             TEXT NOT NULL CHECK (sector IN ('defence','civilian','dual-use')),
  cell_id            TEXT NOT NULL REFERENCES seam_cells(cell_id),
  secondary_cell_ids TEXT,
  source_id          TEXT REFERENCES sources(source_id),
  is_synthetic       INTEGER NOT NULL CHECK (is_synthetic IN (0,1)),
  as_of              TEXT NOT NULL,
  notes              TEXT
);

CREATE TABLE equipment (
  equipment_id    TEXT PRIMARY KEY,
  facility_id     TEXT NOT NULL REFERENCES facilities(facility_id),
  equipment_class TEXT NOT NULL CHECK (equipment_class IN ('high-fidelity-manikin','task-trainer','vr-system','av-capture','standardized-patient-suite','test-stand','cold-flow-rig','console-simulator')),
  fidelity        TEXT NOT NULL CHECK (fidelity IN ('low','medium','high','n/a')),
  quantity        INTEGER NOT NULL CHECK (quantity >= 0),
  modality        TEXT NOT NULL,
  cell_id         TEXT NOT NULL REFERENCES seam_cells(cell_id),
  is_synthetic    INTEGER NOT NULL CHECK (is_synthetic IN (0,1)),
  as_of           TEXT NOT NULL,
  notes           TEXT
);

CREATE TABLE skills (
  skill_id           TEXT PRIMARY KEY,
  name               TEXT NOT NULL,
  domain             TEXT NOT NULL,
  skill_type         TEXT NOT NULL CHECK (skill_type IN ('psychomotor','cognitive','team','psychomotor-team','procedural')),
  decay_form         TEXT NOT NULL CHECK (decay_form IN ('exponential')),
  parameter_status   TEXT NOT NULL CHECK (parameter_status IN ('held','open')),
  cell_id            TEXT NOT NULL REFERENCES seam_cells(cell_id),
  secondary_cell_ids TEXT,
  notes              TEXT
);

CREATE TABLE skill_evidence (
  evidence_id          TEXT PRIMARY KEY,
  skill_id             TEXT NOT NULL REFERENCES skills(skill_id),
  finding              TEXT NOT NULL,
  direction            TEXT NOT NULL CHECK (direction IN ('retained','decayed','mixed')),
  interval_months_low  REAL,
  interval_months_high REAL,
  population           TEXT,
  source_id            TEXT NOT NULL REFERENCES sources(source_id),
  as_of                TEXT NOT NULL
);

CREATE TABLE roles (
  role_id   TEXT PRIMARY KEY,
  title     TEXT NOT NULL,
  noc_2021  TEXT NOT NULL CHECK (length(noc_2021) = 5),
  sector    TEXT NOT NULL CHECK (sector IN ('defence','civilian','dual-use')),
  cell_id   TEXT NOT NULL REFERENCES seam_cells(cell_id),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  notes     TEXT
);

CREATE TABLE indicators (
  indicator_id TEXT PRIMARY KEY,
  name         TEXT NOT NULL,
  value        REAL,
  value_text   TEXT NOT NULL,
  unit         TEXT NOT NULL,
  period       TEXT,
  geography    TEXT,
  role_id      TEXT REFERENCES roles(role_id),
  cell_id      TEXT NOT NULL REFERENCES seam_cells(cell_id),
  source_id    TEXT REFERENCES sources(source_id),
  is_synthetic INTEGER NOT NULL CHECK (is_synthetic IN (0,1)),
  as_of        TEXT NOT NULL,
  notes        TEXT
);

CREATE TABLE enabling_environment (
  instrument_id      TEXT PRIMARY KEY,
  name               TEXT NOT NULL,
  instrument_type    TEXT NOT NULL CHECK (instrument_type IN ('strategy','policy','legislation','regulation','directive','standard','accreditation','credential','classification','institution')),
  jurisdiction       TEXT NOT NULL,
  issuer             TEXT NOT NULL,
  issued             TEXT,
  status             TEXT NOT NULL CHECK (status IN ('in-force','published','announced','sunsetting','repealed','benchmark')),
  relevance          TEXT NOT NULL,
  cell_id            TEXT NOT NULL REFERENCES seam_cells(cell_id),
  secondary_cell_ids TEXT,
  source_id          TEXT NOT NULL REFERENCES sources(source_id),
  as_of              TEXT NOT NULL,
  notes              TEXT
);

-- Design Reference Missions: the real-world job every requirement traces to.
CREATE TABLE missions (
  mission_id         TEXT PRIMARY KEY,
  name               TEXT NOT NULL,
  description        TEXT NOT NULL,
  cell_id            TEXT NOT NULL REFERENCES seam_cells(cell_id),
  secondary_cell_ids TEXT,
  source_id          TEXT NOT NULL REFERENCES sources(source_id),
  as_of              TEXT NOT NULL,
  notes              TEXT
);

-- Link: a mission needs a role to hold a skill. basis = 'source' (cited) or 'inference' (EV judgement, uncited).
CREATE TABLE role_skills (
  link_id    TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL REFERENCES missions(mission_id),
  role_id    TEXT NOT NULL REFERENCES roles(role_id),
  skill_id   TEXT NOT NULL REFERENCES skills(skill_id),
  basis      TEXT NOT NULL CHECK (basis IN ('source','inference')),
  source_id  TEXT REFERENCES sources(source_id),
  notes      TEXT,
  CHECK ((basis = 'source' AND source_id IS NOT NULL) OR (basis = 'inference' AND source_id IS NULL))
);

CREATE TABLE dataset_metadata (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- One row per (record, cell) binding, primary and secondary, across all tables.
CREATE TABLE record_cells (
  table_name   TEXT NOT NULL,
  record_id    TEXT NOT NULL,
  cell_id      TEXT NOT NULL REFERENCES seam_cells(cell_id),
  binding      TEXT NOT NULL CHECK (binding IN ('primary','secondary')),
  is_synthetic INTEGER NOT NULL CHECK (is_synthetic IN (0,1)),
  PRIMARY KEY (table_name, record_id, cell_id)
);

-- Records per Seam cell. Public and synthetic are counted separately, never summed.
CREATE VIEW v_seam_coverage AS
SELECT c.cell_id, c.layer, c.capability,
       SUM(CASE WHEN r.binding = 'primary'   AND r.is_synthetic = 0 THEN 1 ELSE 0 END) AS public_primary,
       SUM(CASE WHEN r.binding = 'secondary' AND r.is_synthetic = 0 THEN 1 ELSE 0 END) AS public_secondary,
       SUM(CASE WHEN r.is_synthetic = 1 THEN 1 ELSE 0 END)                             AS synthetic
FROM seam_cells c
LEFT JOIN record_cells r ON r.cell_id = c.cell_id
GROUP BY c.cell_id, c.layer, c.capability, c.layer_index, c.capability_index
ORDER BY c.layer_index, c.capability_index;
