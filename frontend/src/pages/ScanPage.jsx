import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import ScanResults from '../components/ScanResults';
import ScanLoader from '../components/ScanLoader';
import { Button } from '../components/ui/button';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ScanPage = () => {
  const { scanId } = useParams();
  const navigate = useNavigate();
  const [scanData, setScanData] = useState(null);
  const [status, setStatus] = useState('PENDING');
  const [error, setError] = useState(null);
  const [startTime] = useState(Date.now());
  const [repoInfo, setRepoInfo] = useState({ name: '', branch: 'main', commit: null });

  useEffect(() => {
    if (!scanId) {
      navigate('/demo');
      return;
    }

    pollScanStatus();
  }, [scanId]);

  const pollScanStatus = async () => {
    let attempts = 0;
    const maxAttempts = 60; // 60 attempts * 2s = 2 minutes max
    
    const poll = async () => {
      try {
        const response = await axios.get(`${API}/scans/${scanId}`);
        const data = response.data;
        
        setStatus(data.status);
        
        if (data.status === 'SUCCESS') {
          setScanData(data);
          return; // Stop polling
        } else if (data.status === 'FAILED') {
          setError(data.error_message || 'Scan failed');
          return;
        }
        
        // Continue polling if PENDING or RUNNING
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000); // Poll every 2 seconds
        } else {
          setError('Scan timed out');
        }
      } catch (err) {
        if (err.response?.status === 404) {
          setError('Scan not found');
        } else {
          setError('Failed to fetch scan status');
        }
      }
    };

    poll();
  };

  const elapsed = Math.floor((Date.now() - startTime) / 1000);

  return (
    <div className="min-h-screen bg-background py-12">
      <div className="max-w-6xl mx-auto px-6">
        {/* Loading State */}
        {(status === 'PENDING' || status === 'RUNNING') && (
          <div className="max-w-3xl mx-auto">
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-12">
              <div className="text-center mb-8">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  {STATUS_MESSAGES[messageIndex]}
                </h2>
                <p className="text-gray-600 mb-4">
                  Elapsed: {elapsed}s
                </p>
              </div>

              {/* Horizontal Shimmer Bar */}
              <div className="relative w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-500 to-transparent shimmer"></div>
              </div>

              <p className="text-sm text-gray-500 text-center mt-6">
                This can take 10-40 seconds depending on repository size
              </p>

              <div className="text-center mt-6">
                <button
                  onClick={() => navigate('/demo')}
                  className="text-sm text-gray-600 hover:text-gray-900 underline"
                >
                  Back to demo
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="max-w-3xl mx-auto">
            <div className="bg-red-50 border border-red-200 rounded-xl p-8 text-center">
              <svg className="w-12 h-12 text-red-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h2 className="text-xl font-semibold text-red-900 mb-2">Scan Failed</h2>
              <p className="text-red-700 mb-6">{error}</p>
              <div className="flex gap-4 justify-center">
                <Button onClick={() => navigate('/demo')} variant="outline">
                  Try another repo
                </Button>
                <Button onClick={() => navigate('/')}>
                  Sign in with GitHub
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Results State */}
        {scanData && status === 'SUCCESS' && (
          <div>
            {/* Demo Badge */}
            <div className="mb-6 text-center">
              <span className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-800 border border-blue-200 rounded-full text-sm font-medium">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Demo Scan
              </span>
            </div>

            {/* CTA Banner */}
            <div className="mb-6 bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-6 text-white text-center">
              <h3 className="text-xl font-semibold mb-2">Want to scan your private repos?</h3>
              <p className="text-blue-100 mb-4">Sign in with GitHub to access all features</p>
              <Button
                onClick={() => navigate('/')}
                variant="secondary"
                className="bg-white text-blue-700 hover:bg-blue-50"
              >
                Sign in with GitHub
              </Button>
            </div>

            {/* Results */}
            <ScanResults result={scanData} />
          </div>
        )}
      </div>
    </div>
  );
};

export default ScanPage;
