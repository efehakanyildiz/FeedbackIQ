"""
FastAPI Enterprise Application Server for FeedbackIQ.
Provides high-performance REST endpoints and serves the modern SPA frontend.
100% Free architecture: FastAPI + SQLite + Google Gemini Flash (Free Tier).
"""

import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from feedbackiq.database.db import init_db
from feedbackiq.database.seed import seed_database
from feedbackiq.database.repository import (
    save_case,
    get_case,
    get_cases,
    get_missing_fields_for_case,
    get_follow_up_entries,
    get_kpis,
    get_analytics_data,
)
from feedbackiq.services.gemini_service import extract_feedback_info
from feedbackiq.services.completeness_service import evaluate_completeness
from feedbackiq.services.followup_service import process_case_reevaluation
from feedbackiq.services.ai_call_service import simulate_ai_voice_call

load_dotenv()

# Initialize DB on startup
init_db()
seed_database(force=False)

app = FastAPI(
    title="FeedbackIQ API",
    description="Hasta Deneyimi Kalite & Triage Güvenlik Katmanı REST API",
    version="2.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    feedback_text: str
    source_channel: str = "Web Sitesi"
    known_hospital: Optional[str] = None
    known_date: Optional[str] = None


class ReevaluateRequest(BaseModel):
    confirmed_fields: Dict[str, Any]
    notes: Optional[str] = ""
    contact_status: Optional[str] = "Information Collected"


class AiCallRequest(BaseModel):
    patient_responses: Optional[Dict[str, Any]] = None


@app.get("/api/kpis")
def api_get_kpis():
    """Genel dashboard KPI metriklerini döndürür."""
    return get_kpis()


@app.get("/api/analytics")
def api_get_analytics():
    """Kanal kalitesi ve triage dağılım analitiklerini döndürür."""
    return get_analytics_data()


@app.get("/api/cases")
def api_get_cases(
    tier: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "score_asc"
):
    """Filtrelenmiş vaka listesini döndürür."""
    return get_cases(
        tier_filter=tier,
        issue_type_filter=category,
        status_filter=status,
        sort_by=sort_by
    )


@app.get("/api/cases/{case_id}")
def api_get_case_detail(case_id: str):
    """Tek bir vakanın tüm detaylarını, eksik alanlarını ve geçmişini döndürür."""
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Vaka bulunamadı.")
    missing_fields = get_missing_fields_for_case(case_id)
    history = get_follow_up_entries(case_id)
    return {
        "case": case,
        "missing_fields": missing_fields,
        "history": history
    }


@app.post("/api/analyze")
def api_analyze_feedback(payload: AnalyzeRequest):
    """Hasta geri bildirimini analiz eder, operasyonel değişkenleri çıkarır ve triage kademesini belirler."""
    text = payload.feedback_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Geri bildirim metni boş olamaz.")

    context_parts = []
    if payload.known_hospital and payload.known_hospital.strip():
        context_parts.append(f"Hastane: {payload.known_hospital.strip()}")
    if payload.known_date and payload.known_date.strip():
        context_parts.append(f"Tarih: {payload.known_date.strip()}")
    context_str = ", ".join(context_parts) if context_parts else None

    # Gemini çıkarımı
    extracted, is_live, warning = extract_feedback_info(text, context_hint=context_str)

    # Deterministik kurallar & 3 kademeli triage
    confirmed_overrides = {}
    if payload.known_hospital and payload.known_hospital.strip():
        confirmed_overrides["hospital"] = payload.known_hospital.strip()
    if payload.known_date and payload.known_date.strip():
        confirmed_overrides["incident_date"] = payload.known_date.strip()

    result = evaluate_completeness(extracted, confirmed_overrides=confirmed_overrides)

    case_dict = extracted.model_dump()
    case_dict["source_channel"] = payload.source_channel
    case_dict["original_feedback"] = text
    for k, v in confirmed_overrides.items():
        case_dict[k] = v

    case_id = save_case(case_dict, result)

    return {
        "case_id": case_id,
        "extracted": extracted.model_dump(),
        "result": result.model_dump(),
        "is_live": is_live,
        "warning": warning
    }


@app.post("/api/cases/{case_id}/reevaluate")
def api_reevaluate_case(case_id: str, payload: ReevaluateRequest):
    """Müşteri temsilcisi tarafından girilen teyitli verilerle vakayı yeniden değerlendirir."""
    try:
        updated_case, result, prev_score = process_case_reevaluation(
            case_id=case_id,
            confirmed_fields=payload.confirmed_fields,
            notes=payload.notes or "Müşteri Hizmetleri Masası üzerinden güncellendi.",
            contact_status=payload.contact_status or "Information Collected"
        )
        return {
            "case": updated_case,
            "result": result.model_dump(),
            "prev_score": prev_score
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/cases/{case_id}/simulate-ai-call")
def api_simulate_ai_call(case_id: str, payload: Optional[AiCallRequest] = None):
    """Kademe 2 vakaları için otomatik Yapay Zeka Sesli Arama Botu telefon görüşmesi simülasyonu yapar."""
    try:
        responses = payload.patient_responses if payload else None
        updated_case, result, transcript = simulate_ai_voice_call(
            case_id=case_id,
            patient_responses=responses
        )
        return {
            "case": updated_case,
            "result": result.model_dump(),
            "transcript": transcript
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/seed")
def api_reseed_database():
    """Örnek sentetik verileri yeniden yükler."""
    count = seed_database(force=True)
    return {"message": f"{count} adet sentetik vaka başarıyla yüklendi."}


# Mount modern static web frontend
web_dir = os.path.join(os.path.dirname(__file__), "web")
if os.path.exists(web_dir):
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
