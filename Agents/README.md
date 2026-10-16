Handling: Unclassified — working

# SOI Graph Agents

Three SOI Graph Agents support the Sovereign Supply Chain Survey and the SOI Graph. They use plain, deterministic checks: no AI model, no API keys beyond the built-in GitHub token, no paid data.

| Agent | Job | Where it runs | What it may write |
| :-- | :-- | :-- | :-- |
| **Feed Agent** | Watches the public data feeds in `feed-watchlist.yaml`: still reachable, moved, licence or terms changed, new data published, new regulatory notices | This repository, GitHub Actions, Mondays and Thursdays | One rolling issue labelled `agent:feeds`; a comment only when something needs a maintainer |
| **Contribution Agent** | Screens every pull request, issue and comment against the repository rules | This repository, GitHub Actions, on each event | Labels and a job summary. Never comments, merges, closes or runs contributed code |
| **Supplier Agent** | Builds the survey's candidate frame from open feeds | Private core repository and a Canadian-hosted environment | Nothing in this repository |

## How the agents fit together

```
 public feeds ──► Feed Agent ──► rolling issue (is each feed healthy and still licensed?)
       │
       └──────► Supplier Agent (private) ──► registry database ──► survey invitation frame
                                                                   └► cross-checks (private)
 contributors ──► Contribution Agent ──► labels for maintainers ──► human review and merge
```

The Feed Agent keeps the connectors honest: if a source moves, goes down or changes its licence, a maintainer hears about it before bad data reaches the graph. The Contribution Agent protects the open tier from out-of-scope data, licence contamination and unsigned work. The Supplier Agent turns open records into the survey frame; its output is entity-level, so it never lands here.

## Feed Agent

| Check kind | What it observes | Alert when |
| :-- | :-- | :-- |
| `page` | Status, redirects, visible-text fingerprint, required phrases | Unreachable twice in a row; a required licence phrase disappears; page moves |
| `data` | HTTP headers only (status, Last-Modified, ETag). Never downloads the dataset | Unreachable twice in a row; new publication is reported as information |
| `ckan` | open.canada.ca catalogue record: licence id, last modified | Licence id differs from `expect_licence` or changes |
| `json` | API reachability | Unreachable twice in a row |
| `fedreg` | Newest Federal Register document for a query | A new document appears (used for the BIS Affiliates Rule) |

Run state is stored inside the rolling issue as a hidden, compressed block, so no files are committed and nothing is pushed to `main`.

**Add a feed:** append an entry to `feed-watchlist.yaml` using an ID from `Survey/data-feeds/feed-registry.yaml`. Set `verify: true` until a run confirms the URL.

## Contribution Agent

| Check | Applies label |
| :-- | :-- |
| Missing `Handling:` marker, classification-style marking, credential pattern, personal-information field names | `handling-review` |
| Engineering units or terms in data files (mapping-only rule) | `scope-review` |
| CLA box unchecked, missing DCO sign-off, external change to workflows or legal files, data without `provenance.yaml`, CC BY-NC or ODbL licence in data | `agent:review` |
| Short claim with no proposal (`/take`, "assign me") | `agent:claim-only` |
| Payment or bounty-amount request | `agent:payment-ask` |
| AI assistance or agent account disclosed | `ai-assisted` |

Maintainers (owner, members, collaborators) are exempt from the CLA, DCO and protected-path checks. Labels that do not exist in the repository are skipped, never created.

**Security:** the workflow uses `pull_request_target` but checks out only the base branch. Contributed files are read as text through the API and are never executed.

## Run locally

```bash
pip install pyyaml
python3 -m unittest discover -s Agents/tests -v      # tests
python3 Agents/soi_graph_agents.py feeds --dry-run              # check every feed now, no GitHub writes
python3 Agents/soi_graph_agents.py feeds --dry-run --state-file /tmp/agents-state.json   # compare with a previous run
```

## Supplier Agent (pointer only)

Held in the private core repository under `Registry/agents/`, run in a Canadian-hosted environment. Its database, candidate frame and screening rules are not published. See HANDLING.md.
