import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Switch } from './ui/switch';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';
import { Info } from 'lucide-react';

const RepoForm = ({ onScan, isScanning }) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [fullScan, setFullScan] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (repoUrl.trim()) {
      onScan(repoUrl.trim(), fullScan);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6" data-testid="repo-form">
      <div>
        <label htmlFor="repo-url" className="block text-sm font-medium text-gray-900 mb-3">
          GitHub Repository URL
        </label>
        <Input
          id="repo-url"
          data-testid="repo-url-input"
          type="text"
          placeholder="https://github.com/openai/openai-python"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          disabled={isScanning}
          className="h-12 text-base"
        />
        <p className="text-xs text-gray-500 mt-2">
          Enter a public GitHub repository URL to scan for AI/LLM dependencies.
        </p>
      </div>

      {/* Full Scan Toggle - Compact Row */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <label
            htmlFor="full-scan"
            className="text-sm font-medium text-gray-900 cursor-pointer"
          >
            Scan entire repository
          </label>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  className="inline-flex items-center justify-center"
                  aria-label="More information about full scan"
                >
                  <Info className="w-4 h-4 text-gray-400 hover:text-gray-600 transition-colors" />
                </button>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="text-sm">
                  By default, we scan the first 1,000 files and prioritize src/, lib/, and app/ directories.
                  Turn this on to scan <strong>all</strong> files in the repository.
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <Switch
            id="full-scan"
            checked={fullScan}
            onCheckedChange={setFullScan}
            disabled={isScanning}
            data-testid="full-scan-toggle"
            aria-label="Toggle full repository scan"
          />
          
          {/* Conditional warning - inline on desktop, wraps on mobile */}
          {fullScan && (
            <div className="transition-all duration-200 ease-in-out animate-in fade-in">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-amber-100 border border-amber-300 rounded-full">
                <svg className="w-3.5 h-3.5 flex-shrink-0 text-amber-700" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <p className="text-xs font-medium text-amber-800">
                  May take 30+ seconds for large repos
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      <Button
        type="submit"
        disabled={!repoUrl.trim() || isScanning}
        className="w-full h-12 text-base font-medium"
        data-testid="scan-button"
      >
        {isScanning ? (
          <>
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
            {fullScan ? 'Scanning (Full scan in progress...)' : 'Scanning...'}
          </>
        ) : (
          <>
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Start Scan
          </>
        )}
      </Button>
    </form>
  );
};

export default RepoForm;
