import React from 'react';
import { Badge } from './ui/badge';

const BlastRadiusSummary = ({ blastRadiusSummary }) => {
  if (!blastRadiusSummary) {
    return null;
  }

  const { high = 0, medium = 0, low = 0 } = blastRadiusSummary;
  const total = high + medium + low;

  if (total === 0) {
    return null;
  }

  return (
    <div>
      <h3 className="text-base font-semibold text-gray-900 mb-4">Blast Radius Summary</h3>
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <h4 className="font-semibold text-red-900 text-sm">High Risk</h4>
          </div>
          <p className="text-3xl font-bold text-red-900">{high}</p>
          <p className="text-xs text-red-700 mt-1">Critical files (api/, service/)</p>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <svg className="w-5 h-5 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <h4 className="font-semibold text-amber-900 text-sm">Medium Risk</h4>
          </div>
          <p className="text-3xl font-bold text-amber-900">{medium}</p>
          <p className="text-xs text-amber-700 mt-1">Moderate AI usage</p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <h4 className="font-semibold text-blue-900 text-sm">Low Risk</h4>
          </div>
          <p className="text-3xl font-bold text-blue-900">{low}</p>
          <p className="text-xs text-blue-700 mt-1">Minimal AI usage</p>
        </div>
      </div>
    </div>
  );
};

export default BlastRadiusSummary;
