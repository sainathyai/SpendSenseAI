"""
SpendSenseAI - Financial Management and Recommendation System
"""
from setuptools import setup, find_packages

setup(
    name="spendsense",
    version="0.1.0",
    description="AI-powered financial management and recommendation system",
    author="SpendSense Team",
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests", "scripts", "docs", "frontend"]),
    install_requires=[
        # Read from requirements.txt
        line.strip()
        for line in open("requirements.txt")
        if line.strip() and not line.startswith("#")
    ],
    entry_points={
        "console_scripts": [
            "spendsense-api=ui.api:main",
        ],
    },
)



