# OKF — Open Knowledge Format (Tone Neuron profile)

Tone Neuron's knowledge layer stores cultural etiquette as plain text OKF files, one file per
region: `tone_neuron/data/knowledge/<region>.okf.md`. OKF is deliberately boring: YAML front
matter for machine-readable metadata, Markdown prose for humans, no database, reviewable in a pull
request.

## File shape

```markdown
---
okf: "1.0"
kind: culture-profile
region: JP
region_name: Japan
languages: [ja]
last_reviewed: 2026-01-15
caveat: "Common business norms. Individuals and organisations vary widely."
provenance:
  type: seed            # seed | editorial | user
  confidence: editorial
  sources:
    - "Seed profile written for this project; not a primary source."
entries:
  - id: jp.honorifics
    title: Honorifics and address form
    category: honorifics          # greeting|honorifics|formality|directness|humor|
                                  # idioms|taboo|hierarchy|decision_making|
                                  # punctuality|feedback|small_talk|negotiation
    severity: high                # impact if violated: low|medium|high
    tags: [san, sama, address, respect]
    flagged:
      - pattern: "hey {first_name}"
        match: regex              # literal (default) | regex
        why: "First-name greeting without an honorific reads as dismissive."
        severity: medium
        suggested: "{first_name}-san,"
      - pattern: "asap"
        why: "Deadline demands feel abrupt; give a date and a reason."
        severity: medium
        suggested: "by Friday, 6 March, please"
    preferred: ["Tanaka-san", "Tanaka-sama (client)"]
    do: ["Use surname + san for colleagues", "Use sama for customers"]
    avoid: ["First names without invitation", "Dropping the honorific in email"]
    cites: ["https://example.org/optional-reference"]

## jp.honorifics

### Guidance
Japanese business writing keeps address form stable across a thread...
```

## Parsing rules

1. Front matter must start on line 1 with `---` and parse as a YAML mapping.
2. `region` and `region_name` are required; `entries` must be a non-empty list.
3. Entry `id` must be globally unique across all files and match `^[a-z]{2}\.[a-z0-9_.-]+$`.
4. Any `## <id>` section supplies the prose `guidance` for that entry. Missing sections are allowed
   (metadata-only entries) but discouraged.
5. `flagged[].match` is `literal` (case-insensitive substring, default) or `regex` (Python `re`,
   case-insensitive). Invalid regexes raise `OkfError` at load time — fail loudly, not silently.
6. `severity` defaults to the entry severity when omitted on a flag.
7. `caveat` from the document is attached to every entry and surfaced in culture cards so the
   "norms, not rules about a person" framing travels with the data.

## Adding a region

Drop `xx.okf.md` in the knowledge folder with a `xx.` id prefix, rebuild the index
(`python scripts/build_index.py`), and add a matching entry in `characters.json` and `cards.json`
for the mascot. Nothing else needs to change: retrieval, the gate, cards and coaching read from the
index.
