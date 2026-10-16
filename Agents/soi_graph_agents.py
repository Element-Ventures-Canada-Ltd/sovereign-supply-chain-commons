#!/usr/bin/env python3
# Handling: Unclassified — working
"""
SOI Graph Agents — plain-check agents for the open tier.

  feeds          Feed Agent. Checks every watched data feed for availability,
                 moved URLs, licence changes and new publications. Keeps one
                 rolling GitHub issue up to date and comments only when
                 something needs a maintainer.
  contributions  Contribution Agent. Screens a pull request, issue or comment
                 with plain checks, applies labels and writes a job summary.
                 It never comments, merges, closes or runs contributed code.

The Supplier Agent runs in the private core repository, not here.

Standard library only, plus PyYAML for the watchlist.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checks  # noqa: E402

USER_AGENT = "EV-SOI-Agents/0.1 (+https://elementventures.ca; open-tier feed monitor)"
STATE_MARKER = "soi-graph-agents-state"
FEEDS_LABEL = "agent:feeds"
FEEDS_TITLE = "Feed Agent — rolling report"
MAX_BYTES = 3_000_000


# --------------------------------------------------------------------------- GitHub
class GitHub:
    def __init__(self, repo: str, token: str, api: str = "https://api.github.com"):
        self.repo, self.token, self.api = repo, token, api

    def req(self, method: str, path: str, data=None):
        url = path if path.startswith("http") else f"{self.api}{path}"
        body = json.dumps(data).encode() if data is not None else None
        r = urllib.request.Request(url, data=body, method=method, headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT,
        })
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None

    def paged(self, path: str, limit: int = 1000) -> list:
        out, page = [], 1
        sep = "&" if "?" in path else "?"
        while len(out) < limit:
            chunk = self.req("GET", f"{path}{sep}per_page=100&page={page}")
            if not chunk:
                break
            out += chunk
            if len(chunk) < 100:
                break
            page += 1
        return out

    def label_names(self) -> set[str]:
        return {l["name"] for l in self.paged(f"/repos/{self.repo}/labels")}

    def file_text(self, path: str, ref: str) -> str | None:
        q = urllib.parse.quote(path)
        try:
            meta = self.req("GET", f"/repos/{self.repo}/contents/{q}?ref={ref}")
        except urllib.error.HTTPError:
            return None
        if not isinstance(meta, dict) or meta.get("encoding") != "base64" or meta.get("size", 0) > 1_000_000:
            return None
        return base64.b64decode(meta["content"]).decode("utf-8", errors="ignore")


# --------------------------------------------------------------- Contribution Agent
def run_contributions(event_name: str, event: dict, gh, dry_run: bool = False) -> checks.Result:
    result = checks.Result()
    number, title = None, event_name

    if event_name in ("pull_request_target", "pull_request"):
        pr = event["pull_request"]
        number, title = pr["number"], f"PR #{pr['number']}"
        files = gh.paged(f"/repos/{gh.repo}/pulls/{number}/files")
        paths = [f["filename"] for f in files if f.get("status") != "removed"]
        commits = gh.paged(f"/repos/{gh.repo}/pulls/{number}/commits")
        messages = [c["commit"]["message"] for c in commits]
        for p in paths:
            text = gh.file_text(p, pr["head"]["sha"])
            if text is None:
                if checks.is_data_file(p):
                    result.add("unreadable", "info", p, "file too large or binary; review manually")
                continue
            checks.check_file(p, text, result)
        checks.check_pr(pr.get("body") or "", pr.get("author_association", ""), messages, paths, result)

    elif event_name == "issues":
        issue = event["issue"]
        number, title = issue["number"], f"issue #{issue['number']}"
        if issue.get("author_association") not in checks.MAINTAINER_ASSOCIATIONS:
            checks.check_text_signals(f"{issue.get('title', '')}\n{issue.get('body') or ''}", "issue", result)

    elif event_name == "issue_comment":
        issue, comment = event["issue"], event["comment"]
        number, title = issue["number"], f"comment on #{issue['number']}"
        is_bot = (comment.get("user") or {}).get("type") == "Bot"
        if not is_bot and comment.get("author_association") not in checks.MAINTAINER_ASSOCIATIONS:
            checks.check_text_signals(comment.get("body") or "", "comment", result)

    labels = set(result.labels)
    if result.needs_review:
        labels.add("agent:review")
    if number and labels and not dry_run:
        existing = gh.label_names()
        apply = sorted(labels & existing)
        if apply:
            gh.req("POST", f"/repos/{gh.repo}/issues/{number}/labels", {"labels": apply})

    summary = checks.render_summary(title, result)
    if labels:
        summary += f"\nLabels proposed: {', '.join(sorted(labels))}\n"
    _write_summary(summary)
    return result


# ----------------------------------------------------------------------- Feed Agent
def _fetch(url: str, method: str = "GET", max_bytes: int = MAX_BYTES, headers: dict | None = None):
    h = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    h.update(headers or {})
    req = urllib.request.Request(url, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            body = resp.read(max_bytes) if method == "GET" else b""
            return {"status": resp.status, "final_url": resp.geturl(),
                    "headers": {k.lower(): v for k, v in resp.headers.items()}, "body": body}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "final_url": url, "headers": {}, "body": b"", "error": f"HTTP {e.code}"}
    except Exception as e:  # network, TLS, timeout
        return {"status": 0, "final_url": url, "headers": {}, "body": b"", "error": type(e).__name__}


def normalize_text(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="ignore")
    text = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def observe(check: dict, fetch=_fetch) -> dict:
    """Take one observation of a watched URL. Returns a flat, comparable dict."""
    kind, url = check.get("kind", "page"), check["url"]
    obs: dict = {"kind": kind, "url": url, "bot_protected": bool(check.get("bot_protected"))}
    if kind == "data":
        r = fetch(url, "HEAD")
        if not (200 <= r["status"] < 400):  # many servers reject HEAD; retry with a 1-byte GET
            r = fetch(url, "GET", max_bytes=1, headers={"Range": "bytes=0-0"})
        obs.update(status=r["status"], final_url=r["final_url"], error=r.get("error"),
                   last_modified=r["headers"].get("last-modified"), etag=r["headers"].get("etag"),
                   length=r["headers"].get("content-length"))
        return obs

    r = fetch(url, "GET")
    obs.update(status=r["status"], final_url=r["final_url"], error=r.get("error"))
    if not (200 <= r["status"] < 300):
        return obs
    if kind == "page":
        text = normalize_text(r["body"])
        obs["text_hash"] = hashlib.sha256(text.encode()).hexdigest()[:16]
        obs["missing_phrases"] = [p for p in check.get("must_contain", []) if p.lower() not in text.lower()]
    elif kind in ("ckan", "json", "fedreg"):
        try:
            data = json.loads(r["body"])
        except ValueError:
            obs["error"] = "invalid JSON"
            return obs
        if kind == "ckan":
            res = data.get("result") or {}
            obs.update(metadata_modified=res.get("metadata_modified"), license_id=res.get("license_id"),
                       resources=len(res.get("resources") or []))
            want = check.get("expect_licence")
            obs["licence_ok"] = (want is None) or (res.get("license_id") == want)
        elif kind == "fedreg":
            results = data.get("results") or []
            top = results[0] if results else {}
            obs.update(count=data.get("count"), newest=top.get("document_number"),
                       newest_title=(top.get("title") or "")[:160], newest_date=top.get("publication_date"))
    return obs


def compare(feed_id: str, label: str, prev: dict | None, cur: dict) -> list[dict]:
    """Turn two observations into events. Severity: alert > warn > info."""
    ev = []

    def add(sev, msg):
        ev.append({"severity": sev, "feed": feed_id, "check": label, "message": msg})

    ok = is_ok(cur)
    fails = 0 if ok else (prev or {}).get("fails", 0) + 1
    cur["fails"] = fails
    if not ok:
        reason = cur.get("error") or f"HTTP {cur.get('status')}"
        add("alert" if fails >= 2 else "warn", f"unreachable ({reason}); consecutive failures: {fails}")
        return ev
    if prev and prev.get("fails", 0) >= 1:
        add("info", "reachable again")
    if cur.get("status") == 429:
        add("info", "rate-limited (HTTP 429); reachable, content not checked")
    if cur.get("status") == 403 and cur.get("bot_protected"):
        add("info", "bot-protected (HTTP 403); check this page manually")
    if cur.get("missing_phrases"):
        add("alert", f"licence or terms text no longer found: {', '.join(cur['missing_phrases'])}")
    if cur.get("licence_ok") is False:
        add("alert", f"catalogue licence is now `{cur.get('license_id')}`")
    if not prev or prev.get("status") in (None, 0):
        return ev  # baseline
    if prev.get("final_url") and _host_path(prev["final_url"]) != _host_path(cur.get("final_url", "")):
        add("warn", f"moved: now resolves to {cur.get('final_url')}")
    if cur["kind"] == "ckan" and prev.get("license_id") and prev.get("license_id") != cur.get("license_id"):
        add("alert", f"licence changed from `{prev.get('license_id')}` to `{cur.get('license_id')}`")
    if cur["kind"] == "fedreg" and prev.get("newest") and prev.get("newest") != cur.get("newest"):
        add("alert", f"new Federal Register document: {cur.get('newest_title')} ({cur.get('newest_date')})")
    for key in ("last_modified", "etag", "metadata_modified"):
        if prev.get(key) and cur.get(key) and prev[key] != cur[key]:
            add("info", f"new publication ({key} {prev[key]} → {cur[key]})")
            break
    if cur["kind"] == "page" and prev.get("text_hash") and prev["text_hash"] != cur.get("text_hash"):
        add("info", "page content changed")
    return ev


def is_ok(obs: dict) -> bool:
    status = obs.get("status") or 0
    if 200 <= status < 400 or status == 429:
        return True
    return status == 403 and bool(obs.get("bot_protected"))


def _host_path(u: str) -> str:
    p = urllib.parse.urlsplit(u)
    return f"{p.netloc.lower()}{p.path.rstrip('/')}"


def run_feeds(watchlist: dict, prev_state: dict, fetch=_fetch) -> tuple[dict, list[dict]]:
    state, events = {}, []
    for feed in watchlist["feeds"]:
        for i, check in enumerate(feed.get("checks", [])):
            key = f"{feed['id']}#{i}"
            label = check.get("label") or check.get("kind", "page")
            cur = observe(check, fetch)
            events += compare(feed["id"], label, prev_state.get(key), cur)
            state[key] = cur
    return state, events


SEV_ORDER = {"alert": 0, "warn": 1, "info": 2}


def render_feeds_report(watchlist: dict, state: dict, events: list[dict], baseline: bool) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "Handling: Unclassified — working", "",
        f"**Feed Agent** — last run {now}. Watchlist: `Agents/feed-watchlist.yaml`.", "",
        "The Feed Agent checks public feed endpoints only. It collects no entity data.", "",
    ]
    if baseline:
        lines += ["_Baseline run: observations recorded; changes are reported from the next run._", ""]
    act = sorted((e for e in events if e["severity"] != "info"), key=lambda e: SEV_ORDER[e["severity"]])
    lines += ["### Needs attention", ""]
    if act:
        lines += ["| Severity | Feed | Check | What changed |", "| :-- | :-- | :-- | :-- |"]
        lines += [f"| {e['severity']} | `{e['feed']}` | {e['check']} | {e['message']} |" for e in act]
    else:
        lines.append("Nothing.")
    lines += ["", "### Status", "", "| Feed | Checks | Status |", "| :-- | :-- | :-- |"]
    for feed in watchlist["feeds"]:
        keys = [k for k in state if k.split("#")[0] == feed["id"]]
        bad = [k for k in keys if not is_ok(state[k])]
        flag = [e for e in act if e["feed"] == feed["id"]]
        status = "down" if bad else ("check" if flag else "ok")
        verify = " (URL to verify)" if feed.get("verify") else ""
        lines.append(f"| `{feed['id']}`{verify} | {len(keys)} | {status} |")
    info = [e for e in events if e["severity"] == "info"]
    if info:
        lines += ["", "<details><summary>Informational changes</summary>", ""]
        lines += [f"- `{e['feed']}` {e['check']}: {e['message']}" for e in info]
        lines += ["", "</details>"]
    return "\n".join(lines) + "\n"


def pack_state(state: dict) -> str:
    blob = base64.b64encode(zlib.compress(json.dumps(state, sort_keys=True).encode())).decode()
    return f"<!-- {STATE_MARKER}:{blob} -->"


def unpack_state(body: str | None) -> dict:
    m = re.search(rf"<!-- {STATE_MARKER}:([A-Za-z0-9+/=]+) -->", body or "")
    if not m:
        return {}
    try:
        return json.loads(zlib.decompress(base64.b64decode(m.group(1))))
    except Exception:
        return {}


def publish_feeds(gh: GitHub, watchlist: dict, fetch=_fetch) -> list[dict]:
    issues = gh.req("GET", f"/repos/{gh.repo}/issues?state=open&labels={urllib.parse.quote(FEEDS_LABEL)}&per_page=5") or []
    issue = issues[0] if issues else None
    prev = unpack_state(issue["body"] if issue else None)
    state, events = run_feeds(watchlist, prev, fetch)
    baseline = not prev
    body = render_feeds_report(watchlist, state, events, baseline) + "\n" + pack_state(state)
    if issue is None:
        labels = [l for l in (FEEDS_LABEL, "soi-agent") if l in gh.label_names()]
        gh.req("POST", f"/repos/{gh.repo}/issues", {"title": FEEDS_TITLE, "body": body, "labels": labels})
    else:
        gh.req("PATCH", f"/repos/{gh.repo}/issues/{issue['number']}", {"body": body})
        act = [e for e in events if e["severity"] in ("alert", "warn")]
        if act and not baseline:
            note = ["Feed Agent found changes that need a maintainer:", ""]
            note += [f"- **{e['severity']}** `{e['feed']}` {e['check']}: {e['message']}" for e in act]
            gh.req("POST", f"/repos/{gh.repo}/issues/{issue['number']}/comments", {"body": "\n".join(note)})
    _write_summary(render_feeds_report(watchlist, state, events, baseline))
    return events


# ------------------------------------------------------------------------- helpers
def _write_summary(text: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)


def load_watchlist(path: str) -> dict:
    import yaml  # PyYAML
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("feeds", help="run the Feed Agent")
    f.add_argument("--watchlist", default=str(Path(__file__).with_name("feed-watchlist.yaml")))
    f.add_argument("--dry-run", action="store_true", help="no GitHub writes; use --state-file instead")
    f.add_argument("--state-file", help="local JSON state for dry runs")
    c = sub.add_parser("contributions", help="run the Contribution Agent on the current GitHub event")
    c.add_argument("--dry-run", action="store_true", help="screen and summarise, but apply no labels")
    a = ap.parse_args(argv)

    repo, token = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", "")

    if a.cmd == "feeds":
        wl = load_watchlist(a.watchlist)
        if a.dry_run:
            prev = json.loads(Path(a.state_file).read_text()) if a.state_file and Path(a.state_file).exists() else {}
            state, events = run_feeds(wl, prev)
            print(render_feeds_report(wl, state, events, baseline=not prev))
            if a.state_file:
                Path(a.state_file).write_text(json.dumps(state, indent=1, sort_keys=True))
            return 0
        publish_feeds(GitHub(repo, token), wl)
        return 0

    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    run_contributions(os.environ.get("GITHUB_EVENT_NAME", ""), event, GitHub(repo, token), a.dry_run)
    return 0  # advisory: never fails the build


if __name__ == "__main__":
    sys.exit(main())
