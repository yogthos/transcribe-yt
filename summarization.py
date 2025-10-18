#!/usr/bin/env python3
"""
Summarization functionality for Transcribe YouTube
"""

import requests
from pathlib import Path
from transcription import chunk_text


def generate_summary_deepseek(transcription_path: str, api_key: str, chunk_size: int = None, llm_prompt: str = None, llm_model: str = None) -> str:
    """
    Generate summary using DeepSeek API with optional chunking

    Args:
        transcription_path: Path to the transcription text file
        api_key: DeepSeek API key
        chunk_size: Number of words per chunk (None for no chunking)
        llm_prompt: Custom prompt template (uses {content} placeholder)
        llm_model: Model name to use (default: deepseek-chat)

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

    # Set default values
    if llm_prompt is None:
        llm_prompt = "Please provide a comprehensive summary of the following transcribed content.\nFocus on the main points, key insights, and important details. Make sure not to omit details:\n\n{content}\n\nSummary:"
    if llm_model is None:
        llm_model = "deepseek-chat"

    # If chunk_size is specified, process in chunks
    if chunk_size and chunk_size > 0:
        print(f"Processing transcript in chunks of {chunk_size} words...")
        chunks = chunk_text(transcription, chunk_size)
        print(f"Split into {len(chunks)} chunks")

        chunk_summaries = []

        for i, chunk in enumerate(chunks, 1):
            print(f"Processing chunk {i}/{len(chunks)} ({len(chunk.split())} words)...")

            prompt = llm_prompt.format(content=chunk)

            data = {
                "model": llm_model,
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
        prompt = llm_prompt.format(content=transcription)

        data = {
            "model": llm_model,
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


def generate_summary_ollama(transcription_path: str, model: str = "vicuna:7b", chunk_size: int = None, llm_prompt: str = None) -> str:
    """
    Generate summary using local Ollama model with optional chunking

    Args:
        transcription_path: Path to the transcription text file
        model: Ollama model name
        chunk_size: Number of words per chunk (None for no chunking)
        llm_prompt: Custom prompt template (uses {content} placeholder)

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

    # Set default prompt if not provided
    if llm_prompt is None:
        llm_prompt = "Please provide a comprehensive summary of the following transcribed content.\nFocus on the main points, key insights, and important details:\n\n{content}\n\nSummary:"

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

            prompt = llm_prompt.format(content=chunk)

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
        prompt = llm_prompt.format(content=transcription)

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
