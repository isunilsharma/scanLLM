import React, { useState } from 'react';
import axios from 'axios';
import RepoForm from '../components/RepoForm';
import ScanResults from '../components/ScanResults';
import { Toaster } from '../components/ui/sonner';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ScannerPage = () => {
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);

  const handleScan = async (repoUrl) => {
    setIsScanning(true);
    setError(null);
    setScanResult(null);

    try {
      const response = await axios.post(`${API}/scans`, {
        repo_url: repoUrl
      });

      setScanResult(response.data);
      toast.success('Scan completed successfully!');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to scan repository';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-slate-900 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">AI Dependency Scanner</h1>
              <p className="text-sm text-slate-600">Analyze GitHub repositories for LLM framework usage</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="space-y-8">
          {/* Scan Form */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
            <RepoForm onScan={handleScan} isScanning={isScanning} />
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6" data-testid="error-message">
              <div className="flex gap-3">
                <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <div>
                  <h3 className="font-medium text-red-900">Scan Failed</h3>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Loading State */}
          {isScanning && (
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12" data-testid="loading-state">
              <div className="flex flex-col items-center justify-center gap-4">
                <div className="w-12 h-12 border-4 border-slate-300 border-t-slate-900 rounded-full animate-spin"></div>
                <div className="text-center">
                  <p className="text-lg font-medium text-slate-900">Scanning repository...</p>
                  <p className="text-sm text-slate-600 mt-1">This may take a few moments</p>
                </div>
              </div>
            </div>
          )}

          {/* Results */}
          {scanResult && !isScanning && (
            <ScanResults result={scanResult} />
          )}
        </div>
      </main>
    </div>
  );
};

export default ScannerPage;
