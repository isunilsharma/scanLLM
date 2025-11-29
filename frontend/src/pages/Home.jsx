import React, { useState } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import ScanResults from '../components/ScanResults';
import RepoForm from '../components/RepoForm';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const [repoUrl, setRepoUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);
  const [scanDuration, setScanDuration] = useState(null);

  const handleScan = async (repoUrlParam, fullScan = false) => {
    const startTime = Date.now();

    setIsScanning(true);
    setError(null);
    setScanResult(null);
    setScanDuration(null);

    try {
      const response = await axios.post(`${API}/scans`, {
        repo_url: repoUrlParam,
        full_scan: fullScan
      });

      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      setScanDuration(duration);
      setScanResult(response.data);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to scan repository';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 md:pt-16 lg:pt-20 pb-8 md:pb-12 text-center">
        <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-4 md:mb-6 tracking-tight max-w-5xl mx-auto">
          Know where AI actually lives in your codebase.
        </h1>
        <p className="text-base sm:text-lg md:text-xl text-gray-600 font-normal mb-6 md:mb-8 max-w-3xl mx-auto leading-relaxed">
          ScanLLM.ai scans your GitHub repositories and identifies every AI/LLM integration—giving platform and infra teams a clear, accurate view of their real AI footprint.
        </p>
        
        {/* Feature highlights - compact horizontal row */}
        <div className="flex flex-wrap justify-center items-center gap-x-6 md:gap-x-10 gap-y-3 mb-8 md:mb-10 text-xs sm:text-sm text-gray-600 max-w-4xl mx-auto">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-accent flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Detect OpenAI, Anthropic, LangChain, vLLM, Transformers</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-accent flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Reveal hidden or shadow AI usage</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-accent flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Run lightweight scans in minutes</span>
          </div>
        </div>

        {/* Scan Card */}
        <div className="w-full max-w-2xl lg:max-w-3xl mx-auto bg-white rounded-2xl shadow-lg border border-gray-200 p-6 md:p-8">
          <RepoForm onScan={handleScan} isScanning={isScanning} />
        </div>

        {/* Note below card */}
        <p className="text-xs text-gray-500 mt-6 italic max-w-2xl mx-auto">
          We currently support public repositories. Private repository support and enterprise integrations are on the roadmap.
        </p>
      </section>

      {/* Error Display */}
      {error && (
        <div className="max-w-5xl mx-auto px-6 mb-8">
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
        </div>
      )}

      {/* Loading State */}
      {isScanning && (
        <div className="max-w-5xl mx-auto px-6 mb-8">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-12" data-testid="loading-state">
            <div className="flex flex-col items-center justify-center gap-4">
              <div className="w-12 h-12 border-4 border-gray-300 border-t-primary rounded-full animate-spin"></div>
              <div className="text-center">
                <p className="text-lg font-medium text-gray-900">Scanning repository...</p>
                <p className="text-sm text-gray-600 mt-1">Estimated time: 2-5 seconds</p>
                <p className="text-xs text-gray-500 mt-2">Analyzing code patterns and extracting insights</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {scanResult && !isScanning && (
        <div className="max-w-7xl mx-auto px-6 pb-12">
          {scanDuration && (
            <div className="mb-4 text-center">
              <span className="inline-flex items-center gap-2 px-4 py-2 bg-green-50 text-green-800 rounded-full text-sm font-medium">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Scan completed in {scanDuration}s
              </span>
            </div>
          )}
          <ScanResults result={scanResult} />
        </div>
      )}
    </div>
  );
};

export default Home;
