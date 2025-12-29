import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import LoginButton from '../components/LoginButton';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../components/ui/accordion';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const EXAMPLE_REPOS = [
  'https://github.com/rasbt/LLMs-from-scratch',
  'https://github.com/huggingface/transformers',
  'https://github.com/HandsOnLLM/Hands-On-Large-Language-Models',
  'https://github.com/Hannibal046/Awesome-LLM'
];

const Home = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [demoModalOpen, setDemoModalOpen] = useState(false);
  const [demoRepoUrl, setDemoRepoUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);

  const handleDemoScan = async () => {
    if (!demoRepoUrl.trim()) {
      toast.error('Please enter a GitHub repository URL');
      return;
    }

    setIsScanning(true);
    try {
      const response = await axios.post(`${API}/scans`, {
        repo_url: demoRepoUrl,
        full_scan: false
      });
      
      // Navigate to results (store in sessionStorage for demo badge)
      sessionStorage.setItem('demo_scan', JSON.stringify(response.data));
      sessionStorage.setItem('is_demo', 'true');
      window.location.href = '/#results';
      setDemoModalOpen(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Scan failed');
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="max-w-5xl mx-auto px-6 pt-20 pb-16 text-center">
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-4 tracking-tight">
          AI dependency intelligence for your GitHub repos.
        </h1>
        <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
          Detect AI/LLM frameworks, prompt/tooling usage, and risk signals in minutes.
        </p>

        {/* CTA Row */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-6">
          <LoginButton 
            size="lg" 
            className="w-full sm:w-auto px-8 py-6 text-lg font-semibold"
          />
          <Button
            onClick={() => setDemoModalOpen(true)}
            variant="outline"
            size="lg"
            className="w-full sm:w-auto px-8 py-6 text-lg"
          >
            Try demo on a public repo
          </Button>
        </div>

        {/* Trust Row */}
        <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Read-only access</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>No code copied into prompts</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Takes ~2 minutes</span>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="max-w-5xl mx-auto px-6 py-12 border-t border-gray-200">
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">How it works</h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl font-bold text-blue-600">1</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Connect GitHub</h3>
            <p className="text-sm text-gray-600">Sign in with read-only OAuth or paste a public repo URL</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl font-bold text-blue-600">2</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Pick repo</h3>
            <p className="text-sm text-gray-600">Select from your private repos or enter a public URL</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl font-bold text-blue-600">3</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Get insights</h3>
            <p className="text-sm text-gray-600">View AI usage, risk flags, and dependency intelligence</p>
          </div>
        </div>
      </section>

      {/* What You Get */}
      <section className="max-w-6xl mx-auto px-6 py-12 bg-white">
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">What you get</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="p-6 border border-gray-200 rounded-lg">
            <svg className="w-8 h-8 text-blue-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <h3 className="font-semibold text-gray-900 mb-2">AI Framework Detection</h3>
            <p className="text-sm text-gray-600">OpenAI, Anthropic, LangChain, vLLM, Transformers, and more</p>
          </div>
          <div className="p-6 border border-gray-200 rounded-lg">
            <svg className="w-8 h-8 text-blue-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <h3 className="font-semibold text-gray-900 mb-2">Dependency Intelligence</h3>
            <p className="text-sm text-gray-600">SBOM-style inventory with file locations and usage patterns</p>
          </div>
          <div className="p-6 border border-gray-200 rounded-lg">
            <svg className="w-8 h-8 text-blue-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h3 className="font-semibold text-gray-900 mb-2">Risk & Policy Flags</h3>
            <p className="text-sm text-gray-600">Spot deprecated models, secrets, and compliance issues</p>
          </div>
          <div className="p-6 border border-gray-200 rounded-lg">
            <svg className="w-8 h-8 text-blue-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="font-semibold text-gray-900 mb-2">Shareable Reports</h3>
            <p className="text-sm text-gray-600">Export JSON, view scan history (logged-in users)</p>
          </div>
        </div>
      </section>

      {/* Security & Permissions Accordion */}
      <section className="max-w-4xl mx-auto px-6 py-12">
        <Accordion type="single" collapsible className="bg-white rounded-lg border border-gray-200">
          <AccordionItem value="security">
            <AccordionTrigger className="px-6 py-4 hover:no-underline">
              <span className="font-semibold text-gray-900">Security & Permissions</span>
            </AccordionTrigger>
            <AccordionContent className="px-6 pb-4">
              <div className="space-y-4 text-sm text-gray-700">
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">What we access:</h4>
                  <p>Read-only access to repository contents and metadata. We use GitHub OAuth with minimal scopes (repo, read:org).</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">What we store:</h4>
                  <p>Scan results, findings metadata (file paths, line numbers, pattern matches). We do NOT store your source code.</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">What we never do:</h4>
                  <p>Copy code into LLM prompts, modify repositories, or share your data with third parties.</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">Revoke access anytime:</h4>
                  <p>Disconnect GitHub from your account settings. Tokens are encrypted at rest.</p>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </section>

      {/* Demo Modal */}
      <Dialog open={demoModalOpen} onOpenChange={setDemoModalOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Try it now (no sign-in)</DialogTitle>
            <DialogDescription>
              Analyze a public GitHub repository to see how ScanLLM.ai works
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div>
              <Input
                placeholder="https://github.com/owner/repo"
                value={demoRepoUrl}
                onChange={(e) => setDemoRepoUrl(e.target.value)}
                className="h-12"
                disabled={isScanning}
              />
              <p className="text-xs text-gray-500 mt-2">Enter a public GitHub repository URL</p>
            </div>

            {/* Example Chips */}
            <div>
              <p className="text-sm text-gray-700 font-medium mb-2">Try an example:</p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLE_REPOS.map((url, idx) => {
                  const repoName = url.split('/').pop();
                  return (
                    <button
                      key={idx}
                      onClick={() => setDemoRepoUrl(url)}
                      className="px-3 py-1.5 text-xs font-medium bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-full transition-colors"
                      disabled={isScanning}
                    >
                      {repoName}
                    </button>
                  );
                })}
              </div>
            </div>

            <Button
              onClick={handleDemoScan}
              disabled={!demoRepoUrl.trim() || isScanning}
              className="w-full h-12"
            >
              {isScanning ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Analyzing...
                </>
              ) : (
                'Analyze repo'
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Home;
