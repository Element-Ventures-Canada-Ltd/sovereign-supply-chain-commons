Handling: Unclassified — working

# Red-team checklist: workforce records and parameters

Use this to challenge any row in `data/` or any parameter recorded in the parameter record format (`schema/parameter_record.schema.json`). A challenge that lands is a contribution: open an issue with the row id and the item number below. Process and credit are in [RED-TEAM.md](../RED-TEAM.md).

| # | Test | Fails when | Typical fix |
|---|---|---|---|
| 1 | **Provenance** | The figure was taken from a summary, press story or vendor page, not the primary document | Retrieve the primary; until then cap the grade at AS |
| 2 | **Recency** | The source is over 10 years old, or a newer edition exists | Record the date; look for a newer edition; lower confidence |
| 3 | **Jurisdiction** | A US rule or study is presented as a Canadian obligation or finding | Mark US rules `benchmark`; set `jurisdiction` correctly |
| 4 | **Extrapolation** | Aviation, military or medical evidence is applied to propulsion test crews without saying so | State it in the finding and set `extrapolated_from` |
| 5 | **Sample and spread** | A meta-analytic average is used as if it fits every task | Record study count and moderators; split by task type |
| 6 | **Independence** | Two "corroborating" sources share a principal, author or dataset | Put them in one `independence_group`; count once |
| 7 | **Circular citation** | An "accepted" figure has no traceable origin | Trace it or retire it |
| 8 | **Units** | Units are mixed (SD vs percent, hours vs months) or missing | Convert and state the unit |
| 9 | **Sensitivity** | No one has checked whether a plus or minus 50% change in an S-tier value flips a decision | Run the sweep; record `sensitivity_note` |
| 10 | **Self-interest** | A provider's own figure (price, pass mark, shortage claim) is treated as independent | Grade PR; say whose figure it is |
| 11 | **Conflicts** | Sources disagree and only one is shown | Record both; say which governs and why |
| 12 | **Inference shown as fact** | A requirement in `role_skills.csv` reads as sourced but is EV judgement | Set `basis` to `inference` and remove the source |
| 13 | **Announced vs in force** | Pending legislation or a programme announcement is treated as law or as operating | Use `announced`; note the stage |
| 14 | **Scope and safety** | A row carries technical test or performance data, export-controlled detail, personal data or site-security detail | Remove it; this repository maps workforce and supply chain only |

## Known open challenges (seeded)

- **No propulsion-specific decay or transfer evidence.** Every `skill_evidence` row on `SK-07` to `SK-14` is borrowed from general procedural, military or aviation studies. A study on propulsion or test-stand crews would replace them.
- **Provider claims.** `PG-13` and `EE-19` rest on the provider's own pages; the CCAA certification is not yet confirmed by CCAA.
- **Shared principal.** Organisations that share a principal (for example, a training provider and a competition run by the same founder) are not independent sources for each other.
- **Inferences.** `RS-05`, `RS-07`, `RS-09` and `RS-10` are Element Ventures judgement and are labelled so.

---

Element Ventures (Canada) Ltd. · Sovereign Operating Intelligence (SOI™)
