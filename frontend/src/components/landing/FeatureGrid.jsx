import React, { useState, useEffect, useRef } from 'react';
import { Shield, GitBranch, AlertTriangle, FileCode, BarChart3, Diff } from 'lucide-react';

const features = [
  {
    icon: GitBranch,
    title: 'AI Dependency Graph',
    description: 'Interactive visualization of every AI component and how they connect. See the blast radius of a single provider failure.',
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-400/10',
    borderColor: 'border-cyan-400/20',
    preview: (
      <div className="mt-4 p-3 bg-zinc-900/50 rounded-lg font-mono text-xs text-zinc-400">
        <div className="flex items-center gap-2 mb-2">
          <span className="inline-block w-2 h-2 rounded-full bg-cyan-400" />
          <span className="text-cyan-400">OpenAI GPT-4o</span>
          <span className="text-zinc-600">\u2192</span>
          <span className="inline-block w-2 h-2 rounded-full bg-purple-400" />
          <span className="text-purple-400">LangChain</span>
        </div>
        <div className="flex items-center gap-2 mb-2">
          <span className="inline-block w-2 h-2 rounded-full bg-purple-400" />
          <span className="text-purple-400">LangChain</span>
          <span className="text-zinc-600">\u2192</span>
          <span className="inline-block w-2 h-2 rounded-full bg-green-400" />
          <span className="text-green-400">Pinecone</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-orange-400" />
          <span className="text-orange-400">CrewAI Agent</span>
          <span className="text-zinc-600">\u2192</span>
          <span className="inline-block w-2 h-2 rounded-full bg-cyan-400" />
          <span className="text-cyan-400">OpenAI GPT-4o</span>
        </div>
      </div>
    ),
  },
  {
    icon: Shield,
    title: 'OWASP LLM Top 10',
    description: 'Automatically map findings to OWASP LLM Top 10 (2025). Prompt injection, excessive agency, supply chain risks.',
    color: 'text-amber-400',
    bgColor: 'bg-amber-400/10',
    borderColor: 'border-amber-400/20',
    preview: (
      <div className="mt-4 space-y-1.5 font-mono text-xs">
        <div className="flex justify-between items-center">
          <span className="text-red-400">LLM01 Prompt Injection</span>
          <span className="px-1.5 py-0.5 rounded bg-red-500/20 text-red-400">HIGH</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-amber-400">LLM06 Excessive Agency</span>
          <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">MED</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-green-400">LLM03 Supply Chain</span>
          <span className="px-1.5 py-0.5 rounded bg-green-500/20 text-green-400">PASS</span>
        </div>
      </div>
    ),
  },
  {
    icon: AlertTriangle,
    title: 'Risk Scoring (0\u2013100)',
    description: 'Weighted risk score based on secrets, OWASP findings, provider concentration, and missing safety configs.',
    color: 'text-red-400',
    bgColor: 'bg-red-400/10',
    borderColor: 'border-red-400/20',
    preview: (
      <div className="mt-4 flex items-center gap-4">
        <div className="relative w-16 h-16">
          <svg viewBox="0 0 36 36" className="w-16 h-16 -rotate-90">
            <circle cx="18" cy="18" r="15.5" fill="none" stroke="currentColor" strokeWidth="3" className="text-zinc-800" />
            <circle cx="18" cy="18" r="15.5" fill="none" stroke="currentColor" strokeWidth="3" strokeDasharray="62 100" className="text-amber-400" strokeLinecap="round" />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-amber-400">62</span>
        </div>
        <div className="text-left">
          <div className="text-2xl font-bold text-amber-400">Grade D</div>
          <div className="text-xs text-zinc-500">3 critical, 5 high</div>
        </div>
      </div>
    ),
  },
  {
    icon: FileCode,
    title: 'Policy as Code',
    description: 'Define rules in YAML. Enforce in CI/CD. Block deprecated models, require max_tokens, approve providers.',
    color: 'text-green-400',
    bgColor: 'bg-green-400/10',
    borderColor: 'border-green-400/20',
    preview: (
      <div className="mt-4 p-3 bg-zinc-900/50 rounded-lg font-mono text-xs">
        <div className="text-zinc-500"># .scanllm/policies.yaml</div>
        <div><span className="text-purple-400">policies</span><span className="text-zinc-500">:</span></div>
        <div className="pl-2"><span className="text-zinc-500">-</span> <span className="text-cyan-400">name</span><span className="text-zinc-500">:</span> <span className="text-green-400">no-deprecated-models</span></div>
        <div className="pl-4"><span className="text-cyan-400">severity</span><span className="text-zinc-500">:</span> <span className="text-red-400">error</span></div>
        <div className="pl-4"><span className="text-cyan-400">block_ci</span><span className="text-zinc-500">:</span> <span className="text-amber-400">true</span></div>
      </div>
    ),
  },
  {
    icon: BarChart3,
    title: 'AI-BOM Export',
    description: 'Generate CycloneDX 1.6 ML-BOM for compliance. SOC 2, EU AI Act, customer security questionnaires.',
    color: 'text-purple-400',
    bgColor: 'bg-purple-400/10',
    borderColor: 'border-purple-400/20',
    preview: (
      <div className="mt-4 flex flex-wrap gap-2">
        <span className="px-2 py-1 rounded-full bg-purple-500/20 text-purple-400 text-xs font-mono">CycloneDX 1.6</span>
        <span className="px-2 py-1 rounded-full bg-blue-500/20 text-blue-400 text-xs font-mono">JSON</span>
        <span className="px-2 py-1 rounded-full bg-green-500/20 text-green-400 text-xs font-mono">XML</span>
        <span className="px-2 py-1 rounded-full bg-zinc-500/20 text-zinc-400 text-xs font-mono">SARIF</span>
        <span className="px-2 py-1 rounded-full bg-amber-500/20 text-amber-400 text-xs font-mono">PDF Report</span>
      </div>
    ),
  },
  {
    icon: Diff,
    title: 'Drift Detection',
    description: 'Compare scans over time. See what AI dependencies changed, new risks introduced, policies violated.',
    color: 'text-blue-400',
    bgColor: 'bg-blue-400/10',
    borderColor: 'border-blue-400/20',
    preview: (
      <div className="mt-4 space-y-1.5 font-mono text-xs">
        <div className="text-green-400">+ Added: anthropic (claude-sonnet-4) in src/agent.py</div>
        <div className="text-red-400">- Removed: openai (gpt-3.5-turbo) from src/chat.py</div>
        <div className="text-cyan-400">~ Risk: 45 \u2192 38 (improved)</div>
      </div>
    ),
  },
];

const FeatureCard = ({ feature, index }) => {
  const [isVisible, setIsVisible] = useState(false);
  const cardRef = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTimeout(() => setIsVisible(true), index * 100);
        }
      },
      { threshold: 0.1 }
    );

    if (cardRef.current) observer.observe(cardRef.current);
    return () => observer.disconnect();
  }, [index]);

  const Icon = feature.icon;

  return (
    <div
      ref={cardRef}
      className={`p-6 rounded-xl border ${feature.borderColor} bg-zinc-900/50 backdrop-blur-sm
                  transition-all duration-700 hover:border-opacity-60 hover:shadow-lg hover:shadow-black/20
                  ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
    >
      <div className={`inline-flex p-2 rounded-lg ${feature.bgColor} mb-3`}>
        <Icon className={`w-5 h-5 ${feature.color}`} />
      </div>
      <h3 className="text-lg font-semibold text-zinc-100 mb-2">{feature.title}</h3>
      <p className="text-sm text-zinc-400 leading-relaxed">{feature.description}</p>
      {feature.preview}
    </div>
  );
};

const FeatureGrid = () => {
  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      {features.map((feature, i) => (
        <FeatureCard key={feature.title} feature={feature} index={i} />
      ))}
    </div>
  );
};

export default FeatureGrid;
