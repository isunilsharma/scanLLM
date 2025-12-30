import React, { useState } from 'react';
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

  useEffect(() => {
    loadRecentScans();
  }, [owner, repo]);

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

        {/* Recent Scans Placeholder */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Scans</h2>
          <p className="text-sm text-gray-500">Scan history will appear here</p>
        </div>
      </div>
    </div>
  );
};

export default RepoDashboard;
