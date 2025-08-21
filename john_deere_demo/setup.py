#!/usr/bin/env python3
"""Setup script for Demo Agent package.

This is an alternative to pyproject.toml for users who prefer traditional Python packaging.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="demo-agent",
    version="0.1.0",
    author="Siddharth Gupta",
    author_email="sid2harthgupta@gmail.com",
    description="A modular AI agent system for John Deere equipment sales and support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/john_deere_demo",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.13",
    install_requires=[
        "dotenv>=0.9.9",
        "galileo>=1.15.0",
        "langchain-core>=0.3.74",
        "langchain-openai>=0.3.30",
        "langchain-pinecone>=0.2.11",
        "langchain-tavily>=0.2.11",
        "langgraph>=0.6.5",
        "pinecone>=7.3.0",
        "pinecone-plugin-interface>=0.0.7",
        "requests>=2.31.0",
        "streamlit>=1.48.1",
    ],
    extras_require={
        "dev": [
            "black>=25.1.0",
            "pytest>=8.4.1",
            "ruff>=0.12.9",
        ],
    },
    entry_points={
        "console_scripts": [
            "demo-agent=demo_agent.main:main",
        ],
    },
)
