import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Switch } from '../components/ui/switch';
import { Separator } from '../components/ui/separator';
import { Skeleton } from '../components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { toast } from 'sonner';
import RiskScoreGauge from '../components/RiskScoreGauge';
import {
  GitBranch, Play, Clock, FileSearch, AlertTriangle,
  Shield, Download, CheckCircle, XCircle, Loader2,
  ChevronRight, ExternalLink, Eye
} from 'lucide-react';
import api from '../lib/api';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const STATUS_BADGE = {
  SUCCESS: { variant: 'default', icon: CheckCircle, className: 'bg-green-500/10 text-green-400 border-green-500/20' },
  FAILED: { variant: 'destructive', icon: XCircle, className: 'bg-red-500/10 text-red-400 border-red-500/20' },
  RUNNING: { variant: 'secondary', icon: Loader2, className: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  PENDING: { variant: 'secondary', icon: Clock, className: 'bg-zinc-800 text-zinc-300 border-zinc-700' },
};

const RepoDashboard = () => {
  const { owner, repo } = useParams();
  const navigate = useNavigate();
  const [branch, setBranch] = useState('main');
  const [fullScan, setFullScan] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [recentScans, setRecentScans] = useState([]);
  const [loadingScans, setLoadingScans] = useState(true);

  const loadRecentScans = async () => {
    setLoadingScans(true);
    const token = localStorage.getItem('auth_token');

    try {
      const response = await axios.get(`${API}/scans`, {
        params: {
          repo_full_name: `${owner}/${repo}`,
          limit: 6
        },
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      setRecentScans(response.data.scans || []);
    } catch (error) {
      console.error('Failed to load recent scans:', error);
    } finally {
      setLoadingScans(false);
    }
  };

  useEffect(() => {
    loadRecentScans();
  }, [owner, repo]);

  const handleRunScan = async () => {
    setIsScanning(true);
    const token = localStorage.getItem('auth_token');

    try {
      const response = await axios.post(
        `${API}/scan/github`,
        { owner, repo, branch, full_scan: fullScan },
        { headers: token ? { 'Authorization': `Bearer ${token}` } : {} }
      );
      navigate(`/app/repo/${owner}/${repo}/scan/${response.data.scan_id}`);
    } catch (error) {
      toast.error('Failed to start scan');
      setIsScanning(false);
    }
  };

  const handleDownloadLatestReport = async () => {
    const latestSuccess = recentScans.find((s) => s.status === 'SUCCESS');
    if (!latestSuccess) {
      toast.error('No successful scan found');
      return;
    }
    try {
      const response = await api.get(`/scans/${latestSuccess.id}/report/pdf`, {
        responseType: 'blob',
        timeout: 60000,
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scanllm-report-${latestSuccess.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Report downloaded');
    } catch {
      toast.error('Failed to download report');
    }
  };

  const latestScan = recentScans[0] || null;
  const latestRiskScore = latestScan?.risk_score ?? null;
  const latestOwaspData = latestScan?.owasp_summary ?? null;

  return (
    <div className="p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl md:text-3xl font-bold text-zinc-100">{owner}/{repo}</h1>
              <a
                href={`https://github.com/${owner}/${repo}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-500 hover:text-zinc-300 transition-colors"
              >
                <ExternalLink size={18} />
              </a>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="flex items-center gap-1">
                <GitBranch size={12} />
                {branch}
              </Badge>
              {latestRiskScore != null && (
                <Badge
                  variant={latestRiskScore <= 40 ? 'default' : latestRiskScore <= 60 ? 'secondary' : 'destructive'}
                  className="flex items-center gap-1"
                >
                  <Shield size={12} />
                  Risk: {Math.round(latestRiskScore)}
                </Badge>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            {recentScans.some((s) => s.status === 'SUCCESS') && (
              <Button variant="outline" size="sm" onClick={handleDownloadLatestReport}>
                <Download size={14} className="mr-1.5" />
                Latest Report
              </Button>
            )}
          </div>
        </div>

        {/* Top row: Risk Score + OWASP mini + Scan Config */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Risk Score Card */}
          <Card>
            <CardContent className="p-6 flex items-center justify-center min-h-[200px]">
              {loadingScans ? (
                <Skeleton className="h-32 w-32 rounded-full" />
              ) : latestRiskScore != null ? (
                <RiskScoreGauge score={latestRiskScore} compact={false} />
              ) : (
                <div className="text-center">
                  <Shield size={40} className="text-zinc-600 mx-auto mb-3" />
                  <p className="text-sm text-zinc-500">No risk data yet</p>
                  <p className="text-xs text-zinc-500">Run a scan to see your risk score</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* OWASP Mini Summary */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Shield size={16} className="text-zinc-500" />
                OWASP LLM Coverage
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loadingScans ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-6 w-full" />
                  ))}
                </div>
              ) : latestOwaspData ? (
                <div className="space-y-2">
                  {(latestOwaspData.categories || []).slice(0, 5).map((cat) => (
                    <div key={cat.id} className="flex items-center justify-between text-xs">
                      <span className="text-zinc-400">{cat.id}: {cat.name}</span>
                      {cat.status === 'detected' ? (
                        <XCircle size={14} className="text-red-500" />
                      ) : cat.status === 'partially' ? (
                        <AlertTriangle size={14} className="text-amber-500" />
                      ) : (
                        <CheckCircle size={14} className="text-green-500" />
                      )}
                    </div>
                  ))}
                  {(latestOwaspData.categories || []).length > 5 && (
                    <p className="text-[10px] text-zinc-500 pt-1">
                      +{(latestOwaspData.categories || []).length - 5} more categories
                    </p>
                  )}
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-sm text-zinc-500">No OWASP data</p>
                  <p className="text-xs text-zinc-500">Run a full scan to see coverage</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Scan Configuration */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Play size={16} className="text-zinc-500" />
                Run a Scan
              </CardTitle>
              <CardDescription>Configure and start a new scan</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs font-medium text-zinc-400 mb-1.5 block">Branch</label>
                <Input
                  type="text"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="main"
                  className="h-9"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label htmlFor="full-scan-switch" className="text-xs font-medium text-zinc-300 block">
                    Full Scan
                  </label>
                  <p className="text-[10px] text-zinc-500">Scan entire repository</p>
                </div>
                <Switch
                  id="full-scan-switch"
                  checked={fullScan}
                  onCheckedChange={setFullScan}
                />
              </div>

              <Button
                onClick={handleRunScan}
                disabled={isScanning}
                className="w-full"
              >
                {isScanning ? (
                  <>
                    <Loader2 size={14} className="mr-2 animate-spin" />
                    Starting scan...
                  </>
                ) : (
                  <>
                    <Play size={14} className="mr-2" />
                    Run Scan
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Recent Scans Table */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                <Clock size={16} className="text-zinc-500" />
                Recent Scans
              </CardTitle>
              {!loadingScans && recentScans.length > 0 && (
                <Badge variant="outline" className="text-xs">
                  {recentScans.length} scan{recentScans.length !== 1 ? 's' : ''}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {loadingScans ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <Skeleton key={i} className="h-14 w-full" />
                ))}
              </div>
            ) : recentScans.length === 0 ? (
              <div className="text-center py-8">
                <FileSearch size={40} className="text-zinc-600 mx-auto mb-3" />
                <p className="text-sm text-zinc-500 mb-1">No scans yet</p>
                <p className="text-xs text-zinc-500">Run your first scan to get started</p>
              </div>
            ) : (
              <div className="border border-zinc-800 rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-xs">Date</TableHead>
                      <TableHead className="text-xs">Status</TableHead>
                      <TableHead className="text-xs text-right">Matches</TableHead>
                      <TableHead className="text-xs text-right">Files</TableHead>
                      <TableHead className="text-xs text-right">Risk</TableHead>
                      <TableHead className="text-xs text-right w-20"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recentScans.map(scan => {
                      const statusInfo = STATUS_BADGE[scan.status] || STATUS_BADGE.PENDING;
                      const StatusIcon = statusInfo.icon;
                      return (
                        <TableRow
                          key={scan.id}
                          className="cursor-pointer hover:bg-zinc-800/30 transition-colors"
                          onClick={() => navigate(`/app/repo/${owner}/${repo}/scan/${scan.id}`)}
                        >
                          <TableCell className="text-xs text-zinc-400">
                            {new Date(scan.created_at).toLocaleString(undefined, {
                              month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                            })}
                          </TableCell>
                          <TableCell>
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full border ${statusInfo.className}`}>
                              <StatusIcon size={12} className={scan.status === 'RUNNING' ? 'animate-spin' : ''} />
                              {scan.status}
                            </span>
                          </TableCell>
                          <TableCell className="text-xs text-right font-medium text-zinc-300">
                            {scan.total_matches || 0}
                          </TableCell>
                          <TableCell className="text-xs text-right text-zinc-400">
                            {scan.files_count || 0}
                          </TableCell>
                          <TableCell className="text-xs text-right">
                            {scan.risk_score != null ? (
                              <Badge
                                variant={scan.risk_score <= 40 ? 'default' : scan.risk_score <= 60 ? 'secondary' : 'destructive'}
                                className="text-[10px]"
                              >
                                {Math.round(scan.risk_score)}
                              </Badge>
                            ) : (
                              <span className="text-zinc-500">--</span>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            <Button variant="ghost" size="sm" className="h-7 px-2">
                              <Eye size={14} className="text-zinc-500" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default RepoDashboard;
