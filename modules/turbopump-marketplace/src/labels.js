// Handling: Unclassified — working
// Handling labels attached to every object the module emits.
// Field names follow the NATO STANAG 4774 confidentiality-label concepts
// (policy, classification, categories) so a downstream one-way guard can read them.
// Open tier: the ONLY label this module emits is UNCLASSIFIED // PUBLIC.
// Any other label is refused with an error. Any richer label ladder lives in the private core.

export const OPEN_TIER_LABEL = Object.freeze({
  policy: 'CA-OPEN',
  classification: 'UNCLASSIFIED',
  categories: Object.freeze(['PUBLIC']),
  releasable_to: Object.freeze(['ALL']),
});

const OPEN_TIER_TEXT = 'UNCLASSIFIED // PUBLIC';

function isOpenTier(label) {
  return label != null
    && label.classification === 'UNCLASSIFIED'
    && Array.isArray(label.categories)
    && label.categories.length === 1
    && label.categories[0] === 'PUBLIC';
}

function assertOpenTier(label) {
  if (!isOpenTier(label)) {
    throw new Error(`Open-tier module can only emit ${OPEN_TIER_TEXT}`);
  }
}

export function labelString(label = OPEN_TIER_LABEL) {
  assertOpenTier(label);
  return OPEN_TIER_TEXT;
}

// Wrap a payload with its label. Refuses anything other than the open-tier label.
export function labelled(payload, label = OPEN_TIER_LABEL) {
  assertOpenTier(label);
  return { label, data: payload };
}
