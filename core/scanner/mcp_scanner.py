"""
MCP Configuration Discovery & Security Scanner.

Discovers MCP (Model Context Protocol) server configurations across platforms
(Cursor, Claude Desktop, VS Code, Windsurf, Gemini CLI) and checks for:
  MCP-001  Prompt injection in tool descriptions
  MCP-002  Tool poisoning (claimed function vs actual behavior mismatch)
  MCP-003  Tool shadowing (name collision with built-in tools)
  MCP-004  Toxic flows (dangerous capability chains across tools)
  MCP-005  Overprivileged server (unnecessary fs/net/shell access)
  MCP-006  Unverified server source (untrusted npm/pip/github package)
  MCP-007  Missing transport security (stdio where SSE would be safer)
"""

from __future__ import annotations

import json
import logging
import os
import platform
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx
import yaml

from ._finding import count_severities, make_agent_finding

logger = logging.getLogger(__name__)

# ── Signature loading ──────────────────────────────────────────────────────

_SIGNATURES: dict[str, Any] | None = None


def _load_mcp_signatures() -> dict[str, Any]:
    """Load the mcp_signatures.yaml file (cached on first call)."""
    global _SIGNATURES
    if _SIGNATURES is not None:
        return _SIGNATURES

    sig_path = Path(__file__).parent / "mcp_signatures.yaml"
    if sig_path.exists():
        with open(sig_path, encoding="utf-8") as fh:
            _SIGNATURES = yaml.safe_load(fh) or {}
    else:
        logger.warning("mcp_signatures.yaml not found at %s", sig_path)
        _SIGNATURES = {}
    return _SIGNATURES


# ── Data classes ───────────────────────────────────────────────────────────

@dataclass
class MCPServerInfo:
    """Parsed representation of a single MCP server entry."""

    name: str
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    transport: str = "stdio"  # stdio | sse
    url: str = ""
    tools: list[dict[str, Any]] = field(default_factory=list)
    source_file: str = ""
    platform: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def package_ref(self) -> str:
        """Best-guess package reference from command/args."""
        if self.command in ("npx", "npm", "pnpx"):
            for arg in self.args:
                if not arg.startswith("-"):
                    return arg
        if self.command in ("uvx", "pip", "pipx"):
            for arg in self.args:
                if not arg.startswith("-"):
                    return arg
        return self.command


@dataclass
class MCPConfig:
    """A discovered MCP configuration file."""

    path: str
    platform: str
    servers: list[MCPServerInfo] = field(default_factory=list)
    parse_error: str | None = None


# ── Finding constructor ────────────────────────────────────────────────────

def _make_finding(
    *,
    file_path: str,
    line_number: int = 0,
    risk_id: str,
    severity: str,
    description: str,
    remediation: str = "",
    server_name: str = "",
    snippet: str = "",
    owasp_id: str | None = None,
) -> dict[str, Any]:
    """Construct a finding dict compatible with the core engine format.

    Binds the MCP-specific constants onto the shared constructor; the dict
    itself is built in one place (``_finding.make_finding``).
    """
    return make_agent_finding(
        file_path=file_path,
        line_number=line_number,
        risk_id=risk_id,
        severity=severity,
        description=description,
        framework="mcp",
        component_type="mcp_server",
        remediation=remediation,
        provider=server_name,
        snippet=snippet,
        owasp_id=owasp_id,
    )


# ── MCPScanner ─────────────────────────────────────────────────────────────

class MCPScanner:
    """Discovers and analyses MCP server configurations for security risks."""

    # Platform → list of config paths (~ and env vars expanded at runtime)
    PLATFORM_CONFIGS: dict[str, list[str]] = {
        "cursor": [
            "~/.cursor/mcp.json",
            ".cursor/mcp.json",
        ],
        "claude_desktop": [
            "~/Library/Application Support/Claude/claude_desktop_config.json",
            "~/.config/Claude/claude_desktop_config.json",
            "%APPDATA%/Claude/claude_desktop_config.json",
        ],
        "vscode": [
            "~/.config/Code/User/settings.json",
        ],
        "windsurf": [
            "~/.codeium/windsurf/mcp_config.json",
        ],
        "gemini": [
            "~/.gemini/settings/mcp.json",
        ],
    }

    # File names considered MCP configs when found in a project directory
    PROJECT_CONFIG_NAMES: list[str] = [
        "mcp.json",
        "mcp_config.json",
        ".mcp.json",
    ]

    def __init__(self) -> None:
        self.signatures = _load_mcp_signatures()

    # ── Public API ─────────────────────────────────────────────────────

    def discover_configs(
        self,
        project_dir: Path | None = None,
        platform_filter: str | None = None,
    ) -> list[MCPConfig]:
        """Auto-discover MCP configuration files.

        Args:
            project_dir: If provided, also search this directory for
                project-level MCP configs.
            platform_filter: If provided, only discover configs for this
                platform (e.g. ``"cursor"``).

        Returns:
            A list of :class:`MCPConfig` objects (parsed or with errors).
        """
        configs: list[MCPConfig] = []

        platforms = self.PLATFORM_CONFIGS
        if platform_filter:
            pf = platform_filter.lower()
            platforms = {k: v for k, v in platforms.items() if k == pf}

        for plat, paths in platforms.items():
            for raw_path in paths:
                expanded = self._expand_path(raw_path)
                if expanded is None:
                    continue
                p = Path(expanded)
                if p.is_file():
                    cfg = self._parse_config(str(p), plat)
                    configs.append(cfg)

        # Project-level configs
        if project_dir is not None:
            for name in self.PROJECT_CONFIG_NAMES:
                p = project_dir / name
                if p.is_file():
                    cfg = self._parse_config(str(p), "project")
                    configs.append(cfg)
            # Also check .cursor/mcp.json relative to project
            cursor_proj = project_dir / ".cursor" / "mcp.json"
            if cursor_proj.is_file():
                cfg = self._parse_config(str(cursor_proj), "cursor")
                # Avoid duplicates
                if not any(c.path == str(cursor_proj) for c in configs):
                    configs.append(cfg)

        return configs

    def scan_configs(self, configs: list[MCPConfig]) -> list[dict[str, Any]]:
        """Run all MCP security checks across discovered configs.

        Returns a flat list of finding dicts.
        """
        findings: list[dict[str, Any]] = []
        all_servers: list[MCPServerInfo] = []

        for cfg in configs:
            if cfg.parse_error:
                findings.append(_make_finding(
                    file_path=cfg.path,
                    risk_id="MCP-000",
                    severity="low",
                    description=f"Failed to parse MCP config: {cfg.parse_error}",
                    remediation="Fix the JSON syntax in this configuration file.",
                ))
                continue

            for server in cfg.servers:
                all_servers.append(server)
                findings.extend(self._check_prompt_injection(server))
                findings.extend(self._check_tool_poisoning(server))
                findings.extend(self._check_tool_shadowing(server))
                findings.extend(self._check_overprivileged(server))
                findings.extend(self._check_unverified_source(server))
                findings.extend(self._check_transport_security(server))

        # Toxic flow analysis spans all servers
        findings.extend(self._analyze_toxic_flows(all_servers))

        return findings

    def scan(
        self,
        project_dir: Path | None = None,
        platform_filter: str | None = None,
    ) -> dict[str, Any]:
        """Convenience method: discover + scan in one call.

        Returns:
            ``{"configs": [...], "findings": [...], "summary": {...}}``
        """
        configs = self.discover_configs(project_dir, platform_filter)
        findings = self.scan_configs(configs)
        summary = self._build_summary(configs, findings)
        return {
            "configs": [self._serialize_config(c) for c in configs],
            "findings": findings,
            "summary": summary,
        }

    # ── Config parsing ─────────────────────────────────────────────────

    def _parse_config(self, path: str, plat: str) -> MCPConfig:
        """Read and parse a single MCP config file."""
        cfg = MCPConfig(path=path, platform=plat)
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            cfg.parse_error = str(exc)
            return cfg

        servers_dict = self._extract_servers_dict(data, plat)

        for name, srv_data in servers_dict.items():
            if not isinstance(srv_data, dict):
                continue
            server = MCPServerInfo(
                name=name,
                command=srv_data.get("command", ""),
                args=srv_data.get("args", []),
                env=srv_data.get("env", {}),
                transport=srv_data.get("transport", "stdio"),
                url=srv_data.get("url", ""),
                tools=srv_data.get("tools", []),
                source_file=path,
                platform=plat,
                raw=srv_data,
            )
            cfg.servers.append(server)

        return cfg

    @staticmethod
    def _extract_servers_dict(data: dict[str, Any], plat: str) -> dict[str, Any]:
        """Extract the mcpServers mapping from various config formats."""
        # Standard MCP format: {"mcpServers": {...}}
        if "mcpServers" in data:
            return data["mcpServers"]

        # VS Code nests under mcp.servers
        if plat == "vscode":
            mcp = data.get("mcp", {})
            if isinstance(mcp, dict):
                return mcp.get("servers", {})

        # Claude Desktop format
        if "mcpServers" not in data and "servers" in data:
            return data["servers"]

        # Flat format where the whole file is { "name": { "command": ... } }
        # Heuristic: if every value is a dict with "command", treat as servers
        if all(isinstance(v, dict) and "command" in v for v in data.values() if isinstance(v, dict)):
            return data

        return {}

    # ── MCP-001: Prompt injection in tool descriptions ────────────────

    def _check_prompt_injection(self, server: MCPServerInfo) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        sigs = self.signatures.get("prompt_injection", {})
        instruction_patterns = sigs.get("instruction_patterns", [])
        obfuscation_patterns = sigs.get("obfuscation_patterns", [])
        max_desc_len = sigs.get("max_normal_description_length", 500)

        # Check tool descriptions
        for tool in server.tools:
            desc = tool.get("description", "")
            tool_name = tool.get("name", "unknown_tool")

            # Check instruction-override phrases
            desc_lower = desc.lower()
            for pattern in instruction_patterns:
                if pattern.lower() in desc_lower:
                    findings.append(_make_finding(
                        file_path=server.source_file,
                        risk_id="MCP-001",
                        severity="high",
                        description=(
                            f"Prompt injection indicator in tool '{tool_name}' description: "
                            f"contains '{pattern}'"
                        ),
                        remediation=(
                            "Remove instruction-like language from tool descriptions. "
                            "Tool descriptions should only describe what the tool does, "
                            "not instruct the AI how to behave."
                        ),
                        server_name=server.name,
                        snippet=desc[:200],
                        owasp_id="LLM01",
                    ))
                    break  # One finding per tool for instruction patterns

            # Check obfuscation
            for obf in obfuscation_patterns:
                if re.search(obf["pattern"], desc):
                    findings.append(_make_finding(
                        file_path=server.source_file,
                        risk_id="MCP-001",
                        severity="high",
                        description=(
                            f"Obfuscated content in tool '{tool_name}' description: "
                            f"{obf['description']}"
                        ),
                        remediation=(
                            "Remove encoded or obfuscated content from tool descriptions. "
                            "Descriptions should be plain human-readable text."
                        ),
                        server_name=server.name,
                        snippet=desc[:200],
                        owasp_id="LLM01",
                    ))

            # Check length anomaly
            if len(desc) > max_desc_len:
                findings.append(_make_finding(
                    file_path=server.source_file,
                    risk_id="MCP-001",
                    severity="medium",
                    description=(
                        f"Unusually long description for tool '{tool_name}' "
                        f"({len(desc)} chars, threshold {max_desc_len}). "
                        f"May contain hidden instructions."
                    ),
                    remediation=(
                        "Keep tool descriptions concise. Long descriptions may contain "
                        "hidden prompt injection payloads."
                    ),
                    server_name=server.name,
                    snippet=desc[:200],
                    owasp_id="LLM01",
                ))

        # Also check server-level description if present
        srv_desc = server.raw.get("description", "")
        if srv_desc:
            desc_lower = srv_desc.lower()
            for pattern in instruction_patterns:
                if pattern.lower() in desc_lower:
                    findings.append(_make_finding(
                        file_path=server.source_file,
                        risk_id="MCP-001",
                        severity="high",
                        description=(
                            f"Prompt injection indicator in server '{server.name}' description: "
                            f"contains '{pattern}'"
                        ),
                        remediation="Remove instruction-like language from server descriptions.",
                        server_name=server.name,
                        snippet=srv_desc[:200],
                        owasp_id="LLM01",
                    ))
                    break

        return findings

    # ── MCP-002: Tool poisoning ───────────────────────────────────────

    def _check_tool_poisoning(self, server: MCPServerInfo) -> list[dict[str, Any]]:
        """Detect tools whose description mismatches their likely behavior."""
        findings: list[dict[str, Any]] = []

        # Heuristic: tool name suggests safe read-only, but args/env suggest write/exec
        safe_prefixes = {"read", "get", "list", "search", "query", "fetch", "view", "show"}
        danger_indicators = {"write", "delete", "exec", "run", "remove", "modify", "send", "post"}

        for tool in server.tools:
            tool_name = tool.get("name", "").lower()
            desc = tool.get("description", "").lower()

            # Tool name implies read-only
            name_is_safe = any(tool_name.startswith(p) for p in safe_prefixes)
            # Description mentions dangerous operations
            desc_has_danger = any(d in desc for d in danger_indicators)

            if name_is_safe and desc_has_danger:
                findings.append(_make_finding(
                    file_path=server.source_file,
                    risk_id="MCP-002",
                    severity="high",
                    description=(
                        f"Possible tool poisoning: tool '{tool.get('name', '')}' has a "
                        f"read-only name but description mentions write/exec operations."
                    ),
                    remediation=(
                        "Verify the tool actually performs only the operation its name suggests. "
                        "Rename or restrict tools that have misleading names."
                    ),
                    server_name=server.name,
                    snippet=f"name={tool.get('name', '')} desc={desc[:150]}",
                    owasp_id="LLM06",
                ))

        # Server-level: command suggests one thing, args suggest another
        cmd = server.command.lower()
        args_str = " ".join(str(a) for a in server.args).lower()

        if cmd in ("node", "npx", "python", "uvx") and any(
            d in args_str for d in ("--allow-exec", "--allow-write", "rm ", "del ", "curl ")
        ):
            findings.append(_make_finding(
                file_path=server.source_file,
                risk_id="MCP-002",
                severity="medium",
                description=(
                    f"Server '{server.name}' arguments contain potentially dangerous "
                    f"flags or commands that may not match its stated purpose."
                ),
                remediation="Review server arguments to ensure they match the server's stated purpose.",
                server_name=server.name,
                snippet=f"command={server.command} args={server.args}",
                owasp_id="LLM06",
            ))

        return findings

    # ── MCP-003: Tool shadowing ───────────────────────────────────────

    def _check_tool_shadowing(self, server: MCPServerInfo) -> list[dict[str, Any]]:
        """Detect tool names that collide with built-in/trusted names."""
        findings: list[dict[str, Any]] = []
        builtins = set(
            self.signatures.get("tool_shadowing", {}).get("builtin_tool_names", [])
        )

        for tool in server.tools:
            tool_name = tool.get("name", "").lower().strip()
            if tool_name in builtins:
                findings.append(_make_finding(
                    file_path=server.source_file,
                    risk_id="MCP-003",
                    severity="high",
                    description=(
                        f"Tool shadowing: '{tool.get('name', '')}' in server '{server.name}' "
                        f"collides with a common built-in tool name. An attacker could use this "
                        f"to intercept calls intended for the real tool."
                    ),
                    remediation=(
                        "Rename the tool to avoid collision with built-in tool names. "
                        "Use a namespaced name like 'myserver_read_file'."
                    ),
                    server_name=server.name,
                    snippet=f"tool_name={tool.get('name', '')}",
                    owasp_id="LLM06",
                ))

        # Also check server name against builtins
        if server.name.lower() in builtins:
            findings.append(_make_finding(
                file_path=server.source_file,
                risk_id="MCP-003",
                severity="medium",
                description=(
                    f"Server name '{server.name}' collides with a common built-in tool name."
                ),
                remediation="Rename the server to avoid confusion with built-in tools.",
                server_name=server.name,
            ))

        return findings

    # ── MCP-004: Toxic flows ──────────────────────────────────────────

    def _analyze_toxic_flows(
        self, servers: list[MCPServerInfo],
    ) -> list[dict[str, Any]]:
        """Detect dangerous capability chains across MCP servers/tools.

        Builds a networkx DiGraph where nodes are capability categories
        and edges connect capabilities present within the same server
        constellation. Then checks for known dangerous paths.
        """
        findings: list[dict[str, Any]] = []
        sigs = self.signatures.get("toxic_flows", {})
        cap_indicators = sigs.get("capability_indicators", {})
        dangerous_chains = sigs.get("dangerous_chains", [])

        if not cap_indicators or not dangerous_chains:
            return findings

        # Build a mapping: server_name -> set of capability categories
        server_caps: dict[str, set[str]] = {}
        for server in servers:
            caps: set[str] = set()
            # Derive capabilities from command, args, tool names, and env
            all_text = " ".join([
                server.command,
                " ".join(str(a) for a in server.args),
                " ".join(server.env.keys()),
                " ".join(t.get("name", "") for t in server.tools),
                " ".join(t.get("description", "") for t in server.tools),
            ]).lower()

            for cap_name, cap_data in cap_indicators.items():
                keywords = cap_data.get("keywords", [])
                if any(kw in all_text for kw in keywords):
                    caps.add(cap_name)

            server_caps[server.name] = caps

        # Build a capability graph across ALL servers in the environment
        # (since an agent can chain tools from different servers)
        G = nx.DiGraph()
        all_caps: set[str] = set()
        for caps in server_caps.values():
            all_caps.update(caps)

        for cap in all_caps:
            G.add_node(cap)

        # Add edges between capabilities that co-exist across the server set
        # (any source cap from any server can flow to any sink cap from any server)
        for cap_a in all_caps:
            for cap_b in all_caps:
                if cap_a != cap_b:
                    G.add_edge(cap_a, cap_b)

        # Check for dangerous chains
        for chain in dangerous_chains:
            source = chain["source"]
            sink = chain["sink"]
            if source in all_caps and sink in all_caps:
                # Find which servers provide each capability
                source_servers = [
                    s for s, caps in server_caps.items() if source in caps
                ]
                sink_servers = [
                    s for s, caps in server_caps.items() if sink in caps
                ]

                # Get the file path from the first server that has the source cap
                source_file = ""
                for srv in servers:
                    if srv.name in source_servers:
                        source_file = srv.source_file
                        break
                if not source_file:
                    for srv in servers:
                        if srv.name in sink_servers:
                            source_file = srv.source_file
                            break

                findings.append(_make_finding(
                    file_path=source_file or "unknown",
                    risk_id="MCP-004",
                    severity=chain.get("severity", "high"),
                    description=(
                        f"Toxic flow detected: {chain['description']}. "
                        f"Source ({source}): {', '.join(source_servers)}. "
                        f"Sink ({sink}): {', '.join(sink_servers)}."
                    ),
                    remediation=(
                        "Review whether these servers need to be installed together. "
                        "Consider removing unnecessary servers or restricting their "
                        "capabilities to break dangerous chains."
                    ),
                    server_name=", ".join(source_servers + sink_servers),
                    snippet=f"{source} -> {sink}",
                    owasp_id="LLM06",
                ))

        return findings

    # ── MCP-005: Overprivileged server ────────────────────────────────

    def _check_overprivileged(self, server: MCPServerInfo) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        overpriv = self.signatures.get("overprivileged", {})

        checks = [
            ("filesystem_indicators", "filesystem access"),
            ("network_indicators", "network access"),
            ("shell_indicators", "shell execution"),
        ]

        for indicator_key, access_type in checks:
            indicators = overpriv.get(indicator_key, {})
            arg_patterns = indicators.get("args", [])
            env_patterns = indicators.get("env", [])

            args_str = " ".join(str(a) for a in server.args)
            cmd_args = f"{server.command} {args_str}"

            matched_args = [p for p in arg_patterns if p.lower() in cmd_args.lower()]
            matched_env = [p for p in env_patterns if p in server.env]

            if matched_args or matched_env:
                detail_parts = []
                if matched_args:
                    detail_parts.append(f"args contain {matched_args}")
                if matched_env:
                    detail_parts.append(f"env contains {matched_env}")

                findings.append(_make_finding(
                    file_path=server.source_file,
                    risk_id="MCP-005",
                    severity="medium",
                    description=(
                        f"Server '{server.name}' has {access_type}: "
                        f"{'; '.join(detail_parts)}. "
                        f"Verify this level of access is necessary."
                    ),
                    remediation=(
                        f"Review whether '{server.name}' needs {access_type}. "
                        f"Apply principle of least privilege: restrict to specific "
                        f"directories, disable network access, or remove shell permissions."
                    ),
                    server_name=server.name,
                    snippet=f"command={server.command} args={server.args}",
                    owasp_id="LLM06",
                ))

        return findings

    # ── MCP-006: Unverified server source ─────────────────────────────

    def _check_unverified_source(self, server: MCPServerInfo) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        source_sigs = self.signatures.get("unverified_sources", {})
        trusted_npm = source_sigs.get("trusted_npm_scopes", [])
        trusted_pip = source_sigs.get("trusted_pip_prefixes", [])
        untrusted_patterns = source_sigs.get("untrusted_patterns", [])

        pkg = server.package_ref

        if not pkg:
            return findings

        # Check npm packages
        if server.command in ("npx", "npm", "pnpx"):
            is_trusted = any(pkg.startswith(scope) for scope in trusted_npm)
            if not is_trusted:
                # Check against untrusted patterns
                for utp in untrusted_patterns:
                    if re.search(utp["pattern"], pkg):
                        findings.append(_make_finding(
                            file_path=server.source_file,
                            risk_id="MCP-006",
                            severity="high",
                            description=(
                                f"Server '{server.name}' installed from untrusted source: "
                                f"{pkg}. {utp['description']}."
                            ),
                            remediation=(
                                "Verify the package source. Prefer installing from trusted "
                                "npm scopes (@modelcontextprotocol/, @anthropic-ai/, etc.) "
                                "or audit the package before use."
                            ),
                            server_name=server.name,
                            snippet=f"package={pkg}",
                            owasp_id="LLM03",
                        ))
                        return findings

                # Generic untrusted npm package
                if not pkg.startswith("@"):
                    findings.append(_make_finding(
                        file_path=server.source_file,
                        risk_id="MCP-006",
                        severity="medium",
                        description=(
                            f"Server '{server.name}' uses unscoped npm package '{pkg}'. "
                            f"Cannot verify publisher identity."
                        ),
                        remediation=(
                            "Prefer scoped npm packages from trusted organizations. "
                            "Audit the package source code before installing."
                        ),
                        server_name=server.name,
                        snippet=f"package={pkg}",
                        owasp_id="LLM03",
                    ))

        # Check pip packages
        elif server.command in ("uvx", "pip", "pipx", "python", "python3"):
            is_trusted = any(pkg.startswith(prefix) for prefix in trusted_pip)
            if not is_trusted:
                for utp in untrusted_patterns:
                    if re.search(utp["pattern"], pkg):
                        findings.append(_make_finding(
                            file_path=server.source_file,
                            risk_id="MCP-006",
                            severity="high",
                            description=(
                                f"Server '{server.name}' installed from untrusted source: "
                                f"{pkg}. {utp['description']}."
                            ),
                            remediation=(
                                "Verify the package source. Prefer well-known PyPI packages "
                                "or audit the package before use."
                            ),
                            server_name=server.name,
                            snippet=f"package={pkg}",
                            owasp_id="LLM03",
                        ))
                        return findings

        return findings

    # ── MCP-007: Missing transport security ───────────────────────────

    def _check_transport_security(self, server: MCPServerInfo) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        transport_sigs = self.signatures.get("transport", {})
        sensitive_caps = set(transport_sigs.get("sensitive_capabilities", []))

        if server.transport != "stdio":
            # If using SSE, check for TLS
            if server.url and server.url.startswith("http://"):
                findings.append(_make_finding(
                    file_path=server.source_file,
                    risk_id="MCP-007",
                    severity="high",
                    description=(
                        f"Server '{server.name}' uses SSE transport without TLS "
                        f"(http:// instead of https://)."
                    ),
                    remediation="Use HTTPS for SSE transport to encrypt data in transit.",
                    server_name=server.name,
                    snippet=f"url={server.url}",
                ))
            return findings

        # stdio transport — check if server handles sensitive capabilities
        cap_indicators = self.signatures.get("toxic_flows", {}).get("capability_indicators", {})
        all_text = " ".join([
            server.command,
            " ".join(str(a) for a in server.args),
            " ".join(server.env.keys()),
        ]).lower()

        server_caps: set[str] = set()
        for cap_name, cap_data in cap_indicators.items():
            keywords = cap_data.get("keywords", [])
            if any(kw in all_text for kw in keywords):
                server_caps.add(cap_name)

        overlapping = server_caps & sensitive_caps
        if overlapping:
            findings.append(_make_finding(
                file_path=server.source_file,
                risk_id="MCP-007",
                severity="low",
                description=(
                    f"Server '{server.name}' uses stdio transport but handles "
                    f"sensitive capabilities: {', '.join(sorted(overlapping))}. "
                    f"SSE transport provides better isolation."
                ),
                remediation=(
                    "Consider using SSE (Server-Sent Events) transport with TLS "
                    "for servers that handle sensitive operations like "
                    f"{', '.join(sorted(overlapping))}."
                ),
                server_name=server.name,
                snippet=f"transport=stdio capabilities={sorted(overlapping)}",
            ))

        return findings

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _expand_path(raw: str) -> str | None:
        """Expand ~ and %VAR% in a path. Returns None if not applicable to this OS."""
        # Skip Windows paths on non-Windows
        if "%" in raw and platform.system() != "Windows":
            return None
        # Skip macOS-specific paths on non-macOS
        if "Library/Application Support" in raw and platform.system() != "Darwin":
            return None
        # Skip Linux-specific paths on non-Linux
        if raw.startswith("~/.config/") and platform.system() == "Windows":
            return None

        expanded = os.path.expanduser(raw)
        expanded = os.path.expandvars(expanded)
        return expanded

    @staticmethod
    def _build_summary(
        configs: list[MCPConfig],
        findings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build summary statistics from scan results."""
        total_servers = sum(len(c.servers) for c in configs)
        platforms: dict[str, int] = {}
        for c in configs:
            platforms[c.platform] = platforms.get(c.platform, 0) + len(c.servers)

        severities: dict[str, int] = count_severities(findings)
        risk_ids: dict[str, int] = {}
        for f in findings:
            rid = f.get("risk_id", "")
            risk_ids[rid] = risk_ids.get(rid, 0) + 1

        return {
            "configs_discovered": len(configs),
            "total_servers": total_servers,
            "platforms": platforms,
            "total_findings": len(findings),
            "severities": severities,
            "risk_ids": risk_ids,
        }

    @staticmethod
    def _serialize_config(cfg: MCPConfig) -> dict[str, Any]:
        """Serialize an MCPConfig for JSON output."""
        return {
            "path": cfg.path,
            "platform": cfg.platform,
            "parse_error": cfg.parse_error,
            "servers": [
                {
                    "name": s.name,
                    "command": s.command,
                    "args": s.args,
                    "transport": s.transport,
                    "platform": s.platform,
                }
                for s in cfg.servers
            ],
        }
