#!/usr/bin/env python3
"""
YouTube download and subtitle handling for Transcribe YouTube
"""

import subprocess
from datetime import datetime
from pathlib import Path


def get_video_title(url: str) -> str:
    """
    Extract video title from YouTube URL using yt-dlp

    Args:
        url: YouTube video URL

    Returns:
        Video title or "Unknown Title" if extraction fails
    """
    try:
        cmd = [
            "yt-dlp",
            "--get-title",
            "--no-warnings",
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            return "Unknown Title"
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return "Unknown Title"


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
