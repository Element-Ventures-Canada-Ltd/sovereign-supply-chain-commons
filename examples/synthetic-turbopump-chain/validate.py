#!/usr/bin/env python3
# Handling: Unclassified — working
"""Check the synthetic sample for internal consistency.

Usage: python3 validate.py
Standard library only. Exits non-zero if any check fails.
"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).parent
ENTITY_TYPES = {"assembly", "component", "material", "service", "supplier"}
RELATIONSHIPS = {"supplies", "performs", "input_to"}
SINGLE_SOURCE = {"true", "false", "n/a"}


def read(name):
    with (HERE / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    errors = []
    entities = read("entities.csv")
    deps = read("dependencies.csv")

    ids = [e["entity_id"] for e in entities]
    if len(ids) != len(set(ids)):
        errors.append("entities.csv: duplicate entity_id")
    for e in entities:
        if e["type"] not in ENTITY_TYPES:
            errors.append(f"entities.csv: {e['entity_id']} has unknown type {e['type']!r}")
        if e["fictional"] != "true":
            errors.append(f"entities.csv: {e['entity_id']} must be marked fictional=true")

    known = set(ids)
    for i, d in enumerate(deps, start=2):
        for end in ("from_id", "to_id"):
            if d[end] not in known:
                errors.append(f"dependencies.csv line {i}: unknown {end} {d[end]!r}")
        if d["relationship"] not in RELATIONSHIPS:
            errors.append(f"dependencies.csv line {i}: unknown relationship {d['relationship']!r}")
        if d["single_source"] not in SINGLE_SOURCE:
            errors.append(f"dependencies.csv line {i}: single_source must be true, false, or n/a")
        if not d["known_alternates"].isdigit():
            errors.append(f"dependencies.csv line {i}: known_alternates must be a whole number")

    if errors:
        print("Validation failed:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK: {len(entities)} entities, {len(deps)} dependencies.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
