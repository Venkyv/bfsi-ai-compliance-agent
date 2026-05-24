# BFSI AI Compliance & Fraud Intelligence Agent

> AI Exploration Series — Project 6 | Built by Venkatesh Reddy Valluru

An agentic AI platform that analyses banking customer service calls for fraud, compliance violations, and vulnerable customer risk — using Whisper, LangGraph multi-agent orchestration, FCA regulatory RAG, and a Flask + Chart.js dashboard.

---

## The Problem

UK banks audit only 2–5% of customer calls manually. The rest go unreviewed. This means:
- APP fraud goes undetected until after the money is gone
- FCA Consumer Duty violations slip through
- Vulnerable customers don't get the care they need
- GDPR and SYSC 9 breaches are missed

**This platform analyses 100% of calls automatically.**

---

## Architecture

```
Banking Call Audio (.mp3 / .wav)
            ↓
[Whisper STT]  →  Raw Transcript
            ↓
[pyannote.audio]  →  Diarised Transcript (AGENT / CUSTOMER)
            ↓
[LangGraph Orchestrator]
     ↓              ↓              ↓              ↓
[Fraud Agent] [Compliance   [Vulnerability  [Agent Quality
              Agent + RAG]   Agent]          Agent]
     └──────────────┴──────────────┴──────────────┘
                           ↓
                [Risk Scoring Agent]
                           ↓
                [Report Generation Agent]
                           ↓
              Flask Dashboard + Alerts
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Speech-to-Text | OpenAI Whisper (local) |
| Speaker Diarisation | pyannote.audio |
| Agentic Orchestration | LangGraph |
| LLM | Groq API + Llama 3.3-70b-versatile |
| Embeddings | HuggingFace all-MiniLM-L6-v2 |
| Vector Store | ChromaDB |
| Regulatory Knowledge Base | FCA Consumer Duty, FG21/1, SYSC 9, APP Fraud Guidance |
| Backend API | FastAPI |
| Dashboard | Flask + Chart.js |
| Data Models | Pydantic v2 |

---

## Agents

| Agent | Purpose |
|---|---|
| Fraud Agent | Detects APP fraud, account compromise, and suspicious payment language |
| Compliance Agent | RAG-powered check against FCA Consumer Duty, SYSC 9, and GDPR rules |
| Vulnerability Agent | Identifies vulnerable customer signals per FCA FG21/1 |
| Agent Quality Agent | Scores bank agent conduct on professionalism, disclosure, empathy, escalation |
| Risk Scoring Agent | Produces composite RAG risk score (Red/Amber/Green) |
| Report Agent | Generates executive summary narrative for compliance team |

---

## Project Status

| Sprint | Goal | Status |
|---|---|---|
| Sprint 0 | Setup, synthetic data, schemas, KB ingest | ✅ Complete |
| Sprint 1 | Groq LLM + single-agent structured output | ⏳ Pending |
| Sprint 2 | LangGraph multi-agent orchestration | ⏳ Pending |
| Sprint 3 | Whisper + pyannote diarisation | ⏳ Pending |
| Sprint 4 | Flask dashboard | ⏳ Pending |
| Sprint 5 | FastAPI end-to-end pipeline | ⏳ Pending |
| Sprint 6 | Polish, tests, portfolio post | ⏳ Pending |

---

## Quick Start

```bash
# 1. Clone and set up environment
git clone https://github.com/Venkyv/bfsi-ai-compliance-agent
cd bfsi-ai-compliance-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.template .env
# Edit .env and add your GROQ_API_KEY and HUGGINGFACE_TOKEN

# 3. Ingest the FCA knowledge base
python knowledge_base/ingest_kb.py

# 4. Run analysis on a synthetic transcript
python run.py --transcript synthetic_data/scenario_01_app_fraud.txt
```

---

## Regulatory Coverage

- **FCA Consumer Duty** (PS22/9, effective July 2023) — all four outcomes
- **FCA FG21/1** — Vulnerable customer identification and treatment
- **FCA SYSC 9** — Call recording and customer identity verification
- **UK GDPR / DPA 2018** — Data minimisation and breach obligations
- **PSR APP Fraud Mandatory Reimbursement** (October 2024) — agent intervention requirements

---

*Part of the AI Exploration Series — a self-directed AI engineering capability programme.*
*Stack: Python · LangGraph · LangChain · Groq · Whisper · pyannote · ChromaDB · Flask*
