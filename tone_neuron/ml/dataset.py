"""Synthetic labelled dataset generator for Task A (culture) and Task B (tone/risk).

The dataset is intentionally synthetic: it is a *learnability test-bed*, not a claim about real
people. See ``docs/FAIRNESS.md``. Hard cases (diaspora names, generic domains, dropped metadata,
English-only phrasing) are injected so the models cannot memorise a single shortcut.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from tone_neuron.ml.features import REGIONS
from tone_neuron.schemas import ReceiverInfo

TONES: tuple[str, ...] = ("polite", "neutral", "blunt", "rude", "sensitive")
RISKS: tuple[str, ...] = ("low", "medium", "high")
CANONICAL_RISK: dict[str, str] = {
    "polite": "low",
    "neutral": "low",
    "blunt": "medium",
    "rude": "high",
    "sensitive": "high",
}


@dataclass(slots=True)
class Sample:
    text: str
    region: str
    tone: str
    risk: str
    receiver_name: str
    receiver_email: str
    receiver_language: str | None
    receiver_timezone: str | None
    signature: str
    scenario: str

    def receiver(self) -> ReceiverInfo:
        return ReceiverInfo(
            name=self.receiver_name,
            email=self.receiver_email,
            language=self.receiver_language,
            timezone=self.receiver_timezone,
            signature=self.signature,
        )

    def identity_text(self) -> str:
        parts = [
            self.receiver_name,
            self.receiver_email,
            self.receiver_language or "",
            self.receiver_timezone or "",
            self.signature,
        ]
        return " ".join(part for part in parts if part)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Identity:
    region: str
    names: tuple[tuple[str, str], ...]
    domains: tuple[str, ...]
    languages: tuple[str, ...]
    timezones: tuple[str, ...]
    companies: tuple[str, ...]
    cities: tuple[str, ...]
    titles: tuple[str, ...]


IDENTITIES: dict[str, Identity] = {
    "JP": Identity(
        "JP",
        (("Kenji", "Tanaka"), ("Yuki", "Sato"), ("Hiroshi", "Suzuki"), ("Sakura", "Yamamoto"),
         ("Takumi", "Nakamura"), ("Emi", "Kobayashi"), ("Daiki", "Watanabe")),
        ("example.co.jp", "nihon-tech.jp", "kaisha.co.jp"),
        ("ja",), ("Asia/Tokyo",),
        ("Nihon Tech K.K.", "Sakura Systems", "Kaisha Manufacturing"),
        ("Tokyo", "Osaka", "Kyoto"),
        ("Assistant Manager", "Project Lead", "Section Chief"),
    ),
    "IN": Identity(
        "IN",
        (("Priya", "Sharma"), ("Rahul", "Patel"), ("Ananya", "Iyer"), ("Arjun", "Reddy"),
         ("Vikram", "Nair"), ("Deepa", "Mehta"), ("Rohan", "Gupta")),
        ("example.co.in", "bharat-soft.in", "techlabs.co.in"),
        ("en-IN", "hi"), ("Asia/Kolkata",),
        ("Bharat Soft Pvt Ltd", "TechLabs India", "Sagar Consulting"),
        ("Mumbai", "Bengaluru", "Hyderabad"),
        ("Senior Engineer", "Delivery Manager", "Analyst"),
    ),
    "DE": Identity(
        "DE",
        (("Lukas", "Müller"), ("Anna", "Schmidt"), ("Jonas", "Schneider"), ("Lea", "Fischer"),
         ("Felix", "Weber"), ("Marie", "Hoffmann"), ("Stefan", "Koch")),
        ("example.de", "technik-gmbh.de", "werk.de"),
        ("de",), ("Europe/Berlin",),
        ("Technik GmbH", "Werk Systems AG", "Nord Bau GmbH"),
        ("Berlin", "München", "Hamburg"),
        ("Projektleiter", "Ingenieur", "Teamlead"),
    ),
    "US": Identity(
        "US",
        (("Emily", "Johnson"), ("Michael", "Smith"), ("Sarah", "Williams"), ("David", "Brown"),
         ("Jessica", "Miller"), ("Brian", "Davis"), ("Megan", "Clark")),
        ("example.com", "acme.io", "northstar.co"),
        ("en-US",), ("America/New_York", "America/Los_Angeles", "America/Chicago"),
        ("Acme Inc.", "Northstar Labs", "Blue Ridge Co."),
        ("New York", "San Francisco", "Austin"),
        ("Account Executive", "Product Manager", "Engineering Lead"),
    ),
    "UK": Identity(
        "UK",
        (("Oliver", "Taylor"), ("Poppy", "Evans"), ("Harry", "Wilson"), ("Amelia", "Clarke"),
         ("George", "Hughes"), ("Charlotte", "Green"), ("Jack", "Roberts")),
        ("example.co.uk", "thames-ltd.co.uk", "albion.uk"),
        ("en-GB",), ("Europe/London",),
        ("Thames Ltd", "Albion Consulting", "Northfield plc"),
        ("London", "Manchester", "Edinburgh"),
        ("Programme Manager", "Consultant", "Head of Ops"),
    ),
    "CN": Identity(
        "CN",
        (("Wei", "Wang"), ("Fang", "Li"), ("Jing", "Zhang"), ("Lei", "Liu"),
         ("Min", "Chen"), ("Yan", "Yang"), ("Qiang", "Zhao")),
        ("example.cn", "huaxing.com.cn", "keji.cn"),
        ("zh-CN",), ("Asia/Shanghai",),
        ("华兴科技有限公司", "科际集团", "东方制造"),
        ("北京", "上海", "深圳"),
        ("项目经理", "总监", "工程师"),
    ),
    "BR": Identity(
        "BR",
        (("Ana", "Silva"), ("João", "Santos"), ("Beatriz", "Oliveira"), ("Pedro", "Souza"),
         ("Camila", "Lima"), ("Rafael", "Pereira"), ("Juliana", "Costa")),
        ("example.com.br", "paulista.com.br", "rio-tech.br"),
        ("pt-BR",), ("America/Sao_Paulo",),
        ("Paulista Ltda", "Rio Tech S.A.", "Verde Consultoria"),
        ("São Paulo", "Rio de Janeiro", "Belo Horizonte"),
        ("Gerente de Projetos", "Analista", "Diretor"),
    ),
    "AE": Identity(
        "AE",
        (("Mohammed", "Al Mansoori"), ("Fatima", "Al Suwaidi"), ("Omar", "Haddad"),
         ("Noor", "Khalil"), ("Khalid", "Al Marri"), ("Mariam", "Nasser"), ("Yousef", "Saleh")),
        ("example.ae", "gulf-holdings.ae", "dubai-ventures.ae"),
        ("ar", "en"), ("Asia/Dubai",),
        ("Gulf Holdings LLC", "Dubai Ventures", "Emirates Consulting"),
        ("Dubai", "Abu Dhabi", "Sharjah"),
        ("Projects Director", "Senior Manager", "Consultant"),
    ),
}

SCENARIOS: tuple[tuple[str, str], ...] = (
    ("report", "send the Q3 report"),
    ("kickoff", "book the kickoff call"),
    ("invoice", "approve the invoice"),
    ("proposal", "review the proposal"),
    ("bug", "fix the login bug"),
    ("roadmap", "share the roadmap"),
    ("interview", "schedule the interview"),
    ("budget", "confirm the budget"),
    ("handover", "complete the handover notes"),
    ("pricing", "update the pricing sheet"),
)

GREETINGS: dict[str, tuple[str, ...]] = {
    "JP": ("{addr}、お世話になっております。", "いつもお世話になっております。", "{addr}、お疲れさまです。"),
    "IN": ("Dear {addr},", "Namaste {addr},", "Hello {addr},\nHope you and your family are well."),
    "DE": ("Guten Tag {addr},", "Guten Morgen {addr},", "Hallo {addr},"),
    "US": ("Hi {addr},", "Hey {addr},", "{addr}, quick one:"),
    "UK": ("Dear {addr},", "Hi {addr},", "Hello {addr},"),
    "CN": ("您好，{addr}：", "尊敬的{addr}：", "{addr}，您好！"),
    "BR": ("Olá, {addr}, tudo bem?", "Oi {addr},", "Bom dia, {addr}!"),
    "AE": ("As-salaam alaikum {addr},", "Dear {addr},", "Good morning {addr},"),
}

CLOSINGS: dict[str, dict[str, tuple[str, ...]]] = {
    "JP": {
        "formal": ("よろしくお願いいたします。\n{signature}", "ご確認のほど、よろしくお願いいたします。\n{signature}"),
        "casual": ("よろしくお願いします。\n{signature}",),
    },
    "IN": {"formal": ("Warm regards,\n{signature}", "Thanks and regards,\n{signature}"), "casual": ("Thanks,\n{signature}",)},
    "DE": {"formal": ("Mit freundlichen Grüßen\n{signature}", "Beste Grüße\n{signature}"), "casual": ("Viele Grüße\n{signature}",)},
    "US": {"formal": ("Best,\n{signature}", "Thanks,\n{signature}"), "casual": ("Thanks!\n{signature}",)},
    "UK": {"formal": ("Kind regards,\n{signature}", "Best wishes,\n{signature}"), "casual": ("Cheers,\n{signature}",)},
    "CN": {"formal": ("谢谢！\n{signature}", "此致\n{signature}"), "casual": ("谢谢！\n{signature}",)},
    "BR": {"formal": ("Abraço,\n{signature}", "Atenciosamente,\n{signature}"), "casual": ("Abraço,\n{signature}",)},
    "AE": {"formal": ("Best regards,\n{signature}", "Kind regards,\n{signature}"), "casual": ("Thanks,\n{signature}",)},
}

BODIES: dict[str, tuple[str, ...]] = {
    "polite": (
        "I hope you are well. Could you please {ask} by Friday?",
        "When you have a moment, would you mind helping with this: {ask}?",
        "Thanks for your help last week. Could I ask you to {ask} before Thursday?",
        "I would really appreciate it if you could {ask} at your convenience.",
        "If possible, could you {ask} before the end of the week? No rush if something urgent comes up.",
    ),
    "neutral": (
        "Please {ask} by Friday.",
        "Sharing an update: we need to {ask} this week.",
        "Could you {ask}? Let me know if that works.",
        "Here is the plan: {ask} before the next review.",
        "The current status is unchanged. Please {ask} after the standup.",
    ),
    "blunt": (
        "{Ask} now.",
        "Just {ask}.",
        "I need this today. {Ask}.",
        "This is a reminder: {ask} immediately.",
        "{Ask} before you do anything else.",
    ),
    "rude": (
        "This is the third time I have asked. {Ask} now, this is unacceptable.",
        "Why is this still not done? {Ask} today or I will escalate.",
        "Your work on this is useless. {Ask} properly.",
        "Honestly, this is pathetic. {Ask} immediately.",
        "I am tired of repeating myself. {Ask} now.",
    ),
    "sensitive": (
        "We need to discuss your performance review and the salary decision before Friday.",
        "HR has opened a harassment complaint; please do not discuss it with the team.",
        "Your contract termination will be reviewed on Monday; this is confidential.",
        "There has been a discrimination complaint and legal is involved. Please confirm receipt.",
        "The redundancy consultation starts next week and your role is affected. This is strictly confidential.",
    ),
}

REGION_MARKERS: dict[str, dict[str, tuple[str, ...]]] = {
    "JP": {
        "polite": ("ご確認いただけますと幸いです。", "恐れ入りますが、よろしくお願いいたします。"),
        "neutral": ("ご確認をお願いします。", "以上、よろしくお願いいたします。"),
        "blunt": ("至急対応してください。", "今すぐ送ってください。"),
        "rude": ("いつも遅いですね。", "話になりません。"),
        "sensitive": ("人事の件です。", "社内で確認します。"),
    },
    "IN": {
        "polite": ("Kindly do the needful and confirm.", "Please revert at your earliest convenience."),
        "neutral": ("Please confirm receipt.", "Kindly update the tracker."),
        "blunt": ("Do it today.", "Send it now itself."),
        "rude": ("This is not acceptable at all.", "You always delay things."),
        "sensitive": ("The HR team will call you.", "Please keep this confidential."),
    },
    "DE": {
        "polite": ("Vielen Dank im Voraus.", "Bitte geben Sie kurz Bescheid."),
        "neutral": ("Danke für die Rückmeldung.", "Bitte bis Freitag erledigen."),
        "blunt": ("Sofort erledigen.", "Das muss heute raus."),
        "rude": ("Das ist unbrauchbar.", "So geht das nicht."),
        "sensitive": ("Personalangelegenheit, bitte vertraulich behandeln.",),
    },
    "US": {
        "polite": ("Thanks so much - really appreciate the quick turnaround.", "No worries if this slips to Monday."),
        "neutral": ("Let me know if you have questions.", "Circling back on this."),
        "blunt": ("Need this today.", "Just send it."),
        "rude": ("This is unacceptable.", "You dropped the ball again."),
        "sensitive": ("This is confidential - please keep it off the team channel.",),
    },
    "UK": {
        "polite": ("I wonder if you might have a moment to look at this?", "That would be great, thank you."),
        "neutral": ("Please could you confirm by Friday?", "I'll send the notes over."),
        "blunt": ("Send it today.", "This needs doing now."),
        "rude": ("This is frankly unacceptable.", "I'm afraid this is not good enough."),
        "sensitive": ("This is confidential, so please keep it between us.",),
    },
    "CN": {
        "polite": ("麻烦您确认一下。", "请您指正。"),
        "neutral": ("请尽快处理。", "收到请回复。"),
        "blunt": ("今天必须完成。", "马上发给我。"),
        "rude": ("这个做得太差了。", "你们总是拖。"),
        "sensitive": ("这是人事方面的保密事项。",),
    },
    "BR": {
        "polite": ("Muito obrigado pela ajuda!", "Qualquer coisa me avisa, por favor."),
        "neutral": ("Por favor, confirma o recebimento.", "Segue o arquivo atualizado."),
        "blunt": ("Manda hoje.", "Faz agora."),
        "rude": ("Isso está inaceitável.", "Você sempre atrasa."),
        "sensitive": ("Assunto confidencial de RH.",),
    },
    "AE": {
        "polite": ("We would appreciate your guidance.", "Thank you for your continued support."),
        "neutral": ("Please confirm receipt at your convenience.", "We will follow up in writing."),
        "blunt": ("Send it today.", "This must be done now."),
        "rude": ("This is unacceptable.", "You are not delivering."),
        "sensitive": ("This is a confidential HR matter.",),
    },
}


def _address(region: str, given: str, family: str, rng: random.Random) -> str:
    title = rng.choice(("Mr", "Ms"))
    if region == "JP":
        return f"{family}-san"
    if region == "CN":
        return f"{family}经理"
    if region in ("IN", "AE"):
        return f"{title} {family}"
    if region == "DE":
        return f"{title} {family}"
    if region == "UK":
        return f"{title} {family}" if rng.random() < 0.5 else given
    return given


def _signature(region: str, given: str, family: str, identity: Identity, rng: random.Random) -> str:
    company = rng.choice(identity.companies)
    city = rng.choice(identity.cities)
    title = rng.choice(identity.titles)
    return f"{given} {family}\n{title}\n{company}, {city}"


def _risk_for(tone: str, text: str) -> str:
    from tone_neuron.ml.features import lexicon_counts

    counts = lexicon_counts(text)
    risk = CANONICAL_RISK[tone]
    if counts["insult"] or counts["threat"]:
        return "high"
    if tone in ("rude", "sensitive"):
        return "high"
    if tone == "blunt":
        return "medium"
    if counts["urgency"] >= 2 and tone == "polite":
        return "medium"
    return risk


def _compose(region: str, tone: str, rng: random.Random, noise: float) -> Sample:
    identity = IDENTITIES[region]
    given, family = rng.choice(identity.names)
    scenario_key, ask = rng.choice(SCENARIOS)

    # hard cases: drop/contradict identity signals so region can't be a single-field lookup
    foreign_name = rng.random() < noise * 0.55
    if foreign_name:
        other_region = rng.choice([r for r in REGIONS if r != region])
        other = IDENTITIES[other_region]
        given, family = rng.choice(other.names)

    domain = rng.choice(identity.domains)
    if rng.random() < noise * 0.9:
        domain = rng.choice(("gmail.com", "outlook.com", "proton.me", "yahoo.com"))

    language: str | None = rng.choice(identity.languages)
    if rng.random() < noise * 0.5:
        language = None

    timezone: str | None = rng.choice(identity.timezones)
    if rng.random() < noise * 0.5:
        timezone = None

    english_only = rng.random() < noise * 0.8
    addr = _address(region, given, family, rng)
    greeting = rng.choice(GREETINGS[region]).format(addr=addr)
    body = rng.choice(BODIES[tone]).format(ask=ask, Ask=ask[:1].upper() + ask[1:])
    if not english_only and rng.random() < 0.65:
        body = f"{body} {rng.choice(REGION_MARKERS[region][tone])}"
    if rng.random() < noise * 0.6:
        signature = "Best regards"
    else:
        signature = _signature(region, given, family, identity, rng)
    bucket = "formal" if tone in ("polite", "neutral", "sensitive") else "casual"
    closing = rng.choice(CLOSINGS[region][bucket]).format(signature=signature)
    text = f"{greeting}\n\n{body}\n\n{closing}"

    return Sample(
        text=text,
        region=region,
        tone=tone,
        risk=_risk_for(tone, text),
        receiver_name=f"{given} {family}",
        receiver_email=f"{given.lower()}.{family.lower().replace(' ', '')}@{domain}",
        receiver_language=language,
        receiver_timezone=timezone,
        signature=signature,
        scenario=scenario_key,
    )


def generate_dataset(n: int = 2400, seed: int = 7, noise: float = 0.18) -> list[Sample]:
    """Generate a balanced synthetic dataset across regions and tones."""
    rng = random.Random(seed)
    cells = [(region, tone) for region in REGIONS for tone in TONES]
    samples: list[Sample] = []
    index = 0
    while len(samples) < n:
        region, tone = cells[index % len(cells)]
        samples.append(_compose(region, tone, rng, noise=noise))
        index += 1
    rng.shuffle(samples)
    return samples


def split_dataset(
    samples: list[Sample], test_ratio: float = 0.25, seed: int = 99
) -> tuple[list[Sample], list[Sample]]:
    """Stratified by (region, tone) so every region/class appears in the test split."""
    rng = random.Random(seed)
    buckets: dict[tuple[str, str], list[Sample]] = {}
    for sample in samples:
        buckets.setdefault((sample.region, sample.tone), []).append(sample)
    train: list[Sample] = []
    test: list[Sample] = []
    for bucket in buckets.values():
        rng.shuffle(bucket)
        cut = max(1, int(round(len(bucket) * test_ratio)))
        test.extend(bucket[:cut])
        train.extend(bucket[cut:])
    rng.shuffle(train)
    rng.shuffle(test)
    return train, test


def save_jsonl(samples: list[Sample], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for sample in samples:
            handle.write(json.dumps(sample.as_dict(), ensure_ascii=False) + "\n")
    return path


def load_jsonl(path: str | Path) -> list[Sample]:
    samples: list[Sample] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                samples.append(Sample(**json.loads(line)))
    return samples


def summarize(samples: list[Sample]) -> dict:
    by_region: dict[str, int] = {}
    by_tone: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    for sample in samples:
        by_region[sample.region] = by_region.get(sample.region, 0) + 1
        by_tone[sample.tone] = by_tone.get(sample.tone, 0) + 1
        by_risk[sample.risk] = by_risk.get(sample.risk, 0) + 1
    return {
        "count": len(samples),
        "regions": dict(sorted(by_region.items())),
        "tones": dict(sorted(by_tone.items())),
        "risks": dict(sorted(by_risk.items())),
    }
