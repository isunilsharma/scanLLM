"""Default policy rules for ScanLLM.

These are sensible defaults that engineers can start with via
``scanllm policy init``.  They can be customized in ``.scanllm/policies.yaml``.

The YAML string below is the canonical source — ``PolicyEngine.load_defaults()``
parses it the same way it would parse any user-supplied file.
"""

from __future__ import annotations

DEFAULT_POLICIES_YAML: str = """\
version: "1.0"
policies:
  # -----------------------------------------------------------------------
  # 1. No hardcoded secrets
  # -----------------------------------------------------------------------
  - name: no-hardcoded-secrets
    description: "No API keys or secrets in source code"
    severity: error
    conditions:
      - field: component_type
        operator: equals
        value: "secret"

  # -----------------------------------------------------------------------
  # 2. No deprecated models
  # -----------------------------------------------------------------------
  - name: no-deprecated-models
    description: "Block deprecated or end-of-life models"
    severity: error
    conditions:
      - field: model_name
        operator: in
        value:
          - "gpt-3.5-turbo"
          - "text-davinci-003"
          - "text-davinci-002"
          - "code-davinci-002"
          - "text-curie-001"
          - "text-babbage-001"
          - "text-ada-001"

  # -----------------------------------------------------------------------
  # 3. No eval/exec of LLM output
  # -----------------------------------------------------------------------
  - name: no-eval-llm-output
    description: "Never pass LLM output to eval(), exec(), or subprocess"
    severity: error
    conditions:
      - field: pattern_category
        operator: in
        value:
          - "eval_llm_output"
          - "exec_llm_output"
          - "improper_output_handling"
          - "unsanitized_output_to_shell"

  # -----------------------------------------------------------------------
  # 4. Require max_tokens on LLM calls
  # -----------------------------------------------------------------------
  - name: require-max-tokens
    description: "All LLM API calls should set max_tokens to prevent unbounded consumption"
    severity: warning
    conditions:
      - field: pattern_category
        operator: equals
        value: "missing_max_tokens"

  # -----------------------------------------------------------------------
  # 5. No prompt injection risks
  # -----------------------------------------------------------------------
  - name: no-prompt-injection-risks
    description: "Warn on potential prompt injection vulnerabilities"
    severity: warning
    conditions:
      - field: pattern_category
        operator: in
        value:
          - "prompt_injection"
          - "user_input_in_prompt"
          - "unsanitized_prompt"
          - "f_string_prompt"
          - "format_string_prompt"

  # -----------------------------------------------------------------------
  # 6. Risk score threshold
  # -----------------------------------------------------------------------
  - name: max-risk-score
    description: "Repository risk score must be below threshold"
    severity: error
    type: scan_level
    conditions:
      - field: risk_score
        operator: greater_than
        value: 70

  # -----------------------------------------------------------------------
  # 7. No excessive agent permissions
  # -----------------------------------------------------------------------
  - name: no-excessive-agent-permissions
    description: "Flag agents with broad tool access or missing human-in-the-loop"
    severity: warning
    conditions:
      - field: pattern_category
        operator: in
        value:
          - "excessive_agency"
          - "broad_tool_access"
          - "missing_human_in_loop"

  # -----------------------------------------------------------------------
  # 8. No unauthenticated vector DB connections
  # -----------------------------------------------------------------------
  - name: no-unauthenticated-vectordb
    description: "Vector DB connections must use authentication"
    severity: warning
    conditions:
      - field: pattern_category
        operator: in
        value:
          - "unauthenticated_vectordb"
          - "vectordb_no_auth"
          - "vector_embedding_weakness"

  # -----------------------------------------------------------------------
  # 9. Approved providers only
  # -----------------------------------------------------------------------
  - name: approved-providers-only
    description: "Only allow approved AI providers"
    severity: error
    conditions:
      - field: provider
        operator: not_in
        value:
          - "openai"
          - "anthropic"
          - "google_ai"

  # -----------------------------------------------------------------------
  # 10. No system prompt leakage
  # -----------------------------------------------------------------------
  - name: no-system-prompt-leakage
    description: "Prevent API keys or business logic in system prompts"
    severity: warning
    conditions:
      - field: pattern_category
        operator: in
        value:
          - "system_prompt_leakage"
          - "secret_in_prompt"
          - "business_logic_in_prompt"

  # -----------------------------------------------------------------------
  # 11. No high-severity findings (catch-all)
  # -----------------------------------------------------------------------
  - name: no-critical-findings
    description: "No critical-severity findings allowed"
    severity: error
    conditions:
      - field: severity
        operator: equals
        value: "critical"

  # -----------------------------------------------------------------------
  # 12. Maximum total findings threshold
  # -----------------------------------------------------------------------
  - name: max-total-findings
    description: "Total finding count must stay below threshold"
    severity: warning
    type: scan_level
    conditions:
      - field: total_findings
        operator: greater_than
        value: 100
"""
