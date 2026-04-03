import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Skeleton } from './ui/skeleton';
import { Separator } from './ui/separator';
import {
  Shield, ShieldAlert, ShieldCheck, ShieldX,
  ChevronDown, ChevronUp, AlertTriangle, CheckCircle, XCircle, Info
} from 'lucide-react';

const OWASP_DEFAULTS = [
  { id: 'LLM01', name: 'Prompt Injection', description: 'User input concatenated into prompts without sanitization.', remediation: 'Use parameterized prompts, input validation, and content filtering before passing user input to LLMs.' },
  { id: 'LLM02', name: 'Sensitive Info Disclosure', description: 'Credentials or PII in system prompts, missing output filtering.', remediation: 'Remove sensitive data from prompt templates. Implement output filtering and PII detection on LLM responses.' },
  { id: 'LLM03', name: 'Supply Chain', description: 'Unverified model sources, outdated AI packages with CVEs.', remediation: 'Pin model versions, verify checksums, keep AI packages updated. Use dependency scanning for known CVEs.' },
  { id: 'LLM05', name: 'Improper Output Handling', description: 'eval(llm_response), unsanitized LLM output to SQL/shell/HTML.', remediation: 'Never eval() LLM output. Sanitize and validate all LLM outputs before using in SQL, shell, or HTML contexts.' },
  { id: 'LLM06', name: 'Excessive Agency', description: 'Agent configs with broad tool access, missing human-in-the-loop.', remediation: 'Apply least-privilege to agent tools. Implement human-in-the-loop for destructive actions. Limit agent scope.' },
  { id: 'LLM07', name: 'System Prompt Leakage', description: 'API keys or secrets in prompt templates, business logic exposure.', remediation: 'Store secrets in environment variables, not prompts. Use prompt management systems with access controls.' },
  { id: 'LLM08', name: 'Vector/Embedding Weaknesses', description: 'Unauthenticated vector DB connections, no access controls.', remediation: 'Authenticate all vector DB connections. Implement access controls and data isolation for embeddings.' },
  { id: 'LLM10', name: 'Unbounded Consumption', description: 'Missing max_tokens, no rate limiting, no timeout on LLM calls.', remediation: 'Set max_tokens on all LLM calls. Implement rate limiting and timeouts. Monitor usage and set cost alerts.' },
];

const STATUS_CONFIG = {
  detected: { icon: XCircle, color: '#ef4444', bgColor: 'rgba(239,68,68,0.1)', borderColor: 'rgba(239,68,68,0.2)', label: 'Detected' },
  partially: { icon: AlertTriangle, color: '#f59e0b', bgColor: 'rgba(245,158,11,0.1)', borderColor: 'rgba(245,158,11,0.2)', label: 'Partial' },
  not_detected: { icon: CheckCircle, color: '#22c55e', bgColor: 'rgba(34,197,94,0.1)', borderColor: 'rgba(34,197,94,0.2)', label: 'Clear' },
};

const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
};

const OwaspMapping = ({ owaspData, loading = false }) => {
  const [expandedId, setExpandedId] = useState(null);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Shield size={20} className="text-zinc-500" />
            OWASP LLM Top 10
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-8 w-full" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Merge provided data with defaults
  const categories = OWASP_DEFAULTS.map((def) => {
    const match = owaspData?.categories?.find((c) => c.id === def.id);
    return {
      ...def,
      status: match?.status || 'not_detected',
      severity: match?.severity || null,
      findings_count: match?.findings_count || 0,
      description: match?.description || def.description,
      remediation: match?.remediation || def.remediation,
    };
  });

  const coverage = owaspData?.coverage || {
    detected: categories.filter((c) => c.status === 'detected').length,
    partially: categories.filter((c) => c.status === 'partially').length,
    not_detected: categories.filter((c) => c.status === 'not_detected').length,
    total: categories.length,
  };

  const detectedCount = coverage.detected + (coverage.partially || 0);
  const coveragePercent = coverage.total > 0 ? Math.round(((coverage.total - detectedCount) / coverage.total) * 100) : 100;

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Shield size={20} className="text-zinc-400" />
            OWASP LLM Top 10 (2025)
          </CardTitle>
          <Badge variant={coveragePercent >= 80 ? 'default' : coveragePercent >= 50 ? 'secondary' : 'destructive'}>
            {coveragePercent}% Clear
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        {/* Coverage Summary Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-zinc-500">
            <span>{coverage.not_detected || 0} clear</span>
            <span>{coverage.partially || 0} partial</span>
            <span>{coverage.detected || 0} detected</span>
          </div>
          <div className="flex h-2.5 rounded-full overflow-hidden bg-zinc-800">
            {coverage.not_detected > 0 && (
              <div
                className="bg-green-500 transition-all"
                style={{ width: `${((coverage.not_detected || 0) / coverage.total) * 100}%` }}
              />
            )}
            {(coverage.partially || 0) > 0 && (
              <div
                className="bg-amber-400 transition-all"
                style={{ width: `${((coverage.partially || 0) / coverage.total) * 100}%` }}
              />
            )}
            {coverage.detected > 0 && (
              <div
                className="bg-red-500 transition-all"
                style={{ width: `${(coverage.detected / coverage.total) * 100}%` }}
              />
            )}
          </div>
        </div>

        <Separator />

        {/* OWASP Category Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {categories.map((cat) => {
            const statusConfig = STATUS_CONFIG[cat.status] || STATUS_CONFIG.not_detected;
            const StatusIcon = statusConfig.icon;
            const isExpanded = expandedId === cat.id;

            return (
              <div key={cat.id} className="col-span-1">
                <button
                  onClick={() => setExpandedId(isExpanded ? null : cat.id)}
                  className="w-full text-left p-3 rounded-lg border-2 transition-all hover:shadow-sm"
                  style={{
                    backgroundColor: statusConfig.bgColor,
                    borderColor: isExpanded ? statusConfig.color : statusConfig.borderColor,
                  }}
                >
                  <div className="flex items-start justify-between mb-1.5">
                    <StatusIcon size={16} style={{ color: statusConfig.color }} className="mt-0.5 flex-shrink-0" />
                    <Badge
                      variant="outline"
                      className="text-[10px] px-1.5 py-0"
                      style={{ borderColor: statusConfig.color, color: statusConfig.color }}
                    >
                      {cat.id}
                    </Badge>
                  </div>
                  <p className="text-xs font-semibold text-zinc-200 leading-tight mb-1">
                    {cat.name}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-zinc-500">
                      {cat.findings_count > 0 ? `${cat.findings_count} finding${cat.findings_count !== 1 ? 's' : ''}` : statusConfig.label}
                    </span>
                    {isExpanded ? (
                      <ChevronUp size={12} className="text-zinc-500" />
                    ) : (
                      <ChevronDown size={12} className="text-zinc-500" />
                    )}
                  </div>
                </button>

                {/* Expanded detail */}
                {isExpanded && (
                  <div
                    className="mt-2 p-3 rounded-lg border text-xs space-y-2"
                    style={{ borderColor: statusConfig.borderColor, backgroundColor: '#18181b' }}
                  >
                    <div>
                      <p className="font-medium text-zinc-300 mb-1 flex items-center gap-1">
                        <Info size={12} /> What we detect
                      </p>
                      <p className="text-zinc-400 leading-relaxed">{cat.description}</p>
                    </div>
                    <Separator />
                    <div>
                      <p className="font-medium text-zinc-300 mb-1 flex items-center gap-1">
                        <ShieldCheck size={12} className="text-green-600" /> Remediation
                      </p>
                      <p className="text-zinc-400 leading-relaxed">{cat.remediation}</p>
                    </div>
                    {cat.severity && (
                      <div className="pt-1">
                        <Badge
                          variant="outline"
                          className="text-[10px]"
                          style={{
                            borderColor: SEVERITY_COLORS[cat.severity] || '#94a3b8',
                            color: SEVERITY_COLORS[cat.severity] || '#94a3b8',
                          }}
                        >
                          {cat.severity.toUpperCase()} SEVERITY
                        </Badge>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default OwaspMapping;
