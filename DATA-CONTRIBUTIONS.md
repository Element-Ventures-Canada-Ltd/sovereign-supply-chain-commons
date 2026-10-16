Handling: Unclassified — working

# Data and Model Contributions

Requirements for any contribution of data, datasets, model weights, fine-tunes,
or evaluation sets to the open tier. These sit alongside CLA.md and HANDLING.md.

## Rules

1. **Synthetic or public only.** Data must be synthetic, or public and licensed
   for redistribution and model training. No real entity-level data from
   non-public sources.
2. **No personal information** unless fully de-identified and permitted by the
   source licence.
3. **No export-controlled technical data**, and nothing marked above
   "Unclassified — working".
4. **Right to train.** You must have the right to let EV use the data to train,
   evaluate, and distribute models, including commercially.
5. **Provenance manifest required.** Every data or model contribution includes
   a `provenance.yaml` in the same folder, completed as below.
6. **Mapping only.** Contributions identify suppliers, dependencies, and
   chokepoints. They must not include technical data on how a component is
   designed, made, or tested, or on how it performs, even if that data is public.
   A maintainer may decline or remove any contribution that crosses this line.
   See CONTRIBUTION-SCOPE.md.

### Maintainer scope approval (`# scope-ok`)

The scope check flags engineering units and terms as a heuristic. A flag on a
line that is genuinely mapping-only (for example a public-source figure used to
identify a capacity band or a controlled-item threshold) can be cleared by
ending that line with:

```yaml
options: [...]  # scope-ok: <reason, at least 10 characters>
```

- **Maintainers only.** The marker is honoured only when the PR author is an
  OWNER, MEMBER or COLLABORATOR of the repository. On a PR from anyone else the
  marker itself is a finding ("approval marker added by non-maintainer") and the
  check fails.
- **Public-source figures only.** Use it for figures taken from public sources,
  and say which in the reason. It never covers non-public data or technical data
  on how a component is designed, made, tested, or performs (rule 6).
- A reason shorter than 10 characters, or none, does not count.
- Every approved line (file, line, reason) is listed in the check's job summary
  for review.

## provenance.yaml template

```yaml
handling: "Unclassified — working"
contribution: ""          # short name
type: ""                  # dataset | weights | fine-tune | eval-set
sources:
  - description: ""
    url: ""
    licence: ""           # SPDX id or licence name
    retrieved: ""         # YYYY-MM-DD
synthetic: false          # true if generated
personal_information: none   # none | de-identified (explain in notes)
export_controlled: false
training_rights_confirmed: false
base_model: ""            # for weights / fine-tunes
notes: ""
```

Contributions without a complete manifest will not be merged.
