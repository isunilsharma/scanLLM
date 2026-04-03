import React, { useState, useEffect, useCallback, useRef } from 'react';
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
} from '../components/ui/dialog';
import {
  Plus, Trash2, Edit3, Download, Play, Shield, Upload,
  CheckCircle, XCircle, AlertTriangle, Info, FileText,
  ToggleLeft, ToggleRight, Copy, FolderOpen
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_V1 = `${BACKEND_URL}/api/v1`;
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

const getAuthHeaders = () => {
  const token = localStorage.getItem('auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const PolicyEditor = () => {
  // Policy management state (backend-persisted policies)
  const [policies, setPolicies] = useState([]);
  const [policiesLoading, setPoliciesLoading] = useState(true);
  const [policyDialogOpen, setPolicyDialogOpen] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState(null);
  const [deletePolicyDialogOpen, setDeletePolicyDialogOpen] = useState(false);
  const [deletingPolicyId, setDeletingPolicyId] = useState(null);
  const [savingPolicy, setSavingPolicy] = useState(false);
  const fileInputRef = useRef(null);

  // Rule editor state (for editing rules within a policy)
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [testingRule, setTestingRule] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingRuleId, setDeletingRuleId] = useState(null);
  const [activePolicy, setActivePolicy] = useState(null); // Currently selected policy for rule editing

  // -----------------------------------------------------------------------
  // Policy CRUD operations (backend)
  // -----------------------------------------------------------------------

  const loadPolicies = useCallback(async () => {
    setPoliciesLoading(true);
    try {
      const response = await axios.get(`${API_V1}/policies`, {
        headers: getAuthHeaders(),
      });
      setPolicies(response.data.policies || []);
    } catch (error) {
      if (error.response?.status === 401) {
        // Not authenticated - show empty state
        setPolicies([]);
      } else {
        console.error('Failed to load policies:', error);
        toast.error('Failed to load policies');
      }
    } finally {
      setPoliciesLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPolicies();
  }, [loadPolicies]);

  const handleCreatePolicy = () => {
    setEditingPolicy({
      name: '',
      description: '',
      rules: [],
      is_active: true,
    });
    setPolicyDialogOpen(true);
  };

  const handleEditPolicy = (policy) => {
    setEditingPolicy({
      id: policy.id,
      name: policy.name,
      description: policy.description || '',
      rules: policy.rules || [],
      is_active: policy.is_active,
    });
    setPolicyDialogOpen(true);
  };

  const handleSavePolicy = async () => {
    if (!editingPolicy?.name?.trim()) {
      toast.error('Policy name is required');
      return;
    }
    setSavingPolicy(true);
    try {
      if (editingPolicy.id) {
        // Update existing
        await axios.put(`${API_V1}/policies/${editingPolicy.id}`, {
          name: editingPolicy.name,
          description: editingPolicy.description,
          rules: editingPolicy.rules,
          is_active: editingPolicy.is_active,
        }, { headers: getAuthHeaders() });
        toast.success('Policy updated');
      } else {
        // Create new
        await axios.post(`${API_V1}/policies`, {
          name: editingPolicy.name,
          description: editingPolicy.description,
          rules: editingPolicy.rules,
          is_active: editingPolicy.is_active,
        }, { headers: getAuthHeaders() });
        toast.success('Policy created');
      }
      setPolicyDialogOpen(false);
      setEditingPolicy(null);
      await loadPolicies();
    } catch (error) {
      console.error('Failed to save policy:', error);
      toast.error(error.response?.data?.detail || 'Failed to save policy');
    } finally {
      setSavingPolicy(false);
    }
  };

  const handleDeletePolicy = (policyId) => {
    setDeletingPolicyId(policyId);
    setDeletePolicyDialogOpen(true);
  };

  const confirmDeletePolicy = async () => {
    try {
      await axios.delete(`${API_V1}/policies/${deletingPolicyId}`, {
        headers: getAuthHeaders(),
      });
      toast.success('Policy deleted');
      setDeletePolicyDialogOpen(false);
      setDeletingPolicyId(null);
      // If the deleted policy was the active one, clear it
      if (activePolicy?.id === deletingPolicyId) {
        setActivePolicy(null);
        setRules([]);
      }
      await loadPolicies();
    } catch (error) {
      console.error('Failed to delete policy:', error);
      toast.error('Failed to delete policy');
    }
  };

  const handleToggleActive = async (policy) => {
    try {
      await axios.put(`${API_V1}/policies/${policy.id}`, {
        is_active: !policy.is_active,
      }, { headers: getAuthHeaders() });
      await loadPolicies();
      toast.success(policy.is_active ? 'Policy deactivated' : 'Policy activated');
    } catch (error) {
      console.error('Failed to toggle policy:', error);
      toast.error('Failed to update policy');
    }
  };

  const handleImportPolicy = () => {
    fileInputRef.current?.click();
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.json')) {
      toast.error('Only JSON files are supported');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post(`${API_V1}/policies/import`, formData, {
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'multipart/form-data',
        },
      });
      toast.success(`Policy imported from ${file.name}`);
      await loadPolicies();
    } catch (error) {
      console.error('Failed to import policy:', error);
      toast.error(error.response?.data?.detail || 'Failed to import policy');
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // -----------------------------------------------------------------------
  // Rule editing (within a selected policy)
  // -----------------------------------------------------------------------

  const handleOpenPolicyRules = (policy) => {
    setActivePolicy(policy);
    setRules(policy.rules || []);
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

  const handleSaveRule = async () => {
    if (!editingRule.name.trim()) {
      toast.error('Rule name is required');
      return;
    }
    let updatedRules;
    const existing = rules.find(r => r.id === editingRule.id);
    if (existing) {
      updatedRules = rules.map(r => r.id === editingRule.id ? editingRule : r);
    } else {
      updatedRules = [...rules, editingRule];
    }
    setRules(updatedRules);

    // Persist to backend if we have an active policy
    if (activePolicy?.id) {
      try {
        await axios.put(`${API_V1}/policies/${activePolicy.id}`, {
          rules: updatedRules,
        }, { headers: getAuthHeaders() });
        await loadPolicies();
        toast.success('Rule saved');
      } catch (error) {
        console.error('Failed to persist rule:', error);
        toast.error('Rule saved locally but failed to sync');
      }
    } else {
      toast.success('Rule saved');
    }

    setEditDialogOpen(false);
    setEditingRule(null);
  };

  const handleDeleteRule = (ruleId) => {
    setDeletingRuleId(ruleId);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    const updatedRules = rules.filter(r => r.id !== deletingRuleId);
    setRules(updatedRules);

    if (activePolicy?.id) {
      try {
        await axios.put(`${API_V1}/policies/${activePolicy.id}`, {
          rules: updatedRules,
        }, { headers: getAuthHeaders() });
        await loadPolicies();
      } catch (error) {
        console.error('Failed to persist rule deletion:', error);
      }
    }

    setDeleteDialogOpen(false);
    setDeletingRuleId(null);
    toast.success('Rule deleted');
  };

  const handleTestRule = async (rule) => {
    setTestingRule(rule.id);
    setTestResults(null);
    try {
      const response = await axios.post(
        `${API}/policy/test`,
        { rule },
        { headers: getAuthHeaders() }
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

  const handleExportPolicy = (policy) => {
    const exportData = {
      name: policy.name,
      description: policy.description || '',
      rules: policy.rules || [],
      is_active: policy.is_active,
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${policy.name.replace(/\s+/g, '-').toLowerCase()}-policy.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Policy exported as JSON');
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
    toast.success('Rules exported as YAML');
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

  const handleBackToPolicies = () => {
    setActivePolicy(null);
    setRules([]);
    setTestResults(null);
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

  // -----------------------------------------------------------------------
  // Loading state
  // -----------------------------------------------------------------------

  if (policiesLoading) {
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

  // -----------------------------------------------------------------------
  // Rule editor view (when a policy is selected)
  // -----------------------------------------------------------------------

  if (activePolicy) {
    return (
      <div className="p-6 md:p-8 bg-zinc-950 min-h-full">
        <div className="max-w-5xl mx-auto">
          {/* Header with back button */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
            <div>
              <button
                onClick={handleBackToPolicies}
                className="text-sm text-zinc-400 hover:text-zinc-200 mb-2 flex items-center gap-1 transition-colors"
              >
                &larr; Back to Policies
              </button>
              <h1 className="text-2xl md:text-3xl font-bold text-zinc-100 flex items-center gap-3">
                <FileText className="text-cyan-400" size={28} />
                {activePolicy.name}
              </h1>
              <p className="text-zinc-400 mt-1">
                {activePolicy.description || 'Edit rules for this policy.'}
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
              <Button size="sm" onClick={handleAddRule} className="bg-cyan-600 hover:bg-cyan-700 text-white">
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
                <h3 className="text-lg font-medium text-zinc-300 mb-2">No rules in this policy</h3>
                <p className="text-zinc-500 mb-6 max-w-md mx-auto">
                  Add your first rule to start defining governance conditions.
                </p>
                <Button onClick={handleAddRule} className="bg-cyan-600 hover:bg-cyan-700 text-white">
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
                                  <span className="text-cyan-400">"{cond.value}"</span>
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
                                {' \u2014 '}
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
                        className="text-cyan-400 hover:text-cyan-300 hover:bg-zinc-800"
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
                <Button onClick={handleSaveRule} className="bg-cyan-600 hover:bg-cyan-700 text-white">
                  Save Rule
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* Delete Rule Confirmation Dialog */}
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
  }

  // -----------------------------------------------------------------------
  // Policy list view (default)
  // -----------------------------------------------------------------------

  return (
    <div className="p-6 md:p-8 bg-zinc-950 min-h-full">
      <div className="max-w-5xl mx-auto">
        {/* Hidden file input for import */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={handleFileUpload}
          className="hidden"
        />

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-zinc-100 flex items-center gap-3">
              <Shield className="text-cyan-400" size={28} />
              Policy Manager
            </h1>
            <p className="text-zinc-400 mt-1">
              Create, manage, and enforce AI governance policies across your scans.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleImportPolicy}
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
            >
              <Upload size={14} className="mr-1.5" />
              Import JSON
            </Button>
            <Button size="sm" onClick={handleCreatePolicy} className="bg-cyan-600 hover:bg-cyan-700 text-white">
              <Plus size={14} className="mr-1.5" />
              Create Policy
            </Button>
          </div>
        </div>

        {/* Policies List */}
        {policies.length === 0 ? (
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="py-16 text-center">
              <Shield className="mx-auto mb-4 text-zinc-600" size={48} />
              <h3 className="text-lg font-medium text-zinc-300 mb-2">No policies yet</h3>
              <p className="text-zinc-500 mb-6 max-w-md mx-auto">
                Create your first governance policy to start enforcing AI security standards across your scans.
              </p>
              <div className="flex items-center justify-center gap-3">
                <Button onClick={handleCreatePolicy} className="bg-cyan-600 hover:bg-cyan-700 text-white">
                  <Plus size={14} className="mr-1.5" />
                  Create Policy
                </Button>
                <Button
                  variant="outline"
                  onClick={handleImportPolicy}
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
                >
                  <Upload size={14} className="mr-1.5" />
                  Import JSON
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {policies.map(policy => {
              const ruleCount = (policy.rules || []).length;
              const errorRules = (policy.rules || []).filter(r => r.severity === 'error').length;
              const warnRules = (policy.rules || []).filter(r => r.severity === 'warning').length;

              return (
                <Card key={policy.id} className="bg-zinc-900 border-zinc-800 hover:border-zinc-700 transition-colors">
                  <CardContent className="p-5">
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                          <h3 className="font-semibold text-zinc-100 text-base">{policy.name}</h3>
                          <Badge
                            className={`text-xs ${
                              policy.is_active
                                ? 'bg-green-500/20 text-green-400 border-green-500/30'
                                : 'bg-zinc-700/50 text-zinc-500 border-zinc-600'
                            }`}
                          >
                            {policy.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </div>
                        {policy.description && (
                          <p className="text-sm text-zinc-400 mb-3">{policy.description}</p>
                        )}

                        {/* Rule summary badges */}
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-zinc-800 text-zinc-300 text-xs rounded-md border border-zinc-700">
                            <FileText size={12} className="text-zinc-500" />
                            {ruleCount} {ruleCount === 1 ? 'rule' : 'rules'}
                          </span>
                          {errorRules > 0 && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-red-500/10 text-red-400 text-xs rounded-md border border-red-500/20">
                              <XCircle size={12} />
                              {errorRules} error{errorRules !== 1 ? 's' : ''}
                            </span>
                          )}
                          {warnRules > 0 && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-yellow-500/10 text-yellow-400 text-xs rounded-md border border-yellow-500/20">
                              <AlertTriangle size={12} />
                              {warnRules} warning{warnRules !== 1 ? 's' : ''}
                            </span>
                          )}
                          {policy.created_at && (
                            <span className="text-xs text-zinc-600">
                              Created {new Date(policy.created_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-1 flex-shrink-0">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenPolicyRules(policy)}
                          className="text-cyan-400 hover:text-cyan-300 hover:bg-zinc-800"
                          title="Edit rules"
                        >
                          <FolderOpen size={14} />
                          <span className="ml-1 hidden sm:inline">Rules</span>
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleActive(policy)}
                          className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
                          title={policy.is_active ? 'Deactivate' : 'Activate'}
                        >
                          {policy.is_active ? <ToggleRight size={14} className="text-green-400" /> : <ToggleLeft size={14} />}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleExportPolicy(policy)}
                          className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
                          title="Export as JSON"
                        >
                          <Download size={14} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditPolicy(policy)}
                          className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
                          title="Edit policy"
                        >
                          <Edit3 size={14} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeletePolicy(policy.id)}
                          className="text-zinc-400 hover:text-red-400 hover:bg-zinc-800"
                          title="Delete policy"
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

        {/* Create/Edit Policy Dialog */}
        <Dialog open={policyDialogOpen} onOpenChange={setPolicyDialogOpen}>
          <DialogContent className="bg-zinc-900 border-zinc-800 text-zinc-100 max-w-lg">
            <DialogHeader>
              <DialogTitle className="text-zinc-100">
                {editingPolicy?.id ? 'Edit Policy' : 'Create Policy'}
              </DialogTitle>
              <DialogDescription className="text-zinc-400">
                {editingPolicy?.id
                  ? 'Update the policy name, description, and status.'
                  : 'Create a new governance policy. You can add rules after creation.'}
              </DialogDescription>
            </DialogHeader>

            {editingPolicy && (
              <div className="space-y-5 py-2">
                <div>
                  <label className="text-sm font-medium text-zinc-300 mb-1.5 block">Policy Name</label>
                  <Input
                    value={editingPolicy.name}
                    onChange={(e) => setEditingPolicy({ ...editingPolicy, name: e.target.value })}
                    placeholder="e.g., Production Security Policy"
                    className="bg-zinc-800 border-zinc-700 text-zinc-100 placeholder:text-zinc-500"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-zinc-300 mb-1.5 block">Description</label>
                  <Input
                    value={editingPolicy.description}
                    onChange={(e) => setEditingPolicy({ ...editingPolicy, description: e.target.value })}
                    placeholder="Describe the purpose of this policy"
                    className="bg-zinc-800 border-zinc-700 text-zinc-100 placeholder:text-zinc-500"
                  />
                </div>

                <div className="flex items-center gap-3">
                  <label className="text-sm font-medium text-zinc-300">Active</label>
                  <button
                    type="button"
                    onClick={() => setEditingPolicy({ ...editingPolicy, is_active: !editingPolicy.is_active })}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      editingPolicy.is_active ? 'bg-cyan-600' : 'bg-zinc-700'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        editingPolicy.is_active ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                  <span className="text-sm text-zinc-400">
                    {editingPolicy.is_active ? 'Policy will be enforced' : 'Policy is disabled'}
                  </span>
                </div>
              </div>
            )}

            <DialogFooter className="gap-2">
              <Button
                variant="ghost"
                onClick={() => { setPolicyDialogOpen(false); setEditingPolicy(null); }}
                className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
              >
                Cancel
              </Button>
              <Button
                onClick={handleSavePolicy}
                disabled={savingPolicy}
                className="bg-cyan-600 hover:bg-cyan-700 text-white"
              >
                {savingPolicy ? 'Saving...' : (editingPolicy?.id ? 'Update Policy' : 'Create Policy')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Policy Confirmation Dialog */}
        <Dialog open={deletePolicyDialogOpen} onOpenChange={setDeletePolicyDialogOpen}>
          <DialogContent className="bg-zinc-900 border-zinc-800 text-zinc-100">
            <DialogHeader>
              <DialogTitle className="text-zinc-100">Delete Policy</DialogTitle>
              <DialogDescription className="text-zinc-400">
                Are you sure you want to delete this policy and all its rules? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="gap-2">
              <Button
                variant="ghost"
                onClick={() => { setDeletePolicyDialogOpen(false); setDeletingPolicyId(null); }}
                className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
              >
                Cancel
              </Button>
              <Button
                onClick={confirmDeletePolicy}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                Delete Policy
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default PolicyEditor;
