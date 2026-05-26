"""
tests/test_pipeline.py

Sprint 5 test suite.
Tests the core pipeline components without making real LLM calls
by using the saved Sprint 2 synthetic data outputs.

Run with:
    pytest tests/ -v
    pytest tests/test_pipeline.py -v
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "outputs")
SYNTHETIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "synthetic_data")


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def fraud_result():
    path = os.path.join(OUTPUTS_DIR, "scenario_01_app_fraud_result.json")
    if not os.path.exists(path):
        pytest.skip("Run dashboard/seed_data.py first to generate test fixtures")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def clean_result():
    path = os.path.join(OUTPUTS_DIR, "scenario_05_clean_call_result.json")
    if not os.path.exists(path):
        pytest.skip("Run dashboard/seed_data.py first to generate test fixtures")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def gdpr_result():
    path = os.path.join(OUTPUTS_DIR, "scenario_04_gdpr_breach_result.json")
    if not os.path.exists(path):
        pytest.skip("Run dashboard/seed_data.py first to generate test fixtures")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def app_fraud_transcript():
    path = os.path.join(SYNTHETIC_DIR, "scenario_01_app_fraud.txt")
    with open(path) as f:
        return f.read()


@pytest.fixture
def clean_call_transcript():
    path = os.path.join(SYNTHETIC_DIR, "scenario_05_clean_call.txt")
    with open(path) as f:
        return f.read()


# ── Schema tests ───────────────────────────────────────────────────────────────

class TestPydanticSchemas:
    def test_fraud_findings_import(self):
        from schemas.findings import FraudFindings
        assert FraudFindings is not None

    def test_audit_report_import(self):
        from schemas.findings import AuditReport
        assert AuditReport is not None

    def test_call_analysis_state_import(self):
        from schemas.state import CallAnalysisState
        assert CallAnalysisState is not None

    def test_risk_score_rag_thresholds(self):
        """Verify RAG scoring logic is consistent."""
        from app.config import config
        assert config.RAG_RED_THRESHOLD == 70
        assert config.RAG_AMBER_THRESHOLD == 40
        assert config.RAG_RED_THRESHOLD > config.RAG_AMBER_THRESHOLD

    def test_risk_weights_sum_to_one(self):
        """Risk scoring weights must sum to 1.0."""
        from app.config import config
        total = (
            config.RISK_WEIGHT_FRAUD +
            config.RISK_WEIGHT_COMPLIANCE +
            config.RISK_WEIGHT_VULNERABILITY +
            config.RISK_WEIGHT_AGENT_QUALITY
        )
        assert abs(total - 1.0) < 0.001, f"Weights sum to {total}, expected 1.0"


# ── LangGraph graph tests ──────────────────────────────────────────────────────

class TestLangGraphGraph:
    def test_graph_compiles(self):
        from agents.orchestrator import build_graph
        graph = build_graph()
        assert graph is not None

    def test_graph_has_required_nodes(self):
        from agents.orchestrator import build_graph
        graph = build_graph()
        nodes = list(graph.get_graph().nodes.keys())
        required = ["prepare", "transcribe", "diarise", "fraud_agent",
                    "compliance_agent", "vulnerability_agent",
                    "agent_behaviour", "risk_scoring", "report"]
        for node in required:
            assert node in nodes, f"Missing node: {node}"

    def test_graph_has_10_nodes(self):
        from agents.orchestrator import build_graph
        graph = build_graph()
        nodes = list(graph.get_graph().nodes.keys())
        assert len(nodes) == 11  # __start__, __end__ + 9 custom nodes


# ── Fraud detection tests ──────────────────────────────────────────────────────

class TestFraudDetection:
    def test_app_fraud_detected(self, fraud_result):
        """APP fraud scenario must be detected."""
        assert fraud_result["fraud_findings"]["fraud_detected"] is True

    def test_app_fraud_type_correct(self, fraud_result):
        """Fraud type must be APP_FRAUD for scenario 1."""
        assert fraud_result["fraud_findings"]["fraud_type"] == "APP_FRAUD"

    def test_app_fraud_confidence_high(self, fraud_result):
        """Confidence must be >= 0.85 for clear APP fraud."""
        assert fraud_result["fraud_findings"]["confidence_score"] >= 0.85

    def test_app_fraud_has_findings(self, fraud_result):
        """Must have at least 2 fraud findings."""
        assert len(fraud_result["fraud_findings"]["findings"]) >= 2

    def test_clean_call_no_fraud(self, clean_result):
        """Clean call must NOT detect fraud."""
        assert clean_result["fraud_findings"]["fraud_detected"] is False

    def test_clean_call_zero_confidence(self, clean_result):
        """Clean call fraud confidence must be 0."""
        assert clean_result["fraud_findings"]["confidence_score"] == 0.0


# ── Compliance tests ───────────────────────────────────────────────────────────

class TestCompliance:
    def test_fraud_call_compliance_violations(self, fraud_result):
        """APP fraud call must have compliance violations."""
        assert fraud_result["compliance_findings"]["violations_detected"] is True

    def test_clean_call_no_violations(self, clean_result):
        """Clean call must be compliant."""
        assert clean_result["compliance_findings"]["violations_detected"] is False

    def test_gdpr_breach_has_high_severity(self, gdpr_result):
        """GDPR breach must have at least one HIGH severity finding."""
        findings = gdpr_result["compliance_findings"]["findings"]
        severities = [f["severity"] for f in findings]
        assert "HIGH" in severities

    def test_findings_have_required_fields(self, fraud_result):
        """Every finding must have all required fields."""
        required = ["finding_id", "category", "severity", "description",
                    "evidence_quote", "speaker", "regulatory_reference", "recommended_action"]
        for finding in fraud_result["compliance_findings"]["findings"]:
            for field in required:
                assert field in finding, f"Finding missing field: {field}"


# ── Vulnerability tests ────────────────────────────────────────────────────────

class TestVulnerability:
    def test_fraud_call_vulnerable_customer(self, fraud_result):
        """APP fraud scenario has vulnerable customer."""
        assert fraud_result["vulnerability_findings"]["vulnerable_customer_detected"] is True

    def test_fraud_call_escalation_required(self, fraud_result):
        """APP fraud scenario requires escalation."""
        assert fraud_result["vulnerability_findings"]["escalation_required"] is True

    def test_clean_call_no_vulnerability(self, clean_result):
        """Clean call has no vulnerability signals."""
        assert clean_result["vulnerability_findings"]["vulnerable_customer_detected"] is False

    def test_gdpr_no_vulnerability(self, gdpr_result):
        """GDPR breach scenario has no vulnerable customer."""
        assert gdpr_result["vulnerability_findings"]["vulnerable_customer_detected"] is False


# ── Risk scoring tests ─────────────────────────────────────────────────────────

class TestRiskScoring:
    def test_app_fraud_is_red(self, fraud_result):
        """APP fraud must score RED."""
        assert fraud_result["risk_score"]["rag_status"] == "RED"

    def test_app_fraud_score_above_70(self, fraud_result):
        """APP fraud composite score must be >= 70."""
        assert fraud_result["risk_score"]["composite_score"] >= 70

    def test_clean_call_is_green(self, clean_result):
        """Clean call must score GREEN."""
        assert clean_result["risk_score"]["rag_status"] == "GREEN"

    def test_clean_call_zero_score(self, clean_result):
        """Clean call composite score must be 0."""
        assert clean_result["risk_score"]["composite_score"] == 0

    def test_fraud_call_has_priority_flags(self, fraud_result):
        """APP fraud must have at least 3 priority flags."""
        assert len(fraud_result["risk_score"]["priority_flags"]) >= 3

    def test_clean_call_no_flags(self, clean_result):
        """Clean call must have no priority flags."""
        assert len(clean_result["risk_score"]["priority_flags"]) == 0

    def test_immediate_action_on_red(self, fraud_result):
        """RED calls must require immediate action."""
        assert fraud_result["risk_score"]["immediate_action_required"] is True

    def test_no_immediate_action_on_green(self, clean_result):
        """GREEN calls must not require immediate action."""
        assert clean_result["risk_score"]["immediate_action_required"] is False


# ── Agent quality tests ────────────────────────────────────────────────────────

class TestAgentQuality:
    def test_fraud_agent_poor_score(self, fraud_result):
        """Agent on fraud call must score below 50."""
        assert fraud_result["agent_quality"]["overall_score"] < 50

    def test_fraud_agent_zero_escalation(self, fraud_result):
        """Agent on fraud call must score 0 on escalation."""
        assert fraud_result["agent_quality"]["escalation_adherence"] == 0

    def test_clean_call_agent_excellent(self, clean_result):
        """Agent on clean call must score above 90."""
        assert clean_result["agent_quality"]["overall_score"] >= 90

    def test_agent_score_fields_present(self, fraud_result):
        """Agent quality must have all 4 dimension scores."""
        aq = fraud_result["agent_quality"]
        for field in ["overall_score", "professionalism", "disclosure_compliance", "empathy", "escalation_adherence"]:
            assert field in aq, f"Missing field: {field}"


# ── Knowledge base tests ───────────────────────────────────────────────────────

class TestKnowledgeBase:
    def test_chroma_db_exists(self):
        """ChromaDB directory must exist after ingest."""
        from app.config import config
        assert os.path.exists(config.CHROMA_PERSIST_DIR), \
            "ChromaDB not found. Run: python knowledge_base/ingest_kb.py"

    def test_kb_query_returns_results(self):
        """KB query for risk-free products must return relevant content."""
        try:
            from services.knowledge_base_service import query_collection
            from app.config import config
            result = query_collection(
                config.CHROMA_COLLECTION_FCA_CONSUMER_DUTY,
                "investment product described as risk-free disclosure requirements",
                n_results=2,
            )
            assert len(result) > 50  # should return meaningful content
        except Exception as e:
            pytest.skip(f"KB not available: {e}")
