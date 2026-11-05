"""Rıza ve aydınlatma metinleri.

ÖNEMLİ: Bu metinler hukuki görüş değildir. Uygulamayı gerçek kullanıcılara açmadan önce
bir KVKK avukatına inceletilmelidir. Ayrıntılar: docs/HUKUKI_NOTLAR.md

Tasarım kararları:
- Her rıza ayrı bir onay kutusu; hiçbiri önceden işaretli değil, birbirine bağlanmıyor.
- Her rıza sürümüyle birlikte kaydedilir. Metin değişirse sürüm artırılır ve kullanıcıdan
  yeniden onay istenir (eski onay yeni metni kapsamaz).
- Zorunlu olanlar sadece hizmetin çalışması için gerçekten gereken iki şey.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import Settings


@dataclass(frozen=True)
class ConsentItem:
    kind: str
    version: str
    required: bool
    label: str
    detail: str


DISCLAIMER = ConsentItem(
    "disclaimer", "2", True,
    "Psycalm'ın bir terapist, doktor ya da acil servis olmadığını; teşhis koymadığını ve tedavi önermediğini "
    "anladım. Verdiği bilgileri kendi değerlendirmemle kullanacağım.",
    "Psycalm bir yapay zekâ yönlendirme asistanıdır. Ne yaşadığını anlamana, güvenilir bilgiye ve doğru "
    "uzmana ulaşmana yardım eder. Cevapları hatalı olabilir. Acil bir durumda 112'yi ara.",
)

PROCESSING = ConsentItem(
    "processing", "2", True,
    "Mesajlarımın ve tanışma sorularındaki cevaplarımın (ruh hâlim ve sağlığımla ilgili bilgiler dahil) cevap "
    "üretmek amacıyla işlenmesine ve bu amaçla yurt dışındaki yapay zekâ sağlayıcısına aktarılmasına açık "
    "rıza veriyorum.",
    "Bu onay olmadan sohbet çalışamaz: yazdıkların, cevap üretilmesi için Google'ın Gemini API hizmetine "
    "gönderilir ve bu sunucular yurt dışındadır.",
)

MEMORY = ConsentItem(
    "memory", "1", False,
    "Sohbetlerimden kısa notlar çıkarılıp sonraki sohbetlerde kullanılmasına izin veriyorum.",
    "Notları Hafıza sayfasında görebilir, düzenleyebilir ve silebilirsin. Bu izni istediğin zaman geri alabilirsin; "
    "geri aldığında tüm notlar silinir.",
)

OPEN_MODE = ConsentItem(
    "open_mode", "1", False,
    "18 yaşından büyüğüm. Açık sözlü modda cevapların daha doğrudan, sert ya da rahatsız edici olabileceğini, "
    "hassas konuların açıkça konuşulacağını biliyorum ve bu cevapları kendi sorumluluğumda değerlendireceğim.",
    "Bu mod güvenlik kurallarını kapatmaz: kriz anında yine güvenliğin öncelenir, teşhis ve ilaç tavsiyesi "
    "verilmez. İstediğin zaman Dengeli moda dönebilir ve bu izni geri alabilirsin.",
)

ALL_ITEMS = {c.kind: c for c in (DISCLAIMER, PROCESSING, MEMORY, OPEN_MODE)}
REQUIRED = (DISCLAIMER, PROCESSING)


def provider_notice(settings: Settings) -> str:
    if settings.paid_tier:
        return (
            "Bu kurulum Gemini API'nin **ücretli** kotasını kullanıyor. Google'ın şartlarına göre ücretli kotadaki "
            "içerikler Google ürünlerini geliştirmek için kullanılmaz."
        )
    return (
        "Bu kurulum Gemini API'nin **ücretsiz** kotasını kullanıyor olabilir. Google'ın şartlarına göre ücretsiz "
        "kotada gönderilen içerikler Google ürünlerini geliştirmek için kullanılabilir ve insan değerlendiriciler "
        "tarafından okunabilir. Bu yüzden **adını, adresini, T.C. kimlik numaranı ya da seni tanıtacak başka "
        "bilgileri yazma.**"
    )


def information_notice(settings: Settings) -> str:
    """KVKK m.10 aydınlatma metni (özet). Yer tutucular .env'den doldurulur."""
    return f"""
**Veri sorumlusu:** {settings.controller_name} — {settings.controller_contact}

**Hangi verileri işliyoruz?**
- Hesap: kullanıcı adı, şifrenin geri döndürülemez özeti (şifrenin kendisi saklanmaz), yaş aralığı.
- Tanışma cevapları: seçtiğin konular, süre, günlük hayata etkisi, destek geçmişi, beklentiler ve güvenlik sorusu.
- Sohbetler: yazdığın mesajlar ve verilen cevaplar.
- İzin verirsen: sohbetlerden çıkarılan kısa hafıza notları.
- Rıza kayıtları: hangi metni hangi sürümüyle ne zaman onayladığın.

**Neden?** Sana kişiye uygun cevap üretmek, gerektiğinde seni doğru desteğe yönlendirmek ve geçmiş
sohbetlerini sana göstermek için. Reklam, profil satışı ya da üçüncü kişilerle paylaşım yoktur.

**Hukuki sebep:** Sağlık verisi özel nitelikli kişisel veridir. Bu veriler açık rızana dayanarak işlenir (KVKK m.6).

**Yurt dışına aktarım:** Mesajların cevap üretimi için Google LLC'nin Gemini API hizmetine (yurt dışındaki
sunucular) gönderilir (KVKK m.9). {provider_notice(settings)}

**Nerede ve ne kadar süre?** Veriler bu uygulamanın çalıştığı sunucudaki veritabanında, sen hesabını silene kadar
saklanır. Sohbetleri tek tek, hafızayı ya da hesabının tamamını Ayarlar'dan istediğin an silebilirsin.

**Hakların (KVKK m.11):** Verilerini görme, indirme, düzeltme ve silme; rızanı geri alma. Ayarlar sayfasından
verilerini indirebilir ve silebilirsin; diğer talepler için veri sorumlusuna yazabilirsin.
"""
