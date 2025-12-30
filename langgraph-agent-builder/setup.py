from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="langgraph-agent-builder",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A framework for building production-ready LangGraph agents dynamically",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/langgraph-agent-builder",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "langgraph>=0.0.20",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "langchain-anthropic>=0.0.1",
        "langchain-community>=0.0.10",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "httpx>=0.25.0",
        "redis>=5.0.0",
        "structlog>=23.0.0",
        "prometheus-client>=0.18.0",
        "tenacity>=8.2.0",
        "aiofiles>=23.0.0",
        "pyyaml>=6.0.0",
        "python-multipart>=0.0.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
            "pre-commit>=3.4.0",
        ],
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
) 