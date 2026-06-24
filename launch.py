#!/usr/bin/env python3
"""
Launch script for the Energy Twin digital dashboard.
Bypasses terminal path issues by using Python subprocess.
"""
import subprocess
import sys
import os

def main():
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print(f"📊 Energy Twin Digital Dashboard Launcher")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python: {sys.version}")
    print("-" * 60)
    print("Starting Streamlit server...")
    print("🌐 Open your browser to http://localhost:8501")
    print("-" * 60 + "\n")
    
    try:
        # Run streamlit
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app.py"],
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
