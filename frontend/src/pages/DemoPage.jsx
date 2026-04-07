import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Switch } from '../components/ui/switch';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const EXAMPLE_REPOS = [
  { name: 'LLMs-from-scratch', url: 'https://github.com/rasbt/LLMs-from-scratch' },
  { name: 'Transformers', url: 'https://github.com/huggingface/transformers' },
  { name: 'Hands-On-LLMs', url: 'https://github.com/HandsOnLLM/Hands-On-Large-Language-Models' },
  { name: 'Awesome-LLM', url: 'https://github.com/Hannibal046/Awesome-LLM' }
];

const DemoPage = () => {
  const navigate = useNavigate();
  const [repoUrl, setRepoUrl] = useState('');
  const [fullScan, setFullScan] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!repoUrl.trim()) {
      toast.error('Please enter a GitHub repository URL');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await axios.post(`${API}/scans`, {
        repo_url: repoUrl.trim(),
        full_scan: fullScan
      });
      
      // Navigate to scan status page
      navigate(`/scan/${response.data.scan_id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start scan');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 py-16">
      <div className="max-w-3xl mx-auto px-6">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-zinc-100 mb-4">Try a Demo Scan</h1>
          <p className="text-lg text-zinc-400">
            Analyze any public GitHub repository. No sign-in required.
          </p>
        </div>

        <div className="bg-zinc-900 rounded-2xl shadow-lg border border-zinc-800 p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-zinc-100 mb-3">
                GitHub Repository URL
              </label>
              <Input
                placeholder="https://github.com/owner/repo"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                disabled={isSubmitting}
                className="h-12 text-base bg-zinc-800 border-zinc-700 text-zinc-100 placeholder:text-zinc-500"
              />
            </div>

            {/* Example Chips */}
            <div>
              <p className="text-sm text-zinc-300 font-medium mb-2">Quick start with an example:</p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLE_REPOS.map((repo, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setRepoUrl(repo.url)}
                    disabled={isSubmitting}
                    className="px-3 py-1.5 text-sm bg-zinc-800 hover:bg-zinc-700 border border-zinc-600 text-zinc-300 rounded-full transition-colors disabled:opacity-50"
                  >
                    {repo.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Full Scan Toggle */}
            <div className="flex items-center gap-3">
              <label htmlFor="full-scan-demo" className="text-sm font-medium text-zinc-100">
                Scan entire repository
              </label>
              <Switch
                id="full-scan-demo"
                checked={fullScan}
                onCheckedChange={setFullScan}
                disabled={isSubmitting}
              />
              {fullScan && (
                <span className="text-xs text-amber-400">May take 30+ seconds</span>
              )}
            </div>

            <Button
              type="submit"
              disabled={!repoUrl.trim() || isSubmitting}
              className="w-full h-12 text-base"
            >
              {isSubmitting ? 'Starting scan...' : 'Analyze repo'}
            </Button>
          </form>
        </div>

        <p className="text-center text-sm text-zinc-500 mt-6">
          Want to scan private repos? <button onClick={() => navigate('/')} className="text-primary hover:underline">Sign in with GitHub</button>
        </p>
      </div>
    </div>
  );
};

export default DemoPage;
