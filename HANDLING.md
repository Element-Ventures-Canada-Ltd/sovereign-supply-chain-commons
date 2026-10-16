Handling: Unclassified — working

# Handling Classification

This repository is hosted commercially and is not an accredited environment for classified or Protected-level material. The rules below govern everything committed here.

## Default rule

**Default classification: Unclassified — working.** Every file must carry a `Handling:` marking (in a header comment or front-matter) stating its classification. If a file has no marking, treat it as unreviewed and do not merge it.

## What belongs here

- Unclassified working content: schemas, ontologies, documentation, code, public-domain and openly licensed reference material, synthetic/example data.
- - **Pointer-only references** to sensitive material: a filename, a one-line description, and where the real content is held (e.g., an internal system, a named custodian) — never the sensitive content itself.
 
  - ## What never belongs here
 
  - - Protected-level or higher, or any raw classified material, regardless of source.
    - - Real entity-level registry data derived from non-public sources, unless it has been explicitly cleared for this repository by a maintainer.
      - - Third-party contract text, correspondence, or figures not already public.
        - - Credentials, API keys, tokens, or access details of any kind.
         
          - ## Marking convention
         
          - Place `Handling: Unclassified — working` at the top of every substantive file (markdown front-matter, a leading comment in code, or a dedicated field in structured data).
         
          - ## CI enforcement
         
          - The `data-handling-guard` check in CI (see .github/workflows/ci.yml) scans new and changed files for missing handling markers and for patterns associated with classified markings or credential leakage, and fails the build if either is found. This is a floor, not a substitute for reviewer judgment — maintainers should still read the diff.
         
          - ## Questions
         
          - If you are unsure whether something belongs in this repository, do not commit it — open an issue describing the material at a pointer level (never the content itself) and ask a maintainer.
          - 
