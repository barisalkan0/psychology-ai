# v1 incelemesi ve yapılacaklar

## v1'de bulunan sorunlar

### Kritik (güvenlik / doğruluk)

| Sorun | Neden önemli | v2'de |
|---|---|---|
| Kriz anında **“182 ALO Psikiyatri Hattı”** veriliyordu | 182, MHRS **randevu** hattı; kriz hattı değil. İntihar düşüncesi olan birini randevu hattına yönlendirmek tehlikeli. | Kriz için 112 (+183, 114, KADES); 182 yalnızca “randevu hattı, kriz hattı değildir” notuyla. Testle korunuyor. |
| **“1–2 hafta: kesinlikle uzmana yönlendirme yapma, bu kural ihlal edilemez”** | Gerçeklikten kopma, mani, yeme bozukluğu, ağır işlev kaybı gibi durumlarda süre beklenmez. | Süre × şiddet × kırmızı bayrak mantığı; kırmızı bayrakta süreye bakılmaz. |
| Model link ve kaynak vermeye zorlanıyordu (“gerçek kaynak ver ama uydurma”) | Erişimi olmayan bir modelden link istemek uydurmaya davetiye. | Kapalı, elle doğrulanmış katalog; model yalnızca kimlik yazar, linki uygulama ekler, bilinmeyen kimlik atılır. |
| “İstatistiği umut verici sun: X oranı Y, Z sürede iyileşme” | Modeli sayı uydurmaya itiyordu. | Katalog dışı sayısal istatistik yasak; kanıt gücü dürüstçe etiketleniyor. |
| Kriz tespiti tamamen modele bağlıydı | Model kaçırabilir ya da güvenlik filtresi cevabı tamamen engelleyebilir. | Deterministik Türkçe tarama + modelden bağımsız kriz kartı + engellenme durumunda güvenli yedek metin. |
| **API anahtarı git geçmişinde** (`main.py`, v1.0 commit'i; ayrıca yanlışlıkla `os.getenv`'e değişken adı olarak verilmiş) | Repo herkese açık; anahtar herkes tarafından görülebilir. | Kod `.env`'den okuyor. **Anahtarı mutlaka iptal et**; geçmişi temizlemek yetmez çünkü kopyalanmış olabilir. |
| `sistem_prompt.txt` repodan silinmiş ama `app.py` onu okuyordu | Temiz bir kopyada uygulama açılışta çöküyordu. | Talimat kodda (`psycalm/prompts.py`), sürüm kontrolünde ve test ediliyor. Gizli tutmak istiyorsan repoyu private yap. |
| Rıza, aydınlatma, yaş kontrolü yoktu | Sağlık verisi + yurt dışına aktarım + 18 yaş altı kullanım (Gemini şartları) sorunları. | Bkz. [HUKUKI_NOTLAR.md](HUKUKI_NOTLAR.md). |
| Yapay zekâ olduğunu söyleme, istem enjeksiyonu, kapsam dışı istek, 18 altı için kural yoktu | — | Değişmez güvenlik çekirdeğine eklendi. |

### Mantık ve arayüz

| Sorun | v2'de |
|---|---|
| API hatası, kota aşımı ya da filtre engelinde kırmızı hata ekranı (`response.text` None) | Türkçe hata mesajı, mesaj kaybolmaz, “Tekrar dene”; geçici hatalarda bir kez otomatik yeniden deneme |
| Akış yoktu, cevap gelene kadar ekran donuk | Akışla yazım; yarım kaynak işaretleri gizleniyor |
| Her mesajda tüm geçmiş sınırsız gönderiliyordu | Son 30 mesaj |
| “Önce 8 şeyi öğren, her seferinde tek soru sor” → uzun bir sorgulama | Temel bilgiler kayıtta; model yalnızca eksik ve gerekli olanı soruyor |
| Python'un `lower()`'ı Türkçe “İ”yi bozuyor (anahtar kelime eşleşmesini sessizce kaçırır) | Türkçeye uygun küçültme + ASCII katlama, testli |
| devcontainer CORS ve XSRF korumasını kapatıyordu | Kaldırıldı |
| `requirements.txt` `.gitignore`'daydı | Düzeltildi; veritabanı ve `.env` yok sayılıyor |

### Bu sürümü geliştirirken bulunan ve düzeltilen hatalar

Bunlar tarayıcıda uçtan uca test sırasında bulundu, her biri için regresyon testi var:
- Kaynak listesinin `---` ayracı, üstündeki satırı markdown'da **dev bir başlığa** çeviriyordu (setext başlık kuralı).
- `*Dayanak…*¹` yazımında kapanış yıldızı geçersiz kalıyor, yıldızlar çıplak görünüyordu.
- Yan yana iki kaynak `¹²` (“on iki”) gibi okunuyordu → `¹,²`.
- Açık sözlü mod onay penceresi açılınca mod menüsü pencerenin üstünde açık kalıyordu.
- Aynı sohbette önce intihar sonra şiddet ifadesi geçince ikinci kart kısaltılıyor, 183/KADES bilgisi kayboluyordu.
- Koyu temada birincil butonlarda yazı kontrastı ~1.9:1'di.
- Telefonda nefes egzersizinin butonları kesiliyordu.

## Bilerek yapılmayanlar (ve nedenleri)

- **Cinsiyet sorusu kaldırıldı.** Yönlendirmeyi değiştirmiyor; KVKK'nın ölçülülük ilkesi gereği gereksiz veri toplamamak
  daha doğru. Gerekirse (ör. doğum sonrası dönem, kadına yönelik şiddet) sohbette zaten ortaya çıkıyor. İstersen geri
  eklemek tek satır.
- **PHQ-9 / GAD-7 tarama ölçekleri yok.** Puan hesaplamak uygulamayı tıbbi cihaz ve Gemini şartlarındaki “klinik kullanım”
  sınırına yaklaştırır.
- **FastAPI + React'e geçilmedi.** Streamlit bu aşama için yeterli; asıl risk teknoloji değil, içerik ve güvenlik.

## Yapılacaklar (öncelik sırasıyla)

### Önce bunlar (gerçek kullanıcıdan önce)
1. **Sızan API anahtarını iptal et.**
2. Gerçek anahtarla uçtan uca dene; sistem talimatının Türkçe cevap kalitesini gözle değerlendir.
3. **Değerlendirme (eval) seti:** 50–100 senaryo (kriz, dolaylı ifade, ilaç sorusu, istem enjeksiyonu, 18 altı, açık mod
   sınırları, kapsam dışı). Kural tabanlı kontroller (182'yi kriz hattı demiyor mu, katalog dışı kaynak var mı) + LLM ile
   puanlama. *AI/ML açısından portföyde en değerli parça bu olur.*
4. [HUKUKI_NOTLAR.md](HUKUKI_NOTLAR.md) kontrol listesi, klinik danışman incelemesi.

### Sonra
5. Kalıcı oturum (çerez veya `st.login` ile OIDC).
6. Cevaplara 👍/👎 geri bildirimi → eval setini besler.
7. Diskte şifreleme (kullanıcı şifresinden türetilen anahtarla alan bazında). Ödünleşim: şifre unutulursa veri kurtarılamaz.
8. “Hızlı çıkış” butonu (şiddet gören kullanıcılar için ekranı anında nötr bir siteye çevirir).
9. Risk taramasını küçük bir Türkçe sınıflandırıcıyla güçlendirmek (anahtar kelime + ince ayarlı BERTurk); önce
   yanlış negatif analizi.
10. Kaynak kataloğunu RAG'a çevirmek: kaynakların özetlerinden alıntı yaparak daha somut dayanak.

### Belki
11. Ruh hâli günlüğü / takip — kullanıcı “takip” istemişti; ama tıbbi cihaz sınırına yaklaşır, hukuki değerlendirme şart.
12. Çok dilli destek.
