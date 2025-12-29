import React, { useState } from 'react';
import axios from 'axios';
import ScanResults from '../components/ScanResults';
import RepoForm from '../components/RepoForm';
import LoginButton from '../components/LoginButton';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const { isAuthenticated, user } = useAuth();
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);
  const [scanDuration, setScanDuration] = useState(null);
  const [isFullScan, setIsFullScan] = useState(false);

  const handleScan = async (repoUrlParam, fullScan = false) => {
    const startTime = Date.now();

    setIsScanning(true);
    setIsFullScan(fullScan);
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
        <div className="w-full max-w-3xl lg:max-w-4xl mx-auto space-y-6">
          {/* Dual CTAs */}
          {!isAuthenticated && (
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 md:p-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">Choose how to scan</h3>
              <div className="grid md:grid-cols-2 gap-4">
                {/* Try Demo */}


      {/* How It Works Section */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            From GitHub URL to actionable insights in seconds
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Video Placeholder */}
          <div className="bg-gray-100 rounded-xl aspect-video flex items-center justify-center border-2 border-dashed border-gray-300">
            <div className="text-center">
              <svg className="w-16 h-16 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-gray-500">Product Demo Video</p>
              <p className="text-xs text-gray-400 mt-1">(Coming soon)</p>
            </div>
          </div>

          {/* Screenshot Placeholder */}
          <div className="bg-gray-100 rounded-xl aspect-video flex items-center justify-center border-2 border-dashed border-gray-300">
            <div className="text-center">
              <svg className="w-16 h-16 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p className="text-sm text-gray-500">Dashboard Screenshot</p>
              <p className="text-xs text-gray-400 mt-1">(Coming soon)</p>
            </div>
          </div>
        </div>

        {/* Key features */}
        <div className="grid md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <span className="text-2xl">⚡</span>
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Fast Scans</h4>
            <p className="text-sm text-gray-600">2-15 seconds for most repositories with smart filtering</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <span className="text-2xl">🔒</span>
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Private Repos</h4>
            <p className="text-sm text-gray-600">Secure OAuth integration for your private repositories</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <span className="text-2xl">📊</span>
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Rich Insights</h4>
            <p className="text-sm text-gray-600">Policies, risk flags, blast radius, and AI-powered explanations</p>
          </div>
        </div>
      </section>

                <div className="border-2 border-gray-200 rounded-xl p-6 hover:border-primary transition-colors">
                  <div className="text-center mb-4">
                    <svg className="w-12 h-12 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    <h4 className="font-semibold text-gray-900 mb-2">Try a Demo</h4>
                    <p className="text-sm text-gray-600 mb-4">Scan any public GitHub repository</p>
                  </div>
                </div>
                
                {/* Sign in with GitHub */}
                <div className="border-2 border-primary rounded-xl p-6 bg-blue-50">
                  <div className="text-center mb-4">
                    <svg className="w-12 h-12 mx-auto text-primary mb-3" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                    <h4 className="font-semibold text-gray-900 mb-2">Scan Private Repos</h4>
                    <p className="text-sm text-gray-600 mb-4">Connect GitHub to scan your private repositories</p>
                    <LoginButton className="w-full" />
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Public scan form (always visible or when authenticated) */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 md:p-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{isAuthenticated ? 'Quick Scan (Public Repos)' : 'Try a Demo Scan'}</h3>
            <RepoForm onScan={handleScan} isScanning={isScanning} />
          </div>
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
                <p className="text-sm text-gray-600 mt-1">
                  {isFullScan ? 'Full scan: 20-40 seconds' : 'Estimated time: 2-10 seconds'}
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  {isFullScan ? 'Analyzing all files in repository' : 'Scanning first 1,000 files (prioritizing src/, lib/, app/)'}
                </p>
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
