// Handling: Unclassified — working
// Interoperability: clean-room adapter slots.
//
// Rules (interoperability decision, Oct 2026):
// - Third-party platform SDKs: where an SDK licence bars redistribution, its adapter is an
//   OUT-OF-REPO plugin installed at deploy time. Nothing from those SDKs lives here.
// - Other third-party platforms: design-only import/export mapping. No runtime link, no SDK code.
// - This module's own entity model is the master. Third-party shapes map FROM it, never the reverse.
// CI (scripts/check-interop-guard.mjs) fails the build if a proprietary SDK package appears.
import { isAbsolute } from 'node:path';
import { pathToFileURL } from 'node:url';
import { labelled } from '../labels.js';

// Neutral, vendor-free entity shape. Field names are our own.
export function toNeutralEntity(e, registry) {
  return {
    id: `tpm:entity:${e.id}`,
    kind: e.role,
    name: e.name,
    ownership: { class: e.ownership_class, parent_jurisdiction: e.parent_jurisdiction, ultimate_parent: e.ultimate_parent || null },
    location: { country: e.location?.country || null, region: typeof e.location?.region === 'string' ? e.location.region : null },
    capability: e.capability,
    supplies: registry.partsSuppliedBy(e.id).map((p) => `tpm:part:${p.id}`),
    evidence: { grade: e.evidence_grade, citability: e.citability, sources: e.sources, as_of: e.as_of },
  };
}

export function toNeutralPart(p, registry) {
  return {
    id: `tpm:part:${p.id}`,
    name: p.name,
    parent: p.parent ? `tpm:part:${p.parent}` : null,
    export_list: p.export_list,
    coverage: registry.coverage(p),
    candidates: p.candidates.map((c) => `tpm:entity:${c.id}`),
  };
}

export function exportBundle(registry) {
  return labelled({
    schema: 'tpm-interop/1',
    entities: registry.entities.map((e) => toNeutralEntity(e, registry)),
    parts: registry.parts.map((p) => toNeutralPart(p, registry)),
  });
}

// Flat tables suitable for any analytics platform's CSV dataset import
// (for example a third-party platform object type backed by a dataset). Design-only: no API calls.
export function toCsvTables(registry) {
  const esc = (v) => {
    let s = v == null ? '' : Array.isArray(v) ? v.join('|') : String(v);
    if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`; // neutralise spreadsheet formulas
    return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const table = (cols, rows) => (rows.length === 0 ? cols.join(',') + '\n' : [cols.join(','), ...rows.map((r) => cols.map((c) => esc(r[c])).join(','))].join('\n') + '\n');
  const entities = registry.entities.map((e) => ({ entity_id: e.id, name: e.name, role: e.role, ownership_class: e.ownership_class, parent_jurisdiction: e.parent_jurisdiction, country: e.location?.country, evidence_grade: e.evidence_grade }));
  const parts = registry.parts.map((p) => ({ part_id: p.id, name: p.name, parent_id: p.parent, level: p.level, export_listed: p.export_list.length > 0, coverage: registry.coverage(p) }));
  const links = registry.parts.flatMap((p) => p.candidates.map((c) => ({ part_id: p.id, entity_id: c.id })));
  return {
    'entities.csv': table(['entity_id', 'name', 'role', 'ownership_class', 'parent_jurisdiction', 'country', 'evidence_grade'], entities),
    'parts.csv': table(['part_id', 'name', 'parent_id', 'level', 'export_listed', 'coverage'], parts),
    'part_candidates.csv': table(['part_id', 'entity_id'], links),
  };
}

// Plugin slot for out-of-repo adapters (e.g. a third-party platform plugin in a separate repo).
// We pass plugins only the labelled open-tier bundle, but a plugin runs in-process with the
// same rights as this service: install only reviewed plugins, from absolute file paths.
export async function loadPlugins(list = (process.env.TPM_INTEROP_PLUGINS || '').split(',').map((s) => s.trim()).filter(Boolean)) {
  const plugins = [];
  for (const path of list) {
    if (!isAbsolute(path)) throw new Error(`Interop plugin path must be absolute: ${path}`);
    const mod = await import(pathToFileURL(path).href);
    const p = mod.default;
    if (!p || typeof p.name !== 'string' || typeof p.push !== 'function') throw new Error(`Interop plugin ${path} must export { name, push(bundle) }`);
    plugins.push(p);
  }
  return plugins;
}

export const ADAPTER_SLOTS = Object.freeze([
  { id: 'neutral-json', status: 'built', where: 'this repo', note: 'Labelled JSON bundle; the master format.' },
  { id: 'csv-tables', status: 'built', where: 'this repo', note: 'Flat tables for dataset import into analytics platforms.' },
  { id: 'platform-plugin', status: 'slot', where: 'separate repo (plugin)', note: 'Third-party platform SDK licence bars redistribution. Build after developer-programme sandbox approval.' },
  { id: 'data-platform-mapping', status: 'design-only', where: 'mapping doc', note: 'Import/export mapping for customers moving to or from a third-party data platform. No runtime link.' },
  { id: 'cot-tak', status: 'planned', where: 'this repo', note: 'Cursor on Target markers for sites, once site coordinates are verified.' },
]);
