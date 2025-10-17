#!/usr/bin/env python3
"""
Configuration management for Transcribe YouTube
"""

import os
import json
from pathlib import Path
from datetime import datetime


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


def save_link_to_history(url: str, title: str = None):
    """
    Save a link to the history in the configuration file

    Args:
        url: YouTube URL to save
        title: Optional title for the link
    """
    config = load_config()

    # Generate a unique ID for this link
    import uuid
    link_id = str(uuid.uuid4())

    # Get title if not provided
    if title is None:
        from download import get_video_title
        title = get_video_title(url)

    # Create history entry
    history_entry = {
        "id": link_id,
        "url": url,
        "title": title,
        "timestamp": datetime.now().isoformat()
    }

    # Add to history (most recent first)
    if "link_history" not in config:
        config["link_history"] = []

    config["link_history"].insert(0, history_entry)

    # Keep only the last 50 entries
    config["link_history"] = config["link_history"][:50]

    save_config(config)
    print(f"Link saved to history: {title}")


def load_link_history():
    """
    Load link history from configuration

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
        config["link_history"] = [
            entry for entry in config["link_history"]
            if entry.get("id") != link_id
        ]
        save_config(config)
        print(f"Link {link_id} removed from history")
