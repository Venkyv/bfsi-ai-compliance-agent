"""
agents/report_agent.py
LangGraph node — generates the final AuditReport with LLM executive summary.
"""
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas.state import CallAnalysisState
from schemas.findings import AuditReport
from services.groq_service import _call_groq, _extract_json, _load_prompt, _build_prompt


def _build_executive_summary(state: CallAnalysisState) -> str:
    """Use LLM to generate a 2-3 sentence board-level executive summary."""
    fraud = state.get("fraud_findings")
    compliance = state.get("compliance_findings")
    vuln = state.get("vulnerability_findings")
    agent = state.get("agent_quality")
    risk = state.get("risk_score")

    summary_prompt = f"""You are a compliance officer writing a brief executive summary for a board-level risk report.

Based on the following analysis of a banking customer service call, write exactly 2-3 sentences summarising:
1. The primary risk identified
2. The regulatory implications
3. The recommended immediate action

Keep it professional, concise, and specific. Reference actual findings.

ANALYSIS SUMMARY:
- RAG Status: {risk.rag_status.value if risk else 'UNKNOWN'}
- Composite Risk Score: {risk.composite_score if risk else 'N/A'}/100
- Fraud Detected: {fraud.fraud_detected if fraud else False} ({fraud.fraud_type if fraud and fraud.fraud_detected else 'N/A'})
- Fraud Confidence: {f"{fraud.confidence_score:.0%}" if fraud and fraud.fraud_detected else 'N/A'}
- Compliance Violations: {len(compliance.findings) if compliance else 0} findings
- Vulnerable Customer: {vuln.vulnerable_customer_detected if vuln else False} (Escalation: {vuln.escalation_required if vuln else False})
- Agent Quality Score: {agent.overall_score if agent else 'N/A'}/100
- Priority Flags: {', '.join(risk.priority_flags) if risk and risk.priority_flags else 'None'}
- Key Compliance Issues: {'; '.join([f.description for f in compliance.findings[:2]]) if compliance and compliance.findings else 'None'}
- Key Fraud Signals: {'; '.join([f.description for f in fraud.findings[:2]]) if fraud and fraud.findings else 'None'}

Respond with ONLY the executive summary text. No JSON, no labels, no preamble."""

    try:
        return _call_groq(summary_prompt).strip().strip('"')
    except Exception:
        return f"Call analysis complete. RAG status: {risk.rag_status.value if risk else 'UNKNOWN'} with composite score {risk.composite_score if risk else 0}/100. Please review individual agent findings for detail."


def _build_recommended_actions(state: CallAnalysisState) -> list[str]:
    """Compile prioritised action list from all agent findings."""
    actions = []
    risk = state.get("risk_score")
    fraud = state.get("fraud_findings")
    vuln = state.get("vulnerability_findings")
    compliance = state.get("compliance_findings")
    agent = state.get("agent_quality")

    # Immediate actions first
    if risk and risk.immediate_action_required:
        actions.append("IMMEDIATE: Escalate call to fraud investigation team for same-day review")

    if vuln and vuln.escalation_required:
        actions.append("IMMEDIATE: Contact customer to confirm welfare and review any financial decisions made on this call")

    if fraud and fraud.fraud_detected:
        actions.append("URGENT: File Suspicious Activity Report (SAR) with the NCA if transfer was processed")
        actions.append("Review agent's handling of APP fraud signals and issue remediation training within 5 working days")

    if compliance and compliance.violations_detected:
        high = [f for f in compliance.findings if (f.severity.value if hasattr(f.severity, "value") else f.severity) == "HIGH"]
        if high:
            actions.append(f"Compliance breach review required: {high[0].description}")
        for disc in compliance.missing_disclosures[:2]:
            actions.append(f"Missing disclosure to address: {disc}")

    if agent and agent.overall_score < 50:
        actions.append(f"Agent conduct review: overall score {agent.overall_score}/100 — escalation_adherence score was {agent.escalation_adherence}/100")

    if not actions:
        actions.append("No immediate actions required — call meets compliance standards")

    return actions


def report_agent_node(state: CallAnalysisState) -> dict:
    """
    LangGraph node: generate the final AuditReport from all agent outputs.
    Calls LLM for executive summary, then assembles the full report.
    """
    errors = list(state.get("errors", []))

    try:
        executive_summary = _build_executive_summary(state)
        recommended_actions = _build_recommended_actions(state)

        # Estimate call duration from transcript length (rough heuristic)
        transcript = state.get("formatted_transcript") or state.get("raw_transcript", "")
        word_count = len(transcript.split())
        approx_seconds = int(word_count / 2.5)  # ~150 wpm
        duration = f"{approx_seconds // 60:02d}:{approx_seconds % 60:02d}"

        audit_report = AuditReport(
            call_id=state.get("call_id", "UNKNOWN"),
            scenario_label=state.get("scenario_label", ""),
            analysis_timestamp=datetime.now().isoformat(),
            call_duration_approx=duration,
            risk_score=state["risk_score"],
            fraud_findings=state["fraud_findings"],
            compliance_findings=state["compliance_findings"],
            vulnerability_findings=state["vulnerability_findings"],
            agent_quality=state["agent_quality"],
            executive_summary=executive_summary,
            recommended_actions=recommended_actions,
        )

        return {
            "audit_report": audit_report,
            "processing_status": "complete",
            "errors": errors,
        }

    except Exception as e:
        errors.append(f"ReportAgent error: {str(e)}")
        return {
            "audit_report": None,
            "processing_status": "error",
            "errors": errors,
        }
