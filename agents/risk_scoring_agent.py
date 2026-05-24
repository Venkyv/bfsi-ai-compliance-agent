"""
agents/risk_scoring_agent.py
LangGraph node — aggregates all agent findings into a composite RAG risk score.
Pure Python — no LLM call needed here, deterministic scoring logic.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas.state import CallAnalysisState
from schemas.findings import RiskScore, RAGStatus
from app.config import config


def risk_scoring_node(state: CallAnalysisState) -> dict:
    """
    LangGraph node: compute composite risk score from all agent outputs.
    Weighted formula:
        fraud      40%
        compliance 30%
        vulnerability 20%
        agent quality 10% (inverted — poor agent = higher risk)
    """
    errors = list(state.get("errors", []))

    fraud = state.get("fraud_findings")
    compliance = state.get("compliance_findings")
    vuln = state.get("vulnerability_findings")
    agent = state.get("agent_quality")

    # ── Individual scores ──────────────────────────────────────────────────────
    fraud_score = 0
    if fraud:
        fraud_score = int(fraud.confidence_score * 100) if fraud.fraud_detected else 0

    compliance_score = 0
    if compliance and compliance.violations_detected:
        # Scale by number and severity of findings
        severity_weights = {"HIGH": 40, "MEDIUM": 25, "LOW": 10}
        raw = sum(
            severity_weights.get(
                f.severity.value if hasattr(f.severity, "value") else f.severity, 10
            )
            for f in compliance.findings
        )
        compliance_score = min(raw, 100)

    vulnerability_score = 0
    if vuln:
        if vuln.escalation_required:
            vulnerability_score = 85
        elif vuln.vulnerable_customer_detected:
            vulnerability_score = 45

    agent_quality_contribution = 0
    if agent:
        # Poor agent conduct raises risk — invert the score
        agent_quality_contribution = max(0, 100 - agent.overall_score)

    # ── Composite weighted score ───────────────────────────────────────────────
    composite = int(
        fraud_score        * config.RISK_WEIGHT_FRAUD
        + compliance_score * config.RISK_WEIGHT_COMPLIANCE
        + vulnerability_score * config.RISK_WEIGHT_VULNERABILITY
        + agent_quality_contribution * config.RISK_WEIGHT_AGENT_QUALITY
    )
    composite = min(composite, 100)

    # ── RAG status ─────────────────────────────────────────────────────────────
    if composite >= config.RAG_RED_THRESHOLD:
        rag = RAGStatus.RED
    elif composite >= config.RAG_AMBER_THRESHOLD:
        rag = RAGStatus.AMBER
    else:
        rag = RAGStatus.GREEN

    # ── Priority flags ─────────────────────────────────────────────────────────
    flags = []
    if fraud and fraud.fraud_detected:
        flags.append(f"APP_FRAUD_SUSPECTED" if fraud.fraud_type and "APP" in str(fraud.fraud_type) else "FRAUD_DETECTED")
    if vuln and vuln.escalation_required:
        flags.append("VULNERABLE_CUSTOMER_ESCALATION")
    elif vuln and vuln.vulnerable_customer_detected:
        flags.append("VULNERABLE_CUSTOMER_DETECTED")
    if compliance and compliance.violations_detected:
        high_findings = [f for f in compliance.findings if (f.severity.value if hasattr(f.severity, "value") else f.severity) == "HIGH"]
        if high_findings:
            flags.append("HIGH_SEVERITY_COMPLIANCE_BREACH")
    if agent and agent.overall_score < 50:
        flags.append("AGENT_CONDUCT_REVIEW_REQUIRED")

    risk_score = RiskScore(
        composite_score=composite,
        rag_status=rag,
        fraud_score=fraud_score,
        compliance_score=compliance_score,
        vulnerability_score=vulnerability_score,
        agent_quality_score=agent.overall_score if agent else 0,
        priority_flags=flags,
        immediate_action_required=(rag == RAGStatus.RED),
    )

    return {
        "risk_score": risk_score,
        "processing_status": "scoring_complete",
        "errors": errors,
    }
