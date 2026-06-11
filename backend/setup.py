"""
Setup configuration for backend package.
"""

from setuptools import setup, find_packages

setup(
    name="pole-ai-backend",
    version="0.1.0",
    description="FastAPI backend for AI-powered Pole Sport training plan generator",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        line.strip()
        for line in open("requirements.txt").readlines()
        if line.strip() and not line.startswith("#")
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
    ],
)
