# FeedbackIQ — Müşteri Geri Bildirimi Veri Kalitesi & 3 Kademeli Triage Güvenlik Katmanı

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Google GenAI SDK](https://img.shields.io/badge/Google%20GenAI-Gemini%20Flash-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.7+-E92063?style=flat&logo=pydantic&logoColor=white)](https://pydantic.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**FeedbackIQ**, kurumsal organizasyonlarda gelen müşteri ve hasta geri bildirimlerinin **veri kalitesini iyileştirmek** ve **eksik operasyonel verileri akıllı yöntemlerle tamamlamak** amacıyla geliştirilmiş kurumsal bir kalite güvenlik duvarıdır (Data Quality Firewall).

---

## 1. Projenin Asıl Amacı & Çözülen Temel Problem

### Operasyonel Problem: Eksik ve Kalitesiz Geri Dönüşler
Modern kurumlarda müşteri ve hastalar QR kod, web formları, çağrı merkezleri veya e-posta aracılığıyla sürekli geri bildirim bırakırlar. Ancak bu geri bildirimlerin çok büyük bir kısmı operasyonel açıdan **yetersiz veya eksiktir**:

> *"Dün hastanenize geldim ve bekleme odasında neredeyse bir saat bekletildim. Kimse bana neden geciktiğini açıklamadı."*

Bu mesaj bir memnuniyetsizliği ifade etse de operasyonel olarak çözülemez:
- **Hangi şube / yerleşke** ziyaret edildi? (Belirsiz)
- **Hangi poliklinik / servis** sorumlu? (Kardiyoloji mi, Göz mü, Radyoloji mi?)
- Olay günün **hangi saatinde** gerçekleşti? (Vardiya ve sıra yönetimi logları incelenemez)
- **Hangi hekim, banko personeli veya vezne** ile görüşüldü? (Bilinmiyor)

Bu eksik kayıtlar doğrudan operasyonel birimlere veya CRM sistemlerine aktarıldığında personel günlerce şube tespiti yapmakla uğraşır, biletler birimler arasında sürüncemede kalır ve müşteri memnuniyetsizliği derinleşir.

### FeedbackIQ Çözümü: Kalite Güvenlik Duvarı & Eksik Veri Tamamlama
FeedbackIQ, geri bildirimi doğrudan birim yöneticisine aktarmak yerine araya **sessiz ve deterministik bir kalite katmanı** koyar:
1. **Sessiz Yapılandırılmış Çıkarım:** Google Gemini yapay zekası metindeki şube, poliklinik, tarih, saat, personel ve olay detaylarını şemaya uygun JSON olarak sessizce ayrıştırır.
2. **Deterministik Kalite Puanlaması (0–100):** Python kural motoru, vakanın araştırılabilirlik düzeyini deterministik olarak puanlar.
3. **Eksik Verilerin Akıllı Tamamlanması:** 
   - Küçük eksiklikler **Otonom Yapay Zeka Sesli Arama Botu** ile telefonla teyit edilir.
   - Kritik eksiklikler **Müşteri Hizmetleri Masası** tarafından hedeflenmiş sorularla zenginleştirilir.
4. **Sadece Tam Veri İş Akışına Girer:** Yalnızca operasyonel olarak incelenebilir düzeydeki (%80 ve üzeri kaliteli) kayıtlar birim yöneticilerine onaylanarak sevk edilir.

---

## 2. 3 Kademeli Triage (Yönlendirme) Mimarisi

FeedbackIQ, hastanın veya müşterinin karşısına can sıkıcı sohbet botları çıkarmaz. Bunun yerine arka planda 3 kademeli otonom yönlendirme uygular:

```
[Ham Müşteri Geri Bildirimi]
             │
             ▼
[Sessiz Gemini Bilgi Çıkarımı]
             │
             ▼
[Deterministik Python Kalite Motoru (0-100 Skor)]
             │
             ├───────────────────────────────────────┬───────────────────────────────────────┐
             ▼                                       ▼                                       ▼
       【Kademe 1】                             【Kademe 2】                             【Kademe 3】
      Yeterli Veri                             Biraz Eksik Veri                         Çok Eksik Veri
(Skor >= 80, kritik eksik yok)          (Skor 50-79, 1-2 küçük eksik)            (Skor < 50 veya şube yok)
             │                                       │                                       │
             ▼                                       ▼                                       ▼
  [Doğrudan Sevk / Onay]                  [AI Sesli Arama Botu]                   [Müşteri Hizmetleri]
Poliklinik yöneticisine aktarılır        Otonom telefon araması yapar,            İnsan temsilci masasına
                                         eksik saati/birimi teyit eder            eskalasyon yapılır
```

### Kademe Kriterleri

| Kademe | Adı | Kriter | Aksiyon |
| :--- | :--- | :--- | :--- |
| **Kademe 1** | **Onaylandı** | Skor &ge; 80, kritik alan eksiği yok | Vaka anında ilgili departman yöneticisinin kuyruğuna sevk edilir. |
| **Kademe 2** | **AI Sesli Arama** | Skor 50–79, şube biliniyor, 1–2 küçük operasyonel eksiklik var | Otonom sesli bot hastayı telefonla arar, eksik bilgiyi konuşarak tamamlar ve vakayı onaylar. |
| **Kademe 3** | **Müşteri Hizmetleri** | Skor &lt; 50 veya şube/yerleşke adı belirsiz | İnsan temsilci inceleme masasına eskalasyon yapılır; temsilci teyitli veriyi girerek vakayı onaylar. |

---

## 3. Neden Chatbot Değil?

| Geleneksel Sohbet Botları (Anti-Pattern) | FeedbackIQ Kalite Güvenlik Katmanı |
| :--- | :--- |
| Mağdur müşterinin karşısına bot koyarak tepki toplar. | Müşteri istediği kanaldan (Web, QR, E-posta) serbestçe yazar. |
| Halüsinasyon, yetkisiz sözler verme ve tıbbi risk taşır. | Yapay zeka sadece parametre çıkarıcıdır; karar vermez. |
| İş mantığını ve öncelikleri LLM'e bırakır. | Deterministik Python motoru kural ve ağırlıkları tam kontrol eder. |
| Konuşma geçmişi loglarında denetim zordur. | SQLite üzerinde yapılandırılmış, denetlenebilir ve şeffaf veri kaydı. |

---

## 4. Modern Web Kullanıcı Deneyimi & Tasarım Sistemi

FeedbackIQ, kurumsal standartlarda tasarlanmış modern bir web arayüzüne sahiptir:
* **Kurumsal Renk Paleti:** `rgb(65, 27, 206)` (`#411bce`) ve `rgb(48, 0, 156)` (`#30009c`) bazlı modern gradyanlar.
* **Sıfır Emoji İlkesi:** Çocuksu emojilerden tamamen arındırılmış; saf SVG vektör ikonları ve kurumsal tipografi (`Plus Jakarta Sans`, `Inter`).
* **Glassmorphism Tasarım:** Yarı saydam buzlu cam paneller, canlı durum göstergeleri, dinamik telefon ses dalgası animasyonları.
* **7 Entegre Çalışma Masası:**
  1. *Genel Bakış (Dashboard):* Canlı KPI metrikleri, kademe dağılım çubukları ve son vakalar tablosu.
  2. *Geri Bildirim Analizi (Intake Desk):* 3 hazır test senaryosu ve serbest analiz formu.
  3. *AI Sesli Arama Kuyruğu (Tier 2):* İnteraktif telefon görüşmesi simülatörü ve sesli konuşma dökümü.
  4. *Müşteri Hizmetleri Kuyruğu (Tier 3):* Kritik eksikliklerin temsilci masasına yönlendirilmesi.
  5. *Vaka Masası (Case Desk):* Temsilcinin teyitli verileri girerek kalite skorunu artırması.
  6. *Operasyonel Analitik (Analytics):* QR, Web ve Çağrı Merkezi kanallarının veri kalitesi kıyaslaması.
  7. *Mimari & Yönetişim (Architecture):* Güvenlik ve veri kalitesi ilkeleri.

---

## 5. Kurulum & Yerel Çalıştırma

### Gereksinimler
- Python 3.9 veya üzeri
- Ücretsiz Google AI Studio API Anahtarı (Google AI Studio Free Tier - Kredi kartı gerekmez)

### Adım 1: Depoyu Klonlayın ve Sanal Ortam Oluşturun
```bash
git clone https://github.com/efehakanyildiz/FeedbackIQ.git
cd FeedbackIQ

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Adım 2: Çevre Değişkenlerini Tanımlayın
`.env.example` dosyasını `.env` olarak kopyalayın ve Google AI Studio'dan aldığınız ücretsiz API anahtarınızı girin:
```bash
cp .env.example .env
```
`.env` içeriği:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.7-flash
DEMO_MODE=false
```

### Adım 3: Sunucuyu Başlatın
```bash
uvicorn feedbackiq.server:app --host 0.0.0.0 --port 8000 --reload
```
Tarayıcınızdan **[http://localhost:8000](http://localhost:8000)** adresini açarak uygulamayı kullanmaya başlayabilirsiniz.

---

## 6. Otomasyon Testleri

Tüm 3 kademeli triage mimarisi, bilgi çıkarımı ve veri tamamlama döngüleri kapsamlı birim ve entegrasyon testleriyle korunmaktadır:
```bash
PYTHONPATH=. pytest feedbackiq/tests/ -v
```
Tüm 10 test otomatik olarak çalışır ve onaylanır:
- `test_sufficient_data_reaches_tier_1_approved`
- `test_minor_gap_reaches_tier_2_ai_call`
- `test_major_gap_reaches_tier_3_csr_escalation`
- `test_appreciation_has_lighter_requirements`
- `test_adding_followup_information_increases_score_and_resolves`
- `test_manually_confirmed_values_take_precedence`
- `test_question_generator_asks_only_about_missing_fields`
- `test_no_duplicate_missing_fields`
- `test_core_end_to_end_scenario`
- `test_ai_voice_call_simulation`

---

## 7. Lisans
Bu proje **MIT Lisansı** altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakabilirsiniz.
