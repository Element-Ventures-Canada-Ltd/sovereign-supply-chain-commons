// Handling: Unclassified — working
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  loadRegistry, createRegistry, matchRfq, validateRfq, findGaps, investmentProjects,
  FactsOnlyEngine, loadEngine, exportBundle, toCsvTables, labelled, labelString, OPEN_TIER_LABEL,
  ADAPTER_SLOTS,
} from '../src/index.js';

const reg = loadRegistry();

test('registry loads and is internally consistent', () => {
  const s = reg.summary();
  assert.equal(s.parts, 41);
  assert.equal(s.entities, 28);
  assert.equal(s.coverage.no_candidate + s.coverage.no_canadian_owned_candidate + s.coverage.canadian_owned_candidate, 41);
  assert.equal(s.coverage.no_candidate, 8);
});

test('registry rejects a dangling candidate reference', () => {
  assert.throws(() => createRegistry([{ id: 'X', parent: null, candidates: [{ id: 'E-404' }], export_list: [] }], []), /unknown candidate/);
});

test('ownership is separate from location: a Canadian plant of a foreign parent is not Canadian-owned', () => {
  const blisk = reg.partById.get('TP-310');
  assert.equal(reg.coverage(blisk), 'no_canadian_owned_candidate');
});

test('RFQ validation catches bad input and technical data', () => {
  assert.ok(validateRfq({}, reg).length >= 2);
  const errs = validateRfq({ title: 'Inducer buy', part_ids: ['TP-110'], quantity: 2, notes: 'attached drawing with tolerance' }, reg);
  assert.ok(errs.some((e) => e.includes('technical data')));
  assert.deepEqual(validateRfq({ title: 'Inducer buy', part_ids: ['TP-110'], quantity: 2 }, reg), []);
});

test('matching ranks Canadian-owned first and honours the sovereignty rule', () => {
  const r = matchRfq({ title: 'Fuel volute', part_ids: ['TP-130'], quantity: 4 }, reg);
  assert.ok(r.ok);
  assert.equal(r.lines[0].candidates[0].ownership_class, 'Canadian');
  const strict = matchRfq({ title: 'Fuel inducer', part_ids: ['TP-110'], quantity: 1, sovereignty: 'canadian_owned' }, reg);
  assert.equal(strict.lines[0].eligible, 0);
  assert.ok(strict.lines[0].flags.some((f) => f.code === 'NO_ELIGIBLE'));
  assert.equal(strict.fully_covered, false);
});

test('export-listed parts are flagged', () => {
  const r = matchRfq({ title: 'Turbine assembly', part_ids: ['TP-300'], quantity: 1 }, reg);
  assert.ok(r.lines[0].flags.some((f) => f.code === 'EXPORT_LISTED'));
});

test('test capacity not available until after need-by date is cautioned', () => {
  const r = matchRfq({ title: 'Qualification', part_ids: ['TP-990'], quantity: 1, need_by: '2027-06-01' }, reg);
  const crc = r.lines[0].candidates.find((c) => c.entity_id === 'E-019');
  assert.ok(crc.cautions.some((c) => c.startsWith('available from')));
});

test('gap finder lists every non-covered part, build gaps first', () => {
  const gaps = findGaps(reg);
  assert.equal(gaps.length, 25); // 8 with no candidate + 17 with no Canadian-owned candidate
  assert.equal(gaps[0].pathway, 'build');
  const projects = investmentProjects(reg);
  assert.ok(projects.length > 0);
  assert.equal(projects.reduce((n, p) => n + p.gaps.length, 0), 25);
});

test('open tier never emits scores', async () => {
  const a = await FactsOnlyEngine.assess(reg);
  assert.equal(a.chokepoint_scores, null);
  assert.equal(a.critical_path, null);
  assert.equal(await loadEngine(''), FactsOnlyEngine);
});

test('interop bundle is labelled and vendor-free', () => {
  const b = exportBundle(reg);
  assert.equal(b.label.classification, 'UNCLASSIFIED');
  assert.equal(b.data.entities.length, 28);
  const json = JSON.stringify(b);
  assert.ok(!/lattice|osdk|palantir|anduril/i.test(json));
});

test('labels: only UNCLASSIFIED // PUBLIC is emitted; anything else throws', () => {
  const NOT_PUBLIC = 'NOT-PUBLIC-TEST'; // neutral placeholder, not a real marking
  assert.equal(labelString(), 'UNCLASSIFIED // PUBLIC');
  assert.deepEqual(labelled({ a: 1 }).label, OPEN_TIER_LABEL);
  assert.throws(() => labelled({}, { classification: NOT_PUBLIC, categories: [] }), /can only emit/);
  assert.throws(() => labelled({}, { classification: NOT_PUBLIC, categories: ['PUBLIC'] }), /can only emit/);
  assert.throws(() => labelled({}, { classification: 'UNCLASSIFIED', categories: [NOT_PUBLIC] }), /can only emit/);
  assert.throws(() => labelled({}, { classification: 'UNCLASSIFIED', categories: ['PUBLIC', NOT_PUBLIC] }), /can only emit/);
  assert.throws(() => labelString({ classification: NOT_PUBLIC, categories: ['PUBLIC'] }), /can only emit/);
  assert.throws(() => labelled({}, {}), /can only emit/);
  assert.throws(() => labelled({}, null), /can only emit/);
});

test('CSV tables have one row per record and quote commas', () => {
  const t = toCsvTables(reg);
  assert.equal(t['entities.csv'].trim().split('\n').length, 29);
  assert.match(t['entities.csv'], /"National student rocketry|"AP&C|"Neo|,"/);
});

test('RFQ refuses unknown fields and unit-bearing numbers, allows normal part names', () => {
  const base = { title: 'Titanium billet / bar purchase', part_ids: ['TP-940'], quantity: 1 };
  assert.deepEqual(validateRfq(base, reg), []);
  assert.ok(validateRfq({ ...base, specs: 'x' }, reg).some((e) => e.startsWith('specs')));
  assert.ok(validateRfq({ ...base, notes: 'bore 42.5 mm, 30 krpm' }, reg).some((e) => e.includes('technical data')));
  assert.ok(validateRfq({ ...base, notes: 'see attached drawings' }, reg).some((e) => e.includes('technical data')));
  assert.deepEqual(validateRfq({ ...base, notes: 'Budget about CAD 40k, delivery to Ontario' }, reg), []);
});

test('CSV neutralises spreadsheet formulas', () => {
  const r = createRegistry(
    [{ id: 'TP-000', level: 0, parent: null, name: 'A', export_list: [], candidates: [{ id: 'E-001', ownership_class: 'Foreign' }], sources: [] }],
    [{ id: 'E-001', name: '=HYPERLINK("https://x")', role: 'supplier', ownership_class: 'Foreign', parent_jurisdiction: 'US', location: { country: 'US' }, evidence_grade: 'reported', citability: 'AS', sources: [] }]);
  assert.match(toCsvTables(r)['entities.csv'], /"'=HYPERLINK/);
});

test('engine and plugin loaders refuse relative paths', async () => {
  await assert.rejects(loadEngine('some-package'), /absolute/);
});

test('adapter slots and the web page name no third-party vendor', () => {
  const vendor = /lattice|osdk|palantir|anduril|foundry/i;
  assert.ok(!vendor.test(JSON.stringify(ADAPTER_SLOTS)));
  const page = readFileSync(new URL('../web/template.html', import.meta.url), 'utf8');
  assert.ok(!vendor.test(page));
});
