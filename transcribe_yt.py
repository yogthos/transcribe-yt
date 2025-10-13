#!/usr/bin/env python3
"""
YouTube Video Transcription and Summarization Tool

This script downloads YouTube videos as MP3, transcribes them using WhisperX,
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


def transcribe_audio(mp3_path: str) -> str:
    """
    Transcribe audio file using Whisper

    Args:
        mp3_path: Path to the MP3 file

    Returns:
        Path to the transcription text file
    """
    mp3_path = Path(mp3_path)
    txt_path = mp3_path.with_suffix(".txt")

    print(f"Transcribing audio: {mp3_path}")

    cmd = ["uvx", "whisper", str(mp3_path), "--model", "base", "--output_format", "txt", "--output_dir", str(mp3_path.parent)]

    try:
        subprocess.run(cmd, check=True, timeout=300)

        # Whisper outputs txt file directly
        if txt_path.exists():
            print(f"Transcription saved to: {txt_path}")
            return str(txt_path)
        else:
            raise FileNotFoundError(f"Transcription text file not found: {txt_path}")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to transcribe audio: {e}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Transcription timed out after 5 minutes")


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