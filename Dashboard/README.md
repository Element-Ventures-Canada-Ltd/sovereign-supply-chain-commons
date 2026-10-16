Handling: Unclassified — working

# Dashboard

The query and visualization layer for capability-gap and dependency
analysis — the interface analysts and decision-makers use to explore a
supply-chain registry. The registry, ontology and decision engine are
maintained in a separate private repository and are not part of this one.

## What works today (preview)

`build.py` turns one OpenChokepoint instance file into a single, self-contained HTML page:

| Section | Question it answers |
| :-- | :-- |
| Summary tiles | How many records, organizations and controlling jurisdictions; how many organizations are controlled from outside where they are incorporated; how many steps lack evidence |
| Jurisdiction of control | Where is each organization controlled from (control, not residency)? |
| Capabilities | Who does the file list against each capability, controlled from where, and which programmes require it? Filterable |
| Digital threads | For each physical piece: design, material lot, steps, and whether an evidence record exists for each |
| Evidence gaps | Which steps have no evidence record |
| Declared critical items | Judgments declared on synthetic records only |

The Dashboard holds no data of its own. It reads files only through the
[OpenChokepoint](https://github.com/Element-Ventures-Canada-Ltd/openchokepoint) Python SDK,
pinned to the commit in [`openchokepoint.pin`](openchokepoint.pin).

## Run it

```bash
pip install pyyaml
git clone https://github.com/Element-Ventures-Canada-Ltd/openchokepoint ../openchokepoint
git -C ../openchokepoint checkout "$(sed -n 's/^commit: *//p' Dashboard/openchokepoint.pin)"
python3 Dashboard/build.py ../openchokepoint/examples/synthetic-turbopump-thread.yaml --out dashboard.html
```

Open `dashboard.html` in a browser. Tests: `python3 -m unittest discover -s Dashboard/tests -v`.

## Guardrails

- **Fails closed.** A file that does not pass the OpenChokepoint validator produces no page.
- **Pinned.** The build refuses any OpenChokepoint commit other than the pinned one, so every
  page can be reproduced. Upgrading the pin is a reviewed pull request.
- **Facts, not assessments.** Counts and lists what the file states. Never scores, ranks or
  labels a real organization or part.
- **No inferred order.** Steps are numbered only when the file states their order.
- **Safe output.** Every value from the data is HTML-escaped (tested with injected markup),
  and the page's content security policy blocks all external loads.

## CI

`.github/workflows/dashboard-ci.yml` runs the tests against the pinned SDK on every pull
request that touches `Dashboard/`, and attaches sample pages to the run.

## Scope

- Query interface over the registry (filtering, search, graph traversal)
- Visualizations for dependency concentration, capability gaps, and
  workforce/capacity constraints
- Export and reporting views

## Contributing

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) and [`HANDLING.md`](../HANDLING.md).
Screenshots or sample views used in documentation must use synthetic data only.
