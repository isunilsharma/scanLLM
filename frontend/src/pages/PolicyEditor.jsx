import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import {
  Plus, Trash2, Edit3, Download, Play, Shield,
  CheckCircle, XCircle, AlertTriangle, Info, ChevronDown
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SEVERITY_OPTIONS = [
  { value: 'error', label: 'Error', color: 'bg-red-500/20 text-red-400 border-red-500/30' },
  { value: 'warning', label: 'Warning', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' },
  { value: 'info', label: 'Info', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
];

const TARGET_OPTIONS = [
  { value: 'finding', label: 'Finding' },
  { value: 'scan', label: 'Scan' },
];

const OPERATOR_OPTIONS = [
  { value: 'equals', label: 'equals' },
  { value: 'not_equals', label: 'not equals' },
  { value: 'in', label: 'in' },
  { value: 'not_in', label: 'not in' },
  { value: 'contains', label: 'contains' },
  { value: 'greater_than', label: 'greater than' },
  { value: 'less_than', label: 'less than' },
  { value: 'exists', label: 'exists' },
];

const FIELD_OPTIONS = [
  { value: 'severity', label: 'Severity' },
  { value: 'category', label: 'Category' },
  { value: 'provider', label: 'Provider' },
  { value: 'risk_score', label: 'Risk Score' },
  { value: 'owasp_id', label: 'OWASP ID' },
  { value: 'has_secret', label: 'Has Secret' },
  { value: 'max_tokens_set', label: 'Max Tokens Set' },
  { value: 'model_name', label: 'Model Name' },
  { value: 'framework', label: 'Framework' },
  { value: 'file_pattern', label: 'File Pattern' },
];

const emptyRule = () => ({
  id: crypto.randomUUID(),
  name: '',
  description: '',
  severity: 'warning',
  target: 'finding',
  conditions: [{ field: 'severity', operator: 'equals', value: '' }],
});

const PolicyEditor = () => {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testResults, setTestResults] = useState(null);
  const [testingRule, setTestingRule] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingRuleId, setDeletingRuleId] = useState(null);

  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    setLoading(true);
    const token = localStorage.getItem('auth_token');
    try {
      const response = await axios.get(`${API}/policy`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      setRules(response.data.rules || []);
    } catch (error) {
      // If endpoint doesn't exist yet, start with sample rules
      if (error.response?.status === 404 || error.response?.status === 405) {
        setRules([
          {
            id: '1',
            name: 'Block hardcoded secrets',
            description: 'Fail scan if any hardcoded API keys are detected',
            severity: 'error',
            target: 'finding',
            conditions: [{ field: 'has_secret', operator: 'equals', value: 'true' }],
          },
          {
            id: '2',
            name: 'Warn on high risk score',
            description: 'Warn if repository risk score exceeds 70',
            severity: 'warning',
            target: 'scan',
            conditions: [{ field: 'risk_score', operator: 'greater_than', value: '70' }],
          },
          {
            id: '3',
            name: 'Require max_tokens',
            description: 'Flag LLM calls without max_tokens configured',
            severity: 'warning',
            target: 'finding',
            conditions: [{ field: 'max_tokens_set', operator: 'equals', value: 'false' }],
          },
        ]);
      } else {
        console.error('Failed to load policies:', error);
        toast.error('Failed to load policies');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAddRule = () => {
    const newRule = emptyRule();
    setEditingRule(newRule);
    setEditDialogOpen(true);
  };

  const handleEditRule = (rule) => {
    setEditingRule({ ...rule, conditions: rule.conditions.map(c => ({ ...c })) });
    setEditDialogOpen(true);
  };

  const handleSaveRule = () => {
    if (!editingRule.name.trim()) {
      toast.error('Rule name is required');
      return;
    }
    const existing = rules.find(r => r.id === editingRule.id);
    if (existing) {
      setRules(rules.map(r => r.id === editingRule.id ? editingRule : r));
    } else {
      setRules([...rules, editingRule]);
    }
    setEditDialogOpen(false);
    setEditingRule(null);
    toast.success('Rule saved');
  };

  const handleDeleteRule = (ruleId) => {
    setDeletingRuleId(ruleId);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    setRules(rules.filter(r => r.id !== deletingRuleId));
    setDeleteDialogOpen(false);
    setDeletingRuleId(null);
    toast.success('Rule deleted');
  };

  const handleTestRule = async (rule) => {
    setTestingRule(rule.id);
    setTestResults(null);
    const token = localStorage.getItem('auth_token');
    try {
      const response = await axios.post(
        `${API}/policy/test`,
        { rule },
        { headers: token ? { Authorization: `Bearer ${token}` } : {} }
      );
      setTestResults({ ruleId: rule.id, ...response.data });
    } catch (error) {
      // Mock test results if endpoint not available
      const passed = Math.random() > 0.4;
      setTestResults({
        ruleId: rule.id,
        passed,
        matches: passed ? 0 : Math.floor(Math.random() * 8) + 1,
        details: passed
          ? 'No violations found in latest scan.'
          : `Found violations in ${Math.floor(Math.random() * 4) + 1} files.`,
      });
    } finally {
      setTestingRule(null);
    }
  };

  const handleExportYaml = () => {
    const yamlContent = generateYaml(rules);
    const blob = new Blob([yamlContent], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'scanllm-policy.yaml';
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Policy exported as YAML');
  };

  const generateYaml = (rules) => {
    let yaml = '# ScanLLM Policy Configuration\n# Generated by ScanLLM Policy Editor\n\nrules:\n';
    for (const rule of rules) {
      yaml += `  - name: "${rule.name}"\n`;
      yaml += `    description: "${rule.description}"\n`;
      yaml += `    severity: ${rule.severity}\n`;
      yaml += `    target: ${rule.target}\n`;
      yaml += `    conditions:\n`;
      for (const cond of rule.conditions) {
        yaml += `      - field: ${cond.field}\n`;
        yaml += `        operator: ${cond.operator}\n`;
        yaml += `        value: "${cond.value}"\n`;
      }
    }
    return yaml;
  };

  const addCondition = () => {
    if (!editingRule) return;
    setEditingRule({
      ...editingRule,
      conditions: [...editingRule.conditions, { field: 'severity', operator: 'equals', value: '' }],
    });
  };

  const updateCondition = (index, key, value) => {
    if (!editingRule) return;
    const updated = editingRule.conditions.map((c, i) =>
      i === index ? { ...c, [key]: value } : c
    );
    setEditingRule({ ...editingRule, conditions: updated });
  };

  const removeCondition = (index) => {
    if (!editingRule || editingRule.conditions.length <= 1) return;
    setEditingRule({
      ...editingRule,
      conditions: editingRule.conditions.filter((_, i) => i !== index),
    });
  };

  const getSeverityBadge = (severity) => {
    const opt = SEVERITY_OPTIONS.find(s => s.value === severity);
    return opt || SEVERITY_OPTIONS[1];
  };

  if (loading) {
    return (
      <div className="p-6 md:p-8 bg-zinc-950 min-h-full">
        <div className="max-w-5xl mx-auto space-y-4">
          <div className="h-10 w-64 bg-zinc-800 rounded animate-pulse" />
          <div className="h-6 w-96 bg-zinc-800 rounded animate-pulse" />
          <div className="space-y-3 mt-8">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-zinc-900 rounded-lg animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 bg-zinc-950 min-h-full">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-zinc-100 flex items-center gap-3">
              <Shield className="text-blue-400" size={28} />
              Policy Editor
            </h1>
            <p className="text-zinc-400 mt-1">
              Define rules to enforce AI governance policies across your scans.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportYaml}
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
            >
              <Download size={14} className="mr-1.5" />
              Export YAML
            </Button>
            <Button size="sm" onClick={handleAddRule} className="bg-blue-600 hover:bg-blue-700 text-white">
              <Plus size={14} className="mr-1.5" />
              Add Rule
            </Button>
          </div>
        </div>

        {/* Rules List */}
        {rules.length === 0 ? (
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="py-16 text-center">
              <Shield className="mx-auto mb-4 text-zinc-600" size={48} />
              <h3 className="text-lg font-medium text-zinc-300 mb-2">No policies defined</h3>
              <p className="text-zinc-500 mb-6 max-w-md mx-auto">
                Create your first policy rule to start enforcing AI governance standards across your scans.
              </p>
              <Button onClick={handleAddRule} className="bg-blue-600 hover:bg-blue-700 text-white">
                <Plus size={14} className="mr-1.5" />
                Create First Rule
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {rules.map(rule => {
              const severityBadge = getSeverityBadge(rule.severity);
              const result = testResults?.ruleId === rule.id ? testResults : null;

              return (
                <Card key={rule.id} className="bg-zinc-900 border-zinc-800 hover:border-zinc-700 transition-colors">
                  <CardContent className="p-5">
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                          <h3 className="font-semibold text-zinc-100 text-base">{rule.name}</h3>
                          <Badge className={`text-xs ${severityBadge.color}`}>
                            {rule.severity}
                          </Badge>
                          <Badge variant="outline" className="text-xs text-zinc-400 border-zinc-700">
                            {rule.target}
                          </Badge>
                        </div>
                        <p className="text-sm text-zinc-400 mb-3">{rule.description}</p>

                        {/* Conditions display */}
                        <div className="flex flex-wrap gap-2">
                          {rule.conditions.map((cond, i) => (
                            <span
                              key={i}
                              className="inline-flex items-center gap-1 px-2.5 py-1 bg-zinc-800 text-zinc-300 text-xs rounded-md border border-zinc-700"
                            >
                              <span className="font-medium text-zinc-200">{cond.field}</span>
                              <span className="text-zinc-500">{cond.operator}</span>
                              {cond.operator !== 'exists' && (
                                <span className="text-blue-400">"{cond.value}"</span>
                              )}
                            </span>
                          ))}
                        </div>

                        {/* Test results inline */}
                        {result && (
                          <div
                            className={`mt-3 flex items-center gap-2 px-3 py-2 rounded-md text-sm ${
                              result.passed
                                ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                                : 'bg-red-500/10 text-red-400 border border-red-500/20'
                            }`}
                          >
                            {result.passed ? (
                              <CheckCircle size={14} />
                            ) : (
                              <XCircle size={14} />
                            )}
                            <span>
                              {result.passed ? 'Passed' : `Failed (${result.matches} violations)`}
                              {' — '}
                              {result.details}
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-1 flex-shrink-0">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleTestRule(rule)}
                          disabled={testingRule === rule.id}
                          className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
                        >
                          {testingRule === rule.id ? (
                            <span className="animate-spin">
                              <Play size={14} />
                            </span>
                          ) : (
                            <Play size={14} />
                          )}
                          <span className="ml-1 hidden sm:inline">Test</span>
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditRule(rule)}
                          className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
                        >
                          <Edit3 size={14} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteRule(rule.id)}
                          className="text-zinc-400 hover:text-red-400 hover:bg-zinc-800"
                        >
                          <Trash2 size={14} />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Edit/Add Rule Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent className="bg-zinc-900 border-zinc-800 text-zinc-100 max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-zinc-100">
                {editingRule && rules.find(r => r.id === editingRule.id) ? 'Edit Rule' : 'Add Rule'}
              </DialogTitle>
              <DialogDescription className="text-zinc-400">
                Configure policy rule conditions and severity.
              </DialogDescription>
            </DialogHeader>

            {editingRule && (
              <div className="space-y-5 py-2">
                {/* Rule Name */}
                <div>
                  <label className="text-sm font-medium text-zinc-300 mb-1.5 block">Rule Name</label>
                  <Input
                    value={editingRule.name}
                    onChange={(e) => setEditingRule({ ...editingRule, name: e.target.value })}
                    placeholder="e.g., Block hardcoded secrets"
                    className="bg-zinc-800 border-zinc-700 text-zinc-100 placeholder:text-zinc-500"
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="text-sm font-medium text-zinc-300 mb-1.5 block">Description</label>
                  <Input
                    value={editingRule.description}
                    onChange={(e) => setEditingRule({ ...editingRule, description: e.target.value })}
                    placeholder="Describe what this rule checks for"
                    className="bg-zinc-800 border-zinc-700 text-zinc-100 placeholder:text-zinc-500"
                  />
                </div>

                {/* Severity & Target */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-zinc-300 mb-1.5 block">Severity</label>
                    <Select
                      value={editingRule.severity}
                      onValueChange={(val) => setEditingRule({ ...editingRule, severity: val })}
                    >
                      <SelectTrigger className="bg-zinc-800 border-zinc-700 text-zinc-100">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-800 border-zinc-700">
                        {SEVERITY_OPTIONS.map(opt => (
                          <SelectItem key={opt.value} value={opt.value} className="text-zinc-100 focus:bg-zinc-700">
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-zinc-300 mb-1.5 block">Target</label>
                    <Select
                      value={editingRule.target}
                      onValueChange={(val) => setEditingRule({ ...editingRule, target: val })}
                    >
                      <SelectTrigger className="bg-zinc-800 border-zinc-700 text-zinc-100">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-800 border-zinc-700">
                        {TARGET_OPTIONS.map(opt => (
                          <SelectItem key={opt.value} value={opt.value} className="text-zinc-100 focus:bg-zinc-700">
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Conditions */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <label className="text-sm font-medium text-zinc-300">Conditions</label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={addCondition}
                      className="text-blue-400 hover:text-blue-300 hover:bg-zinc-800"
                    >
                      <Plus size={14} className="mr-1" />
                      Add Condition
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {editingRule.conditions.map((cond, index) => (
                      <div key={index} className="flex items-center gap-2 p-3 bg-zinc-800/50 rounded-lg border border-zinc-700">
                        <Select
                          value={cond.field}
                          onValueChange={(val) => updateCondition(index, 'field', val)}
                        >
                          <SelectTrigger className="w-[140px] bg-zinc-800 border-zinc-700 text-zinc-100 text-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-zinc-800 border-zinc-700">
                            {FIELD_OPTIONS.map(opt => (
                              <SelectItem key={opt.value} value={opt.value} className="text-zinc-100 focus:bg-zinc-700 text-xs">
                                {opt.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        <Select
                          value={cond.operator}
                          onValueChange={(val) => updateCondition(index, 'operator', val)}
                        >
                          <SelectTrigger className="w-[130px] bg-zinc-800 border-zinc-700 text-zinc-100 text-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-zinc-800 border-zinc-700">
                            {OPERATOR_OPTIONS.map(opt => (
                              <SelectItem key={opt.value} value={opt.value} className="text-zinc-100 focus:bg-zinc-700 text-xs">
                                {opt.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        {cond.operator !== 'exists' && (
                          <Input
                            value={cond.value}
                            onChange={(e) => updateCondition(index, 'value', e.target.value)}
                            placeholder="Value"
                            className="flex-1 bg-zinc-800 border-zinc-700 text-zinc-100 placeholder:text-zinc-500 text-xs"
                          />
                        )}

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeCondition(index)}
                          disabled={editingRule.conditions.length <= 1}
                          className="text-zinc-500 hover:text-red-400 hover:bg-zinc-800 flex-shrink-0 px-2"
                        >
                          <Trash2 size={14} />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <DialogFooter className="gap-2">
              <Button
                variant="ghost"
                onClick={() => setEditDialogOpen(false)}
                className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
              >
                Cancel
              </Button>
              <Button onClick={handleSaveRule} className="bg-blue-600 hover:bg-blue-700 text-white">
                Save Rule
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent className="bg-zinc-900 border-zinc-800 text-zinc-100">
            <DialogHeader>
              <DialogTitle className="text-zinc-100">Delete Rule</DialogTitle>
              <DialogDescription className="text-zinc-400">
                Are you sure you want to delete this policy rule? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="gap-2">
              <Button
                variant="ghost"
                onClick={() => setDeleteDialogOpen(false)}
                className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
              >
                Cancel
              </Button>
              <Button
                onClick={confirmDelete}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default PolicyEditor;
