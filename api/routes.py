"""
api/routes.py

FastAPI REST API for the BFSI Compliance Agent.
Accepts audio file uploads or transcript text, runs the full
LangGraph pipeline, and returns structured AuditReport JSON.

Endpoints:
    POST /analyse/audio     — upload audio file → full pipeline
    POST /analyse/transcript — submit text transcript → full pipeline
    GET  /report/{call_id}  — retrieve saved report by call ID
    GET  /calls             — list all analysed calls
    GET  /health            — health check
"""

import os
import sys
import json
import uuid
import shutil
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import config
from agents.orchestrator import run_analysis

# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BFSI AI Compliance & Fraud Intelligence Agent",
    description="Agentic AI platform for banking call compliance monitoring",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to dashboard origin
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "outputs")
AUDIO_DIR   = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "audio")
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)


# ── Request / Response models ──────────────────────────────────────────────────

class TranscriptRequest(BaseModel):
    transcript: str
    call_id: Optional[str] = None
    scenario_label: Optional[str] = ""


class AnalysisResponse(BaseModel):
    call_id: str
    status: str
    rag_status: Optional[str] = None
    composite_score: Optional[int] = None
    message: str


# ── Helpers ────────────────────────────────────────────────────────────────────

def _save_result(state: dict, call_id: str) -> str:
    """Serialise and save AuditReport state to data/outputs/."""
    output_path = os.path.join(OUTPUTS_DIR, f"{call_id}_result.json")

    def serialise(obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "value"):
            return obj.value
        return str(obj)

    output = {
        "call_id": state.get("call_id"),
        "scenario_label": state.get("scenario_label"),
        "processing_status": state.get("processing_status"),
        "errors": state.get("errors", []),
        "risk_score":            serialise(state.get("risk_score"))            if state.get("risk_score")            else None,
        "fraud_findings":        serialise(state.get("fraud_findings"))        if state.get("fraud_findings")        else None,
        "compliance_findings":   serialise(state.get("compliance_findings"))   if state.get("compliance_findings")   else None,
        "vulnerability_findings":serialise(state.get("vulnerability_findings"))if state.get("vulnerability_findings")else None,
        "agent_quality":         serialise(state.get("agent_quality"))         if state.get("agent_quality")         else None,
        "audit_report":          serialise(state.get("audit_report"))          if state.get("audit_report")          else None,
        "diarised_transcript":   state.get("diarised_transcript"),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    return output_path


def _load_result(call_id: str) -> Optional[dict]:
    """Load a saved result by call_id."""
    path = os.path.join(OUTPUTS_DIR, f"{call_id}_result.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _list_results() -> list[dict]:
    """List all saved results as summary dicts."""
    summaries = []
    for filepath in sorted(os.listdir(OUTPUTS_DIR)):
        if not filepath.endswith("_result.json"):
            continue
        try:
            with open(os.path.join(OUTPUTS_DIR, filepath), "r", encoding="utf-8") as f:
                data = json.load(f)
            rs = data.get("risk_score") or {}
            summaries.append({
                "call_id":        data.get("call_id"),
                "scenario_label": data.get("scenario_label"),
                "status":         data.get("processing_status"),
                "rag_status":     rs.get("rag_status"),
                "composite_score":rs.get("composite_score"),
                "errors":         len(data.get("errors", [])),
            })
        except Exception:
            continue
    return summaries


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "BFSI Compliance Agent",
        "version": "1.0.0",
        "llm_provider": config.LLM_PROVIDER,
        "model": config.GROQ_MODEL if config.LLM_PROVIDER == "groq" else config.OPENROUTER_MODEL,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/calls")
def list_calls():
    """List all analysed calls with summary risk scores."""
    return {"calls": _list_results(), "total": len(_list_results())}


@app.get("/report/{call_id}")
def get_report(call_id: str):
    """Retrieve full audit report for a specific call."""
    data = _load_result(call_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Report not found for call_id: {call_id}")
    return data


@app.post("/analyse/transcript", response_model=AnalysisResponse)
def analyse_transcript(request: TranscriptRequest):
    """
    Analyse a text transcript through the full LangGraph pipeline.

    Body:
        transcript:     Plain text transcript (AGENT:/CUSTOMER: format preferred)
        call_id:        Optional — auto-generated if not provided
        scenario_label: Optional human-readable label
    """
    if not request.transcript.strip():
        raise HTTPException(status_code=400, detail="transcript cannot be empty")

    call_id = request.call_id or f"CALL-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

    try:
        state = run_analysis(
            transcript=request.transcript,
            call_id=call_id,
            scenario_label=request.scenario_label or "",
        )

        output_path = _save_result(state, call_id)
        rs = state.get("risk_score")

        return AnalysisResponse(
            call_id=call_id,
            status=state.get("processing_status", "unknown"),
            rag_status=rs.rag_status.value if rs and hasattr(rs.rag_status, "value") else (rs.get("rag_status") if rs else None),
            composite_score=rs.composite_score if rs and hasattr(rs, "composite_score") else None,
            message=f"Analysis complete. Report saved to {output_path}",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyse/audio", response_model=AnalysisResponse)
async def analyse_audio(
    file: UploadFile = File(...),
    call_id: Optional[str] = Form(None),
    scenario_label: Optional[str] = Form(""),
):
    """
    Analyse an audio file through the full pipeline:
    Upload → Whisper → Diarisation → LangGraph agents → AuditReport

    Accepts: .wav, .mp3, .m4a, .ogg, .flac
    Max size: handled by server config
    """
    # Validate file type
    allowed_extensions = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".mp4"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"
        )

    cid = call_id or f"CALL-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

    # Save uploaded file to data/audio/
    audio_filename = f"{cid}{file_ext}"
    audio_path = os.path.join(AUDIO_DIR, audio_filename)

    try:
        with open(audio_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save audio file: {str(e)}")

    # Run full pipeline
    try:
        state = run_analysis(
            audio_path=audio_path,
            call_id=cid,
            scenario_label=scenario_label or file.filename,
        )

        output_path = _save_result(state, cid)
        rs = state.get("risk_score")

        return AnalysisResponse(
            call_id=cid,
            status=state.get("processing_status", "unknown"),
            rag_status=rs.rag_status.value if rs and hasattr(rs.rag_status, "value") else None,
            composite_score=rs.composite_score if rs and hasattr(rs, "composite_score") else None,
            message=f"Audio analysis complete. Report saved to {output_path}",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio analysis failed: {str(e)}")
