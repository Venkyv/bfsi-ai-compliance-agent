from typing import TypedDict, Optional
from schemas.findings import (
    FraudFindings,
    ComplianceFindings,
    VulnerabilityFindings,
    AgentQualityScore,
    RiskScore,
    AuditReport,
)


class CallAnalysisState(TypedDict):
    # ── Input ─────────────────────────────────────────────────────────────────
    audio_path: Optional[str]
    call_id: str
    scenario_label: str

    # ── Transcription ─────────────────────────────────────────────────────────
    raw_transcript: Optional[str]
    diarised_transcript: Optional[list[dict]]
    formatted_transcript: Optional[str]

    # ── Agent outputs ─────────────────────────────────────────────────────────
    fraud_findings: Optional[FraudFindings]
    compliance_findings: Optional[ComplianceFindings]
    vulnerability_findings: Optional[VulnerabilityFindings]
    agent_quality: Optional[AgentQualityScore]

    # ── Final outputs ─────────────────────────────────────────────────────────
    risk_score: Optional[RiskScore]
    audit_report: Optional[AuditReport]

    # ── Pipeline metadata ─────────────────────────────────────────────────────
    processing_status: str
    errors: list[str]
