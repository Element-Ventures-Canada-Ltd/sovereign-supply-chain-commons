// Handling: Unclassified — working
// Assessment engine port.
// The open tier ships only the interface and a facts-only reference engine.
// The private assessment engine (chokepoint scores, lead times, critical path, stress scenarios)
// lives in the private core and plugs in here at deploy time. It is never vendored into this repo.

import { isAbsolute } from 'node:path';
import { pathToFileURL } from 'node:url';

/**
 * @typedef {Object} AssessmentEngine
 * @property {string} name
 * @property {'open'|'private'} tier
 * @property {(registry: object) => Promise<Assessment>} assess
 *
 * @typedef {Object} Assessment
 * @property {Object<string, number>|null} chokepoint_scores  part_id -> 0..1
 * @property {{min_weeks:number,max_weeks:number,path:string[]}|null} critical_path
 * @property {Array<{name:string, critical_path_weeks:number}>|null} scenarios
 * @property {string} note
 */

export const FactsOnlyEngine = Object.freeze({
  name: 'facts-only',
  tier: 'open',
  async assess() {
    return {
      chokepoint_scores: null,
      critical_path: null,
      scenarios: null,
      note: 'Assessment not available in the open tier. Connect the private engine to see scores, lead times and scenarios.',
    };
  },
});

function isEngine(e) {
  return e && typeof e.name === 'string' && (e.tier === 'open' || e.tier === 'private') && typeof e.assess === 'function';
}

// Load an engine from a module path set by the deployer (e.g. the private core package).
// Falls back to the facts-only engine so the open build always works.
export async function loadEngine(modulePath = process.env.TPM_ENGINE_MODULE) {
  if (!modulePath) return FactsOnlyEngine;
  if (!isAbsolute(modulePath)) throw new Error('TPM_ENGINE_MODULE must be an absolute file path to a reviewed private package');
  const mod = await import(pathToFileURL(modulePath).href);
  const engine = mod.default || mod.engine;
  if (!isEngine(engine)) throw new Error(`TPM_ENGINE_MODULE ${modulePath} does not export a valid AssessmentEngine`);
  return engine;
}
