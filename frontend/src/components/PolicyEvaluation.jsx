import React from 'react';
import { Badge } from './ui/badge';

const PolicyEvaluation = ({ policiesResult }) => {
  if (!policiesResult || Object.keys(policiesResult).length === 0) {
    return null;
  }

  const { errors = [], warnings = [], passes = [] } = policiesResult;

  return (
    <div>
      <h3 className="text-base font-semibold text-zinc-100 mb-4">Policy Evaluation</h3>
      <div className="grid md:grid-cols-3 gap-4">
        {/* Errors */}
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <h4 className="font-semibold text-red-300">Errors ({errors.length})</h4>
          </div>
          {errors.length > 0 ? (
            <ul className="space-y-2">
              {errors.map((err, idx) => (
                <li key={idx} className="text-sm text-red-400">
                  <div className="font-medium">{err.message}</div>
                  <div className="text-xs text-red-400 mt-1">{err.rule}</div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-red-400">No errors</p>
          )}
        </div>

        {/* Warnings */}
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-5 h-5 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <h4 className="font-semibold text-amber-300">Warnings ({warnings.length})</h4>
          </div>
          {warnings.length > 0 ? (
            <ul className="space-y-2">
              {warnings.map((warn, idx) => (
                <li key={idx} className="text-sm text-amber-400">
                  <div className="font-medium">{warn.message}</div>
                  <div className="text-xs text-amber-400 mt-1">{warn.rule}</div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-amber-400">No warnings</p>
          )}
        </div>

        {/* Passes */}
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <h4 className="font-semibold text-green-300">Passes ({passes.length})</h4>
          </div>
          {passes.length > 0 ? (
            <ul className="space-y-2">
              {passes.map((pass, idx) => (
                <li key={idx} className="text-sm text-green-400">
                  <div className="font-medium">{pass.message}</div>
                  <div className="text-xs text-green-400 mt-1">{pass.rule}</div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-green-400">No passes</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default PolicyEvaluation;
