---
okf: "1.0"
kind: culture-profile
region: US
region_name: United States
languages: [en]
last_reviewed: 2026-01-15
caveat: "Common US business norms. Region, industry and company size change this a lot."
provenance:
  type: seed
  confidence: editorial
  sources:
    - "Seed profile written for this project; general business-etiquette literature, not a primary source."
entries:
  - id: us.greeting
    title: Friendly, first-name openings
    category: greeting
    severity: low
    tags: [greeting, first name, hi, friendly, opening]
    do:
      - "Open with 'Hi Sam,' or 'Hello Sam,' and get to the point quickly."
      - "Use first names for peers and most colleagues."
      - "Add one warm sentence, then the ask."
    avoid:
      - "Heavy formality such as 'Dear Sir/Madam' with a colleague."
      - "Long preambles before the request."
    preferred: ["Hi Sam,", "Thanks for the quick turnaround, Sam.", "Quick one - could you approve the invoice?"]
    flagged:
      - pattern: "to whom it may concern"
        why: "Impersonal to the point of feeling like a complaint template."
        severity: low
        suggested: "Hi Sam,"
      - pattern: "dear sir/madam"
        why: "Overly formal for most US colleagues; use a name."
        severity: low
        suggested: "Hi Sam,"
  - id: us.formality
    title: Low formality, high clarity
    category: formality
    severity: low
    tags: [formality, casual, titles, first name, plain language]
    do:
      - "Prefer plain, direct sentences and contractions."
      - "Use titles only for senior external contacts, doctors or officials."
    avoid:
      - "Honorific stacking (Mr. Dr. Smith)."
      - "Bureaucratic phrasing that hides the ask."
    preferred: ["Can you send the deck by Thursday?", "I need your sign-off by 3 pm ET."]
    flagged:
      - pattern: "kindly do the needful"
        why: "Reads as an unfamiliar bureaucratic template in US business writing."
        severity: low
        suggested: "please send the signed form"
  - id: us.directness
    title: Direct but positive framing
    category: directness
    severity: low
    tags: [direct, positive, feedback, ask, clarity]
    do:
      - "State the ask in the first two sentences."
      - "Pair a problem with a proposed next step."
      - "Use 'I' statements for disagreement."
    avoid:
      - "Pointed escalation language in reminders."
      - "Passive-aggressive openers."
    preferred: ["I need two changes before we ship: X and Y.", "I see it differently - here's why."]
    flagged:
      - pattern: "per my last email"
        why: "Widely read as a pointed rebuke, even when frustration is justified."
        severity: medium
        suggested: "following up on my note from Tuesday"
      - pattern: "as you should know"
        why: "Condescending; it questions the recipient's competence."
        severity: high
        suggested: "for context"
  - id: us.humor
    title: Light humour, low risk
    category: humor
    severity: low
    tags: [humor, casual, jokes, sports, pop culture]
    do:
      - "Keep humour light and self-directed."
      - "Use sports and pop-culture references only when shared."
    avoid:
      - "Jokes about protected characteristics, politics or appearance."
      - "Sarcasm in written escalation threads."
    preferred: ["My calendar is doing its best impression of a subway map.", "Happy to take this one - I owe you a coffee."]
    flagged:
      - pattern: "that's what she said"
        why: "Reads as inappropriate in a professional thread."
        severity: high
        suggested: "good point"
  - id: us.taboo
    title: Topics to avoid
    category: taboo
    severity: high
    tags: [taboo, politics, religion, salary, health, age]
    do:
      - "Keep small talk on weekend plans, sport, weather and streaming shows."
    avoid:
      - "Politics, religion, salary, age, health and appearance."
      - "Comments about accent or immigration status."
    preferred: ["Any plans for the weekend?", "Did you catch the game?"]
    flagged:
      - pattern: "how old are you"
        why: "Age is a protected characteristic and a risky question."
        severity: high
        suggested: "how long have you been in the role"
      - pattern: "you look tired"
        why: "Comments on appearance and health are inappropriate and often discriminatory."
        severity: high
        suggested: "how is the workload this week"
  - id: us.hierarchy
    title: Flat hierarchy, owner-driven decisions
    category: hierarchy
    severity: low
    tags: [hierarchy, decision_making, ownership, escalation, autonomy]
    do:
      - "Name the decision owner and the deadline."
      - "Give people autonomy and ask for input before the decision is made."
    avoid:
      - "Waiting for consensus when an owner can decide."
      - "Threatening to escalate as leverage."
    preferred: ["You're the owner here - what do you need from me?", "Let's decide by Thursday with input from finance."]
    flagged:
      - pattern: "i'll go over your head"
        why: "A threat that damages the working relationship; ask for a decision path instead."
        severity: high
        suggested: "can we agree who makes the final call"
      - pattern: "let's form a committee"
        why: "Reads as avoiding ownership; name a decision maker."
        severity: low
        suggested: "let's assign an owner and decide by Thursday"
  - id: us.punctuality
    title: Calendar discipline
    category: punctuality
    severity: medium
    tags: [punctuality, calendar, deadline, meetings, timezone]
    do:
      - "Start and end on time and send an agenda."
      - "Include the time zone in deadlines (ET, PT, UTC)."
    avoid:
      - "Overrunning a 30-minute slot."
      - "Double-booking someone without asking."
    preferred: ["Let's keep this to 25 minutes.", "Due Thursday 5 pm ET."]
    flagged:
      - pattern: "asap"
        why: "Urgency without a date creates churn; give a concrete time."
        severity: medium
        suggested: "by Thursday 5 pm ET"
      - pattern: "quick call?"
        why: "Without an agenda or time it reads as an interruption."
        severity: low
        suggested: "10 minutes Thursday to align on the launch date?"
  - id: us.feedback
    title: Feedback sandwich, specific and kind
    category: feedback
    severity: low
    tags: [feedback, positive, sandwich, specific, growth]
    do:
      - "Lead with what worked, then the specific change, then support."
      - "Be concrete and focus on behaviour and impact."
    avoid:
      - "Blunt character judgements."
      - "Feedback with no example attached."
    preferred: ["The structure works well. The one change I'd make is X, because Y.", "Here's what I'd try next time."]
    flagged:
      - pattern: "you're wrong"
        why: "Blunt and person-focused; describe the gap instead."
        severity: medium
        suggested: "I read the data differently - here's the number I have"
      - pattern: "this is bad"
        why: "Unspecific and demoralising; name what to change."
        severity: medium
        suggested: "the intro buries the ask; let's lead with it"
  - id: us.small_talk
    title: Quick, friendly small talk
    category: small_talk
    severity: low
    tags: [small_talk, weekend, sports, weather, streaming]
    do:
      - "Open with a short, positive question and move on."
      - "Weekend plans, sport, weather and shows are safe."
    avoid:
      - "Long personal conversations in a first contact."
      - "Politics and health."
    preferred: ["How's your week going?", "Any fun plans for the long weekend?"]
---

## us.greeting

### Guidance
US business writing is friendly and fast: a first name, one warm sentence, then the ask. Heavy
formality with a colleague reads as distance or as a template.

## us.formality

### Guidance
Plain language and contractions are the norm. Titles are reserved for senior external contacts,
doctors and officials; bureaucratic phrasing hides the ask and slows the reply.

## us.directness

### Guidance
Be direct, but keep it positive and solution-shaped. Pointed escalation language and
passive-aggressive reminders are read as hostility even when they are technically polite.

## us.humor

### Guidance
Light, self-directed humour is welcome. Jokes about protected characteristics, politics or
appearance are not, and sexual innuendo in a work thread is a serious risk.

## us.taboo

### Guidance
Politics, religion, salary, age, health and appearance are the classic no-go areas, along with
comments about accent or immigration status. Weekend plans, sport and weather are safe.

## us.hierarchy

### Guidance
Hierarchies are flat and ownership matters more than title. Name a decision owner and a date rather
than waiting for consensus; escalating over someone's head as leverage damages trust.

## us.punctuality

### Guidance
Calendars are tight: start and end on time, send an agenda, and put a time zone on every deadline.
'Asap' is treated as vague pressure.

## us.feedback

### Guidance
Specific, kind and behaviour-focused. Lead with what worked, name the one change, and offer support;
character judgements land badly.

## us.small_talk

### Guidance
Short and friendly: weekend plans, sport, weather, shows. Keep it brief and move to the ask.
