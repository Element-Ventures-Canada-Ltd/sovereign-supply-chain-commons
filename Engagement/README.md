Handling: Unclassified — working

# Engagement workflow

A client-agnostic workflow for professional-services engagements that feed the platform's products: from solicitation to response, delivery gates, acceptance and periodic reporting.

| Part | Path |
|---|---|
| Engine (validate, status, report, due) | `tools/engagement.py` |
| File format | `schema/engagement.schema.md` |
| Solicitation response: intake → compliance matrix → review → submission | `templates/solicitation-response/` |
| Inception report, gate evidence pack | `templates/` |
| Fictional example | `examples/example-engagement.yaml` |

```bash
python3 Engagement/tools/engagement.py validate Engagement/examples/example-engagement.yaml
python3 Engagement/tools/engagement.py status   Engagement/examples/example-engagement.yaml
python3 Engagement/tools/engagement.py report   Engagement/examples/example-engagement.yaml
```

Rules: counterparties are named by role only; commercial terms never enter the repository; every engagement names a productization target; reports are opened as issues, not committed.

Live engagements and engagement-specific mappings are held in the proprietary core repository.
