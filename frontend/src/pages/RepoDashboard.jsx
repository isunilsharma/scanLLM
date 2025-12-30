import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const RepoDashboard = () => {
  const { owner, repo } = useParams();
  const navigate = useNavigate();
  const [branch, setBranch] = useState('main');
  const [fullScan, setFullScan] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [recentScans, setRecentScans] = useState([]);
  const [loadingScans, setLoadingScans] = useState(true);

  const loadRecentScans = async () => {
    setLoadingScans(true);
    try {
      const response = await axios.get(`${API}/scans`, {
        params: { 
          repo_full_name: `${owner}/${repo}`,
          limit: 4 
        },
        withCredentials: true
      });
      setRecentScans(response.data.scans || []);
    } catch (error) {
      console.error('Failed to load recent scans:', error);
    } finally {
      setLoadingScans(false);
    }
  };

  useEffect(() => {
    loadRecentScans();
  }, [owner, repo]);

  const handleRunScan = async () => {
    setIsScanning(true);
    try {
      const response = await axios.post(
        `${API}/scan/github`,
        { owner, repo, branch, full_scan: fullScan },
        { withCredentials: true }
      );
      
      // Navigate to scan page with loader
      navigate(`/app/repo/${owner}/${repo}/scan/${response.data.scan_id}`);
    } catch (error) {
      toast.error('Failed to start scan');
      setIsScanning(false);
    }
  };

  return (
    <div className="p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{owner}/{repo}</h1>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">Branch: {branch}</Badge>
          </div>
        </div>

        {/* Scan Configuration */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Run a Scan</h2>
          
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-700">Branch:</label>
              <input
                type="text"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                placeholder="main"
              />
            </div>
            
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="full-scan-dash"
                checked={fullScan}
                onChange={(e) => setFullScan(e.target.checked)}
                className="w-4 h-4"
              />
              <label htmlFor="full-scan-dash" className="text-sm text-gray-700">
                Scan entire repository (may take longer)
              </label>
            </div>
            
            <Button
              onClick={handleRunScan}
              disabled={isScanning}
              size="lg"
              className="w-full"
            >
              {isScanning ? 'Starting scan...' : 'Run Scan'}
            </Button>
          </div>
        </div>

        {/* Recent Scans */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Scans</h2>
          {loadingScans ? (
            <div className="space-y-3">
              {[1,2,3].map(i => (
                <div key={i} className="h-16 bg-gray-100 rounded animate-pulse"></div>
              ))}
            </div>
          ) : recentScans.length === 0 ? (
            <p className="text-sm text-gray-500">No scans yet. Run your first scan.</p>
          ) : (
            <div className="space-y-3">
              {recentScans.map(scan => (
                <div key={scan.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-gray-900">
                        {new Date(scan.created_at).toLocaleString()}
                      </span>
                      {scan.status === 'SUCCESS' && (
                        <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs font-medium rounded">SUCCESS</span>
                      )}
                      {scan.status === 'FAILED' && (
                        <span className="px-2 py-0.5 bg-red-100 text-red-800 text-xs font-medium rounded">FAILED</span>
                      )}
                      {scan.status === 'RUNNING' && (
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs font-medium rounded">RUNNING</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500">
                      {scan.total_matches || 0} matches • {scan.files_count || 0} files
                    </p>
                  </div>
                  <Button
                    onClick={() => navigate(`/app/repo/${owner}/${repo}/scan/${scan.id}`)}
                    variant="outline"
                    size="sm"
                  >
                    View
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RepoDashboard;
