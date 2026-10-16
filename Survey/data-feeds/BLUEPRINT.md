Handling: Unclassified — working

# SOI Graph Data Feed Blueprint — Turbopump Supply Chain (Survey Wave 1)

**Status:** v0.1 draft, 8 October 2026. **Priority:** high. **Owner:** repository maintainer (see MAINTAINERS.md).
**Audience:** engineers and contributors who will build the data connectors behind the Sovereign Supply Chain Survey.

This document tells an engineer what to build: which public data feeds to connect, what each one is allowed to be used for, what it must output, and in what order. It covers federal contract histories, supplier and ownership hierarchies, patent filings, venture funding rounds, trade and shipping records, plus sanctions, export-control, certification and registry feeds.

It is open-tier material. Commercial terms, survey validation logic, screening heuristics and the red-team assessment are held privately (see **Restricted companion material** at the end).

---

## 1. Bottom line

1. **Build on a free, redistributable spine of government primary records.** About 20 feeds (sanctions and export lists, GLEIF, USAspending, Canadian proactive disclosure, corporate and beneficial-ownership registries, USPTO patent data) are public domain or openly licensed and can live in this repository.
2. **No feed, free or paid, shows who supplies turbopump parts below tier 1.** The survey is the only source of those supplier relationships. The graph's job is to pre-fill the survey and to cross-check what respondents say against independent records.
3. **Licensing decides placement, not convenience.** Every connector declares its licence and tier in a manifest. Data that cannot be redistributed never enters this repository.
4. **Use FollowTheMoney (FtM) as the core model.** It is the native schema of OpenSanctions, yente and nomenklatura, so sanctions and investigations developers already know it. Export ownership as BODS 0.4 and contracts as OCDS.
5. **Mapping only.** Connectors collect who supplies what, ownership, awards and listings. They never collect design, manufacturing, test or performance information (see CONTRIBUTION-SCOPE.md once merged, and DATA-CONTRIBUTIONS.md).

---

## 2. Scope

| Dimension | Setting |
| :-- | :-- |
| Geography | Five Eyes (Canada, US, UK, Australia, New Zealand) plus EU and ESA member states |
| Adversarial-origin screening | China, Russia, Iran, North Korea, Belarus (configurable list) — ownership, control and influence exposure in the sub-tier |
| First component | Liquid rocket engine turbopump and its supply categories: inducer, impeller, turbine, shaft, bearings, seals, housing, gas generator or preburner, valves, plus materials (nickel superalloys, titanium, bearing steels, ceramic rolling elements, additive-manufacturing powders) |
| Survey role | Pre-population (who to invite, known facts pre-filled) and validation (independent cross-check) |

---

## 3. Placement tiers

| Tier | Meaning | Where it lives |
| :-- | :-- | :-- |
| **OPEN** | Licence permits redistribution (public domain, CC0, CC BY, OGL-Canada, OGL v3) | This repository: connector code, and derived data where the licence allows |
| **META** | Source can be checked but not bulk-redistributed | Only an identifier and a "verified yes/no, date" flag are published; content stays with the source |
| **LICENSED** | Commercial or non-commercial licence prohibits redistribution | Not in this repository. Connector interfaces may be stubbed here; data and credentials never are |

Two popular "open" sources are **not** OPEN for this project:

- **OpenSanctions data** is CC BY-NC 4.0, and OpenSanctions states that compliance and supplier screening is commercial use. The software (yente, nomenklatura, followthemoney) is MIT and free to use; the data needs a licence.
- **OpenCorporates** free API keys carry ODbL share-alike terms and are for "Permitted Users". Store only OpenCorporates IDs here; GLEIF publishes an OpenCorporates-ID to LEI mapping under CC0.

---

## 4. Feed catalogue

Survey role: **PRE** = pre-population, **VAL** = validation.

### 4.1 Open-tier feeds (build first)

| # | Feed | Category | Licence | Tier | Role | Populates |
|---|---|---|---|---|---|---|
| 1 | Trade.gov Consolidated Screening List (CSL) | Export control, sanctions | US public domain | OPEN | VAL | Company, Person, Sanction; LISTED_ON |
| 2 | OFAC SDN and Non-SDN lists | Sanctions | US public domain | OPEN | VAL | Company, Person, Vessel, Sanction; LISTED_ON, OWNS |
| 3 | Canada Consolidated Autonomous Sanctions List (SEMA, JVCFOA) | Sanctions | OGL-Canada (verify page terms) | OPEN | VAL | Sanction; LISTED_ON |
| 4 | UK Sanctions List (FCDO) | Sanctions | OGL v3 | OPEN | VAL | Sanction; LISTED_ON |
| 5 | EU Financial Sanctions Files | Sanctions | EU reuse (verify token terms) | OPEN | VAL | Sanction; LISTED_ON |
| 6 | Australia DFAT Consolidated List; NZ Russia Sanctions Register | Sanctions | CC BY / NZ Crown (verify) | OPEN | VAL | Sanction; LISTED_ON |
| 7 | US DoD Section 1260H list; FCC Covered List | Adversarial-origin lists | US public domain | OPEN | VAL | Sanction (listing); LISTED_ON |
| 8 | GLEIF Golden Copy Level 1 + Level 2 + mapping files | Ownership, identifiers | CC0 | OPEN | PRE + VAL | Company (LEI); SUBSIDIARY_OF; reporting exceptions |
| 9 | Corporations Canada, incl. individuals with significant control (ISC) | Registry, beneficial ownership | OGL-Canada for bulk (verify) | OPEN (company) / LICENSED (person) | PRE + VAL | Company; OWNS, CONTROLS, DIRECTOR_OF |
| 10 | UK Companies House (snapshot, API, PSC) | Registry, beneficial ownership | OGL v3 | OPEN (company) / LICENSED (person) | PRE + VAL | Company; OWNS, CONTROLS, DIRECTOR_OF |
| 11 | SEC EDGAR (10-K Exhibit 21, Form D) | Registry, funding | US public domain | OPEN | PRE + VAL | Company (CIK), FundingRound; SUBSIDIARY_OF, RAISED |
| 12 | USAspending.gov (prime awards and FFATA sub-awards) | US contracts, grants | US public domain | OPEN | PRE + VAL | Contract, Grant; AWARDED, SUBAWARDED_TO |
| 13 | SAM.gov Contract Awards API (FPDS successor) + Entity extract | US contracts, registry | US government data; check SAM terms for entity extract | OPEN (public fields) | PRE + VAL | Contract, Company (UEI, CAGE); AWARDED, LOCATED_IN |
| 14 | SBIR.gov awards | US R&D grants | US public domain | OPEN | PRE | Grant; AWARDED |
| 15 | Canada Proactive Disclosure — Contracts over $10,000 | Canadian contracts | OGL-Canada | OPEN | PRE + VAL | Contract; AWARDED |
| 16 | Canada Proactive Disclosure — Grants and Contributions | Canadian grants | OGL-Canada | OPEN | PRE + VAL | Grant; FUNDED_BY |
| 17 | CanadaBuys contract history and tender notices | Canadian procurement | OGL-Canada (verify) | OPEN | PRE | Contract; AWARDED |
| 18 | EU CORDIS (Horizon) and TED tenders | EU grants, contracts | EU reuse / CC BY 4.0 (verify per dataset) | OPEN | PRE | Grant, Contract; FUNDED_BY, AWARDED |
| 19 | UK Find a Tender / Contracts Finder (OCDS) | UK contracts | OGL v3 | OPEN | PRE | Contract; AWARDED |
| 20 | USPTO Open Data Portal (PatentsView disambiguated tables) | Patents | US public domain | OPEN | PRE + VAL | Patent; ASSIGNED_PATENT, CITES |
| 21 | OpenAlex | Scholarly literature | CC0 | OPEN | PRE | Publication, Organization (ROR); AFFILIATED_WITH |
| 22 | Statistics Canada CIMT; US Census USA Trade | Trade flows (aggregate) | OGL-Canada / US public domain | OPEN | VAL (macro) | TradeFlow by jurisdiction |
| 23 | USGS Mineral Commodity Summaries; NRCan Critical Minerals List; EU CRM list | Materials | US PD / OGL-Canada / EU reuse | OPEN | PRE (context) | Material; PRODUCED_IN |
| 24 | GCAT launch and engine catalogue (J. McDowell) | Space-specific | CC BY (verify) | OPEN | PRE | Product (engine), Company; USES_ENGINE |

### 4.2 META feeds (verify, do not copy)

| Feed | What is published here |
| :-- | :-- |
| Controlled Goods Program registrant directory (PSPC) | Registration flag and check date. Registrants may opt out of the public directory, so absence is not evidence of non-registration |
| IAQG OASIS (AS9100 family) | Certificate flag, scheme and expiry |
| PRI eAuditNet (Nadcap) | Special-process accreditation flag and expiry |
| NATO NCAGE | NCAGE code |
| EPO OPS / Espacenet | Patent family identifiers only (adds CNIPA filings) |

### 4.3 Licensed layer (not in this repository)

Categories only. Vendor selection and terms are held privately.

| Category | Why it is needed | Examples of source type |
| :-- | :-- | :-- |
| Deep ownership resolution in China and Russia | Public registries in those jurisdictions are not available as open bulk data | Commercial ownership-graph providers |
| Consolidated sanctions and PEP data | Lawful commercial use of curated cross-list linkage | OpenSanctions data licence |
| US bills of lading | Materials-tier shipment evidence | US import-record vendors |
| Global company registry lookups | EU and ESA states without free bulk registries | OpenCorporates paid tier |
| Venture funding rounds | Investor and round data beyond SEC Form D | Commercial funding databases |
| Global patent families | Search across jurisdictions | Lens.org commercial licence |

---

## 5. Source changes in 2026 (build against current endpoints)

| Source | Change | What to build against |
| :-- | :-- | :-- |
| FPDS.gov | Decommissioned 24 February 2026; ATOM feed retiring during FY2026 | SAM.gov Contract Awards API (login and API key); USAspending.gov for keyless access |
| eSRS (subcontract reports) | Retired 20 February 2026 | USAspending FFATA sub-award data |
| PatentsView | Moved to the USPTO Open Data Portal on 20 March 2026; PatentSearch API paused; sign-in required since 18 June 2026 | ODP bulk tables with a USPTO.gov account |
| UK OFSI Consolidated List | Closed 28 January 2026 | FCDO UK Sanctions List; key changes from OFSI Group ID to "Unique ID" |
| BIS Affiliates Rule (50% ownership) | Issued 29 September 2025, suspended 10 November 2025. Resumption reported as expected 10 January 2027 (Miller Canfield, 1 October 2026); no Federal Register notice yet | Implement as a toggle in the ownership calculator |

---

## 6. Turbopump code crosswalk (for filters, not for technical data)

| Code system | Codes | Note |
| :-- | :-- | :-- |
| CPC (patents) | F02K 9/46 (propellant feed by pumps, including turbopumps); F02K 9/48 (pumps driven by a gas turbine fed by propellant combustion gases); F02K 9/563 (feed-pump control); F04D 1/, F04D 29/ (impellers, inducers); F01D (turbines); F16C (bearings); F16J 15 (seals); B22F 10 and B33Y (additive manufacturing) | Primary filter for turbopump IP holders |
| NAICS | 336415, 336419, 333914, 333611 | Supplier-base filter for contracts and registries |
| PSC (US contracts) | 2845, 2840, 4320, 1810/1820, AR-series R&D (verify) | US award filter |
| HS (trade) | 8413.70/.81/.91, 8412.10/.90, 8411.99, 8482, 8484, 7502, 7504, 7505, 7506, 8108, 8802.60/8803 | Aggregate trade only; no HS code isolates turbopumps |

A reviewed crosswalk table with sources is a good first issue (section 11).

---

## 7. Connector output contract

Every connector emits FtM entities. Supply-chain concepts FtM does not cover use a small open `soi:` extension.

**Entity vocabulary**

- FtM: Company, Organization, Person, Contract, ContractAward, Patent, Sanction, Ownership, Directorship
- `soi:` extension: Facility, Component, Material, Certification, FundingRound, Shipment, TradeFlow, Jurisdiction

**Relationship vocabulary**

SUPPLIES, OWNS, CONTROLS, SUBSIDIARY_OF, DIRECTOR_OF, AWARDED, SUBAWARDED_TO, FUNDED_BY, INVESTED_IN, ASSIGNED_PATENT, CITES, SHIPPED_TO, SHIPPED_FROM, LOCATED_IN, LISTED_ON, CERTIFIED_BY.

SUPPLIES relationships come from the survey, not from connectors, and are never published at entity level in this repository.

**Mandatory provenance fields on every record**

| Field | Example |
| :-- | :-- |
| `source_feed_id` | `gleif-l2` |
| `source_record_id` | Native record ID |
| `source_url` | Retrieval URL |
| `retrieved_at` / `source_published_at` | ISO 8601 |
| `licence_spdx` | `CC0-1.0`, `OGL-Canada-2.0`, `OGL-UK-3.0` |
| `tier_placement` | `OPEN`, `META` or `LICENSED` |
| `evidence_tier` | `P`, `AN`, `AS` or `S` (below) |
| `method` | `asserted`, `matched`, `inferred` or `attested` |
| `er_match_score` | Present when a record was linked probabilistically |
| `valid_from` / `valid_to` | Time bounds for ownership and listings |
| `content_hash` | Content-addressed hash for tamper evidence |

**Evidence tiers**

| Tier | Definition | Examples |
| :-- | :-- | :-- |
| P — Primary | Issued by the competent authority, or a lossless machine copy | Sanctions list entry; GLEIF relationship record; registry filing; award record; patent grant |
| AN — Named analyst | Curated by an identifiable analyst or vendor with a documented method | Named think-tank report; curated linkage |
| AS — Secondary | Press, aggregators, directories | Trade press on engine contracts |
| S — Speculative | Machine inference or hypothesis | HS-code inference of a component; probabilistic link |

Rules: two secondary sources never add up to primary; a survey answer is recorded as `attested`, and becomes validated only when an independent primary record corroborates it; a conflicting primary record is recorded as a contradiction for analyst review, never as a silent overwrite.

**Export formats:** FtM JSON lines (native), BODS 0.4 (ownership), OCDS (contracts and grants).

---

## 8. Entity resolution

1. **Hard-key joins first:** LEI to registry number (GLEIF); UEI to CAGE (SAM); CIK; OpenCorporates ID to LEI (GLEIF mapping); PatentsView `assignee_id`; ROR.
2. **Probabilistic matching second:** Splink (MIT) for batch linkage on name, address, postcode and jurisdiction; nomenklatura (MIT) for FtM-native deduplication with a human judgement log. Check any other tool's licence against Apache-2.0 before use.
3. **Name normalisation:** strip legal forms (Inc., Ltd., Ltée, GmbH, S.A., ООО, 有限公司); handle Pinyin and Wade-Giles, Cyrillic transliteration, and bilingual Canadian names.
4. **Safety:** auto-merge only with a shared hard key; every merge is reversible and logged; no external flag is raised on a probabilistic match without human review.

Ownership calculation implements the public rules: the OFAC 50% rule (aggregate direct and indirect ownership by blocked persons), the BIS Affiliates Rule as a toggle, and the Canadian and UK "owned, held or controlled" tests as separate CONTROLS edges.

---

## 9. How the feeds serve the survey

**Pre-population.** Build the wave-1 invitation frame from tier-1 Canadian launch and engine developers, then widen it through US sub-award data, Canadian contracts and grants, CPC F02K 9/46–48 patent assignees, Controlled Goods registrants with matching NAICS codes, and regional AS9100 and Nadcap holders. Pre-fill legal identifiers, parent company, published beneficial-ownership summary, certifications, public awards and patents; the respondent confirms or corrects (consistent with Survey/METHODOLOGY.md, section 4).

**Validation.** Respondent claims about foreign ownership, certifications, Controlled Goods registration, material sourcing, sub-supplier origin and in-house design are cross-checked against the feeds above. The specific rules and how contradictions are scored belong to the proprietary core.

**Known gaps the survey fills**

| Gap | Why no feed covers it |
| :-- | :-- |
| Tier-2+ machining, heat-treat, coating and inspection shops | Private, often provincially incorporated, no LEI, no federal contracts |
| Air and truck cross-border flows (Canada–US) | US air, rail and truck manifests are not public (19 CFR 103.31); US importers may also request vessel-manifest confidentiality |
| Canadian import manifests | Customs information protected under Customs Act s.107 |
| Controlled technical content | Legally restricted; the survey asks only whether controls exist, never for the data |
| Contracts withheld on national-security grounds | Exempt from proactive disclosure |
| Material lot provenance | No public mill-to-part linkage |
| Provincial beneficial ownership | The federal ISC register covers CBCA corporations only |

---

## 10. Legal guardrails for contributors

1. **Export control (ITAR, EAR, Canadian Controlled Goods Program):** no drawings, specifications, process parameters or performance data, even if you believe they are public. Connectors and schemas have no fields for them.
2. **Privacy (PIPEDA, GDPR, UK GDPR):** no Person records in this repository. Published views show counts and ownership bands only.
3. **Terms of service:** OASIS, eAuditNet, NCAGE, SEDAR+, ESA EMITS and Space-Track restrict automated harvesting. Do not write scrapers for them.
4. **Licence contamination:** CC BY-NC and ODbL share-alike data must never enter this repository's data. Code is Apache-2.0; each derived record keeps its upstream licence.
5. **Aggregation sensitivity:** individually public facts can combine into a list of single points of failure. Entity-level supplier links and sole-source flags are never published here; published cells follow the survey's disclosure-control rules (minimum five organizations).
6. **Credentials:** API keys go in environment variables or a secrets store, never in code or config (the data-handling guard checks for this).

---

## 11. Build plan

| Phase | Deliverables |
| :-- | :-- |
| 0 — Foundations | `soi:` extension schema, provenance fields, connector manifest format, licence-gate CI check, synthetic fixtures |
| 1 — Open MVP | Sanctions and export lists (CSL, OFAC, SEMA, UK, EU, 1260H); GLEIF L1/L2; Corporations Canada; Companies House; USAspending; Canadian contracts and grants; USPTO F02K 9/46–48 slice; entity resolution; first screening report |
| 2 — Survey-ready | SAM.gov Contract Awards API and entity extract; SBIR; CORDIS and TED; OpenAlex; SEC Exhibit 21 and Form D; META verification workflow (CGP, OASIS, Nadcap); pre-population export to the survey tooling |
| 3 — Licensed layer | Interfaces only in this repository; data and credentials held privately |
| 4 — Wave 1 | Survey cross-check pipeline and analyst queue (private); red-team challenge under RED-TEAM.md |
| 5 — Recurring | Delta ingestion each wave; BIS Affiliates Rule toggle; second component |

**Proposed layout**

```
Connectors/
  <feed_id>/
    manifest.yaml        # licence, tier, cadence, identifier keys (see connector-manifest.template.yaml)
    extract.py
    transform.py         # to FtM + provenance
    tests/
    provenance.yaml      # per DATA-CONTRIBUTIONS.md, if any data is committed
Schema/soi/              # FtM extension
Resolution/              # Splink and nomenklatura configuration
Screening/               # ownership calculator (public rules only)
Survey/data-feeds/       # this blueprint and the feed registry
```

**Good first issues** (to be opened under the bounty tiers once BOUNTIES.md is merged)

1. Connector: UK Sanctions List XML to FtM Sanction, mapping OFSI Group ID to Unique ID.
2. Connector: Canada SEMA consolidated XML to FtM, with a bilingual alias test.
3. Connector: Trade.gov CSL JSON, tagged by source list.
4. Connector: Canadian proactive-disclosure contracts CSV, with a vendor-name normaliser (Ltée, Ltd., Inc.).
5. Connector: GLEIF Level 2 relationships and reporting exceptions to SUBSIDIARY_OF plus exception flags.
6. Connector: USPTO ODP bulk tables filtered to CPC F02K 9/46, 9/48 and 9/563.
7. Connector: DoD 1260H list (PDF to structured), with a change-diff test.
8. Rule: aggregate indirect-ownership calculator with OFAC and BIS toggles and unit tests.
9. Tool: licence-gate CI check that fails a build if any LICENSED-tier field reaches an open export.
10. Docs: reviewed HS, CPC, NAICS and PSC crosswalk for turbopump supply categories, with sources.

---

## 12. Caveats

- Items marked "verify" rest on secondary sources or unconfirmed terms; confirm before building.
- The BIS Affiliates Rule date depends on a Federal Register notice not yet published.
- Export-control and privacy counsel should review connector scope before survey responses are ingested.

## 13. Key references

- 19 CFR 103.31, vessel manifest disclosure: https://www.law.cornell.edu/cfr/text/19/103.31
- SAM.gov, contract awards data move: https://sam.gov/announcements/contract-awards-data-and-searching-now-samgov
- USPTO, PatentsView migration to the Open Data Portal: https://www.uspto.gov/subscription-center/2026/patentsview-migrating-uspto-open-data-portal-march-20
- USPTO Open Data Portal, what's new: https://data.uspto.gov/support/whats-new
- UK Sanctions List: https://www.gov.uk/government/publications/the-uk-sanctions-list
- Trade.gov Consolidated Screening List: https://catalog.data.gov/dataset/consolidated-screening-list-api
- GLEIF Golden Copy: https://www.gleif.org/en/lei-data/gleif-golden-copy/download-the-golden-copy
- Open Ownership, GLEIF in BODS 0.4: https://bods-data.openownership.org/source/gleif_version_0_4/
- Controlled Goods Program directory: https://www.canada.ca/en/public-services-procurement/services/industrial-security/controlled-goods/find-individuals-organizations-registered-program.html
- Canada contracts over $10,000: https://open.canada.ca/data/en/dataset/d8f85d91-7dec-4fd1-8055-483b77225d8b
- Canada grants and contributions: https://open.canada.ca/data/en/dataset/432527ab-7aac-45b5-81d6-7597107a7013
- OpenSanctions, free and non-commercial use: https://www.opensanctions.org/docs/commercial/exemption/
- OpenCorporates API reference: https://api.opencorporates.com/documentation/API-Reference
- IAQG OASIS: https://www.p-r-i.org/certification/services/oasis
- CBCA individuals with significant control: https://www.mltaikins.com/insights/cbca-corporations-new-filing-requirements-on-individuals-with-significant-control/

---

## Restricted companion material (pointer only)

Per HANDLING.md, the following is referenced here and held outside this repository.

| Item | Description | Held by |
| :-- | :-- | :-- |
| Licensed-feed portfolio | Vendor selection, pricing evidence and budget for the licensed layer | Repository maintainer, Element Ventures project records |
| Survey validation rules | Cross-check rules, contradiction handling and anti-gaming controls | Proprietary core repository |
| Screening heuristics | Front-company and influence indicators beyond the public legal rules | Proprietary core repository |
| Red-team assessment | Known weaknesses and evasion paths for the feed portfolio | Repository maintainer, Element Ventures project records |
