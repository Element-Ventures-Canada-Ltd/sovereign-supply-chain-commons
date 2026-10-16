Handling: Unclassified — working

# Partner Platform Import Adapter: Specification (Draft v0.3)

**Repo:** sovereign-supply-chain-commons (open tier, Apache-2.0)
**Path:** `adapters/partner-platform/`
**Adapter slots used:** `data-platform-mapping` (in this repo, design-only) and `platform-plugin` (out of repo)
**Status:** Draft v0.3. v1 read-only scope approved; implementation on hold (see §10).
**Owner:** Maintainer (TLS)

---

## 1. Purpose

Some allied operators already run a third-party intelligence or data platform. This adapter lets them bring supply-chain data into the platform without replacing what they run. The platform stays the system of record, and a partner's platform becomes one optional source among many.

The adapter exists for data portability into the platform's own record of truth, not to extend any third-party platform.

**Design principle:** *coexist, don't depend.* The platform must build, test and run with the adapter removed.

## 2. Interop rule

Maintainer decision, 2026-10-14: **third-party platforms appear only as neutral adapter slots, with no runtime link and no product names.** In practice:

| Rule | What it means here |
|---|---|
| Neutral slot only | This repo holds a neutral import contract (schema, validator, mapping notes). It holds no code that talks to any third-party platform. |
| No runtime link | No third-party SDK, package, API client or network call to a partner platform, not even as a pinned dependency. |
| No product names | No vendor, product, package, module or endpoint names in code, docs, tests, commit messages or PR text. Partners are referred to as "the partner platform". |
| Connector lives out of repo | The code that reads from a specific partner platform is a `platform-plugin`: owned and run by the partner, or kept in a separate private repository. It is never vendored here. |

## 3. Best-practice check

| Practice | Source | How this spec applies it |
|---|---|---|
| Ports and adapters (dependency inversion) | Hexagonal architecture (Cockburn); dependency inversion principle | The platform defines the port, the import contract. Partner connectors implement it. The core never depends on a vendor. |
| Out-of-tree vendor integrations | Kubernetes moved cloud-provider code out of its core repository (KEP-2395); Terraform providers ship separately from Terraform | Vendor-specific code stays outside the open tier, so vendor API changes never break or block the platform. |
| Clean-room interoperability | Standard practice for independent implementations | Field names and the schema are our own and are defined without reference to vendor documentation. |
| Minimise supply-chain surface | NIST SSDF (SP 800-218); SLSA; NIST SP 800-161r1 | No third-party dependency for this integration means no transitive packages to pin, audit or patch in the open tier. |
| Least privilege | NIST SP 800-53 AC-6 | The connector holds read-only scopes for in-scope data only (§6). |
| Vendor-neutral wording | Trademark and endorsement risk | Factual compatibility naming may be lawful, but the stricter no-names rule removes any suggestion of endorsement or affiliation. |

**Trade-off accepted:** partners must build or run their own connector to the import contract. The open tier ships no turnkey connector.

## 4. Scope

The import contract accepts only the record kinds below. **Anything not listed as "in scope (v1)" is excluded by default**, including capabilities a partner platform adds later.

| Capability class | Status | Use |
|---|---|---|
| Position observations: latest and history | **Read: in scope (v1)** | Shipment and asset position observations for the supply-chain map |
| Map context layers, as KML/KMZ (open OGC standard) | **Read: in scope (v1)** | Map context for platform layers |
| Media attachments | Read: in scope (v1) | Inspection imagery and documents attached to supplier and asset records |
| Source catalogue listing | Read: in scope (v1) | Discovery and health check only |
| Map rendering | Out of scope | Rendering stays on the platform side |
| Any write back to a partner platform: creating, loading, linking, unlinking or annotating objects, tracks, layers, symbols or metadata | **Write: not planned** | None |
| Outbound messaging | **Excluded** | A side effect in a partner system that the platform should not trigger |
| Targeting functions | **Permanently excluded** | Military targeting is outside the platform's supply-chain mission. Never accepted, requested or called. |

**Enforcement (three layers).**

1. **Contract.** The import validator accepts only the in-scope record kinds and rejects everything else, with a test for each excluded class. The contract has no write-back path.
2. **Credentials.** The partner's connector credentials are never granted targeting or messaging scopes, and hold read-only scopes for in-scope data only (§6).
3. **Repository guard.** `scripts/check-interop-guard.mjs` fails CI on third-party SDK references. Vendor and product names are checked through the `GUARD_TERMS` secret, so the names are never written into the repo.

## 5. Architecture

```
Partner platform ──► partner connector (platform-plugin, OUT OF REPO, partner-owned)
                              │  writes neutral import bundles (schema: partner-import/1)
                              ▼
                     adapters/partner-platform/   (THIS REPO, data-platform-mapping slot)
                     ├── schema/       neutral import schema; field names are our own
                     ├── validate.py   accepts in-scope record kinds only
                     └── tests/        synthetic fixtures only; no network
                              │
                              ▼
               Platform canonical ingest API (public interface only)
```

- **No network path from the open tier to a partner platform.** Bundles arrive as files or through the public ingest API.
- **One-way boundary.** The adapter calls only the platform's *public* ingest interface. It never imports from the private core.
- **Feature flag.** `PARTNER_IMPORT_ENABLED` defaults to false. There is no write flag, because write paths are not planned.

## 6. Authentication and credentials

- **The open tier holds no partner credentials.** The partner provisions, owns and stores the credentials its connector uses.
- The connector uses service credentials (client credentials), never personal user tokens, in production.
- **The connector's credentials are never granted targeting or messaging scopes.** A deployment whose scope set includes either does not go live.
- The connector requests only the minimum read scopes for in-scope data, and the scope set is documented per deployment.

## 7. Security and classification

| Control | Requirement |
|---|---|
| Input handling | Bundles are untrusted input: schema-validated, size-limited, and escaped before any rendering. Links must be https. |
| Data marking | Every ingested record carries `source=partner:<partner-id>` plus the partner's security marking where present. Records without a marking default to the most restrictive local handling. |
| Enclave rule | No connector is deployed inside any high-side or air-gapped enclave. Inbound flow into such an enclave goes only through the one-way guard, as normalized platform records. |
| Audit | Every import is logged with partner, record count, bundle hash and correlation id (no payloads). |
| Failure mode | Fail closed: a bundle that fails validation is rejected whole, with no partial writes. |
| Content scope | Mapping only. Bundles carrying technical data on how a component is designed, made, tested or performs are rejected (see `CONTRIBUTION-SCOPE.md`). |

## 8. IP and licence obligations

- **No third-party code, documentation or identifiers** enter this repo. The schema is our own (clean-room).
- **No third-party SDK is used or distributed by the open tier**, so the patent-termination and notice duties that came with an installed SDK dependency (v0.2) no longer arise here. A partner's connector carries its own licence obligations, which the partner owns.
- **Access terms:** each partner's use of its own platform is governed by its own agreement with its vendor. **Before any deployment, the operator obtains the partner's written confirmation that its connector and the data flow comply with that agreement.** A note in this spec does not count as that confirmation.

## 9. Acceptance criteria (v1)

1. The platform's full test suite passes with `adapters/partner-platform/` deleted.
2. The validator accepts every in-scope record kind and rejects each excluded class, including targeting and messaging (tested with synthetic fixtures).
3. The adapter has no write-back path and makes no network calls (tested).
4. The interop guard passes, and no third-party SDK appears in any dependency file.
5. No vendor or product name appears anywhere in the repo (checked by the guard through `GUARD_TERMS`).
6. The deployment's documented connector scope set excludes targeting and messaging, and the partner's written compliance confirmation (§8) is on file before go-live.

## 10. Maintainer decisions

- [x] **2026-10-11: v1 read-only scope approved**, subject to an explicit list of excluded write capabilities and three-layer enforcement (§4).
- [x] **2026-10-11: v2 write paths not planned.** Deferred indefinitely and removed from the plan.
- [ ] **2026-10-11: implementation on hold** until a named partner and its credential scope set are confirmed. No implementation PR before then.
- [x] **2026-10-14: neutral slots only.** No runtime link and no product names (§2). This replaces the earlier dependency-pin question: the open tier takes no third-party dependency for this adapter.
