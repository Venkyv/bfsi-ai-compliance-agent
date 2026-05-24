"""
services/groq_service.py
LLM call wrapper — supports both Groq and OpenRouter.
Provider is controlled by LLM_PROVIDER in .env (groq | openrouter).
"""

import os
import sys
import json
import re
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import config
from schemas.findings import (
    FraudFindings,
    ComplianceFindings,
    VulnerabilityFindings,
    AgentQualityScore,
)


# ── Prompt loading ─────────────────────────────────────────────────────────────

def _load_prompt(filename: str) -> str:
    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "prompts", filename,
    )
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def _build_prompt(template: str, transcript: str, kb_context: str = "") -> str:
    prompt = template.replace("{transcript}", transcript)
    prompt = prompt.replace("{kb_context}", kb_context if kb_context else "No additional context retrieved.")
    return prompt


# ── LLM call ───────────────────────────────────────────────────────────────────

def _call_groq(prompt: str, retries: int = 3) -> str:
    """Call Groq API with retry on rate limit."""
    try:
        from groq import Groq, RateLimitError
    except ImportError:
        raise ImportError("groq package not installed. Run: pip install groq")

    client = Groq(api_key=config.GROQ_API_KEY)

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=config.GROQ_MODEL,
                max_tokens=config.GROQ_MAX_TOKENS,
                temperature=config.GROQ_TEMPERATURE,
                messages=[
                    {"role": "system", "content": "You are a precise compliance analyst. You respond ONLY with valid JSON. No markdown, no explanation, no preamble."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content.strip()

        except RateLimitError as e:
            wait = 10
            match = re.search(r"try again in (\d+(?:\.\d+)?)s", str(e))
            if match:
                wait = float(match.group(1)) + 1
            if attempt < retries - 1:
                print(f"\n  [Rate limit] Waiting {wait:.0f}s before retry {attempt + 2}/{retries}...", flush=True)
                time.sleep(wait)
            else:
                raise

    raise RuntimeError("All Groq retries exhausted")


def _call_openrouter(prompt: str, retries: int = 3) -> str:
    """Call OpenRouter API using OpenAI-compatible format."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai package not installed. Run: pip install openai")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config.OPENROUTER_API_KEY,
    )

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=config.OPENROUTER_MODEL,
                max_tokens=config.GROQ_MAX_TOKENS,
                temperature=config.GROQ_TEMPERATURE,
                messages=[
                    {"role": "system", "content": "You are a precise compliance analyst. You respond ONLY with valid JSON. No markdown, no explanation, no preamble."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            msg = str(e)
            # Handle rate limit
            if "429" in msg or "rate limit" in msg.lower():
                wait = 15
                match = re.search(r"try again in (\d+(?:\.\d+)?)s", msg)
                if match:
                    wait = float(match.group(1)) + 1
                if attempt < retries - 1:
                    print(f"\n  [Rate limit] Waiting {wait:.0f}s before retry {attempt + 2}/{retries}...", flush=True)
                    time.sleep(wait)
                    continue
            raise

    raise RuntimeError("All OpenRouter retries exhausted")


def _call_llm(prompt: str) -> str:
    """Route to correct LLM provider based on config."""
    provider = config.LLM_PROVIDER.lower()
    if provider == "openrouter":
        return _call_openrouter(prompt)
    return _call_groq(prompt)


# ── JSON extraction ────────────────────────────────────────────────────────────

def _extract_json(raw: str) -> dict:
    clean = re.sub(r"```(?:json)?", "", raw).strip()
    clean = clean.strip("`").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\n\nRaw response:\n{raw[:500]}")


# ── Normalisation ──────────────────────────────────────────────────────────────

def _normalise(data: dict) -> dict:
    category_map = {
        "AGENT_BEHAVIOUR": "AGENT_QUALITY",
        "AGENT_BEHAVIOR": "AGENT_QUALITY",
        "AGENT_CONDUCT": "AGENT_QUALITY",
        "FRAUD_DETECTION": "FRAUD",
        "VULNERABLE": "VULNERABILITY",
        "VULNERABLE_CUSTOMER": "VULNERABILITY",
    }
    fraud_type_map = {
        "AUTHORISED_PUSH_PAYMENT": "APP_FRAUD",
        "AUTHORIZED_PUSH_PAYMENT": "APP_FRAUD",
        "PUSH_PAYMENT_FRAUD": "APP_FRAUD",
        "SAFE_ACCOUNT_SCAM": "APP_FRAUD",
    }
    for finding in data.get("findings", []):
        if "category" in finding:
            finding["category"] = category_map.get(finding["category"], finding["category"])
    if "fraud_type" in data and data["fraud_type"]:
        data["fraud_type"] = fraud_type_map.get(data["fraud_type"], data["fraud_type"])
    return data


# ── Public analysis functions ──────────────────────────────────────────────────

def analyse_fraud(transcript: str) -> FraudFindings:
    template = _load_prompt("fraud_prompt.txt")
    prompt = _build_prompt(template, transcript)
    raw = _call_llm(prompt)
    return FraudFindings(**_normalise(_extract_json(raw)))


def analyse_compliance(transcript: str, kb_context: str = "") -> ComplianceFindings:
    template = _load_prompt("compliance_prompt.txt")
    prompt = _build_prompt(template, transcript, kb_context)
    raw = _call_llm(prompt)
    return ComplianceFindings(**_normalise(_extract_json(raw)))


def analyse_vulnerability(transcript: str) -> VulnerabilityFindings:
    template = _load_prompt("vulnerability_prompt.txt")
    prompt = _build_prompt(template, transcript)
    raw = _call_llm(prompt)
    return VulnerabilityFindings(**_normalise(_extract_json(raw)))


def analyse_agent_quality(transcript: str) -> AgentQualityScore:
    template = _load_prompt("agent_behaviour_prompt.txt")
    prompt = _build_prompt(template, transcript)
    raw = _call_llm(prompt)
    return AgentQualityScore(**_normalise(_extract_json(raw)))
