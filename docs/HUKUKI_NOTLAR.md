# Hukuki notlar

> **Bu bir hukuki görüş değildir.** Geliştirme sırasında yapılan araştırmanın özeti ve uygulamaya nasıl
> yansıtıldığıdır. Bazı kaynaklara doğrudan erişilemedi; bulgular arama sonuçlarına ve ikincil kaynaklara dayanıyor.
> “⚠️ Emin değilim” işaretli maddeleri bir KVKK avukatına sor. Son kontrol: Kasım 2026.

## 1. KVKK (6698 sayılı Kanun)

| Konu | Durum | Uygulamada ne yapıldı |
|---|---|---|
| **Sağlık verisi özel nitelikli kişisel veridir** (m.6) | Kesin | Ruh hâli, belirtiler, güvenlik sorusu ve sohbetler sağlık verisi kabul edildi. |
| **İşleme şartı** | 7499 sayılı Kanunla (2024) m.6 değişti; açık rıza artık tek yol değil. ⚠️ Emin değilim: diğer şartlar (ör. sır saklama yükümlüsü sağlık personeli) bu uygulamaya uymadığı için en uygun dayanak açık rıza görünüyor. | Açık rıza; ayrı kutular, önceden işaretsiz, sürümlü kayıt (hangi metin, ne zaman), geri alınabilir. |
| **Aydınlatma yükümlülüğü** (m.10) | Kesin | Rıza ekranında özet + tam metin. Veri sorumlusu adı ve iletişim bilgisi `.env`'den doldurulmalı. |
| **Yurt dışına aktarım** (m.9, 2024'te değişti) | ⚠️ **En büyük açık soru.** Yeni rejimde ana yollar: yeterlilik kararı, uygun güvenceler (ör. Kurul'un standart sözleşmeleri, imzadan sonra 5 iş günü içinde Kurul'a bildirim) veya arızi (düzenli olmayan) aktarım istisnaları. Açık rıza artık esas olarak arızi aktarımlar için geçerli görünüyor. Her mesajın Google'a gitmesi “arızi” sayılmayabilir. | Rıza metninde yurt dışına aktarım açıkça yazıldı. **Gerçek yayında** hangi aktarım yolunun kullanılacağı (Google ile standart sözleşme mümkün mü?) avukatla netleştirilmeli. |
| **Veri güvenliği** (m.12) | Kesin | scrypt ile şifre özeti, kullanıcılar arası izolasyon (her sorguda kullanıcı kontrolü), CORS/XSRF koruması açık, kullanım istatistiği kapalı, fontlar yerelde. **Eksik:** diskte şifreleme, yedekleme ve log politikası, erişim kaydı. |
| **İlgili kişinin hakları** (m.11) | Kesin | Verileri indirme (JSON), sohbet/hafıza/hesap silme, rıza geri alma. |
| **VERBİS kaydı** | ⚠️ Emin değilim: Kurul kararlarıyla belirli eşiklerin altındaki veri sorumluları muaf; ancak ana faaliyeti özel nitelikli veri işlemek olanların muafiyet dışında kalabileceği belirtiliyor. | Gerçek yayından önce kontrol edilmeli. |
| **Veri minimizasyonu** (m.4) | Kesin | Tam yaş yerine yaş aralığı; cinsiyet, şehir, e-posta, gerçek ad sorulmuyor. Hafıza notlarında kimlik bilgisi yazılmaması modele talimat olarak verildi. |

## 2. Gemini API şartları

Kaynak: Gemini API Additional Terms of Service (arama sonuçlarına göre Mart 2026 sürümü; sayfaya doğrudan erişilemedi).

- **Yaş:** API'yi kullananlar 18 yaşından büyük olmalı ve API, 18 yaş altına yönelik ya da 18 yaş altının erişmesi
  muhtemel uygulamalarda kullanılmamalı. → Kayıtta yaş aralığı soruluyor, 18 altı hesap açamıyor, gençlik kaynaklarına
  yönlendiriliyor. Sohbette 18 altı olduğunu söyleyen kullanıcı için ayrıca kural var.
- **Ücretsiz kota:** Ücretsiz kotada gönderilen içerik Google ürünlerini geliştirmek için kullanılabiliyor ve insan
  değerlendiriciler okuyabiliyor; şartlar hassas veya kişisel bilgi gönderilmemesini öneriyor. → **Sağlık verisi işleyen
  bir uygulama için ücretsiz kota uygun değil.** Gerçek kullanıcıya açmadan önce ücretli kotaya geç ve
  `GEMINI_PAID_TIER=true` yap. O zamana kadar rıza ekranında açık bir uyarı gösteriliyor.
- **Tıbbi kullanım:** Şartlar, hizmetin klinik uygulamada, tıbbi tavsiye vermek için ya da tıbbi cihaz onayı gerektiren
  bir şekilde kullanılmasını yasaklıyor. → Psikorehber tanı koymuyor, ilaç/tedavi önermiyor, skor hesaplamıyor; bu
  kurallar sistem talimatının değişmez çekirdeğinde. ⚠️ Yine de “psikolojik yönlendirme” ile “tıbbi tavsiye” arasındaki
  sınır gri; bir avukat yorumu almak doğru olur.

## 3. Tıbbi cihaz sınırı

⚠️ Emin değilim. Teşhis, tedavi, izleme ya da tahmin amacı taşıyan yazılımlar Tıbbi Cihaz Yönetmeliği (AB MDR uyumlu)
kapsamına girebiliyor. Psikorehber bu yüzden bilinçli olarak:
- tanı koymuyor ya da “depresyon skoru” gibi bir puan hesaplamıyor,
- PHQ-9/GAD-7 gibi tarama ölçeklerini içermiyor,
- tedavi önermek yerine genel bilgi ve doğru uzmana yönlendirme yapıyor.

Bu özelliklerden biri eklenirse bu değerlendirme yeniden yapılmalı.

## 4. “Açık sözlü” mod ve rızanın sınırları

Rıza, kullanıcının kendi adına aldığı riski kabul ettiğini gösterir ve beklentiyi netleştirir. Ama:
- İntihar ve kendine zarar gibi ciddi risklerde geliştiricinin özen yükümlülüğünü ortadan kaldırmaz. Genel bilgi olarak:
  Türk Borçlar Kanunu m.115'e göre ağır kusurdan sorumsuzluk anlaşması kesin olarak hükümsüzdür. Yani sorumluluk reddi
  metni kötü tasarımı korumaz.
- Yasa dışı içeriği meşrulaştırmaz.
- 18 yaş altı için geçersizdir.

Bu yüzden: 18+ beyanı + ayrı, sürümlü, geri alınabilir rıza; güvenlik çekirdeği her modda aynı; Gemini'nin kendi
filtreleri de devrede (yalnızca yüksek şiddette engelleyecek şekilde ayarlandı, çünkü varsayılan filtreler kriz
mesajlarına verilen cevabı bile engelleyebiliyor; engellenirse sabit ve güvenli bir yedek metin gösteriliyor).

## 5. Unvan ve şeffaflık

Uygulama kendini psikolog, terapist ya da doktor olarak tanıtmıyor; “insan mısın?” sorusuna dürüst cevap vermesi
talimatta zorunlu.

## 6. Gerçek kullanıcılara açmadan önce kontrol listesi

- [ ] Git geçmişinde sızan eski API anahtarını Google AI Studio'dan **iptal et** (repo herkese açık)
- [ ] KVKK avukatı incelemesi: aydınlatma ve rıza metinleri, yurt dışı aktarım yolu, VERBİS
- [ ] Ücretli Gemini kotası, `GEMINI_PAID_TIER=true`, Google'ın veri işleme şartlarının incelenmesi
- [ ] `VERI_SORUMLUSU` ve `VERI_SORUMLUSU_ILETISIM` doldurulması; KVKK m.13 başvuruları için bir kanal
- [ ] Diskte şifreleme, yedekleme ve log politikası, HTTPS arkasında yayın
- [ ] Bir klinik psikolog veya psikiyatristin sistem talimatını, yönlendirme mantığını ve kaynak listesini incelemesi
- [ ] Kriz akışının gerçek senaryolarla test edilmesi (red-team): dolaylı ifadeler, enjeksiyon, ilaç soruları, 18 altı
- [ ] Yardım hattı numaralarının resmi kaynaklardan yeniden doğrulanması (`psikorehber/resources.py`, `VERIFIED_ON`)

## Kaynaklar

- Gemini API Additional Terms of Service — https://ai.google.dev/gemini-api/terms
- KVKK, Standart Sözleşmeler ve Bağlayıcı Şirket Kuralları duyurusu — https://www.kvkk.gov.tr/Icerik/7938/Standart-Sozlesmeler-ve-Baglayici-Sirket-Kurallarina-Iliskin-Dokumanlar-Hakkinda-Kamuoyu-Duyurusu
- KVK Kanunu'nda özel nitelikli veriler ve yurt dışına aktarım değişiklikleri — https://www.hukukihaber.net/kvk-kanununda-ozel-nitelikli-kisisel-verilerin-islenmesi-ve-yurt-disina-veri-aktarimi-kapsaminda-yapilan-degisikliklere-iliskin-degerlendirmeler/amp
- 112 tek acil numara (2021) — https://www.milliyet.com.tr/gundem/icisleri-bakanligi-duyurdu-tum-turkiyede-tek-acil-numaraya-gecildi-6616677
- ALO 183 — https://www.aile.gov.tr/alo-183/alo183pages/hakkinda/
- 182'nin MHRS randevu hattı olduğu — https://www.sozcu.com.tr/mhrs-portal-mhrs-randevu-alma-randevu-iptal-etme-alo-182-2-wp787399
- 115 YEDAM — https://kureansiklopedi.com/tr/detay/115-yedam-danisma-hatti-b185a
- 114 UZEM — https://www.turkgun.com/gundem/ulusal-zehir-danisma-merkezine-gunluk-1000-cagri/294443
