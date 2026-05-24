"""
agents/compliance_agent.py
LangGraph node — FCA compliance agent with RAG.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas.state import CallAnalysisState
from services.groq_service import analyse_compliance
from services.knowledge_base_service import get_compliance_context


def compliance_agent_node(state: CallAnalysisState) -> dict:
    """
    LangGraph node: analyse transcript for FCA compliance violations.
    Retrieves regulatory context from ChromaDB before calling LLM.
    Returns partial state update with compliance_findings.
    """
    transcript = state.get("formatted_transcript") or state.get("raw_transcript", "")

    try:
        kb_context = get_compliance_context(transcript)
        findings = analyse_compliance(transcript, kb_context)
        return {"compliance_findings": findings}
    except Exception as e:
        errors = list(state.get("errors", []))
        errors.append(f"ComplianceAgent error: {str(e)}")
        return {"compliance_findings": None, "errors": errors}
