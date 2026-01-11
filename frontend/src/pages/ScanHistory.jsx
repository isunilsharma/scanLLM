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
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Scan History</h1>
        
        {loading ? (
          <div className="space-y-3">
            {[1,2,3,4,5].map(i => (
              <div key={i} className="h-20 bg-gray-100 rounded animate-pulse"></div>
            ))}
          </div>
        ) : scans.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No scans yet</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
            <table className="w-full min-w-[600px]">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Repository</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Status</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Time</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Summary</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-600">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {scans.map(scan => (
                  <tr key={scan.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {scan.repo_owner}/{scan.repo_name || scan.repo_url}
                    </td>
                    <td className="px-4 py-3">
                      {scan.status === 'SUCCESS' && (
                        <Badge className="bg-green-100 text-green-800">Success</Badge>
                      )}
                      {scan.status === 'FAILED' && (
                        <Badge className="bg-red-100 text-red-800">Failed</Badge>
                      )}
                      {scan.status === 'RUNNING' && (
                        <Badge className="bg-blue-100 text-blue-800">Running</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(scan.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {scan.total_matches || 0} matches • {scan.files_count || 0} files
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
