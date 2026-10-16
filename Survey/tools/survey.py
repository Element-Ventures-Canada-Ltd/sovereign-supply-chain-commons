#!/usr/bin/env python3
# Handling: Unclassified — working
"""Survey item-bank tool — validate and render the public questionnaire.

The item bank (Survey/instrument/item-bank-*.yaml) is the single source of
truth. This tool checks it and renders the human-readable questionnaire.

Usage:
    python3 survey.py validate <item-bank.yaml>
    python3 survey.py render   <item-bank.yaml> [--out <file.md>]
    python3 survey.py paths    <item-bank.yaml>
        (item count per respondent segment; a burden check)

Private-scoring guard: `validate` fails if any item carries a weight,
threshold, multiplier or score field. Scoring lives in the proprietary core.

Requires PyYAML.
"""
import argparse
import sys
from pathlib import Path

import yaml

FORBIDDEN_KEYS = {"weight", "weights", "threshold", "thresholds", "multiplier", "score", "points", "rubric"}
REQUIRED_ITEM_KEYS = {"id", "text", "format", "segments", "feeds"}
MODULE_STATUSES = {"core-frozen", "rotating"}


def load(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def iter_items(bank):
    for module in bank["modules"]:
        for item in module["items"]:
            yield module, item


def validate(bank):
    errors = []
    if "Unclassified" not in str(bank.get("handling", "")):
        errors.append("missing handling marking")
    segments = set(bank["segments"]) | {"ALL"}
    feeds = set(bank["feeds"])
    formats = set(bank["formats"])
    retired = set(bank.get("retired_ids", []))
    seen = set()
    for module in bank["modules"]:
        if module.get("status") not in MODULE_STATUSES:
            errors.append(f"module {module.get('id')}: status must be one of {sorted(MODULE_STATUSES)}")
    for module, item in iter_items(bank):
        iid = item.get("id", "?")
        missing = REQUIRED_ITEM_KEYS - set(item)
        if missing:
            errors.append(f"{iid}: missing {sorted(missing)}")
        if iid in seen:
            errors.append(f"{iid}: duplicate id")
        if iid in retired:
            errors.append(f"{iid}: reuses a retired id")
        if not str(iid).startswith(module["id"]):
            errors.append(f"{iid}: id does not match module {module['id']}")
        seen.add(iid)
        if item.get("format") not in formats:
            errors.append(f"{iid}: unknown format {item.get('format')}")
        for s in item.get("segments", []):
            if s not in segments:
                errors.append(f"{iid}: unknown segment {s}")
        for f in item.get("feeds", []):
            if f not in feeds:
                errors.append(f"{iid}: unknown feed {f}")
        bad = FORBIDDEN_KEYS & {k.lower() for k in item}
        if bad:
            errors.append(f"{iid}: private scoring field(s) {sorted(bad)} must not appear in the public item bank")
        if item.get("format") in {"SC", "MC", "RK"} and not item.get("options"):
            errors.append(f"{iid}: choice item has no options")
    return errors


def applies(item, segment):
    segs = item["segments"]
    return "ALL" in segs or segment in segs


def render(bank):
    out = []
    out.append("Handling: Unclassified — working\n")
    out.append(f"# Sovereign Supply Chain Survey — questionnaire v{bank['version']}\n")
    out.append("*Generated from the item bank by `Survey/tools/survey.py render`. Do not edit by hand.*\n")
    out.append(f"Status: **{bank['status']}**. Rotating module topic: **{bank['rotating_module_topic']}**.\n")
    out.append("## Legend\n")
    out.append("| Code | Segment |\n|---|---|")
    for k, v in bank["segments"].items():
        out.append(f"| {k} | {v} |")
    out.append("\n| Code | Feeds |\n|---|---|")
    for k, v in bank["feeds"].items():
        out.append(f"| {k} | {v} |")
    out.append("\n| Code | Format |\n|---|---|")
    for k, v in bank["formats"].items():
        out.append(f"| {k} | {v} |")
    out.append("\n**Scored** marks items that also feed private scoring. Weights and rubric thresholds are not published.\n")
    out.append("**Evidence tier (asked after every M5 item):** " + "; ".join(f"{k} {v}" for k, v in bank["evidence_tiers"].items()) + ".\n")
    out.append("**Generic M5 anchors** (used where an item gives none): " + " ".join(f"{k} = {v}" for k, v in bank["generic_m5_anchors"].items()) + "\n")
    for module in bank["modules"]:
        out.append(f"## Module {module['id']}: {module['title']}\n")
        out.append(f"Status: {module['status']}. Estimated time: {module['est_minutes']} minutes.\n")
        out.append("| ID | Question | Format and responses | Segments | Feeds | Scored |\n|---|---|---|---|---|---|")
        for item in module["items"]:
            resp = item["format"]
            if item.get("options"):
                resp += ": " + "; ".join(str(o) for o in item["options"])
            if item.get("anchors"):
                resp += ". " + " ".join(f"{k} = {v}" for k, v in item["anchors"].items())
            if item["format"] == "M5":
                resp += " Plus evidence tier."
            if item.get("routing"):
                resp += f" *Routing: {item['routing']}*"
            resp = resp.replace("|", "/")
            scored = "Yes" if item.get("scored") else ""
            out.append(f"| {item['id']} | {item['text']} | {resp} | {', '.join(item['segments'])} | {', '.join(item['feeds']) or 'Gate'} | {scored} |")
        out.append("")
    return "\n".join(out) + "\n"


def paths(bank):
    lines = ["Segment  Items  M5-items"]
    for seg in bank["segments"]:
        items = [i for _, i in iter_items(bank) if applies(i, seg)]
        m5 = sum(1 for i in items if i["format"] == "M5")
        lines.append(f"{seg:<8} {len(items):>5}  {m5:>8}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["validate", "render", "paths"])
    ap.add_argument("bank")
    ap.add_argument("--out")
    args = ap.parse_args()
    bank = load(args.bank)
    errors = validate(bank)
    if errors:
        print("Item bank invalid:")
        for e in errors:
            print(f"  - {e}")
        return 1
    if args.command == "validate":
        n = sum(1 for _ in iter_items(bank))
        print(f"Item bank valid: {n} items, version {bank['version']}.")
    elif args.command == "render":
        text = render(bank)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
            print(f"Wrote {args.out}")
        else:
            print(text)
    else:
        print(paths(bank))
    return 0


if __name__ == "__main__":
    sys.exit(main())
