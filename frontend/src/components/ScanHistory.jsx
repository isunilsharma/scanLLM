import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Badge } from './ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ScanHistory = ({ repoUrl }) => {
  const [history, setHistory] = useState([]);
  const [drift, setDrift] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (repoUrl) {
      loadHistory();
    }
  }, [repoUrl]);

  const loadHistory = async () => {
    try {
      const response = await axios.get(`${API}/scan-history`, {
        params: { repo_url: repoUrl }
      });
      
      const scans = response.data.scans || [];
      setHistory(scans);
      
      // Compute drift if we have at least 2 scans
      if (scans.length >= 2) {
        const latest = scans[0];
        const previous = scans[1];
        
        let latestFrameworks = {};
        let prevFrameworks = {};
        try { latestFrameworks = JSON.parse(latest.frameworks_json || '{}'); } catch (e) { /* malformed JSON */ }
        try { prevFrameworks = JSON.parse(previous.frameworks_json || '{}'); } catch (e) { /* malformed JSON */ }
        
        const newFrameworks = Object.keys(latestFrameworks).filter(f => !prevFrameworks[f]);
        const removedFrameworks = Object.keys(prevFrameworks).filter(f => !latestFrameworks[f]);
        
        setDrift({
          total_matches_delta: latest.total_matches - previous.total_matches,
          ai_files_delta: latest.ai_files_count - previous.ai_files_count,
          new_frameworks: newFrameworks,
          removed_frameworks: removedFrameworks
        });
      }
    } catch (err) {
      console.error('Failed to load scan history:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-4">
        <div className="w-6 h-6 border-2 border-gray-300 border-t-gray-900 rounded-full animate-spin mx-auto"></div>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="text-center py-6 text-gray-500">
        <p className="text-sm">No previous scans found for this repository</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Drift Card */}
      {drift && (
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-5">
          <h4 className="font-semibold text-purple-900 mb-3">Drift Since Last Scan</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-xs text-purple-700 mb-1">Matches</p>
              <p className="text-lg font-semibold text-purple-900">
                {drift.total_matches_delta >= 0 ? '+' : ''}{drift.total_matches_delta}
              </p>
            </div>
            <div>
              <p className="text-xs text-purple-700 mb-1">Files</p>
              <p className="text-lg font-semibold text-purple-900">
                {drift.ai_files_delta >= 0 ? '+' : ''}{drift.ai_files_delta}
              </p>
            </div>
            <div>
              <p className="text-xs text-purple-700 mb-1">New Frameworks</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {drift.new_frameworks.length > 0 ? (
                  drift.new_frameworks.map(fw => (
                    <Badge key={fw} className="text-xs bg-green-600">{fw}</Badge>
                  ))
                ) : (
                  <span className="text-xs text-purple-700">None</span>
                )}
              </div>
            </div>
            <div>
              <p className="text-xs text-purple-700 mb-1">Removed</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {drift.removed_frameworks.length > 0 ? (
                  drift.removed_frameworks.map(fw => (
                    <Badge key={fw} className="text-xs bg-red-600">{fw}</Badge>
                  ))
                ) : (
                  <span className="text-xs text-purple-700">None</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* History Table */}
      <div>
        <h4 className="font-semibold text-gray-900 mb-3">Scan History</h4>
        <div className="border border-gray-200 rounded-lg overflow-x-auto">
          <table className="w-full text-sm min-w-[500px]">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left text-xs font-medium text-gray-600 px-4 py-2">Date</th>
                <th className="text-right text-xs font-medium text-gray-600 px-4 py-2">Files</th>
                <th className="text-right text-xs font-medium text-gray-600 px-4 py-2">Matches</th>
                <th className="text-left text-xs font-medium text-gray-600 px-4 py-2">Frameworks</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {history.map((scan, idx) => {
                const frameworks = JSON.parse(scan.frameworks_json || '{}');
                const frameworkNames = Object.keys(frameworks);
                
                return (
                  <tr key={scan.id} className={`hover:bg-gray-50 ${idx === 0 ? 'bg-blue-50' : ''}`}>
                    <td className="px-4 py-2 text-xs text-gray-600">
                      {new Date(scan.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-2 text-xs text-gray-900 text-right font-medium">
                      {scan.ai_files_count}
                    </td>
                    <td className="px-4 py-2 text-xs text-gray-900 text-right font-medium">
                      {scan.total_matches}
                    </td>
                    <td className="px-4 py-2 max-w-[140px] md:max-w-none">
                      <div className="flex flex-wrap gap-1">
                        {frameworkNames.map(fw => (
                          <Badge key={fw} variant="outline" className="text-xs truncate max-w-full">
                            {fw}
                          </Badge>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ScanHistory;
