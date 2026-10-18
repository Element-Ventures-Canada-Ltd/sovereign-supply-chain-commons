# Handling: Unclassified — working
"""Resolve an automated reviewer's own threads once their finding is gone.

Each review run reports every finding still present in the code. After a run,
this script resolves that reviewer's own unresolved threads on the pull
request, but only in files where the run now reports no finding at all.

What it never touches:
- threads started by anyone other than the review bot;
- the other reviewer's threads (code review and security review each clear
  only their own, told apart by how their comments begin);
- any thread in a file where this run still reports a finding of any level,
  so open MEDIUM, LOW, Nit and Pre-existing threads keep blocking the merge
  until a person resolves them.

Comment text is untrusted; it is read only to tell the two reviewers apart.
Any API failure leaves threads open (the safe direction) and exits 0, so
this step never changes a check result.

Usage:
  resolve_review_threads.py --reviewer code|security --result result.json \
      --repo OWNER/NAME --pr NUMBER
"""
import argparse
import json
import re
import subprocess
import sys

BOT_LOGINS = {"github-actions", "github-actions[bot]"}
CODE_PREFIX = re.compile(r"^(Important|Nit|Pre-existing)\b")
SECURITY_PREFIX = re.compile(r"^Security\b")
LEADING_MARKUP = re.compile(r"^[\s*_>`]+")

THREADS_QUERY = """
query($owner: String!, $name: String!, $pr: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
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


def reviewer_of(body):
    """Which reviewer wrote a comment: 'code', 'security' or None."""
    text = LEADING_MARKUP.sub("", body or "")
    if SECURITY_PREFIX.match(text):
        return "security"
    if CODE_PREFIX.match(text):
        return "code"
    return None


def norm(path):
    path = path or ""
    return path[2:] if path.startswith("./") else path


def select(threads, reviewer, findings):
    """Return the ids of threads safe to resolve. Pure: no network."""
    open_paths = {norm(f.get("path")) for f in findings}
    chosen = []
    for t in threads:
        if t.get("isResolved"):
            continue
        first = (t.get("comments") or {}).get("nodes") or []
        if not first:
            continue
        author = ((first[0].get("author") or {}).get("login")) or ""
        if author not in BOT_LOGINS:
            continue
        if reviewer_of(first[0].get("body")) != reviewer:
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
    for _ in range(10):  # at most 1,000 threads
        page = graphql(THREADS_QUERY, owner=owner, name=name, pr=pr, after=after)
        rt = page["repository"]["pullRequest"]["reviewThreads"]
        threads += rt["nodes"]
        if not rt["pageInfo"]["hasNextPage"]:
            break
        after = rt["pageInfo"]["endCursor"]
    return threads


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reviewer", choices=["code", "security"], required=True)
    ap.add_argument("--result", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", type=int, required=True)
    args = ap.parse_args(argv)
    try:
        with open(args.result, encoding="utf-8") as fh:
            findings = json.load(fh)["findings"]
        owner, name = args.repo.split("/", 1)
        ids = select(fetch_threads(owner, name, args.pr), args.reviewer, findings)
        done = 0
        for tid in ids:
            graphql(RESOLVE_MUTATION, id=tid)
            done += 1
        print(f"Resolved {done} {args.reviewer} review thread(s) whose finding is no longer reported.")
    except Exception as exc:  # leave threads open; never change the check result
        print(f"::warning::Could not resolve review threads ({type(exc).__name__}); "
              "they stay open for the owner.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
