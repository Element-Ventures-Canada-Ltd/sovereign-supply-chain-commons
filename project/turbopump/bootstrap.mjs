#!/usr/bin/env node
// Handling: Unclassified — working
//
// Creates labels, milestones, the epic and all sub-task issues from plan.json.
// Uses the GitHub REST API only. Safe to re-run, by hand or from CI:
//  - labels and milestones are matched by name / title and left alone if present;
//  - issues are matched by a hidden marker in their body (<!-- tpm-plan-id: KEY -->),
//    not by who opened them, so a manual run and a CI run see the same issues;
//  - only issues opened by a trusted author are adopted, so a look-alike issue
//    carrying a copied marker is ignored (and a duplicate is not skipped because of it).
// An issue's KEY is its "key" field in plan.json, or a slug of its title.
// Give a task a "key" before renaming it, so the rename updates the existing issue.
// Existing issue bodies are never overwritten: people tick checklists there.
// When new sub-tasks are added later, they are listed in a comment on the epic.
//
// GH_TOKEN=... node project/turbopump/bootstrap.mjs owner/repo [--dry-run]
// --dry-run reads the repo (if a token is set) and prints what it would change.
// TPM_TRUSTED_AUTHORS (optional): extra comma-separated logins to trust.
// github-actions[bot] and the token's own user are always trusted.
import { readFileSync } from 'node:fs';

const [repo, flag] = process.argv.slice(2);
const dry = flag === '--dry-run';
if (!repo || !/^[\w.-]+\/[\w.-]+$/.test(repo)) { console.error('Usage: bootstrap.mjs owner/repo [--dry-run]'); process.exit(2); }
const token = process.env.GH_TOKEN || process.env.GITHUB_TOKEN;
if (!token && !dry) { console.error('Set GH_TOKEN'); process.exit(2); }
const plan = JSON.parse(readFileSync(new URL('./plan.json', import.meta.url), 'utf8'));

const API = 'https://api.github.com';
const headers = { Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

async function gh(method, path, body) {
  if (method !== 'GET' && dry) { console.log(`[dry-run] ${method} ${path} ${body?.title || body?.name || ''}`.trim()); return { number: 0, title: body?.title }; }
  if (method === 'GET' && !token) return [];
  const res = await fetch(`${API}/repos/${repo}${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) throw new Error(`${method} ${path}: ${res.status} ${await res.text()}`);
  return res.status === 204 ? null : res.json();
}
async function all(path) {
  const out = [];
  for (let page = 1; ; page++) {
    const batch = await gh('GET', `${path}${path.includes('?') ? '&' : '?'}per_page=100&page=${page}`);
    out.push(...batch);
    if (batch.length < 100) return out;
  }
}

// Keys: stable identity for each planned issue.
const slug = (t) => t.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60);
const keyOf = (it) => it.key || slug(it.title);
const EPIC_KEY = 'epic';
const marker = (key) => `<!-- tpm-plan-id: ${key} -->`;
const MARK = /<!-- tpm-plan-id: ([a-z0-9-]+) -->/;
{
  const seen = new Set([EPIC_KEY]);
  for (const it of plan.issues) {
    const k = keyOf(it);
    if (!/^[a-z0-9-]+$/.test(k)) throw new Error(`plan.json: key "${k}" may use only a-z, 0-9 and -`);
    if (seen.has(k)) throw new Error(`plan.json: duplicate key "${k}" (add a unique "key" field)`);
    seen.add(k);
  }
}

// Trusted authors: the CI bot, the token's own user (when the token may ask), and any extras.
const trusted = new Set(['github-actions[bot]', ...(process.env.TPM_TRUSTED_AUTHORS || '').split(',').map((s) => s.trim()).filter(Boolean)]);
if (token) {
  try {
    const r = await fetch(`${API}/user`, { headers });
    if (r.ok) { const u = await r.json(); if (u.login) trusted.add(u.login); }
  } catch { /* CI tokens cannot read /user; the bot login above covers them */ }
}

// Labels and milestones.
const haveLabels = new Set((await all('/labels')).map((l) => l.name));
let newLabels = 0;
for (const l of plan.labels) if (!haveLabels.has(l.name)) { await gh('POST', '/labels', l); newLabels++; }

const ms = new Map((await all('/milestones?state=all')).map((m) => [m.title, m.number]));
let newMilestones = 0;
for (const m of plan.milestones) if (!ms.has(m.title)) { ms.set(m.title, (await gh('POST', '/milestones', m)).number); newMilestones++; }
const msNum = (i) => { const m = plan.milestones[i - 1]; if (!m) throw new Error(`plan.json: milestone ${i} does not exist`); return ms.get(m.title); };

// Existing issues opened by a trusted author, indexed by marker key (or by title for any pre-marker issue).
const byKey = new Map();
const byTitle = new Map();
for (const i of await all('/issues?state=all&labels=module:turbopump')) {
  if (i.pull_request || !trusted.has(i.user?.login)) continue;
  const m = (i.body || '').match(MARK);
  if (m) { if (!byKey.has(m[1])) byKey.set(m[1], i); } else if (!byTitle.has(i.title)) byTitle.set(i.title, i);
}

// Sub-tasks.
const all_ = [];
const added = [];
let renamed = 0;
for (const it of plan.issues) {
  const key = keyOf(it);
  const title = `[TPM] ${it.title}`;
  let issue = byKey.get(key) || byTitle.get(title);
  if (issue) {
    if (issue.title !== title) { await gh('PATCH', `/issues/${issue.number}`, { title }); renamed++; }
  } else {
    const labels = ['module:turbopump', `ws:${it.ws}`, `zone:${it.zone}`, 'status:todo', ...(it.agent ? ['agent:claude'] : [])];
    issue = await gh('POST', '/issues', { title, body: `${it.body}\n\n${marker(key)}`, labels, milestone: msNum(it.m) });
    added.push({ ...it, number: issue.number });
  }
  all_.push({ ...it, number: issue.number });
}

// Epic.
const line = (c) => `- [ ] #${c.number} ${c.title}${c.zone === 'red' ? ' (red zone)' : ''}`;
const checklist = plan.milestones.map((m, i) => `\n### ${m.title}\n` + all_.filter((c) => c.m === i + 1).map(line).join('\n')).join('\n');
const epic = byKey.get(EPIC_KEY) || byTitle.get(plan.epic.title);
let epicNote = 'existing';
if (!epic) {
  await gh('POST', '/issues', { title: plan.epic.title, labels: plan.epic.labels, body: `${plan.epic.body}\n${checklist}\n\n${marker(EPIC_KEY)}` });
  epicNote = 'created';
} else {
  if (epic.title !== plan.epic.title) await gh('PATCH', `/issues/${epic.number}`, { title: plan.epic.title });
  if (added.length) {
    await gh('POST', `/issues/${epic.number}/comments`, { body: `New sub-tasks added from plan.json:\n\n${added.map(line).join('\n')}` });
    epicNote = `existing, ${added.length} new sub-task(s) listed in a comment`;
  }
}

console.log(`Done${dry ? ' (dry run)' : ''}: labels ${newLabels} new of ${plan.labels.length}; milestones ${newMilestones} new of ${plan.milestones.length}; ` +
  `sub-tasks ${added.length} new, ${renamed} renamed, ${all_.length - added.length} already present; epic ${epicNote}.`);
