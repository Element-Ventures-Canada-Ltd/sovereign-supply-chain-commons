# Handling: Unclassified — working
"""Resolve the code reviewer's own Nit threads once the code under them changed.

After a passing claude-review run, this script resolves a thread only when
every one of these holds:
- the review bot started it, and its first comment is a code-review Nit;
- that comment cites a REVIEW.md rule, and none of rules 1-5 (findings under
  rules 1-5 close only by a fix or by the owner, never automatically);
- GitHub marks the thread outdated, so the line it pointed at really changed;
- this run reports no finding of any level in that file.

The reviewer model's silence is never enough on its own: GitHub's outdated
flag is the evidence of a code change, and Important, Pre-existing and all
security threads always stay for the owner.

Fail closed: if any finding's path is not exactly one of the pull request's
changed files, or the inputs cannot be read, nothing is resolved. Comment text
is untrusted; it is only parsed for the tag and rule numbers, and a comment
that parses ambiguously is left open. Any API failure leaves threads open and
exits 0, so this step never changes a check result.

Usage:
  resolve_review_threads.py --result result.json --files files.json \
      --repo OWNER/NAME --pr NUMBER
"""
import argparse
import json
import re
import subprocess
import sys

BOT_LOGINS = {"github-actions", "github-actions[bot]"}
LEADING_MARKUP = re.compile(r"^[\s*_>`]+")
TAG = re.compile(r"^(Important|Nit|Pre-existing|Security)\b")
RULE_REF = re.compile(r"\brules?\s+(\d+(?:\s*(?:-|–|,|and|or)\s*\d+)*)", re.IGNORECASE)
PROTECTED_RULES = {1, 2, 3, 4, 5}

THREADS_QUERY = """
query($owner: String!, $name: String!, $pr: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          comments(first: 1) { nodes { author { login } body } }
        }
      }
    }
  }
}
"""

RESOLVE_MUTATION = """
mutation($id: ID!) { resolveReviewThread(input: {threadId: $id}) { thread { isResolved } } }
"""


def tag_of(body):
    """The leading tag of a review comment, or None."""
    m = TAG.match(LEADING_MARKUP.sub("", body or ""))
    return m.group(1) if m else None


def rules_cited(body):
    """Every REVIEW.md rule number the comment cites (ranges expanded)."""
    found = set()
    for group in RULE_REF.findall(body or ""):
        for a, b in re.findall(r"(\d+)\s*[-–]\s*(\d+)", group):
            lo, hi = int(a), int(b)
            if hi - lo > 20:
                return {0}  # nonsense range: treat as unparseable
            found.update(range(lo, hi + 1))
        found.update(int(n) for n in re.findall(r"\d+", group))
    return found


def auto_resolvable(body):
    """True only for a Nit that cites rules, none of them 1-5."""
    if tag_of(body) != "Nit":
        return False
    rules = rules_cited(body)
    return bool(rules) and not (rules & PROTECTED_RULES) and 0 not in rules


def norm(path):
    path = path or ""
    return path[2:] if path.startswith("./") else path


def finding_paths(findings, changed_files):
    """Normalised finding paths, or None if any is not a changed file."""
    changed = set(changed_files)
    paths = set()
    for f in findings:
        p = norm(f.get("path") if isinstance(f, dict) else None)
        if p not in changed:
            return None
        paths.add(p)
    return paths


def select(threads, findings, changed_files):
    """Return the ids of threads safe to resolve. Pure: no network."""
    open_paths = finding_paths(findings, changed_files)
    if open_paths is None:
        return []
    chosen = []
    for t in threads:
        if t.get("isResolved") or t.get("isOutdated") is not True:
            continue
        first = (t.get("comments") or {}).get("nodes") or []
        if not first:
            continue
        author = ((first[0].get("author") or {}).get("login")) or ""
        if author not in BOT_LOGINS:
            continue
        if not auto_resolvable(first[0].get("body")):
            continue
        if norm(t.get("path")) in open_paths:
            continue
        chosen.append(t["id"])
    return chosen


def graphql(query, **variables):
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if value is None:
            continue
        flag = "-F" if isinstance(value, int) else "-f"
        cmd += [flag, f"{key}={value}"]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    data = json.loads(out)
    if data.get("errors"):
        raise RuntimeError("GraphQL returned errors")
    return data["data"]


def fetch_threads(owner, name, pr):
    threads, after = [], None
    for _ in range(10):  # at most 1,000 threads; any beyond stay open
        page = graphql(THREADS_QUERY, owner=owner, name=name, pr=pr, after=after)
        rt = page["repository"]["pullRequest"]["reviewThreads"]
        threads += rt["nodes"]
        if not rt["pageInfo"]["hasNextPage"]:
            break
        after = rt["pageInfo"]["endCursor"]
    return threads


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True)
    ap.add_argument("--files", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", type=int, required=True)
    args = ap.parse_args(argv)
    try:
        with open(args.result, encoding="utf-8") as fh:
            findings = json.load(fh)["findings"]
        with open(args.files, encoding="utf-8") as fh:
            changed = [f["filename"] for f in json.load(fh)]
        if finding_paths(findings, changed) is None:
            print("::warning::A finding's path is not one of the changed files, "
                  "so no threads were resolved; they stay open for the owner.")
            return 0
        owner, name = args.repo.split("/", 1)
        ids = select(fetch_threads(owner, name, args.pr), findings, changed)
        done = 0
        for tid in ids:
            graphql(RESOLVE_MUTATION, id=tid)
            done += 1
        print(f"Resolved {done} outdated Nit thread(s) whose finding is no longer reported.")
    except Exception as exc:  # leave threads open; never change the check result
        print(f"::warning::Could not resolve review threads ({type(exc).__name__}); "
              "they stay open for the owner.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
