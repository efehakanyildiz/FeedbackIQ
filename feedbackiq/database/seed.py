"""
Synthetic seed data generator for FeedbackIQ.
Seeds 11 realistic demo cases demonstrating all 3 triage tiers:
- Tier 1: Approved / Ready for Workflow (Sufficient data)
- Tier 2: AI Voice Bot Follow-up (Minor missing data)
- Tier 3: Customer Service Escalation (Major missing data)
"""

from feedbackiq.database.db import init_db
from feedbackiq.database.repository import (
    save_case,
    count_cases,
    add_follow_up_entry,
    update_case_after_reevaluation,
)
from feedbackiq.models.schemas import (
    ExtractedFeedbackData,
    FeedbackType,
    IssueType,
    SentimentType,
    ContactStatus,
    SourceChannel,
)
from feedbackiq.services.completeness_service import evaluate_completeness


SEED_CASES = [
    {
        # Kademe 2: Küçük eksiklik (Saat ve bölüm eksik, hastane biliniyor)
        "case_id": "FB-2026-1001",
        "created_at": "2026-10-01 09:15:00",
        "source_channel": SourceChannel.QR_CODE.value,
        "original_feedback": "Dün Merkez Şehir Hastanesi'ne geldim ve bekleme salonunda neredeyse bir saat bekletildim. Kimse bana gecikmenin nedenini açıklamadı.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.WAITING_TIME,
            sentiment=SentimentType.NEGATIVE,
            hospital="Merkez Şehir Hastanesi",
            department=None,
            incident_date="Dün",
            approximate_time=None,
            service_type=None,
            description_of_event="Bekleme salonunda gecikme hakkında bilgilendirme yapılmadan yaklaşık bir saat beklenmesi.",
            extracted_summary="Merkez Şehir Hastanesi'nde yaklaşık bir saatlik bekleme süresi gecikmesi.",
            extraction_confidence=0.88
        ),
        "contact_status": ContactStatus.AI_CALL_PENDING.value
    },
    {
        # Kademe 1: Yeterli veri -> Onaylandı / Doğrudan İş Akışına Sevk
        "case_id": "FB-2026-1002",
        "created_at": "2026-10-01 11:30:00",
        "source_channel": SourceChannel.WEBSITE.value,
        "original_feedback": "3 Ekim saat 14:00'te Merkez Şehir Hastanesi Kardiyoloji polikliniğindeki randevuma gittim. Randevum olmasına rağmen banko kaydı 45 dakika sürdü ve muayeneye gecikmeli alındım.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.WAITING_TIME,
            sentiment=SentimentType.NEGATIVE,
            hospital="Merkez Şehir Hastanesi",
            department="Kardiyoloji Polikliniği",
            incident_date="3 Ekim",
            approximate_time="14:00",
            service_type="Uzman Muayenesi",
            description_of_event="Randevu saatine rağmen banko kayıt süresinin 45 dakika uzaması.",
            extracted_summary="Kardiyoloji polikliniğinde 45 dakikalık randevu gecikmesi.",
            extraction_confidence=0.96
        ),
        "contact_status": ContactStatus.COMPLETED.value
    },
    {
        # Kademe 1: Teşekkür -> Onaylandı
        "case_id": "FB-2026-1003",
        "created_at": "2026-10-02 14:10:00",
        "source_channel": SourceChannel.CALL_CENTER.value,
        "original_feedback": "Merkez Şehir Hastanesi çocuk polikliniğindeki hemşire hanım çocuğumuza son derece şefkatli ve güler yüzlü yaklaştı, kendisine teşekkür ederiz.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.APPRECIATION,
            issue_type=IssueType.APPRECIATION,
            sentiment=SentimentType.POSITIVE,
            hospital="Merkez Şehir Hastanesi",
            department="Çocuk Sağlığı ve Hastalıkları",
            incident_date=None,
            staff_role="Hemşire",
            description_of_event="Pediatri hemşiresinin örnek nezaketi ve hasta odaklı yaklaşımı.",
            extracted_summary="Çocuk polikliniği hemşire personeline teşekkür ve takdir.",
            extraction_confidence=0.94
        ),
        "contact_status": ContactStatus.COMPLETED.value
    },
    {
        # Kademe 3: Kritik eksik veri (Hastane adı yok, tutar ve detay belirsiz)
        "case_id": "FB-2026-1004",
        "created_at": "2026-10-02 16:45:00",
        "source_channel": SourceChannel.WEBSITE.value,
        "original_feedback": "Dün muayene sonrası kredi kartımdan iki kez mükerrer çekim yapılmış. Muhasebeye yazdım kimse cevap vermedi, acil tarafıma dönülmesini istiyorum.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.BILLING_PAYMENT,
            sentiment=SentimentType.NEGATIVE,
            hospital=None,
            department=None,
            incident_date="Dün",
            billing_context="Kredi kartı ekstre kaydında tek işlem için iki kez çekim görünmesi.",
            description_of_event="Hastanın ekstresinde mükerrer işlem tespit edilmesi.",
            extracted_summary="Hangi hastane şubesi olduğu belirtilmemiş mükerrer çekim şikayeti.",
            extraction_confidence=0.88
        ),
        "contact_status": ContactStatus.CSR_CONTACT_ATTEMPTED.value
    },
    {
        # Kademe 1: Tesis Temizlik -> Onaylandı
        "case_id": "FB-2026-1005",
        "created_at": "2026-10-03 08:20:00",
        "source_channel": SourceChannel.QR_CODE.value,
        "original_feedback": "2 Ekim tarihinde Merkez Şehir Hastanesi Radyoloji katındaki lavabolar temiz değildi ve sabunluklar boştu.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.FACILITY_CLEANLINESS,
            sentiment=SentimentType.NEGATIVE,
            hospital="Merkez Şehir Hastanesi",
            department="Radyoloji",
            incident_date="2 Ekim",
            description_of_event="Radyoloji katı lavabo alanının hijyen yetersizliği ve sarf malzeme eksikliği.",
            extracted_summary="Radyoloji katı lavaboları için kat hizmetleri temizlik ihtiyacı.",
            extraction_confidence=0.92
        ),
        "contact_status": ContactStatus.COMPLETED.value
    },
    {
        # Kademe 3: Kritik eksik veri (Hastane yok, poliklinik yok, tarih yok)
        "case_id": "FB-2026-1006",
        "created_at": "2026-10-03 10:05:00",
        "source_channel": SourceChannel.EMAIL.value,
        "original_feedback": "Randevum bana hiçbir SMS veya arama ile bilgi verilmeden iptal edilmiş, hastaneye gelince kapıda kaldım.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.APPOINTMENT,
            sentiment=SentimentType.NEGATIVE,
            hospital=None,
            department=None,
            incident_date=None,
            description_of_event="Randevunun hastaya önceden bildirim yapılmaksızın iptal edilmesi.",
            extracted_summary="Haber verilmeksizin yapılan randevu iptali şikayeti.",
            extraction_confidence=0.84
        ),
        "contact_status": ContactStatus.NOT_CONTACTED.value
    },
    {
        # Kademe 2: Küçük eksiklik (Hastane ve unvan biliniyor, hangi banko olduğu eksik)
        "case_id": "FB-2026-1007",
        "created_at": "2026-10-03 13:50:00",
        "source_channel": SourceChannel.SOCIAL_MEDIA.value,
        "original_feedback": "Dün sabah Merkez Şehir Hastanesi hasta kayıt bankosundaki görevli arkadaş kaba ve ilgisiz bir üslupla konuştu.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.STAFF_BEHAVIOR,
            sentiment=SentimentType.NEGATIVE,
            hospital="Merkez Şehir Hastanesi",
            department=None,
            incident_date="Dün",
            approximate_time="Sabah",
            staff_role="Hasta Kayıt Görevlisi",
            description_of_event="Hasta kayıt bankosunda nezaketsiz iletişim yaşanması.",
            extracted_summary="Hasta kabul bankosu personeli hakkında üslup bildirimi.",
            extraction_confidence=0.90
        ),
        "contact_status": ContactStatus.AI_CALL_PENDING.value
    },
    {
        # Kademe 2: Küçük eksiklik (Öneri var, kat / otopark alanı teyidi gerekiyor)
        "case_id": "FB-2026-1008",
        "created_at": "2026-10-04 09:10:00",
        "source_channel": SourceChannel.WEBSITE.value,
        "original_feedback": "Merkez Şehir Hastanesi yerleşkesinde kapalı otoparkın yönlendirme levhaları ve çıkış okları çok yetersiz, tabelaların belirginleştirilmesini öneriyorum.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.SUGGESTION,
            issue_type=IssueType.PARKING_TRANSPORTATION,
            sentiment=SentimentType.NEUTRAL,
            hospital="Merkez Şehir Hastanesi",
            description_of_event="Kapalı otopark katlarındaki yönlendirme ve çıkış tabelalarının güçlendirilmesi önerisi.",
            extracted_summary="Otopark yönlendirme levhalarının artırılması hakkında gelişim önerisi.",
            extraction_confidence=0.91
        ),
        "contact_status": ContactStatus.AI_CALL_PENDING.value
    },
    {
        # Kademe 3: Kritik eksik veri (Hastane yok, hangi vezne olduğu meçhul)
        "case_id": "FB-2026-1009",
        "created_at": "2026-10-04 14:40:00",
        "source_channel": SourceChannel.QR_CODE.value,
        "original_feedback": "Veznede ödeme yapmaya çalışırken POS cihazı sürekli hata verdi ve işlemi tamamlayamadık, sistem kilitlendi.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.TECHNICAL_ISSUE,
            sentiment=SentimentType.NEGATIVE,
            hospital=None,
            department="Vezne Masası",
            incident_date="Bugün",
            billing_context="POS tahsilat terminali zaman aşımı hatası.",
            description_of_event="Ödeme sırasında banka POS cihazının ardışık olarak hata vermesi.",
            extracted_summary="Ödeme esnasında yaşanan POS donanım hatası.",
            extraction_confidence=0.87
        ),
        "contact_status": ContactStatus.NOT_CONTACTED.value
    },
    {
        # Kademe 1: Teşekkür -> Onaylandı
        "case_id": "FB-2026-1010",
        "created_at": "2026-10-04 17:00:00",
        "source_channel": SourceChannel.CALL_CENTER.value,
        "original_feedback": "Her şey mükemmeldi. Merkez Şehir Hastanesi Kardiyoloji ekibine ve doktorumuza gösterdikleri yakın ilgiden dolayı çok teşekkür ederiz.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.APPRECIATION,
            issue_type=IssueType.APPRECIATION,
            sentiment=SentimentType.POSITIVE,
            hospital="Merkez Şehir Hastanesi",
            department="Kardiyoloji Polikliniği",
            description_of_event="Kardiyoloji ekibinin üstün klinik ilgisi ve hasta memnuniyeti.",
            extracted_summary="Kardiyoloji bölümü sağlık personeline teşekkür bildirimi.",
            extraction_confidence=0.97
        ),
        "contact_status": ContactStatus.COMPLETED.value
    },
    {
        # Kademe 2: AI Sesli Arama ile Çözümlenmiş Vaka
        "case_id": "FB-2026-1011",
        "created_at": "2026-09-30 15:20:00",
        "source_channel": SourceChannel.CALL_CENTER.value,
        "original_feedback": "Geçen salı Merkez Şehir Hastanesi'nde kan tahlili sonuçlarımın çıkması çok uzun sürdü.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.WAITING_TIME,
            sentiment=SentimentType.NEGATIVE,
            hospital="Merkez Şehir Hastanesi",
            department=None,
            incident_date="Geçen salı",
            service_type="Kan Tahlili",
            description_of_event="Flebotomi laboratuvar sonuçlarının onaylanma süresinde gecikme.",
            extracted_summary="Kan tahlili sonuçlarının çıkış süresinde gecikme yaşanması.",
            extraction_confidence=0.87
        ),
        "contact_status": ContactStatus.AI_CALL_COMPLETED.value,
        "ai_call_data": {
            "department": "Biyokimya Laboratuvarı",
            "approximate_time": "10:30"
        },
        "transcript": (
            "YAPAY ZEKA ASİSTANI: Merhaba, Merkez Şehir Hastanesi Hasta Deneyimi Merkezi'nden arıyorum. Geçen salı günkü kan tahlili gecikmeniz hakkında laboratuvar süpervizörümüzle görüşeceğiz. Kan örneğinizi hangi birimde vermiştiniz?\n"
            "HASTA: 2. kattaki ana Biyokimya Laboratuvarı'nda sabah saat 10:30 civarında vermiştim.\n"
            "YAPAY ZEKA ASİSTANI: Çok teşekkürler, bu bilgiyi laboratuvar sorumlusuna ilettik. Sağlıklı günler dileriz!"
        )
    }
]


def seed_database(force: bool = False) -> int:
    """Populate database with synthetic cases if empty or force=True."""
    init_db()
    current_count = count_cases()
    if current_count > 0 and not force:
        return current_count

    inserted = 0
    for item in SEED_CASES:
        ext = item["extracted"]
        result = evaluate_completeness(ext)
        case_dict = ext.model_dump()
        case_dict["case_id"] = item["case_id"]
        case_dict["created_at"] = item["created_at"]
        case_dict["source_channel"] = item["source_channel"]
        case_dict["original_feedback"] = item["original_feedback"]
        case_dict["contact_status"] = item["contact_status"]
        if "transcript" in item:
            case_dict["ai_call_transcript"] = item["transcript"]

        save_case(case_dict, result)
        inserted += 1

        # Simulate completed AI call for case 1011
        if "ai_call_data" in item:
            add_follow_up_entry(
                case_id=item["case_id"],
                contact_status=ContactStatus.AI_CALL_COMPLETED.value,
                additional_information="Yapay Zeka Sesli Arama başarıyla tamamlandı. Alınan bilgiler: Biyokimya Laboratuvarı, 10:30.",
                notes="Otonom sesli arama süresi: 52 saniye."
            )
            overrides = item["ai_call_data"]
            reeval_res = evaluate_completeness(ext, confirmed_overrides=overrides)
            update_case_after_reevaluation(
                case_id=item["case_id"],
                updated_fields={**overrides, "ai_call_transcript": item["transcript"]},
                result=reeval_res,
                extracted_json=ext.model_dump_json()
            )

    return inserted


if __name__ == "__main__":
    count = seed_database(force=True)
    print(f"Successfully seeded {count} cases into FeedbackIQ database.")
