import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import ScanResults from '../components/ScanResults';

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
  const [scanResult, setScanResult] = useState(null);

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
      toast.error('Failed to load repositories');
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async (owner, repoName, branch, fullScan = false) => {
    setScanning(`${owner}/${repoName}`);
    setScanResult(null);
    
    try {
      const response = await axios.post(
        `${API}/scan/github`,
        { owner, repo: repoName, branch, full_scan: fullScan },
        { withCredentials: true }
      );
      setScanResult(response.data);
      toast.success('Scan completed!');
    } catch (error) {
      toast.error('Scan failed: ' + (error.response?.data?.detail || 'Unknown error'));
    } finally {
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
        ) : filteredRepos.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p>No repositories found</p>
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

        {/* Scan Results */}
        {scanResult && (
          <div className="mt-8">
            <ScanResults result={scanResult} />
          </div>
        )}
      </div>
    </div>
  );
};

export default PrivateRepos;
