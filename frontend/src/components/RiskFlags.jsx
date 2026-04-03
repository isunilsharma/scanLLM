import React from 'react';
import { Badge } from './ui/badge';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';

const RiskFlags = ({ riskFlags }) => {
  if (!riskFlags || riskFlags.length === 0) {
    return (
      <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-6">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <div>
            <h3 className="font-semibold text-green-300 text-base">Risk Flags</h3>
            <p className="text-sm text-green-400 mt-2">No notable risk signals detected for this repository.</p>
          </div>
        </div>
      </div>
    );
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'bg-red-500/10 border-red-500/20 text-red-300';
      case 'medium': return 'bg-amber-500/10 border-amber-500/20 text-amber-300';
      case 'low': return 'bg-blue-500/10 border-blue-500/20 text-blue-300';
      default: return 'bg-zinc-800 border-zinc-600 text-zinc-300';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'high':
        return (
          <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'medium':
        return (
          <svg className="w-5 h-5 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  return (
    <div className="space-y-3">
      <h3 className="text-base font-semibold text-zinc-100 mb-4">Risk Flags</h3>
      {riskFlags.map((flag) => (
        <div
          key={flag.id}
          className={`border rounded-xl p-4 ${getSeverityColor(flag.severity)}`}
        >
          <div className="flex items-start gap-3">
            {getSeverityIcon(flag.severity)}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <h4 className="font-medium text-sm">{flag.label}</h4>
                <Badge
                  variant={flag.severity === 'high' ? 'destructive' : 'secondary'}
                  className="text-xs"
                >
                  {flag.severity}
                </Badge>
              </div>
              <p className="text-sm opacity-90">{flag.description}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default RiskFlags;
