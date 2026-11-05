"""Deterministik risk tespiti.

Neden modelin kendisine bırakmıyoruz?
    1. Model bazen sinyali kaçırır ya da güvenlik filtresi cevabı tamamen engeller;
       en çok ihtiyaç duyulan anda ekranda hiçbir şey çıkmayabilir.
    2. Yardım hatları bilgisi uydurulmamalı (eski sürüm 182'yi kriz hattı sanıyordu,
       oysa 182 MHRS randevu hattı).
Bu katman kullanıcının mesajını model cevap vermeden önce tarar. Risk varsa:
    - Arayüz modelden bağımsız, sabit ve doğrulanmış bir kriz kartı gösterir.
    - Modele "bu mesajda risk sinyali var" notu iletilir.

Sınırlar: Anahtar kelime eşleştirmesi dolaylı anlatımları kaçırabilir ve bazen yanlış
alarm verir. Bu yüzden kart suçlamayan, "eğer..." diye başlayan bir dille yazıldı ve
model de ayrıca riski değerlendirmekle görevli. Bu katman bir güvenlik ağıdır, klinik
bir değerlendirme aracı değildir.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from .text import fold

Level = Literal["none", "concern", "high"]

# Kalıplar fold() edilmiş metin üzerinde çalışır: küçük harf, Türkçe karakterler ASCII.
_PATTERNS: dict[str, tuple[str, ...]] = {
    "self_harm": (
        r"\bintihar\w*",
        r"\bkendimi\s+(oldur|as(ar|mak|acag|sam|ip)|vur(mak|acag|sam)|yak(mak|acag|sam)|bitir)\w*",
        r"\bkendimi\s+(kes|yarala|cizi|ciziyor|ciz(dim|mek))\w*",
        r"\bkendime\s+zarar\s+ver\w*",
        r"\bolmek\s+isti\w*",
        r"\bolesi(m|miz)\s+gel\w*",
        r"\bolsem\b",
        r"\bolmeyi\s+(dusun|isti|planl)\w*",
        r"\bolmeliyim\b",
        r"\bolup\s+gitmek\w*",
        r"\byasamak\s+istemi\w*",
        r"\byasamak\s+icin\s+(bir\s+)?(sebeb|neden)\w*\s+(yok|kalmadi)",
        r"\byasamanin\s+(bir\s+)?anlami\s+(yok|kalmadi)",
        r"\bcanima\s+kiy\w*",
        r"\bhayatima\s+son\s+ver\w*",
        r"\bhayatimi\s+(bitir|sonlandir)\w*",
        r"\bbilek\w*\s+(\w+\s+)?kes\w*",
        r"\b(kopru|balkon|pencere|cati|bina)\w*\s+(\w+\s+)?atla\w*",
    ),
    "self_harm_concern": (
        r"\byok\s+olmak\s+isti\w*",
        r"\byok\s+olsam\b",
        r"\bortadan\s+kaybolmak\s+isti\w*",
        r"\buyanmasam\b",
        r"\bbir\s+daha\s+uyanmak\s+istemi\w*",
        r"\bartik\s+dayanam\w*",
        r"\bdayanamiyorum\b",
        r"\bkaldiramiyorum\b",
        r"\bher\s+sey\w*\s+anlamsiz\w*",
        r"\bhicbir\s+seyin\s+anlami\s+(yok|kalmadi)",
        r"\bkimse\s+(fark\s+etmez|umursamaz|ozlemez)\w*",
        r"\bben\s+olmasam\b",
        r"\bherkes\s+bensiz\s+daha\s+iyi",
        r"\b(herkese|ailemize?|aileme)\s+yuk\s+(oluyorum|oldum)",
        r"\bumudum\s+(yok|kalmadi)",
        r"\bjilet\w*",
    ),
    "harm_to_others": (
        r"(?<!kendimi )\boldur(ecegim|ecek\s+gibiyim|mek\s+isti\w*|meyi\s+dusun\w*)",
        r"(?<!kendime )\bzarar\s+(verecegim|vermek\s+isti\w*)",
    ),
    "violence": (
        r"\b(beni|bizi)\s+(dov|darp|tehdit\s+ed|bogmaya)\w*",
        r"\b(esim|sevgilim|babam|annem|kocam|karim|nisanlim|abim|agabeyim|uvey\s+\w+)\s+(beni\s+)?"
        r"(dov|vur|darp|tehdit)\w*",
        r"\b(siddet|istismar|taciz)\w*\s+(goruyorum|gordum|ugradim|ugruyorum|ediyor|etti|ediliyorum)",
        r"\btecavuz\w*",
        r"\bistismar\w*",
    ),
    "overdose": (
        r"\b(cok|fazla|bir\s+kutu|kutu|avuc\s+dolusu|butun)\s+(\w+\s+){0,2}(ilac|hap)\w*\s+(\w+\s+)?(ictim|yuttum|aldim)",
        r"\b(ilac|hap)\w*\s+(\w+\s+)?(fazla|cok)\s+(ictim|yuttum|aldim)",
        r"\bzehir\w*\s+(ictim|aldim|yuttum)",
        r"\bzehirlendim\b",
    ),
    "minor": (
        r"\b(1[0-7]|[6-9])\s*yas(indayim|im)\b",
        r"\blise(deyim|ye\s+gidiyorum|\s+[1-4]\s*\W?\s*(e|de|te)\w*)",
        r"\bortaokul\w*\s+(gidiyorum|okuyorum)",
    ),
}

_COMPILED = {cat: tuple(re.compile(p) for p in pats) for cat, pats in _PATTERNS.items()}

_HIGH = {"self_harm", "harm_to_others", "violence", "overdose"}


@dataclass
class Assessment:
    level: Level = "none"
    categories: set[str] = field(default_factory=set)
    matched: list[str] = field(default_factory=list)

    @property
    def minor(self) -> bool:
        return "minor" in self.categories

    @property
    def needs_card(self) -> bool:
        return self.level != "none"

    def merge(self, other: "Assessment") -> "Assessment":
        order = {"none": 0, "concern": 1, "high": 2}
        level = self.level if order[self.level] >= order[other.level] else other.level
        return Assessment(level, self.categories | other.categories, self.matched + other.matched)


def assess(text: str) -> Assessment:
    folded = fold(text)
    cats: set[str] = set()
    matched: list[str] = []
    for cat, patterns in _COMPILED.items():
        for pat in patterns:
            m = pat.search(folded)
            if m:
                cats.add(cat)
                matched.append(m.group(0))
                break
    if cats & _HIGH:
        level: Level = "high"
    elif "self_harm_concern" in cats:
        level = "concern"
    else:
        level = "none"
    return Assessment(level, cats, matched)


def assess_onboarding(risk_answer: str | None) -> Assessment:
    """Kayıt sırasındaki güvenlik sorusunun cevabını aynı ölçeğe çevirir."""
    if risk_answer in {"siklikla", "su_an"}:
        return Assessment("high", {"self_harm"}, [f"onboarding:{risk_answer}"])
    if risk_answer == "bazen":
        return Assessment("concern", {"self_harm_concern"}, ["onboarding:bazen"])
    return Assessment()


def prompt_note(a: Assessment) -> str:
    """Modele iletilecek, kullanıcıya görünmeyen durum notu."""
    notes = []
    if "self_harm" in a.categories:
        notes.append(
            "Son mesajda kendine zarar verme / intihar ile ilgili olası bir ifade tespit edildi (anahtar kelime "
            "taraması; yanlış alarm olabilir). KRİZ PROTOKOLÜNÜ uygula: önce sakin ve doğrudan şu an güvende olup "
            "olmadığını sor. Uygulama ekranda zaten 112 ve acil servis bilgisini gösteriyor; sen de kısaca hatırlat."
        )
    elif "self_harm_concern" in a.categories:
        notes.append(
            "Son mesajda umutsuzluk ya da dolaylı bir risk ifadesi olabilir. Bunu geçiştirme; nazikçe ve açıkça "
            "kendine zarar verme düşünceleri olup olmadığını sor."
        )
    if "harm_to_others" in a.categories:
        notes.append(
            "Son mesajda başkasına zarar verme ifadesi olabilir. Abartı mı ciddi mi, sakin bir dille netleştir. "
            "Ciddiyse herkesin güvenliği için 112'yi ve ortamdan uzaklaşmayı öncele."
        )
    if "violence" in a.categories:
        notes.append(
            "Son mesajda şiddet ya da istismara uğrama ifadesi olabilir. Yargılamadan dinle, suçun kullanıcıda "
            "olmadığını belirt; acil tehlikede 112, destek için 183 (ve kadınlar için KADES) seçeneklerini hatırlat."
        )
    if "overdose" in a.categories:
        notes.append(
            "Son mesajda ilaç/madde fazla alımı ya da zehirlenme olabilir. Bu tıbbi bir acil durum olabilir: "
            "hemen 112'yi (bilinç ve nefes yerindeyse danışmak için 114 UZEM'i) aramasını söyle, başka konuya geçme."
        )
    if a.minor:
        notes.append(
            "Kullanıcı 18 yaşından küçük olduğunu belirtmiş olabilir. Uygulama 18 yaş üstü içindir: nazikçe belirt, "
            "güvendiği bir yetişkinle (aile, okul rehber öğretmeni) konuşmasını öner; açık sözlü mod içeriği verme."
        )
    return "\n".join(notes)
