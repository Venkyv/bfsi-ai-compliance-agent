"""
agents/orchestrator.py

LangGraph multi-agent graph for BFSI compliance analysis.

Graph flow:
    START
      ↓
    prepare_node
      ↓
    fraud_agent  →  compliance_agent  →  vulnerability_agent  →  agent_behaviour
      ↓  (sequential — avoids Groq TPM rate limit on free tier)
    risk_scoring_node
      ↓
    report_node
      ↓
    END

NOTE: Sequential ordering is intentional for Groq free tier (12,000 TPM limit).
To switch to true parallel execution on paid tier, replace the sequential edges
with fan-out/fan-in edges (see comments in build_graph).
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
    Entry node: validate input and format transcript for agents.
    Sprint 3 will extend this with whisper + diarisation nodes.
    """
    raw = state.get("raw_transcript", "")

    if not raw:
        return {
            "processing_status": "error",
            "errors": ["No transcript provided — raw_transcript is empty"],
        }

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
        "errors": state.get("errors", []),
    }


# ── Graph builder ──────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph multi-agent graph.
    Agents run sequentially to respect Groq free-tier TPM limits.
    """
    graph = StateGraph(CallAnalysisState)

    # Register nodes
    graph.add_node("prepare",              prepare_node)
    graph.add_node("fraud_agent",          fraud_agent_node)
    graph.add_node("compliance_agent",     compliance_agent_node)
    graph.add_node("vulnerability_agent",  vulnerability_agent_node)
    graph.add_node("agent_behaviour",      agent_behaviour_node)
    graph.add_node("risk_scoring",         risk_scoring_node)
    graph.add_node("report",               report_agent_node)

    # Sequential pipeline
    graph.add_edge(START,                "prepare")
    graph.add_edge("prepare",            "fraud_agent")
    graph.add_edge("fraud_agent",        "compliance_agent")
    graph.add_edge("compliance_agent",   "vulnerability_agent")
    graph.add_edge("vulnerability_agent","agent_behaviour")
    graph.add_edge("agent_behaviour",    "risk_scoring")
    graph.add_edge("risk_scoring",       "report")
    graph.add_edge("report",             END)

    # ── To enable true parallel execution on paid tier, replace the above
    # sequential agent edges with:
    #   graph.add_edge("prepare",            "fraud_agent")
    #   graph.add_edge("prepare",            "compliance_agent")
    #   graph.add_edge("prepare",            "vulnerability_agent")
    #   graph.add_edge("prepare",            "agent_behaviour")
    #   graph.add_edge("fraud_agent",        "risk_scoring")
    #   graph.add_edge("compliance_agent",   "risk_scoring")
    #   graph.add_edge("vulnerability_agent","risk_scoring")
    #   graph.add_edge("agent_behaviour",    "risk_scoring")

    return graph.compile()


# ── Public run function ────────────────────────────────────────────────────────

def run_analysis(
    transcript: str,
    call_id: str,
    scenario_label: str = "",
    audio_path: str = None,
    diarised_transcript: list = None,
) -> CallAnalysisState:
    """
    Run the full multi-agent analysis pipeline on a transcript.
    """
    graph = build_graph()

    initial_state: CallAnalysisState = {
        "audio_path": audio_path,
        "call_id": call_id,
        "scenario_label": scenario_label,
        "raw_transcript": transcript,
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

    final_state = graph.invoke(initial_state)
    return final_state
