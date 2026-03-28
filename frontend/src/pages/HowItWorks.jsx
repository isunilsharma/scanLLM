import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { ArrowRight, GitBranch, Search, ShieldCheck, BarChart3, FileCode, Terminal, Zap, Lock, Eye } from 'lucide-react';

const HowItWorks = () => {
  const navigate = useNavigate();

  const steps = [
    {
      number: '01',
      title: 'Install the CLI',
      description: 'One command. No config files, no signup, no API keys. Works on any Python 3.11+ environment.',
      icon: Terminal,
      color: 'cyan',
      code: 'pip install scanllm',
    },
    {
      number: '02',
      title: 'Scan your codebase',
      description: 'ScanLLM walks every file — Python AST analysis, JS/TS regex scanning, config parsing, dependency extraction, notebook cells, and secret detection.',
      icon: Search,
      color: 'blue',
      code: 'scanllm scan .',
    },
    {
      number: '03',
      title: 'Enforce policies in CI/CD',
      description: 'Define rules in YAML. Block PRs with hardcoded secrets, unapproved providers, or excessive agent permissions. Exit code 1 fails the build.',
      icon: ShieldCheck,
      color: 'green',
      code: 'scanllm policy check',
    },
  ];

  const scannerDetails = [
    {
      icon: FileCode,
      title: 'Python AST Scanner',
      description: 'Walks the abstract syntax tree to find imports, API calls, model parameters, and prompt injection risks. Not regex — real code analysis.',
      detects: ['openai.ChatCompletion.create()', 'f"Help with: {user_input}"', 'model="gpt-4o"'],
    },
    {
      icon: GitBranch,
      title: 'JS/TS Scanner',
      description: 'Pattern-based detection for JavaScript and TypeScript — imports, SDK instantiation, Vercel AI SDK, LangChain.js, and more.',
      detects: ["import OpenAI from 'openai'", 'generateText()', '@langchain/core'],
    },
    {
      icon: Lock,
      title: 'Secret Scanner',
      description: 'Finds hardcoded AI API keys in code, configs, and .env files. 30+ provider patterns including OpenAI, Anthropic, Google, Pinecone, HuggingFace.',
      detects: ['OPENAI_API_KEY="sk-..."', 'ANTHROPIC_API_KEY in .env', 'HF_TOKEN in config.yaml'],
    },
    {
      icon: Eye,
      title: 'Config & Dependency Scanner',
      description: 'Parses YAML, JSON, TOML, Dockerfiles, and package manifests. Finds model references, inference servers, MCP configurations, and AI packages.',
      detects: ['requirements.txt → openai==1.82.0', 'docker-compose → ollama service', 'claude_desktop_config.json'],
    },
  ];

  const outputFormats = [
    { name: 'Table', desc: 'Rich terminal output with color-coded severity', cmd: 'scanllm scan . --output table' },
    { name: 'JSON', desc: 'Machine-readable for custom tooling', cmd: 'scanllm scan . --output json' },
    { name: 'SARIF', desc: 'Upload to GitHub Code Scanning', cmd: 'scanllm scan . --output sarif' },
    { name: 'CycloneDX', desc: 'AI-BOM for SOC 2, EU AI Act compliance', cmd: 'scanllm report aibom' },
    { name: 'PDF', desc: 'Executive report for stakeholders', cmd: 'scanllm report pdf' },
  ];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/20 via-transparent to-transparent" />
        <div className="relative max-w-5xl mx-auto px-6 pt-20 pb-16">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-medium mb-6 border border-blue-500/20">
              <Zap className="w-3.5 h-3.5" />
              7 specialized scanners &middot; 200+ AI patterns &middot; 30+ providers
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6 leading-[1.1]">
              How ScanLLM{' '}
              <span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                works
              </span>
            </h1>
            <p className="text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto leading-relaxed">
              From <code className="text-cyan-400 bg-zinc-900 px-2 py-0.5 rounded text-base">pip install</code> to
              a complete AI inventory in under 60 seconds.
            </p>
          </div>
        </div>
      </section>

      {/* 3 Steps */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="space-y-6">
          {steps.map((step) => {
            const Icon = step.icon;
            return (
              <div key={step.number} className="group relative">
                <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-8 hover:border-zinc-700 transition-all duration-300">
                  <div className="flex flex-col md:flex-row gap-6 items-start">
                    <div className="flex items-center gap-4 flex-shrink-0">
                      <span className="text-4xl font-bold text-zinc-800 group-hover:text-zinc-700 transition-colors">
                        {step.number}
                      </span>
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                        step.color === 'cyan' ? 'bg-cyan-500/10 text-cyan-400' :
                        step.color === 'blue' ? 'bg-blue-500/10 text-blue-400' :
                        'bg-green-500/10 text-green-400'
                      }`}>
                        <Icon className="w-6 h-6" />
                      </div>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-zinc-100 mb-2">{step.title}</h3>
                      <p className="text-zinc-400 leading-relaxed mb-4">{step.description}</p>
                      <div className="inline-flex items-center gap-3 px-4 py-2 rounded-lg bg-zinc-950 border border-zinc-800 font-mono text-sm">
                        <span className="text-green-400">$</span>
                        <span className="text-zinc-300">{step.code}</span>
                        <button
                          onClick={() => navigator.clipboard.writeText(step.code)}
                          className="text-xs text-zinc-600 hover:text-zinc-300 transition-colors ml-2"
                        >
                          Copy
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* What the scanner detects */}
      <section className="border-t border-zinc-800/50">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-zinc-100 mb-4">
              What the scanner detects
            </h2>
            <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
              Seven specialized scanners work together to build a complete picture of your AI dependencies.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {scannerDetails.map((scanner) => {
              const Icon = scanner.icon;
              return (
                <div key={scanner.title} className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-all">
                  <div className="flex items-center gap-3 mb-3">
                    <Icon className="w-5 h-5 text-cyan-400" />
                    <h3 className="font-semibold text-zinc-100">{scanner.title}</h3>
                  </div>
                  <p className="text-zinc-400 text-sm leading-relaxed mb-4">{scanner.description}</p>
                  <div className="space-y-1.5">
                    {scanner.detects.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <span className="w-1 h-1 rounded-full bg-cyan-400 flex-shrink-0" />
                        <code className="text-xs text-zinc-500 font-mono">{item}</code>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* OWASP LLM Top 10 */}
      <section className="border-t border-zinc-800/50">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-zinc-100 mb-4">
              OWASP LLM Top 10 coverage
            </h2>
            <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
              Every finding is mapped to the OWASP LLM Top 10 (2025) framework. 8 of 10 categories detected statically.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-800">
                  <th className="text-left py-3 px-4 text-zinc-500 font-medium">ID</th>
                  <th className="text-left py-3 px-4 text-zinc-500 font-medium">Vulnerability</th>
                  <th className="text-left py-3 px-4 text-zinc-500 font-medium">What ScanLLM detects</th>
                  <th className="text-center py-3 px-4 text-zinc-500 font-medium">Severity</th>
                </tr>
              </thead>
              <tbody className="text-zinc-400">
                {[
                  ['LLM01', 'Prompt Injection', 'User input concatenated into prompts (f-strings, .format())', 'High'],
                  ['LLM02', 'Sensitive Info Disclosure', 'Credentials in system prompts, missing output filtering', 'High'],
                  ['LLM03', 'Supply Chain', 'Unverified model sources, outdated AI packages', 'Critical'],
                  ['LLM05', 'Improper Output Handling', 'eval(llm_response), unsanitized output to SQL/shell', 'Critical'],
                  ['LLM06', 'Excessive Agency', 'Agents with broad tool access, no human-in-the-loop', 'High'],
                  ['LLM07', 'System Prompt Leakage', 'API keys in prompt templates, business logic exposure', 'Medium'],
                  ['LLM08', 'Vector/Embedding Weaknesses', 'Unauthenticated vector DB connections', 'Medium'],
                  ['LLM10', 'Unbounded Consumption', 'Missing max_tokens, no rate limiting, no timeouts', 'Low'],
                ].map(([id, name, detects, severity]) => (
                  <tr key={id} className="border-b border-zinc-800/50">
                    <td className="py-3 px-4 text-cyan-400 font-mono text-xs">{id}</td>
                    <td className="py-3 px-4 text-zinc-300 font-medium">{name}</td>
                    <td className="py-3 px-4 text-zinc-500 text-xs">{detects}</td>
                    <td className="text-center py-3 px-4">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        severity === 'Critical' ? 'bg-red-500/10 text-red-400' :
                        severity === 'High' ? 'bg-orange-500/10 text-orange-400' :
                        severity === 'Medium' ? 'bg-yellow-500/10 text-yellow-400' :
                        'bg-zinc-800 text-zinc-500'
                      }`}>
                        {severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Output Formats */}
      <section className="border-t border-zinc-800/50">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-zinc-100 mb-4">
              Output in any format
            </h2>
            <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
              Feed results into your existing security and compliance toolchain.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {outputFormats.map((format) => (
              <div key={format.name} className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-5 hover:border-zinc-700 transition-all">
                <h3 className="font-semibold text-zinc-100 mb-1">{format.name}</h3>
                <p className="text-zinc-500 text-sm mb-3">{format.desc}</p>
                <code className="text-xs text-cyan-400/80 font-mono">{format.cmd}</code>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Full CLI Reference */}
      <section className="border-t border-zinc-800/50">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-zinc-100 mb-4">
              Full CLI reference
            </h2>
          </div>

          <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 bg-zinc-900 border-b border-zinc-800">
              <div className="w-3 h-3 rounded-full bg-red-500/80" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
              <div className="w-3 h-3 rounded-full bg-green-500/80" />
              <span className="text-zinc-500 text-xs ml-2 font-mono">Terminal</span>
            </div>
            <div className="p-6 font-mono text-sm space-y-4">
              {[
                { cmd: 'scanllm scan .', desc: 'Scan current directory for AI dependencies' },
                { cmd: 'scanllm init', desc: 'Initialize .scanllm/ config and policies' },
                { cmd: 'scanllm policy init', desc: 'Create default security policies' },
                { cmd: 'scanllm policy check', desc: 'Enforce policies (exit 1 on failure)' },
                { cmd: 'scanllm diff', desc: 'Compare scans for AI dependency drift' },
                { cmd: 'scanllm fix', desc: 'Show remediation suggestions' },
                { cmd: 'scanllm report aibom', desc: 'Generate CycloneDX AI-BOM' },
                { cmd: 'scanllm report pdf', desc: 'Generate PDF report' },
                { cmd: 'scanllm ui', desc: 'Launch local dashboard at localhost:5787' },
                { cmd: 'scanllm watch', desc: 'Auto-rescan on file changes' },
              ].map(({ cmd, desc }) => (
                <div key={cmd} className="flex items-start gap-4">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-green-400">$</span>
                    <span className="text-zinc-200 whitespace-nowrap">{cmd}</span>
                  </div>
                  <span className="text-zinc-600 hidden sm:block">— {desc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-zinc-800/50">
        <div className="max-w-3xl mx-auto px-6 py-20 text-center">
          <h2 className="text-3xl font-bold text-zinc-100 mb-4">
            Ready to see what AI is in your code?
          </h2>
          <p className="text-zinc-400 text-lg mb-8">
            Install the CLI and scan your first repo in 30 seconds. No signup required.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              onClick={() => navigate('/demo')}
              size="lg"
              className="bg-cyan-600 hover:bg-cyan-500 text-white px-8 py-6 text-lg font-semibold shadow-lg shadow-cyan-600/20"
            >
              Try the demo
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <div className="inline-flex items-center gap-3 px-5 py-3 rounded-lg bg-zinc-900 border border-zinc-800 font-mono text-sm">
              <span className="text-green-400">$</span>
              <span className="text-zinc-300">pip install scanllm</span>
              <button
                onClick={() => navigator.clipboard.writeText('pip install scanllm')}
                className="text-xs text-zinc-600 hover:text-zinc-300 transition-colors"
              >
                Copy
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HowItWorks;
