#!/usr/bin/env python3
"""
YouTube Video Transcription and Summarization Tool

This script downloads YouTube videos as MP3, transcribes them using NVIDIA Parakeet,
and generates summaries using either DeepSeek API or local Ollama models.
"""

import argparse
import os
import subprocess
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

try:
    import nemo.collections.asr as nemo_asr
except ImportError:
    print("Warning: nemo_toolkit not installed. Please install with: pip install -U nemo_toolkit[\"asr\"]")
    nemo_asr = None


def download_audio(url: str, output_dir: str = ".") -> str:
    """
    Download YouTube video as MP3 using yt-dlp

    Args:
        url: YouTube video URL
        output_dir: Directory to save the audio file

    Returns:
        Path to the downloaded MP3 file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use timestamp in filename to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_template = f"{output_dir}/%(title)s_{timestamp}.%(ext)s"

    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "-o", output_template,
        url
    ]

    print(f"Downloading audio from: {url}")
    try:
        subprocess.run(cmd, check=True)

        # Find the downloaded file
        mp3_files = list(output_dir.glob(f"*_{timestamp}.mp3"))
        if mp3_files:
            return str(mp3_files[0])
        else:
            raise FileNotFoundError("Downloaded MP3 file not found")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to download audio: {e}")


def convert_to_wav(mp3_path: str) -> str:
    """
    Convert MP3 file to WAV format for Parakeet

    Args:
        mp3_path: Path to the MP3 file

    Returns:
        Path to the converted WAV file
    """
    mp3_path = Path(mp3_path)
    wav_path = mp3_path.with_suffix(".wav")

    print(f"Converting {mp3_path} to WAV format...")

    # Use ffmpeg to convert MP3 to WAV with 16kHz sample rate
    cmd = ["ffmpeg", "-i", str(mp3_path), "-ac", "1", "-ar", "16000", "-y", str(wav_path)]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        if wav_path.exists():
            print(f"Converted to: {wav_path}")
            return str(wav_path)
        else:
            raise FileNotFoundError(f"Converted WAV file not found: {wav_path}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to convert audio to WAV: {e}")


def transcribe_audio(mp3_path: str) -> str:
    """
    Transcribe audio file using NVIDIA Parakeet

    Args:
        mp3_path: Path to the MP3 file

    Returns:
        Path to the transcription text file
    """
    if nemo_asr is None:
        raise RuntimeError("nemo_toolkit not installed. Please install with: pip install -U nemo_toolkit[\"asr\"]")

    mp3_path = Path(mp3_path)
    txt_path = mp3_path.with_suffix(".txt")

    print(f"Transcribing audio using NVIDIA Parakeet: {mp3_path}")

    try:
        # Convert MP3 to WAV format
        wav_path = convert_to_wav(mp3_path)

        # Load Parakeet model
        print("Loading NVIDIA Parakeet TDT 0.6B v2 model...")
        asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v2")

        # Transcribe audio
        print("Transcribing audio...")
        output = asr_model.transcribe([wav_path])

        if output and len(output) > 0:
            transcription = output[0].text

            # Save transcription to file
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(transcription)

            print(f"Transcription saved to: {txt_path}")

            # Clean up temporary WAV file
            if os.path.exists(wav_path):
                os.remove(wav_path)
                print(f"Removed temporary WAV file: {wav_path}")

            return str(txt_path)
        else:
            raise RuntimeError("No transcription output received from Parakeet")

    except Exception as e:
        raise RuntimeError(f"Failed to transcribe audio with Parakeet: {e}")


def generate_summary_deepseek(transcription_path: str, api_key: str) -> str:
    """
    Generate summary using DeepSeek API

    Args:
        transcription_path: Path to the transcription text file
        api_key: DeepSeek API key

    Returns:
        Path to the summary markdown file
    """
    transcription_path = Path(transcription_path)
    md_path = transcription_path.with_suffix(".md")

    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription = f.read()

    # Calculate approximate token count (rough estimate: 1 token ≈ 4 characters)
    estimated_tokens = len(transcription) // 4

    # DeepSeek models typically have 32k-128k token context windows
    # Only warn if transcript is extremely long
    if estimated_tokens > 100000:
        print(f"Warning: Transcript is very long (~{estimated_tokens:,} tokens). DeepSeek may truncate very long content.")

    prompt = f"""Please provide a comprehensive summary of the following transcribed content.
Focus on the main points, key insights, and important details:

{transcription}

Summary:"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }

    print("Generating summary using DeepSeek API...")
    print(f"Transcript length: {len(transcription):,} characters (~{estimated_tokens:,} tokens)")

    try:
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()

        summary = response.json()["choices"][0]["message"]["content"]

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"Summary saved to: {md_path}")
        return str(md_path)

    except requests.RequestException as e:
        raise RuntimeError(f"Failed to generate summary with DeepSeek: {e}")


def generate_summary_ollama(transcription_path: str, model: str = "qwen3:32b") -> str:
    """
    Generate summary using local Ollama model

    Args:
        transcription_path: Path to the transcription text file
        model: Ollama model name

    Returns:
        Path to the summary markdown file
    """
    transcription_path = Path(transcription_path)
    md_path = transcription_path.with_suffix(".md")

    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription = f.read()

    # Calculate approximate token count (rough estimate: 1 token ≈ 4 characters)
    # Most modern models have context windows of 32k-128k tokens
    estimated_tokens = len(transcription) // 4

    # Only warn if transcript is extremely long (over 100k tokens)
    if estimated_tokens > 100000:
        print(f"Warning: Transcript is very long (~{estimated_tokens:,} tokens). Consider using a model with larger context window.")

    prompt = f"""Please provide a comprehensive summary of the following transcribed content.
Focus on the main points, key insights, and important details:

{transcription}

Summary:"""

    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "options": {
            "num_ctx": 131072  # Request larger context window (128k tokens)
        }
    }

    print(f"Generating summary using Ollama model: {model}...")
    print(f"Transcript length: {len(transcription):,} characters (~{estimated_tokens:,} tokens)")

    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json=data,
            timeout=300  # Increase timeout for longer transcripts
        )
        response.raise_for_status()

        result = response.json()
        summary = result.get("message", {}).get("content", "")

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"Summary saved to: {md_path}")
        return str(md_path)

    except requests.RequestException as e:
        raise RuntimeError(f"Failed to generate summary with Ollama: {e}")


def check_dependencies():
    """Check if required dependencies are available"""
    # Check if ffmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("ffmpeg not found. Please install ffmpeg to use audio conversion features.")

    # Check if nemo_toolkit is available
    if nemo_asr is None:
        raise RuntimeError("nemo_toolkit not installed. Please install with: pip install -U nemo_toolkit[\"asr\"]")


def main():
    parser = argparse.ArgumentParser(description="YouTube Video Transcription and Summarization Tool")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--output-dir", "-o", default="transcripts", help="Output directory (default: transcripts/)")
    parser.add_argument("--model", choices=["deepseek", "ollama"], default="deepseek",
                       help="Summary model to use (default: deepseek)")
    parser.add_argument("--ollama-model", default="qwen3:32b",
                       help="Ollama model name (default: qwen3:32b)")

    args = parser.parse_args()

    try:
        # Check dependencies
        check_dependencies()

        # Step 1: Download audio
        mp3_path = download_audio(args.url, args.output_dir)

        # Step 2: Transcribe audio
        txt_path = transcribe_audio(mp3_path)

        # Step 3: Generate summary
        if args.model == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY environment variable not set")
            md_path = generate_summary_deepseek(txt_path, api_key)
        else:
            md_path = generate_summary_ollama(txt_path, args.ollama_model)

        # Step 4: Clean up intermediate files
        print("\nCleaning up intermediate files...")
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
            print(f"Removed: {mp3_path}")
        if os.path.exists(txt_path):
            os.remove(txt_path)
            print(f"Removed: {txt_path}")

        print(f"\nProcess completed successfully!")
        print(f"Summary saved to: {md_path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()