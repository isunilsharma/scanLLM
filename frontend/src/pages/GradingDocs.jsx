import React from 'react';
import { Shield, AlertTriangle, CheckCircle, XCircle, Info } from 'lucide-react';

const GRADES = [
  {
    grade: 'A',
    range: '0 - 20',
    label: 'Low Risk',
    color: '#22c55e',
    bgClass: 'bg-green-500/10 border-green-500/30',
    textClass: 'text-green-400',
    description: 'Minimal AI risk exposure. Dependencies are well-configured, no hardcoded secrets detected, proper safety measures (max_tokens, rate limiting) are in place, and no critical OWASP LLM violations found.',
    guidance: 'Maintain current practices. Set up CI/CD policy enforcement to prevent regressions. Consider running periodic scans to catch new dependencies as your codebase evolves.',
  },
  {
    grade: 'B',
    range: '21 - 40',
    label: 'Moderate',
    color: '#84cc16',
    bgClass: 'bg-lime-500/10 border-lime-500/30',
    textClass: 'text-lime-400',
    description: 'Generally safe AI posture with some areas for improvement. Typically indicates minor configuration gaps such as missing max_tokens limits, a few medium-severity OWASP findings, or slight provider concentration risk.',
    guidance: 'Review medium-severity findings and address missing safety configurations. Add max_tokens and timeout parameters to LLM calls. Diversify provider usage if concentration risk is flagged.',
  },
  {
    grade: 'C',
    range: '41 - 60',
    label: 'Medium',
    color: '#eab308',
    bgClass: 'bg-yellow-500/10 border-yellow-500/30',
    textClass: 'text-yellow-400',
    description: 'Notable risks present that warrant active remediation. May include a combination of high-severity OWASP findings, outdated AI packages with known CVEs, or agents with overly broad tool access.',
    guidance: 'Prioritize high-severity OWASP findings. Update outdated AI packages. Review agent configurations and apply least-privilege tool access. Consider rotating any exposed credentials.',
  },
  {
    grade: 'D',
    range: '61 - 80',
    label: 'High Risk',
    color: '#f97316',
    bgClass: 'bg-orange-500/10 border-orange-500/30',
    textClass: 'text-orange-400',
    description: 'Significant security concerns requiring immediate attention. Often indicates hardcoded secrets, critical OWASP violations (prompt injection vectors, unsafe output handling), or a combination of multiple high-severity issues.',
    guidance: 'Immediately rotate any hardcoded API keys and move them to a secrets manager. Fix critical OWASP violations (eval of LLM output, unsanitized prompt injection vectors). Restrict agent permissions. Run a full scan after fixes to verify improvement.',
  },
  {
    grade: 'F',
    range: '81 - 100',
    label: 'Critical',
    color: '#ef4444',
    bgClass: 'bg-red-500/10 border-red-500/30',
    textClass: 'text-red-400',
    description: 'Critical risk level. Multiple hardcoded secrets, critical OWASP LLM violations, overprivileged agents, severe provider concentration, and major misconfigurations. This score indicates the codebase has fundamental AI security gaps.',
    guidance: 'Treat as a security incident. Rotate all exposed credentials immediately. Audit every LLM call for prompt injection and unsafe output handling. Lock down agent tool access. Establish a baseline scan and track remediation progress over time.',
  },
];

const SCORE_FACTORS = [
  { factor: 'Hardcoded Secrets', weight: 25, unit: 'per occurrence', icon: XCircle, color: 'text-red-400', description: 'API keys, tokens, or credentials found in source code (e.g. OPENAI_API_KEY, ANTHROPIC_API_KEY)' },
  { factor: 'Critical OWASP Findings', weight: 20, unit: 'per finding', icon: AlertTriangle, color: 'text-red-400', description: 'OWASP LLM Top 10 critical-severity violations such as eval(llm_response) or unsanitized output to shell/SQL' },
  { factor: 'Excessive Agent Permissions', weight: 15, unit: 'per instance', icon: Shield, color: 'text-orange-400', description: 'Agent/tool configurations with overly broad access or missing human-in-the-loop controls' },
  { factor: 'High OWASP Findings', weight: 10, unit: 'per finding', icon: AlertTriangle, color: 'text-orange-400', description: 'OWASP LLM Top 10 high-severity violations such as prompt injection vectors or system prompt leakage' },
  { factor: 'Provider Concentration', weight: 10, unit: 'per provider', icon: Info, color: 'text-yellow-400', description: 'Single-vendor dependency risk when all AI calls go through one provider' },
  { factor: 'Outdated AI Packages', weight: 5, unit: 'per package', icon: Info, color: 'text-yellow-400', description: 'AI packages with known CVEs or significantly outdated versions' },
  { factor: 'Missing Safety Configs', weight: 3, unit: 'per instance', icon: Info, color: 'text-zinc-400', description: 'Missing max_tokens, rate limiting, or timeout parameters on LLM calls' },
];

const GradingDocs = () => {
  return (
    <div className="bg-zinc-950 min-h-screen">
      <div className="max-w-5xl mx-auto px-6 py-16 md:py-24">
        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-zinc-100 mb-4">
            Risk Grading System
          </h1>
          <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
            ScanLLM assigns a risk score from 0 to 100 based on AI security findings in your codebase,
            then maps it to a letter grade from A (safest) to F (critical risk).
          </p>
        </div>

        {/* Grade Cards */}
        <section className="mb-20">
          <h2 className="text-2xl font-bold text-zinc-100 mb-8">Grade Definitions</h2>
          <div className="space-y-4">
            {GRADES.map(g => (
              <div
                key={g.grade}
                className={`rounded-lg border p-6 ${g.bgClass}`}
              >
                <div className="flex flex-col md:flex-row md:items-start gap-4 md:gap-8">
                  <div className="flex items-center gap-4 md:w-48 shrink-0">
                    <span className={`text-4xl font-bold ${g.textClass}`}>{g.grade}</span>
                    <div>
                      <p className={`text-sm font-semibold ${g.textClass}`}>{g.label}</p>
                      <p className="text-xs text-zinc-500">Score: {g.range}</p>
                    </div>
                  </div>
                  <div className="flex-1 space-y-3">
                    <p className="text-sm text-zinc-300">{g.description}</p>
                    <div className="bg-zinc-900/50 rounded-md p-3">
                      <p className="text-xs font-medium text-zinc-400 mb-1">Recommended Action</p>
                      <p className="text-sm text-zinc-300">{g.guidance}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Score Formula */}
        <section className="mb-20">
          <h2 className="text-2xl font-bold text-zinc-100 mb-4">How the Score is Calculated</h2>
          <p className="text-zinc-400 mb-8">
            The risk score is the sum of weighted factors found during a scan, normalized to a 0-100 scale.
            Each factor type has a fixed weight reflecting its security impact.
          </p>

          <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-zinc-800/50 border-b border-zinc-800">
                <tr>
                  <th className="text-left px-5 py-3 text-xs font-medium text-zinc-400">Factor</th>
                  <th className="text-center px-5 py-3 text-xs font-medium text-zinc-400">Weight</th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-zinc-400 hidden md:table-cell">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {SCORE_FACTORS.map(f => {
                  const Icon = f.icon;
                  return (
                    <tr key={f.factor}>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <Icon size={14} className={f.color} />
                          <span className="text-sm text-zinc-200">{f.factor}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span className="text-sm font-mono font-semibold text-zinc-100">{f.weight}</span>
                        <span className="text-xs text-zinc-500 ml-1">{f.unit}</span>
                      </td>
                      <td className="px-5 py-4 text-sm text-zinc-400 hidden md:table-cell">{f.description}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Formula */}
          <div className="mt-6 bg-zinc-900 border border-zinc-800 rounded-lg p-5">
            <p className="text-xs font-medium text-zinc-400 mb-3">Formula</p>
            <pre className="text-sm text-cyan-400 font-mono leading-relaxed overflow-x-auto">
{`score = (
  secrets * 25 +
  owasp_critical * 20 +
  excessive_agent_perms * 15 +
  owasp_high * 10 +
  provider_concentration * 10 +
  outdated_packages * 5 +
  missing_safety_configs * 3
)

risk_score = min(score, 100)  // capped at 100`}
            </pre>
          </div>
        </section>

        {/* OWASP Reference */}
        <section>
          <h2 className="text-2xl font-bold text-zinc-100 mb-4">OWASP LLM Top 10 Coverage</h2>
          <p className="text-zinc-400 mb-6">
            ScanLLM maps findings to the OWASP LLM Top 10 (2025). These are the most common AI/LLM security risks
            that static analysis can detect.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              { id: 'LLM01', name: 'Prompt Injection', severity: 'High', detects: 'User input concatenated into prompts without sanitization' },
              { id: 'LLM02', name: 'Sensitive Info Disclosure', severity: 'High', detects: 'Credentials or PII in system prompts, missing output filtering' },
              { id: 'LLM03', name: 'Supply Chain', severity: 'Critical', detects: 'Unverified model sources, outdated AI packages with CVEs' },
              { id: 'LLM05', name: 'Improper Output Handling', severity: 'Critical', detects: 'eval(llm_response), unsanitized LLM output to SQL/shell/HTML' },
              { id: 'LLM06', name: 'Excessive Agency', severity: 'High', detects: 'Agent configs with broad tool access, missing human-in-the-loop' },
              { id: 'LLM07', name: 'System Prompt Leakage', severity: 'Medium', detects: 'API keys or business logic in prompt templates' },
              { id: 'LLM08', name: 'Vector/Embedding Weaknesses', severity: 'Medium', detects: 'Unauthenticated vector DB connections, no access controls' },
              { id: 'LLM10', name: 'Unbounded Consumption', severity: 'Low', detects: 'Missing max_tokens, no rate limiting, no timeout on LLM calls' },
            ].map(item => (
              <div key={item.id} className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-zinc-100">{item.id}: {item.name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    item.severity === 'Critical' ? 'bg-red-500/10 text-red-400' :
                    item.severity === 'High' ? 'bg-orange-500/10 text-orange-400' :
                    item.severity === 'Medium' ? 'bg-yellow-500/10 text-yellow-400' :
                    'bg-zinc-800 text-zinc-400'
                  }`}>
                    {item.severity}
                  </span>
                </div>
                <p className="text-xs text-zinc-400">{item.detects}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};

export default GradingDocs;
