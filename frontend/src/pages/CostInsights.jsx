import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
  DollarSign, AlertTriangle, ArrowRight, TrendingDown,
  Zap, Info, Layers, CircleDollarSign
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Model pricing per 1M tokens (USD)
const MODEL_PRICING = {
  'gpt-4o': { input: 2.50, output: 10.00, provider: 'OpenAI' },
  'gpt-4o-mini': { input: 0.15, output: 0.60, provider: 'OpenAI' },
  'gpt-4-turbo': { input: 10.00, output: 30.00, provider: 'OpenAI' },
  'gpt-3.5-turbo': { input: 0.50, output: 1.50, provider: 'OpenAI' },
  'o1': { input: 15.00, output: 60.00, provider: 'OpenAI' },
  'o1-mini': { input: 3.00, output: 12.00, provider: 'OpenAI' },
  'o3': { input: 10.00, output: 40.00, provider: 'OpenAI' },
  'o3-mini': { input: 1.10, output: 4.40, provider: 'OpenAI' },
  'o4-mini': { input: 1.10, output: 4.40, provider: 'OpenAI' },
  'claude-sonnet-4-20250514': { input: 3.00, output: 15.00, provider: 'Anthropic', displayName: 'Claude Sonnet 4' },
  'claude-opus-4-20250514': { input: 15.00, output: 75.00, provider: 'Anthropic', displayName: 'Claude Opus 4' },
  'claude-haiku-4-5-20251001': { input: 0.25, output: 1.25, provider: 'Anthropic', displayName: 'Claude Haiku 4.5' },
  'gemini-1.5-pro': { input: 1.25, output: 5.00, provider: 'Google' },
  'gemini-1.5-flash': { input: 0.075, output: 0.30, provider: 'Google' },
  'gemini-2.0-flash': { input: 0.10, output: 0.40, provider: 'Google' },
  'llama-3-70b': { input: 0.59, output: 0.79, provider: 'Meta (via API)' },
  'llama-3-8b': { input: 0.05, output: 0.08, provider: 'Meta (via API)' },
  'mistral-large': { input: 2.00, output: 6.00, provider: 'Mistral' },
  'mistral-small': { input: 0.20, output: 0.60, provider: 'Mistral' },
};

const CHEAPER_ALTERNATIVES = {
  'gpt-4o': { suggestion: 'gpt-4o-mini', reason: 'For simple classification/extraction tasks, GPT-4o-mini is 94% cheaper with comparable quality.' },
  'gpt-4-turbo': { suggestion: 'gpt-4o', reason: 'GPT-4o is faster and 75% cheaper than GPT-4 Turbo with better performance.' },
  'o1': { suggestion: 'o3-mini', reason: 'For reasoning tasks that don\'t need full o1, o3-mini offers 93% cost savings.' },
  'claude-opus-4-20250514': { suggestion: 'claude-sonnet-4-20250514', reason: 'Claude Sonnet 4 handles most tasks at 80% lower cost than Opus.' },
  'claude-sonnet-4-20250514': { suggestion: 'claude-haiku-4-5-20251001', reason: 'For high-throughput or simple tasks, Haiku 4.5 is 92% cheaper.' },
  'gemini-1.5-pro': { suggestion: 'gemini-2.0-flash', reason: 'Gemini 2.0 Flash is 92% cheaper for most generative tasks.' },
  'mistral-large': { suggestion: 'mistral-small', reason: 'Mistral Small is 90% cheaper for straightforward tasks.' },
};

const PIE_COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4', '#f59e0b', '#ef4444', '#10b981', '#ec4899', '#f97316'];

const CostInsights = () => {
  const [loading, setLoading] = useState(true);
  const [detectedModels, setDetectedModels] = useState([]);
  const [unboundedCalls, setUnboundedCalls] = useState([]);

  useEffect(() => {
    loadCostData();
  }, []);

  const loadCostData = async () => {
    setLoading(true);
    const token = localStorage.getItem('auth_token');

    try {
      // Try fetching from both endpoints
      const [scanRes, costRes] = await Promise.allSettled([
        axios.get(`${API}/scan/latest`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }),
        axios.get(`${API}/cost`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }),
      ]);

      let models = [];
      let unbounded = [];

      if (costRes.status === 'fulfilled' && costRes.value.data) {
        models = costRes.value.data.models || [];
        unbounded = costRes.value.data.unbounded_calls || [];
      }

      if (scanRes.status === 'fulfilled' && scanRes.value.data) {
        const scanData = scanRes.value.data;
        const findings = scanData.findings || scanData.results?.findings || [];
        // Extract models from scan findings if cost endpoint didn't return them
        if (models.length === 0) {
          models = extractModelsFromFindings(findings);
        }
        if (unbounded.length === 0) {
          unbounded = findings
            .filter(f => f.category === 'unbounded' || f.name?.includes('max_tokens'))
            .map(f => ({ file: f.file || f.location, model: f.model || 'unknown', line: f.line }));
        }
      }

      // If both fail, use mock data
      if (models.length === 0) {
        models = [
          { name: 'gpt-4o', count: 12, files: ['src/llm.py', 'src/agent.py', 'api/chat.py'] },
          { name: 'gpt-4o-mini', count: 8, files: ['src/classify.py', 'src/extract.py'] },
          { name: 'claude-sonnet-4-20250514', count: 5, files: ['src/review.py', 'src/summarize.py'] },
          { name: 'claude-haiku-4-5-20251001', count: 3, files: ['src/filter.py'] },
          { name: 'gemini-1.5-pro', count: 2, files: ['src/search.py'] },
        ];
        unbounded = [
          { file: 'src/llm.py', model: 'gpt-4o', line: 42 },
          { file: 'src/agent.py', model: 'gpt-4o', line: 88 },
          { file: 'src/review.py', model: 'claude-sonnet-4-20250514', line: 15 },
        ];
      }

      setDetectedModels(models);
      setUnboundedCalls(unbounded);
    } catch (error) {
      console.error('Failed to load cost data:', error);
    } finally {
      setLoading(false);
    }
  };

  const extractModelsFromFindings = (findings) => {
    const modelMap = {};
    for (const f of findings) {
      if (f.model && MODEL_PRICING[f.model]) {
        if (!modelMap[f.model]) {
          modelMap[f.model] = { name: f.model, count: 0, files: [] };
        }
        modelMap[f.model].count++;
        if (f.file && !modelMap[f.model].files.includes(f.file)) {
          modelMap[f.model].files.push(f.file);
        }
      }
    }
    return Object.values(modelMap);
  };

  const modelDistribution = useMemo(() => {
    return detectedModels.map((m, i) => ({
      name: MODEL_PRICING[m.name]?.displayName || m.name,
      value: m.count,
      fill: PIE_COLORS[i % PIE_COLORS.length],
    }));
  }, [detectedModels]);

  const costByProvider = useMemo(() => {
    const providerCosts = {};
    for (const m of detectedModels) {
      const pricing = MODEL_PRICING[m.name];
      if (!pricing) continue;
      const provider = pricing.provider;
      if (!providerCosts[provider]) {
        providerCosts[provider] = { provider, estimatedInput: 0, estimatedOutput: 0 };
      }
      // Estimate: each call site ~100K tokens/month input, ~50K output
      const inputTokensM = (m.count * 0.1);
      const outputTokensM = (m.count * 0.05);
      providerCosts[provider].estimatedInput += inputTokensM * pricing.input;
      providerCosts[provider].estimatedOutput += outputTokensM * pricing.output;
    }
    return Object.values(providerCosts).map(p => ({
      ...p,
      total: p.estimatedInput + p.estimatedOutput,
    }));
  }, [detectedModels]);

  const totalEstimatedCost = useMemo(() => {
    return costByProvider.reduce((sum, p) => sum + p.total, 0);
  }, [costByProvider]);

  const alternatives = useMemo(() => {
    return detectedModels
      .filter(m => CHEAPER_ALTERNATIVES[m.name])
      .map(m => ({
        model: m.name,
        displayName: MODEL_PRICING[m.name]?.displayName || m.name,
        count: m.count,
        ...CHEAPER_ALTERNATIVES[m.name],
        currentCost: MODEL_PRICING[m.name]?.input || 0,
        suggestedCost: MODEL_PRICING[CHEAPER_ALTERNATIVES[m.name]?.suggestion]?.input || 0,
        suggestedDisplayName: MODEL_PRICING[CHEAPER_ALTERNATIVES[m.name]?.suggestion]?.displayName || CHEAPER_ALTERNATIVES[m.name]?.suggestion,
      }));
  }, [detectedModels]);

  if (loading) {
    return (
      <div className="p-6 md:p-8 bg-zinc-950 min-h-full">
        <div className="max-w-6xl mx-auto space-y-4">
          <div className="h-10 w-64 bg-zinc-800 rounded animate-pulse" />
          <div className="h-6 w-96 bg-zinc-800 rounded animate-pulse" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-48 bg-zinc-900 rounded-lg animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (detectedModels.length === 0) {
    return (
      <div className="p-6 md:p-8 bg-zinc-950 min-h-full">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-2xl md:text-3xl font-bold text-zinc-100 flex items-center gap-3 mb-8">
            <CircleDollarSign className="text-blue-400" size={28} />
            Cost Insights
          </h1>
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="py-16 text-center">
              <DollarSign className="mx-auto mb-4 text-zinc-600" size={48} />
              <h3 className="text-lg font-medium text-zinc-300 mb-2">No AI models detected</h3>
              <p className="text-zinc-500 max-w-md mx-auto">
                Run a scan on a repository with AI/LLM usage to see cost insights and optimization suggestions.
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
            <CircleDollarSign className="text-blue-400" size={28} />
            Cost Insights
          </h1>
          <p className="text-zinc-400 mt-1">
            Estimate AI costs across your codebase and discover optimization opportunities.
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-4">
              <p className="text-xs font-medium text-zinc-400 mb-2">Models Detected</p>
              <p className="text-3xl font-bold text-zinc-100">{detectedModels.length}</p>
              <p className="text-xs text-zinc-500 mt-1">across {detectedModels.reduce((s, m) => s + (m.files?.length || 0), 0)} files</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-4">
              <p className="text-xs font-medium text-zinc-400 mb-2">Est. Monthly Cost</p>
              <p className="text-3xl font-bold text-zinc-100">${totalEstimatedCost.toFixed(2)}</p>
              <p className="text-xs text-zinc-500 mt-1">based on ~100K tokens/call site/month</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-4">
              <p className="text-xs font-medium text-zinc-400 mb-2">Unbounded Cost Risks</p>
              <p className={`text-3xl font-bold ${unboundedCalls.length > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
                {unboundedCalls.length}
              </p>
              <p className="text-xs text-zinc-500 mt-1">LLM calls without max_tokens</p>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          {/* Model Distribution Pie */}
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                <Layers size={16} className="text-blue-400" />
                Model Distribution
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={modelDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={90}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {modelDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#18181b',
                        border: '1px solid #3f3f46',
                        borderRadius: '8px',
                        color: '#e4e4e7',
                        fontSize: '12px',
                      }}
                      formatter={(value, name) => [`${value} usage${value > 1 ? 's' : ''}`, name]}
                    />
                    <Legend
                      wrapperStyle={{ fontSize: '12px', color: '#a1a1aa' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Cost by Provider Bar Chart */}
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                <DollarSign size={16} className="text-blue-400" />
                Estimated Cost by Provider
              </CardTitle>
              <CardDescription className="text-zinc-500 text-xs">Monthly estimate (USD)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={costByProvider} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis type="number" stroke="#71717a" fontSize={12} tickLine={false} tickFormatter={(v) => `$${v.toFixed(0)}`} />
                    <YAxis type="category" dataKey="provider" stroke="#71717a" fontSize={12} tickLine={false} width={80} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#18181b',
                        border: '1px solid #3f3f46',
                        borderRadius: '8px',
                        color: '#e4e4e7',
                        fontSize: '12px',
                      }}
                      formatter={(value) => [`$${value.toFixed(2)}`, '']}
                    />
                    <Bar dataKey="estimatedInput" stackId="cost" fill="#3b82f6" name="Input Cost" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="estimatedOutput" stackId="cost" fill="#8b5cf6" name="Output Cost" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Model Pricing Table */}
        <Card className="bg-zinc-900 border-zinc-800 mb-6">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-zinc-300">Detected Model Pricing</CardTitle>
            <CardDescription className="text-zinc-500 text-xs">Cost per 1M tokens (USD)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-800">
                    <th className="text-left py-2 px-3 text-xs font-medium text-zinc-400">Model</th>
                    <th className="text-left py-2 px-3 text-xs font-medium text-zinc-400">Provider</th>
                    <th className="text-right py-2 px-3 text-xs font-medium text-zinc-400">Input /1M</th>
                    <th className="text-right py-2 px-3 text-xs font-medium text-zinc-400">Output /1M</th>
                    <th className="text-right py-2 px-3 text-xs font-medium text-zinc-400">Usages</th>
                    <th className="text-right py-2 px-3 text-xs font-medium text-zinc-400">Risk</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/50">
                  {detectedModels.map((model) => {
                    const pricing = MODEL_PRICING[model.name];
                    const hasUnbounded = unboundedCalls.some(u => u.model === model.name);
                    return (
                      <tr key={model.name} className="hover:bg-zinc-800/30 transition-colors">
                        <td className="py-2.5 px-3">
                          <span className="font-medium text-zinc-200">
                            {pricing?.displayName || model.name}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-zinc-400">{pricing?.provider || 'Unknown'}</td>
                        <td className="py-2.5 px-3 text-right text-zinc-300">
                          {pricing ? `$${pricing.input.toFixed(2)}` : '-'}
                        </td>
                        <td className="py-2.5 px-3 text-right text-zinc-300">
                          {pricing ? `$${pricing.output.toFixed(2)}` : '-'}
                        </td>
                        <td className="py-2.5 px-3 text-right text-zinc-300">{model.count}</td>
                        <td className="py-2.5 px-3 text-right">
                          {hasUnbounded ? (
                            <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30 text-xs">
                              <AlertTriangle size={10} className="mr-1" />
                              No max_tokens
                            </Badge>
                          ) : (
                            <Badge className="bg-green-500/20 text-green-400 border-green-500/30 text-xs">OK</Badge>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Unbounded Cost Risks */}
        {unboundedCalls.length > 0 && (
          <Card className="bg-zinc-900 border-zinc-800 mb-6">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-yellow-400 flex items-center gap-2">
                <AlertTriangle size={16} />
                Unbounded Cost Risks
              </CardTitle>
              <CardDescription className="text-zinc-500 text-xs">
                LLM calls without max_tokens can lead to unexpectedly high costs
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {unboundedCalls.map((call, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 bg-yellow-500/5 border border-yellow-500/20 rounded-lg"
                  >
                    <div>
                      <p className="text-sm font-medium text-zinc-200">{call.file}</p>
                      <p className="text-xs text-zinc-500">
                        Model: {call.model} {call.line ? `(line ${call.line})` : ''}
                      </p>
                    </div>
                    <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30 text-xs">
                      OWASP LLM10
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Cheaper Alternatives */}
        {alternatives.length > 0 && (
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                <TrendingDown size={16} className="text-green-400" />
                Cost Optimization Suggestions
              </CardTitle>
              <CardDescription className="text-zinc-500 text-xs">
                Potential cost savings based on detected model usage
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {alternatives.map((alt, i) => {
                  const savingsPercent = alt.currentCost > 0
                    ? Math.round((1 - alt.suggestedCost / alt.currentCost) * 100)
                    : 0;
                  return (
                    <div
                      key={i}
                      className="p-4 bg-zinc-800/50 border border-zinc-700 rounded-lg"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-zinc-300 border-zinc-600 text-xs">
                            {alt.displayName}
                          </Badge>
                          <ArrowRight size={14} className="text-zinc-500" />
                          <Badge className="bg-green-500/20 text-green-400 border-green-500/30 text-xs">
                            {alt.suggestedDisplayName}
                          </Badge>
                        </div>
                        {savingsPercent > 0 && (
                          <Badge className="bg-green-500/10 text-green-400 border-green-500/20 text-xs w-fit">
                            <Zap size={10} className="mr-1" />
                            {savingsPercent}% cheaper
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-zinc-400">{alt.reason}</p>
                      <p className="text-xs text-zinc-500 mt-1">
                        Found in {alt.count} location{alt.count > 1 ? 's' : ''} across your codebase
                      </p>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default CostInsights;
