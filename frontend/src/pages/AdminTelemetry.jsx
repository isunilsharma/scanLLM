import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { useAuth } from '../context/AuthContext';

const AdminTelemetry = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [feedback, setFeedback] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [feedbackFilter, setFeedbackFilter] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsRes, fbRes] = await Promise.all([
        api.get('/v1/telemetry/stats'),
        api.get('/v1/telemetry/feedback', { params: { limit: 100 } }),
      ]);
      setStats(statsRes.data);
      setFeedback(fbRes.data.feedback || []);
    } catch (err) {
      if (err.response?.status === 403) {
        setError('Admin access required. You do not have permission to view telemetry data.');
      } else if (err.response?.status === 500) {
        setError('Server error loading telemetry. Check backend logs for details.');
      } else if (err.response?.status === 401) {
        setError('Authentication required. Please log in first.');
      } else {
        setError(`Failed to load telemetry data: ${err.message || 'Unknown error'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  if (!user?.is_admin) {
    return (
      <div className="p-8">
        <div className="max-w-4xl mx-auto text-center py-20">
          <h1 className="text-2xl font-bold text-zinc-100 mb-4">Access Denied</h1>
          <p className="text-zinc-500">This page is only available to administrators.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold text-zinc-100 mb-6">Telemetry Dashboard</h1>
          <div className="text-zinc-500">Loading telemetry data...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold text-zinc-100 mb-6">Telemetry Dashboard</h1>
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400">{error}</div>
        </div>
      </div>
    );
  }

  const maxDay = Math.max(...(stats?.events_by_day || []).map(d => d.count), 1);

  const filteredFeedback = feedbackFilter
    ? feedback.filter(f => f.category === feedbackFilter)
    : feedback;

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-zinc-100 mb-2">Telemetry Dashboard</h1>
        <p className="text-zinc-500 mb-8">Anonymous usage analytics and user feedback</p>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <MetricCard label="Total Events" value={stats?.total_events || 0} />
          <MetricCard label="Total Scans" value={stats?.total_scans || 0} />
          <MetricCard
            label="Avg Risk Score"
            value={stats?.avg_risk_score != null ? stats.avg_risk_score.toFixed(1) : '-'}
          />
          <MetricCard
            label="Avg Scan Duration"
            value={stats?.avg_scan_duration_ms != null ? `${(stats.avg_scan_duration_ms / 1000).toFixed(1)}s` : '-'}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Top Commands */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-zinc-100 mb-4">Top Commands</h2>
            {(stats?.top_commands || []).length === 0 ? (
              <p className="text-zinc-500 text-sm">No command data yet</p>
            ) : (
              <div className="space-y-3">
                {stats.top_commands.map((cmd, i) => {
                  const maxCmd = stats.top_commands[0]?.count || 1;
                  return (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-sm text-zinc-400 w-20 shrink-0">{cmd.command || '-'}</span>
                      <div className="flex-1 bg-zinc-800 rounded-full h-5 overflow-hidden">
                        <div
                          className="bg-cyan-500 h-full rounded-full transition-all"
                          style={{ width: `${(cmd.count / maxCmd) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-zinc-300 w-10 text-right">{cmd.count}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Top Providers */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-zinc-100 mb-4">Top Providers Detected</h2>
            {(stats?.top_providers || []).length === 0 ? (
              <p className="text-zinc-500 text-sm">No provider data yet</p>
            ) : (
              <div className="space-y-3">
                {stats.top_providers.map((p, i) => {
                  const maxP = stats.top_providers[0]?.count || 1;
                  return (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-sm text-zinc-400 w-24 shrink-0">{p.provider}</span>
                      <div className="flex-1 bg-zinc-800 rounded-full h-5 overflow-hidden">
                        <div
                          className="bg-cyan-500 h-full rounded-full transition-all"
                          style={{ width: `${(p.count / maxP) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-zinc-300 w-10 text-right">{p.count}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Daily Usage Trend */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6 mb-8">
          <h2 className="text-lg font-semibold text-zinc-100 mb-4">Daily Usage (Last 30 Days)</h2>
          {(stats?.events_by_day || []).length === 0 ? (
            <p className="text-zinc-500 text-sm">No daily data yet</p>
          ) : (
            <div className="flex items-end gap-1 h-32">
              {[...stats.events_by_day].reverse().map((day, i) => (
                <div key={i} className="flex-1 flex flex-col items-center justify-end" title={`${day.date}: ${day.count} events`}>
                  <div
                    className="w-full bg-cyan-400 rounded-t-sm min-h-[2px]"
                    style={{ height: `${(day.count / maxDay) * 100}%` }}
                  />
                </div>
              ))}
            </div>
          )}
          {(stats?.events_by_day || []).length > 0 && (
            <div className="flex justify-between mt-2 text-xs text-zinc-500">
              <span>{stats.events_by_day[stats.events_by_day.length - 1]?.date}</span>
              <span>{stats.events_by_day[0]?.date}</span>
            </div>
          )}
        </div>

        {/* Feedback */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-zinc-100">User Feedback ({feedback.length})</h2>
            <div className="flex gap-2">
              {['', 'bug', 'feature', 'general'].map(cat => (
                <button
                  key={cat}
                  onClick={() => setFeedbackFilter(cat)}
                  className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                    feedbackFilter === cat
                      ? 'border-cyan-500 text-cyan-400 bg-cyan-500/10'
                      : 'border-zinc-700 text-zinc-400 hover:border-zinc-600'
                  }`}
                >
                  {cat || 'All'}
                </button>
              ))}
            </div>
          </div>
          {filteredFeedback.length === 0 ? (
            <p className="text-zinc-500 text-sm py-4 text-center">No feedback yet</p>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {filteredFeedback.map(fb => (
                <div key={fb.id} className="border border-zinc-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-yellow-400">{'★'.repeat(fb.rating)}{'☆'.repeat(5 - fb.rating)}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        fb.category === 'bug' ? 'bg-red-500/10 text-red-400' :
                        fb.category === 'feature' ? 'bg-blue-500/10 text-blue-400' :
                        'bg-zinc-800 text-zinc-400'
                      }`}>
                        {fb.category}
                      </span>
                    </div>
                    <span className="text-xs text-zinc-500">
                      {fb.created_at ? new Date(fb.created_at).toLocaleDateString() : '-'}
                    </span>
                  </div>
                  <p className="text-sm text-zinc-300">{fb.message}</p>
                  {fb.page && <p className="text-xs text-zinc-500 mt-1">Page: {fb.page}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const MetricCard = ({ label, value }) => (
  <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5">
    <p className="text-sm text-zinc-500 mb-1">{label}</p>
    <p className="text-2xl font-bold text-zinc-100">{value}</p>
  </div>
);

export default AdminTelemetry;
