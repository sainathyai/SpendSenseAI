"""
Run the SpendSenseAI Operator Dashboard.

Usage:
    python -m scripts.run_dashboard
    or
    streamlit run ui/dashboard.py
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    # Get dashboard file path
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "ui", "dashboard.py")
    dashboard_path = os.path.abspath(dashboard_path)
    
    # Run streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path])

