// Handling: Unclassified — working
// Gap and investment finder (open tier).
// Turns coverage gaps into investable-project candidates using facts only.
// Sizing, scoring and lead times come from the private assessment engine, never from here.

const PATHWAY = {
  no_candidate: { pathway: 'build', thesis: 'No public supplier anywhere in the registry. Candidate for a new Canadian capability or an allied build-partner-buy arrangement.' },
  no_canadian_owned_candidate: { pathway: 'domesticate', thesis: 'Suppliers exist, but none are Canadian-owned. Candidate for Canadian investment, a joint venture, or qualifying a Canadian alternate.' },
};

export function findGaps(registry) {
  const gaps = [];
  for (const p of registry.parts) {
    const cov = registry.coverage(p);
    if (cov === 'canadian_owned_candidate') continue;
    const foreignParents = [...new Set(p.candidates
      .map((c) => registry.entityById.get(c.id))
      .map((e) => e.parent_jurisdiction)
      .filter((j) => j && j !== 'CA' && j !== 'UNVERIFIED'))];
    const unverifiedOwnership = p.candidates.some((c) => registry.entityById.get(c.id).parent_jurisdiction === 'UNVERIFIED');
    gaps.push({
      part_id: p.id,
      part: p.name,
      level: p.level,
      path: registry.path(p.id),
      gap: cov,
      ...PATHWAY[cov],
      export_listed: p.export_list.length > 0,
      candidate_count: p.candidates.length,
      foreign_parent_jurisdictions: foreignParents,
      unverified_ownership: unverifiedOwnership,
      sources: p.sources,
    });
  }
  // Order: build gaps first, then deeper parts (raw materials) before assemblies.
  return gaps.sort((a, b) => (a.pathway === b.pathway ? b.level - a.level : a.pathway === 'build' ? -1 : 1));
}

// Group gaps into investable "projects": one per parent assembly.
export function investmentProjects(registry) {
  const byParent = new Map();
  for (const g of findGaps(registry)) {
    const parentId = registry.partById.get(g.part_id).parent || g.part_id;
    const key = parentId;
    if (!byParent.has(key)) byParent.set(key, { assembly_id: key, assembly: registry.partById.get(key).name, gaps: [] });
    byParent.get(key).gaps.push(g);
  }
  return [...byParent.values()]
    .map((p) => ({ ...p, build: p.gaps.filter((g) => g.pathway === 'build').length, domesticate: p.gaps.filter((g) => g.pathway === 'domesticate').length }))
    .sort((a, b) => (b.build - a.build) || (b.gaps.length - a.gaps.length));
}
