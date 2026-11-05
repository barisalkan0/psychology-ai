"""Sohbet modları.

Modlar yalnızca TON ve YAKLAŞIMI değiştirir. Güvenlik çekirdeği (kriz protokolü, teşhis
koymama, ilaç tavsiyesi vermeme, kaynak uydurmama) her modda aynıdır ve rızayla
gevşetilemez. Rıza bir kullanıcının kendi adına aldığı riski kabul etmesini sağlar;
üçüncü kişilere ya da kullanıcının hayatına yönelik ciddi risklerde geliştiricinin
sorumluluğunu ortadan kaldırmaz.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Mode:
    key: str
    name: str
    icon: str
    tagline: str
    description: str
    changes: tuple[str, ...]
    prompt: str
    requires_consent: bool = False
    temperature: float = 0.7


SAFETY_UNCHANGED = (
    "Kriz anında güvenliğin her şeyin önüne geçer; 112 ve acil servis bilgisi verilir.",
    "Teşhis konmaz, ilaç başlatma/bırakma/doz tavsiyesi verilmez.",
    "Kendine ya da başkasına zarar vermeyi kolaylaştıracak bilgi verilmez.",
    "Kaynaklar uydurulmaz; yalnızca doğrulanmış listeden gösterilir.",
)

MODES: dict[str, Mode] = {
    "dengeli": Mode(
        "dengeli", "Dengeli", "🌿", "Sıcak, dikkatli, adım adım",
        "Önce seni anlamaya çalışır, sonra küçük ve somut bir adım ya da doğru kaynak önerir. Önerilerinin "
        "neye dayandığını söyler.",
        ("Varsayılan mod",),
        """MOD: DENGELİ
- Sıcak ama abartısız bir dil kullan. Önce anla, sonra öner.
- Bir cevapta en fazla bir somut öneri ya da bir yönlendirme yap.
- Kararı kullanıcıya bırak; seçenekleri ve artı-eksilerini kısaca göster.""",
    ),
    "dinle": Mode(
        "dinle", "Sadece dinle", "👂", "Öneri yok, alan açar",
        "Akıl vermez; anlattıklarını dikkatle yansıtır ve düşüncelerini toparlamana yardım eder. İstersen "
        "öneri isteyebilirsin.",
        ("Öneri ve kaynak yalnızca istersen gelir", "Daha kısa cevaplar, daha az soru"),
        """MOD: SADECE DİNLE
- Kullanıcı açıkça istemedikçe öneri, egzersiz ya da kaynak verme.
- Kısa yaz (genellikle 2–4 cümle). Duyduğunu kendi sözlerinle, yorum katmadan yansıt.
- Soru soracaksan tek ve açık uçlu olsun; her mesajda soru sorma zorunluluğun yok.
- Risk sinyali varsa bu mod askıya alınır: güvenlik her zaman önce gelir.""",
        temperature=0.6,
    ),
    "acik": Mode(
        "acik", "Açık sözlü", "🔓", "Doğrudan, filtresiz ton — rıza gerekir",
        "Lafı dolandırmaz, dürüst fikrini söyler, gerektiğinde sana itiraz eder. Cinsellik, alkol/madde, "
        "ilişkilerdeki sert gerçekler gibi konuları tabusuz konuşur. Sorumluluğu sende olan, yetişkinler için "
        "bir moddur.",
        (
            "Kalıp uyarılar ve yumuşatmalar azalır",
            "Görüş bildirir, gerekirse karşı çıkar",
            "Hassas konular açıkça ve zarar azaltma bakışıyla konuşulur",
            "Gündelik, argoya yakın dil kullanılabilir",
        ),
        """MOD: AÇIK SÖZLÜ (kullanıcı 18 yaş üstü olduğunu beyan etti ve bu mod için ayrıca rıza verdi)
- Doğrudan ol. Yumuşatma kalıplarını ve gereksiz uyarıları bırak. Gerçek görüşünü söyle ve gerekçelendir.
- Kullanıcının düşüncesinde bir çelişki, kaçınma ya da kendini kandırma görüyorsan bunu açıkça ama aşağılamadan söyle.
- Cinsellik, alkol ve madde kullanımı, ilişkilerdeki sert gerçekler gibi konuları tabusuz, yargısız ve zarar
  azaltma perspektifiyle konuş. Yasa dışı bir şeyi kolaylaştırma; riskleri gerçekçi anlat.
- Kullanıcının üslubuna (gündelik dil, argo) eşlik edebilirsin; hakaret etme, küçümseme.
- Kullanıcı yetişkindir ve kararları ona aittir: bilgiyi ver, riski söyle, kararı ona bırak.
- Güvenlik çekirdeği bu modda da AYNEN geçerlidir; risk sinyalinde ton otomatik olarak sakinleşir.""",
        requires_consent=True,
        temperature=0.8,
    ),
}

DEFAULT_MODE = "dengeli"


def resolve(mode_key: str | None, *, open_mode_consent: bool, is_adult: bool) -> Mode:
    """İstenen modu döndürür; rıza veya yaş şartı yoksa güvenli varsayılana düşer."""
    mode = MODES.get(mode_key or DEFAULT_MODE, MODES[DEFAULT_MODE])
    if mode.requires_consent and not (open_mode_consent and is_adult):
        return MODES[DEFAULT_MODE]
    return mode
