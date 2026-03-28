# Contributing AI Detection Signatures

This guide explains how to add new AI detection patterns to ScanLLM's signature database (`ai_signatures.yaml`). New signatures allow ScanLLM to detect additional AI providers, frameworks, vector databases, and tools without any code changes.

## File Structure

The `ai_signatures.yaml` file is organized into top-level sections:

- **providers** -- LLM API providers (OpenAI, Anthropic, Google, etc.)
- **vector_databases** -- Vector storage systems (ChromaDB, Pinecone, etc.)
- **frameworks** -- Orchestration frameworks and agent tools (LangChain, CrewAI, etc.)
- **inference** -- Self-hosted inference servers (vLLM, Ollama, etc.)
- **mcp** -- Model Context Protocol servers
- **risk_patterns** -- Cross-cutting security risk patterns

## Adding a New Provider

Here is a complete example of adding a new LLM provider:

```yaml
providers:
  my_provider:
    display_name: "My Provider"       # Required: human-readable name
    category: "llm_provider"          # Required: component type (see categories below)
    python:                           # Optional: Python detection patterns
      imports:                        # Module import patterns
        - "my_provider"
        - "from my_provider import"
      calls:                          # API call patterns
        - "MyProvider("
        - "client.chat.create"
      models:                         # Known model identifiers
        - "my-model-large"
        - "my-model-small"
    javascript:                       # Optional: JS/TS detection patterns
      imports:
        - "from 'my-provider-sdk'"
        - "require('my-provider-sdk')"
      calls:
        - "new MyProvider("
    env_vars:                         # Optional: environment variable names
      - "MY_PROVIDER_API_KEY"
    endpoint_urls:                    # Optional: API endpoint URLs
      - "api.myprovider.com"
    risk_weight: 1.0                  # Required: 0.0-2.0 (see risk weights below)
```

## Required Fields

Every signature entry must have:

| Field | Description |
|-------|-------------|
| `display_name` | Human-readable name shown in reports |
| `category` | Component classification (see below) |
| `risk_weight` | Float from 0.0 to 2.0 |

At least one detection section is also required (`python`, `javascript`, `env_vars`, `endpoint_urls`, `config_files`, or `docker_images`).

## Valid Categories

- `llm_provider` -- Commercial or open-source LLM API
- `vector_db` -- Vector database or similarity search
- `orchestration_framework` -- LLM orchestration (LangChain, LlamaIndex, etc.)
- `agent_tool` -- Autonomous agent framework (CrewAI, AutoGen, etc.)
- `inference_server` -- Self-hosted model serving (vLLM, Ollama, TGI)
- `mcp_server` -- Model Context Protocol server
- `embedding_service` -- Dedicated embedding provider

## Risk Weight Guidelines

| Weight | When to use |
|--------|------------|
| 0.3-0.4 | Local-only tools with no external API calls (FAISS, Ollama) |
| 0.5-0.6 | Standard tools with moderate risk (vector DBs, frameworks) |
| 0.7-0.8 | Cloud APIs with data sent externally (HuggingFace, Together) |
| 1.0 | Major LLM providers (OpenAI, Anthropic, Google, AWS) |
| 1.2-1.5 | Tools with elevated risk: data residency concerns, code execution, broad agent permissions |

## Adding OWASP Risk Patterns

For signatures that should flag specific OWASP LLM Top 10 risks, add a `risk_patterns` list:

```yaml
  my_agent:
    # ... standard fields ...
    risk_patterns:
      - pattern: "tools=\\["             # Regex pattern to match
        owasp: "LLM06"                   # OWASP LLM Top 10 ID
        severity: "medium"               # critical, high, medium, low
        message: "Agent with tool access — verify least-privilege"
```

Valid OWASP IDs: `LLM01` through `LLM10`.

Valid severity levels: `critical`, `high`, `medium`, `low`.

## Testing Your Signature

1. Add the signature to `core/signatures/ai_signatures.yaml`.

2. Run the validation script:
   ```bash
   python -m core.signatures.validate
   ```
   This checks YAML syntax, required fields, duplicate names, and OWASP ID validity.

3. Create a small test file that uses the provider/framework you added, then scan it:
   ```bash
   scanllm scan ./test_file.py --output json
   ```

4. Verify your provider appears in the scan output under the correct category.

## Checklist Before Submitting

- [ ] `display_name` is set and human-readable
- [ ] `category` is one of the valid categories listed above
- [ ] `risk_weight` is set to an appropriate value
- [ ] At least one detection method is defined (imports, calls, env_vars, etc.)
- [ ] Import patterns match how the library is actually imported (check the library docs)
- [ ] Call patterns match real API usage (not just class names)
- [ ] Model names match official model identifiers
- [ ] Environment variable names match the library's documentation
- [ ] `python -m core.signatures.validate` passes with no errors
- [ ] No duplicate provider key names
