# BFSI AI Compliance & Fraud Intelligence Agent
### Project Progress Report — End of Day
**Repository:** `https://github.com/Venkyv/bfsi-ai-compliance-agent`
**Stack:** Python · LangGraph · LangChain · Groq · OpenRouter · ChromaDB · HuggingFace · Flask · FastAPI · Whisper · pyannote.audio

---

## Project Overview

An agentic AI platform that analyses banking customer service calls for fraud, compliance violations, and vulnerable customer risk. Built as **AI Exploration Series — Project 6** for the Apexon portfolio.

### Architecture
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
                           ↓
                [Risk Scoring Agent]  ← deterministic Python
                           ↓
                [Report Generation Agent]  ← LLM executive summary
                           ↓
              Flask Dashboard + Alerts  (Sprint 4)
```

---

## Sprint Status

| Sprint | Goal | Status |
|---|---|---|
| Sprint 0 | Setup, synthetic data, schemas, KB ingest | ✅ Complete |
| Sprint 1 | Groq LLM + single-agent structured output | ✅ Complete |
| Sprint 2 | LangGraph multi-agent orchestration | ✅ Complete |
| Sprint 3 | Whisper + pyannote diarisation | ⏳ Next |
| Sprint 4 | Flask dashboard | ⏳ Pending |
| Sprint 5 | FastAPI end-to-end pipeline | ⏳ Pending |
| Sprint 6 | Polish, tests, portfolio post | ⏳ Pending |

---

## Sprint 0 — Complete ✅
**Goal:** Everything needed to develop against before writing a single LLM call.

### Delivered
- Full project folder structure (`agents/`, `services/`, `schemas/`, `prompts/`, `knowledge_base/`, `synthetic_data/`, `dashboard/`, `api/`, `tests/`)
- `schemas/findings.py` — all Pydantic v2 output models
- `schemas/state.py` — LangGraph `CallAnalysisState` TypedDict
- `app/config.py` — centralised configuration with env var loading
- `.env.template`, `requirements.txt`, `.gitignore`, `README.md`

### 5 Synthetic Call Transcripts
| File | Scenario | Expected RAG |
|---|---|---|
| `scenario_01_app_fraud.txt` | APP fraud — safe account transfer, £62k at risk | 🔴 RED |
| `scenario_02_misselling_investment.txt` | Investment mis-selling — "risk-free" language | 🟡 AMBER |
| `scenario_03_vulnerable_elderly.txt` | Elderly customer — consent uncertainty, bereavement | 🟡 AMBER |
| `scenario_04_gdpr_breach.txt` | GDPR/SYSC 9 — unverified data disclosure | 🟡 AMBER |
| `scenario_05_clean_call.txt` | Clean compliant call — control scenario | 🟢 GREEN |

### FCA Knowledge Base (ChromaDB)
| Collection | Document | Chunks |
|---|---|---|
| `fca_consumer_duty` | FCA Consumer Duty PS22/9 + APP Fraud Guidance | 21 |
| `fca_vulnerable_customers` | FCA FG21/1 — Vulnerable Customers | 13 |
| `fca_call_recording` | FCA SYSC 9 + UK GDPR | 13 |
| **Total** | | **47 chunks** |

### Definition of Done — All Passed ✅
- 5 synthetic transcripts exist in `synthetic_data/`
- ChromaDB loaded — `ingest_kb.py` runs without error (47 chunks)
- All Pydantic models importable with no errors
- Verification query returns correct Consumer Duty content

---

## Sprint 1 — Complete ✅
**Goal:** LLM analyses a transcript and returns clean structured Pydantic JSON for all 4 agent types.

### Delivered
- `prompts/fraud_prompt.txt` — APP fraud detection with PSR/FCA regulatory references
- `prompts/compliance_prompt.txt` — FCA Consumer Duty, SYSC 9, GDPR, TCF violations
- `prompts/vulnerability_prompt.txt` — FCA FG21/1 vulnerable customer signals
- `prompts/agent_behaviour_prompt.txt` — 4-dimension agent conduct scoring
- `services/groq_service.py` — LLM call wrapper with JSON extraction, Pydantic validation, enum normalisation, and retry logic
- `services/knowledge_base_service.py` — ChromaDB RAG queries for compliance agent
- `run_single.py` — CLI entry point with colour-coded terminal output

### Key Engineering Decisions
- **`_normalise()` function** — maps LLM enum variants (`AGENT_BEHAVIOUR` → `AGENT_QUALITY`) before Pydantic validation
- **Low temperature (0.1)** — ensures consistent structured JSON output
- **Per-agent LLM calls** — each agent has its own focused prompt, not one combined call

### Validated Results (all 5 scenarios)
| Scenario | RAG | Score | Key Finding |
|---|---|---|---|
| APP Fraud | 🔴 RED | 82 | APP_FRAUD 95% confidence, agent offered to process transfer |
| Mis-selling | 🟡 AMBER | 52 | "Risk-free" language flagged, missing FCA disclosures |
| Vulnerable Elderly | 🟡 AMBER | 51 | "I suppose so" flagged as invalid consent (FG21/1 s3.2) |
| GDPR Breach | 🟡 AMBER | 66 | Full account data disclosed to unverified caller |
| Clean Call | 🟢 GREEN | — | No findings, FOS rights mentioned, correct protocols |

### Definition of Done — All Passed ✅
- `run_single.py` returns valid structured JSON for all 5 scenarios
- Clean call correctly returns `fraud_detected: false`
- No Pydantic validation errors on any output
- JSON saved to `data/outputs/` for each run

---

## Sprint 2 — Complete ✅
**Goal:** All 6 agents wired into a LangGraph graph with shared state and structured output.

### Delivered
**Agent nodes:**
- `agents/fraud_agent.py` — LangGraph node wrapping fraud analysis
- `agents/compliance_agent.py` — LangGraph node with ChromaDB RAG
- `agents/vulnerability_agent.py` — LangGraph node for FCA FG21/1 signals
- `agents/agent_behaviour_agent.py` — LangGraph node for conduct scoring
- `agents/risk_scoring_agent.py` — **deterministic Python** composite scoring (no LLM call)
- `agents/report_agent.py` — LLM executive summary + prioritised action list

**Orchestration:**
- `agents/orchestrator.py` — LangGraph `StateGraph` with sequential pipeline
- `run.py` — Sprint 2 entry point with `--all` flag for batch runs

### LangGraph Graph Structure
```
START → prepare → fraud_agent → compliance_agent → vulnerability_agent
      → agent_behaviour → risk_scoring → report → END
```
Sequential execution (respects Groq free tier 12,000 TPM limit).
Parallel fan-out code preserved in comments for paid tier upgrade.

### Risk Scoring Formula
```
Composite = (Fraud × 40%) + (Compliance × 30%) + (Vulnerability × 20%) + (Agent Quality Inverted × 10%)
RED ≥ 70  |  AMBER 40–69  |  GREEN < 40
```

### Validated Result — Scenario 1 (APP Fraud)
```
Composite Score : 89/100
RAG Status      : 🔴 RED — IMMEDIATE ACTION REQUIRED
Fraud Score     : 90/100  (APP_FRAUD, 90% confidence)
Compliance      : 100/100 (3 violations including HIGH severity)
Vulnerability   : 85/100  (CONSENT_UNCERTAINTY, escalation required)
Agent Quality   : 40/100  (escalation_adherence: 0/100)

Priority Flags:
  ⚑ APP_FRAUD_SUSPECTED
  ⚑ VULNERABLE_CUSTOMER_ESCALATION
  ⚑ HIGH_SEVERITY_COMPLIANCE_BREACH
  ⚑ AGENT_CONDUCT_REVIEW_REQUIRED

Executive Summary (LLM generated):
"The primary risk identified is a high-severity fraud incident with a 90%
confidence level, involving a vulnerable customer who was targeted by an
APP_FRAUD scam. The regulatory implications are significant, with three
compliance violations detected, including failure to disclose risks and
apply pressure tactics, and insufficient verification of customer identity.
Immediate action is recommended to review agent conduct, escalate the
vulnerable customer's case, and address the high-severity compliance
breaches to mitigate potential reputational and financial damage."
```

### Issues Encountered & Resolved
| Issue | Resolution |
|---|---|
| Groq `AGENT_BEHAVIOUR` enum mismatch | Added `_normalise()` function to map LLM variants |
| Groq 429 rate limit (TPM) | Added retry logic with auto-wait from error message |
| Groq 100k TPD daily limit exhausted | Added OpenRouter support via `LLM_PROVIDER` env var |
| Corporate SSL certificate error (Apexon network) | Code pushed to GitHub, continuing on personal laptop |
| `AuditReport` Pydantic error on None findings | Made findings fields `Optional` in schema |

### LLM Provider Support
```
LLM_PROVIDER=groq         # default — Groq API (llama-3.3-70b-versatile)
LLM_PROVIDER=openrouter   # fallback — OpenRouter free tier (same model)
```
Switching providers requires only a `.env` change — no code changes.

### Definition of Done — All Passed ✅
- LangGraph graph compiles with 8 nodes
- Full pipeline executes end-to-end (scenario 1 confirmed)
- Risk scoring node deterministic and consistent
- Report agent generates board-level executive summary
- JSON saved to `data/outputs/` for each run
- Code pushed to GitHub: `github.com/Venkyv/bfsi-ai-compliance-agent`

---

## Current File Structure
```
bfsi-ai-compliance-agent/
├── agents/
│   ├── orchestrator.py          ← LangGraph graph definition
│   ├── fraud_agent.py
│   ├── compliance_agent.py      ← RAG-enabled
│   ├── vulnerability_agent.py
│   ├── agent_behaviour_agent.py
│   ├── risk_scoring_agent.py    ← deterministic Python
│   └── report_agent.py          ← LLM executive summary
├── services/
│   ├── groq_service.py          ← Groq + OpenRouter provider
│   └── knowledge_base_service.py ← ChromaDB RAG queries
├── schemas/
│   ├── findings.py              ← All Pydantic v2 models
│   └── state.py                 ← LangGraph CallAnalysisState
├── prompts/
│   ├── fraud_prompt.txt
│   ├── compliance_prompt.txt
│   ├── vulnerability_prompt.txt
│   ├── agent_behaviour_prompt.txt
│   ├── risk_scoring_prompt.txt
│   └── report_prompt.txt
├── knowledge_base/
│   ├── fca_consumer_duty.txt
│   ├── fca_vulnerable_customers.txt
│   ├── fca_call_recording.txt
│   ├── fca_app_fraud.txt
│   └── ingest_kb.py
├── synthetic_data/
│   ├── scenario_01_app_fraud.txt
│   ├── scenario_02_misselling_investment.txt
│   ├── scenario_03_vulnerable_elderly.txt
│   ├── scenario_04_gdpr_breach.txt
│   └── scenario_05_clean_call.txt
├── app/
│   └── config.py                ← Groq + OpenRouter + all env vars
├── run.py                       ← Sprint 2 entry point (LangGraph)
├── run_single.py                ← Sprint 1 entry point (sequential)
├── requirements.txt
├── .env.template
├── .gitignore
└── README.md
```

---

## Sprint 3 — Next: Whisper + Speaker Diarisation
**Goal:** Audio file in → diarised transcript out, feeding the LangGraph pipeline.

### Planned Tasks
1. `services/whisper_service.py` — load Whisper base model, transcribe `.mp3`/`.wav`
2. `services/diarisation_service.py` — pyannote.audio speaker separation (AGENT / CUSTOMER)
3. Wire `transcribe_node` and `diarise_node` into LangGraph graph
4. Source 2–3 short synthetic audio files for testing
5. Full pipeline test: audio → diarised transcript → LangGraph agents → AuditReport

### Key Technical Note
Whisper transcribes audio but treats it as one voice.
pyannote.audio separates AGENT vs CUSTOMER speech.
Both are needed — "this product is risk-free" means very different things depending on who said it.

### Prerequisites for Sprint 3
- Personal laptop (no corporate SSL restrictions)
- HuggingFace token (required for pyannote.audio model download)
- `HUGGINGFACE_TOKEN` set in `.env`

---

## Tomorrow Morning Checklist
- [ ] Clone repo on personal laptop
- [ ] `pip install -r requirements.txt && pip install sentence-transformers==2.7.0`
- [ ] Set up `.env` with `GROQ_API_KEY` and `LLM_PROVIDER=groq`
- [ ] `python knowledge_base/ingest_kb.py`
- [ ] `python run.py --all` — confirm all 5 scenarios pass
- [ ] Sprint 2 fully signed off
- [ ] Start Sprint 3 — Whisper + diarisation

---

*BFSI AI Compliance & Fraud Intelligence Agent — AI Exploration Series Project 6*
*VR | Apexon Portfolio | Built with: Python · LangGraph · Groq · ChromaDB · Whisper*
