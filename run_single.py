"""
run_single.py

Sprint 1 entry point.
Analyses a single transcript (text file) through all 4 agents
and prints the structured results to console.

Usage:
    python run_single.py --transcript synthetic_data/scenario_01_app_fraud.txt
    python run_single.py --transcript synthetic_data/scenario_02_misselling_investment.txt
    python run_single.py --transcript synthetic_data/scenario_03_vulnerable_elderly.txt
    python run_single.py --transcript synthetic_data/scenario_04_gdpr_breach.txt
    python run_single.py --transcript synthetic_data/scenario_05_clean_call.txt
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import config
from services.groq_service import (
    analyse_fraud,
    analyse_compliance,
    analyse_vulnerability,
    analyse_agent_quality,
)
from services.knowledge_base_service import get_compliance_context


# ── Helpers ────────────────────────────────────────────────────────────────────

def _colour(text: str, code: str) -> str:
    """ANSI colour codes for terminal output."""
    codes = {"red": "31", "green": "32", "yellow": "33", "cyan": "36", "bold": "1", "reset": "0"}
    return f"\033[{codes.get(code, '0')}m{text}\033[0m"


def _rag_colour(status: str) -> str:
    if status == "RED":
        return _colour("🔴 RED", "red")
    elif status == "AMBER":
        return _colour("🟡 AMBER", "yellow")
    return _colour("🟢 GREEN", "green")


def _severity_colour(severity: str) -> str:
    if severity == "HIGH":
        return _colour("HIGH", "red")
    elif severity == "MEDIUM":
        return _colour("MEDIUM", "yellow")
    return _colour("LOW", "green")


def _print_section(title: str) -> None:
    print(f"\n{_colour('━' * 60, 'cyan')}")
    print(_colour(f"  {title}", "bold"))
    print(_colour('━' * 60, 'cyan'))


def _print_findings(findings: list, label: str) -> None:
    if not findings:
        print(f"  {_colour('✓ No findings', 'green')}")
        return
    for f in findings:
        sev = _severity_colour(f.severity.value if hasattr(f.severity, 'value') else f.severity)
        print(f"\n  [{sev}] {f.finding_id} — {f.description}")
        print(f"  Quote    : \"{f.evidence_quote}\"")
        print(f"  Speaker  : {f.speaker.value if hasattr(f.speaker, 'value') else f.speaker}")
        print(f"  Rule Ref : {f.regulatory_reference}")
        print(f"  Action   : {f.recommended_action}")


def _compute_risk_score(fraud, compliance, vuln, agent) -> tuple[int, str]:
    """Simple weighted composite risk score."""
    fraud_s = int(fraud.confidence_score * 100) if fraud.fraud_detected else 0
    comp_s = min(len(compliance.findings) * 25, 100) if compliance.violations_detected else 0
    vuln_s = 80 if vuln.escalation_required else (40 if vuln.vulnerable_customer_detected else 0)
    agent_penalty = max(0, 100 - agent.overall_score)

    composite = int(
        fraud_s * config.RISK_WEIGHT_FRAUD
        + comp_s * config.RISK_WEIGHT_COMPLIANCE
        + vuln_s * config.RISK_WEIGHT_VULNERABILITY
        + agent_penalty * config.RISK_WEIGHT_AGENT_QUALITY
    )
    composite = min(composite, 100)

    if composite >= config.RAG_RED_THRESHOLD:
        rag = "RED"
    elif composite >= config.RAG_AMBER_THRESHOLD:
        rag = "AMBER"
    else:
        rag = "GREEN"

    return composite, rag


# ── Main ───────────────────────────────────────────────────────────────────────

def run(transcript_path: str) -> None:
    # Validate config
    issues = config.validate()
    if issues:
        for issue in issues:
            print(_colour(f"[CONFIG ERROR] {issue}", "red"))
        sys.exit(1)

    # Load transcript
    if not os.path.exists(transcript_path):
        print(_colour(f"[ERROR] Transcript not found: {transcript_path}", "red"))
        sys.exit(1)

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    scenario = os.path.basename(transcript_path).replace(".txt", "")

    print(_colour("\n" + "═" * 60, "bold"))
    print(_colour("  BFSI AI COMPLIANCE & FRAUD INTELLIGENCE AGENT", "bold"))
    print(_colour("  Sprint 1 — Single Transcript Analysis", "bold"))
    print(_colour("═" * 60, "bold"))
    print(f"\n  Scenario : {scenario}")
    print(f"  File     : {transcript_path}")
    print(f"  Model    : {config.GROQ_MODEL}")

    results = {}
    total_start = time.time()

    # ── 1. Fraud analysis ──────────────────────────────────────────────────────
    _print_section("1/4  FRAUD DETECTION AGENT")
    print("  Analysing...", end="", flush=True)
    t = time.time()
    fraud = analyse_fraud(transcript)
    print(f" done ({time.time()-t:.1f}s)")

    detected = _colour("FRAUD DETECTED", "red") if fraud.fraud_detected else _colour("No fraud detected", "green")
    print(f"\n  Result     : {detected}")
    if fraud.fraud_type:
        print(f"  Type       : {fraud.fraud_type.value if hasattr(fraud.fraud_type, 'value') else fraud.fraud_type}")
    print(f"  Confidence : {fraud.confidence_score:.0%}")
    print(f"  Summary    : {fraud.summary}")
    _print_findings(fraud.findings, "Fraud")
    results["fraud"] = fraud

    # ── 2. Compliance analysis ─────────────────────────────────────────────────
    _print_section("2/4  COMPLIANCE AGENT  (FCA RAG-enabled)")
    print("  Retrieving regulatory context...", end="", flush=True)
    t = time.time()
    kb_context = get_compliance_context(transcript)
    print(f" done ({time.time()-t:.1f}s)")
    print("  Analysing...", end="", flush=True)
    t = time.time()
    compliance = analyse_compliance(transcript, kb_context)
    print(f" done ({time.time()-t:.1f}s)")

    detected = _colour("VIOLATIONS DETECTED", "red") if compliance.violations_detected else _colour("No violations detected", "green")
    print(f"\n  Result     : {detected}")
    print(f"  Summary    : {compliance.summary}")
    if compliance.missing_disclosures:
        print(f"  Missing disclosures:")
        for d in compliance.missing_disclosures:
            print(f"    • {d}")
    _print_findings(compliance.findings, "Compliance")
    results["compliance"] = compliance

    # ── 3. Vulnerability analysis ──────────────────────────────────────────────
    _print_section("3/4  VULNERABLE CUSTOMER AGENT")
    print("  Analysing...", end="", flush=True)
    t = time.time()
    vuln = analyse_vulnerability(transcript)
    print(f" done ({time.time()-t:.1f}s)")

    detected = _colour("VULNERABLE CUSTOMER DETECTED", "red") if vuln.vulnerable_customer_detected else _colour("No vulnerability signals", "green")
    escalate = _colour("⚠ ESCALATION REQUIRED", "red") if vuln.escalation_required else ""
    print(f"\n  Result     : {detected} {escalate}")
    if vuln.vulnerability_type:
        print(f"  Type       : {vuln.vulnerability_type.value if hasattr(vuln.vulnerability_type, 'value') else vuln.vulnerability_type}")
    print(f"  Summary    : {vuln.summary}")
    _print_findings(vuln.findings, "Vulnerability")
    results["vulnerability"] = vuln

    # ── 4. Agent quality analysis ──────────────────────────────────────────────
    _print_section("4/4  AGENT QUALITY AGENT")
    print("  Analysing...", end="", flush=True)
    t = time.time()
    agent = analyse_agent_quality(transcript)
    print(f" done ({time.time()-t:.1f}s)")

    score_colour = "green" if agent.overall_score >= 70 else ("yellow" if agent.overall_score >= 50 else "red")
    print(f"\n  Overall    : {_colour(str(agent.overall_score) + '/100', score_colour)}")
    print(f"  Professionalism      : {agent.professionalism}/100")
    print(f"  Disclosure Compliance: {agent.disclosure_compliance}/100")
    print(f"  Empathy              : {agent.empathy}/100")
    print(f"  Escalation Adherence : {agent.escalation_adherence}/100")
    print(f"  Notes      : {agent.notes}")
    _print_findings(agent.findings, "Agent Quality")
    results["agent"] = agent

    # ── Risk score summary ─────────────────────────────────────────────────────
    composite, rag = _compute_risk_score(fraud, compliance, vuln, agent)
    elapsed = time.time() - total_start

    _print_section("RISK SCORE SUMMARY")
    print(f"\n  Composite Score : {_colour(str(composite) + '/100', 'red' if rag == 'RED' else ('yellow' if rag == 'AMBER' else 'green'))}")
    print(f"  RAG Status      : {_rag_colour(rag)}")
    print(f"  Immediate Action: {'⚠ YES' if rag == 'RED' else 'No'}")
    print(f"\n  Analysis time   : {elapsed:.1f}s")
    print(_colour("\n" + "═" * 60 + "\n", "bold"))

    # ── Save JSON output ───────────────────────────────────────────────────────
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "outputs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{scenario}_result.json")

    output = {
        "scenario": scenario,
        "rag_status": rag,
        "composite_score": composite,
        "fraud": json.loads(fraud.model_dump_json()),
        "compliance": json.loads(compliance.model_dump_json()),
        "vulnerability": json.loads(vuln.model_dump_json()),
        "agent_quality": json.loads(agent.model_dump_json()),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"  JSON saved to: {output_path}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BFSI Compliance Agent — single transcript analysis")
    parser.add_argument(
        "--transcript",
        required=True,
        help="Path to transcript .txt file e.g. synthetic_data/scenario_01_app_fraud.txt",
    )
    args = parser.parse_args()
    run(args.transcript)
