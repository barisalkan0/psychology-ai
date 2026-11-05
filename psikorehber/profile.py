"""Kayıt (tanışma) soruları.

Tasarım ilkeleri:
- Az ve amaçlı: her soru modelin gerçekten kullandığı bir bilgiyi topluyor. KVKK'nın
  "amaçla sınırlı ve ölçülü" veri ilkesi gereği cinsiyet, şehir, tam yaş gibi cevabı
  yönlendirmeyi değiştirmeyen bilgiler sorulmuyor.
- Her sorunun altında "Neden soruyoruz?" açıklaması var.
- Güvenlik sorusu dışında hepsi atlanabilir; atlamak da bir cevap.
- Cevaplar serbest metin değil, seçenek: modelin bağlamına güvenli şekilde girer ve
  istem enjeksiyonu (prompt injection) yüzeyini küçültür. Tek serbest alan (hitap) kısa
  ve temizlenmiş.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

AGE_BANDS: dict[str, str] = {
    "18-24": "18–24",
    "25-34": "25–34",
    "35-44": "35–44",
    "45-54": "45–54",
    "55-64": "55–64",
    "65+": "65 ve üzeri",
    "<18": "18 yaşından küçüğüm",
}


@dataclass(frozen=True)
class Question:
    key: str
    title: str
    why: str
    options: dict[str, str]
    multi: bool = False
    max_select: int | None = None
    optional: bool = True


QUESTIONS: tuple[Question, ...] = (
    Question(
        "topics",
        "Seni buraya getiren ne?",
        "İlk sohbette doğru yerden başlayabilmek için. En fazla üç tane seçebilirsin.",
        {
            "stres": "Stres, bunalmışlık",
            "kaygi": "Kaygı, endişe, panik",
            "ruh-hali": "Keyifsizlik, isteksizlik, çökkünlük",
            "uyku": "Uyku sorunları",
            "iliskiler": "İlişkiler, aile",
            "yalnizlik": "Yalnızlık",
            "okul-is": "Okul ya da iş baskısı",
            "kayip": "Kayıp, yas",
            "ofke": "Öfke",
            "bagimlilik": "Alkol, madde, kumar ya da ekran kullanımı",
            "beden-yeme": "Beden algısı, yeme",
            "travma": "Sarsıcı bir olay",
            "kesif": "Belirli bir sorun yok, kendimi tanımak istiyorum",
        },
        multi=True,
        max_select=3,
    ),
    Question(
        "duration",
        "Bu durum ne zamandır var?",
        "Süre, kendi başına atılabilecek adımlar ile bir uzmana başvurmak arasındaki dengeyi belirleyen "
        "şeylerden biri. Tek başına belirleyici değil.",
        {
            "gunler": "Birkaç gündür",
            "1-2hafta": "1–2 haftadır",
            "2-4hafta": "2–4 haftadır",
            "1-6ay": "1–6 aydır",
            "6ay+": "6 aydan uzun süredir",
            "gidip-gelen": "Gidip geliyor",
            "yok": "Belirli bir sorun yok",
        },
    ),
    Question(
        "impact",
        "Son iki haftada bu durum günlük hayatını ne kadar etkiledi?",
        "Okul, iş, ilişkiler, uyku ya da kendine bakım gibi alanları düşün. Ne kadar zorlandığın, "
        "yönlendirmenin ne kadar acil olması gerektiğini belirler.",
        {
            "hic": "Hiç",
            "biraz": "Biraz",
            "belirgin": "Belirgin şekilde",
            "cok": "Çok",
            "neredeyse-her-sey": "Neredeyse her şeyi",
        },
    ),
    Question(
        "support",
        "Daha önce ya da şu anda profesyonel destek aldın mı?",
        "Şu an biriyle görüşüyorsan buradaki fikirleri onunla da konuşmanı önerebiliriz. İlaç "
        "kullanıyorsan ilaçla ilgili soruları her zaman hekimine yönlendiririz.",
        {
            "hayir": "Hayır",
            "gecmiste": "Geçmişte terapi ya da danışmanlık aldım",
            "su-an-terapi": "Şu an bir psikolog ya da terapistle görüşüyorum",
            "ilac": "Psikiyatrik ilaç kullanıyorum",
            "belirtmek-istemiyorum": "Belirtmek istemiyorum",
        },
        multi=True,
    ),
    Question(
        "goals",
        "Buradan en çok ne bekliyorsun?",
        "Cevapların tarzını buna göre ayarlıyoruz. Birden fazla seçebilirsin.",
        {
            "dertlesmek": "Anlatıp rahatlamak",
            "anlamak": "Ne yaşadığımı anlamak",
            "adimlar": "Somut, küçük adımlar",
            "yonlendirme": "Kime başvuracağımı öğrenmek",
            "kaynak": "Güvenilir bilgi ve kaynak okumak",
        },
        multi=True,
    ),
    Question(
        "risk",
        "Son iki haftada kendine zarar vermeyi ya da yaşamına son vermeyi düşündüğün oldu mu?",
        "Bu soruyu herkese soruyoruz. Araştırmalar bu konuyu sormanın riski artırmadığını gösteriyor. "
        "Cevabın yalnızca seni doğru desteğe yönlendirmek için kullanılır.",
        {
            "hayir": "Hayır",
            "bazen": "Aklımdan geçtiği oldu",
            "siklikla": "Evet, sık sık",
            "su_an": "Şu an bu düşünceler var",
            "cevapsiz": "Cevaplamak istemiyorum",
        },
        optional=False,
    ),
)

QUESTIONS_BY_KEY = {q.key: q for q in QUESTIONS}

_NICKNAME_OK = re.compile(r"[^\w\sçğıöşüÇĞİÖŞÜ'\-]", re.UNICODE)


def clean_nickname(raw: str | None) -> str:
    """Hitap: harf, rakam, boşluk, kesme ve tire dışındaki her şeyi at, 30 karakterle sınırla."""
    if not raw:
        return ""
    cleaned = _NICKNAME_OK.sub("", raw).strip()
    return re.sub(r"\s+", " ", cleaned)[:30]


def validate(answers: dict) -> list[str]:
    """Eksik zorunlu cevapları ve kural ihlallerini döndürür (boş liste = geçerli)."""
    errors = []
    for q in QUESTIONS:
        value = answers.get(q.key)
        if not q.optional and not value:
            errors.append(f"“{q.title}” sorusunu cevaplaman gerekiyor (“Cevaplamak istemiyorum” da bir cevap).")
        if value is None:
            continue
        values = value if isinstance(value, list) else [value]
        unknown = [v for v in values if v not in q.options]
        if unknown:
            errors.append(f"“{q.title}” için geçersiz seçenek.")
        if q.max_select and len(values) > q.max_select:
            errors.append(f"“{q.title}” için en fazla {q.max_select} seçenek seçebilirsin.")
    return errors


def label(key: str, value) -> str:
    q = QUESTIONS_BY_KEY[key]
    if value in (None, [], ""):
        return "—"
    if isinstance(value, list):
        return ", ".join(q.options.get(v, v) for v in value)
    return q.options.get(value, value)


def summary_for_prompt(nickname: str, age_band: str, answers: dict) -> str:
    """Modele verilecek profil özeti. JSON olarak verilir ki talimat gibi okunmasın."""
    data = {"hitap": nickname or None, "yas_araligi": AGE_BANDS.get(age_band, age_band)}
    for q in QUESTIONS:
        data[q.key] = label(q.key, answers.get(q.key))
    return json.dumps(data, ensure_ascii=False, indent=1)


def needs_prompt_referral(answers: dict) -> bool:
    """Profil tek başına uzman yönlendirmesini öne çıkarmayı gerektiriyor mu?"""
    long = answers.get("duration") in {"2-4hafta", "1-6ay", "6ay+", "gidip-gelen"}
    heavy = answers.get("impact") in {"cok", "neredeyse-her-sey"}
    return heavy or (long and answers.get("impact") == "belirgin")
