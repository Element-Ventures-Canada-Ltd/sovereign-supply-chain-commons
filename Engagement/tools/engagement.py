#!/usr/bin/env python3
# Handling: Unclassified — working
"""Engagement workflow engine — validate, track and report on an engagement.

Client-agnostic. An engagement is described in one YAML file (see
Engagement/schema/engagement.schema.md and Engagement/examples/). The engine
never stores commercial terms: `validate` fails if fee or currency amounts
appear in the file.

Usage:
    python3 engagement.py validate <engagement.yaml>
    python3 engagement.py status   <engagement.yaml> [--today YYYY-MM-DD]
    python3 engagement.py report   <engagement.yaml> [--today YYYY-MM-DD]
    python3 engagement.py due      <engagement.yaml> [--today YYYY-MM-DD]
        (exit 0 if a progress report is due today, 1 otherwise)

Requires PyYAML.
"""
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

DELIVERABLE_STATES = ["not_started", "in_progress", "in_review", "submitted", "accepted"]
SOLICITATION_STAGES = ["intake", "compliance", "drafting", "review", "submitted", "awarded", "declined"]
OPEN_ITEM_STATES = ["open", "decided", "closed"]
# Commercial-terms guard: no currency amounts or fee language in engagement files.
COMMERCIAL_RE = re.compile(
    r"(\$\s?\d|\b(CAD|USD|EUR|GBP)\s?\$?\s?\d|\d[\d,]*\s?(CAD|USD|EUR|GBP)\b|\bfee\b|\bpayment\b|\binvoice)",
    re.IGNORECASE,
)


def load(path):
    text = Path(path).read_text(encoding="utf-8")
    return text, yaml.safe_load(text)["engagement"]


def as_date(v):
    if v is None or isinstance(v, dt.date):
        return v
    return dt.date.fromisoformat(str(v))


def validate(path):
    errors, warnings = [], []
    text, e = load(path)

    for key in ["id", "title", "handling", "roles", "term", "reporting", "deliverables", "gates", "acceptance", "productization"]:
        if key not in e:
            errors.append(f"missing required key '{key}'")
    if errors:
        return errors, warnings

    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        if COMMERCIAL_RE.search(line):
            errors.append(f"line {n}: commercial term or currency amount — keep commercials out of the repo")

    d_ids = [d["id"] for d in e["deliverables"]]
    if len(set(d_ids)) != len(d_ids):
        errors.append("duplicate deliverable id")
    for d in e["deliverables"]:
        if d.get("status", "not_started") not in DELIVERABLE_STATES:
            errors.append(f"{d['id']}: status must be one of {DELIVERABLE_STATES}")
        if not d.get("evidence"):
            errors.append(f"{d['id']}: no acceptance evidence listed")

    gated = set()
    for g in e["gates"]:
        for did in g.get("deliverables", []):
            if did not in d_ids:
                errors.append(f"gate {g['id']}: unknown deliverable '{did}'")
            gated.add(did)
        try:
            gd = as_date(g.get("date"))
        except ValueError:
            errors.append(f"gate {g['id']}: invalid date")
            continue
        if gd and gd.weekday() >= 5:
            warnings.append(f"gate {g['id']} falls on a {gd.strftime('%A')} — confirm the working-day submission date")
        if gd is None:
            warnings.append(f"gate {g['id']}: date not set")
    for d in e["deliverables"]:
        if d["id"] not in gated and not d.get("continuous"):
            warnings.append(f"deliverable {d['id']} is not attached to any gate")

    for p in e.get("phases", []):
        if p.get("deliverable") and p["deliverable"] not in d_ids:
            errors.append(f"phase {p['id']}: unknown deliverable '{p['deliverable']}'")

    for a in e["acceptance"]:
        if not a.get("evidence"):
            errors.append(f"acceptance '{a['id']}': evidence missing")
        m = a.get("metric")
        if m and m not in e.get("metrics", {}):
            errors.append(f"acceptance '{a['id']}': metric '{m}' not tracked under metrics")

    rep = e["reporting"]
    if not rep.get("cadence_days") or not rep.get("anchor"):
        errors.append("reporting: cadence_days and anchor are required")

    sol = e.get("solicitation")
    if sol and sol.get("stage") not in SOLICITATION_STAGES:
        errors.append(f"solicitation.stage must be one of {SOLICITATION_STAGES}")

    prod = e["productization"]
    if not prod.get("target"):
        errors.append("productization.target missing — every services engagement names its product conversion")
    if not prod.get("conversion_date"):
        warnings.append("productization.conversion_date not set — record it as an open item with an owner")

    for oi in e.get("open_items", []):
        if not oi.get("owner"):
            errors.append(f"open item '{oi.get('id')}': owner missing")
        if oi.get("status", "open") not in OPEN_ITEM_STATES:
            errors.append(f"open item '{oi.get('id')}': bad status")

    if not as_date(e["term"].get("start")):
        warnings.append("term.start (effective date) not set")
    return errors, warnings


def report_due(e, today):
    rep = e["reporting"]
    anchor = as_date(rep["anchor"])
    if today < anchor:
        return False
    end = as_date(e["term"].get("end"))
    if end and today > end:
        return False
    return (today - anchor).days % int(rep["cadence_days"]) == 0


def next_report(e, today):
    rep = e["reporting"]
    anchor, step = as_date(rep["anchor"]), int(rep["cadence_days"])
    if today <= anchor:
        return anchor
    k = -(-(today - anchor).days // step)
    return anchor + dt.timedelta(days=k * step)


def gate_rows(e, today):
    by_id = {d["id"]: d for d in e["deliverables"]}
    rows = []
    for g in e["gates"]:
        gd = as_date(g.get("date"))
        days = (gd - today).days if gd else None
        ds = [by_id[x] for x in g.get("deliverables", []) if x in by_id]
        done = all(d.get("status") == "accepted" for d in ds) if ds else False
        if done:
            flag = "met"
        elif days is None:
            flag = "date not set"
        elif days < 0:
            flag = "OVERDUE"
        elif days <= 14:
            flag = "due within 14 days"
        else:
            flag = "on track"
        rows.append((g, gd, days, ds, flag))
    return rows


def metric_rows(e):
    out = []
    metrics = e.get("metrics", {})
    for a in e["acceptance"]:
        m = a.get("metric")
        if m:
            cur, thr = metrics.get(m, 0), a.get("threshold")
            state = "TBD" if thr is None else ("met" if cur >= thr else f"{cur}/{thr}")
            out.append((a, cur, thr, state))
        else:
            out.append((a, None, None, "qualitative"))
    return out


def render_status(e, today):
    lines = [f"{e['id']} — {e['title']}  (as of {today.isoformat()})", ""]
    for g, gd, days, ds, flag in gate_rows(e, today):
        when = gd.isoformat() if gd else "unset"
        dleft = "" if days is None else f" ({days:+d} d)"
        lines.append(f"[{flag}] {g['id']} {g['name']} — {when}{dleft}")
        for d in ds:
            lines.append(f"    {d['id']} {d['title']}: {d.get('status', 'not_started')}")
    lines += ["", "Acceptance:"]
    for a, cur, thr, state in metric_rows(e):
        lines.append(f"    {a['id']}: {state}")
    open_items = [o for o in e.get("open_items", []) if o.get("status", "open") == "open"]
    lines += ["", f"Open items: {len(open_items)}", f"Next progress report: {next_report(e, today).isoformat()}"]
    return "\n".join(lines)


def render_report(e, today):
    period_start = today - dt.timedelta(days=int(e["reporting"]["cadence_days"]))
    out = [
        f"<!-- Handling: {e['handling']} -->",
        f"# Progress report — {e['id']}",
        "",
        f"**Engagement:** {e['title']}  ",
        f"**Period:** {period_start.isoformat()} to {today.isoformat()}  ",
        f"**Prepared by:** {e['roles']['delivery_lead']['label']}",
        "",
        "## Gates",
        "",
        "| Gate | Date | Days to go | Deliverables | State |",
        "|---|---|---|---|---|",
    ]
    for g, gd, days, ds, flag in gate_rows(e, today):
        out.append(f"| {g['id']} {g['name']} | {gd.isoformat() if gd else 'unset'} | "
                   f"{'' if days is None else days} | {', '.join(d['id'] for d in ds)} | {flag} |")
    out += ["", "## Deliverables", "", "| ID | Deliverable | Status |", "|---|---|---|"]
    for d in e["deliverables"]:
        out.append(f"| {d['id']} | {d['title']} | {d.get('status', 'not_started')} |")
    out += ["", "## Acceptance criteria", "", "| Criterion | Standard | Progress |", "|---|---|---|"]
    for a, cur, thr, state in metric_rows(e):
        out.append(f"| {a['name']} | {a['standard']} | {state} |")
    phases = [p for p in e.get("phases", []) if p.get("status") in ("in_progress", "complete")]
    if phases:
        out += ["", "## Method steps active or complete", ""]
        out += [f"- {p['id']} {p['name']} — {p['status']}" for p in phases]
    out += ["", "## Open items", "", "| ID | Item | Owner | Status |", "|---|---|---|---|"]
    for o in e.get("open_items", []):
        out.append(f"| {o['id']} | {o['question']} | {o['owner']} | {o.get('status', 'open')} |")
    out += [
        "",
        "## This period / next period",
        "",
        "_Complete before sending: work done, work planned, risks, decisions needed._",
        "",
        f"Next report: {next_report(e, today + dt.timedelta(days=1)).isoformat()}",
    ]
    return "\n".join(out) + "\n"


def main(argv):
    if len(argv) < 3 or argv[1] not in ("validate", "status", "report", "due"):
        print(__doc__)
        return 2
    cmd, path = argv[1], argv[2]
    today = dt.date.today()
    if "--today" in argv:
        today = dt.date.fromisoformat(argv[argv.index("--today") + 1])
    if cmd == "validate":
        errors, warnings = validate(path)
        for w in warnings:
            print(f"WARN  {w}")
        for x in errors:
            print(f"ERROR {x}")
        print("OK" if not errors else "FAIL", path)
        return 1 if errors else 0
    _, e = load(path)
    if cmd == "status":
        print(render_status(e, today))
        return 0
    if cmd == "report":
        sys.stdout.write(render_report(e, today))
        return 0
    return 0 if report_due(e, today) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
