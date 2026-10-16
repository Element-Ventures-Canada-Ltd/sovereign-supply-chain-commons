#!/usr/bin/env node
// Handling: Unclassified — working
// Interop and IP guard for the open tier. Fails CI when:
// 1. a proprietary third-party platform SDK package is referenced: their licences bar redistribution
//    (vendor tokens come from `sdk:` lines in the GUARD_TERMS secret, never the repo);
// 2. restricted engagement references appear (terms come from the GUARD_TERMS secret, never the repo);
// 3. a file carries a handling label (an upper-case marking, double slash, category) other than UNCLASSIFIED // PUBLIC;
// 4. a binary document type that could carry technical drawings is added (fail closed);
// 5. a data record has a malformed id or a non-https source.
// Zero dependencies. Run from the BASE branch against the PR checkout:
// node scripts/check-interop-guard.mjs <dir-to-scan> [--require-terms]
import { readdirSync, readFileSync, lstatSync, realpathSync } from 'node:fs';
import { join, relative, extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const args = process.argv.slice(2);
const requireTerms = args.includes('--require-terms');
const root = resolve(args.find((a) => !a.startsWith('--')) || join(fileURLToPath(import.meta.url), '..', '..'));
const self = realpathSync(fileURLToPath(import.meta.url));

const SKIP_DIRS = new Set(['node_modules', '.git', 'coverage']);
// Python's local cache. Skipped only when git confirms nothing inside it is committed (see cacheIsUntracked).
const CACHE_DIRS = new Set(['__pycache__']);
const TEXT = new Set(['.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx', '.json', '.yaml', '.yml', '.md', '.html', '.css', '.txt', '.csv', '.py', '.sh', '.toml', '.xml', '.svg', '.pin', '.sql', '']);
const BLOCKED = new Set(['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.zip', '.7z', '.tar', '.gz', '.step', '.stp', '.iges', '.igs', '.dwg', '.dxf', '.stl', '.sldprt', '.x_t']);
const IMAGES = new Set(['.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.woff', '.woff2']);

// Any upper-case marking-double-slash-category label shape is checked; only UNCLASSIFIED is allowed.
const LABEL = /\b([A-Z][A-Z-]+(?: [A-Z][A-Z-]+)*)\s*\/\/\s*[A-Z]{2,}/g;
// GUARD_TERMS: one entry per line. A line starting `sdk:` names a proprietary SDK vendor token;
// every other line is a restricted reference. Both are matched case-insensitively.
const lines = (process.env.GUARD_TERMS || '').split('\n').map((s) => s.trim()).filter(Boolean);
const isSdk = (l) => /^sdk:/i.test(l);
const sdkTokens = lines.filter(isSdk).map((l) => l.slice(4).trim().toLowerCase()).filter(Boolean);
const terms = lines.filter((l) => !isSdk(l));
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
// Package names: `@token/...` or `token` followed by a non-alphanumeric character or the end.
const SDK_NAME = sdkTokens.length
  ? new RegExp(`^(?:${sdkTokens.map((t) => `@${esc(t)}/|${esc(t)}(?![a-z0-9])`).join('|')})`, 'i')
  : null;

const failures = [];
const fail = (rel, msg) => failures.push(`${rel}: ${msg}`);

// True only when git runs here and lists no tracked file inside dir. Anything else
// (not a git checkout, git missing, a force-added file) means the folder is scanned: fail closed.
function cacheIsUntracked(dir) {
  const r = spawnSync('git', ['-C', dir, 'ls-files', '--', '.'], { encoding: 'utf8' });
  return r.status === 0 && r.stdout.trim() === '';
}

function checkPackageJson(rel, text) {
  let pkg; try { pkg = JSON.parse(text); } catch { return fail(rel, 'invalid JSON'); }
  for (const field of ['dependencies', 'devDependencies', 'optionalDependencies', 'peerDependencies', 'bundledDependencies']) {
    for (const [name, spec] of Object.entries(pkg[field] || {})) {
      if (SDK_NAME && (SDK_NAME.test(name) || SDK_NAME.test(String(spec).replace(/^npm:/, '')))) fail(rel, `proprietary SDK dependency "${name}" — move the adapter out of the open repo`);
    }
  }
}

function checkData(rel, text) {
  let doc; try { doc = JSON.parse(text); } catch { return fail(rel, 'invalid JSON'); }
  const recs = doc.parts || doc.entities || [];
  for (const r of recs) {
    if (!/^(TP|E)-\d{3}$/.test(String(r.id))) fail(rel, `malformed id ${JSON.stringify(r.id).slice(0, 40)}`);
    for (const s of r.sources || []) {
      let ok = false; try { ok = new URL(s).protocol === 'https:'; } catch { /* invalid */ }
      if (!ok) fail(rel, `${r.id}: source is not an https URL`);
    }
    for (const c of r.candidates || []) if (!/^E-\d{3}$/.test(String(c.id))) fail(rel, `${r.id}: malformed candidate id`);
  }
}

function walk(dir) {
  for (const name of readdirSync(dir)) {
    if (SKIP_DIRS.has(name)) continue;
    const p = join(dir, name);
    const st = lstatSync(p);
    const rel = relative(root, p);
    if (st.isSymbolicLink()) { fail(rel, 'symbolic links are not allowed'); continue; }
    if (st.isDirectory()) {
      if (CACHE_DIRS.has(name) && cacheIsUntracked(p)) continue;
      walk(p);
      continue;
    }
    if (realpathSync(p) === self) continue;
    const ext = extname(name).toLowerCase();
    if (BLOCKED.has(ext)) { fail(rel, `${ext} files are not accepted in the open tier (possible technical data)`); continue; }
    if (IMAGES.has(ext)) continue;
    if (!TEXT.has(ext)) { fail(rel, `unrecognised file type ${ext || '(none)'}; add it to the guard after review`); continue; }
    if (st.size > 5_000_000) { fail(rel, 'text file over 5 MB'); continue; }
    const text = readFileSync(p, 'utf8');
    const lower = text.toLowerCase();
    if (sdkTokens.some((t) => lower.includes(t))) fail(rel, 'proprietary SDK reference — move the adapter out of the open repo');
    for (const m of text.matchAll(LABEL)) if (m[1] !== 'UNCLASSIFIED') { fail(rel, 'handling label other than UNCLASSIFIED // PUBLIC'); break; }
    terms.forEach((t, i) => { if (text.toLowerCase().includes(t.toLowerCase())) fail(rel, `restricted reference found (term #${i + 1})`); });
    if (name === 'package.json') checkPackageJson(rel, text);
    if (rel.split(sep).includes('data') && ext === '.json' && rel.includes('turbopump-marketplace')) checkData(rel, text);
  }
}

if (requireTerms && terms.length === 0) {
  console.error('Interop/IP guard: GUARD_TERMS is empty but --require-terms was set. Refusing to pass.');
  process.exit(1);
}
if (requireTerms && sdkTokens.length === 0) {
  console.error('Interop/IP guard: GUARD_TERMS has no sdk: lines but --require-terms was set. Refusing to pass.');
  process.exit(1);
}
walk(root);
if (failures.length) {
  console.error(`Interop/IP guard: ${failures.length} problem(s)\n` + failures.map((f) => ` - ${f}`).join('\n'));
  process.exit(1);
}
console.log(`Interop/IP guard: clean (${terms.length} restricted terms, ${sdkTokens.length} SDK tokens checked)`);
