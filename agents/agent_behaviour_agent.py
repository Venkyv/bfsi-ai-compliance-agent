"""
agents/agent_behaviour_agent.py
LangGraph node — bank agent conduct quality scoring.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas.state import CallAnalysisState
from services.groq_service import analyse_agent_quality


def agent_behaviour_node(state: CallAnalysisState) -> dict:
    """
    LangGraph node: score bank agent conduct against FCA standards.
    Returns partial state update with agent_quality.
    """
    transcript = state.get("formatted_transcript") or state.get("raw_transcript", "")

    try:
        score = analyse_agent_quality(transcript)
        return {"agent_quality": score}
    except Exception as e:
        errors = list(state.get("errors", []))
        errors.append(f"AgentBehaviourAgent error: {str(e)}")
        return {"agent_quality": None, "errors": errors}
