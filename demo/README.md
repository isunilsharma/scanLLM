# ScanLLM Demo

This directory contains a sample project with intentional AI security issues for demonstrating ScanLLM's detection capabilities.

## Try It

```bash
cd demo/sample_project
scanllm scan .
scanllm policy check
scanllm ui
```

## What It Contains

The sample project (`sample_project/`) includes:

- **OpenAI, Anthropic, and LangChain imports** — detected as AI provider dependencies
- **CrewAI agent setup** — flagged for excessive agency (OWASP LLM06)
- **User input in f-string prompt** — flagged as prompt injection risk (OWASP LLM01)
- **Missing max_tokens** — flagged as unbounded consumption (OWASP LLM10)
- **Hardcoded API key** — flagged as sensitive info disclosure (OWASP LLM02)
- **AI package dependencies** in requirements.txt
- **Model references** in config.yaml

All issues are intentional and use fake credentials. This project is safe to scan and share.
