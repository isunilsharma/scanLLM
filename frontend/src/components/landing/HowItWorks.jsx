import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Search, ShieldCheck } from 'lucide-react';

const steps = [
  {
    number: '01',
    icon: Terminal,
    title: 'Install',
    command: 'pip install scanllm',
    description: 'One command. No config. Works on any repo with Python, JavaScript, TypeScript, or Jupyter notebooks.',
    color: 'text-green-400',
    borderColor: 'border-green-400/30',
  },
  {
    number: '02',
    icon: Search,
    title: 'Scan',
    command: 'scanllm scan .',
    description: 'AST-level Python analysis, regex-based JS/TS scanning, config/dependency/secret detection. Takes ~30 seconds.',
    color: 'text-cyan-400',
    borderColor: 'border-cyan-400/30',
  },
  {
    number: '03',
    icon: ShieldCheck,
    title: 'Govern',
    command: 'scanllm policy check',
    description: 'Enforce policies in CI/CD. Block deprecated models, require safety configs, approve providers. Exit code 1 = build fails.',
    color: 'text-amber-400',
    borderColor: 'border-amber-400/30',
  },
];

const CopyButton = ({ text }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="ml-2 px-2 py-0.5 text-xs rounded bg-zinc-700 hover:bg-zinc-600 text-zinc-400 transition-colors"
    >
      {copied ? 'Copied!' : 'Copy'}
    </button>
  );
};

const StepCard = ({ step, index }) => {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTimeout(() => setIsVisible(true), index * 200);
        }
      },
      { threshold: 0.2 }
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [index]);

  const Icon = step.icon;

  return (
    <div
      ref={ref}
      className={`relative p-6 rounded-xl border ${step.borderColor} bg-zinc-900/30
                  transition-all duration-700
                  ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
    >
      <div className="flex items-center gap-3 mb-4">
        <span className={`text-3xl font-bold ${step.color} opacity-30`}>{step.number}</span>
        <Icon className={`w-5 h-5 ${step.color}`} />
        <h3 className="text-xl font-semibold text-zinc-100">{step.title}</h3>
      </div>

      <div className="flex items-center gap-2 mb-4 p-3 rounded-lg bg-zinc-950 border border-zinc-800">
        <span className="text-green-400 font-mono text-sm">$</span>
        <code className="font-mono text-sm text-zinc-300 flex-1">{step.command}</code>
        <CopyButton text={step.command} />
      </div>

      <p className="text-sm text-zinc-400 leading-relaxed">{step.description}</p>
    </div>
  );
};

const HowItWorksSection = () => {
  return (
    <div className="grid md:grid-cols-3 gap-6">
      {steps.map((step, i) => (
        <StepCard key={step.number} step={step} index={i} />
      ))}
    </div>
  );
};

export default HowItWorksSection;
