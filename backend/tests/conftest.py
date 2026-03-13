"""Shared pytest fixtures for ScanLLM test suite."""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def tmp_repo_dir(tmp_path: Path) -> Path:
    """Create a temporary directory populated with sample files from fixtures.

    Copies all fixture files into a temp directory that mimics a small
    repository layout.  Cleaned up automatically by pytest's tmp_path.
    """
    repo = tmp_path / "sample_repo"
    repo.mkdir()

    # Copy fixture files into the repo
    for fixture_file in FIXTURES_DIR.iterdir():
        if fixture_file.is_file():
            shutil.copy2(fixture_file, repo / fixture_file.name)

    # Create some subdirectory structure
    src_dir = repo / "src"
    src_dir.mkdir()
    for py_file in FIXTURES_DIR.glob("*.py"):
        shutil.copy2(py_file, src_dir / py_file.name)

    return repo


@pytest.fixture
def sample_python_file(tmp_path: Path) -> Path:
    """Create a Python file with OpenAI, LangChain, and various AI imports."""
    content = '''\
from openai import OpenAI
from langchain_openai import ChatOpenAI
from anthropic import Anthropic
import chromadb

client = OpenAI()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

def get_completion(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000,
        stream=True
    )
    return response

def get_anthropic_response(msg):
    ac = Anthropic()
    message = ac.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=[{"role": "user", "content": msg}]
    )
    return message.content[0].text
'''
    p = tmp_path / "sample_multi_ai.py"
    p.write_text(content)
    return p


@pytest.fixture
def sample_js_file(tmp_path: Path) -> Path:
    """Create a JS/TS file with AI SDK imports."""
    content = '''\
import OpenAI from 'openai';
import Anthropic from '@anthropic-ai/sdk';
import { generateText, streamText } from 'ai';
import { openai } from '@ai-sdk/openai';
import { ChatOpenAI } from '@langchain/openai';

const client = new OpenAI();
const anthropic = new Anthropic();

async function chat() {
  const result = await generateText({
    model: openai('gpt-4o'),
    prompt: 'Hello',
  });
  return result;
}
'''
    p = tmp_path / "sample_ai.ts"
    p.write_text(content)
    return p


@pytest.fixture
def sample_config_file(tmp_path: Path) -> Path:
    """Create a YAML file with model configurations."""
    content = '''\
llm:
  provider: openai
  model: gpt-4o
  temperature: 0.7
  max_tokens: 2000
  endpoint: https://api.openai.com/v1

embedding:
  model: text-embedding-3-small

vector_db:
  type: chromadb
  host: localhost
  port: 8000

services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
'''
    p = tmp_path / "config.yaml"
    p.write_text(content)
    return p


@pytest.fixture
def sample_requirements(tmp_path: Path) -> Path:
    """Create a requirements.txt with AI and non-AI packages."""
    content = '''\
openai==1.12.0
anthropic==0.23.0
langchain==0.2.0
langchain-openai==0.1.0
chromadb==0.4.24
pinecone-client==3.2.0
transformers==4.40.0
crewai==0.28.0
faiss-cpu==1.8.0
sentence-transformers==2.7.0
flask==3.0.0
requests==2.31.0
'''
    p = tmp_path / "requirements.txt"
    p.write_text(content)
    return p


@pytest.fixture
def sample_notebook(tmp_path: Path) -> Path:
    """Create a .ipynb notebook with AI code cells."""
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11.0"},
        },
        "cells": [
            {
                "cell_type": "code",
                "id": "cell-1",
                "metadata": {},
                "source": ["import openai\n", "client = openai.OpenAI()"],
                "outputs": [],
                "execution_count": None,
            },
            {
                "cell_type": "code",
                "id": "cell-2",
                "metadata": {},
                "source": [
                    'response = client.chat.completions.create(model="gpt-4o", '
                    'messages=[{"role": "user", "content": "hello"}])'
                ],
                "outputs": [],
                "execution_count": None,
            },
            {
                "cell_type": "code",
                "id": "cell-3",
                "metadata": {},
                "source": [
                    "from langchain_openai import ChatOpenAI\n",
                    "llm = ChatOpenAI()",
                ],
                "outputs": [],
                "execution_count": None,
            },
        ],
    }
    p = tmp_path / "sample.ipynb"
    p.write_text(json.dumps(notebook, indent=2))
    return p


@pytest.fixture
def sample_env_file(tmp_path: Path) -> Path:
    """Create a .env file with API keys."""
    content = '''\
OPENAI_API_KEY=sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234
ANTHROPIC_API_KEY=sk-ant-abc123def456
PINECONE_API_KEY=pcsk_abc123
HF_TOKEN=hf_abc123def456
DATABASE_URL=postgresql://localhost/mydb
SECRET_KEY=not-an-ai-key
'''
    p = tmp_path / ".env"
    p.write_text(content)
    return p


@pytest.fixture
def sample_package_json(tmp_path: Path) -> Path:
    """Create a package.json with AI and non-AI dependencies."""
    data = {
        "dependencies": {
            "openai": "^4.47.1",
            "@anthropic-ai/sdk": "^0.20.0",
            "@langchain/openai": "^0.2.0",
            "ai": "^3.1.0",
            "@ai-sdk/openai": "^0.0.36",
            "@modelcontextprotocol/sdk": "^1.0.0",
            "express": "^4.18.0",
            "react": "^19.0.0",
        }
    }
    p = tmp_path / "package.json"
    p.write_text(json.dumps(data, indent=2))
    return p


@pytest.fixture
def ai_signatures() -> dict:
    """Load the ai_signatures.yaml file used by scanners."""
    import yaml

    sig_path = Path(__file__).parent.parent.parent / "ai_signatures.yaml"
    if not sig_path.exists():
        sig_path = Path(__file__).parent.parent / "app" / "scanner" / "signatures" / "ai_signatures.yaml"
    if not sig_path.exists():
        pytest.skip("ai_signatures.yaml not found")
    with open(sig_path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def scoring_rules() -> dict:
    """Load the scoring rules.yaml file."""
    import yaml

    rules_path = Path(__file__).parent.parent / "app" / "scoring" / "rules.yaml"
    if not rules_path.exists():
        pytest.skip("rules.yaml not found")
    with open(rules_path) as f:
        return yaml.safe_load(f)
