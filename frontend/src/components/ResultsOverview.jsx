import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import KeyInsights from './KeyInsights';
import RiskFlags from './RiskFlags';
import AIHotspots from './AIHotspots';
import UsageTypes from './UsageTypes';
import RecommendedActions from './RecommendedActions';
import PolicyEvaluation from './PolicyEvaluation';
import BlastRadiusSummary from './BlastRadiusSummary';
import ModelContracts from './ModelContracts';
import OwnershipHotspots from './OwnershipHotspots';
import AIHeatmap from './AIHeatmap';
import ScanHistory from './ScanHistory';
import ExplainRepoButton from './ExplainRepoButton';
import SecurityOverview from './SecurityOverview';

const COLORS = ['#06b6d4', '#22d3ee', '#67e8f9', '#a5f3fc', '#cffafe', '#ecfeff'];

const ResultsOverview = ({ result, frameworks }) => {
  // Framework distribution data
  const frameworkData = useMemo(() => {
    if (result.frameworks_summary) {
      return result.frameworks_summary.map(fw => ({
        name: fw.framework,
        count: fw.total_matches
      }));
    }
    // Fallback to old calculation
    const counts = {};
    result.files.forEach(file => {
      file.frameworks.forEach(fw => {
        counts[fw] = (counts[fw] || 0) + file.occurrences.length;
      });
    });
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
  }, [result]);

  // Files per framework
  const filesPerFramework = useMemo(() => {
    if (result.frameworks_summary) {
      return result.frameworks_summary.map(fw => ({
        name: fw.framework,
        files: fw.files_count
      }));
    }
    // Fallback
    const counts = {};
    result.files.forEach(file => {
      file.frameworks.forEach(fw => {
        counts[fw] = (counts[fw] || 0) + 1;
      });
    });
    return Object.entries(counts)
      .map(([name, files]) => ({ name, files }))
      .sort((a, b) => b.files - a.files);
  }, [result]);

  // Top files by occurrences
  const topFiles = useMemo(() => {
    return [...result.files]
      .sort((a, b) => b.occurrences.length - a.occurrences.length)
      .slice(0, 5);
  }, [result]);

  const hasRiskData = result.risk_score != null || result.risk_data != null;
  const riskScore = result.risk_data || result.risk_score || 0;

  return (
    <div className="space-y-8">
      {/* Security Overview - shown at top if risk data available */}
      {hasRiskData && (
        <>
          <SecurityOverview
            riskScore={riskScore}
            owaspData={result.owasp_data}
            graphAnalysis={result.graph_analysis}
          />
          <Separator />
        </>
      )}

      {/* Key Insights */}
      <KeyInsights result={result} />

      <Separator />

      {/* Explain My Repo AI Button */}
      <ExplainRepoButton scanId={result.scan_id} />

      <Separator />

      {/* Policy Evaluation */}
      <PolicyEvaluation policiesResult={result.policies_result} />

      <Separator />

      {/* Blast Radius Summary */}
      <BlastRadiusSummary blastRadiusSummary={result.blast_radius_summary} />

      {/* Framework Badges */}
      <div>
        <h3 className="text-sm font-medium text-zinc-100 mb-3">Detected Frameworks</h3>
        <div className="flex flex-wrap gap-2">
          {frameworks.map(fw => (
            <Badge key={fw} variant="secondary" className="text-sm py-1 px-3">
              {fw}
            </Badge>
          ))}
        </div>
      </div>

      <Separator />

      {/* Risk Flags */}
      <RiskFlags riskFlags={result.risk_flags} />

      <Separator />

      {/* Usage Types */}
      <UsageTypes frameworksSummary={result.frameworks_summary} />

      <Separator />

      {/* AI Hotspots */}
      <AIHotspots hotspots={result.hotspots} />

      <Separator />

      {/* Ownership Hotspots */}
      <OwnershipHotspots ownershipSummary={result.ownership_summary} />

      <Separator />

      {/* Model & Prompt Contracts */}
      <ModelContracts contracts={result.contracts} />

      <Separator />

      {/* AI Heatmap */}
      <AIHeatmap heatmap={result.heatmap} />

      <Separator />

      {/* Charts Row */}
      <div className="grid md:grid-cols-2 gap-8">
        {/* Occurrences by Framework */}
        <div>
          <h3 className="text-sm font-medium text-zinc-100 mb-4">Occurrences by Framework</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={frameworkData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} angle={-45} textAnchor="end" height={80} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px', color: '#e4e4e7' }}
              />
              <Bar dataKey="count" fill="#06b6d4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Files by Framework */}
        <div>
          <h3 className="text-sm font-medium text-zinc-100 mb-4">Files by Framework</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={filesPerFramework}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="files"
              >
                {filesPerFramework.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <Separator />

      {/* Top Files Table */}
      <div>
        <h3 className="text-sm font-medium text-zinc-100 mb-4">Top Files by Matches</h3>
        <div className="border border-zinc-800 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-zinc-800/50">
              <tr>
                <th className="text-left text-xs font-medium text-zinc-400 px-4 py-3">File Path</th>
                <th className="text-left text-xs font-medium text-zinc-400 px-4 py-3">Frameworks</th>
                <th className="text-right text-xs font-medium text-zinc-400 px-4 py-3">Matches</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {topFiles.map((file, idx) => (
                <tr key={idx} className="hover:bg-zinc-800/30">
                  <td className="px-4 py-3 text-sm text-zinc-100 font-mono max-w-[200px] truncate">{file.file_path}</td>
                  <td className="px-4 py-3 max-w-[160px] md:max-w-none">
                    <div className="flex flex-wrap gap-1">
                      {file.frameworks.map(fw => (
                        <Badge key={fw} variant="outline" className="text-xs truncate max-w-full">
                          {fw}
                        </Badge>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-zinc-100 text-right font-medium">
                    {file.occurrences.length}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Separator />

      {/* Recommended Actions */}
      <RecommendedActions actions={result.recommended_actions} />

      <Separator />

      {/* Scan History & Drift */}
      <ScanHistory repoUrl={result.repo_url} />
    </div>
  );
};

export default ResultsOverview;
