---
okf: "1.0"
kind: culture-profile
region: JP
region_name: Japan
languages: [ja]
last_reviewed: 2026-01-15
caveat: "Common Japanese business norms. Individuals, teams and multinational offices vary widely."
provenance:
  type: seed
  confidence: editorial
  sources:
    - "Seed profile written for this project; general business-etiquette literature, not a primary source."
entries:
  - id: jp.greeting
    title: Opening a Japanese business message
    category: greeting
    severity: medium
    tags: [greeting, opening, bow, osewa, season, acknowledgement]
    do:
      - "Open with お世話になっております (osewa ni natte orimasu) in business threads."
      - "Add a seasonal greeting when it fits, then a one-line self-introduction."
      - "Acknowledge receipt before asking for anything."
    avoid:
      - "Opening with a bare request or a first name only."
      - "Over-familiar openings copied from English email templates."
    preferred: ["お世話になっております。", "いつもお世話になっております。", "田中さん、お疲れさまです。"]
    flagged:
      - pattern: "hey"
        why: "Reads as casual and dismissive in Japanese business writing."
        severity: medium
        suggested: "お世話になっております"
      - pattern: "hi there"
        why: "Too casual for a first or external contact; use a set business greeting."
        severity: medium
        suggested: "田中さん、お世話になっております"
  - id: jp.formality
    title: Honorifics and address form
    category: formality
    severity: high
    tags: [honorifics, san, sama, keigo, address, respect]
    do:
      - "Use surname + さん for colleagues and 様 for customers."
      - "Keep keigo (敬語) in external mail even when the thread becomes friendly."
      - "Use 您-equivalent polite forms and avoid contractions."
    avoid:
      - "First names unless the person has explicitly invited them."
      - "Dropping honorifics mid-thread because the other side did."
      - "Attaching さん to your own name."
    preferred: ["田中さん", "山田様", "恐れ入りますが、ご確認をお願いいたします。"]
    flagged:
      - pattern: "dear tanaka"
        why: "First-name-only address skips the honorific and reads as dismissive."
        severity: medium
        suggested: "田中さん"
      - pattern: "mr. tanaka-san"
        why: "Doubling an English title with a Japanese honorific is a common, noticeable error."
        severity: low
        suggested: "田中さん"
  - id: jp.directness
    title: Indirect refusal and softened disagreement
    category: directness
    severity: medium
    tags: [indirect, refusal, disagreement, face, consider, difficult]
    do:
      - "Use '検討します' (we will consider) or '難しいかもしれません' to signal a soft no."
      - "Frame disagreement as a question about the facts."
      - "Give the reason before the conclusion."
    avoid:
      - "A flat 'no', 'that is wrong' or 'I disagree' in a first message."
      - "Reading a soft no as agreement."
    preferred: ["ご検討いただけますと幸いです。", "この点、いかがでしょうか。", "少し難しいかもしれません。"]
    flagged:
      - pattern: "that's wrong"
        why: "Direct contradiction costs face; reframe as a question about the data."
        severity: medium
        suggested: "could we double-check this point"
      - pattern: "no way"
        why: "Blunt refusal reads as hostile in an indirect-feedback culture."
        severity: medium
        suggested: "this may be difficult under the current schedule"
  - id: jp.humor
    title: Humour and idiom at work
    category: humor
    severity: low
    tags: [humor, sarcasm, idiom, modesty, jokes]
    do:
      - "Prefer gentle, self-deprecating humour and seasonal references."
      - "Keep jokes out of a first contact or a client thread."
    avoid:
      - "Sarcasm and irony aimed at a person or a team."
      - "Jokes about hierarchy, age or working hours."
      - "English idioms that do not translate (e.g. 'ballpark figure')."
    preferred: ["まだまだ勉強中です。", "お恥ずかしい限りです。"]
    flagged:
      - pattern: "ballpark figure"
        why: "Baseball idiom does not translate; state the range instead."
        severity: low
        suggested: "an approximate range"
      - pattern: "no offense"
        why: "Announcing that a comment may offend rarely softens it."
        severity: medium
        suggested: "one point to check"
  - id: jp.taboo
    title: Topics to avoid
    category: taboo
    severity: high
    tags: [taboo, politics, war, religion, salary, privacy]
    do:
      - "Keep small talk to weather, seasons, food, travel and work topics."
      - "Let the other side raise personal topics first."
    avoid:
      - "War history, regional politics and religion."
      - "Salary, family composition, health and age questions."
      - "Jokes about tattoos, nuclear issues or minority groups."
    preferred: ["最近のお天気はいかがですか。", "季節の変わり目ですので、ご自愛ください。"]
    flagged:
      - pattern: "how much do you earn"
        why: "Income is a private matter and a high-risk question in Japan."
        severity: high
        suggested: "what does the budget look like for this project"
      - pattern: "world war"
        why: "War history is politically charged and inappropriate at work."
        severity: high
        suggested: "the project background"
  - id: jp.hierarchy
    title: Hierarchy, nemawashi and consensus decisions
    category: hierarchy
    severity: medium
    tags: [hierarchy, nemawashi, ringi, consensus, decision_making, seniority, escalation]
    do:
      - "Socialise a proposal informally (nemawashi) before the formal meeting."
      - "Address the most senior person last in a group message and with extra formality."
      - "Give the team time to align before asking for a decision."
    avoid:
      - "Bypassing a manager to reach their boss."
      - "Demanding a decision in the meeting itself."
    preferred: ["事前にご相談させていただけますか。", "社内で確認のうえ、改めてご連絡いたします。"]
    flagged:
      - pattern: "decide now"
        why: "Consensus decisions need pre-alignment; an on-the-spot demand reads as pressure."
        severity: medium
        suggested: "could we aim to align by next Tuesday"
      - pattern: "i'll ask your boss"
        why: "Escalating over a manager damages trust in a seniority-based organisation."
        severity: medium
        suggested: "could you help me route this to the right owner"
  - id: jp.punctuality
    title: Time, meetings and deadlines
    category: punctuality
    severity: medium
    tags: [punctuality, meetings, deadline, timing, agenda]
    do:
      - "Arrive five minutes early and start on time."
      - "Send the agenda and materials in advance."
      - "Confirm deadlines explicitly with a date and time."
    avoid:
      - "Open-ended deadlines such as 'asap' or 'when you can'."
      - "Keeping people waiting without a message."
    preferred: ["3月6日（金）17時までにお願いできますか。", "本日はお時間をいただき、ありがとうございます。"]
    flagged:
      - pattern: "asap"
        why: "Urgency without a date reads as inconsiderate; give a concrete deadline."
        severity: medium
        suggested: "by Friday 6 March, 17:00 JST"
      - pattern: "running 10 minutes late"
        why: "Tardiness is noticed; send a short notice with a new time instead."
        severity: low
        suggested: "I will join at 10:10 and send the notes ahead"
  - id: jp.feedback
    title: Giving feedback without public correction
    category: feedback
    severity: medium
    tags: [feedback, criticism, public, private, face, sandwich]
    do:
      - "Give corrective feedback privately and start with the shared goal."
      - "Soften with 'another option might be...' and offer to discuss."
    avoid:
      - "Correcting a senior colleague in front of the team."
      - "Listing mistakes without acknowledging what worked."
    preferred: ["別の方法も一案としてご検討いただけますか。", "ここは非常に助かりました。一点だけ確認させてください。"]
    flagged:
      - pattern: "this is wrong"
        why: "Blunt correction in a group setting costs face."
        severity: medium
        suggested: "could we revisit this section together"
      - pattern: "you failed"
        why: "Person-focused blame rather than work-focused feedback."
        severity: high
        suggested: "the deadline was missed; what would help next time"
  - id: jp.small_talk
    title: Small talk that lands
    category: small_talk
    severity: low
    tags: [small_talk, weather, food, travel, seasons, relationship]
    do:
      - "Use weather, seasons, food and travel as safe openers."
      - "Ask about the region's seasonal highlights."
    avoid:
      - "Interrogating someone about their private life."
      - "Assuming shared hobbies."
    preferred: ["そちらはもう桜が咲きましたか。", "最近、何か美味しいものを召し上がりましたか。"]
---

## jp.greeting

### Guidance
Japanese business email opens with a set phrase before any content. お世話になっております is the
default for colleagues and clients; a seasonal greeting plus a one-line self-introduction works for
a first contact. The acknowledgement comes first, the request second.

## jp.formality

### Guidance
Address form carries the relationship. Surname + さん is the workplace default, 様 for customers and
documents, and keigo stays in place for external mail even after the thread warms up. First names
are an invitation, not a default.

## jp.directness

### Guidance
Refusals and disagreement are usually softened: 'we will consider it' or 'this may be difficult'
often means no. Blunt contradiction costs face. Ask about the data instead of contradicting the
person, and read a soft no as a no.

## jp.humor

### Guidance
Modest, self-deprecating humour works; sarcasm aimed at a person does not. English idioms are risky
because they rarely translate, and jokes about hierarchy or hours land as criticism.

## jp.taboo

### Guidance
War history, regional politics, religion, income and family/health questions are best left alone.
Weather, seasons, food, travel and work are reliable ground. Let the other side open personal topics.

## jp.hierarchy

### Guidance
Decisions are prepared before they are taken: nemawashi aligns stakeholders informally, ringi
circulates the proposal for formal sign-off. Escalating over a manager, or demanding a decision in
the room, breaks that process even when the request is reasonable.

## jp.punctuality

### Guidance
Meetings start on time and materials arrive beforehand. Deadlines are exact: a date and a time,
not 'asap'. Lateness is noticed even when it is tolerated politely.

## jp.feedback

### Guidance
Correct privately, tie the feedback to the shared goal, and offer an alternative rather than a
verdict. Public correction of a senior colleague is a serious breach; public correction of anyone
should be avoided.

## jp.small_talk

### Guidance
Seasonal references are the safest opener, followed by food and travel. Questions about private
life feel intrusive; let the other side volunteer.
