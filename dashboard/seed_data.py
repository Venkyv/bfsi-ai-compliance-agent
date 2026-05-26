"""
dashboard/seed_data.py

Creates seed AuditReport JSON files for the dashboard
based on known Sprint 2 results. Run this once to populate
data/outputs/ for dashboard development without needing LLM calls.

Usage:
    python dashboard/seed_data.py
"""

import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

SEED_REPORTS = [
    {
        "filename": "scenario_01_app_fraud_result.json",
        "data": {
            "call_id": "CALL-001",
            "scenario_label": "APP Fraud — Urgent Safe Account Transfer",
            "processing_status": "complete",
            "errors": [],
            "risk_score": {
                "composite_score": 83,
                "rag_status": "RED",
                "fraud_score": 95,
                "compliance_score": 75,
                "vulnerability_score": 85,
                "agent_quality_score": 40,
                "priority_flags": ["APP_FRAUD_SUSPECTED","VULNERABLE_CUSTOMER_ESCALATION","HIGH_SEVERITY_COMPLIANCE_BREACH","AGENT_CONDUCT_REVIEW_REQUIRED"],
                "immediate_action_required": True
            },
            "fraud_findings": {
                "fraud_detected": True,
                "fraud_type": "APP_FRAUD",
                "confidence_score": 0.95,
                "findings": [
                    {"finding_id":"FRAUD-001","category":"FRAUD","severity":"HIGH","description":"Customer received unsolicited call instructing transfer to safe account","evidence_quote":"They said my account has been compromised and that I need to move all my money to a safe account they've set up for me","speaker":"CUSTOMER","timestamp_approx":"00:30","regulatory_reference":"PSR APP Fraud Mandatory Reimbursement / FCA Consumer Duty Outcome 4","recommended_action":"Immediately flag account for potential APP fraud and review recent transactions"},
                    {"finding_id":"FRAUD-002","category":"FRAUD","severity":"HIGH","description":"Artificial urgency applied — customer told to act within one hour","evidence_quote":"They said if I didn't do it within the next hour my account would be completely drained by fraudsters","speaker":"CUSTOMER","timestamp_approx":"02:00","regulatory_reference":"PSR APP Fraud Mandatory Reimbursement / FCA Consumer Duty Outcome 4","recommended_action":"Review account activity for suspicious transactions"},
                    {"finding_id":"FRAUD-003","category":"AGENT_QUALITY","severity":"MEDIUM","description":"Agent failed to issue APP fraud warnings and offered to process suspicious transfer","evidence_quote":"It's your money Mr Collins, it's your decision. Would you like to go ahead?","speaker":"AGENT","timestamp_approx":"06:30","regulatory_reference":"FCA Consumer Duty Outcome 4","recommended_action":"Provide APP fraud detection training to agent"}
                ],
                "summary": "High risk of APP fraud detected — customer targeted via safe account scam with artificial urgency."
            },
            "compliance_findings": {
                "violations_detected": True,
                "findings": [
                    {"finding_id":"COMP-001","category":"COMPLIANCE","severity":"HIGH","description":"Failure to disclose risks and challenge pressure tactics","evidence_quote":"They said if I didn't do it within the next hour my account would be completely drained","speaker":"CUSTOMER","timestamp_approx":"02:45","regulatory_reference":"FCA Consumer Duty Outcome 3 — Risk disclosure requirement","recommended_action":"Provide clear risk disclosure and avoid pressure tactics"},
                    {"finding_id":"COMP-002","category":"COMPLIANCE","severity":"MEDIUM","description":"Agent offered to process suspicious transfer without challenge","evidence_quote":"The transfer itself I can process right now if you confirm.","speaker":"AGENT","timestamp_approx":"07:10","regulatory_reference":"FCA SYSC 9 / UK GDPR","recommended_action":"Challenge suspicious transfer requests before processing"},
                    {"finding_id":"COMP-003","category":"COMPLIANCE","severity":"LOW","description":"Failure to provide clear guidance on next steps","evidence_quote":"Is there anything else I can help with?","speaker":"AGENT","timestamp_approx":"08:50","regulatory_reference":"FCA Consumer Duty Outcome 4 — Consumer Support","recommended_action":"Provide clear guidance on fraud reporting procedures"}
                ],
                "missing_disclosures": ["Risks associated with transferring funds to a new account","Cooling-off and cancellation rights","Complaint handling procedures"],
                "summary": "Multiple compliance violations including failure to challenge APP fraud indicators."
            },
            "vulnerability_findings": {
                "vulnerable_customer_detected": True,
                "vulnerability_type": "CONSENT_UNCERTAINTY",
                "findings": [
                    {"finding_id":"VULN-001","category":"VULNERABILITY","severity":"HIGH","description":"Customer uses uncertain language as consent — 'I suppose if you say it's okay'","evidence_quote":"I suppose if you say it's okay","speaker":"CUSTOMER","timestamp_approx":"07:30","regulatory_reference":"FCA FG21/1 Section 3.2 — Consent requirements for vulnerable customers","recommended_action":"Agent should pause and check understanding before proceeding"},
                    {"finding_id":"VULN-002","category":"VULNERABILITY","severity":"MEDIUM","description":"Elderly customer expresses fear with £62k savings at risk","evidence_quote":"I'm quite scared, I have everything in that account","speaker":"CUSTOMER","timestamp_approx":"05:40","regulatory_reference":"FCA FG21/1 Section 3.2 — Consent requirements for vulnerable customers","recommended_action":"Offer reassurance and escalate to specialist team"}
                ],
                "escalation_required": True,
                "summary": "Vulnerable customer detected — elderly, fearful, consent uncertainty present."
            },
            "agent_quality": {
                "overall_score": 40,
                "professionalism": 80,
                "disclosure_compliance": 20,
                "empathy": 60,
                "escalation_adherence": 0,
                "findings": [
                    {"finding_id":"AQ-001","category":"AGENT_QUALITY","severity":"HIGH","description":"Failed to issue APP fraud warnings","evidence_quote":"I can proceed with that transfer if you'd like. You'll just need to confirm the amount.","speaker":"AGENT","timestamp_approx":"05:30","regulatory_reference":"FCA Consumer Duty Outcome 4 — Consumer Support","recommended_action":"Provide APP fraud training"},
                    {"finding_id":"AQ-002","category":"AGENT_QUALITY","severity":"HIGH","description":"Did not escalate to fraud team","evidence_quote":"The transfer itself I can process right now if you confirm.","speaker":"AGENT","timestamp_approx":"07:00","regulatory_reference":"FCA Consumer Duty Outcome 4 — Consumer Support","recommended_action":"Escalation protocol training required"}
                ],
                "notes": "Agent demonstrated good professionalism but critically failed on fraud detection and escalation."
            },
            "audit_report": {
                "call_id": "CALL-001",
                "scenario_label": "APP Fraud — Urgent Safe Account Transfer",
                "analysis_timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "call_duration_approx": "09:14",
                "executive_summary": "The primary risk identified is a high-severity fraud incident with 95% confidence, involving a vulnerable elderly customer targeted by an APP fraud safe account scam. The agent critically failed to issue fraud warnings or escalate to the fraud team despite clear indicators. Immediate action required to contact the customer, review account activity, and initiate fraud investigation.",
                "recommended_actions": [
                    "IMMEDIATE: Escalate call to fraud investigation team for same-day review",
                    "IMMEDIATE: Contact customer to confirm welfare and review financial decisions",
                    "URGENT: File SAR with the NCA if transfer was processed",
                    "Review agent APP fraud handling and issue remediation training within 5 working days",
                    "Agent conduct review: overall score 40/100 — escalation_adherence score was 0/100"
                ]
            }
        }
    },
    {
        "filename": "scenario_02_misselling_investment_result.json",
        "data": {
            "call_id": "CALL-002",
            "scenario_label": "Mis-selling — Investment Product",
            "processing_status": "complete",
            "errors": [],
            "risk_score": {
                "composite_score": 46,
                "rag_status": "AMBER",
                "fraud_score": 0,
                "compliance_score": 75,
                "vulnerability_score": 85,
                "agent_quality_score": 32,
                "priority_flags": ["VULNERABLE_CUSTOMER_ESCALATION","HIGH_SEVERITY_COMPLIANCE_BREACH","AGENT_CONDUCT_REVIEW_REQUIRED"],
                "immediate_action_required": False
            },
            "fraud_findings": {
                "fraud_detected": False, "fraud_type": None, "confidence_score": 0.0,
                "findings": [],
                "summary": "No fraud indicators detected."
            },
            "compliance_findings": {
                "violations_detected": True,
                "findings": [
                    {"finding_id":"COMP-001","category":"COMPLIANCE","severity":"HIGH","description":"Investment product described as risk-free — FCA Consumer Duty Outcome 3 breach","evidence_quote":"It's basically risk-free for someone in your position.","speaker":"AGENT","timestamp_approx":"04:20","regulatory_reference":"FCA Consumer Duty Outcome 3 — Risk disclosure requirement","recommended_action":"Immediate retraining on accurate risk disclosure"},
                    {"finding_id":"COMP-002","category":"COMPLIANCE","severity":"MEDIUM","description":"Cooling-off period not clearly explained","evidence_quote":"There's a standard process for any changes you want to make after signing up.","speaker":"AGENT","timestamp_approx":"08:10","regulatory_reference":"FCA TCF — Cooling-off periods","recommended_action":"Update agent scripts with clear cooling-off period explanation"}
                ],
                "missing_disclosures": ["Clear explanation of investment risks","Detailed cooling-off period information","Prominent fee disclosure"],
                "summary": "Agent described investment as risk-free — direct FCA Consumer Duty breach."
            },
            "vulnerability_findings": {
                "vulnerable_customer_detected": True, "vulnerability_type": "FINANCIAL_STRESS",
                "findings": [
                    {"finding_id":"VULN-001","category":"VULNERABILITY","severity":"HIGH","description":"Customer states they cannot afford to lose the money — retirement savings","evidence_quote":"I'm 61 so I can't really afford to lose this money — it's part of my retirement pot","speaker":"CUSTOMER","timestamp_approx":"03:15","regulatory_reference":"FCA FG21/1 Section 3.2","recommended_action":"Agent should have paused and provided balanced risk information"}
                ],
                "escalation_required": True,
                "summary": "Vulnerable customer — financial stress, retirement savings at risk from mis-sold product."
            },
            "agent_quality": {
                "overall_score": 32, "professionalism": 80, "disclosure_compliance": 20, "empathy": 60, "escalation_adherence": 0,
                "findings": [
                    {"finding_id":"AQ-001","category":"AGENT_QUALITY","severity":"HIGH","description":"Described investment as risk-free without basis","evidence_quote":"It's basically risk-free for someone in your position.","speaker":"AGENT","timestamp_approx":"04:20","regulatory_reference":"FCA Consumer Duty Outcome 3","recommended_action":"Immediate retraining on product risk disclosure"}
                ],
                "notes": "Agent failed to provide accurate risk disclosures — significant conduct risk."
            },
            "audit_report": {
                "call_id": "CALL-002", "scenario_label": "Mis-selling — Investment Product",
                "analysis_timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
                "call_duration_approx": "11:38",
                "executive_summary": "A high-severity compliance breach was identified where the agent described an investment product as 'risk-free' to a 61-year-old customer investing retirement savings. This directly breaches FCA Consumer Duty Outcome 3 and creates significant mis-selling liability. Immediate review of the sale and customer contact is required.",
                "recommended_actions": [
                    "IMMEDIATE: Contact customer to confirm welfare and review investment decision",
                    "Compliance breach review: Agent described product as risk-free",
                    "Missing disclosure: Clear explanation of investment risks",
                    "Agent conduct review: overall score 32/100"
                ]
            }
        }
    },
    {
        "filename": "scenario_03_vulnerable_elderly_result.json",
        "data": {
            "call_id": "CALL-003",
            "scenario_label": "Vulnerable Customer — Elderly, Consent Uncertainty",
            "processing_status": "complete",
            "errors": [],
            "risk_score": {
                "composite_score": 45,
                "rag_status": "AMBER",
                "fraud_score": 0,
                "compliance_score": 75,
                "vulnerability_score": 85,
                "agent_quality_score": 42,
                "priority_flags": ["VULNERABLE_CUSTOMER_ESCALATION","HIGH_SEVERITY_COMPLIANCE_BREACH","AGENT_CONDUCT_REVIEW_REQUIRED"],
                "immediate_action_required": False
            },
            "fraud_findings": {
                "fraud_detected": False, "fraud_type": None, "confidence_score": 0.0,
                "findings": [], "summary": "No fraud indicators detected."
            },
            "compliance_findings": {
                "violations_detected": True,
                "findings": [
                    {"finding_id":"COMP-001","category":"COMPLIANCE","severity":"HIGH","description":"Pressure tactics used — customer told decision required same day","evidence_quote":"We do need a decision today if you want to keep the old rate.","speaker":"AGENT","timestamp_approx":"10:20","regulatory_reference":"FCA Consumer Duty Outcome 4 — Consumer Support","recommended_action":"Avoid artificial urgency with vulnerable customers"},
                    {"finding_id":"COMP-002","category":"COMPLIANCE","severity":"MEDIUM","description":"Product terms not clearly explained to confused customer","evidence_quote":"The Flexi-Saver Bond locks your money away for 18 months in exchange for a higher rate.","speaker":"AGENT","timestamp_approx":"05:30","regulatory_reference":"FCA Consumer Duty Outcome 3","recommended_action":"Simplify product explanations for vulnerable customers"}
                ],
                "missing_disclosures": ["Clear explanation of Flexi-Saver Bond terms","Penalty information","Right to cancel"],
                "summary": "Pressure tactics used with a confused elderly customer — FCA Consumer Duty breach."
            },
            "vulnerability_findings": {
                "vulnerable_customer_detected": True, "vulnerability_type": "ELDERLY_AT_RISK",
                "findings": [
                    {"finding_id":"VULN-001","category":"VULNERABILITY","severity":"HIGH","description":"79-year-old customer confused, states she finds financial matters confusing","evidence_quote":"I'm 79 and I do find these things quite confusing I'm afraid","speaker":"CUSTOMER","timestamp_approx":"01:45","regulatory_reference":"FCA FG21/1 Section 3.2","recommended_action":"Agent should pause and offer time to consult family"},
                    {"finding_id":"VULN-002","category":"VULNERABILITY","severity":"HIGH","description":"Customer defers entirely to agent — invalid consent","evidence_quote":"I suppose just do whatever you think is best. I trust you","speaker":"CUSTOMER","timestamp_approx":"11:30","regulatory_reference":"FCA FG21/1 Section 3.2 — Consent requirements","recommended_action":"Do not proceed on basis of deferred consent — seek explicit confirmation"}
                ],
                "escalation_required": True,
                "summary": "Highly vulnerable elderly customer — bereaved, confused, deferred consent used as basis for product commitment."
            },
            "agent_quality": {
                "overall_score": 42, "professionalism": 80, "disclosure_compliance": 40, "empathy": 60, "escalation_adherence": 20,
                "findings": [
                    {"finding_id":"AQ-001","category":"AGENT_QUALITY","severity":"HIGH","description":"Proceeded with product commitment on basis of 'I suppose so'","evidence_quote":"I'll note that as a yes then and process accordingly.","speaker":"AGENT","timestamp_approx":"12:10","regulatory_reference":"FCA Consumer Duty Outcome 4","recommended_action":"Training on vulnerable customer consent requirements"}
                ],
                "notes": "Agent failed to recognise and appropriately respond to clear vulnerability signals."
            },
            "audit_report": {
                "call_id": "CALL-003", "scenario_label": "Vulnerable Customer — Elderly, Consent Uncertainty",
                "analysis_timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
                "call_duration_approx": "14:22",
                "executive_summary": "A 79-year-old recently bereaved customer was committed to a financial product on the basis of 'I suppose so' — which does not constitute informed consent under FCA FG21/1. The agent applied time pressure and failed to recognise clear vulnerability signals. Immediate customer contact and product review required.",
                "recommended_actions": [
                    "IMMEDIATE: Contact customer to confirm welfare and review product commitment",
                    "Review validity of consent obtained during this call",
                    "Missing disclosure: Right to cancel and penalty information",
                    "Agent conduct review: overall score 42/100"
                ]
            }
        }
    },
    {
        "filename": "scenario_04_gdpr_breach_result.json",
        "data": {
            "call_id": "CALL-004",
            "scenario_label": "GDPR Breach — Unverified Data Disclosure",
            "processing_status": "complete",
            "errors": [],
            "risk_score": {
                "composite_score": 72,
                "rag_status": "RED",
                "fraud_score": 90,
                "compliance_score": 100,
                "vulnerability_score": 0,
                "agent_quality_score": 32,
                "priority_flags": ["FRAUD_DETECTED","HIGH_SEVERITY_COMPLIANCE_BREACH","AGENT_CONDUCT_REVIEW_REQUIRED"],
                "immediate_action_required": True
            },
            "fraud_findings": {
                "fraud_detected": True, "fraud_type": "ACCOUNT_COMPROMISE", "confidence_score": 0.90,
                "findings": [
                    {"finding_id":"FRAUD-001","category":"FRAUD","severity":"HIGH","description":"Full account details disclosed to unverified caller","evidence_quote":"Your sort code is 40-27-11, account number 31458823, and the balance as of this morning was four thousand, two hundred and sixty-seven pounds","speaker":"AGENT","timestamp_approx":"01:45","regulatory_reference":"FCA SYSC 9 / UK GDPR Article 32","recommended_action":"Review call recording and assess data breach notification obligations"}
                ],
                "summary": "Account compromise risk — full financial data disclosed without identity verification."
            },
            "compliance_findings": {
                "violations_detected": True,
                "findings": [
                    {"finding_id":"SYSC-001","category":"COMPLIANCE","severity":"HIGH","description":"Account details disclosed before identity verification","evidence_quote":"Your sort code is 40-27-11, account number 31458823","speaker":"AGENT","timestamp_approx":"01:45","regulatory_reference":"FCA SYSC 9 / UK GDPR","recommended_action":"Immediate retraining on identity verification protocols"},
                    {"finding_id":"SYSC-002","category":"COMPLIANCE","severity":"HIGH","description":"Confirming disclosed data treated as identity verification","evidence_quote":"You confirmed the account balance was correct.","speaker":"AGENT","timestamp_approx":"02:30","regulatory_reference":"FCA SYSC 9 / UK GDPR","recommended_action":"Update verification scripts"},
                    {"finding_id":"COMP-001","category":"COMPLIANCE","severity":"MEDIUM","description":"FOS rights not communicated during complaint","evidence_quote":"Our complaints team is available on the main number.","speaker":"AGENT","timestamp_approx":"06:20","regulatory_reference":"FCA Complaints Handling (DISP)","recommended_action":"Include FOS referral in complaint handling script"}
                ],
                "missing_disclosures": ["Identity verification questions","FOS referral rights"],
                "summary": "Serious GDPR and SYSC 9 breach — full customer data disclosed to unverified caller."
            },
            "vulnerability_findings": {
                "vulnerable_customer_detected": False, "vulnerability_type": None,
                "findings": [], "escalation_required": False,
                "summary": "No vulnerability signals detected."
            },
            "agent_quality": {
                "overall_score": 32, "professionalism": 60, "disclosure_compliance": 20, "empathy": 40, "escalation_adherence": 20,
                "findings": [
                    {"finding_id":"AQ-001","category":"AGENT_QUALITY","severity":"HIGH","description":"Failed to verify identity before disclosing sensitive data","evidence_quote":"Yes, I've got you here. Thomas Harding, is that the account ending 8823?","speaker":"AGENT","timestamp_approx":"00:45","regulatory_reference":"FCA SYSC 9 / UK GDPR","recommended_action":"Mandatory identity verification training"}
                ],
                "notes": "Serious protocol failure — full account data disclosed without any verification."
            },
            "audit_report": {
                "call_id": "CALL-004", "scenario_label": "GDPR Breach — Unverified Data Disclosure",
                "analysis_timestamp": (datetime.now() - timedelta(hours=8)).isoformat(),
                "call_duration_approx": "06:55",
                "executive_summary": "A serious GDPR and SYSC 9 breach occurred — the agent disclosed full account details including sort code, account number, balance, address and phone number to an unverified caller. This constitutes a potential personal data breach requiring ICO notification assessment within 72 hours. Immediate investigation required.",
                "recommended_actions": [
                    "IMMEDIATE: Assess data breach notification obligations under UK GDPR Article 33",
                    "URGENT: Review whether ICO notification required within 72 hours",
                    "Mandatory identity verification retraining for agent",
                    "Missing disclosure: FOS referral rights",
                    "Agent conduct review: overall score 32/100"
                ]
            }
        }
    },
    {
        "filename": "scenario_05_clean_call_result.json",
        "data": {
            "call_id": "CALL-005",
            "scenario_label": "Clean Call — Compliant Agent Conduct",
            "processing_status": "complete",
            "errors": [],
            "risk_score": {
                "composite_score": 0,
                "rag_status": "GREEN",
                "fraud_score": 0,
                "compliance_score": 0,
                "vulnerability_score": 0,
                "agent_quality_score": 98,
                "priority_flags": [],
                "immediate_action_required": False
            },
            "fraud_findings": {
                "fraud_detected": False, "fraud_type": None, "confidence_score": 0.0,
                "findings": [], "summary": "No fraud indicators detected."
            },
            "compliance_findings": {
                "violations_detected": False, "findings": [],
                "missing_disclosures": [],
                "summary": "Full compliance with FCA regulatory requirements — identity verified, FOS rights communicated, complaint handled correctly."
            },
            "vulnerability_findings": {
                "vulnerable_customer_detected": False, "vulnerability_type": None,
                "findings": [], "escalation_required": False,
                "summary": "No vulnerability signals detected."
            },
            "agent_quality": {
                "overall_score": 98, "professionalism": 100, "disclosure_compliance": 100, "empathy": 100, "escalation_adherence": 95,
                "findings": [
                    {"finding_id":"AQ-001","category":"AGENT_QUALITY","severity":"LOW","description":"Exemplary identity verification before account access","evidence_quote":"Before I access your account, I'll need to go through our standard security check.","speaker":"AGENT","timestamp_approx":"00:30","regulatory_reference":"FCA SYSC 9","recommended_action":"Use as training example for correct verification procedure"},
                    {"finding_id":"AQ-002","category":"AGENT_QUALITY","severity":"LOW","description":"FOS rights proactively communicated","evidence_quote":"you have the right to refer the matter to the Financial Ombudsman Service free of charge","speaker":"AGENT","timestamp_approx":"05:20","regulatory_reference":"FCA Complaints Handling (DISP)","recommended_action":"Use as best practice example"}
                ],
                "notes": "Exemplary conduct throughout — correct verification, FOS disclosure, empathetic complaint handling, proactive goodwill gesture."
            },
            "audit_report": {
                "call_id": "CALL-005", "scenario_label": "Clean Call — Compliant Agent Conduct",
                "analysis_timestamp": (datetime.now() - timedelta(hours=10)).isoformat(),
                "call_duration_approx": "08:17",
                "executive_summary": "This call demonstrates exemplary compliance standards. The agent correctly verified identity, proactively disclosed FOS referral rights, handled the complaint empathetically, and offered a goodwill refund. No regulatory concerns identified. Recommend using as a training example.",
                "recommended_actions": ["No immediate actions required — call meets all compliance standards"]
            }
        }
    }
]


def create_seed_data():
    count = 0
    for report in SEED_REPORTS:
        filepath = os.path.join(OUTPUTS_DIR, report["filename"])
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report["data"], f, indent=2)
        print(f"✓ Created: {report['filename']}")
        count += 1
    print(f"\nSeed data ready — {count} reports in {OUTPUTS_DIR}")
    print("Now run: python dashboard/app.py")


if __name__ == "__main__":
    create_seed_data()
