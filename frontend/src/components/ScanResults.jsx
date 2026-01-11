import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import ResultsOverview from './ResultsOverview';
import FileList from './FileList';
import { Separator } from './ui/separator';
import { toast } from 'sonner';

const ScanResults = ({ result, showRescan = true }) => {
  const navigate = useNavigate();
  const [selectedFramework, setSelectedFramework] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  const handleRescan = () => {
    // Extract owner/repo from result URL
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

    // Filter by framework
    if (selectedFramework !== 'all') {
      files = files.filter(file => file.frameworks.includes(selectedFramework));
    }

    // Filter by search query
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

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200" data-testid="scan-results">
      {/* Scan Metadata Header */}
      <div className="px-4 md:px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h2 className="text-lg md:text-xl font-semibold text-gray-900">Scan Results</h2>
              <Badge 
                variant={result.status === 'SUCCESS' ? 'default' : 'destructive'}
                className="text-xs flex-shrink-0"
                data-testid="scan-status"
              >
                {result.status}
              </Badge>
            </div>
            <p className="text-sm text-gray-600 truncate">{result.repo_url}</p>
          </div>
          {showRescan && (
            <Button onClick={handleRescan} variant="outline" size="sm" className="w-full sm:w-auto">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Rescan
            </Button>
          )}
        </div>
      </div>

      {/* Quick Stats - Responsive Grid */}
      <div className="p-4 md:p-6 border-b border-slate-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-600 mb-1">Total Files</p>
            <p className="text-2xl font-semibold text-slate-900" data-testid="total-files">{result.files_count}</p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-600 mb-1">Total Matches</p>
            <p className="text-2xl font-semibold text-slate-900" data-testid="total-matches">{result.total_occurrences}</p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-600 mb-1">Frameworks Found</p>
            <p className="text-2xl font-semibold text-slate-900" data-testid="frameworks-count">{frameworks.length}</p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-600 mb-1">Avg per File</p>
            <p className="text-2xl font-semibold text-slate-900">
              {result.files_count > 0 ? (result.total_occurrences / result.files_count).toFixed(1) : '0'}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <div className="px-6 pt-6 border-b border-slate-200">
          <TabsList className="grid w-full max-w-md grid-cols-3">
            <TabsTrigger value="overview" data-testid="tab-overview">Overview</TabsTrigger>
            <TabsTrigger value="files" data-testid="tab-files">Files</TabsTrigger>
            <TabsTrigger value="raw" data-testid="tab-raw">Raw Data</TabsTrigger>
          </TabsList>
        </div>

        {/* Overview Tab */}
        <TabsContent value="overview" className="p-6 space-y-6">
          <ResultsOverview result={result} frameworks={frameworks} />
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

        {/* Raw Data Tab */}
        <TabsContent value="raw" className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-900">Raw JSON Data</h3>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(result, null, 2));
                  toast.success('JSON copied to clipboard!');
                }}
                className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors flex items-center gap-1.5"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy JSON
              </button>
              <button
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
                className="px-3 py-1.5 text-xs font-medium text-white bg-primary rounded-md hover:bg-primary/90 transition-colors flex items-center gap-1.5"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download JSON
              </button>
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
