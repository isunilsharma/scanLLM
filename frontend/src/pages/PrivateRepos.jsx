import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PrivateRepos = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [scanning, setScanning] = useState(null);

  useEffect(() => {
    loadRepos();
  }, [filter]);

  const loadRepos = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/github/repos`, {
        params: { visibility: filter },
        withCredentials: true
      });
      setRepos(response.data.repos || []);
    } catch (error) {
      console.error('Failed to load repositories:', error);
      toast.error('Failed to load repositories');
    } finally {
      setLoading(false);
    }
  };

  const handleInstallApp = () => {
    // Redirect to GitHub App installation page
    window.location.href = `https://github.com/apps/scanllm-ai/installations/new`;
  };

  const handleScan = async (owner, repoName, branch, fullScan = false) => {
    setScanning(`${owner}/${repoName}`);
    
    try {
      const response = await axios.post(
        `${API}/scan/github`,
        { owner, repo: repoName, branch, full_scan: fullScan },
        { withCredentials: true }
      );
      
      // Navigate to scan page with loader (don't show results inline)
      navigate(`/scan/${response.data.scan_id}`);
    } catch (error) {
      toast.error('Scan failed: ' + (error.response?.data?.detail || 'Unknown error'));
      setScanning(null);
    }
  };

  const filteredRepos = repos.filter(repo =>
    repo.full_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header with user profile */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            {user?.avatar_url && (
              <img src={user.avatar_url} alt={user.login} className="w-12 h-12 rounded-full border-2 border-gray-200" />
            )}
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Your Repositories</h1>
              <p className="text-sm text-gray-600">Signed in as @{user?.login}</p>
            </div>
          </div>
          <Button onClick={logout} variant="outline">
            Disconnect GitHub
          </Button>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <Input
            placeholder="Search repositories..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="sm:flex-1"
          />
          <div className="flex gap-2">
            {['all', 'private', 'public'].map(f => (
              <Button
                key={f}
                onClick={() => setFilter(f)}
                variant={filter === f ? 'default' : 'outline'}
                size="sm"
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </Button>
            ))}
          </div>
        </div>

        {/* Repo list */}
        {loading ? (
          <div className="text-center py-12">
            <div className="w-12 h-12 border-4 border-gray-300 border-t-primary rounded-full animate-spin mx-auto"></div>
            <p className="text-gray-600 mt-4">Loading repositories...</p>
          </div>
        ) : repos.length === 0 ? (
          <div>
            {/* Installation Required Banner */}
            <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-8 text-center">
              <svg className="w-16 h-16 mx-auto text-blue-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">Install ScanLLM.ai GitHub App</h3>
              <p className="text-gray-700 mb-6 max-w-2xl mx-auto">
                To scan your private repositories, you need to install the ScanLLM.ai GitHub App and grant access to your repos.
              </p>
              
              <div className="bg-white rounded-lg p-6 mb-6 text-left max-w-2xl mx-auto">
                <h4 className="font-semibold text-gray-900 mb-3">Installation Steps:</h4>
                <ol className="space-y-2 text-sm text-gray-700">
                  <li className="flex gap-2">
                    <span className="font-semibold text-blue-600">1.</span>
                    <span>Click the button below to go to GitHub App installation</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="font-semibold text-blue-600">2.</span>
                    <span>Select which repositories to grant access (choose &quot;All repositories&quot; for full access)</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="font-semibold text-blue-600">3.</span>
                    <span>Click &quot;Install&quot; or &quot;Save&quot;</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="font-semibold text-blue-600">4.</span>
                    <span>You&apos;ll be redirected back here to see all your repositories</span>
                  </li>
                </ol>
              </div>
              
              <Button
                onClick={handleInstallApp}
                size="lg"
                className="px-8 py-6 text-lg font-semibold"
              >
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                Install GitHub App
              </Button>
              
              <p className="text-xs text-gray-500 mt-4">
                ScanLLM.ai requires read-only access to your repositories. We never modify code or share your data.
              </p>
            </div>
          </div>
        ) : filteredRepos.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p>No repositories found matching your search</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredRepos.map(repo => (
              <div key={repo.full_name} className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-gray-900">{repo.full_name}</h3>
                      {repo.private && <Badge variant="secondary">Private</Badge>}
                    </div>
                    {repo.description && (
                      <p className="text-sm text-gray-600 mb-3">{repo.description}</p>
                    )}
                    <p className="text-xs text-gray-500">
                      Updated: {new Date(repo.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Button
                    onClick={() => handleScan(repo.owner, repo.name, repo.default_branch)}
                    disabled={scanning === repo.full_name}
                  >
                    {scanning === repo.full_name ? 'Scanning...' : 'Scan'}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PrivateRepos;
