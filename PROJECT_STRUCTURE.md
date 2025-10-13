# Project Structure

```
transcribe-yt/
├── transcribe_yt.py          # Main Python script
├── requirements.txt          # Python dependencies
├── setup.sh                 # Automated setup script
├── run_example.sh           # Usage examples
├── test_basic.py            # Basic functionality test
├── README.md                # Comprehensive documentation
├── PROJECT_STRUCTURE.md     # This file
└── plan.md                  # Original implementation plan
```

## File Descriptions

### Core Files
- **`transcribe_yt.py`**: Main script that implements the complete workflow
- **`requirements.txt`**: Python package dependencies (only `requests`)

### Setup & Usage
- **`setup.sh`**: Automated installation script for all dependencies
- **`run_example.sh`**: Shows various usage examples and checks system status
- **`test_basic.py`**: Verifies basic functionality and dependencies

### Documentation
- **`README.md`**: Complete setup and usage instructions
- **`PROJECT_STRUCTURE.md`**: Project overview (this file)
- **`plan.md`**: Original implementation requirements

## Workflow

1. **Setup**: Run `./setup.sh` to install all dependencies
2. **Activate**: Use `source venv/bin/activate` to activate Python environment
3. **Run**: Execute `python3 transcribe_yt.py [OPTIONS] YOUTUBE_URL`
4. **Output**: Get summary markdown file in `transcripts/` folder (intermediate files automatically deleted)

## Dependencies

### System Tools
- `yt-dlp`: YouTube video downloader
- `uvx`: Universal Python runner for WhisperX
- `Python 3.7+`: Runtime environment

### Python Packages
- `requests`: HTTP library for API calls

### Optional
- `Ollama`: Local LLM for summaries
- `DeepSeek API`: Cloud-based LLM for summaries