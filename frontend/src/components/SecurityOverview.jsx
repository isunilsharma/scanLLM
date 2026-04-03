import React from 'react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Skeleton } from './ui/skeleton';
import RiskScoreGauge from './RiskScoreGauge';
import {
  Shield, ShieldAlert, ShieldCheck, AlertTriangle,
  KeyRound, Target, Zap, Activity
} from 'lucide-react';

const SecurityOverview = ({ riskScore, owaspData, graphAnalysis, loading = false }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
      </div>
    );
  }

  // Compute OWASP summary
  const owaspCategories = owaspData?.categories || [];
  const owaspDetected = owaspCategories.filter((c) => c.status === 'detected').length;
  const owaspPartial = owaspCategories.filter((c) => c.status === 'partially').length;
  const owaspClear = owaspCategories.filter((c) => c.status === 'not_detected').length;
  const owaspTotal = owaspData?.coverage?.total || 8;

  // Graph analysis stats
  const criticalFindings = graphAnalysis?.critical_findings || riskScore?.owasp_critical_count || 0;
  const secretsFound = graphAnalysis?.secrets_found || riskScore?.secrets_count || 0;
  const concentrationRisk = graphAnalysis?.concentration_risk || riskScore?.concentration_risk || null;
  const totalNodes = graphAnalysis?.total_nodes || 0;
  const totalEdges = graphAnalysis?.total_edges || 0;

  const score = typeof riskScore === 'number' ? riskScore : riskScore?.score || 0;
  const grade = typeof riskScore === 'object' ? riskScore?.grade : undefined;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Left: Risk Score Gauge */}
      <Card className="flex items-center justify-center p-6">
        <RiskScoreGauge score={score} grade={grade} />
      </Card>

      {/* Center: OWASP Quick Summary */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Shield size={18} className="text-zinc-400" />
            <h3 className="text-sm font-semibold text-zinc-200">OWASP LLM Coverage</h3>
          </div>

          <div className="space-y-3">
            {/* Summary bars */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 min-w-[80px]">
                <ShieldCheck size={14} className="text-green-500" />
                <span className="text-xs text-zinc-400">Clear</span>
              </div>
              <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 rounded-full transition-all"
                  style={{ width: `${(owaspClear / owaspTotal) * 100}%` }}
                />
              </div>
              <span className="text-xs font-semibold text-zinc-300 min-w-[20px] text-right">{owaspClear}</span>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 min-w-[80px]">
                <AlertTriangle size={14} className="text-amber-500" />
                <span className="text-xs text-zinc-400">Partial</span>
              </div>
              <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-400 rounded-full transition-all"
                  style={{ width: `${(owaspPartial / owaspTotal) * 100}%` }}
                />
              </div>
              <span className="text-xs font-semibold text-zinc-300 min-w-[20px] text-right">{owaspPartial}</span>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 min-w-[80px]">
                <ShieldAlert size={14} className="text-red-500" />
                <span className="text-xs text-zinc-400">Detected</span>
              </div>
              <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500 rounded-full transition-all"
                  style={{ width: `${(owaspDetected / owaspTotal) * 100}%` }}
                />
              </div>
              <span className="text-xs font-semibold text-zinc-300 min-w-[20px] text-right">{owaspDetected}</span>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-zinc-800">
            <p className="text-xs text-zinc-500">
              {owaspTotal} categories scanned
              {owaspDetected === 0 && owaspPartial === 0 && (
                <span className="text-green-600 font-medium ml-1">- All clear</span>
              )}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Right: Key Stats */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Activity size={18} className="text-zinc-400" />
            <h3 className="text-sm font-semibold text-zinc-200">Key Findings</h3>
          </div>

          <div className="space-y-3">
            {/* Critical Findings */}
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-red-500/10 border border-red-500/20">
              <div className="flex items-center gap-2">
                <Zap size={14} className="text-red-500" />
                <span className="text-xs font-medium text-zinc-300">Critical Findings</span>
              </div>
              <span className="text-sm font-bold text-red-600">{criticalFindings}</span>
            </div>

            {/* Secrets Found */}
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <div className="flex items-center gap-2">
                <KeyRound size={14} className="text-amber-500" />
                <span className="text-xs font-medium text-zinc-300">Secrets Found</span>
              </div>
              <span className="text-sm font-bold text-amber-600">{secretsFound}</span>
            </div>

            {/* Concentration Risk */}
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <div className="flex items-center gap-2">
                <Target size={14} className="text-blue-500" />
                <span className="text-xs font-medium text-zinc-300">Concentration Risk</span>
              </div>
              {concentrationRisk != null ? (
                <Badge
                  variant={concentrationRisk === 'high' ? 'destructive' : concentrationRisk === 'medium' ? 'secondary' : 'default'}
                  className="text-[10px]"
                >
                  {typeof concentrationRisk === 'string' ? concentrationRisk.toUpperCase() : `${concentrationRisk}%`}
                </Badge>
              ) : (
                <span className="text-xs text-zinc-500">N/A</span>
              )}
            </div>

            {/* Graph Stats */}
            {(totalNodes > 0 || totalEdges > 0) && (
              <div className="pt-2 border-t border-zinc-800 flex items-center gap-4 text-xs text-zinc-500">
                <span>{totalNodes} component{totalNodes !== 1 ? 's' : ''}</span>
                <span>{totalEdges} connection{totalEdges !== 1 ? 's' : ''}</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SecurityOverview;
