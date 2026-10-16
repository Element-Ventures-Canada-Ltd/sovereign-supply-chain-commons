// Handling: Unclassified — working
// Request for quotation (RFQ) and supplier matchmaking.
// Matching is transparent and facts-based: no prices, no hidden scores.
// Ranking order: Canadian-owned first, then stronger evidence, then better source citability.
import { OWNERSHIP } from './registry.js';

const OWN_RANK = { [OWNERSHIP.CANADIAN]: 0, [OWNERSHIP.CA_SUB]: 1, [OWNERSHIP.FOREIGN]: 2 };
const GRADE_RANK = { confirmed: 0, reported: 1 };
const CITE_RANK = { P: 0, AN: 1, AS: 2 };
const SOVEREIGNTY = ['any', 'canadian_presence', 'canadian_owned'];
const FIELDS = new Set(['title', 'part_ids', 'quantity', 'need_by', 'sovereignty', 'notes']);
// Advisory screen only: buyers also attest that no technical data is included.
export const TECH_DATA = /\b(drawings?|tolerances?|rpm|pressure[\s-]*ratios?|test[\s-]*data|spec(ification)?[\s-]*sheets?|cad (files?|models?)|step files?|microns?)\b|\d+(\.\d+)?\s*(mm|µm|psi|mpa|bar|krpm|rpm|kn|kw)\b/i;

export function validateRfq(rfq, registry) {
  const errors = [];
  if (!rfq || typeof rfq !== 'object') return ['RFQ must be an object'];
  for (const k of Object.keys(rfq)) if (!FIELDS.has(k)) errors.push(`${k}: field not accepted`);
  if (!rfq.title || String(rfq.title).trim().length < 4 || String(rfq.title).length > 120) errors.push('title: 4 to 120 characters');
  if (rfq.notes != null && String(rfq.notes).length > 1000) errors.push('notes: at most 1000 characters');
  if (!Array.isArray(rfq.part_ids) || rfq.part_ids.length === 0) errors.push('part_ids: choose at least one part');
  else for (const id of rfq.part_ids) if (!registry.partById.has(id)) errors.push(`part_ids: unknown part ${id}`);
  if (!Number.isInteger(rfq.quantity) || rfq.quantity < 1 || rfq.quantity > 10000) errors.push('quantity: whole number 1-10000');
  if (rfq.need_by && Number.isNaN(Date.parse(rfq.need_by))) errors.push('need_by: use YYYY-MM-DD');
  if (rfq.sovereignty && !SOVEREIGNTY.includes(rfq.sovereignty)) errors.push(`sovereignty: one of ${SOVEREIGNTY.join(', ')}`);
  // Open tier refuses technical data: controlled goods details never go in an RFQ here.
  const text = `${rfq.title} ${rfq.notes || ''}`;
  if (TECH_DATA.test(text)) {
    errors.push('notes: technical data is not accepted in the open tier; share it under NDA through the controlled channel');
  }
  return errors;
}

function allowed(ownership, sovereignty) {
  if (sovereignty === 'canadian_owned') return ownership === OWNERSHIP.CANADIAN;
  if (sovereignty === 'canadian_presence') return ownership !== OWNERSHIP.FOREIGN;
  return true;
}

export function matchRfq(rfq, registry) {
  const errors = validateRfq(rfq, registry);
  if (errors.length) return { ok: false, errors };
  const sovereignty = rfq.sovereignty || 'any';

  const lines = rfq.part_ids.map((pid) => {
    const part = registry.partById.get(pid);
    const flags = [];
    if (part.export_list.length) flags.push({ code: 'EXPORT_LISTED', text: `Export Control List ${part.export_list.join(', ')}: suppliers need Controlled Goods Program registration` });

    const ranked = part.candidates
      .map((c) => registry.entityById.get(c.id))
      .filter((e) => e.role === 'supplier' || e.role === 'design_authority' || e.role === 'test_capacity')
      .map((e) => {
        const cautions = [];
        if (e.parent_jurisdiction === 'UNVERIFIED') cautions.push('ownership not verified');
        if (e.identity_known === false) cautions.push('identity not disclosed');
        if (e.available_from && rfq.need_by && Date.parse(e.available_from) > Date.parse(rfq.need_by)) cautions.push(`available from ${e.available_from}`);
        return { entity_id: e.id, name: e.name, ownership_class: e.ownership_class, evidence_grade: e.evidence_grade, citability: e.citability, eligible: allowed(e.ownership_class, sovereignty), cautions };
      })
      .sort((a, b) =>
        (b.eligible - a.eligible) ||
        (OWN_RANK[a.ownership_class] - OWN_RANK[b.ownership_class]) ||
        (GRADE_RANK[a.evidence_grade] - GRADE_RANK[b.evidence_grade]) ||
        (CITE_RANK[a.citability] - CITE_RANK[b.citability]) ||
        a.name.localeCompare(b.name));

    const eligible = ranked.filter((r) => r.eligible).length;
    if (ranked.length === 0) flags.push({ code: 'NO_CANDIDATE', text: 'No public candidate. Routed to the gap finder.' });
    else if (eligible === 0) flags.push({ code: 'NO_ELIGIBLE', text: `No candidate meets the "${sovereignty}" rule.` });

    return { part_id: pid, part: part.name, path: registry.path(pid), candidates: ranked, eligible, flags };
  });

  const { title, part_ids, quantity, need_by = null, notes = '' } = rfq;
  return { ok: true, rfq: { title, part_ids, quantity, need_by, sovereignty, notes }, lines, fully_covered: lines.every((l) => l.eligible > 0) };
}
