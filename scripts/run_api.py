"""
Run the SpendSenseAI API server.

Usage:
    python -m scripts.run_api
    or
    uvicorn ui.api:app --reload
"""

import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Run the API server
    uvicorn.run(
        "ui.api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info"
    )

