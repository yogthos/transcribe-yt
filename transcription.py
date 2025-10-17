#!/usr/bin/env python3
"""
Audio transcription functionality for Transcribe YouTube
"""

import os
import subprocess
from pathlib import Path

try:
    import nemo.collections.asr as nemo_asr
except ImportError:
    print("Warning: nemo_toolkit not installed. Please install with: pip install -U nemo_toolkit[\"asr\"]")
    nemo_asr = None


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
