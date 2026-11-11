---
okf: "1.0"
kind: culture-profile
region: CN
region_name: China
languages: [zh]
last_reviewed: 2026-01-15
caveat: "Common mainland Chinese business norms. Generational and regional differences are large."
provenance:
  type: seed
  confidence: editorial
  sources:
    - "Seed profile written for this project; general business-etiquette literature, not a primary source."
entries:
  - id: cn.greeting
    title: Formal openings and self-introduction
    category: greeting
    severity: medium
    tags: [greeting, ninhao, title, introduction, surname]
    do:
      - "Open with 您好 and title + surname: 王经理 (Manager Wang)."
      - "Introduce yourself with company and role on first contact."
    avoid:
      - "Casual 'Hey' or first names without an invitation."
      - "Skipping the introduction and starting with the request."
    preferred: ["您好，王经理：", "我是某某公司的李明，负责……"]
    flagged:
      - pattern: "hey"
        why: "Too casual for Chinese business correspondence."
        severity: medium
        suggested: "您好，王经理："
      - pattern: "dear friend"
        why: "Reads as a mass mailing rather than a serious introduction."
        severity: low
        suggested: "尊敬的陈总："
  - id: cn.formality
    title: Titles, 您 and face
    category: formality
    severity: high
    tags: [titles, nin, face, mianzi, respect, formality]
    do:
      - "Use 您 rather than 你 with seniors and clients."
      - "Use surname + title (王总, 李经理) instead of first names."
      - "Protect the other side's face: give room to change position without losing standing."
    avoid:
      - "Calling a senior colleague by first name."
      - "Correcting someone in front of their team."
    preferred: ["您好，王总：", "麻烦您确认一下。", "请您指正。"]
    flagged:
      - pattern: "just call me"
        why: "Inviting first names from a senior contact breaks the expected title boundary."
        severity: low
        suggested: "please let me know how you would like to be addressed"
  - id: cn.directness
    title: Indirect refusal, preserved face
    category: directness
    severity: high
    tags: [indirect, face, refusal, consider, harmony, mianzi]
    do:
      - "Use 'we will consider it' (我们再考虑考虑) or 'the conditions are not mature yet'."
      - "Raise problems privately and in the form of a question."
      - "Offer a face-saving route to a revised position."
    avoid:
      - "A flat 'no' or public criticism."
      - "Reading a soft deferral as agreement."
    preferred: ["我们再研究一下。", "目前条件还不太成熟。", "这个方向可以再讨论。"]
    flagged:
      - pattern: "that's wrong"
        why: "Direct contradiction in a group setting causes a loss of face."
        severity: high
        suggested: "we may want to double-check this data"
      - pattern: "you don't understand"
        why: "Explicitly questioning someone's understanding is a face threat."
        severity: high
        suggested: "let me share some additional context"
  - id: cn.humor
    title: Modest humour, no political jokes
    category: humor
    severity: medium
    tags: [humor, modesty, politics, jokes, idioms]
    do:
      - "Use modest, self-effacing humour and food or travel references."
    avoid:
      - "Political and historical jokes."
      - "Humour that embarrasses a colleague in front of seniors."
    preferred: ["还在学习中，请多指教。", "这次多亏了大家。"]
    flagged:
      - pattern: "tiananmen"
        why: "Politically sensitive and never appropriate in a business thread."
        severity: high
        suggested: "the project history"
      - pattern: "taiwan is a country"
        why: "Politically sensitive; avoid territorial framing entirely at work."
        severity: high
        suggested: "the regional office"
  - id: cn.taboo
    title: Topics to avoid
    category: taboo
    severity: high
    tags: [taboo, politics, taiwan, tibet, salary, religion]
    do:
      - "Keep small talk on food, travel, family in general terms and business achievements."
    avoid:
      - "Tiananmen, Taiwan, Tibet, Xinjiang and party politics."
      - "Salary, religion and comparisons between regions."
    preferred: ["最近工作忙吗？", "这边的菜还习惯吗？"]
    flagged:
      - pattern: "how much do you earn"
        why: "Income is private and asking is a high-risk intrusion."
        severity: high
        suggested: "what is the budget range for this project"
      - pattern: "human rights"
        why: "Politically loaded; not workplace conversation."
        severity: high
        suggested: "the compliance requirements"
  - id: cn.hierarchy
    title: Seniority and top-down decisions
    category: hierarchy
    severity: medium
    tags: [hierarchy, decision_making, seniority, leader, approval]
    do:
      - "Address the most senior person first and let them set direction."
      - "Secure the leader's approval before broad circulation."
      - "Use a local partner or manager to raise sensitive issues."
    avoid:
      - "Contradicting a senior in a group meeting."
      - "Assuming a junior contact can approve commercial terms."
    preferred: ["请王总批示。", "我们会按照您的意见推进。"]
    flagged:
      - pattern: "i'll escalate"
        why: "Escalation framing is read as a challenge to the senior's authority."
        severity: medium
        suggested: "could we ask for the leadership's guidance"
  - id: cn.punctuality
    title: Meetings and deadlines
    category: punctuality
    severity: low
    tags: [punctuality, meetings, deadline, schedule, overrun]
    do:
      - "Arrive on time; meetings may run long and include relationship talk."
      - "Confirm deadlines with a date and reconfirm before holidays."
    avoid:
      - "Rushing a senior contact off a call."
      - "Scheduling over the Lunar New Year period without checking."
    preferred: ["请您确认一下时间。", "节后再推进可以吗？"]
    flagged:
      - pattern: "asap"
        why: "Urgency without a date creates confusion around holidays and approvals."
        severity: medium
        suggested: "by Friday 6 March, before the holiday"
  - id: cn.feedback
    title: Private, indirect correction
    category: feedback
    severity: medium
    tags: [feedback, private, face, indirect, suggestion]
    do:
      - "Give correction one-to-one, starting from the shared goal."
      - "Frame it as a suggestion for consideration (供参考)."
    avoid:
      - "Public correction, especially of a senior."
      - "Written criticism that can be forwarded."
    preferred: ["这一点供您参考。", "我们一起再看看，好吗？"]
    flagged:
      - pattern: "you failed"
        why: "Person-level blame in writing is a serious face violation."
        severity: high
        suggested: "the deliverable missed the date; what support would help"
      - pattern: "this is unacceptable"
        why: "Confrontational in writing; state the gap and propose a next step."
        severity: medium
        suggested: "this does not yet meet the brief because"
  - id: cn.small_talk
    title: Relationship-first small talk
    category: small_talk
    severity: low
    tags: [small_talk, food, family, travel, relationship, guanxi]
    do:
      - "Ask about food, travel and family in general terms."
      - "Invest time in relationship building before business."
    avoid:
      - "Probing personal income or political views."
    preferred: ["您最近出差多吗？", "有机会一起吃饭。"]
---

## cn.greeting

### Guidance
Open with 您好 and title + surname. A serious self-introduction (company, role) signals that the
message is worth attention; casual openers read as unserious.

## cn.formality

### Guidance
Titles and 您 carry the relationship, and face (mianzi) is the currency of every exchange. Give the
other side room to adjust a position without public loss of standing.

## cn.directness

### Guidance
Refusals arrive as deferrals: 'we will consider it', 'the conditions are not mature yet'. Flat
contradiction in a group costs face, so problems are raised privately and as questions.

## cn.humor

### Guidance
Modest, self-effacing humour and food or travel references work. Political and historical jokes are
dangerous; humour that embarrasses a colleague in front of seniors is not humour.

## cn.taboo

### Guidance
Tiananmen, Taiwan, Tibet, Xinjiang, party politics and religion are off limits, as are salary
questions and regional comparisons. Food, travel and general family talk are safe.

## cn.hierarchy

### Guidance
Decisions are top-down and the senior person's direction is expected to hold. Secure leadership
approval before circulation, and never contradict a senior in a group meeting.

## cn.punctuality

### Guidance
Arrive on time, but expect meetings to run long with relationship talk. Deadlines need a date and a
check around major holidays, especially Lunar New Year.

## cn.feedback

### Guidance
Correction is private, indirect and framed as a suggestion for consideration. Public correction of a
senior is a serious breach; written criticism may be forwarded.

## cn.small_talk

### Guidance
Relationships precede transactions: food, travel and general family questions are the way in. Avoid
income and politics.
