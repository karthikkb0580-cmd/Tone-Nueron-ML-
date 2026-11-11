---
okf: "1.0"
kind: culture-profile
region: BR
region_name: Brazil
languages: [pt-BR]
last_reviewed: 2026-01-15
caveat: "Common Brazilian business norms. São Paulo, Rio and the Nordeste differ noticeably."
provenance:
  type: seed
  confidence: editorial
  sources:
    - "Seed profile written for this project; general business-etiquette literature, not a primary source."
entries:
  - id: br.greeting
    title: Warm openers
    category: greeting
    severity: low
    tags: [greeting, ola, warmth, relationship, bom_dia]
    do:
      - "Open with a warm greeting: Olá, Bom dia, or a friendly first-name address."
      - "Spend a line on the relationship before the business point."
    avoid:
      - "Cold, template-like openers with no human line."
      - "Getting straight to a demand with no greeting."
    preferred: ["Olá, Ana, tudo bem?", "Bom dia! Como foi o fim de semana?"]
    flagged:
      - pattern: "to whom it may concern"
        why: "Impersonal and cold in a relationship-driven culture."
        severity: medium
        suggested: "Olá, Ana, tudo bem?"
  - id: br.formality
    title: First names with respect
    category: formality
    severity: low
    tags: [formality, first name, voce, senhor, titles]
    do:
      - "Use first names with peers; use senhor/senhora and titles with much older or senior contacts."
      - "Mirror the formality the other side uses."
    avoid:
      - "Excessive formality that creates distance with a peer."
      - "Assuming instant intimacy with a senior contact."
    preferred: ["Oi, Ana, tudo bem?", "Bom dia, Sr. Ferreira."]
    flagged:
      - pattern: "dear sir"
        why: "Stiff for Brazilian peers; a warm first-name opening lands better."
        severity: low
        suggested: "Olá, Ana,"
  - id: br.directness
    title: Relationship first, then directness
    category: directness
    severity: medium
    tags: [relationship, indirect, face, harmony, request]
    do:
      - "Build the relationship before pushing a hard ask."
      - "Wrap criticism in warmth and offer to help fix it."
    avoid:
      - "Cold, transactional messages with no relationship context."
      - "Correcting a colleague in front of the team."
    preferred: ["Consegue me ajudar com isso até quinta?", "Vamos resolver juntos."]
    flagged:
      - pattern: "that's wrong"
        why: "Blunt contradiction can read as personal; soften and ask about the data."
        severity: medium
        suggested: "acho que os números podem estar diferentes"
      - pattern: "i don't care"
        why: "Reads as dismissive and damages the relationship."
        severity: high
        suggested: "let us focus on the part that affects the deadline"
  - id: br.humor
    title: Playful humour and teasing
    category: humor
    severity: low
    tags: [humor, playful, teasing, football, warmth]
    do:
      - "Use light teasing and football banter once a relationship exists."
    avoid:
      - "Jokes about competence, salary or regional stereotypes."
      - "Sarcasm in a written escalation thread."
    preferred: ["Vamos torcer para o trânsito colaborar hoje.", "Time tá animado hoje!"]
    flagged:
      - pattern: "your english is"
        why: "Commenting on language ability reads as a status attack."
        severity: high
        suggested: "could you clarify this part for me"
  - id: br.taboo
    title: Topics to avoid
    category: taboo
    severity: high
    tags: [taboo, politics, corruption, salary, football, inequality]
    do:
      - "Keep small talk on family, football, food and the weekend."
    avoid:
      - "Party politics, corruption and inequality."
      - "Salary, religion and insults about someone's football team."
    preferred: ["Como foi o fim de semana?", "Alguma novidade na família?"]
    flagged:
      - pattern: "how much do you earn"
        why: "Income is private and asking is a high-risk intrusion."
        severity: high
        suggested: "what is the budget for this project"
      - pattern: "corruption"
        why: "Politically loaded and unsafe at work."
        severity: high
        suggested: "the compliance process"
  - id: br.hierarchy
    title: Friendly hierarchy, flexible decisions
    category: hierarchy
    severity: low
    tags: [hierarchy, decision_making, relationship, flexibility, seniority]
    do:
      - "Respect seniority while keeping the tone warm."
      - "Expect decisions to shift as relationships and priorities shift."
    avoid:
      - "Publicly contradicting a senior."
      - "Treating a verbal agreement as final without a written follow-up."
    preferred: ["Vou alinhar com a diretoria e retorno.", "Podemos confirmar por escrito?"]
    flagged:
      - pattern: "i'll go over your head"
        why: "Escalation threats damage the relationship that decisions depend on."
        severity: high
        suggested: "could we agree who signs this off"
  - id: br.punctuality
    title: Flexible time, real deadlines
    category: punctuality
    severity: low
    tags: [punctuality, meetings, flexibility, deadline, relationships]
    do:
      - "Confirm times the day before and allow a relaxed start."
      - "Still give exact dates for hard deadlines."
    avoid:
      - "Scolding people for small delays."
      - "Assuming a soft 'amanhã' means a firm date."
    preferred: ["Podemos marcar para quinta às 15h?", "Confirmo até amanhã sem falta."]
    flagged:
      - pattern: "you are late"
        why: "Public scolding over small delays damages the relationship; address it privately."
        severity: medium
        suggested: "vamos começar em 10 minutos para todos chegarem"
  - id: br.feedback
    title: Warm, private feedback
    category: feedback
    severity: medium
    tags: [feedback, warm, private, face, suggestion]
    do:
      - "Give feedback privately, warmly and with a concrete suggestion."
      - "Acknowledge what worked before the change."
    avoid:
      - "Public criticism, which costs face and damages trust."
    preferred: ["Ficou muito bom! Só ajustaria esta parte, o que acha?", "Vamos revisar juntos?"]
    flagged:
      - pattern: "you failed"
        why: "Person-level blame; keep it about the deliverable."
        severity: high
        suggested: "o prazo não foi cumprido; o que ajudaria na próxima?"
      - pattern: "this is unacceptable"
        why: "Confrontational in writing; name the gap and propose a fix."
        severity: medium
        suggested: "isso ainda não atende ao briefing porque"
  - id: br.small_talk
    title: Family, football and food
    category: small_talk
    severity: low
    tags: [small_talk, family, football, food, weekend]
    do:
      - "Ask about family, football, food and the weekend."
      - "Share something personal back; warmth is reciprocal."
    avoid:
      - "Politics, corruption and money."
    preferred: ["Como está a família?", "Vai ver o jogo no fim de semana?"]
---

## br.greeting

### Guidance
Brazilian business messages open warmly, often with the person's first name and a genuine question.
The relationship line is not small talk; it is the reason the request will be answered.

## br.formality

### Guidance
First names are normal between peers, with senhor/senhora and titles for much older or senior
contacts. Mirror the other side's level of formality rather than defaulting to either extreme.

## br.directness

### Guidance
Warmth and directness coexist: build the relationship, then be clear about the ask. Blunt
contradiction reads as personal, and public correction costs face.

## br.humor

### Guidance
Playful teasing and football banter build rapport once a relationship exists. Jokes about
competence, money or regional stereotypes do not, and language comments read as attacks.

## br.taboo

### Guidance
Party politics, corruption, inequality, salary and religion are unsafe. Family, football, food and
the weekend are reliable and expected.

## br.hierarchy

### Guidance
Hierarchy is real but friendly, and decisions can shift with relationships and priorities. Respect
seniority, and confirm verbal agreements in writing.

## br.punctuality

### Guidance
Social flexibility around start times coexists with hard business deadlines. Confirm times the day
before, allow a relaxed start, but keep exact dates for deliverables.

## br.feedback

### Guidance
Feedback is private, warm and specific, with the relationship protected. Public criticism is the
main thing to avoid.

## br.small_talk

### Guidance
Family, football, food and the weekend are the standard openers, and warmth is expected to be
reciprocal.
