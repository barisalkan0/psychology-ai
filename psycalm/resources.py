"""Doğrulanmış kaynaklar, yardım hatları ve "kime başvurmalıyım" rehberi.

Neden kapalı bir katalog?
    Eski sürüm modele "gerçek kaynak ver, link ekle, ama uydurma" diyordu. Dil modelleri
    erişimi olmadan link ve DOI üretmeye zorlanınca tam olarak uydurur. Burada model
    yalnızca bu listedeki kimlikleri ([kaynak:who-depression] gibi) kullanabilir; linkleri
    uygulama ekler. Listede olmayan bir kimlik ekrana hiç çıkmaz.

Her kayda bir "dayanak düzeyi" (evidence) eklendi; kullanıcı "neye dayanarak?" sorusunun
cevabını akademik dile girmeden görebilsin diye.

Bakım notu: Telefon numaraları ve linkler değişebilir. VERIFIED_ON tarihini güncellemeden
önce her kaydı resmi kaynağından tekrar kontrol et.
"""

from __future__ import annotations

from dataclasses import dataclass, field

VERIFIED_ON = "2026-11"


# ─────────────────────────── Dayanak düzeyleri ───────────────────────────
@dataclass(frozen=True)
class EvidenceLevel:
    key: str
    label: str
    icon: str
    meaning: str


EVIDENCE = {
    "guclu": EvidenceLevel(
        "guclu", "Güçlü dayanak", "🟢",
        "Klinik kılavuzlar ya da çok sayıda çalışmayı birleştiren analizler destekliyor.",
    ),
    "orta": EvidenceLevel(
        "orta", "Orta / sınırlı dayanak", "🟡",
        "Destekleyen çalışmalar var ama az, küçük ya da sonuçları karışık.",
    ),
    "deneyim": EvidenceLevel(
        "deneyim", "Yaygın uygulama", "⚪",
        "Uzmanların sık kullandığı ama doğrudan araştırması az olan bir yaklaşım.",
    ),
    "kurum": EvidenceLevel(
        "kurum", "Resmî / kurumsal bilgi", "🔵",
        "Bir kamu kurumu ya da meslek kuruluşunun yayımladığı bilgi veya hizmet.",
    ),
}


# ─────────────────────────────── Kaynaklar ───────────────────────────────
@dataclass(frozen=True)
class Source:
    id: str
    title: str  # Türkçe, kullanıcıya görünen başlık
    publisher: str
    url: str
    kind: str  # "kılavuz" | "bilgi" | "araştırma" | "hizmet"
    evidence: str  # EVIDENCE anahtarı
    topics: tuple[str, ...]
    supports: str  # Bu kaynak neyi destekliyor? (modele ve kullanıcıya)
    language: str = "en"


SOURCES: tuple[Source, ...] = (
    # ── Klinik kılavuzlar ──
    Source(
        "nice-depression", "Yetişkinlerde depresyon: tedavi ve yönetim (NG222)", "NICE (Birleşik Krallık)",
        "https://www.nice.org.uk/guidance/ng222", "kılavuz", "guclu", ("ruh-hali",),
        "Hafif depresyonda yönlendirilmiş kendi kendine yardım, davranışsal aktivasyon, BDT ve grup egzersizi; "
        "daha ağır durumlarda terapi ve/veya ilaç. Basamaklı bakım yaklaşımı.",
    ),
    Source(
        "nice-anxiety", "Yaygın anksiyete bozukluğu ve panik bozukluk (CG113)", "NICE (Birleşik Krallık)",
        "https://www.nice.org.uk/guidance/cg113", "kılavuz", "guclu", ("kaygi",),
        "Kaygıda basamaklı bakım: bilgilendirme ve izleme, kendi kendine yardım, BDT ve uygulamalı gevşeme; "
        "gerekirse ilaç.",
    ),
    Source(
        "nice-social-anxiety", "Sosyal kaygı bozukluğu (CG159)", "NICE (Birleşik Krallık)",
        "https://www.nice.org.uk/guidance/cg159", "kılavuz", "guclu", ("kaygi", "iliskiler"),
        "Sosyal kaygıda ilk seçenek olarak sosyal kaygıya özgü BDT.",
    ),
    Source(
        "nice-ptsd", "Travma sonrası stres bozukluğu (NG116)", "NICE (Birleşik Krallık)",
        "https://www.nice.org.uk/guidance/ng116", "kılavuz", "guclu", ("travma",),
        "Travma sonrası belirtilerde travma odaklı BDT ve EMDR gibi travmaya odaklanan terapiler.",
    ),
    Source(
        "nice-ocd", "Obsesif-kompulsif bozukluk (CG31)", "NICE (Birleşik Krallık)",
        "https://www.nice.org.uk/guidance/cg31", "kılavuz", "guclu", ("kaygi",),
        "Takıntılı düşünce ve zorlantılarda maruz bırakma ve tepki önlemeyi içeren BDT.",
    ),
    Source(
        "nice-eating", "Yeme bozuklukları (NG69)", "NICE (Birleşik Krallık)",
        "https://www.nice.org.uk/guidance/ng69", "kılavuz", "guclu", ("beden-yeme",),
        "Yeme bozukluklarında erken uzman değerlendirmesinin önemi ve bozukluğa özgü terapiler.",
    ),
    Source(
        "nice-selfharm", "Kendine zarar verme: değerlendirme ve yönetim (NG225)", "NICE (Birleşik Krallık)",
        "https://www.nice.org.uk/guidance/ng225", "kılavuz", "guclu", ("kriz",),
        "Kendine zarar verme davranışında yargılamadan yaklaşım ve profesyonel değerlendirme.",
    ),
    Source(
        "acp-insomnia", "Kronik uykusuzlukta ilk basamak: uykusuzluk için BDT (BDT-U)", "American College of Physicians, 2016",
        "https://doi.org/10.7326/M15-2175", "kılavuz", "guclu", ("uyku",),
        "Kronik uykusuzlukta ilk tedavi seçeneği olarak ilaç yerine uykusuzluğa özgü bilişsel davranışçı terapi.",
    ),
    # ── Kurumsal bilgi sayfaları ──
    Source(
        "who-depression", "Depresyon bilgi notu", "Dünya Sağlık Örgütü (WHO)",
        "https://www.who.int/news-room/fact-sheets/detail/depression", "bilgi", "kurum", ("ruh-hali",),
        "Depresyonun belirtileri, ne kadar yaygın olduğu ve etkili tedavilerin var olduğu.",
    ),
    Source(
        "who-anxiety", "Kaygı (anksiyete) bozuklukları bilgi notu", "Dünya Sağlık Örgütü (WHO)",
        "https://www.who.int/news-room/fact-sheets/detail/anxiety-disorders", "bilgi", "kurum", ("kaygi",),
        "Kaygı bozukluklarının belirtileri ve tedavi edilebilir olduğu.",
    ),
    Source(
        "who-suicide", "İntihar bilgi notu", "Dünya Sağlık Örgütü (WHO)",
        "https://www.who.int/news-room/fact-sheets/detail/suicide", "bilgi", "kurum", ("kriz",),
        "İntiharın önlenebilir olduğu, risk faktörleri ve destek almanın önemi.",
    ),
    Source(
        "who-stress-guide", "Stresli Zamanlarda Önemli Olanı Yapmak (resimli rehber)", "Dünya Sağlık Örgütü (WHO)",
        "https://www.who.int/publications/i/item/9789240003927", "bilgi", "kurum", ("stres", "ruh-hali", "kaygi"),
        "Stresle baş etmek için kanıta dayalı, kendi kendine uygulanabilir beceriler (topraklanma, değerlerle hareket).",
    ),
    Source(
        "nimh-depression", "Depresyon", "ABD Ulusal Ruh Sağlığı Enstitüsü (NIMH)",
        "https://www.nimh.nih.gov/health/topics/depression", "bilgi", "kurum", ("ruh-hali",),
        "Depresyon belirtileri, türleri ve tedavi seçenekleri.",
    ),
    Source(
        "nimh-anxiety", "Kaygı bozuklukları", "ABD Ulusal Ruh Sağlığı Enstitüsü (NIMH)",
        "https://www.nimh.nih.gov/health/topics/anxiety-disorders", "bilgi", "kurum", ("kaygi",),
        "Yaygın kaygı, panik ve sosyal kaygının belirtileri ve tedavileri.",
    ),
    Source(
        "nimh-ptsd", "Travma sonrası stres bozukluğu", "ABD Ulusal Ruh Sağlığı Enstitüsü (NIMH)",
        "https://www.nimh.nih.gov/health/topics/post-traumatic-stress-disorder-ptsd", "bilgi", "kurum", ("travma",),
        "Travma sonrası tepkiler, ne zaman destek alınması gerektiği.",
    ),
    Source(
        "nimh-bipolar", "Bipolar bozukluk", "ABD Ulusal Ruh Sağlığı Enstitüsü (NIMH)",
        "https://www.nimh.nih.gov/health/topics/bipolar-disorder", "bilgi", "kurum", ("ruh-hali",),
        "Aşırı yükselme (mani) ve çökkünlük dönemlerinin belirtileri; psikiyatrik değerlendirme gereği.",
    ),
    Source(
        "nimh-eating", "Yeme bozuklukları", "ABD Ulusal Ruh Sağlığı Enstitüsü (NIMH)",
        "https://www.nimh.nih.gov/health/topics/eating-disorders", "bilgi", "kurum", ("beden-yeme",),
        "Yeme bozukluklarının ciddi ama tedavi edilebilir olduğu.",
    ),
    Source(
        "nimh-psychotherapies", "Psikoterapi türleri", "ABD Ulusal Ruh Sağlığı Enstitüsü (NIMH)",
        "https://www.nimh.nih.gov/health/topics/psychotherapies", "bilgi", "kurum", ("genel",),
        "BDT, DBT ve diğer terapi türlerinin ne olduğu ve nasıl terapist seçileceği.",
    ),
    Source(
        "nhs-insomnia", "Uykusuzluk", "NHS (Birleşik Krallık)",
        "https://www.nhs.uk/conditions/insomnia/", "bilgi", "kurum", ("uyku",),
        "Uykusuzluğun nedenleri, kendi başına denenebilecekler ve ne zaman doktora gidileceği.",
    ),
    Source(
        "mind-info", "Ruh sağlığı bilgi ve destek sayfaları", "Mind (Birleşik Krallık, sivil toplum kuruluşu)",
        "https://www.mind.org.uk/information-support/", "bilgi", "kurum", ("genel",),
        "Pek çok ruh sağlığı konusunda sade dille yazılmış bilgi.",
    ),
    # ── Araştırmalar ──
    Source(
        "exercise-depression", "Depresyonda egzersizin etkisi: 218 çalışmanın analizi", "Noetel ve ark., BMJ 2024",
        "https://doi.org/10.1136/bmj-2023-075847", "araştırma", "orta", ("ruh-hali",),
        "Yürüyüş/koşu, yoga ve kuvvet antrenmanı depresif belirtilerde orta düzeyde azalma ile ilişkili; "
        "çalışmaların kesinlik düzeyi düşük.",
    ),
    Source(
        "behavioral-activation", "Davranışsal aktivasyon (etkinlik planlama) çalışmalarının analizi",
        "Cuijpers ve ark., Clinical Psychology Review 2007",
        "https://doi.org/10.1016/j.cpr.2006.11.001", "araştırma", "guclu", ("ruh-hali",),
        "Keyif ve anlam veren küçük etkinlikleri planlamak depresyonda etkili; diğer terapilere benzer sonuç.",
    ),
    Source(
        "breathwork-meta", "Nefes egzersizlerinin stres üzerine etkisi: kontrollü çalışmaların analizi",
        "Fincham ve ark., Scientific Reports 2023",
        "https://doi.org/10.1038/s41598-022-27247-y", "araştırma", "orta", ("stres", "kaygi", "nefes"),
        "Nefes çalışmaları stresi küçük-orta düzeyde azaltıyor; çalışmalar az ve orta yanlılık riskli.",
    ),
    Source(
        "cyclic-sighing", "Kısa nefes egzersizleri ve ruh hâli (döngüsel iç çekiş)", "Balban ve ark., Cell Reports Medicine 2023",
        "https://doi.org/10.1016/j.xcrm.2022.100895", "araştırma", "orta", ("stres", "nefes"),
        "Günde 5 dakika döngüsel iç çekiş, bir ay boyunca ruh hâlini farkındalık meditasyonundan daha fazla iyileştirdi; "
        "tek bir çalışma.",
    ),
    Source(
        "slow-breathing-review", "Yavaş nefesin beden ve zihin üzerindeki etkileri (sistematik derleme)",
        "Zaccaro ve ark., Frontiers in Human Neuroscience 2018",
        "https://doi.org/10.3389/fnhum.2018.00353", "araştırma", "orta", ("nefes", "stres"),
        "Dakikada 10'dan az nefesle yapılan yavaş nefes, otonom sinir sistemi ve duygusal durumla ilişkili.",
    ),
    Source(
        "asking-about-suicide", "İntiharı sormak riski artırır mı?", "Dazzi ve ark., Psychological Medicine 2014",
        "https://doi.org/10.1017/S0033291714001299", "araştırma", "orta", ("kriz",),
        "İntihar düşüncelerini sormanın bu düşünceleri artırdığına dair kanıt bulunmadı.",
    ),
    Source(
        "therapeutic-alliance", "Terapötik ilişki ve terapi sonucu: 295 çalışmanın analizi",
        "Flückiger ve ark., Psychotherapy 2018",
        "https://doi.org/10.1037/pst0000172", "araştırma", "guclu", ("genel",),
        "Danışan ile terapist arasındaki güven ve iş birliği, terapinin sonucunu tutarlı biçimde etkiliyor.",
    ),
    Source(
        "social-connection", "Sosyal ilişkiler ve sağlık: 148 çalışmanın analizi", "Holt-Lunstad ve ark., PLOS Medicine 2010",
        "https://doi.org/10.1371/journal.pmed.1000316", "araştırma", "guclu", ("yalnizlik", "iliskiler"),
        "Güçlü sosyal bağlar daha iyi sağlık ve daha uzun yaşamla ilişkili.",
    ),
    # ── Türkiye'deki hizmetler ──
    Source(
        "mhrs", "MHRS — Merkezi Hekim Randevu Sistemi", "T.C. Sağlık Bakanlığı",
        "https://www.mhrs.gov.tr", "hizmet", "kurum", ("yonlendirme",),
        "Devlet hastanelerinden psikiyatri dahil randevu almak için (telefonla: 182). Kriz hattı değildir.", "tr",
    ),
    Source(
        "yedam", "Yeşilay Danışmanlık Merkezi (YEDAM)", "Yeşilay",
        "https://www.yedam.org.tr", "hizmet", "kurum", ("bagimlilik",),
        "Alkol, madde, tütün, kumar ve teknoloji bağımlılığında kişiye ve ailesine ücretsiz danışmanlık (115).", "tr",
    ),
    Source(
        "aile-bakanligi", "ALO 183 Sosyal Destek Hattı", "T.C. Aile ve Sosyal Hizmetler Bakanlığı",
        "https://www.aile.gov.tr", "hizmet", "kurum", ("siddet",),
        "Şiddet, istismar ve ihmal durumlarında destek ve ihbar (183, 7/24).", "tr",
    ),
    Source(
        "tpd", "Türkiye Psikiyatri Derneği", "Türkiye Psikiyatri Derneği",
        "https://www.psikiyatri.org.tr", "bilgi", "kurum", ("genel", "yonlendirme"),
        "Psikiyatrik konularda Türkçe halk bilgilendirme yazıları.", "tr",
    ),
    Source(
        "turk-psikologlar", "Türk Psikologlar Derneği", "Türk Psikologlar Derneği",
        "https://www.psikolog.org.tr", "bilgi", "kurum", ("genel", "yonlendirme"),
        "Psikologların meslek kuruluşu; psikolojik destek ve meslek etiği hakkında bilgi.", "tr",
    ),
    Source(
        "findahelpline", "Find A Helpline — ülkelere göre yardım hatları", "Throughline",
        "https://findahelpline.com", "hizmet", "kurum", ("kriz", "yonlendirme"),
        "Türkiye dışındaysan bulunduğun ülkedeki ücretsiz ve gizli destek hatları.",
    ),
)

SOURCES_BY_ID: dict[str, Source] = {s.id: s for s in SOURCES}

TOPIC_LABELS: dict[str, str] = {
    "genel": "Genel",
    "ruh-hali": "Ruh hâli / depresyon",
    "kaygi": "Kaygı",
    "stres": "Stres",
    "uyku": "Uyku",
    "travma": "Travma",
    "iliskiler": "İlişkiler",
    "yalnizlik": "Yalnızlık",
    "beden-yeme": "Beden ve yeme",
    "bagimlilik": "Bağımlılık",
    "siddet": "Şiddet ve istismar",
    "kriz": "Kriz ve intihar",
    "nefes": "Nefes",
    "yonlendirme": "Nereye başvurmalı",
}


# ───────────────────────────── Yardım hatları ─────────────────────────────
@dataclass(frozen=True)
class Helpline:
    number: str
    name: str
    when: str
    hours: str
    note: str = ""
    is_emergency: bool = False


HELPLINES: tuple[Helpline, ...] = (
    Helpline(
        "112", "Acil Çağrı Merkezi",
        "Hayati tehlike: kendine ya da başkasına zarar verme riski, şiddet, zehirlenme, kaza. Polis, ambulans ve "
        "itfaiye 2021'den beri tek numarada.",
        "7/24 · ücretsiz", is_emergency=True,
    ),
    Helpline(
        "183", "ALO 183 Sosyal Destek Hattı",
        "Şiddet, istismar, ihmal; kadın, çocuk, yaşlı, engelli ve aileler için destek ve ihbar.",
        "7/24 · ücretsiz", "Türkçe, Arapça ve Kürtçe hizmet verdiği duyuruldu.",
    ),
    Helpline(
        "114", "Ulusal Zehir Danışma Merkezi (UZEM)",
        "İlaç ya da madde fazla alındıysa, zehirlenme şüphesi varsa.",
        "7/24 · ücretsiz", "Bilinç bulanıklığı veya nefes sorunu varsa önce 112.",
    ),
    Helpline(
        "115", "Yeşilay Danışmanlık Hattı (YEDAM)",
        "Alkol, madde, tütün, kumar ya da teknoloji bağımlılığı; kişinin kendisi veya ailesi için.",
        "Ücretsiz · çalışma saatleri değişebilir",
    ),
    Helpline(
        "182", "MHRS randevu hattı",
        "Devlet hastanelerinden psikiyatri dahil randevu almak için. Ayrıca mhrs.gov.tr ve e-Nabız.",
        "Randevu hattı", "Kriz ya da intihar önleme hattı DEĞİLDİR. Acil durumda 112.",
    ),
)

KADES_NOTE = (
    "Kadına yönelik şiddette KADES uygulaması (Emniyet Genel Müdürlüğü) tek dokunuşla polise ihbar gönderir."
)
ABROAD_NOTE = "Türkiye dışındaysan: findahelpline.com bulunduğun ülkedeki ücretsiz ve gizli hatları listeler."
EMERGENCY_ROOM_NOTE = "En yakın hastanenin acil servisine kendin gidebilir ya da bir yakınından seni götürmesini isteyebilirsin."


# ─────────────────────────── Kime başvurmalıyım? ───────────────────────────
@dataclass(frozen=True)
class Specialist:
    key: str
    title: str
    who: str
    when: tuple[str, ...]
    how: str
    cost: str
    sources: tuple[str, ...] = field(default_factory=tuple)


SPECIALISTS: tuple[Specialist, ...] = (
    Specialist(
        "aile-hekimi", "Aile hekimi",
        "Çoğu zaman ilk durak. Yorgunluk, uyku, iştah ya da çarpıntı gibi şikâyetlerin fiziksel bir nedeni "
        "(ör. tiroid, kansızlık, vitamin eksikliği) olup olmadığına bakar, gerekirse sevk eder.",
        ("Belirtilerin bedensel tarafı da varsa", "Nereden başlayacağını bilmiyorsan"),
        "Kayıtlı olduğun aile sağlığı merkezi; e-Nabız'dan aile hekimini görebilirsin.",
        "Ücretsiz",
    ),
    Specialist(
        "psikiyatrist", "Psikiyatrist (ruh sağlığı ve hastalıkları uzmanı)",
        "Tıp doktorudur. Değerlendirme yapar, tanı koyar, gerekirse ilaç başlatır ve takip eder.",
        (
            "Belirtiler birkaç haftadır sürüyor ve günlük hayatını belirgin şekilde etkiliyorsa",
            "Yaşamına son verme ya da kendine zarar verme düşüncelerin varsa",
            "Gerçeklikle bağın zayıflıyor gibiyse, sesler duyuyor ya da olağandışı şeylere inanıyorsan",
            "Günlerce az uyuyup aşırı enerjik ve kontrolsüz hissettiğin dönemler oluyorsa",
            "İlaçla ilgili bir sorun ya da soru varsa",
        ),
        "Devlet hastanelerinin psikiyatri polikliniklerine MHRS (182 / mhrs.gov.tr) üzerinden randevu alınabilir.",
        "Devlet hastanelerinde SGK kapsamında; özelde ücretli",
        ("mhrs", "tpd"),
    ),
    Specialist(
        "klinik-psikolog", "Klinik psikolog",
        "Psikoloji eğitimi üzerine klinik psikoloji yüksek lisansı yapmıştır. Değerlendirme yapar ve "
        "BDT gibi kanıta dayalı terapiler uygular. İlaç yazamaz.",
        (
            "Kaygı, çökkünlük, travma, ilişki örüntüleri gibi konularda düzenli terapi istiyorsan",
            "Kendi başına denediğin adımlar yetmiyorsa",
        ),
        "Devlet hastanelerinde de bulunabilir ama erişim sınırlı; özel muayenehane ve merkezler yaygın.",
        "Özelde ücretli; ücretler çok değişken",
        ("nimh-psychotherapies", "turk-psikologlar"),
    ),
    Specialist(
        "psikolojik-danisman", "Üniversite / okul psikolojik danışma merkezi",
        "Psikolojik danışmanlar (PDR) öğrencilere ders stresi, uyum, ilişki ve kariyer konularında destek verir; "
        "ağır durumlarda uygun yere yönlendirir.",
        ("Öğrenciysen ve hızlı, ücretsiz bir başlangıç istiyorsan",),
        "Üniversitenin sağlık, kültür ve spor daire başkanlığı ya da psikolojik danışma birimi.",
        "Öğrenciler için genellikle ücretsiz",
    ),
    Specialist(
        "bagimlilik", "Bağımlılık destekleri (YEDAM, AMATEM)",
        "YEDAM ücretsiz psikososyal destek verir; AMATEM'ler devlet hastanelerindeki alkol ve madde "
        "bağımlılığı tedavi merkezleridir.",
        ("Alkol, madde, kumar ya da ekran kullanımın kontrolünden çıktıysa", "Bir yakının için destek arıyorsan"),
        "YEDAM için 115; AMATEM için MHRS üzerinden randevu.",
        "YEDAM ücretsiz; AMATEM SGK kapsamında",
        ("yedam", "mhrs"),
    ),
    Specialist(
        "siddet", "Şiddet ve istismar durumunda",
        "ALO 183 ve Şiddet Önleme ve İzleme Merkezleri (ŞÖNİM) barınma, hukuki ve psikososyal destek sağlar.",
        ("Evde, ilişkide ya da başka bir yerde şiddet görüyorsan",),
        "Acil tehlikede 112; destek ve ihbar için 183; kadınlar için KADES uygulaması.",
        "Ücretsiz",
        ("aile-bakanligi",),
    ),
    Specialist(
        "trsm", "Toplum Ruh Sağlığı Merkezi (TRSM)",
        "Şizofreni ve bipolar bozukluk gibi uzun süreli ağır ruhsal hastalıkları olan kişilerin toplum içinde "
        "takibini yapar.",
        ("Tanısı konmuş ağır bir ruhsal hastalık için düzenli takip gerekiyorsa",),
        "Genellikle bir psikiyatristin yönlendirmesiyle.",
        "SGK kapsamında",
    ),
)

THERAPIST_TIPS: tuple[str, ...] = (
    "Unvanını ve eğitimini sor: psikiyatri uzmanlığı mı, klinik psikoloji yüksek lisansı mı?",
    "Hangi yöntemle çalıştığını ve bu yöntemin senin konunda araştırmayla desteklenip desteklenmediğini sor.",
    "İlk birkaç görüşmede kendini güvende ve anlaşılmış hissedip hissetmediğine dikkat et; terapötik ilişkinin "
    "kalitesi sonucu en tutarlı etkileyen şeylerden biri [kaynak:therapeutic-alliance].",
    "Kesin ve hızlı iyileşme vaat edenlere ya da doktorun olmadan ilacını bırakmanı söyleyenlere temkinli yaklaş.",
    "Uyum olmazsa terapisti değiştirmek normaldir; bu bir başarısızlık değildir.",
)


def catalog_for_prompt() -> str:
    """Modelin görebileceği kaynak listesi (kimlik + neyi desteklediği)."""
    lines = []
    for s in SOURCES:
        lines.append(f"- {s.id} | {s.publisher} | {EVIDENCE[s.evidence].label} | {s.supports}")
    return "\n".join(lines)


def sources_for_topics(topics: list[str]) -> list[Source]:
    if not topics:
        return list(SOURCES)
    wanted = set(topics)
    return [s for s in SOURCES if wanted.intersection(s.topics)]
