"""
agents/fraud_agent.py
LangGraph node — fraud detection agent.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas.state import CallAnalysisState
from services.groq_service import analyse_fraud


def fraud_agent_node(state: CallAnalysisState) -> dict:
    """
    LangGraph node: analyse transcript for fraud indicators.
    Returns partial state update with fraud_findings.
    """
    transcript = state.get("formatted_transcript") or state.get("raw_transcript", "")

    try:
        findings = analyse_fraud(transcript)
        return {"fraud_findings": findings}
    except Exception as e:
        errors = list(state.get("errors", []))
        errors.append(f"FraudAgent error: {str(e)}")
        return {"fraud_findings": None, "errors": errors}
