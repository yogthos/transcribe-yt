# Project Structure

```
transcribe-yt/
├── Core Application
│   ├── transcribe_yt.py          # Main application driver (~189 lines)
│   ├── config.py                 # Configuration and link history management
│   ├── download.py               # YouTube download and subtitle handling
│   ├── transcription.py          # Audio transcription with NVIDIA Parakeet
│   ├── summarization.py          # Summary generation (DeepSeek, Ollama, extractive)
│   └── transcribe_yt_gui.py      # GTK-based graphical interface
│
├── Build System
│   ├── build_app.py              # Main build script for macOS app bundles
│   ├── build_minimal.py          # Minimal build for testing
│   ├── build_minimal_core.py     # Core functionality build
│   ├── build.sh                  # Build automation script
│   └── TranscribeYouTube_minimal.spec  # PyInstaller spec file
│
├── Scripts & Automation
│   ├── setup.sh                  # Automated setup script
│   ├── gui.sh                    # GUI launcher script
│   ├── run_gui.py                # GUI entry point
│   ├── test_basic.py             # Basic functionality test
│   └── run_example.sh            # Usage examples
│
├── Dependencies
│   ├── requirements.txt           # Python dependencies
│   ├── requirements_build.txt    # Build-specific dependencies
│   └── venv/                     # Virtual environment
│
├── Documentation
│   ├── README.md                 # Comprehensive documentation
│   └── PROJECT_STRUCTURE.md      # This file
│
└── Output
    └── dist/                     # Built app bundles
```

## Core Modules

### `transcribe_yt.py` - Main Application Driver
- **Purpose**: Orchestrates the complete workflow
- **Size**: ~189 lines (down from 1171 lines)
- **Responsibilities**: Command-line interface, workflow coordination
- **Dependencies**: Imports from all other modules

### `config.py` - Configuration Management
- **Purpose**: Handles configuration and link history
- **Functions**: `load_config()`, `save_config()`, `save_link_to_history()`, etc.
- **File**: `~/.transcribe-yt/config.json`

### `download.py` - YouTube Download & Subtitles
- **Purpose**: Downloads YouTube content and subtitles
- **Functions**: `download_audio()`, `download_subtitles()`, `convert_srt_to_text()`, etc.
- **Dependencies**: `yt-dlp`, `ffmpeg`

### `transcription.py` - Audio Transcription
- **Purpose**: Transcribes audio using NVIDIA Parakeet
- **Functions**: `transcribe_audio()`, `transcribe_audio_chunked()`, `chunk_text()`, etc.
- **Dependencies**: `nemo_toolkit`, `librosa`, `soundfile`

### `summarization.py` - Summary Generation
- **Purpose**: Generates summaries using multiple methods
- **Functions**: `generate_summary_deepseek()`, `generate_summary_ollama()`, `generate_summary_extractive()`, etc.
- **Dependencies**: `requests`, `spacy`, `beautifulsoup4`

### `transcribe_yt_gui.py` - Graphical Interface
- **Purpose**: GTK-based GUI with keyboard shortcuts
- **Features**: Link history, transcription list, rich text display
- **Shortcuts**: Cmd+Q (quit), Cmd+C (copy), Cmd+V (paste), etc.

## Build System

### `build_app.py` - Main Build Script
- **Purpose**: Creates macOS app bundles
- **Features**: GTK dependency copying, code signing
- **Output**: `dist/TranscribeYouTube.app`

### `build_minimal.py` - Minimal Build
- **Purpose**: Lightweight build for testing
- **Features**: Core functionality only
- **Use Case**: Development and testing

### `build_minimal_core.py` - Core Build
- **Purpose**: Essential functionality build
- **Features**: Minimal dependencies
- **Use Case**: Production deployment

## Workflow

### Development
1. **Setup**: `./setup.sh` installs all dependencies
2. **Activate**: `source venv/bin/activate` activates environment
3. **Test**: `python3 test_basic.py` verifies functionality
4. **Run**: `./gui.sh` or `python3 transcribe_yt.py [URL]`

### Building
1. **Main Build**: `./build.sh` creates production app
2. **Minimal Build**: `python3 build_minimal.py` for testing
3. **Output**: `dist/TranscribeYouTube.app` ready for distribution

## Dependencies

### System Tools
- `yt-dlp`: YouTube video downloader
- `ffmpeg`: Audio/video processing
- `gtk+3`: GUI framework (macOS)
- `Python 3.7+`: Runtime environment

### Python Packages
- `nemo_toolkit`: NVIDIA Parakeet transcription
- `librosa`: Audio processing
- `requests`: HTTP client for APIs
- `spacy`: Natural language processing
- `PyGObject`: GTK bindings
- `markdown`: Text formatting
- `beautifulsoup4`: HTML parsing

### Optional
- `Ollama`: Local LLM for summaries
- `DeepSeek API`: Cloud-based LLM for summaries

## Benefits of Modular Architecture

### Maintainability
- **Single Responsibility**: Each module has one clear purpose
- **Easy Navigation**: Find functionality quickly
- **Clean Interfaces**: Clear module boundaries

### Testability
- **Unit Testing**: Test individual modules
- **Integration Testing**: Test module interactions
- **Mocking**: Replace dependencies easily

### Reusability
- **Import Modules**: Use in other projects
- **Standalone Functions**: Import specific functionality
- **API Design**: Clean function interfaces

### Development
- **Parallel Work**: Multiple developers can work on different modules
- **Debugging**: Isolate issues to specific modules
- **Documentation**: Module-specific documentation

## File Sizes (Before vs After Refactoring)

| File | Before | After | Reduction |
|------|--------|-------|-----------|
| `transcribe_yt.py` | 1171 lines | 189 lines | 84% |
| Total Core Files | 1171 lines | 5 modules | Modular |
| Maintainability | Difficult | Easy | ✅ |
| Testability | Hard | Simple | ✅ |
| Reusability | Limited | High | ✅ |