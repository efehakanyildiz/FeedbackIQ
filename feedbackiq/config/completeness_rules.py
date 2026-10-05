"""
Kategori bazlı deterministik tamamlanma kuralları ve puanlama ağırlıkları.
Tüm açıklamalar ve iş kuralları Türkçe olarak yapılandırılmıştır.
"""

from typing import Dict, Any, List

# Tamamlanma eşik değerleri
THRESHOLD_COMPLETE = 80
THRESHOLD_NEEDS_REVIEW = 50

# Şikayet/Bildirim Türüne Göre Ağırlık ve Kritik Alan Konfigürasyonu
# Puanlama Modeli:
# - Başlangıç Skoru: 100
# - Büyük Eksikler (critical_fields): Her biri -30 puan
# - Küçük Eksikler (minor_fields): Her biri -5 puan
# - Triage:
#     * 0 eksik -> Kademe 1: Onaylandı (100 Puan)
#     * 1-4 küçük eksik veya 1 büyük eksik -> Kademe 2: Yapay Zeka Asistanı (AI Sesli Bot)
#     * 2 veya daha fazla büyük eksik veya skor < 50 -> Kademe 3: Müşteri Hizmetleri Masası
ISSUE_RULES_CONFIG: Dict[str, Dict[str, Any]] = {
    "Bekleme Süresi": {
        "critical_fields": ["hospital", "department", "description_of_event"],
        "minor_fields": ["approximate_time", "incident_date"],
        "weights": {
            "hospital": 30,
            "department": 30,
            "description_of_event": 30,
            "approximate_time": 5,
            "incident_date": 5,
        },
        "or_groups": [],
        "explanation": "Bekleme süresi şikayetlerinde kuyruk ve randevu loglarını denetlemek için hastane şubesi ve poliklinik bilgisi zorunludur."
    },
    "Personel Davranışı": {
        "critical_fields": ["hospital", "department", "description_of_event"],
        "minor_fields": ["approximate_time", "incident_date", "staff_role"],
        "weights": {
            "hospital": 30,
            "department": 30,
            "description_of_event": 30,
            "approximate_time": 5,
            "incident_date": 5,
            "staff_role": 5,
        },
        "or_groups": [
            ("staff_role", "staff_name"),
        ],
        "explanation": "Personel tutumu bildirimlerinde birim yöneticisinin inceleme yapabilmesi için hastane ve ilgili poliklinik zorunludur."
    },
    "Fatura & Ödeme": {
        "critical_fields": ["hospital", "billing_context", "description_of_event"],
        "minor_fields": ["department", "incident_date"],
        "weights": {
            "hospital": 30,
            "billing_context": 30,
            "description_of_event": 30,
            "department": 5,
            "incident_date": 5,
        },
        "or_groups": [],
        "explanation": "Ödeme ve fatura incelemelerinde muhasebe mutabakatı için hastane şubesi ve ödeme tutarsızlığı detayları zorunludur."
    },
    "Randevu Süreci": {
        "critical_fields": ["hospital", "department", "description_of_event"],
        "minor_fields": ["approximate_time", "incident_date"],
        "weights": {
            "hospital": 30,
            "department": 30,
            "description_of_event": 30,
            "approximate_time": 5,
            "incident_date": 5,
        },
        "or_groups": [],
        "explanation": "Randevu aksaklıklarında HBYS kayıtlarını denetlemek için hastane şubesi ve poliklinik / uzmanlık alanı zorunludur."
    },
    "Danışma / Kayıt": {
        "critical_fields": ["hospital", "department", "description_of_event"],
        "minor_fields": ["approximate_time", "incident_date"],
        "weights": {
            "hospital": 30,
            "department": 30,
            "description_of_event": 30,
            "approximate_time": 5,
            "incident_date": 5,
        },
        "or_groups": [],
        "explanation": "Hasta kabul ve kayıt aksaklıklarında desk işlemlerini incelemek için hastane lokasyonu ve birim bilgisi zorunludur."
    },
    "Temizlik & Tesis": {
        "critical_fields": ["hospital", "department", "description_of_event"],
        "minor_fields": ["approximate_time", "incident_date"],
        "weights": {
            "hospital": 30,
            "department": 30,
            "description_of_event": 30,
            "approximate_time": 5,
            "incident_date": 5,
        },
        "or_groups": [],
        "explanation": "Hijyen ve teknik altyapı bildirimlerinde temizlik ekiplerini yönlendirmek için tam hastane ve birim/kat bilgisi zorunludur."
    },
    "Tıbbi Hizmet Süreci": {
        "critical_fields": ["hospital", "department", "description_of_event"],
        "minor_fields": ["incident_date", "approximate_time", "staff_role"],
        "weights": {
            "hospital": 30,
            "department": 30,
            "description_of_event": 30,
            "incident_date": 5,
            "approximate_time": 5,
            "staff_role": 5,
        },
        "or_groups": [
            ("staff_role", "staff_name"),
        ],
        "explanation": "Klinik süreç geri bildirimlerinde kalite direktörlüğü incelemesi için hastane ve poliklinik bilgisi zorunludur."
    },
    "İletişim & Bilgilendirme": {
        "critical_fields": ["hospital", "department", "description_of_event"],
        "minor_fields": ["approximate_time", "incident_date"],
        "weights": {
            "hospital": 30,
            "department": 30,
            "description_of_event": 30,
            "approximate_time": 5,
            "incident_date": 5,
        },
        "or_groups": [],
        "explanation": "İletişim eksikliklerinde hasta bilgilendirme süreçlerini netleştirmek için hastane ve birim bağlamı zorunludur."
    },
    "Teknik Aksaklık": {
        "critical_fields": ["hospital", "description_of_event"],
        "minor_fields": ["department", "incident_date"],
        "weights": {
            "hospital": 30,
            "description_of_event": 30,
            "department": 5,
            "incident_date": 5,
        },
        "or_groups": [],
        "explanation": "Sistem arızalarında arızalanan cihaz veya yazılımın açıkça tanımlanması gereklidir."
    },
    "Yemek & İkram": {
        "critical_fields": ["hospital", "description_of_event"],
        "minor_fields": ["department", "incident_date"],
        "weights": {
            "hospital": 30,
            "description_of_event": 30,
            "department": 5,
            "incident_date": 5,
        },
        "or_groups": [],
        "explanation": "Yemek ve ikram bildirimlerinde dağıtım servisini denetlemek için hastane ve servis katı bilgisi gereklidir."
    },
    "Otopark & Ulaşım": {
        "critical_fields": ["hospital", "description_of_event"],
        "minor_fields": ["incident_date"],
        "weights": {
            "hospital": 30,
            "description_of_event": 30,
            "incident_date": 5,
        },
        "or_groups": [],
        "explanation": "Otopark bildirimlerinde yerleşke ve otopark alanı tanımı gereklidir."
    },
    "Teşekkür & Memnuniyet": {
        "critical_fields": ["description_of_event"],
        "minor_fields": ["hospital", "department"],
        "weights": {
            "description_of_event": 30,
            "hospital": 5,
            "department": 5,
        },
        "or_groups": [
            ("hospital", "department"),
        ],
        "explanation": "Memnuniyet bildirimlerinde hastane veya birim bilgisinin bulunması tebrik iletimi için yeterlidir."
    },
    "Genel Öneri": {
        "critical_fields": ["description_of_event"],
        "minor_fields": ["hospital", "department"],
        "weights": {
            "description_of_event": 30,
            "hospital": 5,
            "department": 5,
        },
        "or_groups": [],
        "explanation": "Öneri kayıtlarında uygulanabilir operasyonel fikir ve bağlamın açıklanması gereklidir."
    },
    "Diğer": {
        "critical_fields": ["hospital", "description_of_event"],
        "minor_fields": ["department", "incident_date"],
        "weights": {
            "hospital": 30,
            "description_of_event": 30,
            "department": 5,
            "incident_date": 5,
        },
        "or_groups": [],
        "explanation": "Kategorize edilmemiş geri bildirimlerde ön inceleme için yeterli açıklama ve bağlam gereklidir."
    }
}

# English key alias fallback so tests and legacy schemas remain compatible
ISSUE_RULES_CONFIG["Waiting Time"] = ISSUE_RULES_CONFIG["Bekleme Süresi"]
ISSUE_RULES_CONFIG["Staff Behavior"] = ISSUE_RULES_CONFIG["Personel Davranışı"]
ISSUE_RULES_CONFIG["Billing / Payment"] = ISSUE_RULES_CONFIG["Fatura & Ödeme"]
ISSUE_RULES_CONFIG["Appointment"] = ISSUE_RULES_CONFIG["Randevu Süreci"]
ISSUE_RULES_CONFIG["Registration"] = ISSUE_RULES_CONFIG["Danışma / Kayıt"]
ISSUE_RULES_CONFIG["Facility / Cleanliness"] = ISSUE_RULES_CONFIG["Temizlik & Tesis"]
ISSUE_RULES_CONFIG["Medical Service Process"] = ISSUE_RULES_CONFIG["Tıbbi Hizmet Süreci"]
ISSUE_RULES_CONFIG["Communication"] = ISSUE_RULES_CONFIG["İletişim & Bilgilendirme"]
ISSUE_RULES_CONFIG["Technical Issue"] = ISSUE_RULES_CONFIG["Teknik Aksaklık"]
ISSUE_RULES_CONFIG["Food / Catering"] = ISSUE_RULES_CONFIG["Yemek & İkram"]
ISSUE_RULES_CONFIG["Parking / Transportation"] = ISSUE_RULES_CONFIG["Otopark & Ulaşım"]
ISSUE_RULES_CONFIG["Appreciation"] = ISSUE_RULES_CONFIG["Teşekkür & Memnuniyet"]
ISSUE_RULES_CONFIG["General Suggestion"] = ISSUE_RULES_CONFIG["Genel Öneri"]
ISSUE_RULES_CONFIG["Other"] = ISSUE_RULES_CONFIG["Diğer"]
