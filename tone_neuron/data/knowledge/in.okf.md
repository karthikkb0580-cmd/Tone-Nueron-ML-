---
okf: "1.0"
kind: culture-profile
region: IN
region_name: India
languages: [en, hi]
last_reviewed: 2026-01-15
caveat: "Common Indian business norms. India is highly diverse; language, state and company culture dominate."
provenance:
  type: seed
  confidence: editorial
  sources:
    - "Seed profile written for this project; general business-etiquette literature, not a primary source."
entries:
  - id: in.greeting
    title: Greetings and openings
    category: greeting
    severity: medium
    tags: [greeting, namaste, sir, madam, opening, respect]
    do:
      - "Open with 'Dear Mr Sharma' or 'Dear Ms Iyer' for a first contact."
      - "Namaste works well in person and in informal written openings."
      - "Ask about the family in a warm, brief way once the relationship exists."
    avoid:
      - "Jumping into business before a short warm opening."
      - "Using a first name for a senior contact without an invitation."
    preferred: ["Dear Mr Sharma,", "Namaste, and thank you for your time.", "Hope you and your family are doing well."]
    flagged:
      - pattern: "hey"
        why: "Reads as too casual for a first or senior contact in most Indian offices."
        severity: medium
        suggested: "Dear Mr Sharma,"
      - pattern: "hi guys"
        why: "Casual group address can read as disrespectful to seniors."
        severity: low
        suggested: "Hello team,"
  - id: in.formality
    title: Titles, seniority and address
    category: formality
    severity: medium
    tags: [titles, sir, madam, ji, surname, seniority]
    do:
      - "Use title + surname for seniors and external contacts (Mr, Ms, Dr)."
      - "Keep 'Sir' or 'Madam' in chat with senior colleagues where the office uses it."
      - "Add -ji to a first name only in informal, relationship-warm contexts."
    avoid:
      - "Dropping titles with a much older or more senior colleague."
      - "Assuming a woman's marital title; use Ms unless told otherwise."
    preferred: ["Dear Sir,", "Ms Iyer,", "Ramesh-ji"]
    flagged:
      - pattern: "mrs."
        why: "Marital title assumptions are risky; Ms is the safe default."
        severity: low
        suggested: "Ms"
  - id: in.directness
    title: Indirect requests and face-saving refusals
    category: directness
    severity: medium
    tags: [indirect, face, needful, request, refusal, polite]
    do:
      - "Wrap requests in a reason and a polite frame."
      - "Signal problems with 'there may be a small challenge' before the detail."
      - "Follow up gently rather than escalating on the first miss."
    avoid:
      - "Flat refusals and public correction."
      - "Reading a polite 'we will try' as a firm commitment."
    preferred: ["Kindly do the needful.", "Request you to please confirm by Friday.", "There may be a small challenge with the timeline."]
    flagged:
      - pattern: "that's wrong"
        why: "Blunt contradiction costs face, especially in front of the team."
        severity: medium
        suggested: "there may be a small gap here"
      - pattern: "you never"
        why: "Absolute accusations escalate; describe the specific instance."
        severity: medium
        suggested: "in the last two handovers, the figures were missing"
  - id: in.humor
    title: Warmth, humour and idioms
    category: humor
    severity: low
    tags: [humor, warmth, idioms, cricket, family]
    do:
      - "Use warm, light humour about traffic, weather, cricket or food."
      - "Let humour follow the relationship, not precede it."
    avoid:
      - "Sarcasm about competence or seniority."
      - "Jokes about caste, religion, region or marriage."
    preferred: ["Traffic was kind to me today, for once.", "Hope the monsoon is not causing too much trouble."]
    flagged:
      - pattern: "your english is"
        why: "Commenting on someone's English reads as a status attack, not a compliment."
        severity: high
        suggested: "could you clarify this sentence for me"
  - id: in.taboo
    title: Topics to avoid
    category: taboo
    severity: high
    tags: [taboo, caste, religion, politics, salary, marriage]
    do:
      - "Stick to work, cricket, food, travel and family in general terms."
    avoid:
      - "Caste, religion, party politics and India-Pakistan commentary."
      - "Salary, marital plans, and jokes about arranged marriage."
    preferred: ["How was the long weekend?", "Did you catch the match last night?"]
    flagged:
      - pattern: "arranged marriage"
        why: "Personal and culturally loaded; not workplace small talk."
        severity: high
        suggested: "your weekend plans"
      - pattern: "caste"
        why: "Caste is a sensitive social fault line and never appropriate at work."
        severity: high
        suggested: "the team structure"
  - id: in.hierarchy
    title: Seniority and decision-making
    category: hierarchy
    severity: medium
    tags: [hierarchy, seniority, manager, decision_making, approval, escalation]
    do:
      - "Route proposals through the manager who owns the relationship."
      - "Give the most senior person in the room the first and last word."
      - "Expect a senior sign-off even after team-level agreement."
    avoid:
      - "Contradicting a senior colleague in a group thread."
      - "Assuming a team member can approve budget."
    preferred: ["I will seek our manager's approval and revert by Thursday.", "Request your guidance on this."]
    flagged:
      - pattern: "i'll escalate"
        why: "Escalation language is read as a threat; ask for guidance instead."
        severity: medium
        suggested: "could we take your guidance on the next step"
  - id: in.punctuality
    title: Time and meeting expectations
    category: punctuality
    severity: low
    tags: [punctuality, meetings, ist, deadline, flexibility]
    do:
      - "Confirm times with the IST offset and reconfirm the day before."
      - "Plan for a gentle start and a possible overrun in large meetings."
      - "State deadlines as dates, and confirm receipt."
    avoid:
      - "Scolding a team for a five-minute start delay."
      - "Assuming a soft 'by EOD' means midnight."
    preferred: ["Let us target 4 pm IST on Thursday.", "Shall we reconfirm for tomorrow at 11?"]
    flagged:
      - pattern: "you are late"
        why: "Public scolding over small delays damages relationships; address it privately."
        severity: medium
        suggested: "let us restart at 11:10 so everyone can join"
  - id: in.feedback
    title: Feedback and correction
    category: feedback
    severity: medium
    tags: [feedback, private, sandwich, face, suggestion]
    do:
      - "Give feedback privately and start with what worked."
      - "Use 'one small suggestion' framing and an offer to help."
    avoid:
      - "Correcting a colleague in a group chat."
      - "Written criticism that can be forwarded."
    preferred: ["One small suggestion - could we add the source for these numbers?", "This is a good start. May I suggest one change?"]
    flagged:
      - pattern: "you failed"
        why: "Person-level blame in writing; focus on the missed deliverable."
        severity: high
        suggested: "the deliverable missed the date; what support would help"
      - pattern: "this is unacceptable"
        why: "Confrontational in writing and hard to walk back; state the gap instead."
        severity: medium
        suggested: "this does not yet meet the brief because the figures are missing"
  - id: in.small_talk
    title: Small talk that builds trust
    category: small_talk
    severity: low
    tags: [small_talk, family, cricket, food, festival, relationship]
    do:
      - "Ask about family in general terms, festivals and weekend plans."
      - "Mention cricket, food and travel."
    avoid:
      - "Probing questions about marriage, children or income."
    preferred: ["Hope the family is well.", "Any plans for the festival?"]
---

## in.greeting

### Guidance
Indian business email usually opens warmly and with a title. 'Dear Mr Sharma' or 'Sir' for seniors,
Namaste in person or in a warm written opener, and a short personal line before the business ask.

## in.formality

### Guidance
Titles carry respect and seniority matters. Use Mr/Ms/Dr with the surname for first contacts and
seniors, keep 'Sir'/'Madam' where the office uses it, and default to Ms rather than assuming a
marital title.

## in.directness

### Guidance
Requests are usually wrapped in a reason and a polite frame, and problems are signalled before they
are stated bluntly. A polite 'we will try' is not a guarantee; confirm the date and owner.

## in.humor

### Guidance
Warmth comes before wit. Light observations about traffic, weather, cricket or food are safe once a
relationship exists; sarcasm about competence or comments about someone's English are not.

## in.taboo

### Guidance
Caste, religion, party politics and any India-Pakistan commentary are off limits at work, as are
salary, marital plans and arranged-marriage jokes. Cricket, food, festivals and general family
warmth are reliable.

## in.hierarchy

### Guidance
Decisions usually carry a senior sign-off even after the team agrees, and contradicting a senior in
a group thread costs face. Route proposals through the manager who owns the relationship.

## in.punctuality

### Guidance
Times need an explicit IST offset and a reconfirmation. Large meetings may start a little late;
scolding individuals for small delays does more damage than the delay. Deadlines need a date and a
confirmed receipt.

## in.feedback

### Guidance
Feedback is private, starts with what worked, and is framed as a suggestion. Written criticism can
be forwarded, so it should still be respectful if it is.

## in.small_talk

### Guidance
General family questions, festivals, cricket and food build trust quickly. Marriage, children and
income questions feel intrusive.
