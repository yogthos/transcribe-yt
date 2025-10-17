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


def get_config_path():
    """Get the path to the configuration file"""
    return os.path.expanduser("~/.transcribe-yt/config.json")


def load_config():
    """Load configuration from ~/.transcribe-yt/config.json"""
    config_path = get_config_path()
    default_config = {
        "deepseek_api_key": None,
        "ollama_model": "vicuna:7b",
        "ollama_formatting_model": "nous-hermes2-mixtral:latest",
        "use_ollama_formatting": True,
        "chunk_duration": 300,
        "overlap_duration": 30,
        "summary_chunk_size": None,  # None means no chunking, 0 means full text
        "link_history": []
    }

    if not os.path.exists(config_path):
        return default_config

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # Merge with defaults to ensure all keys exist
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load config file: {e}")
        return default_config


def save_config(config):
    """Save configuration to ~/.transcribe-yt/config.json"""
    config_path = get_config_path()
    config_dir = os.path.dirname(config_path)

    # Create config directory if it doesn't exist
    Path(config_dir).mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        print(f"Configuration saved to: {config_path}")
    except IOError as e:
        raise RuntimeError(f"Could not save config file: {e}")


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


def save_link_to_history(url: str, title: str = None):
    """
    Save a link to the history in the config file

    Args:
        url: YouTube video URL
        title: Video title (will be extracted if not provided)
    """
    if title is None:
        title = get_video_title(url)

    config = load_config()

    # Create new history entry
    history_entry = {
        "id": str(int(datetime.now().timestamp())),
        "url": url,
        "title": title,
        "timestamp": datetime.now().isoformat()
    }

    # Add to beginning of history (most recent first)
    if "link_history" not in config:
        config["link_history"] = []

    config["link_history"].insert(0, history_entry)

    # Limit history to last 50 entries
    config["link_history"] = config["link_history"][:50]

    save_config(config)
    return history_entry


def load_link_history():
    """
    Load link history from config

    Returns:
        List of history entries
    """
    config = load_config()
    return config.get("link_history", [])


def remove_link_from_history(link_id: str):
    """
    Remove a link from history by ID

    Args:
        link_id: ID of the link to remove
    """
    config = load_config()
    if "link_history" in config:
        config["link_history"] = [entry for entry in config["link_history"] if entry.get("id") != link_id]
        save_config(config)


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


def transcribe_audio(mp3_path: str, chunk_duration: int = 300, overlap_duration: int = 30) -> str:
    """
    Transcribe audio file using NVIDIA Parakeet with memory optimization for large files

    Args:
        mp3_path: Path to the MP3 file
        chunk_duration: Duration of each audio chunk in seconds (default: 300s = 5min)
        overlap_duration: Overlap between chunks in seconds (default: 30s)

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

        # Check audio duration to determine if chunking is needed
        import librosa
        duration = librosa.get_duration(path=wav_path)
        print(f"Audio duration: {duration:.2f} seconds")

        # Load Parakeet model
        print("Loading NVIDIA Parakeet TDT 0.6B v2 model...")
        asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v2")

        # Configure model for memory optimization
        if hasattr(asr_model, 'cfg') and hasattr(asr_model.cfg, 'model'):
            # Set batch size to 1 to minimize memory usage
            asr_model.cfg.model.batch_size = 1
            # Enable local attention if available
            if hasattr(asr_model.cfg.model, 'encoder'):
                if hasattr(asr_model.cfg.model.encoder, 'local_attention'):
                    asr_model.cfg.model.encoder.local_attention = True
                if hasattr(asr_model.cfg.model.encoder, 'local_attention_context_size'):
                    asr_model.cfg.model.encoder.local_attention_context_size = 1024

        # Determine if we need to chunk the audio
        if duration > chunk_duration:
            print(f"Large audio file detected ({duration:.2f}s). Using chunked processing...")
            transcription = transcribe_audio_chunked(wav_path, asr_model, chunk_duration, overlap_duration)
        else:
            print("Transcribing audio in single pass...")
            output = asr_model.transcribe([wav_path])
            if output and len(output) > 0:
                transcription = output[0].text
            else:
                raise RuntimeError("No transcription output received from Parakeet")

        # Save transcription to file
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(transcription)

        print(f"Transcription saved to: {txt_path}")

        # Clean up temporary WAV file
        if os.path.exists(wav_path):
            os.remove(wav_path)
            print(f"Removed temporary WAV file: {wav_path}")

        return str(txt_path)

    except Exception as e:
        raise RuntimeError(f"Failed to transcribe audio with Parakeet: {e}")


def transcribe_audio_chunked(wav_path: str, asr_model, chunk_duration: int, overlap_duration: int) -> str:
    """
    Transcribe audio in chunks to manage memory usage for large files

    Args:
        wav_path: Path to the WAV file
        asr_model: Loaded ASR model
        chunk_duration: Duration of each chunk in seconds
        overlap_duration: Overlap between chunks in seconds

    Returns:
        Complete transcription text
    """
    import librosa
    import numpy as np

    # Load audio
    audio, sr = librosa.load(wav_path, sr=None)
    duration = len(audio) / sr

    print(f"Processing {duration:.2f}s audio in {chunk_duration}s chunks with {overlap_duration}s overlap")

    transcriptions = []
    chunk_samples = chunk_duration * sr
    overlap_samples = overlap_duration * sr

    start_sample = 0
    chunk_num = 0

    while start_sample < len(audio):
        end_sample = min(start_sample + chunk_samples, len(audio))
        chunk_audio = audio[start_sample:end_sample]

        # Save chunk to temporary file
        chunk_path = f"{wav_path}_chunk_{chunk_num}.wav"
        import soundfile as sf
        sf.write(chunk_path, chunk_audio, sr)

        try:
            print(f"Processing chunk {chunk_num + 1} ({start_sample/sr:.2f}s - {end_sample/sr:.2f}s)...")

            # Transcribe chunk
            output = asr_model.transcribe([chunk_path])

            if output and len(output) > 0:
                chunk_text = output[0].text.strip()
                if chunk_text:
                    transcriptions.append(chunk_text)
                    print(f"Chunk {chunk_num + 1} transcribed: {len(chunk_text)} characters")
                else:
                    print(f"Chunk {chunk_num + 1} produced empty transcription")
            else:
                print(f"Chunk {chunk_num + 1} failed to transcribe")

        except Exception as e:
            print(f"Error transcribing chunk {chunk_num + 1}: {e}")

        finally:
            # Clean up chunk file
            if os.path.exists(chunk_path):
                os.remove(chunk_path)

        # Move to next chunk with overlap
        start_sample = end_sample - overlap_samples
        chunk_num += 1

        # Prevent infinite loop
        if start_sample >= len(audio) - overlap_samples:
            break

    # Combine all transcriptions
    full_transcription = " ".join(transcriptions)
    print(f"Combined transcription: {len(full_transcription)} characters from {len(transcriptions)} chunks")

    return full_transcription


def chunk_text(text: str, chunk_size: int) -> list:
    """
    Split text into chunks of approximately chunk_size words, breaking at sentence boundaries

    Args:
        text: Text to chunk
        chunk_size: Target number of words per chunk

    Returns:
        List of text chunks
    """
    import re

    # Split text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = []
    current_word_count = 0

    for sentence in sentences:
        sentence_words = len(sentence.split())

        # If adding this sentence would exceed chunk size, start a new chunk
        if current_word_count + sentence_words > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_word_count = sentence_words
        else:
            current_chunk.append(sentence)
            current_word_count += sentence_words

    # Add the last chunk if it has content
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def generate_summary_deepseek(transcription_path: str, api_key: str, chunk_size: int = None) -> str:
    """
    Generate summary using DeepSeek API with optional chunking

    Args:
        transcription_path: Path to the transcription text file
        api_key: DeepSeek API key
        chunk_size: Number of words per chunk (None for no chunking)

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

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print("Generating summary using DeepSeek API...")
    print(f"Transcript length: {len(transcription):,} characters (~{estimated_tokens:,} tokens)")

    # If chunk_size is specified, process in chunks
    if chunk_size and chunk_size > 0:
        print(f"Processing transcript in chunks of {chunk_size} words...")
        chunks = chunk_text(transcription, chunk_size)
        print(f"Split into {len(chunks)} chunks")

        chunk_summaries = []

        for i, chunk in enumerate(chunks, 1):
            print(f"Processing chunk {i}/{len(chunks)} ({len(chunk.split())} words)...")

            prompt = f"""Please provide a comprehensive summary of the following transcribed content.
Focus on the main points, key insights, and important details. Make sure not to omit details:

{chunk}

Summary:"""

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

            try:
                response = requests.post(
                    "https://api.deepseek.com/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=60
                )
                response.raise_for_status()

                chunk_summary = response.json()["choices"][0]["message"]["content"]
                chunk_summaries.append(f"## Chunk {i} Summary\n\n{chunk_summary}\n")

            except requests.RequestException as e:
                print(f"Error processing chunk {i}: {e}")
                chunk_summaries.append(f"## Chunk {i} Summary\n\n*Error processing this chunk*\n")

        # Combine all chunk summaries
        final_summary = "# Detailed Summary\n\n" + "\n".join(chunk_summaries)

    else:
        # Process entire transcript at once
        prompt = f"""Please provide a comprehensive summary of the following transcribed content.
Focus on the main points, key insights, and important details. Make sure not to omit details:

{transcription}

Summary:"""

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

        try:
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()

            final_summary = response.json()["choices"][0]["message"]["content"]

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to generate summary with DeepSeek: {e}")

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(final_summary)

    print(f"Summary saved to: {md_path}")
    return str(md_path)


def generate_summary_ollama(transcription_path: str, model: str = "vicuna:7b", chunk_size: int = None) -> str:
    """
    Generate summary using local Ollama model with optional chunking

    Args:
        transcription_path: Path to the transcription text file
        model: Ollama model name
        chunk_size: Number of words per chunk (None for no chunking)

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

    print(f"Generating summary using Ollama model: {model}...")
    print(f"Transcript length: {len(transcription):,} characters (~{estimated_tokens:,} tokens)")

    # If chunk_size is specified, process in chunks
    if chunk_size and chunk_size > 0:
        print(f"Processing transcript in chunks of {chunk_size} words...")
        chunks = chunk_text(transcription, chunk_size)
        print(f"Split into {len(chunks)} chunks")

        chunk_summaries = []

        for i, chunk in enumerate(chunks, 1):
            print(f"Processing chunk {i}/{len(chunks)} ({len(chunk.split())} words)...")

            prompt = f"""Please provide a comprehensive summary of the following transcribed content.
Focus on the main points, key insights, and important details:

{chunk}

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

            try:
                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json=data,
                    timeout=300  # Increase timeout for longer transcripts
                )
                response.raise_for_status()

                result = response.json()
                chunk_summary = result.get("message", {}).get("content", "")
                chunk_summaries.append(f"## Chunk {i} Summary\n\n{chunk_summary}\n")

            except requests.RequestException as e:
                print(f"Error processing chunk {i}: {e}")
                chunk_summaries.append(f"## Chunk {i} Summary\n\n*Error processing this chunk*\n")

        # Combine all chunk summaries
        final_summary = "# Detailed Summary\n\n" + "\n".join(chunk_summaries)

    else:
        # Process entire transcript at once
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

        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json=data,
                timeout=300  # Increase timeout for longer transcripts
            )
            response.raise_for_status()

            result = response.json()
            final_summary = result.get("message", {}).get("content", "")

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to generate summary with Ollama: {e}")

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(final_summary)

    print(f"Summary saved to: {md_path}")
    return str(md_path)


def apply_ollama_formatting(summary_text: str, ollama_model: str = "nous-hermes2-mixtral:latest") -> str:
    """
    Format a summary using Ollama to improve readability while preserving all content

    Args:
        summary_text: The summary text to format
        ollama_model: Ollama model to use for formatting

    Returns:
        Formatted summary text
    """
    import requests

    print(f"Formatting summary with Ollama model: {ollama_model}...")

    prompt = f"""Please reformat the following summary text for better readability and organization.
IMPORTANT: Do NOT omit any content or change the meaning. Only improve the formatting, structure, and flow.

SPECIFIC FORMATTING INSTRUCTIONS:
- Add clear headings to organize the content into logical sections
- Break the text into well-structured paragraphs with proper spacing
- Use appropriate heading levels (H1, H2, H3) to create a hierarchical structure
- Ensure each paragraph focuses on one main idea
- Use bullet points or numbered lists where appropriate for clarity
- Maintain all original information and details

Original summary:
{summary_text}

Reformatted summary with headings and paragraph breaks:"""

    data = {
        "model": ollama_model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.3,  # Lower temperature for more consistent formatting
            "num_ctx": 131072
        }
    }

    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json=data,
            timeout=120  # Allow more time for formatting
        )
        response.raise_for_status()

        result = response.json()
        formatted_summary = result.get("message", {}).get("content", "")

        if formatted_summary:
            print("✓ Summary formatted successfully with Ollama")
            return formatted_summary
        else:
            print("⚠️ Ollama returned empty response, using original summary")
            return summary_text

    except requests.RequestException as e:
        print(f"⚠️ Ollama formatting failed: {e}")
        print("Using original summary without formatting")
        return summary_text


def apply_ollama_formatting_if_enabled(summary_text: str, use_ollama_formatting: bool, ollama_formatting_model: str) -> str:
    """
    Apply Ollama formatting if enabled, otherwise return original text

    Args:
        summary_text: The summary text to potentially format
        use_ollama_formatting: Whether to apply Ollama formatting
        ollama_formatting_model: Ollama model to use for formatting

    Returns:
        Formatted summary text if enabled, otherwise original text
    """
    if use_ollama_formatting:
        print("Applying Ollama formatting for improved readability...")
        try:
            formatted_summary = apply_ollama_formatting(summary_text, ollama_formatting_model)
            print("✓ Ollama formatting applied successfully")
            return formatted_summary
        except Exception as e:
            print(f"⚠️ Ollama formatting failed: {e}")
            print("Using original summary without formatting")
            return summary_text
    else:
        return summary_text


def save_summary_to_file(summary_text: str, transcription_path: Path) -> str:
    """
    Save summary text to markdown file

    Args:
        summary_text: The summary text to save
        transcription_path: Path to the original transcription file

    Returns:
        Path to the saved markdown file
    """
    md_path = transcription_path.with_suffix(".md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(summary_text)
    print(f"Summary saved to: {md_path}")
    return str(md_path)


def generate_summary_extractive(transcription_path: str, chunk_size: int = None, use_ollama_formatting: bool = True, ollama_formatting_model: str = "nous-hermes2-mixtral:latest") -> str:
    """
    Generate detailed summary using extractive summarization (selecting important sentences)
    This approach preserves more details and produces longer, more accurate summaries

    Args:
        transcription_path: Path to the transcription text file
        chunk_size: Number of words per chunk (None for no chunking)
        use_ollama_formatting: Whether to use Ollama for post-processing (default: True)
        ollama_formatting_model: Ollama model to use for formatting (default: nous-hermes2-mixtral:latest)

    Returns:
        Path to the summary markdown file
    """
    transcription_path = Path(transcription_path)
    md_path = transcription_path.with_suffix(".md")

    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription = f.read()

    print("Generating detailed summary using extractive summarization...")
    print(f"Transcript length: {len(transcription):,} characters")

    try:
        # Use spaCy for extractive summarization if available
        try:
            import spacy
            from spacy.lang.en.stop_words import STOP_WORDS

            # Load English model
            try:
                nlp = spacy.load("en_core_web_sm")
            except OSError as e:
                print(f"spaCy English model not found: {e}")
                print("Attempting to download the model...")
                import subprocess
                import sys
                try:
                    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
                    nlp = spacy.load("en_core_web_sm")
                    print("spaCy English model downloaded and loaded successfully")
                except subprocess.CalledProcessError as download_error:
                    print(f"Failed to download spaCy model: {download_error}")
                    raise ImportError("spaCy English model not available and could not be downloaded")

            # Process the text
            doc = nlp(transcription)

            # Calculate sentence scores based on word frequency
            word_frequencies = {}
            for word in doc:
                if word.text.lower() not in STOP_WORDS and word.text.lower() not in ['\n', '\t', ' '] and word.pos_ != 'PUNCT':
                    if word.text not in word_frequencies.keys():
                        word_frequencies[word.text] = 1
                    else:
                        word_frequencies[word.text] += 1

            # Normalize frequencies
            max_frequency = max(word_frequencies.values()) if word_frequencies else 1
            for word in word_frequencies.keys():
                word_frequencies[word] = word_frequencies[word] / max_frequency

            # Score sentences
            sentence_scores = {}
            for sent in doc.sents:
                for word in sent:
                    if word.text.lower() in word_frequencies.keys():
                        if sent not in sentence_scores.keys():
                            sentence_scores[sent] = word_frequencies[word.text.lower()]
                        else:
                            sentence_scores[sent] += word_frequencies[word.text.lower()]

            # Select top sentences (aim for ~40% of original text)
            target_sentences = max(3, len(list(doc.sents)) // 3)
            sorted_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)

            # Select top sentences
            selected_sentences = []
            for sent, score in sorted_sentences[:target_sentences]:
                selected_sentences.append(sent.text.strip())

            # Create summary
            final_summary = "# Detailed Summary\n\n" + " ".join(selected_sentences)

        except ImportError:
            # Fallback to simple sentence selection if spaCy is not available
            print("spaCy not available, using simple extractive summarization...")

            import re

            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', transcription)

            # Simple scoring based on sentence length and keywords
            def score_sentence(sentence):
                # Score based on length (longer sentences often contain more information)
                length_score = len(sentence.split()) / 20.0

                # Score based on important keywords
                keywords = ['important', 'key', 'main', 'primary', 'significant', 'major',
                           'conclusion', 'summary', 'overview', 'discuss', 'explain', 'describe']
                keyword_score = sum(1 for keyword in keywords if keyword in sentence.lower()) * 2

                return length_score + keyword_score

            # Score all sentences
            scored_sentences = [(sentence, score_sentence(sentence)) for sentence in sentences if len(sentence.split()) > 5]

            # Select top sentences (~40% of original)
            target_sentences = max(3, len(scored_sentences) // 3)
            sorted_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)

            # Select top sentences
            selected_sentences = [sentence for sentence, score in sorted_sentences[:target_sentences]]

            # Create summary
            final_summary = "# Detailed Summary\n\n" + " ".join(selected_sentences)

        # Apply Ollama formatting for improved readability if requested
        final_summary = apply_ollama_formatting_if_enabled(final_summary, use_ollama_formatting, ollama_formatting_model)

        return save_summary_to_file(final_summary, transcription_path)

    except Exception as e:
        raise RuntimeError(f"Failed to generate extractive summary: {e}")


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
    parser.add_argument("url", nargs="?", help="YouTube video URL")
    parser.add_argument("--output-dir", "-o", default="~/.transcribe-yt/transcripts", help="Output directory (default: ~/.transcribe-yt/transcripts)")
    parser.add_argument("--model", choices=["deepseek", "ollama", "extractive"], default="extractive",
                       help="Summary model to use (default: extractive)")
    parser.add_argument("--ollama-model", default="vicuna:7b",
                       help="Ollama model name (default: vicuna:7b)")
    parser.add_argument("--force-transcribe", action="store_true",
                       help="Force audio transcription even if subtitles are available")

    # Memory optimization options
    config = load_config()
    parser.add_argument("--chunk-duration", type=int, default=config.get("chunk_duration", 300),
                       help="Audio chunk duration in seconds for large files (default: 300)")
    parser.add_argument("--overlap-duration", type=int, default=config.get("overlap_duration", 30),
                       help="Overlap between audio chunks in seconds (default: 30)")
    parser.add_argument("--summary-chunk-size", type=int, default=config.get("summary_chunk_size"),
                       help="Summary chunk size in words (default: None for no chunking)")

    # Configuration management options
    parser.add_argument("--set-api-key", help="Set DeepSeek API key in configuration")
    parser.add_argument("--set-chunk-duration", type=int, help="Set default chunk duration in configuration")
    parser.add_argument("--set-overlap-duration", type=int, help="Set default overlap duration in configuration")
    parser.add_argument("--set-summary-chunk-size", type=int, help="Set default summary chunk size in configuration")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")
    parser.add_argument("--config-dir", help="Show configuration directory path")

    args = parser.parse_args()

    # Handle configuration management commands
    if args.set_api_key:
        config = load_config()
        config["deepseek_api_key"] = args.set_api_key
        save_config(config)
        print("DeepSeek API key saved to configuration")
        return


    if args.set_chunk_duration:
        config = load_config()
        config["chunk_duration"] = args.set_chunk_duration
        save_config(config)
        print(f"Chunk duration set to {args.set_chunk_duration} seconds")
        return

    if args.set_overlap_duration:
        config = load_config()
        config["overlap_duration"] = args.set_overlap_duration
        save_config(config)
        print(f"Overlap duration set to {args.set_overlap_duration} seconds")
        return

    if args.set_summary_chunk_size:
        config = load_config()
        config["summary_chunk_size"] = args.set_summary_chunk_size
        save_config(config)
        print(f"Summary chunk size set to {args.set_summary_chunk_size} words")
        return

    if args.show_config:
        config = load_config()
        print("Current configuration:")
        for key, value in config.items():
            if key == "deepseek_api_key" and value:
                # Mask the API key for security
                masked_value = value[:8] + "*" * (len(value) - 8) if len(value) > 8 else "*" * len(value)
                print(f"  {key}: {masked_value}")
            else:
                print(f"  {key}: {value}")
        return

    if args.config_dir:
        print(f"Configuration directory: {os.path.dirname(get_config_path())}")
        return

    # Require URL for main functionality
    if not args.url:
        parser.error("YouTube video URL is required for transcription")

    # Expand the output directory path and ensure it exists
    output_dir = os.path.expanduser(args.output_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    args.output_dir = output_dir

    try:
        # Check dependencies
        check_dependencies()

        # Save link to history
        print("Saving link to history...")
        save_link_to_history(args.url)

        txt_path = None
        mp3_path = None
        srt_path = None

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
            txt_path = transcribe_audio(mp3_path, args.chunk_duration, args.overlap_duration)

        # Step 3: Generate summary
        if args.model == "deepseek":
            config = load_config()
            api_key = config.get("deepseek_api_key")
            if not api_key:
                raise ValueError("DeepSeek API key not set. Use --set-api-key to configure it.")
            chunk_size = args.summary_chunk_size
            md_path = generate_summary_deepseek(txt_path, api_key, chunk_size)
        elif args.model == "extractive":
            chunk_size = args.summary_chunk_size
            md_path = generate_summary_extractive(txt_path, chunk_size)
        else:
            config = load_config()
            ollama_model = config.get("ollama_model", args.ollama_model)
            chunk_size = args.summary_chunk_size
            md_path = generate_summary_ollama(txt_path, ollama_model, chunk_size)

        # Step 4: Clean up intermediate files
        print("\nCleaning up intermediate files...")
        if mp3_path and os.path.exists(mp3_path):
            os.remove(mp3_path)
            print(f"Removed: {mp3_path}")
        if srt_path and os.path.exists(srt_path):
            os.remove(srt_path)
            print(f"Removed: {srt_path}")
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