"""
run.py

Sprint 2 entry point.
Runs the full LangGraph multi-agent pipeline on a transcript file.

Usage:
    python run.py --transcript synthetic_data/scenario_01_app_fraud.txt
    python run.py --transcript synthetic_data/scenario_01_app_fraud.txt --call-id CALL-001
    python run.py --all   # run all 5 synthetic scenarios
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import config
from agents.orchestrator import run_analysis


# ── Colour helpers ─────────────────────────────────────────────────────────────

def _c(text, code):
    codes = {"red": "31", "green": "32", "yellow": "33", "cyan": "36", "bold": "1"}
    return f"\033[{codes.get(code, '0')}m{text}\033[0m"

def _rag(status):
    s = status.value if hasattr(status, "value") else status
    if s == "RED":    return _c("🔴  RED   — IMMEDIATE ACTION REQUIRED", "red")
    if s == "AMBER":  return _c("🟡  AMBER — REVIEW REQUIRED", "yellow")
    return _c("🟢  GREEN — NO ACTION REQUIRED", "green")

def _sev(s):
    sv = s.value if hasattr(s, "value") else s
    if sv == "HIGH":   return _c("HIGH", "red")
    if sv == "MEDIUM": return _c("MEDIUM", "yellow")
    return _c("LOW", "green")


# ── Print helpers ──────────────────────────────────────────────────────────────

def _section(title):
    print(f"\n{_c('─' * 62, 'cyan')}")
    print(f"  {_c(title, 'bold')}")
    print(_c('─' * 62, 'cyan'))

def _print_findings(findings):
    if not findings:
        print(f"    {_c('✓ No findings', 'green')}")
        return
    for f in findings:
        print(f"\n    [{_sev(f.severity)}] {f.finding_id}")
        print(f"    {f.description}")
        print(f"    {_c('Quote', 'cyan')}  : \"{f.evidence_quote}\"")
        print(f"    {_c('Speaker', 'cyan')}: {f.speaker.value if hasattr(f.speaker, 'value') else f.speaker}")
        print(f"    {_c('Rule', 'cyan')}   : {f.regulatory_reference}")
        print(f"    {_c('Action', 'cyan')} : {f.recommended_action}")


def print_results(state: dict, elapsed: float) -> None:
    report = state.get("audit_report")
    risk   = state.get("risk_score")
    fraud  = state.get("fraud_findings")
    comp   = state.get("compliance_findings")
    vuln   = state.get("vulnerability_findings")
    agent  = state.get("agent_quality")

    print(_c("\n" + "═" * 62, "bold"))
    print(_c("  BFSI AI COMPLIANCE & FRAUD INTELLIGENCE AGENT", "bold"))
    print(_c("  Sprint 2 — LangGraph Multi-Agent Analysis", "bold"))
    print(_c("═" * 62, "bold"))
    print(f"\n  Call ID  : {state.get('call_id')}")
    print(f"  Scenario : {state.get('scenario_label')}")
    print(f"  Status   : {state.get('processing_status')}")
    if state.get("errors"):
        for err in state["errors"]:
            print(f"  {_c('⚠ Error', 'red')}: {err}")

    # ── Risk summary ───────────────────────────────────────────────────────────
    _section("RISK SCORE SUMMARY")
    if risk:
        score_col = "red" if risk.rag_status.value == "RED" else ("yellow" if risk.rag_status.value == "AMBER" else "green")
        print(f"\n  Composite Score : {_c(str(risk.composite_score) + '/100', score_col)}")
        print(f"  RAG Status      : {_rag(risk.rag_status)}")
        print(f"\n  Fraud Score         : {risk.fraud_score}/100")
        print(f"  Compliance Score    : {risk.compliance_score}/100")
        print(f"  Vulnerability Score : {risk.vulnerability_score}/100")
        print(f"  Agent Quality Score : {risk.agent_quality_score}/100")
        if risk.priority_flags:
            print(f"\n  Priority Flags  :")
            for flag in risk.priority_flags:
                print(f"    ⚑  {_c(flag, 'red' if 'IMMEDIATE' in flag or 'FRAUD' in flag else 'yellow')}")

    # ── Agent results ──────────────────────────────────────────────────────────
    _section("1/4  FRAUD DETECTION AGENT")
    if fraud:
        detected = _c("FRAUD DETECTED", "red") if fraud.fraud_detected else _c("No fraud detected", "green")
        print(f"\n  {detected}")
        if fraud.fraud_type:
            print(f"  Type       : {fraud.fraud_type.value if hasattr(fraud.fraud_type, 'value') else fraud.fraud_type}")
        print(f"  Confidence : {fraud.confidence_score:.0%}")
        print(f"  Summary    : {fraud.summary}")
        _print_findings(fraud.findings)

    _section("2/4  COMPLIANCE AGENT  (FCA RAG)")
    if comp:
        detected = _c("VIOLATIONS DETECTED", "red") if comp.violations_detected else _c("Compliant", "green")
        print(f"\n  {detected}")
        print(f"  Summary    : {comp.summary}")
        if comp.missing_disclosures:
            print(f"  Missing disclosures:")
            for d in comp.missing_disclosures:
                print(f"    • {d}")
        _print_findings(comp.findings)

    _section("3/4  VULNERABLE CUSTOMER AGENT")
    if vuln:
        detected = _c("VULNERABLE CUSTOMER DETECTED", "red") if vuln.vulnerable_customer_detected else _c("No vulnerability signals", "green")
        escalate = f"  {_c('⚠ ESCALATION REQUIRED', 'red')}" if vuln.escalation_required else ""
        print(f"\n  {detected}{escalate}")
        if vuln.vulnerability_type:
            print(f"  Type       : {vuln.vulnerability_type.value if hasattr(vuln.vulnerability_type, 'value') else vuln.vulnerability_type}")
        print(f"  Summary    : {vuln.summary}")
        _print_findings(vuln.findings)

    _section("4/4  AGENT QUALITY AGENT")
    if agent:
        score_col = "green" if agent.overall_score >= 70 else ("yellow" if agent.overall_score >= 50 else "red")
        print(f"\n  Overall Score        : {_c(str(agent.overall_score) + '/100', score_col)}")
        print(f"  Professionalism      : {agent.professionalism}/100")
        print(f"  Disclosure Compliance: {agent.disclosure_compliance}/100")
        print(f"  Empathy              : {agent.empathy}/100")
        print(f"  Escalation Adherence : {agent.escalation_adherence}/100")
        print(f"  Notes : {agent.notes}")
        _print_findings(agent.findings)

    # ── Executive summary & actions ────────────────────────────────────────────
    _section("EXECUTIVE SUMMARY & RECOMMENDED ACTIONS")
    if report:
        print(f"\n  {report.executive_summary}\n")
        if report.recommended_actions:
            print(f"  {_c('Recommended Actions:', 'bold')}")
            for i, action in enumerate(report.recommended_actions, 1):
                col = "red" if "IMMEDIATE" in action or "URGENT" in action else "cyan"
                print(f"    {i}. {_c(action, col)}")

    print(f"\n  {_c('Analysis time', 'cyan')}: {elapsed:.1f}s")
    print(_c("═" * 62 + "\n", "bold"))


# ── Save output ────────────────────────────────────────────────────────────────

def save_output(state: dict, scenario: str) -> str:
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "outputs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{scenario}_result.json")

    def serialise(obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "value"):
            return obj.value
        return str(obj)

    output = {
        "call_id": state.get("call_id"),
        "scenario_label": state.get("scenario_label"),
        "processing_status": state.get("processing_status"),
        "errors": state.get("errors", []),
        "risk_score": serialise(state.get("risk_score")) if state.get("risk_score") else None,
        "fraud_findings": serialise(state.get("fraud_findings")) if state.get("fraud_findings") else None,
        "compliance_findings": serialise(state.get("compliance_findings")) if state.get("compliance_findings") else None,
        "vulnerability_findings": serialise(state.get("vulnerability_findings")) if state.get("vulnerability_findings") else None,
        "agent_quality": serialise(state.get("agent_quality")) if state.get("agent_quality") else None,
        "audit_report": serialise(state.get("audit_report")) if state.get("audit_report") else None,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    return output_path


# ── Main ───────────────────────────────────────────────────────────────────────

SYNTHETIC_SCENARIOS = [
    ("synthetic_data/scenario_01_app_fraud.txt",          "CALL-001", "APP Fraud — Urgent Safe Account Transfer"),
    ("synthetic_data/scenario_02_misselling_investment.txt", "CALL-002", "Mis-selling — Investment Product"),
    ("synthetic_data/scenario_03_vulnerable_elderly.txt", "CALL-003", "Vulnerable Customer — Elderly, Consent Uncertainty"),
    ("synthetic_data/scenario_04_gdpr_breach.txt",        "CALL-004", "GDPR Breach — Unverified Data Disclosure"),
    ("synthetic_data/scenario_05_clean_call.txt",         "CALL-005", "Clean Call — Compliant Agent Conduct"),
]


def run_one(transcript_path: str, call_id: str, scenario_label: str) -> None:
    issues = config.validate()
    if issues:
        for issue in issues:
            print(_c(f"[CONFIG ERROR] {issue}", "red"))
        sys.exit(1)

    if not os.path.exists(transcript_path):
        print(_c(f"[ERROR] File not found: {transcript_path}", "red"))
        sys.exit(1)

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    scenario = os.path.basename(transcript_path).replace(".txt", "")
    print(f"\n  {_c('Running LangGraph pipeline...', 'cyan')} [{scenario_label}]")

    start = time.time()
    state = run_analysis(
        transcript=transcript,
        call_id=call_id,
        scenario_label=scenario_label,
    )
    elapsed = time.time() - start

    print_results(state, elapsed)
    path = save_output(state, scenario)
    print(f"  {_c('JSON saved to:', 'cyan')} {path}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BFSI Compliance Agent — LangGraph multi-agent pipeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--transcript", help="Path to a transcript .txt file")
    group.add_argument("--all", action="store_true", help="Run all 5 synthetic scenarios")
    parser.add_argument("--call-id", default=None, help="Optional call ID (auto-generated if not set)")
    parser.add_argument("--label", default="", help="Optional scenario label")
    args = parser.parse_args()

    if args.all:
        for path, cid, label in SYNTHETIC_SCENARIOS:
            run_one(path, cid, label)
    else:
        call_id = args.call_id or f"CALL-{datetime.now().strftime('%H%M%S')}"
        label   = args.label or os.path.basename(args.transcript).replace(".txt", "").replace("_", " ").title()
        run_one(args.transcript, call_id, label)
