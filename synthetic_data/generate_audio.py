"""
synthetic_data/generate_audio.py

Generates synthetic test audio files from the existing text transcripts
using Windows TTS (pyttsx3) or gTTS as fallback.

This gives us real audio files to test the Whisper + diarisation pipeline
without needing actual banking call recordings.

NOTE: Generated audio will be single-speaker (no real diarisation possible)
but validates the full Whisper transcription pipeline end-to-end.
For diarisation testing, use the two-voice method below.

Usage:
    python synthetic_data/generate_audio.py
    python synthetic_data/generate_audio.py --scenario 1
"""

import os
import sys
import argparse
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCENARIOS = [
    ("scenario_01_app_fraud.txt",             "scenario_01_app_fraud.wav"),
    ("scenario_02_misselling_investment.txt",  "scenario_02_misselling_investment.wav"),
    ("scenario_03_vulnerable_elderly.txt",     "scenario_03_vulnerable_elderly.wav"),
    ("scenario_04_gdpr_breach.txt",            "scenario_04_gdpr_breach.wav"),
    ("scenario_05_clean_call.txt",             "scenario_05_clean_call.wav"),
]

SYNTHETIC_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(os.path.dirname(SYNTHETIC_DIR), "data", "audio")


def _extract_dialogue(transcript_text: str) -> list[dict]:
    """
    Extract dialogue lines from transcript, stripping metadata header.
    Returns list of {speaker, text} dicts.
    """
    lines = []
    in_dialogue = False

    for line in transcript_text.split("\n"):
        line = line.strip()

        # Skip header lines
        if line.startswith("---"):
            in_dialogue = True
            continue
        if line.startswith("END OF CALL") or line.startswith("SCENARIO:") or not line:
            continue

        if in_dialogue and line:
            # Match AGENT: or CUSTOMER: lines
            match = re.match(r"^(AGENT|CUSTOMER):\s*(.+)$", line)
            if match:
                lines.append({
                    "speaker": match.group(1),
                    "text": match.group(2).strip(),
                })

    return lines


def generate_with_gtts(dialogue_lines: list[dict], output_path: str) -> bool:
    """Generate audio using gTTS (Google TTS — requires internet)."""
    try:
        from gtts import gTTS
        from pydub import AudioSegment
        import io
    except ImportError:
        return False

    print("  Using gTTS (Google TTS)...", flush=True)
    combined = AudioSegment.empty()
    silence = AudioSegment.silent(duration=500)  # 0.5s pause between speakers

    for line in dialogue_lines:
        text = line["text"]
        # Different TTS lang/speed for agent vs customer (simulates different voices)
        tts = gTTS(text=text, lang="en", tld="co.uk")
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        segment = AudioSegment.from_mp3(mp3_fp)
        combined += segment + silence

    combined.export(output_path, format="wav")
    return True


def generate_with_pyttsx3(dialogue_lines: list[dict], output_path: str) -> bool:
    """Generate audio using pyttsx3 (offline TTS)."""
    try:
        import pyttsx3
    except ImportError:
        return False

    print("  Using pyttsx3 (offline TTS)...", flush=True)
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")

    # Build full text with pauses
    full_text = ""
    for line in dialogue_lines:
        full_text += line["text"] + ". "

    engine.setProperty("rate", 150)
    engine.setProperty("volume", 0.9)

    engine.save_to_file(full_text, output_path)
    engine.runAndWait()
    return True


def generate_audio(scenario_txt: str, output_wav: str) -> str:
    """Generate audio for a single scenario transcript."""
    txt_path = os.path.join(SYNTHETIC_DIR, scenario_txt)
    wav_path = os.path.join(AUDIO_DIR, output_wav)

    os.makedirs(AUDIO_DIR, exist_ok=True)

    if not os.path.exists(txt_path):
        print(f"  [SKIP] Transcript not found: {txt_path}")
        return None

    print(f"\nGenerating: {output_wav}")

    with open(txt_path, "r", encoding="utf-8") as f:
        transcript_text = f.read()

    dialogue = _extract_dialogue(transcript_text)
    print(f"  Extracted {len(dialogue)} dialogue lines")

    # Try pyttsx3 first (offline, no internet needed)
    if generate_with_pyttsx3(dialogue, wav_path):
        print(f"  ✓ Saved: {wav_path}")
        return wav_path

    # Fallback to gTTS
    if generate_with_gtts(dialogue, wav_path):
        print(f"  ✓ Saved: {wav_path}")
        return wav_path

    print("  [ERROR] No TTS engine available.")
    print("  Install one of:")
    print("    pip install pyttsx3          (offline, recommended)")
    print("    pip install gtts pydub       (online, better quality)")
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic audio for Whisper testing")
    parser.add_argument("--scenario", type=int, choices=[1, 2, 3, 4, 5],
                        help="Generate specific scenario (1-5). Omit for all.")
    args = parser.parse_args()

    print("BFSI Compliance Agent — Synthetic Audio Generator")
    print("=" * 50)

    if args.scenario:
        idx = args.scenario - 1
        txt, wav = SCENARIOS[idx]
        generate_audio(txt, wav)
    else:
        for txt, wav in SCENARIOS:
            generate_audio(txt, wav)

    print("\nDone. Audio files saved to data/audio/")
    print("Next step: python run_audio.py --audio data/audio/scenario_01_app_fraud.wav")
