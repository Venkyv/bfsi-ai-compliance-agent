import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Groq ──────────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "2048"))
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.1"))

    # ── OpenRouter ────────────────────────────────────────────────────────────
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

    # ── Provider selector: "groq" (default) or "openrouter" ──────────────────
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")

    # ── HuggingFace ───────────────────────────────────────────────────────────
    HUGGINGFACE_TOKEN: str = os.getenv("HUGGINGFACE_TOKEN", "")

    # ── Whisper ───────────────────────────────────────────────────────────────
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    CHROMA_COLLECTION_FCA_CONSUMER_DUTY: str = "fca_consumer_duty"
    CHROMA_COLLECTION_VULNERABLE_CUSTOMERS: str = "fca_vulnerable_customers"
    CHROMA_COLLECTION_CALL_RECORDING: str = "fca_call_recording"
    CHROMA_COLLECTION_GDPR: str = "gdpr_financial"

    # ── Embeddings ────────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_CHUNK_SIZE: int = 500
    EMBEDDING_CHUNK_OVERLAP: int = 50
    KB_TOP_K: int = 5

    # ── Paths ─────────────────────────────────────────────────────────────────
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")
    AUDIO_DIR: str = f"{DATA_DIR}/audio"
    TRANSCRIPTS_DIR: str = f"{DATA_DIR}/transcripts"
    DIARISED_DIR: str = f"{DATA_DIR}/diarised"
    OUTPUTS_DIR: str = f"{DATA_DIR}/outputs"
    SYNTHETIC_DATA_DIR: str = os.getenv("SYNTHETIC_DATA_DIR", "./synthetic_data")
    KB_DIR: str = os.getenv("KB_DIR", "./knowledge_base")

    # ── Flask ─────────────────────────────────────────────────────────────────
    FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-prod")
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))

    # ── FastAPI ───────────────────────────────────────────────────────────────
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # ── Risk scoring weights ──────────────────────────────────────────────────
    RISK_WEIGHT_FRAUD: float = 0.40
    RISK_WEIGHT_COMPLIANCE: float = 0.30
    RISK_WEIGHT_VULNERABILITY: float = 0.20
    RISK_WEIGHT_AGENT_QUALITY: float = 0.10
    RAG_RED_THRESHOLD: int = 70
    RAG_AMBER_THRESHOLD: int = 40

    @classmethod
    def validate(cls) -> list[str]:
        issues = []
        if cls.LLM_PROVIDER == "groq" and not cls.GROQ_API_KEY:
            issues.append("GROQ_API_KEY is not set")
        if cls.LLM_PROVIDER == "openrouter" and not cls.OPENROUTER_API_KEY:
            issues.append("OPENROUTER_API_KEY is not set")
        if not cls.HUGGINGFACE_TOKEN:
            issues.append("HUGGINGFACE_TOKEN is not set (required for pyannote.audio)")
        return issues


config = Config()
