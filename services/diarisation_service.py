"""
services/diarisation_service.py

Speaker diarisation using pyannote.audio.
Separates AGENT and CUSTOMER speech from a banking call audio file.

Requires:
    - HuggingFace token (pyannote models are gated)
    - HUGGINGFACE_TOKEN in .env
    - Accept model terms at:
        https://hf.co/pyannote/speaker-diarization-3.1
        https://hf.co/pyannote/segmentation-3.0

How it works:
    1. pyannote identifies WHO is speaking and WHEN (speaker segments)
    2. Whisper segments tell us WHAT was said and WHEN
    3. We align them by timestamp → each text segment gets a speaker label
    4. We map SPEAKER_00/SPEAKER_01 to AGENT/CUSTOMER
       (AGENT = speaker with more total speaking time in most banking calls)
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import config

_pipeline_cache = None


def _get_pipeline():
    """Load pyannote diarisation pipeline (cached after first load)."""
    global _pipeline_cache
    if _pipeline_cache is None:
        if not config.HUGGINGFACE_TOKEN:
            raise ValueError(
                "HUGGINGFACE_TOKEN is not set in .env. "
                "Required for pyannote.audio model download. "
                "Get a free token at https://huggingface.co/settings/tokens"
            )
        try:
            from pyannote.audio import Pipeline
        except ImportError:
            raise ImportError(
                "pyannote.audio not installed. Run: pip install pyannote.audio"
            )

        print("  [Diarisation] Loading pyannote pipeline...", flush=True)
        print("  [Diarisation] First run will download model (~200MB)...", flush=True)

        _pipeline_cache = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=config.HUGGINGFACE_TOKEN,
        )
        print("  [Diarisation] Pipeline loaded.", flush=True)
    return _pipeline_cache


def _assign_speaker_labels(diarisation_result) -> dict[str, str]:
    """
    Map pyannote speaker IDs (SPEAKER_00, SPEAKER_01) to AGENT / CUSTOMER.
    Strategy: AGENT is the speaker with the most speaking time.
    (In banking calls the agent typically speaks more than the customer)
    """
    speaker_durations: dict[str, float] = {}

    for turn, _, speaker in diarisation_result.itertracks(yield_label=True):
        duration = turn.end - turn.start
        speaker_durations[speaker] = speaker_durations.get(speaker, 0) + duration

    if len(speaker_durations) == 0:
        return {}

    if len(speaker_durations) == 1:
        # Only one speaker detected — label as AGENT
        only_speaker = list(speaker_durations.keys())[0]
        return {only_speaker: "AGENT"}

    # Sort by duration — most speaking time = AGENT
    sorted_speakers = sorted(speaker_durations.items(), key=lambda x: x[1], reverse=True)
    label_map = {}
    labels = ["AGENT", "CUSTOMER"]

    for i, (speaker, _) in enumerate(sorted_speakers):
        label_map[speaker] = labels[i] if i < len(labels) else f"SPEAKER_{i}"

    return label_map


def _get_speaker_at_time(
    diarisation_result,
    timestamp: float,
    label_map: dict[str, str],
) -> str:
    """Find which speaker was active at a given timestamp."""
    for turn, _, speaker in diarisation_result.itertracks(yield_label=True):
        if turn.start <= timestamp <= turn.end:
            return label_map.get(speaker, "UNKNOWN")
    return "UNKNOWN"


def diarise(audio_path: str, whisper_segments: list[dict]) -> list[dict]:
    """
    Combine pyannote diarisation with Whisper segments to produce
    a speaker-labelled transcript.

    Args:
        audio_path:       Path to audio file
        whisper_segments: List of Whisper segments [{id, start, end, text}]

    Returns:
        List of diarised segments:
        [{speaker, text, start_time, end_time}]
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    pipeline = _get_pipeline()

    print(f"  [Diarisation] Analysing speakers in: {os.path.basename(audio_path)}", flush=True)

    # Pre-load audio as waveform dict to bypass torchcodec on Windows CPU
    import torch
    import warnings

    audio_input = None

    # Try torchaudio first
    try:
        import torchaudio
        waveform, sample_rate = torchaudio.load(audio_path)
        audio_input = {"waveform": waveform, "sample_rate": sample_rate}
        print(f"  [Diarisation] Audio loaded via torchaudio: {waveform.shape}, {sample_rate}Hz", flush=True)
    except Exception as e1:
        print(f"  [Diarisation] torchaudio failed ({e1}), trying soundfile...", flush=True)
        # Try soundfile + torch
        try:
            import soundfile as sf
            import numpy as np
            data, sample_rate = sf.read(audio_path, dtype="float32", always_2d=True)
            waveform = torch.from_numpy(data.T)  # (channels, time)
            audio_input = {"waveform": waveform, "sample_rate": sample_rate}
            print(f"  [Diarisation] Audio loaded via soundfile: {waveform.shape}, {sample_rate}Hz", flush=True)
        except Exception as e2:
            print(f"  [Diarisation] soundfile failed ({e2}), passing path directly", flush=True)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if audio_input is not None:
            diarisation_result = pipeline(audio_input)
        else:
            diarisation_result = pipeline(audio_path)

    print("  [Diarisation] Speaker analysis complete.", flush=True)

    # Build speaker label map
    label_map = _assign_speaker_labels(diarisation_result)
    print(f"  [Diarisation] Speaker mapping: {label_map}", flush=True)

    # Align Whisper segments with diarisation
    diarised_segments = []
    for seg in whisper_segments:
        # Use midpoint of segment to determine speaker
        midpoint = (seg["start"] + seg["end"]) / 2
        speaker = _get_speaker_at_time(diarisation_result, midpoint, label_map)

        text = seg["text"].strip()
        if not text:
            continue

        diarised_segments.append({
            "speaker": speaker,
            "text": text,
            "start_time": round(seg["start"], 2),
            "end_time": round(seg["end"], 2),
        })

    # Merge consecutive segments from the same speaker
    diarised_segments = _merge_consecutive(diarised_segments)

    # Save diarised transcript
    diarised_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "diarised"
    )
    os.makedirs(diarised_dir, exist_ok=True)
    base_name = Path(audio_path).stem
    diarised_path = os.path.join(diarised_dir, f"{base_name}_diarised.json")

    with open(diarised_path, "w", encoding="utf-8") as f:
        json.dump(diarised_segments, f, indent=2)

    print(f"  [Diarisation] {len(diarised_segments)} segments saved to: {diarised_path}", flush=True)
    return diarised_segments


def _merge_consecutive(segments: list[dict]) -> list[dict]:
    """
    Merge consecutive segments from the same speaker into one.
    Reduces noise from short Whisper segments being split unnecessarily.
    """
    if not segments:
        return segments

    merged = [segments[0].copy()]
    for seg in segments[1:]:
        last = merged[-1]
        if seg["speaker"] == last["speaker"]:
            last["text"] = last["text"].rstrip() + " " + seg["text"].lstrip()
            last["end_time"] = seg["end_time"]
        else:
            merged.append(seg.copy())

    return merged


def format_diarised_transcript(diarised_segments: list[dict]) -> str:
    """
    Format diarised segments into a readable transcript string.
    Used as input to the LangGraph agents.

    Output format:
        AGENT: Good morning, thank you for calling...
        CUSTOMER: Hi, I wanted to ask about...
    """
    lines = []
    for seg in diarised_segments:
        speaker = seg.get("speaker", "UNKNOWN")
        text = seg.get("text", "").strip()
        if text:
            lines.append(f"{speaker}: {text}")
    return "\n".join(lines)
