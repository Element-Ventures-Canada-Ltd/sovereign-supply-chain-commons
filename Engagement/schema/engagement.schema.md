Handling: Unclassified — working

# Engagement file format (`engagement.yaml`)

All keys sit under `engagement:`. The engine (`Engagement/tools/engagement.py validate`) enforces this format.

| Key | Required | Meaning |
|---|---|---|
| `id` | yes | `E-YYYY-NN` |
| `title` | yes | Neutral descriptive title; no counterparty names |
| `handling` | yes | Handling marking (see HANDLING.md) |
| `roles` | yes | `client`, `sponsor`, `delivery_lead` — labels by role only |
| `term` | yes | `start` (effective date, may be null until signature), `end` |
| `solicitation` | no | `stage` (intake, compliance, drafting, review, submitted, awarded, declined), `response_version`, `compliance_matrix` |
| `reporting` | yes | `cadence_days`, `anchor` (first report date), `channel` (`issue`) |
| `phases` | no | Method steps: `id`, `name`, `deliverable`, `status` |
| `deliverables` | yes | `id`, `title`, `components`, `evidence` (required), `status` (not_started, in_progress, in_review, submitted, accepted), `continuous` |
| `gates` | yes | `id`, `name`, `date`, `deliverables` |
| `acceptance` | yes | `id`, `name`, `standard`, `evidence`, optional `metric` + `threshold` |
| `metrics` | no | Counters referenced by acceptance criteria |
| `productization` | yes | `target` (required), `conversion_date` — every services engagement names its product conversion |
| `open_items` | no | `id`, `question`, `owner` (required), `status` (open, decided, closed) |

**Never in this file:** fees, payment percentages, payment triggers, currency amounts, counterparty names, solicitation text. The validator fails on currency amounts and fee or payment language.
