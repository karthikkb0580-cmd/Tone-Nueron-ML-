---
okf: "1.0"
kind: culture-profile
region: AE
region_name: United Arab Emirates
languages: [ar, en]
last_reviewed: 2026-01-15
caveat: "Common UAE business norms. Emirati, expatriate and free-zone offices differ substantially."
provenance:
  type: seed
  confidence: editorial
  sources:
    - "Seed profile written for this project; general business-etiquette literature, not a primary source."
entries:
  - id: ae.greeting
    title: Salaam and the order of greetings
    category: greeting
    severity: medium
    tags: [greeting, salaam, handshake, respect, introduction]
    do:
      - "Open with As-salaam alaikum and reply Wa alaikum as-salaam when greeted that way."
      - "Greet the most senior person first and take time with the greeting."
      - "Offer a handshake to a man; wait for a woman to offer hers first."
    avoid:
      - "Rushing past the greeting into business."
      - "Physical contact with someone of the opposite gender who has not offered it."
    preferred: ["As-salaam alaikum,", "Good morning, Mr Al Mansoori."]
    flagged:
      - pattern: "hey"
        why: "Too casual for a first or senior contact in the Gulf."
        severity: medium
        suggested: "As-salaam alaikum,"
      - pattern: "what's up"
        why: "Reads as unserious in a formal business context."
        severity: low
        suggested: "I hope you are well."
  - id: ae.formality
    title: Titles, family names and formality
    category: formality
    severity: medium
    tags: [titles, sheikh, engineer, doctor, family name, formality]
    do:
      - "Use titles and family names: Mr Al Mansoori, Dr Haddad, Eng. Khalid."
      - "Keep a formal register in external mail even after friendly meetings."
    avoid:
      - "First names with Emirati senior contacts unless invited."
      - "Abbreviating or mispronouncing family names."
    preferred: ["Dear Mr Al Mansoori,", "Dr Haddad,"]
    flagged:
      - pattern: "dear first name"
        why: "First-name address without an invitation is too familiar for most Gulf business contacts."
        severity: medium
        suggested: "Dear Mr Al Mansoori,"
  - id: ae.directness
    title: Polite indirectness and face
    category: directness
    severity: medium
    tags: [indirect, face, polite, refusal, harmony]
    do:
      - "Soften disagreement and frame requests around the relationship."
      - "Use 'let us look into it' and confirm privately."
    avoid:
      - "Blunt criticism in a group, especially of a senior."
      - "Treating a polite deferral as agreement."
    preferred: ["We will review this and revert to you.", "Perhaps we could consider another option."]
    flagged:
      - pattern: "that's wrong"
        why: "Blunt contradiction costs face in a group setting."
        severity: medium
        suggested: "we may want to double-check this point"
      - pattern: "you don't understand"
        why: "Directly questioning someone's understanding is a face threat."
        severity: high
        suggested: "let me add some context"
  - id: ae.humor
    title: Warm humour, no religious jokes
    category: humor
    severity: medium
    tags: [humor, religion, politics, warmth, jokes]
    do:
      - "Use warm, gentle humour and hospitality themes."
      - "Compliment the food, the city or the project."
    avoid:
      - "Jokes about religion, politics or family honour."
      - "Sarcasm about someone's competence."
    preferred: ["The hospitality here is always a pleasure.", "We are looking forward to working together."]
    flagged:
      - pattern: "your english is"
        why: "Reads as a status attack rather than a compliment."
        severity: high
        suggested: "could you clarify this part for me"
  - id: ae.taboo
    title: Topics to avoid
    category: taboo
    severity: high
    tags: [taboo, religion, politics, ramadan, alcohol, family]
    do:
      - "Keep small talk on family in general terms, travel, food and business."
    avoid:
      - "Religion, politics, Israel-Palestine and comments on regional policy."
      - "Questions about someone's wife or daughters."
      - "Offering alcohol or scheduling lunches during Ramadan fasting hours."
    preferred: ["How is your family?", "How was the holiday?"]
    flagged:
      - pattern: "how is your wife"
        why: "Questions about a colleague's wife or female family members are intrusive."
        severity: high
        suggested: "how is your family"
      - pattern: "let's grab a beer"
        why: "Alcohol-based social invitations exclude and can offend in the Gulf."
        severity: high
        suggested: "let us grab a coffee"
      - pattern: "israel"
        why: "Politically charged and unsafe in a business thread."
        severity: high
        suggested: "the regional offices"
  - id: ae.hierarchy
    title: Seniority, consensus and relationship decisions
    category: hierarchy
    severity: medium
    tags: [hierarchy, decision_making, seniority, consensus, relationship]
    do:
      - "Route proposals through the most senior decision maker and their trusted contact."
      - "Invest in the relationship before expecting a decision."
    avoid:
      - "Bypassing the person who owns the relationship."
      - "Demanding a decision in the first meeting."
    preferred: ["We would appreciate your guidance on the next step.", "We will follow up through Ahmed."]
    flagged:
      - pattern: "decide now"
        why: "Decisions follow relationship and senior approval; an on-the-spot demand pressures the contact."
        severity: medium
        suggested: "could we aim to align by next week"
      - pattern: "i'll escalate"
        why: "Escalation framing strains the relationship the deal depends on."
        severity: medium
        suggested: "could we seek leadership guidance"
  - id: ae.punctuality
    title: Meeting rhythm and Ramadan scheduling
    category: punctuality
    severity: low
    tags: [punctuality, meetings, ramadan, deadlines, scheduling]
    do:
      - "Arrive on time as the visitor, and allow the host a flexible start."
      - "Avoid scheduling around prayer times and adjust hours during Ramadan."
      - "Confirm deadlines with a date and a written recap."
    avoid:
      - "Aggressive reminders about a few minutes of delay."
      - "Booking back-to-back meetings across the city without travel time."
    preferred: ["Would 10 am on Thursday work for you?", "We can adjust after iftar during Ramadan."]
    flagged:
      - pattern: "asap"
        why: "Vague urgency ignores approval and scheduling rhythms; give a date."
        severity: medium
        suggested: "by Thursday 12 March"
      - pattern: "you are late"
        why: "Public scolding over timing damages the relationship; adapt privately."
        severity: medium
        suggested: "we can start when you are ready"
  - id: ae.feedback
    title: Private, face-saving feedback
    category: feedback
    severity: medium
    tags: [feedback, private, face, indirect, suggestion]
    do:
      - "Give feedback privately, one-to-one, framed as an improvement idea."
      - "Praise publicly, correct privately."
    avoid:
      - "Criticism in front of the team or in a group email."
      - "Written criticism that can be forwarded."
    preferred: ["One idea that might strengthen this is...", "We are grateful for the work; may we suggest one adjustment?"]
    flagged:
      - pattern: "you failed"
        why: "Person-level blame in writing is a serious face violation."
        severity: high
        suggested: "the deliverable missed the date; what support would help"
      - pattern: "this is unacceptable"
        why: "Confrontational in writing; state the gap and propose a next step."
        severity: medium
        suggested: "this does not yet meet the brief because"
  - id: ae.small_talk
    title: Hospitality and family warmth
    category: small_talk
    severity: low
    tags: [small_talk, family, hospitality, travel, coffee]
    do:
      - "Ask about family in general terms, travel and food."
      - "Accept coffee or dates when offered; it is part of the welcome."
    avoid:
      - "Probing questions about female relatives or religion."
    preferred: ["How is your family?", "The coffee here is excellent - thank you."]
---

## ae.greeting

### Guidance
Greetings carry the relationship: As-salaam alaikum, a warm handshake from the same gender, and
greeting the most senior person first. Rushing into business signals that the person does not matter.

## ae.formality

### Guidance
Titles and family names are the safe default, and external mail stays formal even after a warm
meeting. Wait to be invited before using first names.

## ae.directness

### Guidance
Disagreement is softened and face is protected, especially in groups. 'We will review it' is a
deferral, not an agreement; confirm privately and in writing.

## ae.humor

### Guidance
Warm, hospitable humour works. Religion, politics and family honour are never joke material, and
comments on someone's English read as a status attack.

## ae.taboo

### Guidance
Religion, politics, Israel-Palestine, alcohol and questions about a colleague's wife or daughters
are off limits. During Ramadan, avoid lunch and coffee invitations during fasting hours.

## ae.hierarchy

### Guidance
Decisions follow senior approval and the trusted relationship owner. Invest in the relationship,
route proposals through the right person, and do not demand a decision in the first meeting.

## ae.punctuality

### Guidance
The visitor arrives on time and the host may start flexibly. Avoid prayer times, shorten hours during
Ramadan, and confirm deadlines with a written recap.

## ae.feedback

### Guidance
Praise publicly, correct privately, and frame correction as an improvement idea. Written criticism
may be forwarded and must still protect face.

## ae.small_talk

### Guidance
General family questions, travel, food and hospitality are the way in. Never probe female relatives
or religion.
