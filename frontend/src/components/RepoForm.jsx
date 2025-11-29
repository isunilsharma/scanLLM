import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Checkbox } from './ui/checkbox';

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

      {/* Full Scan Option */}
      <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <Checkbox
          id="full-scan"
          checked={fullScan}
          onCheckedChange={setFullScan}
          disabled={isScanning}
          data-testid="full-scan-checkbox"
        />
        <div className="flex-1">
          <label
            htmlFor="full-scan"
            className="text-sm font-medium text-gray-900 cursor-pointer"
          >
            Scan entire repository (no file limit)
          </label>
          <p className="text-xs text-gray-600 mt-1">
            By default, we scan the first 1,000 files (prioritizing src/, lib/, app/ directories). 
            Enable this for a complete scan of all files.
            {fullScan && <span className="text-amber-600 font-medium"> ⚠️ May take 30+ seconds for large repositories.</span>}
          </p>
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
            Scanning{fullScan ? ' (Full scan in progress...)' : '...'}
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
