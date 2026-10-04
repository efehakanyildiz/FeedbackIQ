"""
Deterministik takip sorusu şablonları ve alan görüntüleme eşleştirmeleri.
Yalnızca eksik olan alanlar için hedefe yönelik Türkçe sorular üretilir.
"""

FIELD_DISPLAY_NAMES = {
    "hospital": "Hastane / Şube Adı",
    "department": "Poliklinik / Birim",
    "incident_date": "Olay Tarihi",
    "approximate_time": "Yaklaşık Saat",
    "service_type": "Hizmet / Tetkik Türü",
    "staff_role": "Personel Görevi / Unvanı",
    "staff_name": "Personel Adı",
    "billing_context": "Fatura / Ödeme Detayı",
    "description_of_event": "Olay Açıklaması",
    "impact": "Operasyonel Etki / Mağduriyet",
}

QUESTION_TEMPLATES = {
    "hospital": "Ziyaret ettiğiniz hastane veya şubeyi öğrenebilir miyiz?",
    "department": "Hangi poliklinik veya tıbbi birimden hizmet aldınız?",
    "incident_date": "Yaşanan durum hangi tarihte gerçekleşti?",
    "approximate_time": "Durum yaklaşık olarak günün hangi saatinde meydana geldi?",
    "service_type": "Hangi muayene veya tetkik işlemi sırasında bu durum yaşandı?",
    "staff_role": "Görüştüğünüz personelin unvanını hatırlıyor musunuz (doktor, hemşire, vezne görevlisi vb.)?",
    "staff_name": "İlgili personelin ismini hatırlıyor musunuz?",
    "billing_context": "Ödeme veya fatura tutarsızlığı hakkında biraz daha ayrıntı verebilir misiniz?",
    "description_of_event": "Yaşanan durumu kısaca biraz daha detaylandırabilir misiniz?",
    "impact": "Bu durum tedavi sürecinizi veya günlük planınızı nasıl etkiledi?",
}


def get_question_for_field(field_name: str) -> str:
    """Eksik alan için hedefe yönelik standart Türkçe soruyu döndürür."""
    return QUESTION_TEMPLATES.get(
        field_name,
        f"{FIELD_DISPLAY_NAMES.get(field_name, field_name)} hakkında bilgi verebilir misiniz?"
    )


def get_field_display_name(field_name: str) -> str:
    """Alan anahtarı için temiz, profesyonel Türkçe başlık döndürür."""
    return FIELD_DISPLAY_NAMES.get(field_name, field_name.replace("_", " ").title())
