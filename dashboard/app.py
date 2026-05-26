"""
dashboard/app.py
Flask dashboard for BFSI AI Compliance & Fraud Intelligence Agent.
"""

import os
import sys
import json
import glob
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, abort, request, redirect, url_for, flash
from app.config import config

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"),
)
app.secret_key = config.FLASK_SECRET_KEY

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "outputs")


# ── Data helpers ───────────────────────────────────────────────────────────────

def load_all_reports():
    reports = []
    pattern = os.path.join(OUTPUTS_DIR, "*_result.json")
    for filepath in sorted(glob.glob(pattern)):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["_filename"] = os.path.basename(filepath).replace("_result.json", "")
            reports.append(data)
        except Exception as e:
            print(f"[WARN] Could not load {filepath}: {e}")
    return reports


def load_report(call_id):
    reports = load_all_reports()
    for r in reports:
        if r.get("call_id") == call_id or r.get("_filename") == call_id:
            return r
    return None


def get_dashboard_stats(reports):
    total = len(reports)
    red   = sum(1 for r in reports if (r.get("risk_score") or {}).get("rag_status") == "RED")
    amber = sum(1 for r in reports if (r.get("risk_score") or {}).get("rag_status") == "AMBER")
    green = sum(1 for r in reports if (r.get("risk_score") or {}).get("rag_status") == "GREEN")
    fraud    = sum(1 for r in reports if (r.get("fraud_findings") or {}).get("fraud_detected"))
    vuln     = sum(1 for r in reports if (r.get("vulnerability_findings") or {}).get("vulnerable_customer_detected"))
    comp     = sum(1 for r in reports if (r.get("compliance_findings") or {}).get("violations_detected"))
    avg      = int(sum((r.get("risk_score") or {}).get("composite_score", 0) for r in reports) / total) if total else 0
    return {"total": total, "red": red, "amber": amber, "green": green,
            "fraud_detected": fraud, "vulnerable_customers": vuln,
            "compliance_breaches": comp, "avg_risk_score": avg, "immediate_action": red}


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    reports = load_all_reports()
    stats   = get_dashboard_stats(reports)
    rag_chart     = {"RED": stats["red"], "AMBER": stats["amber"], "GREEN": stats["green"]}
    score_labels  = [r.get("scenario_label", r.get("call_id", "Unknown"))[:35] for r in reports]
    score_data    = [(r.get("risk_score") or {}).get("composite_score", 0) for r in reports]
    score_colours = []
    for r in reports:
        rag = (r.get("risk_score") or {}).get("rag_status", "GREEN")
        score_colours.append("#EF4444" if rag == "RED" else ("#F59E0B" if rag == "AMBER" else "#10B981"))
    agent_labels = [r.get("call_id", "?") for r in reports]
    agent_scores = [(r.get("agent_quality") or {}).get("overall_score", 0) for r in reports]
    return render_template("index.html",
        reports=reports, stats=stats,
        rag_chart=json.dumps(rag_chart),
        score_labels=json.dumps(score_labels),
        score_data=json.dumps(score_data),
        score_colours=json.dumps(score_colours),
        agent_labels=json.dumps(agent_labels),
        agent_scores=json.dumps(agent_scores),
        now=datetime.now().strftime("%d %b %Y %H:%M"),
    )


@app.route("/report/<call_id>")
def report(call_id):
    data = load_report(call_id)
    if not data:
        abort(404)
    return render_template("report.html", r=data, now=datetime.now().strftime("%d %b %Y %H:%M"))


@app.route("/upload", methods=["POST"])
def upload_transcript():
    """Submit a transcript for analysis via the FastAPI backend."""
    transcript = request.form.get("transcript", "").strip()
    label      = request.form.get("label", "").strip()

    if not transcript:
        flash("Transcript cannot be empty", "error")
        return redirect(url_for("index"))

    try:
        resp = requests.post(
            f"http://localhost:{config.API_PORT}/analyse/transcript",
            json={"transcript": transcript, "scenario_label": label},
            timeout=180,
        )
        if resp.status_code == 200:
            data = resp.json()
            flash(
                f"Analysis complete — {data['call_id']} — "
                f"{data['rag_status']} ({data['composite_score']}/100)",
                "success",
            )
            return redirect(url_for("report", call_id=data["call_id"]))
        else:
            flash(f"Analysis failed: {resp.text[:200]}", "error")
    except requests.exceptions.ConnectionError:
        flash("FastAPI server not running. Start it with: python app/main.py", "error")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")

    return redirect(url_for("index"))


@app.route("/api/reports")
def api_reports():
    return jsonify(load_all_reports())


@app.route("/api/report/<call_id>")
def api_report(call_id):
    data = load_report(call_id)
    if not data:
        return jsonify({"error": "Not found"}), 404
    return jsonify(data)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n  BFSI Compliance Dashboard")
    print(f"  Reports directory: {OUTPUTS_DIR}")
    reports = load_all_reports()
    print(f"  Loaded {len(reports)} reports")
    print(f"  Dashboard: http://localhost:{config.FLASK_PORT}\n")
    app.run(host="0.0.0.0", port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
