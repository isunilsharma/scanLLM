import React, { useState, useEffect, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { useAuth } from '../context/AuthContext';
import Logo from './Logo';
import {
  Search, Plus, Clock, Settings, History, Shield,
  Lock, Globe, X, Zap, GitBranch, ChevronRight
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AppSidebar = ({ onRepoSelect, onClose }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');

  const loadRepos = useCallback(async () => {
    setLoading(true);
    const token = localStorage.getItem('auth_token');

    if (!token) {
      console.warn('AppSidebar: No auth token found, skipping API call');
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/github/repos`, {
        params: { visibility: filter },
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setRepos(response.data.repos || []);
    } catch (error) {
      console.error('AppSidebar: Failed to load repos:', error);
      if (error.response?.status === 401) {
        setRepos([]);
      }
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }
    loadRepos();
  }, [loadRepos, isAuthenticated, authLoading]);

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && onClose) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const handleInstallApp = () => {
    window.open('https://github.com/apps/scanllm-ai/installations/new', '_blank');
  };

  const handleNewScan = () => {
    // Navigate to the first repo or a scan page
    if (repos.length > 0) {
      navigate(`/app/repo/${repos[0].owner}/${repos[0].name}`);
    }
    if (onRepoSelect) onRepoSelect();
  };

  const filteredRepos = repos.filter(repo =>
    repo.full_name.toLowerCase().includes(search.toLowerCase())
  );

  const isRepoActive = (repoFullName) => {
    const pathMatch = location.pathname.match(/\/app\/repo\/([^\/]+)\/([^\/]+)/);
    if (!pathMatch) return false;
    const activeFullName = `${pathMatch[1]}/${pathMatch[2]}`;
    return activeFullName === repoFullName;
  };

  return (
    <div className="w-full h-full bg-white border-r border-gray-200 flex flex-col">
      {/* Mobile Close Button */}
      {onClose && (
        <button
          onClick={onClose}
          className="md:hidden absolute top-4 right-4 p-2 text-gray-600 hover:text-gray-900 z-10"
          aria-label="Close menu"
        >
          <X size={20} />
        </button>
      )}

      {/* Logo Header */}
      <div className="p-4 border-b border-gray-100">
        <Link to="/app" className="block">
          <Logo size="default" />
        </Link>
      </div>

      {/* New Scan Button */}
      <div className="px-4 pt-4 pb-2">
        <Button
          onClick={handleNewScan}
          className="w-full"
          size="sm"
          disabled={repos.length === 0 && !loading}
        >
          <Plus size={14} className="mr-1.5" />
          New Scan
        </Button>
      </div>

      {/* Search */}
      <div className="px-4 pb-3">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="Search repos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-8 text-sm"
          />
        </div>
      </div>

      {/* Filters */}
      <div className="px-4 pb-3">
        <div className="flex gap-1.5">
          {['all', 'private', 'public'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                filter === f
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {f === 'private' && <Lock size={10} />}
              {f === 'public' && <Globe size={10} />}
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <Separator />

      {/* Section Header */}
      <div className="px-4 pt-3 pb-1">
        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
          Your Repositories
        </p>
      </div>

      {/* Repo List */}
      <ScrollArea className="flex-1">
        <div className="px-2 pb-2">
          {loading ? (
            <div className="space-y-1.5 p-2">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="h-14 bg-gray-100 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : repos.length === 0 ? (
            <div className="p-4">
              <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-4 text-center">
                <Zap size={32} className="text-blue-600 mx-auto mb-3" />
                <h3 className="font-bold text-gray-900 mb-2 text-sm">Install GitHub App</h3>
                <p className="text-xs text-gray-700 mb-3">
                  Install ScanLLM.ai to access your repositories
                </p>
                <div className="bg-white rounded-lg p-3 mb-3 text-left">
                  <p className="text-xs font-medium text-gray-700 mb-2">Quick Steps:</p>
                  <ol className="text-xs text-gray-600 space-y-1">
                    <li>1. Click Install below</li>
                    <li>2. Select repositories</li>
                    <li>3. Click &ldquo;Install&rdquo;</li>
                    <li>4. Return here</li>
                  </ol>
                </div>
                <Button onClick={handleInstallApp} className="w-full" size="sm">
                  Install GitHub App
                </Button>
                <p className="text-xs text-gray-500 mt-2">Read-only access</p>
              </div>
            </div>
          ) : filteredRepos.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-sm">
              <p>No repositories found</p>
            </div>
          ) : (
            <div className="space-y-0.5">
              {filteredRepos.map(repo => {
                const active = isRepoActive(repo.full_name);
                return (
                  <button
                    key={repo.full_name}
                    onClick={() => {
                      navigate(`/app/repo/${repo.owner}/${repo.name}`);
                      if (onRepoSelect) onRepoSelect();
                    }}
                    className={`w-full text-left p-3 rounded-lg transition-all group ${
                      active
                        ? 'bg-blue-50 border border-blue-200'
                        : 'hover:bg-gray-50 border border-transparent'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <h3 className="font-medium text-sm text-gray-900 truncate">
                            {repo.name}
                          </h3>
                          {repo.private && (
                            <Lock size={10} className="text-slate-400 flex-shrink-0" />
                          )}
                        </div>
                        <p className="text-xs text-gray-400 truncate">{repo.owner}</p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {/* Risk score placeholder - populated when scan data available */}
                        {repo.last_risk_score != null && (
                          <Badge
                            variant={repo.last_risk_score <= 40 ? 'default' : repo.last_risk_score <= 60 ? 'secondary' : 'destructive'}
                            className="text-[10px] px-1.5"
                          >
                            <Shield size={8} className="mr-0.5" />
                            {Math.round(repo.last_risk_score)}
                          </Badge>
                        )}
                        <ChevronRight
                          size={14}
                          className={`text-slate-300 transition-transform ${active ? 'text-blue-400' : 'group-hover:translate-x-0.5'}`}
                        />
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Sidebar Footer */}
      <Separator />
      <div className="p-3 space-y-0.5">
        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-3 mb-2">
          Quick Links
        </p>
        <Link
          to="/app/history"
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-primary hover:bg-slate-50 rounded-md transition-colors"
        >
          <History size={14} />
          Scan History
        </Link>
        <Link
          to="/app/settings"
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-primary hover:bg-slate-50 rounded-md transition-colors"
        >
          <Settings size={14} />
          Settings
        </Link>
      </div>
    </div>
  );
};

export default AppSidebar;
