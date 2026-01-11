import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AppSidebar = ({ onRepoSelect }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadRepos();
  }, [filter]);

  const loadRepos = async () => {
    setLoading(true);
    const token = localStorage.getItem('auth_token');
    
    console.log('AppSidebar: Loading repos with filter:', filter);
    
    try {
      const response = await axios.get(`${API}/github/repos`, {
        params: { visibility: filter },
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      setRepos(response.data.repos || []);
      console.log(`AppSidebar: Loaded ${response.data.repos?.length || 0} repos`);
    } catch (error) {
      console.error('AppSidebar: Failed to load repos:', error);
      setRepos([]); // Clear repos on error for security
    } finally {
      setLoading(false);
    }
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
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
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
