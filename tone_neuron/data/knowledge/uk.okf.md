---
okf: "1.0"
kind: culture-profile
region: UK
region_name: United Kingdom
languages: [en-GB]
last_reviewed: 2026-01-15
caveat: "Common UK business norms. Sector and region (London vs elsewhere) shift the tone."
provenance:
  type: seed
  confidence: editorial
  sources:
    - "Seed profile written for this project; general business-etiquette literature, not a primary source."
entries:
  - id: uk.greeting
    title: Openings and the first-name threshold
    category: greeting
    severity: medium
    tags: [greeting, dear, hi, first name, introduction]
    do:
      - "Open with 'Dear Ms Patel' for a first contact, then switch to 'Hi Priya' once she replies that way."
      - "Keep the opening brief and understated."
    avoid:
      - "Instant first names with external or senior contacts."
      - "American-style superlatives in the first line."
    preferred: ["Dear Ms Patel,", "Hi Priya,", "I hope this finds you well."]
    flagged:
      - pattern: "hey"
        why: "Too casual for a first contact in most UK offices."
        severity: medium
        suggested: "Hi Priya,"
      - pattern: "dear friend"
        why: "Reads as a mass-mailing template rather than a real introduction."
        severity: low
        suggested: "Dear Ms Patel,"
  - id: uk.formality
    title: Understatement and indirect formality
    category: formality
    severity: medium
    tags: [formality, understatement, hedging, politeness, titles]
    do:
      - "Use hedged, understated phrasing: 'I wonder if we could...'"
      - "Say 'please' and 'thank you' explicitly, and apologise lightly when needed."
    avoid:
      - "Hype and superlatives ('incredible opportunity', 'awesome')."
      - "Over-familiarity before the relationship exists."
    preferred: ["I wonder if you might have a moment to look at this?", "That would be great, thank you."]
    flagged:
      - pattern: "awesome"
        why: "Reads as over-enthusiastic in UK business writing; understatement lands better."
        severity: low
        suggested: "very helpful"
      - pattern: "reach out"
        why: "Corporate Americanism that some UK readers find grating."
        severity: low
        suggested: "get in touch"
  - id: uk.directness
    title: Softened disagreement
    category: directness
    severity: medium
    tags: [indirect, hedged, disagreement, understatement, polite]
    do:
      - "Soften disagreement with 'I'd push back slightly on...' or 'I'm not sure that quite works'."
      - "Give the reason and offer an alternative in the same breath."
    avoid:
      - "Flat contradiction in group threads."
      - "Reading British understatement as full agreement."
    preferred: ["I'm not sure that quite works, because...", "Could I suggest an alternative?"]
    flagged:
      - pattern: "that's wrong"
        why: "Direct contradiction reads as blunt; hedge and give the reason."
        severity: medium
        suggested: "I'm not sure that's quite right, because"
      - pattern: "with all due respect"
        why: "Widely read as the opposite of respect."
        severity: medium
        suggested: "I see it slightly differently"
  - id: uk.humor
    title: Self-deprecating irony
    category: humor
    severity: low
    tags: [humor, irony, sarcasm, self-deprecation, banter]
    do:
      - "Use light self-deprecation and gentle irony."
      - "Keep banter for relationships that already exist."
    avoid:
      - "Mocking a colleague's work in the name of banter."
      - "Irony in a written escalation where tone is ambiguous."
    preferred: ["My inbox is currently a work of abstract art.", "That went better than my last attempt."]
    flagged:
      - pattern: "just joking"
        why: "Signals the joke did not land; apologise briefly and move on."
        severity: medium
        suggested: "that came out badly - sorry"
  - id: uk.taboo
    title: Topics to avoid
    category: taboo
    severity: high
    tags: [taboo, politics, class, salary, brexit, health]
    do:
      - "Keep small talk on weather, weekend, football and tea."
    avoid:
      - "Party politics, Brexit, class and salary."
      - "Questions about health, age or personal finances."
    preferred: ["Any plans for the weekend?", "Awful weather for the commute."]
    flagged:
      - pattern: "how much do you earn"
        why: "Income is private and asking is a high-risk intrusion."
        severity: high
        suggested: "what band is the role"
      - pattern: "brexit"
        why: "Politically divisive; avoid at work."
        severity: high
        suggested: "the current trading arrangements"
  - id: uk.hierarchy
    title: Informal hierarchy, quiet escalation
    category: hierarchy
    severity: low
    tags: [hierarchy, decision_making, consensus, escalation, meetings]
    do:
      - "Argue on the merits and use 'we' language."
      - "Take contested points offline rather than winning them in the meeting."
    avoid:
      - "Pulling rank or threatening to escalate."
      - "Ambushing a colleague with criticism in a group call."
    preferred: ["Let's take that offline and come back with a proposal.", "We could try X and see how it lands."]
    flagged:
      - pattern: "i'll go over your head"
        why: "Escalation threats are read as a breach of professional courtesy."
        severity: high
        suggested: "could we agree who signs this off"
      - pattern: "because i said so"
        why: "Rank-based authority is weakly received; explain the reasoning."
        severity: medium
        suggested: "because the regulator requires it"
  - id: uk.punctuality
    title: Diary discipline
    category: punctuality
    severity: medium
    tags: [punctuality, calendar, deadline, meetings, agenda]
    do:
      - "Start and end on time; send materials beforehand."
      - "Give a dated deadline and a time zone."
    avoid:
      - "Open-ended 'asap' deadlines."
      - "Booking over lunch without asking."
    preferred: ["Could you get this to me by Thursday 6 March?", "I'll send the agenda this afternoon."]
    flagged:
      - pattern: "asap"
        why: "Vague urgency; UK teams respond better to a dated request."
        severity: medium
        suggested: "by Thursday 6 March"
      - pattern: "circle back"
        why: "Corporate jargon that slows the point."
        severity: low
        suggested: "follow up next week"
  - id: uk.feedback
    title: Softened, private feedback
    category: feedback
    severity: medium
    tags: [feedback, soft, private, understatement, sandwich]
    do:
      - "Deliver criticism privately and lightly: 'a couple of small things'."
      - "Pair the issue with a concrete suggestion."
    avoid:
      - "Public correction, even when framed as a joke."
      - "Overloading one message with every issue."
    preferred: ["A couple of small things on slide 3, otherwise it reads well.", "I'd tighten the second paragraph - what do you think?"]
    flagged:
      - pattern: "you failed"
        why: "Person-level blame; UK feedback focuses on the work."
        severity: high
        suggested: "the deadline was missed; what would help next time"
      - pattern: "this is unacceptable"
        why: "Escalatory in writing; state the concrete gap instead."
        severity: medium
        suggested: "this does not yet meet the brief because"
  - id: uk.small_talk
    title: Weather, tea and football
    category: small_talk
    severity: low
    tags: [small_talk, weather, football, tea, weekend]
    do:
      - "Use weather, tea, weekend plans and football as openers."
      - "Keep it short and let the other side lead."
    avoid:
      - "Personal finances, health and politics."
    preferred: ["Terrible weather for the commute.", "Any plans for the weekend?"]
---

## uk.greeting

### Guidance
Formality is a sliding scale: 'Dear Ms Patel' for a first contact, 'Hi Priya' once she signs off that
way. Openings are brief and understated rather than effusive.

## uk.formality

### Guidance
Understatement and hedging carry politeness. Superlatives and heavy corporate Americanisms read as
over-enthusiastic; a light 'I wonder if...' often carries a firm request.

## uk.directness

### Guidance
Disagreement is softened but real: 'I'm not sure that quite works' is a clear objection. Blunt
contradiction and 'with all due respect' land badly.

## uk.humor

### Guidance
Self-deprecating irony is the native register and often signals goodwill. Banter needs an existing
relationship; jokes about someone's work are not banter.

## uk.taboo

### Guidance
Party politics, Brexit, class, salary, health and age stay out of workplace conversation. Weather,
weekend plans, football and tea are the reliable ground.

## uk.hierarchy

### Guidance
Hierarchies are informal but real. Argue on the merits, use 'we', and take contested points offline
rather than winning them in public; escalation threats breach professional courtesy.

## uk.punctuality

### Guidance
Meetings start and end on time with materials sent ahead. Deadlines are dated; 'asap' and jargon
like 'circle back' slow things down.

## uk.feedback

### Guidance
Feedback is private, light and specific. Public correction, even framed as a joke, is remembered.
One or two concrete suggestions work better than a list.

## uk.small_talk

### Guidance
Weather, tea, football and weekend plans are safe and expected. Politics, money and health are not.
