#!/usr/bin/env python3
"""
Basic test script to verify the transcribe_yt.py structure works
"""

import subprocess
import sys

def test_help():
    """Test that the help command works"""
    try:
        result = subprocess.run(
            [sys.executable, "transcribe_yt.py", "--help"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ Help command works")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Help command failed: {e}")
        return False

def test_dependencies():
    """Test that required dependencies are available"""
    dependencies = ["yt-dlp", "uvx"]
    all_available = True

    for dep in dependencies:
        try:
            subprocess.run([dep, "--version"], capture_output=True, check=True)
            print(f"✓ {dep} is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"✗ {dep} is not available")
            all_available = False

    return all_available

def main():
    print("Testing YouTube Transcription Tool...")
    print("=" * 50)

    tests_passed = 0
    total_tests = 2

    if test_help():
        tests_passed += 1

    if test_dependencies():
        tests_passed += 1

    print("=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("✓ All basic tests passed!")
        print("\nNext steps:")
        print("1. Set DEEPSEEK_API_KEY environment variable for DeepSeek summaries")
        print("2. Install and run Ollama for local model summaries")
        print("3. Test with a real YouTube URL")
    else:
        print("✗ Some tests failed. Please check the dependencies.")

if __name__ == "__main__":
    main()