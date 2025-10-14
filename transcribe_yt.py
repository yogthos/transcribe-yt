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


def download_subtitles(url: str, output_dir: str = ".") -> str:
    """
    Download YouTube video subtitles using yt-dlp

    Args:
        url: YouTube video URL
        output_dir: Directory to save the subtitle file

    Returns:
        Path to the downloaded subtitle file, or None if no subtitles available
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use timestamp in filename to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_template = f"{output_dir}/%(title)s_{timestamp}.%(ext)s"

    cmd = [
        "yt-dlp",
        "--write-auto-subs",
        "--sub-langs", "en",
        "--sub-format", "srt",
        "--skip-download",
        "--ignore-errors",
        "-o", output_template,
        url
    ]

    print(f"Downloading subtitles from: {url}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"yt-dlp error output: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, cmd, output=result.stdout, stderr=result.stderr)

        # Find the downloaded subtitle file
        subtitle_files = list(output_dir.glob(f"*_{timestamp}.en.srt"))
        if subtitle_files:
            subtitle_path = str(subtitle_files[0])
            print(f"Subtitles downloaded to: {subtitle_path}")
            return subtitle_path
        else:
            print("No subtitles available for this video")
            return None

    except subprocess.CalledProcessError as e:
        print(f"Failed to download subtitles: {e}")
        return None


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


def convert_srt_to_text(srt_path: str) -> str:
    """
    Convert SRT subtitle file to plain text format

    Args:
        srt_path: Path to the SRT subtitle file

    Returns:
        Path to the converted text file
    """
    srt_path = Path(srt_path)
    txt_path = srt_path.with_suffix(".txt")

    print(f"Converting SRT subtitles to text: {srt_path}")

    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()

        # Parse SRT format and extract text
        lines = srt_content.split('\n')
        text_lines = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and timestamp lines
            if not line or line.isdigit() or '-->' in line:
                i += 1
                continue

            # Add text content
            text_lines.append(line)
            i += 1

        # Join text lines with spaces
        text_content = ' '.join(text_lines)

        # Save as text file
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text_content)

        print(f"Converted subtitles to: {txt_path}")
        return str(txt_path)

    except Exception as e:
        raise RuntimeError(f"Failed to convert SRT to text: {e}")


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
Focus on the main points, key insights, and important details. Make sure not to omit details:

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
    parser.add_argument("--force-transcribe", action="store_true",
                       help="Force audio transcription even if subtitles are available")

    args = parser.parse_args()

    try:
        # Check dependencies
        check_dependencies()

        txt_path = None
        mp3_path = None

        # Step 1: Try to download subtitles first (unless forced to transcribe)
        if not args.force_transcribe:
            print("Attempting to download subtitles...")
            srt_path = download_subtitles(args.url, args.output_dir)
            if srt_path:
                txt_path = convert_srt_to_text(srt_path)
                print("✓ Using subtitles instead of audio transcription")

        # Step 2: If no subtitles available or forced transcription, download and transcribe audio
        if txt_path is None:
            print("No subtitles available, falling back to audio transcription...")
            mp3_path = download_audio(args.url, args.output_dir)
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
        if mp3_path and os.path.exists(mp3_path):
            os.remove(mp3_path)
            print(f"Removed: {mp3_path}")
        if txt_path and os.path.exists(txt_path):
            os.remove(txt_path)
            print(f"Removed: {txt_path}")

        print(f"\nProcess completed successfully!")
        print(f"Summary saved to: {md_path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()