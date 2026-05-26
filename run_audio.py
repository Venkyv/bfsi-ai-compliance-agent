"""
run_audio.py

Sprint 3 entry point.
Analyses a banking call audio file through the full pipeline:
    Audio → Whisper → pyannote diarisation → LangGraph agents → AuditReport

Usage:
    python run_audio.py --audio data/audio/scenario_01_app_fraud.wav
    python run_audio.py --audio data/audio/scenario_01_app_fraud.wav --call-id CALL-001
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


# ── Reuse colour helpers from run.py ──────────────────────────────────────────

def _c(text, code):
    codes = {"red": "31", "green": "32", "yellow": "33", "cyan": "36", "bold": "1"}
    return f"\033[{codes.get(code, '0')}m{text}\033[0m"

def _rag(status):
    s = status.value if hasattr(status, "value") else status
    if s == "RED":    return _c("🔴  RED   — IMMEDIATE ACTION REQUIRED", "red")
    if s == "AMBER":  return _c("🟡  AMBER — REVIEW REQUIRED", "yellow")
    return _c("🟢  GREEN — NO ACTION REQUIRED", "green")


def print_diarised_preview(diarised: list[dict], max_lines: int = 8) -> None:
    """Print a preview of the diarised transcript."""
    if not diarised:
        return
    print(f"\n  {_c('Diarised transcript preview:', 'cyan')}")
    for seg in diarised[:max_lines]:
        speaker = seg.get("speaker", "UNKNOWN")
        text = seg.get("text", "")[:80]
        t = seg.get("start_time", 0)
        col = "cyan" if speaker == "AGENT" else "green"
        print(f"    [{t:05.1f}s] {_c(speaker, col)}: {text}")
    if len(diarised) > max_lines:
        print(f"    ... and {len(diarised) - max_lines} more segments")


def save_output(state: dict, audio_path: str) -> str:
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "outputs")
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(audio_path))[0]
    output_path = os.path.join(output_dir, f"{base}_audio_result.json")

    def serialise(obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "value"):
            return obj.value
        return str(obj)

    output = {
        "call_id": state.get("call_id"),
        "scenario_label": state.get("scenario_label"),
        "audio_file": audio_path,
        "processing_status": state.get("processing_status"),
        "errors": state.get("errors", []),
        "diarised_segments": state.get("diarised_transcript"),
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


def run(audio_path: str, call_id: str, label: str) -> None:
    # Validate
    issues = config.validate()
    if issues:
        for issue in issues:
            print(_c(f"[CONFIG ERROR] {issue}", "red"))
        sys.exit(1)

    if not os.path.exists(audio_path):
        print(_c(f"[ERROR] Audio file not found: {audio_path}", "red"))
        print("Run first: python synthetic_data/generate_audio.py")
        sys.exit(1)

    file_size = os.path.getsize(audio_path) / (1024 * 1024)

    print(_c("\n" + "═" * 62, "bold"))
    print(_c("  BFSI AI COMPLIANCE & FRAUD INTELLIGENCE AGENT", "bold"))
    print(_c("  Sprint 3 — Audio Pipeline (Whisper + Diarisation)", "bold"))
    print(_c("═" * 62, "bold"))
    print(f"\n  Audio file : {os.path.basename(audio_path)}")
    print(f"  File size  : {file_size:.1f} MB")
    print(f"  Call ID    : {call_id}")
    print(f"  Scenario   : {label}")
    print(f"  Provider   : {config.LLM_PROVIDER.upper()}")
    print(f"\n  {_c('Step 1/3: Whisper transcription...', 'cyan')}")

    start = time.time()
    state = run_analysis(
        audio_path=audio_path,
        call_id=call_id,
        scenario_label=label,
    )
    elapsed = time.time() - start

    # Show errors if any
    if state.get("errors"):
        for err in state["errors"]:
            print(f"  {_c('⚠ ' + err, 'yellow')}")

    # Show diarised transcript preview
    if state.get("diarised_transcript"):
        print(f"\n  {_c('Step 2/3: Diarisation complete ✓', 'cyan')}")
        print_diarised_preview(state["diarised_transcript"])
    else:
        print(f"\n  {_c('⚠ Diarisation not available — used raw transcript', 'yellow')}")

    print(f"\n  {_c('Step 3/3: LangGraph agent analysis complete ✓', 'cyan')}")

    # Risk summary
    risk = state.get("risk_score")
    if risk:
        score_col = "red" if risk.rag_status.value == "RED" else ("yellow" if risk.rag_status.value == "AMBER" else "green")
        print(_c("\n" + "─" * 62, "cyan"))
        print(f"\n  Composite Score : {_c(str(risk.composite_score) + '/100', score_col)}")
        print(f"  RAG Status      : {_rag(risk.rag_status)}")
        if risk.priority_flags:
            for flag in risk.priority_flags:
                print(f"    ⚑  {_c(flag, 'red')}")

    # Executive summary
    report = state.get("audit_report")
    if report and report.executive_summary:
        print(_c("\n" + "─" * 62, "cyan"))
        print(f"\n  {_c('Executive Summary:', 'bold')}")
        print(f"  {report.executive_summary}")

        if report.recommended_actions:
            print(f"\n  {_c('Recommended Actions:', 'bold')}")
            for i, action in enumerate(report.recommended_actions, 1):
                col = "red" if "IMMEDIATE" in action or "URGENT" in action else "cyan"
                print(f"    {i}. {_c(action, col)}")

    print(f"\n  {_c('Total pipeline time', 'cyan')}: {elapsed:.1f}s")
    print(_c("═" * 62 + "\n", "bold"))

    output_path = save_output(state, audio_path)
    print(f"  {_c('JSON saved to:', 'cyan')} {output_path}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="BFSI Compliance Agent — audio file analysis pipeline"
    )
    parser.add_argument("--audio", required=True, help="Path to audio file (.wav, .mp3, .m4a)")
    parser.add_argument("--call-id", default=None)
    parser.add_argument("--label", default="")
    args = parser.parse_args()

    call_id = args.call_id or f"CALL-{datetime.now().strftime('%H%M%S')}"
    label = args.label or os.path.splitext(os.path.basename(args.audio))[0].replace("_", " ").title()
    run(args.audio, call_id, label)
