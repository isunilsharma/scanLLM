import React, { useState } from 'react';
import axios from 'axios';
import ScanResults from '../components/ScanResults';
import RepoForm from '../components/RepoForm';
import LoginButton from '../components/LoginButton';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SAMPLE_REPOS = [
  { name: 'LLMs from Scratch', url: 'https://github.com/rasbt/LLMs-from-scratch' },
  { name: 'Transformers', url: 'https://github.com/huggingface/transformers' },
  { name: 'Hands-On LLMs', url: 'https://github.com/HandsOnLLM/Hands-On-Large-Language-Models' },
  { name: 'Awesome LLM', url: 'https://github.com/Hannibal046/Awesome-LLM' }
];

const Home = () => {
  const { isAuthenticated, user } = useAuth();
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);
  const [scanDuration, setScanDuration] = useState(null);
  const [isFullScan, setIsFullScan] = useState(false);
  const [demoRepoUrl, setDemoRepoUrl] = useState('');

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

  const handleSampleClick = (url) => {
    setDemoRepoUrl(url);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 md:pt-16 lg:pt-20 pb-8 md:pb-12 text-center">
        <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-4 md:mb-6 tracking-tight max-w-5xl mx-auto">
          Know where AI actually lives in your codebase.
        </h1>
        <p className="text-base sm:text-lg md:text-xl text-gray-600 font-normal mb-6 md:mb-8 max-w-3xl mx-auto leading-relaxed">
          ScanLLM.ai identifies AI and LLM usage across your repositories—giving platform and infra teams a clear view of their real AI footprint.
        </p>
        
        {/* Feature highlights */}
        <div className="flex flex-wrap justify-center items-center gap-x-6 md:gap-x-10 gap-y-3 mb-10 md:mb-12 text-xs sm:text-sm text-gray-600 max-w-4xl mx-auto">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-accent flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Detect OpenAI, vLLM, Transformers, LangChain</span>
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
            <span>Lightweight scans in minutes</span>
          </div>
        </div>

        {/* PRIMARY CTA - Sign in with GitHub */}
        {!isAuthenticated && (
          <div className="max-w-2xl mx-auto mb-12">
            <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl shadow-xl p-8 text-white">
              <div className="text-center">
                <svg className="w-16 h-16 mx-auto mb-4 opacity-90" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                <h2 className="text-2xl font-bold mb-3">Scan Private Repositories</h2>
                <p className="text-blue-100 mb-6">
                  Connect GitHub to scan private repositories securely
                </p>
                <LoginButton 
                  variant="secondary" 
                  size="lg" 
                  className="bg-white text-blue-700 hover:bg-blue-50 font-semibold text-base px-8"
                />
                <p className="text-xs text-blue-200 mt-4">
                  Read-only access • No code changes • Secure OAuth
                </p>
              </div>
            </div>
          </div>
        )}

        {/* SECONDARY - Try Demo Section */}
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Try a Demo Scan</h2>
            <p className="text-gray-600">
              Explore ScanLLM using a public GitHub repository. No sign-in required.
            </p>
          </div>

          {/* Demo Form */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 md:p-8 mb-6">
            <RepoForm onScan={handleScan} isScanning={isScanning} />
          </div>

          {/* Sample Repos - Chips/Pills */}
          <div className="text-center">
            <p className="text-sm text-gray-700 font-medium mb-3">Quick start with a sample repository</p>
            <div className="flex flex-wrap justify-center gap-3">
              {SAMPLE_REPOS.map((repo, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    document.querySelector('[data-testid="repo-url-input"]').value = repo.url;
                    document.querySelector('[data-testid="repo-url-input"]').dispatchEvent(new Event('input', { bubbles: true }));
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-full text-sm font-medium text-gray-700 transition-colors"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                  {repo.name}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-4 italic">
              Demo scans public repositories only. Sign in with GitHub to scan private repos, save results, and view org-wide insights.
            </p>
          </div>
        </div>

        {/* Note */}
        <p className="text-xs text-gray-500 mt-8 italic max-w-2xl mx-auto">
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

      {/* Simplified How It Works */}
      <section className="max-w-6xl mx-auto px-6 py-16 border-t border-gray-200">
        <div className="grid md:grid-cols-3 gap-8 text-center">
          <div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Fast Scans</h3>
            <p className="text-sm text-gray-600">2-15 seconds for most repositories with smart filtering</p>
          </div>
          
          <div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Private Repos via GitHub</h3>
            <p className="text-sm text-gray-600">Secure OAuth integration for your private repositories</p>
          </div>
          
          <div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Rich AI Insights</h3>
            <p className="text-sm text-gray-600">Policies, risk flags, blast radius, and AI-powered explanations</p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
