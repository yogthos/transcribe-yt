#!/usr/bin/env python3
"""
Launcher script for the Transcribe YouTube GUI
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from transcribe_yt_gui import main
    main()
except ImportError as e:
    print(f"Error importing GUI module: {e}")
    print("Make sure you have installed the required dependencies:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error running GUI: {e}")
    sys.exit(1)
