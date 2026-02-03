import React, { useState, useEffect, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { useAuth } from '../context/AuthContext';

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
    
    // Safety check: don't make API call without token
    if (!token) {
      console.warn('AppSidebar: No auth token found, skipping API call');
      setLoading(false);
      return;
    }
    
    console.log('AppSidebar: Loading repos with filter:', filter);
    
    try {
      const response = await axios.get(`${API}/github/repos`, {
        params: { visibility: filter },
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setRepos(response.data.repos || []);
      console.log(`AppSidebar: Loaded ${response.data.repos?.length || 0} repos`);
    } catch (error) {
      console.error('AppSidebar: Failed to load repos:', error);
      // Only clear repos on 401 (unauthorized), not on other errors
      if (error.response?.status === 401) {
        console.log('AppSidebar: 401 response - may need to re-authenticate');
        setRepos([]);
      }
    } finally {
      setLoading(false);
    }
  }, [filter]);

  // Load repos only when authenticated
  useEffect(() => {
    // Wait for auth to be ready before fetching repos
    if (authLoading) {
      console.log('AppSidebar: Waiting for auth to complete...');
      return;
    }
    
    if (!isAuthenticated) {
      console.log('AppSidebar: Not authenticated, skipping repo fetch');
      setLoading(false);
      return;
    }
    
    // Fetch repos when authenticated
    loadRepos();
  }, [loadRepos, isAuthenticated, authLoading]);

  // ESC key to close drawer
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && onClose) {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const loadRepos = async () => {
    setLoading(true);
    const token = localStorage.getItem('auth_token');
    
    // Safety check: don't make API call without token
    if (!token) {
      console.warn('AppSidebar: No auth token found, skipping API call');
      setLoading(false);
      return;
    }
    
    console.log('AppSidebar: Loading repos with filter:', filter);
    
    try {
      const response = await axios.get(`${API}/github/repos`, {
        params: { visibility: filter },
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setRepos(response.data.repos || []);
      console.log(`AppSidebar: Loaded ${response.data.repos?.length || 0} repos`);
    } catch (error) {
      console.error('AppSidebar: Failed to load repos:', error);
      // Only clear repos on 401 (unauthorized), not on other errors
      if (error.response?.status === 401) {
        console.log('AppSidebar: 401 response - may need to re-authenticate');
        setRepos([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleInstallApp = () => {
    // Redirect to GitHub App installation
    window.open('https://github.com/apps/scanllm-ai/installations/new', '_blank');
  };

  const filteredRepos = repos.filter(repo =>
    repo.full_name.toLowerCase().includes(search.toLowerCase())
  );

  const isRepoActive = (repoFullName) => {
    // Extract owner and repo from current route
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
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
      
      {/* Search */}
      <div className="p-4 border-b border-gray-200">
        <Input
          placeholder="Search repos..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="mb-3"
        />
        
        {/* Filters */}
        <div className="flex gap-2">
          {['all', 'private', 'public'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                filter === f
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Repo List */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {loading ? (
            <div className="space-y-2">
              {[1,2,3,4,5].map(i => (
                <div key={i} className="h-16 bg-gray-100 rounded animate-pulse"></div>
              ))}
            </div>
          ) : repos.length === 0 ? (
            <div className="p-4">
              {/* Installation Prompt */}
              <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4 text-center">
                <svg className="w-12 h-12 mx-auto text-blue-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <h3 className="font-bold text-gray-900 mb-2 text-sm">Install GitHub App</h3>
                <p className="text-xs text-gray-700 mb-3">
                  Install ScanLLM.ai to access your repositories
                </p>
                
                <div className="bg-white rounded p-3 mb-3 text-left">
                  <p className="text-xs font-medium text-gray-700 mb-2">Quick Steps:</p>
                  <ol className="text-xs text-gray-600 space-y-1">
                    <li>1. Click Install below</li>
                    <li>2. Select repositories</li>
                    <li>3. Click &ldquo;Install&rdquo;</li>
                    <li>4. Return here</li>
                  </ol>
                </div>
                
                <button
                  onClick={handleInstallApp}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded text-sm transition-colors"
                >
                  Install GitHub App
                </button>
                
                <p className="text-xs text-gray-500 mt-2">
                  Read-only access
                </p>
              </div>
            </div>
          ) : filteredRepos.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-sm">
              <p>No repositories found</p>
            </div>
          ) : (
            <div className="space-y-1">
              {filteredRepos.map(repo => (
                <button
                  key={repo.full_name}
                  onClick={() => {
                    navigate(`/app/repo/${repo.owner}/${repo.name}`);
                    if (onRepoSelect) onRepoSelect(); // Close sidebar on mobile
                  }}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    isRepoActive(repo.full_name)
                      ? 'bg-blue-50 border border-blue-200'
                      : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <div className="flex items-start justify-between mb-1">
                    <h3 className="font-medium text-sm text-gray-900 truncate flex-1">
                      {repo.name}
                    </h3>
                    {repo.private && (
                      <Badge variant="secondary" className="text-xs ml-2 flex-shrink-0">Private</Badge>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 truncate">{repo.owner}</p>
                </button>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Sidebar Footer */}
      <div className="p-4 border-t border-gray-200 space-y-2">
        <Link to="/app/history" className="block text-sm text-gray-700 hover:text-primary transition-colors">
          Scan History
        </Link>
        <Link to="/app/settings" className="block text-sm text-gray-700 hover:text-primary transition-colors">
          Settings
        </Link>
      </div>
    </div>
  );
};

export default AppSidebar;
