import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import ResultsOverview from './ResultsOverview';
import FileList from './FileList';
import SecurityOverview from './SecurityOverview';
import OwaspMapping from './OwaspMapping';
import DependencyGraph from './DependencyGraph';
import ReportDownloads from './ReportDownloads';
import { Separator } from './ui/separator';
import { toast } from 'sonner';
import { Shield, RefreshCw } from 'lucide-react';

function getRiskGrade(score) {
  if (score == null) return null;
  if (score <= 20) return 'A';
  if (score <= 40) return 'B';
  if (score <= 60) return 'C';
  if (score <= 80) return 'D';
  return 'F';
}

function getRiskBadgeVariant(score) {
  if (score == null) return 'secondary';
  if (score <= 40) return 'default';
  if (score <= 60) return 'secondary';
  return 'destructive';
}

const ScanResults = ({ result, showRescan = true }) => {
  const navigate = useNavigate();
  const [selectedFramework, setSelectedFramework] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  const handleRescan = () => {
    if (result.repo_url) {
      const parts = result.repo_url.replace('https://github.com/', '').split('/');
      if (parts.length >= 2) {
        navigate(`/app/repo/${parts[0]}/${parts[1]}`);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }
  };

  // Extract unique frameworks
  const frameworks = useMemo(() => {
    const uniqueFrameworks = new Set();
    result.files.forEach(file => {
      file.frameworks.forEach(fw => uniqueFrameworks.add(fw));
    });
    return Array.from(uniqueFrameworks).sort();
  }, [result]);

  // Filter files based on framework and search
  const filteredFiles = useMemo(() => {
    let files = result.files;
    if (selectedFramework !== 'all') {
      files = files.filter(file => file.frameworks.includes(selectedFramework));
    }
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      files = files.filter(file =>
        file.file_path.toLowerCase().includes(query)
      );
    }
    return files;
  }, [result.files, selectedFramework, searchQuery]);

  // Calculate filtered stats
  const filteredStats = useMemo(() => {
    const totalOccurrences = filteredFiles.reduce(
      (sum, file) => sum + file.occurrences.length,
      0
    );
    return {
      files_count: filteredFiles.length,
      total_occurrences: totalOccurrences
    };
  }, [filteredFiles]);

  const riskScore = result.risk_score ?? result.risk_data?.score ?? null;
  const riskGrade = getRiskGrade(riskScore);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200" data-testid="scan-results">
      {/* Scan Metadata Header */}
      <div className="px-4 md:px-6 py-4 border-b border-indigo-100 bg-gradient-to-r from-indigo-50/60 to-slate-50">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h2 className="text-lg md:text-xl font-semibold text-gray-900">Scan Results</h2>
              <Badge
                variant={result.status === 'SUCCESS' ? 'default' : 'destructive'}
                className={`text-xs flex-shrink-0 ${result.status === 'SUCCESS' ? 'bg-emerald-600 hover:bg-emerald-600/80' : ''}`}
                data-testid="scan-status"
              >
                {result.status}
              </Badge>
              {riskScore != null && (
                <Badge
                  variant={getRiskBadgeVariant(riskScore)}
                  className={`text-xs flex-shrink-0 flex items-center gap-1 ${riskScore <= 40 ? 'bg-emerald-600 hover:bg-emerald-600/80' : riskScore <= 60 ? 'bg-amber-500 hover:bg-amber-500/80 text-white' : 'bg-red-600 hover:bg-red-600/80'}`}
                >
                  <Shield size={10} />
                  Risk: {Math.round(riskScore)}{riskGrade ? ` (${riskGrade})` : ''}
                </Badge>
              )}
            </div>
            <p className="text-sm text-gray-600 truncate">{result.repo_url}</p>
          </div>
          {showRescan && (
            <Button onClick={handleRescan} variant="outline" size="sm" className="w-full sm:w-auto border-indigo-200 text-indigo-700 hover:bg-indigo-50">
              <RefreshCw size={14} className="mr-2" />
              Rescan
            </Button>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="p-4 md:p-6 border-b border-slate-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
          <div className="bg-slate-50 rounded-lg p-4 border-t-2 border-indigo-500">
            <p className="text-xs text-slate-500 mb-1 font-medium">Total Files</p>
            <p className="text-2xl font-bold text-indigo-900" data-testid="total-files">{result.files_count}</p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 border-t-2 border-indigo-400">
            <p className="text-xs text-slate-500 mb-1 font-medium">Total Matches</p>
            <p className="text-2xl font-bold text-indigo-900" data-testid="total-matches">{result.total_occurrences}</p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 border-t-2 border-indigo-300">
            <p className="text-xs text-slate-500 mb-1 font-medium">Frameworks Found</p>
            <p className="text-2xl font-bold text-indigo-900" data-testid="frameworks-count">{frameworks.length}</p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 border-t-2 border-indigo-200">
            <p className="text-xs text-slate-500 mb-1 font-medium">Avg per File</p>
            <p className="text-2xl font-bold text-indigo-900">
              {result.files_count > 0 ? (result.total_occurrences / result.files_count).toFixed(1) : '0'}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <div className="px-6 pt-6 border-b border-slate-200">
          <TabsList className="grid w-full max-w-2xl grid-cols-6 bg-indigo-50/60">
            <TabsTrigger value="overview" className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white" data-testid="tab-overview">Overview</TabsTrigger>
            <TabsTrigger value="security" className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white" data-testid="tab-security">Security</TabsTrigger>
            <TabsTrigger value="graph" className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white" data-testid="tab-graph">Graph</TabsTrigger>
            <TabsTrigger value="files" className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white" data-testid="tab-files">Files</TabsTrigger>
            <TabsTrigger value="reports" className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white" data-testid="tab-reports">Reports</TabsTrigger>
            <TabsTrigger value="raw" className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white" data-testid="tab-raw">Raw Data</TabsTrigger>
          </TabsList>
        </div>

        {/* Overview Tab */}
        <TabsContent value="overview" className="p-6 space-y-6">
          <ResultsOverview result={result} frameworks={frameworks} />
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="p-6 space-y-6">
          <SecurityOverview
            riskScore={result.risk_data || riskScore || 0}
            owaspData={result.owasp_data}
            graphAnalysis={result.graph_analysis}
          />
          <OwaspMapping owaspData={result.owasp_data} />
        </TabsContent>

        {/* Graph Tab */}
        <TabsContent value="graph" className="p-6 space-y-6">
          <DependencyGraph graphData={result.dependency_graph} />
        </TabsContent>

        {/* Files Tab */}
        <TabsContent value="files" className="p-6 space-y-6">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                data-testid="search-input"
                className="w-full"
              />
            </div>
            <div className="sm:w-48">
              <Select value={selectedFramework} onValueChange={setSelectedFramework}>
                <SelectTrigger data-testid="framework-filter">
                  <SelectValue placeholder="Filter by framework" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Frameworks</SelectItem>
                  {frameworks.map(fw => (
                    <SelectItem key={fw} value={fw}>{fw}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Filtered Stats */}
          {(selectedFramework !== 'all' || searchQuery.trim()) && (
            <div className="flex gap-6 text-sm text-slate-600">
              <span>Showing {filteredStats.files_count} files</span>
              <span>•</span>
              <span>{filteredStats.total_occurrences} occurrences</span>
            </div>
          )}

          {/* File List */}
          <FileList files={filteredFiles} />
        </TabsContent>

        {/* Reports Tab */}
        <TabsContent value="reports" className="p-6 space-y-6">
          <ReportDownloads scanId={result.scan_id} />
        </TabsContent>

        {/* Raw Data Tab */}
        <TabsContent value="raw" className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-900">Raw JSON Data</h3>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(result, null, 2));
                  toast.success('JSON copied to clipboard!');
                }}
              >
                <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy JSON
              </Button>
              <Button
                size="sm"
                onClick={() => {
                  const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `scan-result-${result.scan_id}.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                  toast.success('JSON downloaded!');
                }}
              >
                <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download JSON
              </Button>
            </div>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 overflow-auto max-h-[600px]">
            <pre className="text-xs text-slate-800" data-testid="raw-data">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ScanResults;
