"""
Run the SpendSenseAI Customer Dashboard.

Usage:
    python -m scripts.run_customer_dashboard
    or
    streamlit run ui/customer_dashboard.py
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    # Get dashboard file path
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "ui", "customer_dashboard.py")
    dashboard_path = os.path.abspath(dashboard_path)
    
    # Run streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path])
