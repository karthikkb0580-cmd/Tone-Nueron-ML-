# Fairness, bias and privacy notes

Tone Neuron makes guesses about people. This document states exactly which guesses it makes, how
much weight they carry, and how the product is designed so a guess never becomes a stereotype
applied to an individual.

## 1. What the system infers

| Signal | Example | Weight | Failure mode |
|---|---|---|---|
| Name script/origin | `田中健司`, `Müller`, `Souza` | moderate | mixed families, diaspora, transliteration |
| Email TLD | `.jp`, `.de`, `.co.in`, `.ae` | moderate | global companies, personal domains, VPN-era mobility |
| Explicit language | `ja`, `de-DE` | strong when stated | multilingual people, code-switching |
| Time zone | `Asia/Tokyo` | moderate | travel, remote work, night shifts |
| Signature | `Kind regards, Kenji Tanaka, Tokyo` | weak | copy-pasted templates |
| Phrasing cues | honorifics, indirectness markers | weak | non-native speakers imitating a style |

Signals are combined into a probability distribution, never a single deterministic answer. The
reported confidence is capped at **0.95** and labelled `low` / `moderate` / `strong`, and every
response carries `is_guess: true` plus `alternatives`.

## 2. Rules the code enforces

1. **Override beats inference.** `receiver_info.region_override` short-circuits Task A entirely and
   the response marks `region_overridden: true`. The mascot UI exposes the same switch.
2. **No "person X is from country Y" statement.** The API returns `region`/`confidence`, and reason
   strings say *"likely"*, *"signals suggest"*, *"this suggests"* — never identity claims.
3. **No individual scoring.** Nothing is stored per person. The session store keeps only aggregate
   counts, region codes, risk labels and short redacted excerpts that are cleared after the daily
   review. There is no recipient profile, no reputation score, no cross-day history per person.
4. **Region-conditioned, not region-determined.** Task B adds region as a *feature*; the same sentence
   can be `polite` in one region and `blunt` in another, and the reasons show which etiquette entry
   drove the verdict so the user can disagree with it.
5. **Knowledge is framed as norms, not rules about a person.** Every OKF file states
   *"common business norms; individuals and organisations vary"* and includes a `caveat` field that
   is surfaced in the card and available to the rewriter.
6. **Citations are mandatory.** `analyze()`, `gate()` and `coaching/daily` all return the OKF entry
   ids and excerpts behind each claim. If retrieval finds nothing relevant, the verdict degrades to
   `low` confidence and says so rather than inventing a rule.

## 3. Dataset bias

`tone_neuron/ml/dataset.py` generates **synthetic** drafts. Consequences:

* Reported metrics measure how well the models learn the synthetic template distribution. They are
  **not** estimates of real-world accuracy and must not be presented as such.
* The generator deliberately includes hard cases (diaspora names, generic `.com` addresses,
  multilingual signatures, quiet/indirect rude messages, polite-sounding sensitive content) so the
  region model cannot trivially memorise a TLD table.
* Region coverage is limited to 8 seed regions and 5 tone labels. Low-resource regions, dialects,
  non-business registers and non-Latin scripts are under-represented.
* English-dominant phrasing means the tone model partly learns English politeness markers. A
  production model needs per-language data and human annotation.

**Before real deployment:** collect consented, annotated messages per region and language; report
metrics sliced by region, language, gender-signalled names and native/non-native speaker status;
run a red-team review for dignity harms (e.g. flagging AAVE or Indian English as "rude").

## 4. Risk of over-blocking

The gate blocks only `risk == "high"` AND a high-severity sensitive/rude flag. Everything else is a
hint. Every block lists at least one rewrite and an explicit "send as-is" path after mascot
verification. The system is deliberately biased toward *not* blocking, because falsely blocking
speech is a bigger harm than a gentle nudge.

## 5. Privacy

* Email and meeting content is processed in memory; the backend never writes it to disk and logs
  only counts/labels.
* Redaction (`name@domain` → `n***@domain`, phone digits → `*`) is applied before anything is kept
  for the daily review, and `POST /coaching/daily` clears the buffer.
* Gmail access is read-only (`gmail.readonly`); Tone Neuron cannot send email.
* If an LLM rewriter is enabled, only the message text plus the retrieved OKF snippets leave the
  machine. Users can keep it fully local by leaving `TONE_NEURON_ENABLE_LLM=false`.
* Art/characters are placeholders, not depictions of real people or a claim to represent a culture's
  "look".
