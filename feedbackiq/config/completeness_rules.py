"""
Kategori bazlı deterministik tamamlanma kuralları ve puanlama ağırlıkları.
Tüm açıklamalar ve iş kuralları Türkçe olarak yapılandırılmıştır.
"""

from typing import Dict, Any, List

# Tamamlanma eşik değerleri
THRESHOLD_COMPLETE = 80
THRESHOLD_NEEDS_REVIEW = 50

# Şikayet/Bildirim Türüne Göre Ağırlık ve Kritik Alan Konfigürasyonu
ISSUE_RULES_CONFIG: Dict[str, Dict[str, Any]] = {
    "Bekleme Süresi": {
        "weights": {
            "hospital": 25,
            "department": 25,
            "incident_date": 15,
            "approximate_time": 15,
            "description_of_event": 20,
        },
        "critical_fields": ["hospital", "department", "incident_date", "description_of_event"],
        "or_groups": [],
        "explanation": "Bekleme süresi şikayetlerinde kuyruk ve randevu loglarını denetlemek için hastane şubesi, poliklinik, tarih ve yaklaşık saat bilgisi gereklidir."
    },
    "Personel Davranışı": {
        "weights": {
            "hospital": 25,
            "department": 20,
            "incident_date": 15,
            "staff_role": 15,
            "staff_name": 5,
            "approximate_time": 5,
            "description_of_event": 15,
        },
        "critical_fields": ["hospital", "department", "incident_date", "description_of_event"],
        "or_groups": [
            ("staff_role", "staff_name"),
        ],
        "explanation": "Personel tutumu bildirimlerinde birim yöneticisinin hedefe yönelik inceleme yapabilmesi için hastane, ilgili poliklinik ve personelin unvanı/adı gereklidir."
    },
    "Fatura & Ödeme": {
        "weights": {
            "hospital": 25,
            "department": 15,
            "incident_date": 15,
            "billing_context": 25,
            "description_of_event": 20,
        },
        "critical_fields": ["hospital", "billing_context", "description_of_event"],
        "or_groups": [],
        "explanation": "Ödeme ve fatura incelemelerinde muhasebe mutabakatı için ilgili hastane, işlem tarihi ve ödeme tutarsızlığı detayları zorunludur."
    },
    "Randevu Süreci": {
        "weights": {
            "hospital": 25,
            "department": 25,
            "incident_date": 15,
            "approximate_time": 15,
            "description_of_event": 20,
        },
        "critical_fields": ["hospital", "department", "incident_date", "description_of_event"],
        "or_groups": [],
        "explanation": "Randevu aksaklıklarında HBYS kayıtlarını denetlemek için hastane, poliklinik / uzmanlık alanı ve randevu tarihi gereklidir."
    },
    "Danışma / Kayıt": {
        "weights": {
            "hospital": 25,
            "department": 20,
            "incident_date": 20,
            "approximate_time": 15,
            "description_of_event": 20,
        },
        "critical_fields": ["hospital", "incident_date", "description_of_event"],
        "or_groups": [],
        "explanation": "Hasta kabul ve kayıt aksaklıklarında desk işlemlerini incelemek için hastane lokasyonu ve tarih bilgisi gereklidir."
    },
    "Temizlik & Tesis": {
        "weights": {
            "hospital": 30,
            "department": 25,
            "incident_date": 15,
            "description_of_event": 30,
        },
        "critical_fields": ["hospital", "department", "description_of_event"],
        "or_groups": [],
        "explanation": "Hijyen ve teknik altyapı bildirimlerinde temizlik veya teknik ekipleri yönlendirmek için tam hastane ve birim/kat lokasyonu gereklidir."
    },
    "Tıbbi Hizmet Süreci": {
        "weights": {
            "hospital": 25,
            "department": 25,
            "incident_date": 15,
            "service_type": 15,
            "description_of_event": 20,
        },
        "critical_fields": ["hospital", "department", "incident_date", "description_of_event"],
        "or_groups": [],
        "explanation": "Klinik süreç geri bildirimlerinde kalite direktörlüğü incelemesi için hastane, poliklinik ve tetkik bilgisi gereklidir."
    },
    "İletişim & Bilgilendirme": {
        "weights": {
            "hospital": 25,
            "department": 25,
            "incident_date": 20,
            "description_of_event": 30,
        },
        "critical_fields": ["hospital", "department", "description_of_event"],
        "or_groups": [],
        "explanation": "İletişim eksikliklerinde hasta bilgilendirme süreçlerini netleştirmek için hastane ve birim bağlamı gereklidir."
    },
    "Teknik Aksaklık": {
        "weights": {
            "hospital": 25,
            "department": 20,
            "incident_date": 20,
            "description_of_event": 35,
        },
        "critical_fields": ["hospital", "description_of_event"],
        "or_groups": [],
        "explanation": "Sistem arızalarında arızalanan cihaz veya yazılımın (portal, vezne POS, sıramatik) açıkça tanımlanması gereklidir."
    },
    "Yemek & İkram": {
        "weights": {
            "hospital": 30,
            "department": 20,
            "incident_date": 20,
            "description_of_event": 30,
        },
        "critical_fields": ["hospital", "description_of_event"],
        "or_groups": [],
        "explanation": "Yemek ve ikram bildirimlerinde dağıtım servisini denetlemek için hastane ve servis katı bilgisi gereklidir."
    },
    "Otopark & Ulaşım": {
        "weights": {
            "hospital": 40,
            "incident_date": 20,
            "description_of_event": 40,
        },
        "critical_fields": ["hospital", "description_of_event"],
        "or_groups": [],
        "explanation": "Otopark bildirimlerinde yerleşke ve otopark alanı tanımı gereklidir."
    },
    "Teşekkür & Memnuniyet": {
        "weights": {
            "hospital": 25,
            "department": 25,
            "staff_role": 15,
            "staff_name": 15,
            "description_of_event": 20,
        },
        "critical_fields": ["description_of_event"],
        "or_groups": [
            ("hospital", "department"),
        ],
        "explanation": "Memnuniyet bildirimlerinde hastane veya birim bilgisinin bulunması tebrik iletimi için yeterlidir."
    },
    "Genel Öneri": {
        "weights": {
            "hospital": 20,
            "department": 20,
            "description_of_event": 40,
            "service_type": 20,
        },
        "critical_fields": ["description_of_event"],
        "or_groups": [],
        "explanation": "Öneri kayıtlarında uygulanabilir operasyonel fikir ve bağlamın açıklanması gereklidir."
    },
    "Diğer": {
        "weights": {
            "hospital": 25,
            "department": 20,
            "incident_date": 20,
            "description_of_event": 35,
        },
        "critical_fields": ["description_of_event"],
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
