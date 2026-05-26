"""
agents/orchestrator.py

LangGraph multi-agent graph for BFSI compliance analysis.

Sprint 3 graph flow:
    START
      ↓
    prepare_node        — route: audio file OR text transcript
      ↓
    transcribe_node     — Whisper: audio → raw transcript (skipped for text input)
      ↓
    diarise_node        — pyannote: raw → AGENT/CUSTOMER labelled segments (skipped for text)
      ↓
    fraud_agent → compliance_agent → vulnerability_agent → agent_behaviour
      ↓
    risk_scoring_node
      ↓
    report_node
      ↓
    END
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, START, END

from schemas.state import CallAnalysisState
from agents.fraud_agent import fraud_agent_node
from agents.compliance_agent import compliance_agent_node
from agents.vulnerability_agent import vulnerability_agent_node
from agents.agent_behaviour_agent import agent_behaviour_node
from agents.risk_scoring_agent import risk_scoring_node
from agents.report_agent import report_agent_node


# ── Prepare node ───────────────────────────────────────────────────────────────

def prepare_node(state: CallAnalysisState) -> dict:
    """
    Entry node: validate input and determine pipeline path.
    - Audio path provided → will go through transcribe + diarise nodes
    - Raw transcript provided → skip to agent analysis directly
    """
    audio_path = state.get("audio_path")
    raw = state.get("raw_transcript", "")
    errors = list(state.get("errors", []))

    if not audio_path and not raw:
        return {
            "processing_status": "error",
            "errors": ["No input provided — supply either audio_path or raw_transcript"],
        }

    # If text transcript provided directly, format it now
    if raw and not audio_path:
        diarised = state.get("diarised_transcript")
        if diarised:
            lines = []
            for seg in diarised:
                speaker = seg.get("speaker", "UNKNOWN").upper()
                text = seg.get("text", "").strip()
                if text:
                    lines.append(f"{speaker}: {text}")
            formatted = "\n".join(lines)
        else:
            formatted = raw

        return {
            "formatted_transcript": formatted,
            "processing_status": "analysing",
            "errors": errors,
        }

    # Audio path provided — transcription happens in next nodes
    return {
        "processing_status": "transcribing",
        "errors": errors,
    }


# ── Transcription node ─────────────────────────────────────────────────────────

def transcribe_node(state: CallAnalysisState) -> dict:
    """
    LangGraph node: transcribe audio file using Whisper.
    Skipped if raw_transcript already provided.
    """
    if state.get("raw_transcript") and not state.get("audio_path"):
        return {}  # Already have transcript — skip

    audio_path = state.get("audio_path")
    if not audio_path:
        return {}

    errors = list(state.get("errors", []))

    try:
        from services.whisper_service import transcribe
        result = transcribe(audio_path)
        return {
            "raw_transcript": result["text"],
            "whisper_segments": result["segments"],
            "processing_status": "diarising",
            "errors": errors,
        }
    except Exception as e:
        errors.append(f"TranscribeNode error: {str(e)}")
        return {
            "processing_status": "error",
            "errors": errors,
        }


# ── Diarisation node ───────────────────────────────────────────────────────────

def diarise_node(state: CallAnalysisState) -> dict:
    """
    LangGraph node: separate AGENT and CUSTOMER speech using pyannote.
    Skipped if no audio_path (text-only pipeline).
    """
    audio_path = state.get("audio_path")
    if not audio_path:
        return {}  # Text-only pipeline — skip diarisation

    errors = list(state.get("errors", []))

    try:
        from services.diarisation_service import diarise, format_diarised_transcript

        # Reuse segments already stored by transcribe_node — avoid double transcription
        segments = state.get("whisper_segments") or []
        if not segments:
            from services.whisper_service import get_segments
            segments = get_segments(audio_path)
        diarised = diarise(audio_path, segments)
        formatted = format_diarised_transcript(diarised)

        return {
            "diarised_transcript": diarised,
            "formatted_transcript": formatted,
            "processing_status": "analysing",
            "errors": errors,
        }
    except Exception as e:
        errors.append(f"DiariseNode error: {str(e)}")
        # Fallback: use raw transcript without speaker labels
        raw = state.get("raw_transcript", "")
        return {
            "formatted_transcript": raw,
            "processing_status": "analysing",
            "errors": errors,
        }


# ── Graph builder ──────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph multi-agent graph.
    Sprint 3: includes transcribe and diarise nodes.
    """
    graph = StateGraph(CallAnalysisState)

    # Register all nodes
    graph.add_node("prepare",              prepare_node)
    graph.add_node("transcribe",           transcribe_node)
    graph.add_node("diarise",              diarise_node)
    graph.add_node("fraud_agent",          fraud_agent_node)
    graph.add_node("compliance_agent",     compliance_agent_node)
    graph.add_node("vulnerability_agent",  vulnerability_agent_node)
    graph.add_node("agent_behaviour",      agent_behaviour_node)
    graph.add_node("risk_scoring",         risk_scoring_node)
    graph.add_node("report",               report_agent_node)

    # Pipeline edges
    graph.add_edge(START,                  "prepare")
    graph.add_edge("prepare",              "transcribe")
    graph.add_edge("transcribe",           "diarise")
    graph.add_edge("diarise",              "fraud_agent")
    graph.add_edge("fraud_agent",          "compliance_agent")
    graph.add_edge("compliance_agent",     "vulnerability_agent")
    graph.add_edge("vulnerability_agent",  "agent_behaviour")
    graph.add_edge("agent_behaviour",      "risk_scoring")
    graph.add_edge("risk_scoring",         "report")
    graph.add_edge("report",               END)

    return graph.compile()


# ── Public run functions ───────────────────────────────────────────────────────

def run_analysis(
    transcript: str = None,
    call_id: str = "",
    scenario_label: str = "",
    audio_path: str = None,
    diarised_transcript: list = None,
) -> CallAnalysisState:
    """
    Run full multi-agent analysis.
    Accepts either a text transcript OR an audio file path.
    """
    graph = build_graph()

    initial_state: CallAnalysisState = {
        "audio_path": audio_path,
        "call_id": call_id,
        "scenario_label": scenario_label,
        "raw_transcript": transcript,
        "whisper_segments": None,
        "diarised_transcript": diarised_transcript,
        "formatted_transcript": None,
        "fraud_findings": None,
        "compliance_findings": None,
        "vulnerability_findings": None,
        "agent_quality": None,
        "risk_score": None,
        "audit_report": None,
        "processing_status": "pending",
        "errors": [],
    }

    return graph.invoke(initial_state)
