# Psycalm

Ne yaşadığını anlamana, **güvenilir bilgiye** ve **doğru uzmana** ulaşmana yardım eden, Türkçe bir yapay zekâ
yönlendirme asistanı. Psikolojik tedavi vermez; söylediklerinin **neye dayandığını** her zaman gösterir.

> ⚠️ Psycalm bir terapist, doktor ya da acil servis değildir. Gerçek kullanıcılara açmadan önce
> [docs/HUKUKI_NOTLAR.md](docs/HUKUKI_NOTLAR.md) içindeki kontrol listesini tamamla.

## Neler var?

| Özellik | Açıklama |
|---|---|
| **Kayıt → İzinler → Tanışma → Tanıtım** | Sağlık verisi toplamadan önce KVKK aydınlatması ve ayrı ayrı açık rıza alınır. Tanışma soruları az, amaçlı ve her biri “neden soruyoruz?” açıklamalı. |
| **Kaynak gösteren cevaplar** | Model yalnızca elle doğrulanmış bir katalogdaki kaynakları `[kaynak:kimlik]` olarak anabilir; linkleri uygulama ekler. Uydurma kaynak ekrana çıkamaz. Her öneride 🟢/🟡/⚪ dayanak düzeyi. |
| **Doğru yönlendirme** | Süre × şiddet × kırmızı bayrak mantığı; aile hekimi, psikiyatrist, klinik psikolog, üniversite danışma merkezi, YEDAM/AMATEM, 183 gibi somut yerler. |
| **Kriz güvenlik ağı** | Model cevap vermeden önce deterministik Türkçe risk taraması; modelden bağımsız, doğrulanmış kriz kartı (112, 183, 114, KADES). |
| **Modlar** | 🌿 Dengeli · 👂 Sadece dinle · 🔓 Açık sözlü (18+ ve ayrı rıza). Güvenlik çekirdeği hiçbir modda gevşemez. |
| **Hafıza** | İsteğe bağlı; sohbetten kısa notlar çıkarılır, kullanıcı hepsini görür, düzenler, siler. |
| **Nefes** | 3 teknik, kanıt düzeyi dürüstçe belirtilmiş; kaymayan zamanlayıcı, hareket azaltma desteği, mobil uyumlu. |
| **Yardım ve Kaynaklar** | Giriş yapmadan da açılır: acil hatlar, “kime başvurmalıyım?”, terapist seçme ipuçları, okuma listesi. |
| **Veri hakları** | Verilerini JSON olarak indir, sohbetleri tek tek ya da hesabı tamamen sil (KVKK m.11). |

## Kurulum

```bash
python -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
cp .env.example .env
```

`.env` içine `GEMINI_API_KEY` yaz (Google AI Studio). Anahtar yoksa uygulama **demo modunda** sabit cevaplarla açılır;
arayüzü denemek için yeterli.

```bash
streamlit run app.py
```

Testler (API anahtarı gerekmez):

```bash
pip install -r requirements-dev.txt && pytest -q
```

## Mimari

```
app.py                 Giriş noktası; duruma göre sayfa kapıları (giriş → izin → tanışma → tanıtım → uygulama)
psycalm/
  safety.py            Deterministik Türkçe risk taraması (İ/ı doğru küçültme + ASCII katlama)
  resources.py         Doğrulanmış kaynak kataloğu, yardım hatları, “kime başvurmalı” rehberi
  citations.py         [kaynak:id] → ¹ ² + kaynak listesi; bilinmeyen kimlikleri atar, akışta yarım işareti gizler
  prompts.py           Sistem talimatı: değişmez güvenlik çekirdeği + yaklaşım + dayanak kuralları + mod + profil
  modes.py             Modlar ve rıza/yaş kontrolüyle güvenli varsayılana düşme
  consent.py           Sürümlü rıza metinleri ve KVKK aydınlatma metni
  profile.py           Tanışma soruları, doğrulama
  llm.py               Gemini istemcisi (akış, güvenlik filtresi yedeği, Türkçe hata mesajları) + demo istemcisi
  storage.py           SQLite; scrypt şifre, kullanıcı izolasyonu, cascade silme, dışa aktarma
views/                 Streamlit sayfaları
assets/breathing.html  Nefes bileşeni (requestAnimationFrame, prefers-reduced-motion)
static/fonts/          Kendi sunucumuzdan sunulan fontlar (Google Fonts'a istek yok)
tests/                 Birim + AppTest uçtan uca testler (API gerektirmez)
```

**Neden bu tasarım?** Güvenlik açısından kritik kısımlar (kriz tespiti, yardım hatları, kaynak linkleri) modele
bırakılmadı; deterministik ve test edilebilir. Model yalnızca dil ve muhakeme işini yapıyor. Bunun bedeli: kaynak
kataloğu ve risk kalıplarının elle bakımı gerekiyor.

## Bilinen sınırlar

- **Gerçek Gemini API'siyle uçtan uca test edilmedi** (geliştirme ortamında anahtar yoktu); akış, engelleme ve hata
  mantığı sahte istemciyle test edildi. İlk iş gerçek anahtarla denemek olmalı.
- Sayfa yenilenince oturum kapanır (Streamlit oturumu sekmeye bağlı; kalıcı giriş için çerez/OIDC gerekir).
- Veritabanı diskte şifrelenmeden durur.
- Risk taraması anahtar kelime tabanlıdır: dolaylı anlatımları kaçırabilir, bazen yanlış alarm verir.
- Model adı varsayılan olarak `gemini-flash-latest` takma adı; davranışı Google model güncelledikçe değişebilir.

Eski sürümün eleştirisi ve yapılacaklar listesi: [docs/INCELEME.md](docs/INCELEME.md)
