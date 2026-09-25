"""
Agent Skill Security Scanner.

Analyses agent skill source code (Python/JS/shell files) for security risks:
  SKILL-001  Prompt injection in skill definitions
  SKILL-002  Malware payloads (obfuscated code, encoded executables, suspicious commands)
  SKILL-003  Credential harvesting patterns
  SKILL-004  Hardcoded secrets in skill source
  SKILL-005  Untrusted external content fetch
  SKILL-006  Data exfiltration patterns (read local + send external)
  SKILL-007  Permission escalation
  SKILL-008  Cross-tool manipulation (modifies other tools' configs)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


# ── Signature loading ──────────────────────────────────────────────────────

_SIGNATURES: dict[str, Any] | None = None


def _load_skill_signatures() -> dict[str, Any]:
    """Load skill risk patterns from mcp_signatures.yaml."""
    global _SIGNATURES
    if _SIGNATURES is not None:
        return _SIGNATURES

    sig_path = Path(__file__).parent / "mcp_signatures.yaml"
    if sig_path.exists():
        with open(sig_path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
            _SIGNATURES = data.get("skill_risks", {})
    else:
        logger.warning("mcp_signatures.yaml not found at %s", sig_path)
        _SIGNATURES = {}
    return _SIGNATURES


# ── Finding constructor ────────────────────────────────────────────────────

def _make_finding(
    *,
    file_path: str,
    line_number: int = 0,
    risk_id: str,
    severity: str,
    description: str,
    remediation: str = "",
    snippet: str = "",
    owasp_id: str | None = None,
) -> dict[str, Any]:
    """Construct a finding dict compatible with the core engine format."""
    return {
        "file_path": file_path,
        "line_number": line_number,
        "line_text": snippet,
        "framework": "agent_skill",
        "pattern_name": risk_id,
        "pattern_category": "agent_security",
        "pattern_severity": severity,
        "pattern_description": description,
        "snippet": snippet,
        "model_name": None,
        "temperature": None,
        "max_tokens": None,
        "is_streaming": False,
        "has_tools": False,
        "component_type": "agent_skill",
        "provider": "",
        "owasp_id": owasp_id,
        "remediation": remediation,
        "risk_id": risk_id,
    }


# ── SkillScanner ───────────────────────────────────────────────────────────

class SkillScanner:
    """Analyses agent skill source files for security risks."""

    # File extensions we will scan for skill content
    SKILL_EXTENSIONS: set[str] = {".py", ".js", ".ts", ".sh", ".bash", ".yaml", ".yml", ".json"}

    def __init__(self) -> None:
        self.signatures = _load_skill_signatures()

    # ── Public API ─────────────────────────────────────────────────────

    def scan_file(self, file_path: Path, relative_path: str = "") -> list[dict[str, Any]]:
        """Scan a single skill source file for security risks.

        Args:
            file_path: Absolute path to the skill file.
            relative_path: Path shown in findings (defaults to file_path).

        Returns:
            A list of finding dicts.
        """
        if not file_path.is_file():
            return []

        display_path = relative_path or str(file_path)

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.debug("Cannot read %s: %s", file_path, exc)
            return []

        lines = content.splitlines()
        findings: list[dict[str, Any]] = []

        findings.extend(self._check_prompt_injection(content, lines, display_path))
        findings.extend(self._check_malware_payloads(content, lines, display_path))
        findings.extend(self._check_credential_harvesting(content, lines, display_path))
        findings.extend(self._check_hardcoded_secrets(content, lines, display_path))
        findings.extend(self._check_external_fetch(content, lines, display_path))
        findings.extend(self._check_data_exfiltration(content, lines, display_path))
        findings.extend(self._check_permission_escalation(content, lines, display_path))
        findings.extend(self._check_cross_tool_manipulation(content, lines, display_path))

        return findings

    def scan_directory(self, directory: Path) -> list[dict[str, Any]]:
        """Scan all skill files in a directory tree.

        Returns:
            A list of finding dicts.
        """
        findings: list[dict[str, Any]] = []

        if not directory.is_dir():
            return findings

        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in self.SKILL_EXTENSIONS:
                continue
            # Skip common non-skill directories
            parts = file_path.relative_to(directory).parts
            skip_dirs = {"node_modules", ".git", "__pycache__", ".venv", "venv"}
            if any(p in skip_dirs for p in parts):
                continue

            try:
                rel = str(file_path.relative_to(directory))
            except ValueError:
                rel = str(file_path)

            findings.extend(self.scan_file(file_path, rel))

        return findings

    # ── SKILL-001: Prompt injection in skill definitions ──────────────

    def _check_prompt_injection(
        self, content: str, lines: list[str], file_path: str,
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []

        # Reuse prompt injection patterns from the MCP signatures
        sig_path = Path(__file__).parent / "mcp_signatures.yaml"
        instruction_patterns: list[str] = []
        if sig_path.exists():
            with open(sig_path, encoding="utf-8") as fh:
                all_sigs = yaml.safe_load(fh) or {}
            instruction_patterns = all_sigs.get("prompt_injection", {}).get(
                "instruction_patterns", []
            )

        content_lower = content.lower()
        for pattern in instruction_patterns:
            if pattern.lower() in content_lower:
                # Find the first line containing this pattern
                for i, line in enumerate(lines, start=1):
                    if pattern.lower() in line.lower():
                        findings.append(_make_finding(
                            file_path=file_path,
                            line_number=i,
                            risk_id="SKILL-001",
                            severity="high",
                            description=(
                                f"Prompt injection indicator in skill: contains '{pattern}'"
                            ),
                            remediation=(
                                "Remove instruction-override language from skill definitions. "
                                "Skill descriptions and prompts should not contain phrases that "
                                "attempt to override agent behavior."
                            ),
                            snippet=line.strip()[:200],
                            owasp_id="LLM01",
                        ))
                        break  # One finding per pattern

        return findings

    # ── SKILL-002: Malware payloads ───────────────────────────────────

    def _check_malware_payloads(
        self, content: str, lines: list[str], file_path: str,
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        patterns = self.signatures.get("malware_patterns", [])

        for pat_def in patterns:
            regex = pat_def["pattern"]
            try:
                for i, line in enumerate(lines, start=1):
                    if re.search(regex, line):
                        findings.append(_make_finding(
                            file_path=file_path,
                            line_number=i,
                            risk_id="SKILL-002",
                            severity="high",
                            description=(
                                f"Potential malware payload: {pat_def['description']}"
                            ),
                            remediation=(
                                "Review this code for malicious intent. Dynamic code "
                                "execution, pickle deserialization, and subprocess calls "
                                "are common malware vectors in agent skills."
                            ),
                            snippet=line.strip()[:200],
                            owasp_id="LLM06",
                        ))
                        break  # One finding per pattern type
            except re.error:
                logger.debug("Invalid regex in malware_patterns: %s", regex)

        return findings

    # ── SKILL-003: Credential harvesting ──────────────────────────────

    def _check_credential_harvesting(
        self, content: str, lines: list[str], file_path: str,
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        patterns = self.signatures.get("credential_harvesting", [])

        for pat_def in patterns:
            regex = pat_def["pattern"]
            try:
                for i, line in enumerate(lines, start=1):
                    if re.search(regex, line, re.IGNORECASE):
                        findings.append(_make_finding(
                            file_path=file_path,
                            line_number=i,
                            risk_id="SKILL-003",
                            severity="high",
                            description=(
                                f"Credential harvesting pattern: {pat_def['description']}"
                            ),
                            remediation=(
                                "Skills should not directly handle credentials. Use "
                                "environment variables or a secrets manager instead. "
                                "Review whether this skill needs access to credentials."
                            ),
                            snippet=line.strip()[:200],
                            owasp_id="LLM02",
                        ))
                        break
            except re.error:
                logger.debug("Invalid regex in credential_harvesting: %s", regex)

        return findings

    # ── SKILL-004: Hardcoded secrets ──────────────────────────────────

    def _check_hardcoded_secrets(
        self, content: str, lines: list[str], file_path: str,
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        patterns = self.signatures.get("hardcoded_secrets", [])

        for pat_def in patterns:
            regex = pat_def["pattern"]
            try:
                for i, line in enumerate(lines, start=1):
                    if re.search(regex, line):
                        # Mask the actual secret in the snippet
                        masked = re.sub(regex, "***REDACTED***", line.strip())
                        findings.append(_make_finding(
                            file_path=file_path,
                            line_number=i,
                            risk_id="SKILL-004",
                            severity="critical",
                            description=(
                                f"Hardcoded secret detected: {pat_def['description']}"
                            ),
                            remediation=(
                                "Remove hardcoded secrets from skill source code. Use "
                                "environment variables or a secrets manager. Rotate any "
                                "exposed credentials immediately."
                            ),
                            snippet=masked[:200],
                            owasp_id="LLM07",
                        ))
                        break
            except re.error:
                logger.debug("Invalid regex in hardcoded_secrets: %s", regex)

        return findings

    # ── SKILL-005: Untrusted external content fetch ───────────────────

    def _check_external_fetch(
        self, content: str, lines: list[str], file_path: str,
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        patterns = self.signatures.get("external_fetch", [])

        for pat_def in patterns:
            regex = pat_def["pattern"]
            try:
                for i, line in enumerate(lines, start=1):
                    if re.search(regex, line):
                        findings.append(_make_finding(
                            file_path=file_path,
                            line_number=i,
                            risk_id="SKILL-005",
                            severity="medium",
                            description=(
                                f"External content fetch: {pat_def['description']}"
                            ),
                            remediation=(
                                "Review whether this skill needs to fetch external content. "
                                "If it does, validate URLs against an allowlist, verify "
                                "content integrity, and never execute fetched content directly."
                            ),
                            snippet=line.strip()[:200],
                            owasp_id="LLM05",
                        ))
                        break
            except re.error:
                logger.debug("Invalid regex in external_fetch: %s", regex)

        return findings

    # ── SKILL-006: Data exfiltration ──────────────────────────────────

    def _check_data_exfiltration(
        self, content: str, lines: list[str], file_path: str,
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        exfil_patterns = self.signatures.get("exfiltration", [])

        for pat_def in exfil_patterns:
            read_regex = pat_def.get("read_pattern", "")
            send_regex = pat_def.get("send_pattern", "")

            if not read_regex or not send_regex:
                continue

            try:
                has_read = bool(re.search(read_regex, content))
                has_send = bool(re.search(send_regex, content))
            except re.error:
                continue

            if has_read and has_send:
                # Find the send line for reporting
                line_num = 0
                snippet = ""
                for i, line in enumerate(lines, start=1):
                    try:
                        if re.search(send_regex, line):
                            line_num = i
                            snippet = line.strip()
                            break
                    except re.error:
                        continue

                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=line_num,
                    risk_id="SKILL-006",
                    severity="high",
                    description=(
                        f"Data exfiltration risk: {pat_def['description']}"
                    ),
                    remediation=(
                        "This skill both reads local data and sends it externally. "
                        "Review whether this combination is intentional. If needed, "
                        "restrict which files can be read and which endpoints can be contacted."
                    ),
                    snippet=snippet[:200],
                    owasp_id="LLM06",
                ))

        return findings

    # ── SKILL-007: Permission escalation ──────────────────────────────

    def _check_permission_escalation(
        self, content: str, lines: list[str], file_path: str,
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        patterns = self.signatures.get("permission_escalation", [])

        for pat_def in patterns:
            regex = pat_def["pattern"]
            try:
                for i, line in enumerate(lines, start=1):
                    if re.search(regex, line):
                        findings.append(_make_finding(
                            file_path=file_path,
                            line_number=i,
                            risk_id="SKILL-007",
                            severity="high",
                            description=(
                                f"Permission escalation: {pat_def['description']}"
                            ),
                            remediation=(
                                "Skills should not modify system permissions or escalate "
                                "privileges. Remove privilege-changing operations and run "
                                "the skill with the minimum required permissions."
                            ),
                            snippet=line.strip()[:200],
                            owasp_id="LLM06",
                        ))
                        break
            except re.error:
                logger.debug("Invalid regex in permission_escalation: %s", regex)

        return findings

    # ── SKILL-008: Cross-tool manipulation ────────────────────────────

    def _check_cross_tool_manipulation(
        self, content: str, lines: list[str], file_path: str,
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        patterns = self.signatures.get("cross_tool", [])

        for pat_def in patterns:
            regex = pat_def["pattern"]
            try:
                for i, line in enumerate(lines, start=1):
                    if re.search(regex, line):
                        findings.append(_make_finding(
                            file_path=file_path,
                            line_number=i,
                            risk_id="SKILL-008",
                            severity="high",
                            description=(
                                f"Cross-tool manipulation: {pat_def['description']}"
                            ),
                            remediation=(
                                "Skills should not modify the configuration of other tools "
                                "or MCP servers. This can be used to install malicious "
                                "servers or change tool behavior."
                            ),
                            snippet=line.strip()[:200],
                            owasp_id="LLM06",
                        ))
                        break
            except re.error:
                logger.debug("Invalid regex in cross_tool: %s", regex)

        return findings
