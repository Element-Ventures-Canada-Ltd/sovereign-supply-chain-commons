// Handling: Unclassified — working
// Tests for scripts/check-interop-guard.mjs. Run: node --test scripts/tests/*.test.mjs
// Vendor tokens are synthetic (`vendorx`); real ones live only in the GUARD_TERMS secret.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const GUARD = join(dirname(fileURLToPath(import.meta.url)), '..', 'check-interop-guard.mjs');
const SDK_TERMS = 'sdk:vendorx';
const SDK_REF = '"@vendorx/client"';
const SDK_REPO = 'github:vendorx/x';

// files: { path: body }. git: null (plain folder), or { add: [paths to commit, forced] }.
function run(files, git = null, { terms = SDK_TERMS, args = [] } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'interop-guard-'));
  try {
    for (const [rel, body] of Object.entries(files)) {
      mkdirSync(dirname(join(dir, rel)), { recursive: true });
      writeFileSync(join(dir, rel), body);
    }
    if (git) {
      const g = (...a) => spawnSync('git', ['-C', dir, ...a], { encoding: 'utf8' });
      g('init', '-q');
      for (const p of git.add) g('add', '-f', p);
    }
    const r = spawnSync(process.execPath, [GUARD, dir, ...args], { encoding: 'utf8', env: { ...process.env, GUARD_TERMS: terms } });
    return { code: r.status, out: r.stdout + r.stderr };
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

const PYC = { 'pkg/__pycache__/m.cpython-313.pyc': '\0binary' };

test('clean tree passes', () => {
  const r = run({ 'a.md': 'Handling: Unclassified — working\n' });
  assert.equal(r.code, 0, r.out);
});

test('.pin and .sql files are recognised as text and pass when clean', () => {
  const r = run({ 'x.pin': 'commit: abc\n', 'schema.sql': '-- ok\nCREATE TABLE t (id TEXT);\n' });
  assert.equal(r.code, 0, r.out);
});

test('.pin and .sql files are still scanned for SDK references', () => {
  const pin = run({ 'x.pin': `repository: ${SDK_REPO}\n` });
  assert.equal(pin.code, 1, pin.out);
  assert.match(pin.out, /proprietary SDK reference/);
  const sql = run({ 'schema.sql': `-- ${SDK_REF}\n` });
  assert.equal(sql.code, 1, sql.out);
  assert.match(sql.out, /proprietary SDK reference/);
});

test('an untracked __pycache__ in a git checkout is skipped', () => {
  const r = run(PYC, { add: [] });
  assert.equal(r.code, 0, r.out);
});

test('a __pycache__ with a committed (force-added) file is scanned and rejected', () => {
  const r = run(PYC, { add: ['pkg/__pycache__/m.cpython-313.pyc'] });
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /unrecognised file type \.pyc/);
});

test('outside a git checkout, __pycache__ is scanned (fail closed)', () => {
  const r = run(PYC);
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /unrecognised file type \.pyc/);
});

test('a .pyc outside __pycache__ is still rejected', () => {
  const r = run({ 'pkg/m.pyc': '\0binary' });
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /unrecognised file type \.pyc/);
});

test('binary documents and databases are still rejected', () => {
  const xlsx = run({ 'release/db.xlsx': 'PK' });
  assert.equal(xlsx.code, 1, xlsx.out);
  assert.match(xlsx.out, /\.xlsx files are not accepted/);
  const sqlite = run({ 'release/db.sqlite': 'SQLite format 3\0' });
  assert.equal(sqlite.code, 1, sqlite.out);
  assert.match(sqlite.out, /unrecognised file type \.sqlite/);
});

// The workflow scans the PR checkout with the BASE copy of the guard, so the PR's own copy of the
// guard is scanned like any other file. Its comments must not trip the label rule.
test('a copy of the guard inside the scanned tree passes (no self-match on the label rule)', async () => {
  const { readFileSync } = await import('node:fs');
  const r = run({ 'scripts/check-interop-guard.mjs': readFileSync(GUARD, 'utf8') });
  assert.equal(r.code, 0, r.out);
});

test('a handling label other than UNCLASSIFIED is still rejected', () => {
  const label = ['SEC', 'RET'].join('') + ' // ' + 'REL';
  const r = run({ 'notes.md': `Marking: ${label}\n` });
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /handling label other than UNCLASSIFIED/);
});

test('an SDK vendor token from the secret is rejected anywhere in text', () => {
  const r = run({ 'notes.md': 'Built on VendorX tooling.\n' });
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /proprietary SDK reference/);
});

test('a package.json dependency on an SDK vendor package is rejected', () => {
  const r = run({ 'package.json': JSON.stringify({ dependencies: { '@vendorx/sdk': '1.0.0' } }) });
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /proprietary SDK dependency/);
});

test('sdk: lines are not treated as restricted terms, and plain lines still are', () => {
  const r = run({ 'a.md': 'the word sdk:vendorx is never written here\nProject Zeta\n' }, null, { terms: 'sdk:vendory\nProject Zeta' });
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /restricted reference found \(term #1\)/);
  assert.doesNotMatch(r.out, /proprietary SDK/);
});

test('--require-terms refuses to pass when the secret has no sdk: lines', () => {
  const r = run({ 'a.md': 'ok\n' }, null, { terms: 'Project Zeta', args: ['--require-terms'] });
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /no sdk: lines/);
});

test('--require-terms passes a clean tree when both kinds of entry are present', () => {
  const r = run({ 'a.md': 'Handling: Unclassified — working\n' }, null, { terms: 'sdk:vendorx\nProject Zeta', args: ['--require-terms'] });
  assert.equal(r.code, 0, r.out);
  assert.match(r.out, /1 restricted terms, 1 SDK tokens checked/);
});
