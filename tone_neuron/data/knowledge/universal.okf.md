---
okf: "1.0"
kind: culture-profile
region: GL
region_name: Global (universal)
languages: []
last_reviewed: 2026-01-15
caveat: "Universal workplace baseline. Individual teams and relationships override any norm."
provenance:
  type: seed
  confidence: editorial
  sources:
    - "Seed profile written for this project; general workplace-communication practice, not a primary source."
entries:
  - id: gl.rudeness.insults
    title: Personal attacks and contempt
    category: taboo
    severity: high
    tags: [insult, contempt, respect, dignity, rude]
    do:
      - "Criticise the work or the process, never the person."
      - "Name the observable behaviour and its impact."
    avoid:
      - "Labels about someone's competence or character."
      - "Sarcasm aimed at a person in front of others."
    preferred: ["This does not meet the brief because the figures are missing.", "Can we fix the missing figures before Friday?"]
    flagged:
      - pattern: "idiot"
        why: "Direct personal insult; a high-risk dignity violation in any region."
        severity: high
        suggested: "this draft"
      - pattern: "stupid"
        why: "Personal attack, not feedback."
        severity: high
        suggested: "not yet ready"
      - pattern: "incompetent"
        why: "Character judgement about a colleague; escalates conflict."
        severity: high
        suggested: "the handover was incomplete"
      - pattern: "useless"
        why: "Contemptuous label; it attacks the person rather than the work."
        severity: high
        suggested: "not useful in its current form"
      - pattern: "shut up"
        why: "Silencing someone is a high-risk dignity violation."
        severity: high
        suggested: "let us park that point"
      - pattern: "you people"
        why: "Grouping the recipient into a 'them' reads as discriminatory."
        severity: high
        suggested: "the team"
      - pattern: "pathetic"
        why: "Contemptuous insult."
        severity: high
        suggested: "disappointing"
  - id: gl.sensitivity.legal_hr
    title: Sensitive employment and legal content
    category: taboo
    severity: high
    tags: [hr, legal, termination, lawsuit, sensitive, confidentiality]
    do:
      - "Move termination, discipline and legal matters to a private, documented channel."
      - "Have HR or legal review wording before it is sent."
    avoid:
      - "Announcing firings, lawsuits or allegations in a group thread."
      - "Admitting liability or promising outcomes in writing without approval."
    preferred: ["Let us discuss this in the HR session on Thursday.", "Legal will confirm the wording before we send anything."]
    flagged:
      - pattern: "you're fired"
        why: "Termination must never be delivered in a routine email or chat."
        severity: high
        suggested: "let us schedule a private conversation with HR"
      - pattern: "we will sue"
        why: "Legal threats escalate immediately and are hard to reverse."
        severity: high
        suggested: "legal is reviewing the contract"
      - pattern: "lawsuit"
        why: "Legal escalation language; route through legal counsel."
        severity: high
        suggested: "a formal contract review"
      - pattern: "discrimination"
        why: "Allegations of discrimination are sensitive and need a formal, confidential process."
        severity: high
        suggested: "a confidential concerns process"
      - pattern: "harassment"
        why: "Harassment claims must go through a confidential HR process, not a draft."
        severity: high
        suggested: "a confidential HR conversation"
  - id: gl.tone.passive_aggressive
    title: Passive-aggressive escalation cues
    category: directness
    severity: medium
    tags: [passive-aggressive, escalation, reminder, friction]
    do:
      - "State what you need, by when, and why it matters."
      - "Assume good intent in reminders."
    avoid:
      - "Pointed reminders that imply the recipient is careless."
      - "Repeating 'as I said' in a thread."
    preferred: ["Could you confirm the figures by Thursday so finance can close the month?"]
    flagged:
      - pattern: "per my last email"
        why: "Reads as a pointed rebuke even when the frustration is justified."
        severity: medium
        suggested: "to add to my earlier note"
      - pattern: "as I already said"
        why: "Implies the recipient was not listening."
        severity: medium
        suggested: "to restate the key point"
      - pattern: "as previously stated"
        why: "Formal phrasing that can read as cold escalation."
        severity: medium
        suggested: "as we agreed earlier"
      - pattern: "any update on this"
        why: "Can read as pressure when no deadline was set."
        severity: medium
        suggested: "when you have a moment, could you share where this stands?"
  - id: gl.clarity.plain_language
    title: Plain language and one clear ask
    category: directness
    severity: low
    tags: [clarity, structure, ask, brevity]
    do:
      - "Lead with the ask, then the context."
      - "Use one call to action per message and a concrete deadline."
      - "Keep sentences short and name the owner."
    avoid:
      - "Three requests buried in a long paragraph."
      - "Vague deadlines such as 'soon' or 'asap'."
    preferred: ["Could you review section 2 by Thursday 14:00 CET? I need it for the board pack."]
---

## gl.rudeness.insults

### Guidance
Contempt toward a person is read as hostile across every seeded region. Flag the behaviour, not the
human: describe what happened, why it matters, and what would fix it. Personal labels escalate
conflict and are the single most common cause of an email that cannot be walked back.

## gl.sensitivity.legal_hr

### Guidance
Termination, discipline, allegations and legal threats are high-stakes content. They should leave
the drafting tool only through a private, documented channel with HR or legal review. A group
thread, a chat message or a meeting caption is never the right venue.

## gl.tone.passive_aggressive

### Guidance
Pointed reminders signal frustration while pretending to be neutral, and they tend to escalate
threads. Say what is needed, by when, and why - the recipient can act on that; they cannot act on
implied blame.

## gl.clarity.plain_language

### Guidance
A message with one ask and one deadline gets answered. Burying three requests in a paragraph, or
using 'asap' without a date, reliably produces delays in every region.
