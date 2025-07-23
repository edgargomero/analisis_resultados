#!/usr/bin/env python3
"""
CEAPSI PCF System - Run Script
Simple launcher for the Streamlit application
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the CEAPSI PCF Streamlit application"""
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    app_path = project_root / "app.py"
    
    # Change to project directory
    os.chdir(project_root)
    
    # Check if app.py exists
    if not app_path.exists():
        print("❌ Error: app.py not found in project root")
        sys.exit(1)
    
    # Launch Streamlit
    try:
        print("🚀 Launching CEAPSI PCF System...")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.address", "localhost",
            "--server.port", "8501"
        ], check=True)
    except KeyboardInterrupt:
        print("\n✋ Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()