#!/usr/bin/env python3
"""
Launcher script for the Transcribe YouTube .app bundle
This script handles the virtual environment and dependencies
"""

import sys
import os
import subprocess
from pathlib import Path

def find_app_resources():
    """Find the app bundle resources directory"""
    # Get the path to the app bundle
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        app_bundle_path = os.path.dirname(sys.executable)
    else:
        # Running as a script
        app_bundle_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    resources_path = os.path.join(app_bundle_path, "Resources")
    return resources_path

def setup_environment():
    """Set up the Python environment for the app"""
    resources_path = find_app_resources()

    # Add the resources path to Python path
    if resources_path not in sys.path:
        sys.path.insert(0, resources_path)

    # Change to the resources directory
    os.chdir(resources_path)

    # Set up environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = resources_path
    env['PYTHONUNBUFFERED'] = '1'

    return env, resources_path

def check_dependencies(resources_path):
    """Check if dependencies are installed"""
    venv_path = os.path.join(resources_path, "venv")
    pip_path = os.path.join(venv_path, "bin", "pip")

    if not os.path.exists(pip_path):
        print("❌ Virtual environment not found. Please run the packaging script first.")
        return False

    # Check if required packages are installed
    try:
        result = subprocess.run([pip_path, "list"], capture_output=True, text=True)
        if "PyGObject" not in result.stdout:
            print("Installing missing dependencies...")
            requirements_path = os.path.join(resources_path, "requirements.txt")
            if os.path.exists(requirements_path):
                subprocess.run([pip_path, "install", "-r", requirements_path], check=True)
            else:
                print("❌ Requirements file not found")
                return False
    except subprocess.CalledProcessError:
        print("❌ Error checking dependencies")
        return False

    return True

def run_gui():
    """Run the GUI application"""
    env, resources_path = setup_environment()

    # Check dependencies
    if not check_dependencies(resources_path):
        return False

    # Set up the Python path for the virtual environment
    venv_path = os.path.join(resources_path, "venv")
    venv_python = os.path.join(venv_path, "bin", "python")

    if os.path.exists(venv_python):
        # Use the virtual environment Python
        python_executable = venv_python
    else:
        # Fall back to system Python
        python_executable = sys.executable

    # Import and run the GUI
    try:
        # Add the virtual environment to the path
        venv_site_packages = os.path.join(venv_path, "lib", "python3.13", "site-packages")
        if os.path.exists(venv_site_packages):
            sys.path.insert(0, venv_site_packages)

        from transcribe_yt_gui import main
        main()
        return True

    except ImportError as e:
        print(f"❌ Error importing GUI module: {e}")
        print("Make sure all dependencies are installed in the virtual environment.")
        return False
    except Exception as e:
        print(f"❌ Error running GUI: {e}")
        return False

def main():
    """Main launcher function"""
    print("Transcribe YouTube - Starting Application...")

    try:
        success = run_gui()
        if not success:
            print("\n❌ Failed to start the application")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
