import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import {
  ArrowRight, Terminal, Server, Database, Shield, Eye, GitBranch,
  FileCode, Search, AlertTriangle, BarChart3, FileText, Network,
  Cpu, Lock, Layers, Box, Workflow, ChevronDown, ChevronUp
} from 'lucide-react';

const Architecture = () => {
  const navigate = useNavigate();
  const [expandedLayer, setExpandedLayer] = useState(null);

  const toggleLayer = (id) => {
    setExpandedLayer(expandedLayer === id ? null : id);
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">

      {/* Hero */}
      <section className="relative overflow-hidden py-20 px-6">
        <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 via-transparent to-transparent" />
        <div className="relative max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm mb-6">
            <Layers className="w-4 h-4" />
            System Architecture
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            How ScanLLM is <span className="text-cyan-400">Built</span>
          </h1>
          <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
            A layered architecture designed for extensibility, speed, and enterprise-grade security scanning.
          </p>
        </div>
      </section>

      {/* High-Level Architecture Diagram */}
      <section className="px-6 pb-16">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-8 text-center">System Overview</h2>
          <div className="relative">

            {/* CLI / Web UI Layer */}
            <div className="border border-cyan-500/30 rounded-xl bg-cyan-500/5 p-6 mb-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                  <Terminal className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <h3 className="font-bold text-cyan-400">Interface Layer</h3>
                  <p className="text-zinc-500 text-sm">User-facing entry points</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { name: 'CLI (Typer)', desc: 'pip install scanllm', icon: Terminal },
                  { name: 'Web Dashboard', desc: 'React + Tailwind', icon: Eye },
                  { name: 'GitHub Actions', desc: 'CI/CD integration', icon: GitBranch },
                  { name: 'REST API', desc: 'FastAPI v1', icon: Server },
                ].map((item, i) => (
                  <div key={i} className="bg-zinc-900/80 rounded-lg p-3 border border-zinc-800/50">
                    <item.icon className="w-4 h-4 text-cyan-400 mb-1" />
                    <div className="text-sm font-medium">{item.name}</div>
                    <div className="text-xs text-zinc-500">{item.desc}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Arrow */}
            <div className="flex justify-center py-2">
              <div className="flex flex-col items-center">
                <div className="w-px h-4 bg-zinc-600" />
                <ArrowRight className="w-4 h-4 text-zinc-500 rotate-90" />
                <div className="text-xs text-zinc-600 mt-1">commands / API calls</div>
              </div>
            </div>

            {/* Scanning Engine Layer */}
            <div className="border border-orange-500/30 rounded-xl bg-orange-500/5 p-6 mb-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
                  <Search className="w-5 h-5 text-orange-400" />
                </div>
                <div>
                  <h3 className="font-bold text-orange-400">Scanning Engine</h3>
                  <p className="text-zinc-500 text-sm">7 specialized scanners, 200+ detection patterns</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { name: 'Python AST', desc: 'Import/call/model analysis', icon: FileCode },
                  { name: 'JS/TS Regex', desc: 'ES6 import/require', icon: FileCode },
                  { name: 'Config Parser', desc: 'YAML/JSON/TOML/ENV', icon: FileText },
                  { name: 'Dependency', desc: 'requirements/package.json', icon: Box },
                  { name: 'Secret Scanner', desc: '30+ AI key patterns', icon: Lock },
                  { name: 'Notebook', desc: '.ipynb cell extraction', icon: FileCode },
                  { name: 'License', desc: 'Restrictive license flags', icon: Shield },
                  { name: 'Prompt Inventory', desc: 'AST prompt extraction', icon: Search },
                ].map((item, i) => (
                  <div key={i} className="bg-zinc-900/80 rounded-lg p-3 border border-zinc-800/50">
                    <item.icon className="w-4 h-4 text-orange-400 mb-1" />
                    <div className="text-sm font-medium">{item.name}</div>
                    <div className="text-xs text-zinc-500">{item.desc}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Arrow */}
            <div className="flex justify-center py-2">
              <div className="flex flex-col items-center">
                <div className="w-px h-4 bg-zinc-600" />
                <ArrowRight className="w-4 h-4 text-zinc-500 rotate-90" />
                <div className="text-xs text-zinc-600 mt-1">findings</div>
              </div>
            </div>

            {/* Analysis Layer */}
            <div className="border border-purple-500/30 rounded-xl bg-purple-500/5 p-6 mb-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <Cpu className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <h3 className="font-bold text-purple-400">Analysis & Intelligence</h3>
                  <p className="text-zinc-500 text-sm">Risk scoring, graph construction, OWASP mapping</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { name: 'Risk Engine', desc: '0-100 scoring, A-F grades', icon: BarChart3 },
                  { name: 'OWASP Mapper', desc: 'LLM Top 10 coverage', icon: Shield },
                  { name: 'Graph Builder', desc: 'NetworkX dependency map', icon: Network },
                  { name: 'Policy Engine', desc: '12 built-in rules', icon: AlertTriangle },
                  { name: 'Config Health', desc: 'Best practice checks', icon: Search },
                  { name: 'Cost Estimator', desc: 'Token usage analysis', icon: BarChart3 },
                  { name: 'Drift Detector', desc: 'Scan-to-scan diff', icon: GitBranch },
                  { name: 'Auto-Fix', desc: 'Remediation engine', icon: Workflow },
                ].map((item, i) => (
                  <div key={i} className="bg-zinc-900/80 rounded-lg p-3 border border-zinc-800/50">
                    <item.icon className="w-4 h-4 text-purple-400 mb-1" />
                    <div className="text-sm font-medium">{item.name}</div>
                    <div className="text-xs text-zinc-500">{item.desc}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Arrow */}
            <div className="flex justify-center py-2">
              <div className="flex flex-col items-center">
                <div className="w-px h-4 bg-zinc-600" />
                <ArrowRight className="w-4 h-4 text-zinc-500 rotate-90" />
                <div className="text-xs text-zinc-600 mt-1">reports / visualizations</div>
              </div>
            </div>

            {/* Output Layer */}
            <div className="border border-emerald-500/30 rounded-xl bg-emerald-500/5 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <h3 className="font-bold text-emerald-400">Output & Reports</h3>
                  <p className="text-zinc-500 text-sm">Multiple export formats for every audience</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {[
                  { name: 'Rich Table', desc: 'Terminal output' },
                  { name: 'JSON', desc: 'Machine-readable' },
                  { name: 'SARIF', desc: 'IDE integration' },
                  { name: 'CycloneDX', desc: 'AI-BOM standard' },
                  { name: 'PDF Report', desc: 'Executive summary' },
                  { name: 'Model Card', desc: 'Google format' },
                  { name: 'Markdown', desc: 'Docs / wiki' },
                  { name: 'React Flow', desc: 'Interactive graph' },
                  { name: 'PR Comment', desc: 'GitHub inline' },
                  { name: 'Audit Log', desc: 'Compliance trail' },
                ].map((item, i) => (
                  <div key={i} className="bg-zinc-900/80 rounded-lg p-3 border border-zinc-800/50">
                    <div className="text-sm font-medium">{item.name}</div>
                    <div className="text-xs text-zinc-500">{item.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Data Flow Detail */}
      <section className="px-6 pb-16">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-8 text-center">Scan Data Flow</h2>
          <div className="space-y-3">
            {[
              {
                id: 'clone',
                step: '1',
                title: 'Repository Ingestion',
                summary: 'Clone via GitPython or read local directory',
                color: 'cyan',
                details: [
                  'Public repos: clone by URL, no auth required',
                  'Private repos: GitHub OAuth token injection',
                  'Local mode: direct filesystem walk, no clone needed',
                  'Temp directory cleanup on completion',
                ]
              },
              {
                id: 'walk',
                step: '2',
                title: 'File Discovery & Filtering',
                summary: '20+ file extensions across Python, JS/TS, configs, notebooks',
                color: 'cyan',
                details: [
                  '.py, .js, .ts, .jsx, .tsx — source code',
                  '.yaml, .yml, .json, .toml, .env — configuration',
                  '.ipynb — Jupyter notebooks (code cell extraction)',
                  'requirements.txt, pyproject.toml, package.json — dependencies',
                  'Dockerfile, docker-compose.yml, .github/workflows/*.yml — infra',
                  'Respects .gitignore and .scanllmignore patterns',
                ]
              },
              {
                id: 'parse',
                step: '3',
                title: 'Multi-Scanner Parallel Analysis',
                summary: 'Each scanner specializes in a file type and extraction method',
                color: 'orange',
                details: [
                  'Python AST: ast.NodeVisitor walks Import, ImportFrom, Call, Assign nodes',
                  'JS/TS: Regex-based pattern matching for ES6 imports, require(), SDK calls',
                  'Config: PyYAML/json/tomllib parsing for model refs, endpoints, MCP configs',
                  'Dependencies: Cross-reference against 200+ AI package signatures',
                  'Secrets: detect-secrets + 30 custom AI key patterns (OPENAI_API_KEY, etc.)',
                  'Notebooks: JSON parsing → code cell extraction → Python scanner per cell',
                  'License: AI package license database, flags GPL/AGPL/SSPL',
                  'Prompts: AST extraction of system prompts, user input injection detection',
                ]
              },
              {
                id: 'classify',
                step: '4',
                title: 'Finding Classification',
                summary: 'Tag each finding with component type and metadata',
                color: 'orange',
                details: [
                  'Component types: llm_provider, embedding_service, vector_db, orchestration_framework',
                  'Additional: agent_tool, prompt_file, mcp_server, inference_server, ai_package, secret',
                  'Metadata: file path, line number, confidence score, provider name, model name',
                  'OWASP mapping: each finding mapped to LLM01-LLM10 categories',
                ]
              },
              {
                id: 'graph',
                step: '5',
                title: 'Dependency Graph Construction',
                summary: 'NetworkX DiGraph with file-level and component-level edges',
                color: 'purple',
                details: [
                  'Nodes: each AI component (provider, model, framework, tool)',
                  'Edges: import chains, data flow, config references, agent tools',
                  'Layout: dagre algorithm for automatic hierarchical positioning',
                  'Metrics: concentration risk, blast radius, single points of failure',
                  'Serialized to React Flow JSON format for interactive visualization',
                ]
              },
              {
                id: 'score',
                step: '6',
                title: 'Risk Scoring & Policy Evaluation',
                summary: '0-100 composite score with OWASP weighting and policy rules',
                color: 'purple',
                details: [
                  'Secrets: +25 per hardcoded key (critical)',
                  'OWASP critical findings: +20 each (eval/exec, supply chain)',
                  'OWASP high findings: +10 each (prompt injection, excessive agency)',
                  'Outdated packages: +5 each (known CVEs)',
                  'Provider concentration: +10 if >80% single provider',
                  'Missing safety configs: +3 each (no max_tokens, no timeout)',
                  'Policy rules: 12 built-in + custom YAML policies',
                  'Grade: A (0-20), B (21-40), C (41-60), D (61-80), F (81-100)',
                ]
              },
            ].map((item) => (
              <div key={item.id} className="border border-zinc-800/50 rounded-lg overflow-hidden">
                <button
                  onClick={() => toggleLayer(item.id)}
                  className="w-full flex items-center gap-4 p-4 hover:bg-zinc-900/50 transition-colors"
                >
                  <div className={`w-8 h-8 rounded-full bg-${item.color}-500/20 flex items-center justify-center text-${item.color}-400 font-bold text-sm flex-shrink-0`}>
                    {item.step}
                  </div>
                  <div className="text-left flex-1">
                    <div className="font-semibold">{item.title}</div>
                    <div className="text-sm text-zinc-500">{item.summary}</div>
                  </div>
                  {expandedLayer === item.id ? (
                    <ChevronUp className="w-5 h-5 text-zinc-500 flex-shrink-0" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-zinc-500 flex-shrink-0" />
                  )}
                </button>
                {expandedLayer === item.id && (
                  <div className="px-4 pb-4 pl-16">
                    <ul className="space-y-1">
                      {item.details.map((d, i) => (
                        <li key={i} className="text-sm text-zinc-400 flex items-start gap-2">
                          <span className="text-zinc-600 mt-1.5 block w-1 h-1 rounded-full bg-zinc-600 flex-shrink-0" />
                          {d}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="px-6 pb-16">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-8 text-center">Tech Stack</h2>
          <div className="grid md:grid-cols-2 gap-6">

            <div className="border border-zinc-800/50 rounded-xl p-6">
              <h3 className="font-bold text-cyan-400 mb-4 flex items-center gap-2">
                <Server className="w-5 h-5" /> Backend
              </h3>
              <div className="space-y-3">
                {[
                  { name: 'FastAPI', role: 'REST API framework', version: 'Python 3.9+' },
                  { name: 'SQLAlchemy', role: 'ORM + database', version: 'SQLite / PostgreSQL' },
                  { name: 'Typer + Rich', role: 'CLI framework', version: 'Terminal UI' },
                  { name: 'GitPython', role: 'Repository cloning', version: 'Git operations' },
                  { name: 'NetworkX', role: 'Dependency graph', version: 'Graph analysis' },
                  { name: 'detect-secrets', role: 'Secret detection', version: 'Yelp engine' },
                  { name: 'CycloneDX', role: 'AI-BOM generation', version: 'v1.6 spec' },
                  { name: 'Jinja2 + xhtml2pdf', role: 'PDF report generation', version: 'Templates' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium">{item.name}</span>
                      <span className="text-sm text-zinc-500 ml-2">— {item.role}</span>
                    </div>
                    <span className="text-xs text-zinc-600 bg-zinc-900 px-2 py-0.5 rounded">{item.version}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="border border-zinc-800/50 rounded-xl p-6">
              <h3 className="font-bold text-cyan-400 mb-4 flex items-center gap-2">
                <Eye className="w-5 h-5" /> Frontend
              </h3>
              <div className="space-y-3">
                {[
                  { name: 'React 19', role: 'UI framework', version: 'Functional components' },
                  { name: 'Tailwind CSS', role: 'Styling', version: 'Utility-first' },
                  { name: 'shadcn/ui', role: 'Component library', version: 'Radix primitives' },
                  { name: 'React Flow', role: 'Dependency graph viz', version: '@xyflow/react' },
                  { name: 'Recharts', role: 'Charts and metrics', version: 'SVG-based' },
                  { name: 'React Table', role: 'Data tables', version: '@tanstack/react-table' },
                  { name: 'Axios', role: 'API client', version: 'HTTP requests' },
                  { name: 'React Router', role: 'Client routing', version: 'v6' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium">{item.name}</span>
                      <span className="text-sm text-zinc-500 ml-2">— {item.role}</span>
                    </div>
                    <span className="text-xs text-zinc-600 bg-zinc-900 px-2 py-0.5 rounded">{item.version}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 pb-20">
        <div className="max-w-3xl mx-auto text-center">
          <div className="border border-zinc-800/50 rounded-xl p-8 bg-gradient-to-b from-zinc-900/50 to-transparent">
            <h2 className="text-2xl font-bold mb-3">Ready to scan?</h2>
            <p className="text-zinc-400 mb-6">Install ScanLLM and discover every AI component in your codebase in under 60 seconds.</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <div className="bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 font-mono text-sm text-cyan-400">
                pip install scanllm
              </div>
              <Button onClick={() => navigate('/demo')} className="bg-cyan-600 hover:bg-cyan-500 text-white">
                Try Live Demo <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Architecture;
