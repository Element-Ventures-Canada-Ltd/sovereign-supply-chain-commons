#!/usr/bin/env python3
# Handling: Unclassified — working
# SPDX-License-Identifier: Apache-2.0
"""Build a static, self-contained HTML dashboard from an OpenChokepoint instance file.

The Dashboard reads data only through the OpenChokepoint Python SDK, pinned to the
commit in Dashboard/openchokepoint.pin. It holds no data of its own.

Usage:
    python3 Dashboard/build.py INSTANCE.yaml --openchokepoint PATH --out dashboard.html

    INSTANCE.yaml      an OpenChokepoint instance file (synthetic example or public registry)
    --openchokepoint   a checkout of the OpenChokepoint repository at the pinned commit
                       (default: $OPENCHOKEPOINT_ROOT, then ../openchokepoint next to this repo)
    --out              where to write the page (default: dashboard.html)
    --allow-unpinned   build against a different OpenChokepoint commit (local experiments only)

Guardrails (the page is a reading aid, not an assessment):
  - Fails closed: a file that does not pass the OpenChokepoint validator produces no page.
  - Facts only: counts and lists what the file states; never scores, ranks or labels a real
    organization or part. Critical-item judgments appear only as declared on synthetic records.
  - No inferred order: steps are numbered only when the file states their order.
  - Safe output: every value from the data is HTML-escaped; the page loads nothing external.
"""
import argparse
import base64
import hashlib
import html
import os
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIN_FILE = HERE / "openchokepoint.pin"
DELAY = {"d30_90": "30–90 days", "d90_180": "90–180 days", "d180_365": "180–365 days", "over_365": "over 365 days"}


class BuildError(Exception):
    """Raised when the dashboard cannot be built; the message says why and what to do."""


def read_pin(path=PIN_FILE):
    pin = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and ":" in line:
            key, value = line.split(":", 1)
            pin[key.strip()] = value.strip()
    if "commit" not in pin:
        raise BuildError(f"{path} has no commit line")
    return pin


def resolve_root(arg):
    candidates = [arg, os.environ.get("OPENCHOKEPOINT_ROOT"), HERE.parent.parent / "openchokepoint"]
    for c in candidates:
        if c and (Path(c) / "sdk" / "python" / "openchokepoint").is_dir():
            return Path(c).resolve()
    raise BuildError(
        "OpenChokepoint checkout not found. Clone it next to this repository:\n"
        "  git clone https://github.com/Element-Ventures-Canada-Ltd/openchokepoint ../openchokepoint\n"
        "  git -C ../openchokepoint checkout <commit from Dashboard/openchokepoint.pin>\n"
        "or pass --openchokepoint PATH."
    )


def check_pin(root, allow_unpinned):
    want = read_pin()["commit"]
    try:
        have = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                              capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        have = None
    if have == want:
        return have
    if allow_unpinned:
        return have or "unknown"
    raise BuildError(
        f"OpenChokepoint checkout is at {have or 'an unknown commit'}, but the Dashboard is pinned to {want}.\n"
        f"Run: git -C {root} checkout {want}   (or pass --allow-unpinned for a local experiment)"
    )


def load_sdk(root):
    sys.path.insert(0, str(root / "sdk" / "python"))
    import openchokepoint  # noqa: E402
    return openchokepoint


# ---------------------------------------------------------------- page pieces

def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def name_of(rec):
    if rec is None:
        return "<em>not stated</em>"
    return f'{esc(rec.name or rec.id)} <code>{esc(rec.id)}</code>'


def tile(label, value, note=""):
    return (f'<div class="tile"><div class="tile-value">{esc(value)}</div>'
            f'<div class="tile-label">{esc(label)}</div>'
            + (f'<div class="tile-note">{esc(note)}</div>' if note else "") + "</div>")


def section_jurisdiction(reg):
    entities = reg.of_type("Entity")
    if not entities:
        return ""
    counts = Counter(e.get("controlling_jurisdiction") for e in entities)
    top = max(counts.values())
    bars = "".join(
        f'<div class="bar-row"><span class="bar-label">{esc(j)}</span>'
        f'<span class="bar-track"><span class="bar" style="width:{100 * n / top:.1f}%"></span></span>'
        f'<span class="bar-value">{n}</span></div>'
        for j, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    )
    split = [e for e in entities if e.get("incorporation_jurisdiction") != e.get("controlling_jurisdiction")]
    if split:
        rows = "".join(
            f"<tr><td>{name_of(e)}</td><td>{esc(e.get('incorporation_jurisdiction'))}</td>"
            f"<td>{esc(e.get('controlling_jurisdiction'))}</td><td>{esc(e.get('evidence_grade'))}</td></tr>"
            for e in split
        )
        split_html = ("<h3>Incorporated in one jurisdiction, controlled from another</h3>"
                      '<div class="scroll"><table><thead><tr><th>Organization</th><th>Incorporated</th>'
                      f"<th>Controlled from</th><th>Evidence</th></tr></thead><tbody>{rows}</tbody></table></div>")
    else:
        split_html = "<p>No organization in this file is incorporated in one jurisdiction and controlled from another.</p>"
    return ('<section id="jurisdiction"><h2>Jurisdiction of control</h2>'
            "<p class=\"lede\">Where each organization is controlled from, as the file states it. Control, not residency.</p>"
            f'<div class="bars" role="list">{bars}</div>{split_html}</section>')


def control_label(rec):
    """Who controls a record: never a host location presented as control."""
    if rec.get("controlling_jurisdiction"):
        return rec["controlling_jurisdiction"]
    host = rec.get("host_jurisdiction")
    if host:
        return f"not stated (hosted in {host})"
    return "not stated"


def section_capabilities(reg):
    caps = reg.of_type("Capability")
    if not caps:
        return ""
    rows = []
    for c in caps:
        providers = reg.sources(c.id, "provides_capability")
        programmes = reg.sources(c.id, "requires_capability")
        juris = sorted({control_label(p) for p in providers})
        rows.append(
            f"<tr><td>{name_of(c)}</td><td>{len(providers)}</td>"
            f"<td>{'<br>'.join(name_of(p) for p in providers) or '<em>none listed</em>'}</td>"
            f"<td>{esc(', '.join(juris)) or '—'}</td>"
            f"<td>{'<br>'.join(name_of(p) for p in programmes) or '<em>none listed</em>'}</td></tr>"
        )
    return ('<section id="capabilities"><h2>Capabilities</h2>'
            '<p class="lede">Providers listed <strong>in this file</strong>. A count describes the file, not the market, '
            "and is not a judgment about any provider.</p>"
            '<label class="filter">Filter <input id="cap-filter" type="search" placeholder="capability, provider or jurisdiction"></label>'
            '<div class="scroll"><table id="cap-table"><thead><tr><th>Capability</th><th>Listed</th><th>Providers</th>'
            f"<th>Controlled from</th><th>Required by</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>")


def section_threads(reg):
    serials = reg.of_type("SerialItem")
    if not serials:
        return ""
    parts = []
    for s in serials:
        designs = reg.targets(s.id, "instance_of")
        lots = reg.targets(s.id, "made_from")
        lot_html = "; ".join(
            f"{name_of(l)} ({esc(l.get('material_class'))}) from "
            + (", ".join(name_of(p) for p in reg.targets(l.id, "produced_by")) or "<em>producer not stated</em>")
            for l in lots) or "<em>not stated</em>"
        steps, ordered = reg.steps_for(s.id)
        if steps:
            rows = []
            for seq, step in steps:
                where = ", ".join(name_of(f) for f in reg.targets(step.id, "performed_at")) or "<em>not stated</em>"
                ev = reg.evidence_for(step.id)
                ev_html = ("; ".join(f"{esc(e.get('record_kind'))} · {esc(e.get('issuer'))}" for e in ev)
                           if ev else '<span class="gap">missing</span>')
                rows.append(f"<tr><td>{esc(seq) if ordered else '–'}</td><td>{esc(step.get('step_kind'))}</td>"
                            f"<td>{where}</td><td>{ev_html}</td></tr>")
            order_note = "" if ordered else '<p class="note">Order not published: the file records that these steps happened, not their sequence.</p>'
            table = (f'{order_note}<div class="scroll"><table><thead><tr><th>#</th><th>Step</th><th>Where</th>'
                     f"<th>Evidence record</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>")
        else:
            table = "<p>No process steps recorded.</p>"
        design = ", ".join(f"{name_of(d)} rev {esc(d.get('revision'))}" for d in designs) or "<em>not stated</em>"
        parts.append(f'<div class="card"><h3>{name_of(s)}</h3><p>Design: {design}<br>Material lot: {lot_html}</p>{table}</div>')
    return ('<section id="threads"><h2>Digital threads</h2>'
            "<p class=\"lede\">Each physical piece, its design, its material, and the steps it went through. "
            "An evidence record shows that a record exists and where it sits; it is not proof the part was accepted.</p>"
            + "".join(parts) + "</section>")


def section_gaps(reg):
    if not reg.of_type("ProcessStep"):
        return ""
    gaps = reg.steps_without_evidence()
    if not gaps:
        body = "<p>Every recorded step has at least one evidence record.</p>"
    else:
        items = "".join(
            f"<li>{esc(g.get('step_kind'))} step <code>{esc(g.id)}</code> on "
            f"{', '.join(name_of(p) for p in reg.sources(g.id, 'underwent')) or '<em>no piece stated</em>'}</li>"
            for g in gaps)
        body = f"<p>A gap is shown, never filled: it tells a reader where to ask.</p><ul>{items}</ul>"
    return f'<section id="gaps"><h2>Evidence gaps</h2>{body}</section>'


def section_critical(reg):
    items = [c for c in reg.of_type("CriticalItem") if c.synthetic]
    if not items:
        return ""
    rows = []
    for c in items:
        alts = reg.sources(c.id, "alternate_for")
        alt = ("yes" if c.get("qualified_alternate") else "no") + (": " + ", ".join(name_of(a) for a in alts) if alts else "")
        rows.append(
            f"<tr><td>{name_of(c)}</td><td>{', '.join(name_of(t) for t in reg.targets(c.id, 'flags')) or '—'}</td>"
            f"<td>{esc(DELAY.get(c.get('delay_band'), c.get('delay_band')))}</td>"
            f"<td>{'yes' if c.get('single_source') else 'no'}</td><td>{alt}</td>"
            f"<td>{'yes' if c.get('missing_evidence') else 'no'}</td></tr>")
    return ('<section id="critical"><h2>Declared critical items <span class="badge">synthetic</span></h2>'
            "<p class=\"lede\">Judgments declared in the file: loss of the flagged item would delay a programme by more than "
            "30 days. The validator permits these on fictional records only.</p>"
            '<div class="scroll"><table><thead><tr><th>Item</th><th>Flags</th><th>Delay</th><th>Single source</th>'
            f"<th>Qualified alternate</th><th>Missing evidence</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>")


STYLE = """
:root{--bg:#f7f7f5;--surface:#fff;--ink:#1c1c1e;--muted:#5c5c66;--line:#e2e2e6;--accent:#1f5f8b;--accent-soft:#dbe8f2;--gap:#a33a1f;--gap-soft:#f6e1da}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#111214;--surface:#1b1c1f;--ink:#ececef;--muted:#a3a3ad;--line:#2d2e33;--accent:#7fb6dc;--accent-soft:#1f3443;--gap:#f0a58f;--gap-soft:#3d241c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:24px 16px 64px}header h1{font-size:1.6rem;margin:0 0 4px}
.meta{color:var(--muted);margin:0 0 16px}.disclaimer{border-left:3px solid var(--accent);background:var(--accent-soft);padding:10px 14px;border-radius:4px;margin:0 0 20px}
nav{display:flex;flex-wrap:wrap;gap:12px;margin:0 0 20px}nav a{color:var(--accent);text-decoration:none;font-weight:600}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:0 0 28px}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:14px}.tile-value{font-size:1.7rem;font-weight:700;font-variant-numeric:tabular-nums}
.tile-label{color:var(--muted);font-size:.85rem}.tile-note{color:var(--muted);font-size:.75rem;margin-top:4px}
section{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:18px 18px 8px;margin:0 0 20px}
h2{font-size:1.2rem;margin:0 0 6px}h3{font-size:1rem;margin:14px 0 8px}.lede,.note{color:var(--muted);margin:0 0 12px}
.bars{margin:0 0 12px}.bar-row{display:grid;grid-template-columns:4.5rem 1fr 2.5rem;gap:10px;align-items:center;margin:4px 0}
.bar-track{background:var(--line);border-radius:3px;height:12px;overflow:hidden}.bar{display:block;height:100%;background:var(--accent)}
.bar-label,.bar-value{font-variant-numeric:tabular-nums}.bar-value{text-align:right}
.scroll{overflow-x:auto;margin:0 0 12px}table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{text-align:left;vertical-align:top;padding:7px 8px;border-bottom:1px solid var(--line)}th{color:var(--muted);font-weight:600;white-space:nowrap}
code{font-size:.78rem;color:var(--muted)}.card{border-top:1px solid var(--line);padding-top:4px}
.gap{color:var(--gap);background:var(--gap-soft);padding:1px 6px;border-radius:3px;font-weight:600}
.badge{font-size:.7rem;font-weight:600;color:var(--accent);background:var(--accent-soft);padding:2px 7px;border-radius:10px;vertical-align:middle}
.filter{display:block;margin:0 0 10px;color:var(--muted);font-size:.85rem}.filter input{margin-left:8px;padding:6px 8px;border:1px solid var(--line);border-radius:4px;background:var(--bg);color:var(--ink);width:min(320px,70%)}
footer{color:var(--muted);font-size:.8rem;margin-top:28px}
"""

SCRIPT = """
(function(){var i=document.getElementById('cap-filter');if(!i)return;var rows=document.querySelectorAll('#cap-table tbody tr');
i.addEventListener('input',function(){var q=i.value.toLowerCase();rows.forEach(function(r){r.style.display=r.textContent.toLowerCase().indexOf(q)<0?'none':'';});});})();
"""
SCRIPT_HASH = "sha256-" + base64.b64encode(hashlib.sha256(SCRIPT.encode("utf-8")).digest()).decode("ascii")


def render(reg, source_name, pin_commit, today=None):
    entities = reg.of_type("Entity")
    real = len(reg.real_records())
    status = ("Synthetic: every record is fictional." if real == 0 else
              "Public record: real records drawn from cited public sources." if real == len(reg) else
              f"Mixed: {real} of {len(reg)} records are real.")
    split = sum(1 for e in entities if e.get("incorporation_jurisdiction") != e.get("controlling_jurisdiction"))
    tiles = [tile("Records", len(reg), f"{len(reg.objects)} objects · {len(reg.links)} links")]
    if entities:
        tiles += [tile("Organizations", len(entities)),
                  tile("Controlling jurisdictions", len({e.get('controlling_jurisdiction') for e in entities})),
                  tile("Controlled from elsewhere", split, "incorporated in one jurisdiction, controlled from another")]
    if reg.of_type("ProcessStep"):
        tiles.append(tile("Evidence gaps", len(reg.steps_without_evidence()), "steps with no evidence record"))
    sections = [section_jurisdiction(reg), section_capabilities(reg), section_threads(reg),
                section_gaps(reg), section_critical(reg)]
    titles = {"jurisdiction": "Jurisdiction", "capabilities": "Capabilities", "threads": "Digital threads",
              "gaps": "Evidence gaps", "critical": "Critical items"}
    nav = "".join(f'<a href="#{k}">{v}</a>' for k, v in titles.items() if f'id="{k}"' in "".join(sections))
    built = (today or date.today()).isoformat()
    return f"""<!doctype html>
<!-- Handling: Unclassified — working. Generated by Dashboard/build.py; do not edit by hand. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src '{SCRIPT_HASH}'">
<title>Supply-chain dashboard</title><style>{STYLE}</style></head>
<body><main>
<header><h1>Supply-chain dashboard</h1>
<p class="meta">Source: <code>{esc(source_name)}</code> · {esc(status)} · Validated · Built {esc(built)} · OpenChokepoint <code>{esc(pin_commit[:7])}</code></p>
<p class="disclaimer">This page lists what the file states. It does not score, rank or assess any organization or part.</p>
<nav>{nav}</nav></header>
<div class="tiles">{''.join(tiles)}</div>
{''.join(sections)}
<footer>Element Ventures (Canada) Ltd. · Built with the OpenChokepoint Python SDK · Code under Apache-2.0</footer>
</main><script>{SCRIPT}</script></body></html>
"""


def build(instance, root, out, allow_unpinned=False, today=None):
    """Validate `instance` and write the dashboard to `out`. Returns the output path."""
    commit = check_pin(root, allow_unpinned)
    sdk = load_sdk(root)
    issues = sdk.validate(instance, root=root)
    if issues:
        raise BuildError("No dashboard: the file does not pass validation.\n" + "\n".join(f"  - {i}" for i in issues))
    reg = sdk.Registry.load(instance)
    Path(out).write_text(render(reg, Path(instance).name, commit, today), encoding="utf-8")
    return Path(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a static HTML dashboard from an OpenChokepoint instance file.")
    ap.add_argument("instance")
    ap.add_argument("--openchokepoint", help="path to an OpenChokepoint checkout at the pinned commit")
    ap.add_argument("--out", default="dashboard.html")
    ap.add_argument("--allow-unpinned", action="store_true")
    args = ap.parse_args(argv)
    try:
        root = resolve_root(args.openchokepoint)
        path = build(args.instance, root, args.out, args.allow_unpinned)
    except BuildError as e:
        print(e, file=sys.stderr)
        return 2
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
