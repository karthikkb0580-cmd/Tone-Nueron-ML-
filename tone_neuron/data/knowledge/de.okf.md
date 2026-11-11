---
okf: "1.0"
kind: culture-profile
region: DE
region_name: Germany
languages: [de]
last_reviewed: 2026-01-15
caveat: "Common German business norms. Start-ups, agencies and international teams often differ."
provenance:
  type: seed
  confidence: editorial
  sources:
    - "Seed profile written for this project; general business-etiquette literature, not a primary source."
entries:
  - id: de.greeting
    title: Formal openings and introductions
    category: greeting
    severity: medium
    tags: [greeting, guten_tag, sie, introduction, handshake]
    do:
      - "Open with 'Sehr geehrte Frau Müller' or 'Sehr geehrter Herr Müller' in formal mail."
      - "Use 'Guten Tag' in writing and a handshake in person."
      - "Introduce yourself with role and company on first contact."
    avoid:
      - "Starting with 'Hey' or a first name before the relationship is established."
      - "Over-friendly openers that delay the point."
    preferred: ["Sehr geehrte Frau Müller,", "Guten Tag Herr Weber,", "vielen Dank für Ihre Rückmeldung."]
    flagged:
      - pattern: "hey"
        why: "Too informal for a first or external contact in most German offices."
        severity: medium
        suggested: "Guten Tag Herr Weber,"
      - pattern: "dear friend"
        why: "Reads as insincere in a business context; use a title and surname."
        severity: low
        suggested: "Sehr geehrte Frau Müller,"
  - id: de.formality
    title: Sie, du and titles
    category: formality
    severity: high
    tags: [sie, du, titles, doctor, professor, formality, distance]
    do:
      - "Use Sie with colleagues you do not know well and with all external contacts."
      - "Keep academic titles: Frau Dr. Schmidt, Herr Professor Weber."
      - "Wait to be offered 'du' before switching."
    avoid:
      - "Switching to du without an explicit offer."
      - "Dropping a doctoral title in writing."
    preferred: ["Frau Dr. Schmidt", "Herr Professor Weber", "Würden Sie mir bitte bis Freitag antworten?"]
    flagged:
      - pattern: "dear first name"
        why: "First-name address without an invitation breaks the Sie/du boundary."
        severity: medium
        suggested: "Sehr geehrte Frau Dr. Schmidt,"
  - id: de.directness
    title: Direct, fact-based disagreement
    category: directness
    severity: low
    tags: [direct, facts, disagreement, clarity, criticism]
    do:
      - "State your position, then the evidence, then the proposed fix."
      - "Disagree explicitly and impersonally: 'Die Zahlen passen nicht, weil...'"
      - "Separate the issue from the person."
    avoid:
      - "Hedging so heavily that the point disappears."
      - "Reading direct criticism as a personal attack."
    preferred: ["Ich sehe das anders, und zwar aus folgendem Grund:", "Die Zahlen passen nicht zu Anlage 2."]
    flagged:
      - pattern: "just a small suggestion maybe"
        why: "Excessive hedging obscures the ask and reads as unclear."
        severity: low
        suggested: "I suggest we change X because Y"
      - pattern: "with all due respect"
        why: "Reads as dismissive escalation rather than constructive disagreement."
        severity: medium
        suggested: "I disagree on this point, because"
  - id: de.humor
    title: Dry humour and understatement
    category: humor
    severity: low
    tags: [humor, dry, irony, sarcasm, understatement]
    do:
      - "Keep humour dry, brief and work-adjacent."
      - "Use understatement rather than exclamation."
    avoid:
      - "Hype, superlatives and motivational language in written communication."
      - "Jokes that mock a colleague's work."
    preferred: ["Das lief besser als befürchtet.", "Kurz gesagt: es funktioniert."]
    flagged:
      - pattern: "awesome!!!"
        why: "Over-enthusiastic punctuation reads as unserious in German business mail."
        severity: low
        suggested: "Das Ergebnis überzeugt."
      - pattern: "let's crush it"
        why: "Motivational hype translates poorly; be concrete."
        severity: low
        suggested: "let us finish the remaining two items by Friday"
  - id: de.taboo
    title: Topics to avoid
    category: taboo
    severity: high
    tags: [taboo, politics, history, salary, privacy, health]
    do:
      - "Keep small talk on weather, travel, sport, food and work."
    avoid:
      - "Nazi-era history, war and party politics."
      - "Salary, health, religion and personal finances."
      - "Efficiency stereotypes about German colleagues."
    preferred: ["Wie war Ihr Wochenende?", "Sind Sie im Urlaub gewesen?"]
    flagged:
      - pattern: "how much do you earn"
        why: "Income is private and asking is a high-risk intrusion."
        severity: high
        suggested: "what is the budget for this role"
      - pattern: "nazi"
        why: "Historical references are inflammatory and never workplace small talk."
        severity: high
        suggested: "the historical context"
  - id: de.hierarchy
    title: Flat hierarchy, documented decisions
    category: hierarchy
    severity: medium
    tags: [hierarchy, decision_making, documentation, process, escalation, titles]
    do:
      - "Argue the case with data; hierarchy does not settle a factual question."
      - "Write decisions down, with owner, date and next step."
      - "Escalate factually when a decision is blocked."
    avoid:
      - "Pulling rank instead of making an argument."
      - "Vague verbal agreements with no written follow-up."
    preferred: ["Wir halten fest: Owner ist Frau Klein, Frist 6. März.", "Ich schlage vor, wir entscheiden anhand der Testdaten."]
    flagged:
      - pattern: "because i'm the boss"
        why: "Rank-based arguments are weakly received; justify with facts and impact."
        severity: medium
        suggested: "because the client contract requires it"
      - pattern: "let's decide later"
        why: "Unclear commitments create rework; agree an owner and a date."
        severity: low
        suggested: "let us set an owner and decide by Thursday"
  - id: de.punctuality
    title: Punctuality and scheduling
    category: punctuality
    severity: medium
    tags: [punctuality, calendar, deadline, agenda, meetings]
    do:
      - "Start and end on the minute; arrive early."
      - "Send an agenda and materials in advance."
      - "Give a dated deadline with a time zone."
    avoid:
      - "Open-ended 'asap' requests."
      - "Booking over lunch or after-hours without asking."
    preferred: ["Bitte bis Freitag, 6. März, 17:00 CET.", "Die Agenda sende ich vorab zu."]
    flagged:
      - pattern: "asap"
        why: "Urgency without a date is seen as poor planning; name the deadline."
        severity: medium
        suggested: "by Friday 6 March, 17:00 CET"
      - pattern: "sorry i'm late"
        why: "Lateness is noticed as unreliability; give notice and a new time."
        severity: low
        suggested: "I am delayed by 10 minutes and will send the update beforehand"
  - id: de.feedback
    title: Direct feedback, separated from the person
    category: feedback
    severity: medium
    tags: [feedback, direct, criticism, private, facts, improvement]
    do:
      - "Be specific and prompt: what happened, the impact, the expected change."
      - "Deliver criticism privately but without a long cushion."
    avoid:
      - "Public shaming; directness is not the same as an audience."
      - "Vague praise that hides a real problem."
    preferred: ["Die Präsentation war sachlich gut, aber die Folie 4 enthält einen Rechenfehler.", "Bitte korrigieren Sie bis morgen."]
    flagged:
      - pattern: "you are not a team player"
        why: "Character judgement without evidence; describe the behaviour instead."
        severity: high
        suggested: "the handover did not include the open items"
      - pattern: "maybe you could possibly"
        why: "Triple hedging hides the request; say what you need."
        severity: low
        suggested: "please revise section 2 by Thursday"
  - id: de.small_talk
    title: Brief, work-adjacent small talk
    category: small_talk
    severity: low
    tags: [small_talk, weather, sport, travel, weekend, brevity]
    do:
      - "Keep the warm-up to a sentence or two, then get to the point."
      - "Weather, weekend plans, football and travel are safe."
    avoid:
      - "Long personal conversations before business."
      - "Questions about family planning or health."
    preferred: ["Schönes Wochenende gehabt?", "Wie war der Urlaub?"]
---

## de.greeting

### Guidance
German business mail opens with a formal salutation and moves quickly to the point. 'Sehr geehrte
Frau Müller' for a first contact, 'Guten Tag Herr Weber' once the relationship exists, and a
handshake in person.

## de.formality

### Guidance
Sie is the default until 'du' is explicitly offered, including between colleagues who work together
daily. Academic titles are part of the name and are kept in writing.

## de.directness

### Guidance
Directness is a courtesy here: state the position, the evidence and the fix. Disagreement is
explicit but impersonal. Heavy hedging makes the message harder to act on.

## de.humor

### Guidance
Humour is dry and understated. Superlatives, exclamation marks and motivational slogans read as
unserious in business writing, especially to external partners.

## de.taboo

### Guidance
Nazi-era history, war, party politics, salary, health and religion stay out of workplace
conversation. Weather, travel, sport and food are safe.

## de.hierarchy

### Guidance
Hierarchies are relatively flat for factual debate, but decisions are expected to be documented with
an owner and a date. Rank alone rarely wins an argument; data does.

## de.punctuality

### Guidance
Meetings start and end on time, agendas are shared beforehand, and deadlines are dated. 'Asap'
signals poor planning rather than urgency.

## de.feedback

### Guidance
Feedback is direct, specific and prompt, and it is about the work rather than the person. Directness
does not require an audience: criticism is still delivered privately.

## de.small_talk

### Guidance
A sentence or two of warm-up, then business. Weather, weekend plans, football and travel are
reliable; family planning and health are not.
