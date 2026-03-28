## :shield: ScanLLM AI Security Report

![Risk Score](https://img.shields.io/badge/Risk_Score-{{RISK_SCORE}}%2F100-{{BADGE_COLOR}})
![Grade](https://img.shields.io/badge/Grade-{{GRADE}}-{{BADGE_COLOR}})

### Summary

| Metric | Result |
|--------|--------|
| **Risk Score** | {{RISK_SCORE}}/100 (Grade: **{{GRADE}}**) |
| **New Findings** | {{NEW_FINDINGS_COUNT}} |
| **Total Findings** | {{TOTAL_FINDINGS_COUNT}} |
| **Policy Check** | {{POLICY_RESULT_ICON}} {{POLICY_RESULT}} |
| **Severity Threshold** | {{SEVERITY_THRESHOLD}} |

### New Findings in This PR

{{#if NEW_FINDINGS}}
| Severity | Type | File | Line | Description |
|----------|------|------|------|-------------|
{{#each NEW_FINDINGS}}
| {{severity_badge}} | {{component_type}} | `{{file_path}}` | {{line_number}} | {{message}} |
{{/each}}
{{else}}
No new AI/LLM security findings detected in this PR. :tada:
{{/if}}

### Policy Check

{{#if POLICY_PASSED}}
:white_check_mark: **All policies passed.**
{{else}}
:x: **Policy violations detected:**

| Policy | Status | Details |
|--------|--------|---------|
{{#each POLICY_VIOLATIONS}}
| {{policy_name}} | :x: Failed | {{details}} |
{{/each}}
{{/if}}

### OWASP LLM Top 10 Coverage

| ID | Category | Findings | Status |
|----|----------|----------|--------|
| LLM01 | Prompt Injection | {{LLM01_COUNT}} | {{LLM01_ICON}} |
| LLM02 | Sensitive Info Disclosure | {{LLM02_COUNT}} | {{LLM02_ICON}} |
| LLM03 | Supply Chain | {{LLM03_COUNT}} | {{LLM03_ICON}} |
| LLM05 | Improper Output Handling | {{LLM05_COUNT}} | {{LLM05_ICON}} |
| LLM06 | Excessive Agency | {{LLM06_COUNT}} | {{LLM06_ICON}} |
| LLM07 | System Prompt Leakage | {{LLM07_COUNT}} | {{LLM07_ICON}} |
| LLM08 | Vector/Embedding Weaknesses | {{LLM08_COUNT}} | {{LLM08_ICON}} |
| LLM10 | Unbounded Consumption | {{LLM10_COUNT}} | {{LLM10_ICON}} |

<details>
<summary>View full SARIF results</summary>

[View in GitHub Code Scanning](../security/code-scanning)

</details>

---

<!-- Badge color mapping: A=brightgreen, B=green, C=yellow, D=orange, F=red -->
<!-- Severity badges: critical=🔴, high=🟠, medium=🟡, low=🔵, info=⚪ -->

*Scanned by [ScanLLM](https://scanllm.ai) v{{SCANLLM_VERSION}} | Commit: {{COMMIT_SHA_SHORT}}*
