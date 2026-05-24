from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Category(str, Enum):
    FRAUD = "FRAUD"
    COMPLIANCE = "COMPLIANCE"
    VULNERABILITY = "VULNERABILITY"
    AGENT_QUALITY = "AGENT_QUALITY"


class Speaker(str, Enum):
    AGENT = "AGENT"
    CUSTOMER = "CUSTOMER"
    UNKNOWN = "UNKNOWN"


class RAGStatus(str, Enum):
    RED = "RED"
    AMBER = "AMBER"
    GREEN = "GREEN"


class FraudType(str, Enum):
    APP_FRAUD = "APP_FRAUD"
    ACCOUNT_COMPROMISE = "ACCOUNT_COMPROMISE"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    IDENTITY_FRAUD = "IDENTITY_FRAUD"


class VulnerabilityType(str, Enum):
    COGNITIVE = "COGNITIVE"
    FINANCIAL_STRESS = "FINANCIAL_STRESS"
    EMOTIONAL_DISTRESS = "EMOTIONAL_DISTRESS"
    CONSENT_UNCERTAINTY = "CONSENT_UNCERTAINTY"
    ELDERLY_AT_RISK = "ELDERLY_AT_RISK"


# ── Individual finding ────────────────────────────────────────────────────────

class Finding(BaseModel):
    finding_id: str = Field(description="Unique ID e.g. FRAUD-001, COMP-001")
    category: Category
    severity: Severity
    description: str = Field(description="Plain-English description of the finding")
    evidence_quote: str = Field(description="Exact quote from the transcript supporting this finding")
    speaker: Speaker = Field(description="Who said the flagged content")
    timestamp_approx: str = Field(description="Approximate position in call e.g. '02:15'")
    regulatory_reference: str = Field(description="e.g. 'FCA Consumer Duty — Outcome 4' or 'FCA FG21/1 Section 3.2'")
    recommended_action: str = Field(description="Concrete next step for compliance team")


# ── Agent output models ───────────────────────────────────────────────────────

class FraudFindings(BaseModel):
    fraud_detected: bool
    fraud_type: Optional[FraudType] = None
    confidence_score: float = Field(ge=0.0, le=1.0, description="0.0 = no confidence, 1.0 = certain")
    findings: list[Finding] = Field(default_factory=list)
    summary: str = Field(description="One-sentence summary of fraud assessment")


class ComplianceFindings(BaseModel):
    violations_detected: bool
    findings: list[Finding] = Field(default_factory=list)
    missing_disclosures: list[str] = Field(
        default_factory=list,
        description="List of disclosures that should have been made but weren't"
    )
    summary: str = Field(description="One-sentence summary of compliance assessment")


class VulnerabilityFindings(BaseModel):
    vulnerable_customer_detected: bool
    vulnerability_type: Optional[VulnerabilityType] = None
    findings: list[Finding] = Field(default_factory=list)
    escalation_required: bool = Field(description="True if case needs immediate human review")
    summary: str = Field(description="One-sentence summary of vulnerability assessment")


class AgentQualityScore(BaseModel):
    overall_score: int = Field(ge=0, le=100, description="Overall agent conduct score 0–100")
    professionalism: int = Field(ge=0, le=100)
    disclosure_compliance: int = Field(ge=0, le=100, description="Did agent deliver required disclosures?")
    empathy: int = Field(ge=0, le=100, description="Did agent respond appropriately to customer emotion?")
    escalation_adherence: int = Field(ge=0, le=100, description="Did agent follow escalation protocols?")
    findings: list[Finding] = Field(default_factory=list)
    notes: str = Field(description="Qualitative notes on agent performance")


# ── Risk scoring ──────────────────────────────────────────────────────────────

class RiskScore(BaseModel):
    composite_score: int = Field(ge=0, le=100, description="Overall risk score — higher = more risk")
    rag_status: RAGStatus = Field(description="RED ≥70, AMBER 40–69, GREEN <40")
    fraud_score: int = Field(ge=0, le=100)
    compliance_score: int = Field(ge=0, le=100)
    vulnerability_score: int = Field(ge=0, le=100)
    agent_quality_score: int = Field(ge=0, le=100, description="Inverted — high agent quality = low risk contribution")
    priority_flags: list[str] = Field(
        default_factory=list,
        description="Short flags for dashboard e.g. ['APP_FRAUD_SUSPECTED', 'VULNERABLE_CUSTOMER']"
    )
    immediate_action_required: bool


# ── Final audit report ────────────────────────────────────────────────────────

class AuditReport(BaseModel):
    call_id: str
    scenario_label: str = Field(description="Human-readable scenario name for demo e.g. 'APP Fraud — Urgent Transfer'")
    analysis_timestamp: str
    call_duration_approx: str = Field(description="e.g. '08:42'")
    risk_score: RiskScore
    fraud_findings: Optional[FraudFindings] = None
    compliance_findings: Optional[ComplianceFindings] = None
    vulnerability_findings: Optional[VulnerabilityFindings] = None
    agent_quality: Optional[AgentQualityScore] = None
    executive_summary: str = Field(description="2–3 sentence board-level narrative of the call risk")
    recommended_actions: list[str] = Field(description="Prioritised action list for compliance team")
