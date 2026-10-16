Handling: Unclassified — working

# Turbopump Marketplace (open tier)

A marketplace and control tower for the Canadian supply chain of a small liquid-rocket turbopump.
It answers four questions from public records:

| Question | Where |
|---|---|
| Who could supply each of the 41 parts, and who owns them? | Supplier Registry (`src/registry.js`) |
| I need these parts. Who should I ask first? | RFQ & Matching (`src/rfq.js`) |
| Where is Canada exposed? | Control Tower (`web/`) |
| Which gaps are investable projects? | Gap & Investment Finder (`src/gaps.js`) |

## What this module will not do

- **No technical data.** Turbopumps are on Canada's Export Control List (item 6-3). The module holds part categories, companies and sources only. RFQs that contain drawings, tolerances, speeds or test data are refused.
- **No scores in the open tier.** Chokepoint scores, lead times, critical path and stress scenarios come from a private assessment engine that plugs in through `src/engine.js` at deploy time. It is never stored here.
- **No proprietary SDKs.** Third-party platform SDKs are not redistributed here: one adapter is an out-of-repo plugin slot (its SDK licence bars redistribution) and another is an import/export mapping only. `scripts/check-interop-guard.mjs` fails CI if either SDK appears.

## Ranking rule (RFQ)

Transparent and repeatable, so a supplier can see why they ranked where they did:

1. Meets the buyer's sovereignty rule (any / Canadian presence / Canadian-owned)
2. Ownership: Canadian-owned, then Canadian plant of a foreign parent, then foreign
3. Evidence grade: confirmed, then reported
4. Source citability: primary, named analyst, secondary

Ownership is recorded separately from location: a foreign-owned plant in Canada is not Canadian-owned.

## Run it

```bash
cd modules/turbopump-marketplace
node --test test/*.test.js        # 11 tests
node web/build.mjs                # builds web/dist/index.html, open it in a browser
node ../../scripts/check-interop-guard.mjs
```

No dependencies. Node 20 or later.

## Layout

```
data/          parts.json (41), entities.json (28), every entity cites https sources or carries a source_note pointer
src/           registry, rfq, gaps, engine port, labels, interop
api/           openapi.yaml: the contract for the hosted API (lint-clean)
web/           Dashboard template and build script
test/          node:test suite
```

## Handling

Every object leaves the module wrapped in a handling label (`src/labels.js`) using STANAG 4774 concepts. The open tier can only emit `UNCLASSIFIED // PUBLIC`; anything higher throws.

Licence: Apache-2.0.
