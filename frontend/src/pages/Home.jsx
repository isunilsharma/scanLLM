import React, { useState } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import ScanResults from '../components/ScanResults';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const [repoUrl, setRepoUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);

  const handleScan = async (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;

    setIsScanning(true);
    setError(null);
    setScanResult(null);

    try {
      const response = await axios.post(`${API}/scans`, {
        repo_url: repoUrl.trim()
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
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="max-w-5xl mx-auto px-6 pt-16 pb-12 text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6 tracking-tight">
          Know exactly where your LLMs live in your codebase.
        </h1>
        <p className="text-lg text-gray-700 mb-8 max-w-3xl mx-auto leading-relaxed">
          ScanLLM.ai analyzes your GitHub repositories and detects all AI/LLM framework usage, 
          so platform and infra teams finally get a clean map of their AI surface area.
        </p>
        
        {/* Feature bullets */}
        <div className="flex flex-wrap justify-center gap-6 mb-12 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-accent" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Detect OpenAI, Anthropic, LangChain, vLLM, and more</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-accent" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Spot risky or shadow AI usage fast</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-accent" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Run scans in minutes, not days</span>
          </div>
        </div>

        {/* Scan Card */}
        <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
          <form onSubmit={handleScan} className="space-y-6" data-testid="repo-form">
            <div className="text-left">
              <label htmlFor="repo-url" className="block text-sm font-medium text-gray-900 mb-3">
                GitHub Repository URL
              </label>
              <Input
                id="repo-url"
                data-testid="repo-url-input"
                type="text"
                placeholder="https://github.com/openai/openai-python"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                disabled={isScanning}
                className="h-12 text-base"
              />
              <p className="text-xs text-gray-500 mt-2">
                Enter a public GitHub repository URL to scan for AI/LLM dependencies.
              </p>
            </div>

            <Button
              type="submit"
              disabled={!repoUrl.trim() || isScanning}
              className="w-full h-12 text-base font-medium bg-primary hover:bg-primary/90"
              data-testid="scan-button"
            >
              {isScanning ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Scanning...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  Start Scan
                </>
              )}
            </Button>
          </form>
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
                <p className="text-sm text-gray-600 mt-1">This may take a few moments</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {scanResult && !isScanning && (
        <div className="max-w-7xl mx-auto px-6 pb-12">
          <ScanResults result={scanResult} />
        </div>
      )}
    </div>
  );
};

export default Home;
