"""Hand-crafted cultural and tone features shared by training and inference.

Everything here is deterministic, explainable and offline. No feature is treated as proof of
someone's origin: each contributes soft evidence with a visible weight.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable

from tone_neuron.schemas import AnalyzeContext, ReceiverInfo, RegionSignal

REGION_NAMES: dict[str, str] = {
    "JP": "Japan",
    "IN": "India",
    "DE": "Germany",
    "US": "United States",
    "UK": "United Kingdom",
    "CN": "China",
    "BR": "Brazil",
    "AE": "United Arab Emirates",
}
REGIONS: tuple[str, ...] = tuple(REGION_NAMES)


@dataclass(frozen=True, slots=True)
class RegionProfile:
    region: str
    region_name: str
    languages: tuple[str, ...]
    tlds: tuple[str, ...]
    timezones: tuple[str, ...]
    surnames: tuple[str, ...]
    given_names: tuple[str, ...]
    greeting_cues: tuple[str, ...]
    honorific_cues: tuple[str, ...]
    indirect_cues: tuple[str, ...]
    signature_cues: tuple[str, ...]


PROFILES: dict[str, RegionProfile] = {
    "JP": RegionProfile(
        region="JP", region_name="Japan", languages=("ja",),
        tlds=("jp", "co.jp", "ne.jp", "or.jp", "ac.jp"),
        timezones=("asia/tokyo",),
        surnames=(
            "tanaka", "suzuki", "sato", "watanabe", "yamamoto", "nakamura", "kobayashi",
            "kato", "yoshida", "yamada", "sasaki", "kimura", "hayashi", "mori", "abe",
            "ishikawa", "fujita", "ogawa", "okada", "endo", "aoki", "fujii",
        ),
        given_names=(
            "kenji", "yuki", "hiroshi", "sakura", "haruto", "yui", "akira", "nao",
            "takumi", "emi", "daiki", "rin", "sota", "mei", "kenta", "aoi",
        ),
        greeting_cues=("お世話になっております", "よろしくお願いいたします", "お疲れさまです", "ございます"),
        honorific_cues=("さん", "様", "先生", "-san", "-sama"),
        indirect_cues=("検討します", "難しいかもしれません", "いかがでしょうか", "恐れ入ります"),
        signature_cues=("株式会社", "東京都", "japan", "k.k.", "co., ltd."),
    ),
    "IN": RegionProfile(
        region="IN", region_name="India", languages=("hi", "en-in"),
        tlds=("in", "co.in", "net.in", "org.in", "ac.in"),
        timezones=("asia/kolkata", "asia/calcutta"),
        surnames=(
            "sharma", "patel", "singh", "kumar", "iyer", "reddy", "nair", "gupta",
            "mehta", "desai", "rao", "das", "banerjee", "khanna", "malhotra",
            "chowdhury", "iyengar", "pillai", "joshi", "agarwal", "bose",
        ),
        given_names=(
            "priya", "rahul", "ananya", "arjun", "ramesh", "sunita", "vikram", "deepa",
            "aditya", "kavya", "rohan", "isha", "neha", "sanjay", "pooja", "amit",
        ),
        greeting_cues=(
            "namaste", "do the needful", "kindly", "please find attached", "revert",
            "prepone", "sir/madam", "respected",
        ),
        honorific_cues=("ji", "sir", "madam", "shri", "smt"),
        indirect_cues=("please do the needful", "we will try", "small challenge", "kindly cooperate"),
        signature_cues=("pvt", "ltd", "mumbai", "bengaluru", "bangalore", "delhi", "hyderabad"),
    ),
    "DE": RegionProfile(
        region="DE", region_name="Germany", languages=("de",),
        tlds=("de", "co.de"),
        timezones=("europe/berlin", "europe/vienna", "europe/zurich"),
        surnames=(
            "müller", "mueller", "schmidt", "schneider", "fischer", "weber", "meyer",
            "wagner", "becker", "schulz", "hoffmann", "klein", "wolf", "richter",
            "koch", "bauer", "schäfer", "braun", "keller", "hofmann",
        ),
        given_names=(
            "lukas", "anna", "jonas", "lea", "felix", "marie", "max", "sophie",
            "thomas", "julia", "stefan", "katharina", "jan", "lena", "moritz", "hannah",
        ),
        greeting_cues=("sehr geehrte", "mit freundlichen grüßen", "guten tag", "guten morgen", "bitte", "danke"),
        honorific_cues=("herr", "frau", "dr.", "prof."),
        indirect_cues=("ich würde vorschlagen", "vielleicht", "könnten sie"),
        signature_cues=("gmbh", "ag", "berlin", "münchen", "hamburg", "frankfurt"),
    ),
    "US": RegionProfile(
        region="US", region_name="United States", languages=("en-us", "en"),
        tlds=("us",),
        timezones=(
            "america/new_york", "america/chicago", "america/denver",
            "america/los_angeles", "america/phoenix", "america/anchorage",
        ),
        surnames=(
            "smith", "johnson", "williams", "brown", "jones", "garcia", "miller",
            "davis", "rodriguez", "martinez", "wilson", "anderson", "taylor",
            "thomas", "moore", "jackson", "white", "harris", "clark", "lewis",
        ),
        given_names=(
            "james", "michael", "emily", "sarah", "david", "jessica", "john",
            "ashley", "brian", "jordan", "sam", "taylor", "megan", "chris", "alex", "katie",
        ),
        greeting_cues=("hey", "hi ", "per my last email", "circle back", "reach out", "touch base", "awesome"),
        honorific_cues=("mr.", "ms.", "mrs."),
        indirect_cues=("just checking in", "wanted to circle back"),
        signature_cues=("inc.", "llc", "san francisco", "new york", "seattle", "austin"),
    ),
    "UK": RegionProfile(
        region="UK", region_name="United Kingdom", languages=("en-gb",),
        tlds=("uk", "co.uk", "ac.uk", "gov.uk", "org.uk"),
        timezones=("europe/london",),
        surnames=(
            "smith", "jones", "taylor", "brown", "wilson", "evans", "thomas",
            "roberts", "walker", "wright", "patel", "khan", "green", "hall",
            "wood", "clarke", "hughes", "edwards", "turner", "hill",
        ),
        given_names=(
            "oliver", "amelia", "harry", "poppy", "george", "charlotte", "jack",
            "emily", "thomas", "sophie", "james", "priya", "will", "ellie", "alfie", "freya",
        ),
        greeting_cues=("i wonder if", "i'm afraid", "cheers", "brilliant", "quite", "rather", "whilst"),
        honorific_cues=("mr", "mrs", "ms", "dr"),
        indirect_cues=("i'm not sure that", "perhaps we could", "i'd push back"),
        signature_cues=("ltd", "plc", "london", "manchester", "edinburgh", "leeds"),
    ),
    "CN": RegionProfile(
        region="CN", region_name="China", languages=("zh", "zh-cn"),
        tlds=("cn", "com.cn", "net.cn", "org.cn"),
        timezones=("asia/shanghai", "asia/beijing", "asia/chongqing"),
        surnames=(
            "王", "李", "张", "刘", "陈", "杨", "黄", "赵", "周", "吴", "徐", "孙",
            "马", "朱", "胡", "郭", "林", "何", "高", "罗",
            "wang", "li", "zhang", "liu", "chen", "yang", "huang", "zhao", "zhou", "wu",
        ),
        given_names=(
            "伟", "芳", "娜", "敏", "静", "强", "磊", "洋", "勇", "艳", "杰", "娟",
            "wei", "fang", "na", "min", "jing", "qiang", "lei", "yong", "yan", "jie",
        ),
        greeting_cues=("您好", "麻烦", "请", "谢谢", "尽快", "经理", "总", "辛苦了"),
        honorific_cues=("总", "经理", "主任", "您"),
        indirect_cues=("再研究", "条件不太成熟", "再考虑", "看看情况"),
        signature_cues=("有限公司", "北京", "上海", "深圳", "hangzhou"),
    ),
    "BR": RegionProfile(
        region="BR", region_name="Brazil", languages=("pt", "pt-br"),
        tlds=("br", "com.br", "net.br", "org.br"),
        timezones=("america/sao_paulo", "america/recife", "america/manaus", "america/fortaleza"),
        surnames=(
            "silva", "santos", "oliveira", "souza", "lima", "pereira", "costa",
            "ferreira", "almeida", "rodrigues", "gomes", "martins", "araujo",
            "barbosa", "ribeiro", "carvalho", "nascimento", "moreira",
        ),
        given_names=(
            "ana", "joão", "joao", "maria", "pedro", "lucas", "beatriz", "gabriel",
            "camila", "rafael", "juliana", "thiago", "bruna", "felipe", "larissa", "vitor",
        ),
        greeting_cues=("olá", "ola", "obrigado", "obrigada", "por favor", "tudo bem", "abraço", "segue"),
        honorific_cues=("senhor", "senhora", "sr.", "sra."),
        indirect_cues=("vamos resolver juntos", "acho que", "pode ser"),
        signature_cues=("ltda", "s.a.", "são paulo", "rio de janeiro", "brasília"),
    ),
    "AE": RegionProfile(
        region="AE", region_name="United Arab Emirates", languages=("ar", "ar-ae"),
        tlds=("ae", "co.ae", "ac.ae", "gov.ae"),
        timezones=("asia/dubai", "asia/abu_dhabi", "asia/muscat"),
        surnames=(
            "al mansoori", "al maktoum", "al nahyan", "al falasi", "al suwaidi",
            "al marri", "al zaabi", "haddad", "khalil", "nasser", "saleh", "mansour",
            "hussein", "al hashimi", "al balushi",
            "المزروعي", "المنصوري", "الهاشمي",
        ),
        given_names=(
            "mohammed", "ahmed", "fatima", "noor", "omar", "layla", "khalid",
            "mariam", "yousef", "sara", "ali", "aisha", "rashid", "huda",
            "محمد", "أحمد", "فاطمة", "نور",
        ),
        greeting_cues=("as-salaam", "assalam", "inshallah", "shukran", "ramadan", "yalla", "habibi"),
        honorific_cues=("sheikh", "eng.", "dr.", "mr.", "al "),
        indirect_cues=("we will review", "perhaps we could", "inshallah"),
        signature_cues=("llc", "dubai", "abu dhabi", "sharjah", "dmcc"),
    ),
}


_SCRIPT_BONUS: dict[str, dict[str, float]] = {
    "kana": {"JP": 2.6},
    "han": {"CN": 1.8, "JP": 0.9},
    "arabic": {"AE": 2.2},
    "devanagari": {"IN": 2.0},
}

_KANA_RE = re.compile(r"[\u3040-\u30ff]")
_HAN_RE = re.compile(r"[\u4e00-\u9fff]")
_ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097f]")


def detect_scripts(text: str) -> list[str]:
    found: list[str] = []
    if _KANA_RE.search(text):
        found.append("kana")
    if _HAN_RE.search(text):
        found.append("han")
    if _ARABIC_RE.search(text):
        found.append("arabic")
    if _DEVANAGARI_RE.search(text):
        found.append("devanagari")
    return found


def _strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _normalise_name(value: str) -> str:
    return _strip_accents(value).lower().replace("-", " ").replace("_", " ").strip()


def name_region_scores(name: str | None) -> dict[str, float]:
    if not name:
        return {}
    normalised = _normalise_name(name)
    tokens = [token.strip(".,") for token in re.split(r"[\s]+", normalised) if token.strip(".,")]
    if not tokens:
        return {}
    combined = normalised
    scores: dict[str, float] = {}
    for region, profile in PROFILES.items():
        hits = 0
        for token in tokens:
            if token in profile.surnames or token in profile.given_names:
                hits += 1
        if any(surname in combined for surname in profile.surnames if " " in surname):
            hits += 1
        if hits:
            scores[region] = min(1.0, 0.55 * hits)
    return scores


def domain_region_scores(domain_or_email: str | None) -> dict[str, float]:
    if not domain_or_email:
        return {}
    value = domain_or_email.lower().strip()
    if "@" in value:
        value = value.split("@", 1)[1]
    value = value.split(":")[0]
    parts = [part for part in value.split(".") if part]
    if len(parts) < 2:
        return {}
    suffix2 = ".".join(parts[-2:])
    suffix1 = parts[-1]
    scores: dict[str, float] = {}
    for region, profile in PROFILES.items():
        for tld in profile.tlds:
            if "." in tld:
                if suffix2 == tld or value.endswith("." + tld):
                    scores[region] = max(scores.get(region, 0.0), 1.0)
            elif suffix1 == tld:
                scores[region] = max(scores.get(region, 0.0), 1.0)
    return scores


def timezone_region_scores(timezone: str | None) -> dict[str, float]:
    if not timezone:
        return {}
    value = timezone.strip().lower().replace(" ", "_")
    scores: dict[str, float] = {}
    for region, profile in PROFILES.items():
        if any(value == tz or value.endswith("/" + tz.split("/")[-1]) for tz in profile.timezones):
            scores[region] = 1.0
    return scores


def language_region_scores(language: str | None) -> dict[str, float]:
    if not language:
        return {}
    value = language.strip().lower()
    if value == "en-gb":
        return {"UK": 0.9}
    if value in ("en", "en-us"):
        return {"US": 0.6}
    scores: dict[str, float] = {}
    for region, profile in PROFILES.items():
        if value in profile.languages or value.split("-")[0] in profile.languages:
            scores[region] = 1.0
    return scores


def cue_region_scores(text: str) -> dict[str, float]:
    if not text:
        return {}
    lowered = text.lower()
    scores: dict[str, float] = {}
    for region, profile in PROFILES.items():
        hits = sum(
            1
            for cue in profile.greeting_cues + profile.honorific_cues + profile.indirect_cues
            if cue and cue in lowered
        )
        if hits:
            scores[region] = min(1.0, 0.35 * hits)
    return scores


WEIGHTS: dict[str, float] = {
    "script": 2.4,
    "language": 1.8,
    "tld": 1.5,
    "timezone": 1.2,
    "name": 1.0,
    "signature": 0.8,
    "phrasing": 0.7,
    "participants": 0.6,
}


@dataclass(slots=True)
class IdentityEvidence:
    scores: dict[str, float] = field(default_factory=dict)
    signals: list[RegionSignal] = field(default_factory=list)

    def add(self, region: str, kind: str, value: str, weight: float, note: str = "") -> None:
        self.scores[region] = self.scores.get(region, 0.0) + weight
        self.signals.append(RegionSignal(kind=kind, value=value[:80], weight=round(weight, 3), note=note))


def _signature_scores(signature: str) -> dict[str, float]:
    lowered = signature.lower()
    return {
        region: 1.0
        for region, profile in PROFILES.items()
        if any(cue in lowered for cue in profile.signature_cues)
    }


def identity_evidence(
    text: str,
    receiver: ReceiverInfo | None = None,
    context: AnalyzeContext | None = None,
) -> IdentityEvidence:
    """Collect weighted, explainable signals. Absence of a signal never penalises a region."""
    receiver = receiver or ReceiverInfo()
    context = context or AnalyzeContext()
    evidence = IdentityEvidence()

    for script in detect_scripts(text):
        for region, weight in _SCRIPT_BONUS[script].items():
            evidence.add(region, "script", script, weight, f"{script} script in the message")

    email = receiver.email or ""
    domain = receiver.domain or (email.split("@", 1)[1] if "@" in email else "")
    for region, strength in domain_region_scores(domain).items():
        evidence.add(region, "email_domain", domain, WEIGHTS["tld"] * strength, "email domain suffix")

    for region, strength in language_region_scores(receiver.language).items():
        evidence.add(region, "language", receiver.language or "", WEIGHTS["language"] * strength, "declared language")

    for region, strength in timezone_region_scores(receiver.timezone).items():
        evidence.add(region, "timezone", receiver.timezone or "", WEIGHTS["timezone"] * strength)

    for region, strength in name_region_scores(receiver.name).items():
        evidence.add(region, "name", receiver.name or "", WEIGHTS["name"] * strength, "name origin cue")

    signature = receiver.signature or ""
    if signature:
        signature_scores = cue_region_scores(signature) | _signature_scores(signature)
        for region, strength in signature_scores.items():
            evidence.add(region, "signature", signature, WEIGHTS["signature"] * strength, "signature cues")

    for region, strength in cue_region_scores(text).items():
        evidence.add(region, "phrasing", region, WEIGHTS["phrasing"] * strength, "phrasing cue")

    participants = (context.meeting.participants if context.meeting else []) or []
    for participant in participants:
        for region, strength in name_region_scores(participant).items():
            evidence.add(region, "participants", participant, WEIGHTS["participants"] * strength, "meeting participant name")

    return evidence


def softmax_distribution(scores: dict[str, float], temperature: float = 1.0) -> dict[str, float]:
    regions = list(REGIONS)
    if not scores:
        return {region: 1.0 / len(regions) for region in regions}
    peak = max(scores.values())
    exps = {
        region: math.exp((scores.get(region, 0.0) - peak) / max(temperature, 1e-6))
        for region in regions
    }
    total = sum(exps.values()) or 1.0
    return {region: value / total for region, value in exps.items()}


def identity_tokens(text: str, receiver: ReceiverInfo | None, context: AnalyzeContext | None) -> list[str]:
    evidence = identity_evidence(text, receiver, context)
    tokens = [f"{signal.kind}:{signal.value.lower()[:40]}" for signal in evidence.signals]
    if receiver and receiver.name:
        tokens.extend(f"name:{token}" for token in re.split(r"\s+", _normalise_name(receiver.name)) if token)
    if receiver and receiver.domain:
        tokens.append(f"domain:{receiver.domain.lower()}")
    return tokens


def region_feature_text(
    text: str,
    receiver: ReceiverInfo | None = None,
    context: AnalyzeContext | None = None,
    include_text: bool = True,
) -> str:
    """Feature string for the region classifier.

    With ``include_text=False`` only identity evidence (name, script, TLD, language, time zone,
    signature, regional phrasing cues) is used. This stops the model learning "English body
    text means US" from the synthetic corpus.
    """
    tokens = " ".join(identity_tokens(text, receiver, context))
    if not include_text:
        return tokens
    return tokens + " | " + " ".join(text.split())


def tone_feature_text(text: str, region: str) -> str:
    return (
        f"__region__{region.upper()} __regionname__{REGION_NAMES.get(region.upper(), '')} "
        + " ".join(text.split())
    )


LEXICONS: dict[str, tuple[str, ...]] = {
    "insult": (
        "idiot", "stupid", "incompetent", "useless", "pathetic", "moron", "clueless",
        "shut up", "you people", "nonsense", "ridiculous", "hopeless",
    ),
    "threat": ("sue", "lawsuit", "legal action", "fired", "terminate", "harassment", "discrimination"),
    "sensitive": (
        "salary", "performance review", "termination", "redundancy", "confidential",
        "medical", "religion", "politics", "complaint", "disciplinary",
    ),
    "urgency": ("asap", "immediately", "right now", "urgent", "deadline", "hurry", "now", "today"),
    "hedge": (
        "maybe", "perhaps", "i think", "might", "could", "would", "possibly",
        "sort of", "kind of", "i wonder", "if possible", "when you have a moment",
    ),
    "polite": (
        "please", "thank", "thanks", "appreciate", "grateful", "kindly", "would you mind",
        "could you please", "at your convenience", "best regards", "kind regards",
    ),
    "formal": ("dear", "regards", "sincerely", "respectfully", "dear sir", "dear madam"),
    "casual": ("hey", "yo", "gonna", "wanna", "lol", "btw", "tbh", "pls", "cool"),
    "apology": ("sorry", "apologise", "apologize", "my mistake", "my fault"),
    "gratitude": ("thank you", "thanks so much", "much appreciated"),
}


def lexicon_counts(text: str) -> dict[str, int]:
    lowered = f" {text.lower()} "
    return {name: sum(lowered.count(term) for term in terms) for name, terms in LEXICONS.items()}


_IMPERATIVES = {
    "send", "do", "fix", "call", "reply", "confirm", "review", "update", "give",
    "get", "make", "check", "provide", "schedule", "book", "stop", "start",
}


def imperative_score(text: str) -> float:
    commands = 0
    for clause in re.split(r"[.!?;\n]+", text):
        words = clause.strip().split()
        if words and words[0].lower().strip(",") in _IMPERATIVES:
            commands += 1
    return float(commands)


@dataclass(frozen=True, slots=True)
class Expectation:
    region: str
    code: str
    category: str
    pattern: str
    message: str
    severity: str = "low"


EXPECTATIONS: tuple[Expectation, ...] = (
    Expectation(
        "JP", "missing_jp_greeting", "greeting",
        r"(お世話|よろしく|ございます|お疲れ|はじめまして|拝啓)",
        "Japanese business threads usually open with a set phrase such as お世話になっております.",
    ),
    Expectation(
        "JP", "missing_jp_honorific", "honorifics",
        r"(さん|様|先生|-san|-sama)",
        "Address form usually carries an honorific (さん/様) for the recipient.",
    ),
    Expectation(
        "CN", "missing_cn_greeting", "greeting",
        r"(您好|你好|尊敬的|老师|经理|总)",
        "Chinese business messages usually open with 您好 and title + surname.",
    ),
    Expectation(
        "AE", "missing_ae_greeting", "greeting",
        r"(salaam|assalam|marhaba|صباح|السلام)",
        "Gulf business greetings often open with As-salaam alaikum or a warm equivalent.",
    ),
    Expectation(
        "DE", "missing_de_salutation", "formality",
        r"(sehr geehrte|guten tag|guten morgen|hallo|liebe)",
        "German business mail normally starts with a formal salutation.",
    ),
    Expectation(
        "IN", "missing_in_warmth", "small_talk",
        r"(hope|trust|greetings|namaste|dear|regards)",
        "Indian business mail usually opens with a short warm line before the request.",
    ),
    Expectation(
        "BR", "missing_br_warmth", "greeting",
        r"(ol[áa]|bom dia|boa tarde|oi|tudo bem)",
        "Brazilian messages usually open with a warm greeting and a personal line.",
    ),
    Expectation(
        "UK", "missing_uk_softener", "formality",
        r"(please|wonder|afraid|perhaps|could|would)",
        "UK business requests are usually softened with please / could / I wonder if.",
    ),
    Expectation(
        "US", "missing_us_ask", "directness",
        r"(please|could|can you|let's|need)",
        "US business messages work best with an explicit ask and a deadline.",
    ),
)


def missing_expectations(text: str, region: str, surface: str) -> list[Expectation]:
    if surface not in ("email_draft", "email_thread", "chat"):
        return []
    missing: list[Expectation] = []
    for expectation in EXPECTATIONS:
        if expectation.region != region.upper():
            continue
        if re.search(expectation.pattern, text, re.IGNORECASE | re.UNICODE):
            continue
        missing.append(expectation)
    return missing


def iter_terms(category: str) -> Iterable[str]:
    return LEXICONS.get(category, ())
