import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { FileText, FileJson, FileCode, Download, Loader2, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import api from '../lib/api';

const REPORT_TYPES = [
  {
    id: 'pdf',
    label: 'PDF Report',
    description: 'Executive summary with risk scores, OWASP mapping, and remediation guidance.',
    icon: FileText,
    endpoint: (scanId) => `/scans/${scanId}/report/pdf`,
    filename: (scanId) => `scanllm-report-${scanId}.pdf`,
    contentType: 'application/pdf',
    color: '#ef4444',
    bgColor: 'rgba(239, 68, 68, 0.1)',
  },
  {
    id: 'aibom-json',
    label: 'AI-BOM (JSON)',
    description: 'CycloneDX Machine Learning Bill of Materials in JSON format.',
    icon: FileJson,
    endpoint: (scanId) => `/scans/${scanId}/report/aibom`,
    filename: (scanId) => `scanllm-aibom-${scanId}.json`,
    contentType: 'application/json',
    color: '#3b82f6',
    bgColor: 'rgba(59, 130, 246, 0.1)',
  },
  {
    id: 'aibom-xml',
    label: 'AI-BOM (XML)',
    description: 'CycloneDX Machine Learning Bill of Materials in XML format.',
    icon: FileCode,
    endpoint: (scanId) => `/scans/${scanId}/report/aibom.xml`,
    filename: (scanId) => `scanllm-aibom-${scanId}.xml`,
    contentType: 'application/xml',
    color: '#8b5cf6',
    bgColor: 'rgba(139, 92, 246, 0.1)',
  },
];

const ReportDownloads = ({ scanId }) => {
  const [loadingStates, setLoadingStates] = useState({});
  const [completedStates, setCompletedStates] = useState({});

  const handleDownload = async (report) => {
    if (!scanId) {
      toast.error('No scan ID available');
      return;
    }

    setLoadingStates((prev) => ({ ...prev, [report.id]: true }));
    setCompletedStates((prev) => ({ ...prev, [report.id]: false }));

    try {
      const response = await api.get(report.endpoint(scanId), {
        responseType: 'blob',
        timeout: 60000,
      });

      const blob = new Blob([response.data], { type: report.contentType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = report.filename(scanId);
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setCompletedStates((prev) => ({ ...prev, [report.id]: true }));
      toast.success(`${report.label} downloaded successfully`);

      // Clear completed state after a few seconds
      setTimeout(() => {
        setCompletedStates((prev) => ({ ...prev, [report.id]: false }));
      }, 3000);
    } catch (error) {
      console.error(`Failed to download ${report.label}:`, error);
      const message = error.response?.status === 404
        ? 'Report not available for this scan'
        : `Failed to download ${report.label}`;
      toast.error(message);
    } finally {
      setLoadingStates((prev) => ({ ...prev, [report.id]: false }));
    }
  };

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Download size={20} className="text-zinc-400" />
            Export Reports
          </CardTitle>
          {scanId && (
            <Badge variant="outline" className="text-xs">
              Scan #{String(scanId).slice(0, 8)}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {REPORT_TYPES.map((report) => {
            const Icon = report.icon;
            const isLoading = loadingStates[report.id];
            const isCompleted = completedStates[report.id];

            return (
              <div
                key={report.id}
                className="p-4 rounded-xl border-2 border-zinc-800 hover:border-zinc-700 transition-all"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: report.bgColor }}
                  >
                    <Icon size={20} style={{ color: report.color }} />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-zinc-200">{report.label}</h4>
                  </div>
                </div>
                <p className="text-xs text-zinc-500 mb-4 leading-relaxed">
                  {report.description}
                </p>
                <Button
                  onClick={() => handleDownload(report)}
                  disabled={isLoading || !scanId}
                  variant="outline"
                  size="sm"
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <Loader2 size={14} className="mr-1.5 animate-spin" />
                      Generating...
                    </>
                  ) : isCompleted ? (
                    <>
                      <CheckCircle size={14} className="mr-1.5 text-green-400" />
                      Downloaded
                    </>
                  ) : (
                    <>
                      <Download size={14} className="mr-1.5" />
                      Download
                    </>
                  )}
                </Button>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default ReportDownloads;
