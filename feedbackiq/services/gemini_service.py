"""
Gemini Information Extraction Service.
Extracts structured operational data from patient feedback with strict schema validation.
Includes deterministic Demo Mode fallback for offline or zero-quota portfolio demonstration.
"""

import os
import json
import re
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

from feedbackiq.models.schemas import (
    ExtractedFeedbackData,
    FeedbackType,
    IssueType,
    SentimentType,
)

load_dotenv()

SYSTEM_INSTRUCTION = """Sen hastane ve sağlık kurumları için hasta/müşteri geri bildirimlerinden operasyonel verileri çıkaran uzman bir kurumsal veri analitiği motorusun.
Görevin hastaya cevap vermek ya da tıbbi tavsiye vermek KESİNLİKLE DEĞİLDİR.
Görevin metindeki açıkça belirtilen veya doğrudan anlaşılan operasyonel parametreleri çıkarıp şemaya uygun JSON olarak döndürmektir.

KESİN ÇIKARIM KURALLARI:
1. Asla uydurma veri üretme. Metinde açıkça yoksa veya ima edilmiyorsa null bırak.
2. issue_type alanını KESİNLİKLE şu listeden tam eşleşen değerle seç:
   - "Waiting Time": Randevuya rağmen bekleme, kuyrukta bekleme, geç çağrılma, ameliyat gerekçesiyle bekletilme, tahlil sonucunun geç çıkması, vezne/banko bekleme süresi şikayetleri.
   - "Staff Behavior": Doktor, hemşire, vezne veya hasta kabul personelinin kaba, saygısız, ilgisiz veya azarlayıcı tutumu/üslubu.
   - "Appointment": Randevu iptali, randevu saatinin haber verilmeden değiştirilmesi, randevu bulamama.
   - "Billing / Payment": Mükerrer çekim, karttan iki kez veya fazla para çekilmesi, fatura tutarsızlığı, vezne ödeme arızası, haksız tahsilat ve iade talepleri.
   - "Registration": Hasta kabul, banko kayıt sırası, giriş işlemleri aksaması.
   - "Medical Service Process": Teşhis, tedavi veya klinik uygulama sürecindeki tıbbi olmayan aksaklıklar.
   - "Communication": SMS/arama ile bilgilendirme yapılmaması, telefona yanıt verilmemesi.
   - "Facility / Cleanliness": Lavabo, poliklinik, sedye veya ortak alanların kirli olması, hijyen eksikliği.
   - "Technical Issue": POS cihazı hatası, web sitesi/uygulama arızası, kiosk arızası.
   - "Food / Catering": Yemek, kafeterya şikayetleri.
   - "Parking / Transportation": Otopark, vale, yönlendirme levhası eksikliği.
   - "Appreciation": Teşekkür, takdir, hekime/sağlık personeline övgü.
   - "General Suggestion": Gelişim ve iyileştirme önerisi.
   - "Other": Yukarıdakilere uymayan diğer konular.

3. hospital: Hastane, yerleşke veya sağlık kuruluşu adını tam çıkar (Örn: "Merkez Şehir Hastanesi", "Anadolu Sağlık", "Özel Hastane"). Metinde hastane geçmiyorsa null bırak.
4. department: Poliklinik, servis veya birim adını çıkar (Örn: "Ortopedi", "Kardiyoloji", "Göz Polikliniği", "Dahiliye", "Çocuk Sağlığı ve Hastalıkları", "Radyoloji", "Vezne ve Muhasebe", "Laboratuvar", "Acil Servis"). Yoksa null bırak.
5. incident_date: Olay tarihini veya zaman ifadesini koru (Örn: "Dün", "Bugün", "Geçen hafta", "3 Ekim", "2026-10-03"). Yoksa null bırak.
6. approximate_time: Saat veya günün vaktini çıkar (Örn: "10:30", "14:00", "sabah", "öğleden sonra"). Yoksa null bırak.
7. service_type: Alınan hizmet türü (Örn: "Muayene randevusu", "Kan tahlili", "Tetkik", "Görüntüleme", "Ameliyat").
8. feedback_type: "complaint" (şikayet), "appreciation" (teşekkür), "suggestion" (öneri).
9. sentiment: "negative", "positive", "neutral", "mixed".
"""


def _heuristic_mock_extraction(text: str, context: Optional[str] = None) -> ExtractedFeedbackData:
    """
    Kapsamlı Türkçe ve İngilizce kural tabanlı deterministik çıkarıcı.
    Yapay zeka API bağlantısında geçici bir kesinti yaşanırsa devreye girer.
    """
    lower = text.lower()
    full_text = f"{text} {context or ''}".lower()

    # 1. Geri Bildirim Türü & Duygu
    if any(w in lower for w in ["teşekkür", "eline sağlık", "harika", "mükemmel", "takdir", "övgü", "allah razı", "thank", "helpful", "great"]):
        feedback_type = FeedbackType.APPRECIATION
        sentiment = SentimentType.POSITIVE
    elif any(w in lower for w in ["öneri", "öneriyorum", "geliştirilmeli", "tavsiye", "olsa iyi olur", "suggest", "recommend"]):
        feedback_type = FeedbackType.SUGGESTION
        sentiment = SentimentType.NEUTRAL
    else:
        feedback_type = FeedbackType.COMPLAINT
        sentiment = SentimentType.NEGATIVE

    # 2. Şikayet / Konu Türü (Issue Type)
    if any(w in full_text for w in ["bekle", "gecik", "sıra", "dakika", "saat", "ameliyatta", "bekletildim", "geç çağrıldım", "wait", "delay", "late", "hour"]):
        issue_type = IssueType.WAITING_TIME
    elif any(w in full_text for w in ["fatura", "çekim", "mükerrer", "ücret", "hesabımdan", "kartımdan", "fazla para", "tahsil", "iade", "muhasebe", "charge", "refund", "billing"]):
        issue_type = IssueType.BILLING_PAYMENT
    elif any(w in full_text for w in ["randevu", "iptal", "appointment", "booking", "schedule"]):
        issue_type = IssueType.APPOINTMENT
    elif any(w in full_text for w in ["kaba", "saygısız", "tavır", "üslup", "davranış", "bağırdı", "ilgilenmedi", "rude", "behavior"]):
        issue_type = IssueType.STAFF_BEHAVIOR
    elif any(w in full_text for w in ["banko", "kayıt", "hasta kabul", "giriş işlemi", "registration"]):
        issue_type = IssueType.REGISTRATION
    elif any(w in full_text for w in ["temiz", "kirli", "lavabo", "tuvalet", "hijyen", "çöp", "clean", "dirty"]):
        issue_type = IssueType.FACILITY_CLEANLINESS
    elif any(w in full_text for w in ["pos", "cihaz", "terminal", "sistem", "kilitlendi", "hata verdi", "teknik"]):
        issue_type = IssueType.TECHNICAL_ISSUE
    elif any(w in full_text for w in ["otopark", "vale", "park", "tabela", "levha", "parking"]):
        issue_type = IssueType.PARKING_TRANSPORTATION
    elif any(w in full_text for w in ["yemek", "kafeterya", "kahvaltı", "food", "meal"]):
        issue_type = IssueType.FOOD_CATERING
    elif feedback_type == FeedbackType.APPRECIATION:
        issue_type = IssueType.APPRECIATION
    elif feedback_type == FeedbackType.SUGGESTION:
        issue_type = IssueType.GENERAL_SUGGESTION
    else:
        issue_type = IssueType.OTHER

    # 3. Hastane / Şube Tespiti
    hospital = None
    if "merkez" in full_text:
        hospital = "Merkez Şehir Hastanesi"
    elif "example hospital" in full_text:
        hospital = "Example Hospital"
    else:
        hosp_match = re.search(r"([A-ZÇĞİÖŞÜ][a-zçğıöşüA-ZÇĞİÖŞÜ0-9\s]+(?:Hastanesi|Hospital|Tıp Merkezi|Sağlık Merkezi))", text)
        if hosp_match:
            hospital = hosp_match.group(1).strip()

    # 4. Poliklinik / Birim Tespiti
    department = None
    dept_map = [
        ("ortopedi", "Ortopedi"),
        ("kardiyoloji", "Kardiyoloji"),
        ("göz", "Göz"),
        ("dahiliye", "Dahiliye"),
        ("iç hastalıkları", "Dahiliye"),
        ("çocuk", "Çocuk Sağlığı ve Hastalıkları"),
        ("pediatri", "Çocuk Sağlığı ve Hastalıkları"),
        ("radyoloji", "Radyoloji"),
        ("biyokimya", "Biyokimya Laboratuvarı"),
        ("laboratuvar", "Laboratuvar"),
        ("acil", "Acil Servis"),
        ("vezne", "Vezne ve Muhasebe"),
        ("muhasebe", "Vezne ve Muhasebe"),
        ("kayıt", "Hasta Kabul ve Kayıt"),
    ]
    for kw, d_name in dept_map:
        if kw in full_text:
            department = d_name
            break

    # 5. Olay Tarihi
    incident_date = None
    if "dün" in full_text or "yesterday" in full_text:
        incident_date = "Dün"
    elif "bugün" in full_text or "today" in full_text:
        incident_date = "Bugün"
    elif "geçen hafta" in full_text or "last week" in full_text:
        incident_date = "Geçen hafta"
    else:
        date_match = re.search(r"(\d{1,2}\s+(?:ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık|october)\b|\b\d{4}-\d{2}-\d{2}\b)", full_text, re.IGNORECASE)
        if date_match:
            incident_date = date_match.group(1).title()

    # 6. Yaklaşık Saat
    approximate_time = None
    time_match = re.search(r"(\b\d{1,2}:\d{2}\b|\b\d{1,2}\s*(?:am|pm)\b|sabah|öğleden sonra|akşam)", full_text)
    if time_match:
        approximate_time = time_match.group(1)

    # 7. Personel Unvanı
    staff_role = None
    for kw, role in [("doktor", "Doktor"), ("hekim", "Hekim"), ("hemşire", "Hemşire"), ("sekreter", "Tıbbi Sekreter"), ("banko", "Hasta Kayıt Görevlisi"), ("vezne", "Vezne Görevlisi")]:
        if kw in full_text:
            staff_role = role
            break

    # 8. Fatura / İşlem Bağlamı
    billing_context = None
    if issue_type == IssueType.BILLING_PAYMENT or "çekim" in full_text or "fatura" in full_text:
        billing_context = "Mükerrer veya tutarsız ücret tahsilatı bildirimi"
    elif issue_type == IssueType.TECHNICAL_ISSUE and "pos" in full_text:
        billing_context = "POS ödeme terminali donanım / zaman aşımı hatası"

    summary = text[:120] + "..." if len(text) > 120 else text

    return ExtractedFeedbackData(
        feedback_type=feedback_type,
        issue_type=issue_type,
        sentiment=sentiment,
        hospital=hospital,
        department=department,
        incident_date=incident_date,
        approximate_time=approximate_time,
        service_type="Muayene / Tetkik" if department else None,
        staff_role=staff_role,
        staff_name=None,
        billing_context=billing_context,
        description_of_event=text.strip(),
        impact="Operasyonel aksaklık veya hizmet gecikmesi",
        explicit_request=None,
        mentioned_entities=[e for e in [hospital, department, staff_role] if e],
        extracted_summary=summary,
        extraction_confidence=0.92
    )


def extract_feedback_info(
    feedback_text: str,
    context_hint: Optional[str] = None
) -> Tuple[ExtractedFeedbackData, bool, Optional[str]]:
    """
    Extract structured feedback data using Gemini API or fallback to Demo Mode.
    
    Returns:
        (ExtractedFeedbackData, is_live_gemini: bool, warning_or_error: Optional[str])
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    demo_mode_env = os.environ.get("DEMO_MODE", "true").lower() in ["true", "1", "yes"]
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip() or "gemini-2.0-flash"

    # If no valid API key or explicitly configured Demo Mode
    if not api_key or api_key in ["your_gemini_api_key_here", ""]:
        mock_data = _heuristic_mock_extraction(feedback_text, context_hint)
        return mock_data, False, "Demo Mode active (no Gemini API key detected). Running deterministic extraction."

    if demo_mode_env and os.environ.get("FORCE_GEMINI", "").lower() not in ["true", "1"]:
        # When demo mode is on but API key exists, still try live API if desired, or allow override
        pass

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        prompt = f"PATIENT FEEDBACK TEXT:\n\"\"\"{feedback_text}\"\"\"\n"
        if context_hint:
            prompt += f"\nCONFIRMED / ADDITIONAL OPERATIONAL CONTEXT:\n\"\"\"{context_hint}\"\"\"\n"

        prompt += "\nExtract structured JSON adhering strictly to the schema. Do not invent details."

        candidate_models = [model_name, "gemini-flash-latest", "gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.7-flash"]
        seen_models = set()
        models_to_try = [m for m in candidate_models if not (m in seen_models or seen_models.add(m))]

        last_err = None
        for m in models_to_try:
            try:
                response = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.1,
                        response_mime_type="application/json",
                        response_schema=ExtractedFeedbackData,
                    )
                )

                raw_json = response.text
                parsed = ExtractedFeedbackData.model_validate_json(raw_json)
                return parsed, True, None
            except Exception as candidate_err:
                last_err = candidate_err
                continue

        raise last_err or Exception("All candidate models failed.")

    except Exception as e:
        error_msg = f"Gemini API request failed ({type(e).__name__}: {str(e)[:120]}). Falling back to deterministic analysis."
        fallback_data = _heuristic_mock_extraction(feedback_text, context_hint)
        fallback_data.extraction_confidence = 0.75
        return fallback_data, False, error_msg
