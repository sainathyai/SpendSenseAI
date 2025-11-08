"""
Elastic Beanstalk entry point for SpendSenseAI
This file is used by AWS Elastic Beanstalk to run the FastAPI application
"""

import uvicorn
from ui.api import app

# Elastic Beanstalk expects 'application' variable
application = app

if __name__ == "__main__":
    # For local development
    uvicorn.run(app, host="0.0.0.0", port=8000)

