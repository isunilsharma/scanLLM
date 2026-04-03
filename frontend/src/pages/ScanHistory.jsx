import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ScanHistory = () => {
  const navigate = useNavigate();
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/scans`, {
        params: { limit: 50 },
        withCredentials: true
      });
      setScans(response.data.scans || []);
    } catch (error) {
      console.error('Failed to load scan history:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-zinc-100 mb-6">Scan History</h1>

        {loading ? (
          <div className="space-y-3">
            {[1,2,3,4,5].map(i => (
              <div key={i} className="h-20 bg-zinc-800 rounded animate-pulse"></div>
            ))}
          </div>
        ) : scans.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-zinc-500">No scans yet</p>
          </div>
        ) : (
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 overflow-x-auto">
            <table className="w-full min-w-[600px]">
              <thead className="bg-zinc-800/50 border-b border-zinc-800">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-medium text-zinc-400">Repository</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-zinc-400">Status</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-zinc-400">Time</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-zinc-400">Summary</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-zinc-400">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {scans.map(scan => (
                  <tr key={scan.id} className="hover:bg-zinc-800/30">
                    <td className="px-4 py-3 text-sm font-medium text-zinc-100">
                      {scan.repo_owner}/{scan.repo_name || scan.repo_url}
                    </td>
                    <td className="px-4 py-3">
                      {scan.status === 'SUCCESS' && (
                        <Badge className="bg-green-500/10 text-green-400 border-green-500/20">Success</Badge>
                      )}
                      {scan.status === 'FAILED' && (
                        <Badge className="bg-red-500/10 text-red-400 border-red-500/20">Failed</Badge>
                      )}
                      {scan.status === 'RUNNING' && (
                        <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/20">Running</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-zinc-400">
                      {new Date(scan.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-zinc-400">
                      {scan.total_matches || 0} matches &bull; {scan.files_count || 0} files
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        onClick={() => navigate(`/scan/${scan.id}`)}
                        variant="outline"
                        size="sm"
                      >
                        View
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScanHistory;
