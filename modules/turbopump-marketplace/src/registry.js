// Handling: Unclassified — working
// Supplier registry: parts (bill of materials) and entities (companies, labs, funders).
// Facts only: who could supply what, who owns them, which parts are export-listed.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const DATA = join(here, '..', 'data');

export const OWNERSHIP = Object.freeze({
  CANADIAN: 'Canadian',
  CA_SUB: 'Canadian subsidiary of foreign parent',
  FOREIGN: 'Foreign',
});

export function loadRegistry(dir = DATA) {
  const parts = JSON.parse(readFileSync(join(dir, 'parts.json'), 'utf8')).parts;
  const entities = JSON.parse(readFileSync(join(dir, 'entities.json'), 'utf8')).entities;
  return createRegistry(parts, entities);
}

export function createRegistry(parts, entities) {
  const partById = new Map(parts.map((p) => [p.id, p]));
  const entityById = new Map(entities.map((e) => [e.id, e]));

  for (const p of parts) {
    if (p.parent && !partById.has(p.parent)) throw new Error(`Part ${p.id}: unknown parent ${p.parent}`);
    for (const c of p.candidates) {
      if (!entityById.has(c.id)) throw new Error(`Part ${p.id}: unknown candidate ${c.id}`);
    }
  }

  const children = (id) => parts.filter((p) => p.parent === id);

  // Path from root, e.g. ["Turbopump assembly", "Fuel (RP-1) pump assembly", "Fuel inducer"]
  const path = (id) => {
    const out = [];
    for (let p = partById.get(id); p; p = p.parent ? partById.get(p.parent) : null) out.unshift(p.name);
    return out;
  };

  const coverage = (p) => {
    if (p.candidates.length === 0) return 'no_candidate';
    if (!p.candidates.some((c) => c.ownership_class === OWNERSHIP.CANADIAN)) return 'no_canadian_owned_candidate';
    return 'canadian_owned_candidate';
  };

  const search = ({ q = '', ownership = null, role = null } = {}) => {
    const needle = q.trim().toLowerCase();
    return entities.filter((e) =>
      (!ownership || e.ownership_class === ownership) &&
      (!role || e.role === role) &&
      (!needle || `${e.name} ${e.capability}`.toLowerCase().includes(needle)));
  };

  const partsSuppliedBy = (entityId) => parts.filter((p) => p.candidates.some((c) => c.id === entityId));

  const summary = () => {
    const byCov = { no_candidate: 0, no_canadian_owned_candidate: 0, canadian_owned_candidate: 0 };
    for (const p of parts) byCov[coverage(p)] += 1;
    const byOwner = {};
    for (const e of entities) byOwner[e.ownership_class] = (byOwner[e.ownership_class] || 0) + 1;
    return {
      parts: parts.length,
      entities: entities.length,
      export_listed: parts.filter((p) => p.export_list.length > 0).length,
      coverage: byCov,
      entities_by_ownership: byOwner,
    };
  };

  return { parts, entities, partById, entityById, children, path, coverage, search, partsSuppliedBy, summary };
}
