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
from pathlib import Path

# Import from our new modules
from config import load_config, save_config, save_link_to_history
from download import get_video_title, download_subtitles, download_audio, convert_srt_to_text
from transcription import transcribe_audio
from summarization import generate_summary_deepseek, generate_summary_ollama, generate_summary_extractive

try:
    import nemo.collections.asr as nemo_asr
except ImportError:
    print("Warning: nemo_toolkit not installed. Please install with: pip install -U nemo_toolkit[\"asr\"]")
    nemo_asr = None


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
    parser = argparse.ArgumentParser(description="Transcribe and summarize YouTube videos")
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

    args = parser.parse_args()

    # Handle configuration management
    if args.set_api_key:
        config = load_config()
        config["deepseek_api_key"] = args.set_api_key
        save_config(config)
        print(f"DeepSeek API key set successfully")
        return

    if args.set_chunk_duration:
        config = load_config()
        config["chunk_duration"] = args.set_chunk_duration
        save_config(config)
        print(f"Default chunk duration set to {args.set_chunk_duration} seconds")
        return

    if args.set_overlap_duration:
        config = load_config()
        config["overlap_duration"] = args.set_overlap_duration
        save_config(config)
        print(f"Default overlap duration set to {args.set_overlap_duration} seconds")
        return

    if args.set_summary_chunk_size:
        config = load_config()
        config["summary_chunk_size"] = args.set_summary_chunk_size
        save_config(config)
        print(f"Default summary chunk size set to {args.set_summary_chunk_size} words")
        return

    if args.show_config:
        config = load_config()
        print("Current configuration:")
        for key, value in config.items():
            if key == "deepseek_api_key" and value:
                print(f"  {key}: {'*' * len(value)}")
            else:
                print(f"  {key}: {value}")
        return

    # Validate URL
    if not args.url:
        parser.error("YouTube URL is required")

    if "youtube.com" not in args.url and "youtu.be" not in args.url:
        parser.error("Please provide a valid YouTube URL")

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
        config = load_config()
        llm_prompt = config.get("llm_prompt")
        llm_model = config.get("llm_model")
        chunk_size = args.summary_chunk_size

        if args.model == "deepseek":
            api_key = config.get("deepseek_api_key")
            if not api_key:
                raise ValueError("DeepSeek API key not set. Use --set-api-key to configure it.")
            md_path = generate_summary_deepseek(txt_path, api_key, chunk_size, llm_prompt, llm_model)
        elif args.model == "extractive":
            use_ollama_formatting = config.get("use_ollama_formatting", True)
            ollama_formatting_model = config.get("ollama_formatting_model", "nous-hermes2-mixtral:latest")
            md_path = generate_summary_extractive(txt_path, chunk_size, use_ollama_formatting, ollama_formatting_model)
        else:
            ollama_model = config.get("ollama_model", args.ollama_model)
            md_path = generate_summary_ollama(txt_path, ollama_model, chunk_size, llm_prompt)

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

        print(f"\n✅ Transcription and summarization complete!")
        print(f"📄 Summary saved to: {md_path}")
        print(f"📁 Output directory: {args.output_dir}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
