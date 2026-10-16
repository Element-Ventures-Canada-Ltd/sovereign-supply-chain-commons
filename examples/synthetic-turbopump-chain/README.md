Handling: Unclassified — working

# Synthetic sample: turbopump-class supply chain

A small, entirely fictional dataset showing the *shape* of a supply-chain mapping contribution. Every supplier, country, and relationship here is invented. Nothing in it is a finding about any real company, country, or program.

## What it contains

| File | Purpose |
| :-- | :-- |
| `entities.csv` | Suppliers, components, a material, services, and one assembly |
| `dependencies.csv` | Who supplies or performs what, and what feeds what |
| `provenance.yaml` | Provenance manifest required by DATA-CONTRIBUTIONS.md |
| `validate.py` | Checks that the files are internally consistent |

## Try it

```
python3 validate.py
```

You should see a line starting with `OK`. The script uses the Python standard library only.

## What is deliberately not here

- **No technical data.** Nothing about how any part is designed, made, or tested, and no performance figures. This repository accepts mapping only (see CONTRIBUTION-SCOPE.md). An automatic scope check flags engineering units and terms in data files on every pull request; a maintainer reviews anything it flags.
- **No scoring.** The sample shows raw mapping fields only (`single_source`, `known_alternates`). How chokepoints are scored is not part of the open tier.
- **No real data.** This sample is for learning the format and testing tools. Real supplier relationships go through the project's contribution process, not into this folder.

## Using it as a template

Copy the column layout when proposing real entries. Field names here are working names and may change as the open schema is finalized.
