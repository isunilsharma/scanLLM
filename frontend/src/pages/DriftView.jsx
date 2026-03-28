import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine
} from 'recharts';
import {
  GitCompare, ArrowUp, ArrowDown, Minus, TrendingUp,
  TrendingDown, AlertTriangle, Plus, Trash2, Activity
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DriftView = () => {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLeft, setSelectedLeft] = useState(null);
  const [selectedRight, setSelectedRight] = useState(null);
  const [diffData, setDiffData] = useState(null);
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    loadScanHistory();
  }, []);

  const loadScanHistory = async () => {
    setLoading(true);
    const token = localStorage.getItem('auth_token');
    try {
      const response = await axios.get(`${API}/scan/history`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const scanList = response.data.scans || response.data || [];
      setScans(scanList);

      // Default: latest vs previous
      if (scanList.length >= 2) {
        setSelectedRight(scanList[0].id || scanList[0].scan_id);
        setSelectedLeft(scanList[1].id || scanList[1].scan_id);
      }
    } catch (error) {
      // Use mock data if endpoint not available
      if (error.response?.status === 404 || error.response?.status === 405) {
        const mockScans = generateMockScans();
        setScans(mockScans);
        if (mockScans.length >= 2) {
          setSelectedRight(mockScans[0].id);
          setSelectedLeft(mockScans[1].id);
        }
      } else {
        console.error('Failed to load scan history:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  const generateMockScans = () => {
    const now = Date.now();
    return [
      {
        id: 'scan-5',
        repo: 'myorg/ai-service',
        created_at: new Date(now - 1 * 86400000).toISOString(),
        risk_score: 62,
        total_findings: 28,
        providers: ['openai', 'anthropic', 'pinecone'],
        findings: [
          { id: 'f1', name: 'OpenAI GPT-4o usage', category: 'llm_provider', severity: 'info', file: 'src/llm.py' },
          { id: 'f2', name: 'Anthropic Claude usage', category: 'llm_provider', severity: 'info', file: 'src/claude.py' },
          { id: 'f3', name: 'Hardcoded API key', category: 'secret', severity: 'critical', file: 'config.py' },
          { id: 'f4', name: 'Missing max_tokens', category: 'unbounded', severity: 'warning', file: 'src/llm.py' },
          { id: 'f5', name: 'Pinecone vector DB', category: 'vector_db', severity: 'info', file: 'src/rag.py' },
          { id: 'f7', name: 'Prompt injection risk', category: 'owasp', severity: 'high', file: 'src/chat.py' },
        ],
      },
      {
        id: 'scan-4',
        repo: 'myorg/ai-service',
        created_at: new Date(now - 3 * 86400000).toISOString(),
        risk_score: 55,
        total_findings: 24,
        providers: ['openai', 'pinecone'],
        findings: [
          { id: 'f1', name: 'OpenAI GPT-4o usage', category: 'llm_provider', severity: 'info', file: 'src/llm.py' },
          { id: 'f3', name: 'Hardcoded API key', category: 'secret', severity: 'critical', file: 'config.py' },
          { id: 'f4', name: 'Missing max_tokens', category: 'unbounded', severity: 'warning', file: 'src/llm.py' },
          { id: 'f5', name: 'Pinecone vector DB', category: 'vector_db', severity: 'info', file: 'src/rag.py' },
          { id: 'f6', name: 'Outdated langchain', category: 'supply_chain', severity: 'medium', file: 'requirements.txt' },
        ],
      },
      {
        id: 'scan-3',
        repo: 'myorg/ai-service',
        created_at: new Date(now - 7 * 86400000).toISOString(),
        risk_score: 48,
        total_findings: 20,
        providers: ['openai'],
      },
      {
        id: 'scan-2',
        repo: 'myorg/ai-service',
        created_at: new Date(now - 14 * 86400000).toISOString(),
        risk_score: 35,
        total_findings: 15,
        providers: ['openai'],
      },
      {
        id: 'scan-1',
        repo: 'myorg/ai-service',
        created_at: new Date(now - 21 * 86400000).toISOString(),
        risk_score: 28,
        total_findings: 12,
        providers: ['openai'],
      },
    ];
  };

  useEffect(() => {
    if (selectedLeft && selectedRight) {
      compareScan();
    }
  }, [selectedLeft, selectedRight]);

  const compareScan = () => {
    const leftScan = scans.find(s => (s.id || s.scan_id) === selectedLeft);
    const rightScan = scans.find(s => (s.id || s.scan_id) === selectedRight);
    if (!leftScan || !rightScan) return;

    const leftFindings = leftScan.findings || [];
    const rightFindings = rightScan.findings || [];

    const leftIds = new Set(leftFindings.map(f => f.id || f.name));
    const rightIds = new Set(rightFindings.map(f => f.id || f.name));

    const added = rightFindings.filter(f => !leftIds.has(f.id || f.name));
    const removed = leftFindings.filter(f => !rightIds.has(f.id || f.name));
    const unchanged = rightFindings.filter(f => leftIds.has(f.id || f.name));

    const leftProviders = new Set(leftScan.providers || []);
    const rightProviders = new Set(rightScan.providers || []);
    const addedProviders = [...rightProviders].filter(p => !leftProviders.has(p));
    const removedProviders = [...leftProviders].filter(p => !rightProviders.has(p));

    setDiffData({
      leftScan,
      rightScan,
      added,
      removed,
      unchanged,
      addedProviders,
      removedProviders,
      riskDelta: (rightScan.risk_score || 0) - (leftScan.risk_score || 0),
      findingsDelta: (rightScan.total_findings || rightFindings.length) - (leftScan.total_findings || leftFindings.length),
    });
  };

  const timelineData = useMemo(() => {
    return [...scans]
      .reverse()
      .map(scan => ({
        date: new Date(scan.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        risk_score: scan.risk_score || 0,
        findings: scan.total_findings || (scan.findings || []).length,
      }));
  }, [scans]);

  const getScanLabel = (scan) => {
    const date = new Date(scan.created_at).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
    return `${scan.repo || 'Scan'} - ${date}`;
  };

  if (loading) {
    return (
      <div className="p-6 md:p-8 bg-zinc-950 min-h-full">
        <div className="max-w-6xl mx-auto space-y-4">
          <div className="h-10 w-64 bg-zinc-800 rounded animate-pulse" />
          <div className="h-6 w-96 bg-zinc-800 rounded animate-pulse" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-28 bg-zinc-900 rounded-lg animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (scans.length < 2) {
    return (
      <div className="p-6 md:p-8 bg-zinc-950 min-h-full">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-2xl md:text-3xl font-bold text-zinc-100 flex items-center gap-3 mb-8">
            <GitCompare className="text-blue-400" size={28} />
            Drift Detection
          </h1>
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="py-16 text-center">
              <Activity className="mx-auto mb-4 text-zinc-600" size={48} />
              <h3 className="text-lg font-medium text-zinc-300 mb-2">Not enough scan data</h3>
              <p className="text-zinc-500 max-w-md mx-auto">
                Run <code className="px-2 py-0.5 bg-zinc-800 rounded text-blue-400 text-sm">scanllm scan . --save</code> twice
                to see drift detection between scans.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 bg-zinc-950 min-h-full">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-zinc-100 flex items-center gap-3">
            <GitCompare className="text-blue-400" size={28} />
            Drift Detection
          </h1>
          <p className="text-zinc-400 mt-1">
            Compare scans to track how your AI dependencies change over time.
          </p>
        </div>

        {/* Scan Selectors */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-6">
          <div className="flex-1">
            <label className="text-xs font-medium text-zinc-400 mb-1 block">Baseline (Before)</label>
            <Select value={selectedLeft} onValueChange={setSelectedLeft}>
              <SelectTrigger className="bg-zinc-900 border-zinc-800 text-zinc-100">
                <SelectValue placeholder="Select baseline scan" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-800">
                {scans.map(scan => (
                  <SelectItem
                    key={scan.id || scan.scan_id}
                    value={scan.id || scan.scan_id}
                    className="text-zinc-100 focus:bg-zinc-800"
                  >
                    {getScanLabel(scan)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-end justify-center pb-1">
            <ArrowDown className="text-zinc-600 rotate-0 sm:-rotate-90" size={20} />
          </div>

          <div className="flex-1">
            <label className="text-xs font-medium text-zinc-400 mb-1 block">Current (After)</label>
            <Select value={selectedRight} onValueChange={setSelectedRight}>
              <SelectTrigger className="bg-zinc-900 border-zinc-800 text-zinc-100">
                <SelectValue placeholder="Select current scan" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-800">
                {scans.map(scan => (
                  <SelectItem
                    key={scan.id || scan.scan_id}
                    value={scan.id || scan.scan_id}
                    className="text-zinc-100 focus:bg-zinc-800"
                  >
                    {getScanLabel(scan)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Summary Cards */}
        {diffData && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {/* Risk Score Delta */}
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-4">
                  <p className="text-xs font-medium text-zinc-400 mb-2">Risk Score</p>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-zinc-300">{diffData.leftScan.risk_score || 0}</span>
                    <span className="text-zinc-500">→</span>
                    <span className={`text-2xl font-bold ${
                      diffData.riskDelta > 0 ? 'text-red-400' : diffData.riskDelta < 0 ? 'text-green-400' : 'text-zinc-300'
                    }`}>
                      {diffData.rightScan.risk_score || 0}
                    </span>
                    {diffData.riskDelta !== 0 && (
                      <Badge className={`ml-1 ${
                        diffData.riskDelta > 0
                          ? 'bg-red-500/20 text-red-400 border-red-500/30'
                          : 'bg-green-500/20 text-green-400 border-green-500/30'
                      }`}>
                        {diffData.riskDelta > 0 ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
                        <span className="ml-0.5">{Math.abs(diffData.riskDelta)}</span>
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Findings Delta */}
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-4">
                  <p className="text-xs font-medium text-zinc-400 mb-2">Total Findings</p>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-zinc-300">
                      {diffData.leftScan.total_findings || (diffData.leftScan.findings || []).length}
                    </span>
                    <span className="text-zinc-500">→</span>
                    <span className="text-2xl font-bold text-zinc-300">
                      {diffData.rightScan.total_findings || (diffData.rightScan.findings || []).length}
                    </span>
                    {diffData.findingsDelta !== 0 && (
                      <Badge className={`ml-1 ${
                        diffData.findingsDelta > 0
                          ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
                          : 'bg-green-500/20 text-green-400 border-green-500/30'
                      }`}>
                        {diffData.findingsDelta > 0 ? '+' : ''}{diffData.findingsDelta}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Providers Added */}
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-4">
                  <p className="text-xs font-medium text-zinc-400 mb-2">Providers Added</p>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-green-400">{diffData.addedProviders.length}</span>
                    {diffData.addedProviders.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {diffData.addedProviders.map(p => (
                          <Badge key={p} className="bg-green-500/20 text-green-400 border-green-500/30 text-xs">
                            +{p}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Providers Removed */}
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-4">
                  <p className="text-xs font-medium text-zinc-400 mb-2">Providers Removed</p>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-red-400">{diffData.removedProviders.length}</span>
                    {diffData.removedProviders.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {diffData.removedProviders.map(p => (
                          <Badge key={p} className="bg-red-500/20 text-red-400 border-red-500/30 text-xs">
                            -{p}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Diff View */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
              {/* Added Findings */}
              <Card className="bg-zinc-900 border-zinc-800">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-green-400 flex items-center gap-2">
                    <Plus size={16} />
                    Added Findings ({diffData.added.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {diffData.added.length === 0 ? (
                    <p className="text-zinc-500 text-sm py-4 text-center">No new findings</p>
                  ) : (
                    <div className="space-y-2">
                      {diffData.added.map((finding, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-3 bg-green-500/5 border border-green-500/20 rounded-lg"
                        >
                          <div>
                            <p className="text-sm font-medium text-green-300">{finding.name}</p>
                            <p className="text-xs text-zinc-500">{finding.file}</p>
                          </div>
                          <Badge className="bg-green-500/20 text-green-400 border-green-500/30 text-xs">
                            {finding.severity}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Removed Findings */}
              <Card className="bg-zinc-900 border-zinc-800">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-red-400 flex items-center gap-2">
                    <Trash2 size={16} />
                    Removed Findings ({diffData.removed.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {diffData.removed.length === 0 ? (
                    <p className="text-zinc-500 text-sm py-4 text-center">No removed findings</p>
                  ) : (
                    <div className="space-y-2">
                      {diffData.removed.map((finding, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-3 bg-red-500/5 border border-red-500/20 rounded-lg"
                        >
                          <div>
                            <p className="text-sm font-medium text-red-300 line-through">{finding.name}</p>
                            <p className="text-xs text-zinc-500 line-through">{finding.file}</p>
                          </div>
                          <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-xs">
                            {finding.severity}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Unchanged Findings */}
            {diffData.unchanged.length > 0 && (
              <Card className="bg-zinc-900 border-zinc-800 mb-6">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                    <Minus size={16} />
                    Unchanged Findings ({diffData.unchanged.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {diffData.unchanged.map((finding, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between p-3 bg-zinc-800/50 border border-zinc-800 rounded-lg"
                      >
                        <div>
                          <p className="text-sm font-medium text-zinc-300">{finding.name}</p>
                          <p className="text-xs text-zinc-500">{finding.file}</p>
                        </div>
                        <Badge variant="outline" className="text-zinc-400 border-zinc-700 text-xs">
                          {finding.severity}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* Timeline Chart */}
        {timelineData.length > 1 && (
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                <TrendingUp size={16} className="text-blue-400" />
                Risk Score Timeline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timelineData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis
                      dataKey="date"
                      stroke="#71717a"
                      fontSize={12}
                      tickLine={false}
                    />
                    <YAxis
                      stroke="#71717a"
                      fontSize={12}
                      tickLine={false}
                      domain={[0, 100]}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#18181b',
                        border: '1px solid #3f3f46',
                        borderRadius: '8px',
                        color: '#e4e4e7',
                      }}
                    />
                    <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'High Risk', fill: '#ef4444', fontSize: 10 }} />
                    <Line
                      type="monotone"
                      dataKey="risk_score"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                      activeDot={{ r: 6, fill: '#60a5fa' }}
                      name="Risk Score"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default DriftView;
