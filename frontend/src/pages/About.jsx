import React from 'react';
import { ArrowRight, Shield, Eye, Zap, Users, Globe, BookOpen, Github, Linkedin, Calendar } from 'lucide-react';
import { Button } from '../components/ui/button';

const About = () => {
  const principles = [
    {
      icon: Eye,
      title: 'Visibility first',
      description: 'You can\'t govern what you can\'t see. Every engineering team deserves a clear, real-time inventory of the AI running in their systems.',
    },
    {
      icon: Shield,
      title: 'Security by default',
      description: 'AI adoption should not mean AI chaos. Hardcoded keys, prompt injection risks, and overprivileged agents should be caught before they ship.',
    },
    {
      icon: Zap,
      title: 'Developer-first tooling',
      description: 'If it requires a sales call to try, developers won\'t adopt it. ScanLLM is pip install, zero config, instant results. Always.',
    },
    {
      icon: Globe,
      title: 'Open source core',
      description: 'The scanning engine, CLI, and signature database are open source. Community contributions make detection better for everyone.',
    },
  ];

  const stats = [
    { value: '200+', label: 'AI detection patterns' },
    { value: '30+', label: 'Providers covered' },
    { value: '7', label: 'Specialized scanners' },
    { value: '8/10', label: 'OWASP LLM categories' },
  ];

  const timeline = [
    {
      phase: 'Today',
      title: 'CLI + Cloud Scanner',
      items: ['7 scanners (Python AST, JS/TS, configs, deps, notebooks, secrets)', 'Interactive dependency graph', 'OWASP LLM Top 10 mapping', 'Policy-as-code with CI/CD gates', 'AI-BOM (CycloneDX 1.6) export', 'Cost insights and drift detection'],
    },
    {
      phase: 'Next',
      title: 'Ecosystem integrations',
      items: ['VS Code extension with inline warnings', 'Pre-commit hooks (built)', 'GitHub Action with SARIF upload (built)', 'Community signature contributions', 'IDE-native policy violations'],
    },
    {
      phase: 'Future',
      title: 'Enterprise platform',
      items: ['Multi-repo org-wide AI inventory', 'Scheduled scanning for continuous monitoring', 'API-first export (ServiceNow, Archer, OneTrust)', 'SSO/SAML, audit logs, RBAC', 'Cost optimization recommendations'],
    },
  ];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-900/15 via-transparent to-transparent" />
        <div className="relative max-w-5xl mx-auto px-6 pt-20 pb-16">
          <div className="text-center">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6 leading-[1.1]">
              The AI visibility layer{' '}
              <span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                your stack is missing
              </span>
            </h1>
            <p className="text-lg md:text-xl text-zinc-400 max-w-3xl mx-auto leading-relaxed">
              ScanLLM answers the question no tool answers today:
              <span className="text-zinc-200 italic"> "What AI is in our code, where, and what depends on what?"</span>
            </p>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="max-w-4xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl">
              <div className="text-3xl font-bold text-cyan-400 mb-1">{stat.value}</div>
              <div className="text-sm text-zinc-500">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Why we built this */}
      <section className="border-t border-zinc-800/50">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-zinc-100 mb-6">Why we built ScanLLM</h2>
              <div className="space-y-4 text-zinc-400 leading-relaxed">
                <p>
                  As companies race to adopt LLMs across dozens of services, it has become nearly impossible
                  to answer basic questions: <span className="text-zinc-200">Where are we calling OpenAI? What breaks if we
                  change this model? Are we leaking API keys?</span>
                </p>
                <p>
                  Existing tools don't solve this. Snyk found only 10/26 LLM-specific vulnerabilities in
                  independent testing. Cycode and Noma cost six figures. Promptfoo does red teaming, not
                  code scanning.
                </p>
                <p>
                  ScanLLM is the scanning engine layer that produces the AI inventory your SAST tool,
                  your GRC platform, and your compliance team all need but cannot generate themselves.
                </p>
              </div>
            </div>
            <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6">
              <div className="text-sm text-zinc-500 mb-4 font-medium">THE PROBLEM</div>
              <div className="space-y-3">
                {[
                  '"We have no AI inventory for our SOC 2 audit"',
                  '"Developers are using 5 different LLM providers"',
                  '"We found API keys in 3 prompt templates"',
                  '"We can\'t answer EU AI Act Article 9"',
                  '"What happens if OpenAI goes down?"',
                ].map((problem, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-red-500/5 border border-red-500/10">
                    <span className="text-red-400 text-lg leading-none mt-0.5">!</span>
                    <span className="text-zinc-400 text-sm italic">{problem}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Principles */}
      <section className="border-t border-zinc-800/50">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-zinc-100 mb-4">What we believe</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {principles.map((principle) => {
              const Icon = principle.icon;
              return (
                <div key={principle.title} className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-all">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center">
                      <Icon className="w-5 h-5 text-cyan-400" />
                    </div>
                    <h3 className="font-semibold text-zinc-100">{principle.title}</h3>
                  </div>
                  <p className="text-zinc-400 text-sm leading-relaxed">{principle.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Roadmap */}
      <section className="border-t border-zinc-800/50">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-zinc-100 mb-4">Where we're going</h2>
            <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
              From CLI scanner to the enterprise AI governance platform.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {timeline.map((phase, idx) => (
              <div key={phase.phase} className="relative">
                <div className={`bg-zinc-900/80 border rounded-xl p-6 h-full ${
                  idx === 0 ? 'border-cyan-500/30' : 'border-zinc-800'
                }`}>
                  <div className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium mb-3 ${
                    idx === 0 ? 'bg-cyan-500/10 text-cyan-400' :
                    idx === 1 ? 'bg-blue-500/10 text-blue-400' :
                    'bg-purple-500/10 text-purple-400'
                  }`}>
                    {phase.phase}
                  </div>
                  <h3 className="font-semibold text-zinc-100 mb-4">{phase.title}</h3>
                  <ul className="space-y-2">
                    {phase.items.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-zinc-400">
                        <span className="w-1 h-1 rounded-full bg-zinc-600 flex-shrink-0 mt-2" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Open Source */}
      <section className="border-t border-zinc-800/50">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-8 md:p-12">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <BookOpen className="w-5 h-5 text-cyan-400" />
                  <span className="text-sm text-cyan-400 font-medium">Open Source</span>
                </div>
                <h2 className="text-2xl font-bold text-zinc-100 mb-4">
                  Built in the open. Maintained by the community.
                </h2>
                <p className="text-zinc-400 leading-relaxed mb-6">
                  The CLI, scanning engine, and AI signatures database are MIT licensed.
                  Community contributions to detection patterns make ScanLLM better for everyone.
                </p>
                <div className="flex flex-wrap gap-3">
                  <a
                    href="https://github.com/isunilsharma/scanllm"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-zinc-800 text-zinc-200 rounded-lg hover:bg-zinc-700 transition-colors text-sm font-medium"
                  >
                    <Github className="w-4 h-4" />
                    View on GitHub
                  </a>
                  <a
                    href="https://github.com/isunilsharma/scanllm/blob/main/CONTRIBUTING.md"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-transparent border border-zinc-700 text-zinc-300 rounded-lg hover:bg-zinc-800 transition-colors text-sm font-medium"
                  >
                    Contribute
                  </a>
                </div>
              </div>
              <div className="space-y-3">
                {[
                  { label: 'License', value: 'MIT' },
                  { label: 'Language', value: 'Python + React' },
                  { label: 'Install', value: 'pip install scanllm' },
                  { label: 'Signatures', value: '200+ patterns, community-maintained' },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between p-3 bg-zinc-950 rounded-lg border border-zinc-800/50">
                    <span className="text-sm text-zinc-500">{item.label}</span>
                    <span className="text-sm text-zinc-300 font-medium">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-zinc-800/50">
        <div className="max-w-3xl mx-auto px-6 py-20 text-center">
          <h2 className="text-3xl font-bold text-zinc-100 mb-4">
            Get in touch
          </h2>
          <p className="text-zinc-400 text-lg mb-8">
            Interested in ScanLLM for your team? Book a live demo and tell us about your AI stack.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="https://calendly.com/sunildec1991/30min"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button
                size="lg"
                className="bg-cyan-600 hover:bg-cyan-500 text-white px-8 py-6 text-lg font-semibold shadow-lg shadow-cyan-600/20"
              >
                <Calendar className="w-5 h-5 mr-2" />
                Book a Demo
              </Button>
            </a>
            <div className="flex items-center gap-4">
              <a
                href="https://github.com/isunilsharma/scanllm"
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-500 hover:text-zinc-300 transition-colors"
              >
                <Github className="w-6 h-6" />
              </a>
              <a
                href="https://www.linkedin.com/company/scanllm-ai/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-500 hover:text-zinc-300 transition-colors"
              >
                <Linkedin className="w-6 h-6" />
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default About;
