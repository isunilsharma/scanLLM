import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import {
  ArrowRight, ArrowDown, Terminal, GitBranch, Search, Shield,
  FileText, Eye, BarChart3, AlertTriangle, CheckCircle2, XCircle,
  Workflow, RefreshCw, Download, Bug, Wrench, Clock, Users
} from 'lucide-react';

const UserWorkflow = () => {
  const navigate = useNavigate();
  const [activePersona, setActivePersona] = useState('developer');

  const personas = {
    developer: {
      title: 'Individual Developer',
      subtitle: 'CLI-first, fast feedback loop',
      icon: Terminal,
      color: 'cyan',
      steps: [
        {
          title: 'Install & First Scan',
          commands: ['pip install scanllm', 'cd my-project', 'scanllm scan .'],
          output: 'Rich table with all AI findings, risk score (A-F), OWASP mapping',
          time: '< 60 seconds',
          icon: Terminal,
        },
        {
          title: 'Review Risk Score',
          commands: ['scanllm score'],
          output: 'Detailed score breakdown: secrets (+25), OWASP critical (+20), provider concentration (+10)',
          time: 'Instant',
          icon: BarChart3,
        },
        {
          title: 'Get Actionable Fix Suggestions',
          commands: ['scanllm fix'],
          output: 'Prioritized list: "Replace deprecated gpt-3.5-turbo with gpt-4o-mini", "Add max_tokens to OpenAI call on line 42"',
          time: 'Instant',
          icon: Wrench,
        },
        {
          title: 'Auto-Fix Issues',
          commands: ['scanllm fix --apply'],
          output: 'Automatically replaces deprecated models, adds missing max_tokens. Shows diff before applying.',
          time: '< 5 seconds',
          icon: CheckCircle2,
        },
        {
          title: 'Check Environment Health',
          commands: ['scanllm doctor'],
          output: 'Python version, dependencies, optional packages, .scanllm/ directory status',
          time: 'Instant',
          icon: Bug,
        },
        {
          title: 'Export for Documentation',
          commands: ['scanllm export --formats json,aibom,summary'],
          output: 'JSON scan data + CycloneDX AI-BOM + Markdown summary in ./scanllm-reports/',
          time: '< 2 seconds',
          icon: Download,
        },
      ]
    },
    team: {
      title: 'Team / DevSecOps Lead',
      subtitle: 'CI/CD integration, policy enforcement',
      icon: Users,
      color: 'purple',
      steps: [
        {
          title: 'Initialize Project Config',
          commands: ['scanllm init'],
          output: 'Creates .scanllm/ directory with default config, policies.yaml, and .scanllmignore',
          time: '< 1 second',
          icon: Terminal,
        },
        {
          title: 'Define Custom Policies',
          commands: ['# .scanllm/policies.yaml', 'rules:', '  - name: no-hardcoded-secrets', '    severity: critical', '    action: block', '  - name: approved-providers-only', '    providers: [openai, anthropic]', '    action: warn'],
          output: 'YAML-based policy rules that control what passes CI/CD',
          time: 'One-time setup',
          icon: Shield,
        },
        {
          title: 'Add to CI/CD Pipeline',
          commands: ['# .github/workflows/scanllm.yml', 'steps:', '  - uses: isunilsharma/scanllm-action@v1', '    with:', '      policy: .scanllm/policies.yaml', '      fail-on: critical'],
          output: 'Runs on every PR. Exit code 1 blocks merge if critical findings exist.',
          time: 'Every PR',
          icon: GitBranch,
        },
        {
          title: 'Check Policy Compliance',
          commands: ['scanllm policy check'],
          output: '12 built-in rules + custom rules evaluated. Pass/fail per rule with details.',
          time: '< 5 seconds',
          icon: CheckCircle2,
        },
        {
          title: 'Monitor Drift Over Time',
          commands: ['scanllm diff'],
          output: 'Shows new findings since last scan, removed findings, and risk score trend',
          time: '< 10 seconds',
          icon: RefreshCw,
        },
        {
          title: 'Generate Compliance Reports',
          commands: ['scanllm report pdf', 'scanllm report aibom', 'scanllm report model-card'],
          output: 'PDF executive summary, CycloneDX AI-BOM, Model Card — audit-ready artifacts',
          time: '< 10 seconds',
          icon: FileText,
        },
      ]
    },
    enterprise: {
      title: 'Enterprise / CISO',
      subtitle: 'Web dashboard, org-wide visibility',
      icon: Eye,
      color: 'emerald',
      steps: [
        {
          title: 'Connect GitHub Organization',
          commands: ['Sign in with GitHub OAuth', 'Select repositories to scan'],
          output: 'All org repos visible in dashboard. Private repos supported via OAuth token.',
          time: '< 1 minute',
          icon: GitBranch,
        },
        {
          title: 'Scan Across All Repos',
          commands: ['Trigger scans from web dashboard', 'or schedule via CI/CD'],
          output: 'Centralized findings across all repositories with org-level risk score',
          time: 'Minutes',
          icon: Search,
        },
        {
          title: 'Interactive Dependency Graph',
          commands: ['Navigate to any repo dashboard', 'Click "Dependency Graph" tab'],
          output: 'React Flow interactive visualization — zoom, pan, click nodes for details. See all AI components and their relationships.',
          time: 'Real-time',
          icon: Workflow,
        },
        {
          title: 'OWASP LLM Top 10 Coverage',
          commands: ['Dashboard > OWASP tab'],
          output: '8/10 OWASP categories covered with finding counts per category. Export for auditors.',
          time: 'Real-time',
          icon: Shield,
        },
        {
          title: 'Track Risk Over Time',
          commands: ['Dashboard > Scan History', 'Dashboard > Drift View'],
          output: 'Historical scan results, risk score trends, new vs resolved findings',
          time: 'Ongoing',
          icon: Clock,
        },
        {
          title: 'Export AI-BOM for Compliance',
          commands: ['Dashboard > Reports', 'or: scanllm export --formats all'],
          output: 'CycloneDX AI-BOM for EU AI Act / SOC 2 / NIST RMF compliance evidence',
          time: '< 10 seconds',
          icon: Download,
        },
      ]
    }
  };

  const active = personas[activePersona];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">

      {/* Hero */}
      <section className="relative overflow-hidden py-20 px-6">
        <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 via-transparent to-transparent" />
        <div className="relative max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm mb-6">
            <Workflow className="w-4 h-4" />
            User Workflow
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            From Install to <span className="text-cyan-400">Insight</span>
          </h1>
          <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
            Three workflows for three personas. Pick your path.
          </p>
        </div>
      </section>

      {/* Persona Selector */}
      <section className="px-6 pb-6">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-3 gap-3">
            {Object.entries(personas).map(([key, persona]) => (
              <button
                key={key}
                onClick={() => setActivePersona(key)}
                className={`p-4 rounded-xl border transition-all text-left ${
                  activePersona === key
                    ? `border-${persona.color}-500/50 bg-${persona.color}-500/10`
                    : 'border-zinc-800/50 bg-zinc-900/30 hover:bg-zinc-900/60'
                }`}
              >
                <persona.icon className={`w-6 h-6 mb-2 ${activePersona === key ? `text-${persona.color}-400` : 'text-zinc-500'}`} />
                <div className={`font-semibold text-sm ${activePersona === key ? 'text-white' : 'text-zinc-400'}`}>
                  {persona.title}
                </div>
                <div className="text-xs text-zinc-500 mt-0.5">{persona.subtitle}</div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow Steps */}
      <section className="px-6 pb-16">
        <div className="max-w-4xl mx-auto">
          <div className="space-y-0">
            {active.steps.map((step, idx) => (
              <div key={idx}>
                {/* Step Card */}
                <div className="flex gap-4">
                  {/* Timeline */}
                  <div className="flex flex-col items-center flex-shrink-0">
                    <div className={`w-10 h-10 rounded-full bg-${active.color}-500/20 border border-${active.color}-500/30 flex items-center justify-center`}>
                      <step.icon className={`w-5 h-5 text-${active.color}-400`} />
                    </div>
                    {idx < active.steps.length - 1 && (
                      <div className="w-px flex-1 bg-zinc-800 my-2" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="pb-8 flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-bold">
                        <span className="text-zinc-500 mr-2">Step {idx + 1}.</span>
                        {step.title}
                      </h3>
                      <span className="text-xs bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded text-zinc-500">
                        {step.time}
                      </span>
                    </div>

                    {/* Command Block */}
                    <div className="bg-zinc-900 border border-zinc-800/50 rounded-lg p-3 mb-3 font-mono text-sm">
                      {step.commands.map((cmd, i) => (
                        <div key={i} className={cmd.startsWith('#') || cmd.startsWith('  ') || cmd.startsWith('or') || cmd.startsWith('Sign') || cmd.startsWith('Select') || cmd.startsWith('Navigate') || cmd.startsWith('Click') || cmd.startsWith('Trigger') || cmd.startsWith('Dashboard')
                          ? 'text-zinc-500'
                          : 'text-cyan-400'
                        }>
                          {!cmd.startsWith('#') && !cmd.startsWith('  ') && !cmd.startsWith('or') && !cmd.startsWith('Sign') && !cmd.startsWith('Select') && !cmd.startsWith('Navigate') && !cmd.startsWith('Click') && !cmd.startsWith('Trigger') && !cmd.startsWith('Dashboard')
                            ? <span className="text-zinc-600 mr-2">$</span>
                            : null
                          }
                          {cmd}
                        </div>
                      ))}
                    </div>

                    {/* Output */}
                    <div className="flex items-start gap-2">
                      <ArrowRight className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-zinc-400">{step.output}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Decision Flowchart */}
      <section className="px-6 pb-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-8 text-center">Decision Guide: What to Run When</h2>

          <div className="space-y-4">
            {[
              {
                question: 'First time using ScanLLM?',
                yes: { cmd: 'pip install scanllm && scanllm scan .', desc: 'Install and run your first scan' },
                no: null,
              },
              {
                question: 'Want to understand your risk score?',
                yes: { cmd: 'scanllm score', desc: 'See detailed breakdown of each risk factor' },
                no: null,
              },
              {
                question: 'Found issues and want to fix them?',
                yes: { cmd: 'scanllm fix --apply', desc: 'Auto-fix deprecated models, add missing configs' },
                no: { cmd: 'scanllm fix', desc: 'Just show suggestions without changing files' },
              },
              {
                question: 'Need compliance artifacts?',
                yes: { cmd: 'scanllm export --formats all', desc: 'JSON + SARIF + AI-BOM + summary in one command' },
                no: null,
              },
              {
                question: 'Setting up CI/CD?',
                yes: { cmd: 'scanllm init && scanllm policy check', desc: 'Create config, then validate policies' },
                no: null,
              },
              {
                question: 'Something not working?',
                yes: { cmd: 'scanllm doctor', desc: 'Check Python version, dependencies, environment' },
                no: null,
              },
            ].map((item, i) => (
              <div key={i} className="border border-zinc-800/50 rounded-lg p-4">
                <div className="font-medium text-zinc-300 mb-3">{item.question}</div>
                <div className="flex flex-col sm:flex-row gap-3">
                  <div className="flex-1 flex items-start gap-2 bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-3">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <code className="text-sm text-cyan-400">{item.yes.cmd}</code>
                      <div className="text-xs text-zinc-500 mt-1">{item.yes.desc}</div>
                    </div>
                  </div>
                  {item.no && (
                    <div className="flex-1 flex items-start gap-2 bg-zinc-900/50 border border-zinc-800/50 rounded-lg p-3">
                      <XCircle className="w-4 h-4 text-zinc-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <code className="text-sm text-zinc-400">{item.no.cmd}</code>
                        <div className="text-xs text-zinc-500 mt-1">{item.no.desc}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CLI Quick Reference */}
      <section className="px-6 pb-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-8 text-center">Complete CLI Reference</h2>
          <div className="bg-zinc-900 border border-zinc-800/50 rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-zinc-800/50">
              <div className="w-3 h-3 rounded-full bg-red-500/60" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
              <div className="w-3 h-3 rounded-full bg-green-500/60" />
              <span className="text-sm text-zinc-500 ml-2 font-mono">scanllm --help</span>
            </div>
            <div className="p-4 font-mono text-sm space-y-3">
              {[
                { cmd: 'scanllm scan .', desc: 'Scan current directory for AI dependencies' },
                { cmd: 'scanllm scan . --format json', desc: 'Output as JSON' },
                { cmd: 'scanllm scan . --save', desc: 'Save results for later comparison' },
                { cmd: 'scanllm score', desc: 'Risk score breakdown' },
                { cmd: 'scanllm fix', desc: 'Show fix suggestions' },
                { cmd: 'scanllm fix --apply', desc: 'Auto-fix issues' },
                { cmd: 'scanllm doctor', desc: 'Environment health check' },
                { cmd: 'scanllm export', desc: 'Export all formats' },
                { cmd: 'scanllm diff', desc: 'Compare with previous scan' },
                { cmd: 'scanllm init', desc: 'Initialize project config' },
                { cmd: 'scanllm policy check', desc: 'Evaluate policy rules' },
                { cmd: 'scanllm report pdf', desc: 'Generate PDF report' },
                { cmd: 'scanllm report aibom', desc: 'Generate CycloneDX AI-BOM' },
                { cmd: 'scanllm report model-card', desc: 'Generate model card' },
                { cmd: 'scanllm watch', desc: 'Watch for changes and re-scan' },
                { cmd: 'scanllm ui', desc: 'Launch local web dashboard' },
              ].map((item, i) => (
                <div key={i} className="flex items-baseline gap-4">
                  <span className="text-cyan-400 whitespace-nowrap">{item.cmd}</span>
                  <span className="text-zinc-600 text-xs">{item.desc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 pb-20">
        <div className="max-w-3xl mx-auto text-center">
          <div className="border border-zinc-800/50 rounded-xl p-8 bg-gradient-to-b from-zinc-900/50 to-transparent">
            <h2 className="text-2xl font-bold mb-3">Start Scanning Now</h2>
            <p className="text-zinc-400 mb-6">No signup. No config. Just install and scan.</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <div className="bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 font-mono text-sm text-cyan-400">
                pip install scanllm && scanllm scan .
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

export default UserWorkflow;
